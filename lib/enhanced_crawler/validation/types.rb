# frozen_string_literal: true

require 'dry-types'
require 'uri'

module EnhancedCrawler
  module Validation
    # Custom Dry::Types definitions for configuration values.
    module Types
      include Dry.Types()

      # Custom type for mount strings like "/local/path:http://remote/path"
      # Coerces the string into a hash { local_path: String, dest_uri: URI }
      MountString = Types::String.constrained(
        format: %r{\A/.+:.+\z} # Basic format check: starts with /, contains :
      ).constructor do |value|
        begin
          local_path, dest_url_str = value.split(':', 2)
          raise ArgumentError, "Invalid destination URL format: cannot be empty" if dest_url_str.nil? || dest_url_str.empty?

          # Use HttpUrl type for coercion and basic validation of the destination URL
          # This will raise Dry::Types::CoercionError if invalid (caught below)
          dest_uri = HttpUrl[dest_url_str] # Apply the HttpUrl type constructor

          # Ensure local path is absolute (already partially checked by regex)
          raise ArgumentError, "Local path must be absolute" unless local_path.start_with?('/')

          { local_path: local_path, dest_uri: dest_uri }
        rescue Dry::Types::CoercionError, ArgumentError => e
          raise Dry::Types::CoercionError, "Invalid MountString format or content: #{e.message}"
        end
      end

      # Define other custom types if needed, e.g., for HTTP URLs if coercion is desired
      HttpUrl = Types::String.constructor do |value|
        begin
          uri = URI.parse(value)
          unless (uri.is_a?(URI::HTTP) || uri.is_a?(URI::HTTPS)) && !uri.host.nil?
             raise ArgumentError, "URL must be HTTP/HTTPS with a host"
          end
          uri
        rescue URI::InvalidURIError, ArgumentError => e
          raise Dry::Types::CoercionError, "Invalid HTTP URL: #{e.message}"
        end
      end

       # Define GitUrl type if coercion to URI is desired
       GitUrl = Types::String.constructor do |value|
         begin
           # Handle SSH syntax separately as URI.parse struggles
           if value.include?('@') && value.include?(':') && !value.start_with?('http', 'git:')
             # For SSH, we might not return a standard URI object easily,
             # or we could create a custom struct/object.
             parts = value.split(':')
             unless parts.size == 2 && parts[0].include?('@') && !parts[1].empty?
               raise ArgumentError, "Invalid SSH Git URL format"
             end
             value
           else
             uri = URI.parse(value)
             valid_scheme = %w[http https git].include?(uri.scheme)
             valid_host = !uri.host.nil? && !uri.host.empty?
             valid_path_or_opaque = !uri.path.nil? || !uri.opaque.nil?

             unless valid_scheme && valid_host && valid_path_or_opaque
               raise ArgumentError, "Invalid Git URL format"
             end
             uri
           end
         rescue URI::InvalidURIError, ArgumentError => e
           raise Dry::Types::CoercionError, "Invalid Git URL: #{e.message}"
         end
       end

    end
  end
end