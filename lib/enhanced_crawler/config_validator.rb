# frozen_string_literal: true

require 'dry-validation'
require 'uri'
require 'set'
require_relative 'validation/predicates'
require_relative 'validation/types'

module EnhancedCrawler
  # Define the validation contract using dry-validation
  class ConfigContract < Dry::Validation::Contract
    # Configure localization
    config.messages.backend = :yaml
    config.messages.load_paths << File.expand_path('../../../config/locales/en.yml', __dir__)
    params do
      optional(:domains).array(:hash) do
        required(:url).filled(Types::HttpUrl)
        optional(:seed_urls).array(:string)
      end
      optional(:repositories).array(:hash) do
        required(:url).filled(Types::HttpUrl).value(:http_url?, check_path_empty: true)
        required(:git_urls).array(min_size?: 1).each(Types::GitUrl)
      end
      optional(:directories).array(:hash) do
        required(:url).filled(Types::HttpUrl).value(:http_url?, check_path_empty: true)
        required(:mounts).array(min_size?: 1).each(Types::MountString)
      end
    end

    # --- Rules ---

    rule(:directories).each do |context:|
      next unless value[:url].is_a?(URI::Generic)

      base_uri = value[:url]
      base_hostname = base_uri.host

      value[:mounts].each_with_index do |mount_data, idx|
        next unless mount_data.is_a?(Hash) && mount_data[:dest_uri].is_a?(URI::Generic)

        mount_key_path = [:directories, context[:index_key], :mounts, idx]
        dest_uri = mount_data[:dest_uri]

        if dest_uri.host != base_hostname
          key(mount_key_path).failure(:invalid_mount_host, dest_host: dest_uri.host, base_host: base_hostname)
        end

        if dest_uri.path.nil? || dest_uri.path.empty? || dest_uri.path == '/'
           key(mount_key_path).failure(:invalid_mount_path)
        end
      end
    end

    rule do # Hostname uniqueness
      host_map = {}

      [:domains, :repositories, :directories].each do |section_key|
        values[section_key]&.each_with_index do |entry, index|
          next unless entry.is_a?(Hash) && entry[:url].is_a?(URI::Generic)

          host = entry[:url].host
          path = [section_key, index, :url]

          if host && !host.empty?
            host_map[host] ||= []
            host_map[host] << path
          end
        end
      end

      host_map.each do |host, paths|
        if paths.size > 1
          paths.each do |path|
            key(path).failure(:not_unique, host: host)
          end
        end
      end
    end
  end # End ConfigContract

  class ConfigValidator
    def initialize(config_hash)
      unless config_hash.is_a?(Hash)
        raise EnhancedCrawler::ConfigValidationError, "Configuration must be a Hash."
      end
      @config = config_hash
      @contract = ConfigContract.new
    end

    def validate!
      result = @contract.call(@config)

      unless result.success?
        error_messages = result.errors(full: true).to_h.map do |path_keys, messages|
          "#{path_keys.join('.')}: #{messages.join(', ')}"
        end.join("\n")
        raise EnhancedCrawler::ConfigValidationError, "Configuration validation failed:\n#{error_messages}"
      end

      result.to_h
    end
  end
end