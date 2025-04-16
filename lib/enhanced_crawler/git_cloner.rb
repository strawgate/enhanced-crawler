# frozen_string_literal: true

require 'fileutils'
require 'English' # For $CHILD_STATUS
require 'open3'

module EnhancedCrawler
  # Handles cloning of Git repositories
  class GitCloner
    def initialize(static_temp_dir)
      @static_temp_dir = static_temp_dir
      # Ensure the base directory exists (though it should be pre-created)
      FileUtils.mkdir_p(@static_temp_dir) unless Dir.exist?(@static_temp_dir)
    end

    # Clones a git repository into a specified subdirectory within the static temp dir.
    # Returns [true, path] on success, [false, error_message] on failure.
    def clone(git_url, destination_dir_name)
      target_clone_path = File.join(@static_temp_dir, destination_dir_name)

      warn "Cloning #{git_url} to #{target_clone_path}..."
      stdout, stderr, status = Open3.capture3('git', 'clone', '--quiet', '--depth', '1', git_url, target_clone_path)

      if status.success?
        warn "Successfully cloned #{git_url}"
        [true, target_clone_path] # Return success and path
      else
        error_message = stderr.strip.empty? ? "Git clone failed with exit status #{status.exitstatus}" : stderr.strip
        warn "Failed to clone repository: #{git_url}. Error: #{error_message}"
        # Optionally clean up failed clone attempt directory
        FileUtils.remove_entry_secure(target_clone_path) if Dir.exist?(target_clone_path)
        [false, error_message] # Indicate failure and provide stderr
      end
    rescue StandardError => e
      warn "Error during git clone of #{git_url}: #{e.message}"
      [false, e.message] # Indicate failure and provide exception message
    end

    # No private methods needed for now
  end
end