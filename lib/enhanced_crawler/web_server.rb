# frozen_string_literal: true

require 'webrick'
require 'thread'

module EnhancedCrawler
  # Manages the WEBrick HTTP server lifecycle
  class WebServer
    HTTP_PORT = 80 # Fixed port

    def initialize
      @vhost_configs = {}
      @server = nil
      @server_thread = nil
      @cleaning_up = false # Prevent recursive cleanup calls
    end

    # Configures the document root for a given hostname.
    def add_vhost_root(hostname, document_root_path)
      return if hostname.nil? || document_root_path.nil?

      @vhost_configs[hostname] ||= { repo_root: nil, mounts: [] } # Ensure host entry exists

      # Check for idempotency
      if @vhost_configs[hostname].key?(:repo_root) && !@vhost_configs[hostname][:repo_root].nil?
        warn "Warning: Vhost root for '#{hostname}' already set to '#{@vhost_configs[hostname][:repo_root]}'. Ignoring new path '#{document_root_path}'."
        return
      end

      @vhost_configs[hostname][:repo_root] = document_root_path
      warn "WebServer: Configured root for #{hostname} -> #{document_root_path}"
    end

    # Adds a mount point for a given hostname.
    # Validates the source path exists and is a directory.
    def add_vhost_mount(hostname, url_path, source_path)
      return if hostname.nil? || url_path.nil? || source_path.nil?

      unless File.exist?(source_path) && File.directory?(source_path)
        warn "WebServer: Source directory for mount does not exist or is not a directory, skipping: #{source_path}"
        return
      end

      @vhost_configs[hostname] ||= { repo_root: nil, mounts: [] }
      @vhost_configs[hostname][:mounts] << { url_path: url_path, source_path: source_path }
      warn "WebServer: Configured mount for #{hostname}: #{url_path} -> #{source_path}"
    end

    # Starts the WEBrick server if any vhosts have been configured.
    # Returns true on success or if no vhosts were configured, false on failure.
    def start!
      return true if @vhost_configs.empty?

      warn "Starting local server on port #{HTTP_PORT}..."
      server_options = {
        Port: HTTP_PORT,
        Logger: WEBrick::Log.new($stderr, WEBrick::Log::WARN),
        AccessLog: [], # Disable access logging for cleaner output
        BindAddress: '0.0.0.0' # Listen on all interfaces
      }

      begin
        @server = WEBrick::HTTPServer.new(server_options)

        @vhost_configs.each do |hostname, config|
          warn "Configuring virtual host: #{hostname}"
          vhost = WEBrick::HTTPVirtualHost.new(@server, hostname)

          if config[:repo_root] && Dir.exist?(config[:repo_root])
            warn "  DocumentRoot: #{config[:repo_root]}"
            # WEBrick expects DocumentRoot to be set directly on the server options
            # for the virtual host, not on the vhost object itself after creation.
            # However, WEBrick's vhost handling is a bit limited. A common pattern
            # is to mount everything explicitly. Let's stick to explicit mounts
            # for clarity and mount the repo_root at '/'.
            warn "  WEBrick Mounting repo root #{config[:repo_root]} at /"
            vhost.mount('/', WEBrick::HTTPServlet::FileHandler, config[:repo_root], true)
          elsif config[:repo_root]
             warn "  DocumentRoot directory does not exist, skipping: #{config[:repo_root]}"
          end

          config[:mounts].each do |mount_info|
            warn "  WEBrick Mounting #{mount_info[:source_path]} at #{mount_info[:url_path]}"
            vhost.mount(mount_info[:url_path], WEBrick::HTTPServlet::FileHandler, mount_info[:source_path], true)
          end
        end

        @server_thread = Thread.new { @server.start }
        sleep 1.0 # Give server a moment to start
        warn "Server started."
        true
      rescue StandardError => e
        warn "Error starting WEBrick server: #{e.message}"
        warn e.backtrace.join("\n")
        @server = nil
        @server_thread = nil
        # Raise specific error instead of returning false
        raise EnhancedCrawler::WebServerStartError, "Error starting WEBrick server: #{e.message}"
      end
    end

    # Stops the WEBrick server if it's running.
    def stop!
      return unless @server_thread&.alive?
      return if @cleaning_up # Avoid issues if called during cleanup

      warn 'Shutting down server...'
      begin
        @server&.shutdown
        @server_thread.join(2) # Wait max 2 seconds
        @server_thread.kill if @server_thread.alive? # Force kill if needed
        warn 'Server shut down.'
      rescue StandardError => e
        warn "Error shutting down server: #{e.message}"
        @server_thread.kill if @server_thread&.alive? # Ensure thread is killed on error
      end
      @server = nil
      @server_thread = nil
    end

    # Cleanup method (currently just calls stop!)
    def cleanup
       return if @cleaning_up
       @cleaning_up = true
       warn "Cleaning up WebServer..."
       stop!
       warn "WebServer cleanup complete."
       @cleaning_up = false
    end

  end
end
