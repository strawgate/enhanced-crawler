# frozen_string_literal: true

require 'dry-validation'
require 'uri'

module EnhancedCrawler
  module Validation
    # Custom predicates for validating configuration values.
    module Predicates
      include Dry::Logic::Predicates

      # Predicate to check if a value is a valid HTTP/HTTPS URL.
      # Optionally checks if the path is empty (for base URLs).
      predicate(:http_url?) do |value, check_path_empty: false|
        return false unless value.is_a?(String)

        begin
          uri = URI.parse(value)
          valid_scheme = uri.is_a?(URI::HTTP) || uri.is_a?(URI::HTTPS)
          valid_host = !uri.host.nil? && !uri.host.empty?
          valid_path = check_path_empty ? (uri.path.nil? || uri.path.empty? || uri.path == '/') : true

          valid_scheme && valid_host && valid_path
        rescue URI::InvalidURIError
          false
        end
      end

      # Predicate to check if a value is a valid Git URL (basic check).
      # Allows http, https, ssh, git schemes.
      predicate(:git_url?) do |value|
        return false unless value.is_a?(String)

        begin
          uri = URI.parse(value)
          valid_scheme = %w[http https ssh git].include?(uri.scheme)
          # SSH URLs might not have a traditional host in URI.parse, path is often user@host:repo
          is_ssh_like = value.include?('@') && value.include?(':') && !value.start_with?('http', 'git:')

          if is_ssh_like
            parts = value.split(':')
            return false unless parts.size == 2 && parts[0].include?('@') && !parts[1].empty?
            true
          else
            valid_host = !uri.host.nil? && !uri.host.empty?
            valid_path_or_opaque = !uri.path.nil? || !uri.opaque.nil? # Git scheme might use opaque
            valid_scheme && valid_host && valid_path_or_opaque
          end

        rescue URI::InvalidURIError
          # Handle cases like ssh URLs that URI.parse struggles with
          is_ssh_like = value.include?('@') && value.include?(':') && !value.start_with?('http', 'git:')
          if is_ssh_like
             parts = value.split(':')
             return false unless parts.size == 2 && parts[0].include?('@') && !parts[1].empty?
             true
          else
            false
          end
        end
      end
    end
  end
end