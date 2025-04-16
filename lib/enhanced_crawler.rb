# frozen_string_literal: true

require_relative 'enhanced_crawler/dns_server'
require_relative 'enhanced_crawler/web_server'
require_relative 'enhanced_crawler/git_cloner'
# Wrapper class will be defined in bin/enhanced-crawler

module EnhancedCrawler
  # Base error class for the gem
  class Error < StandardError; end

  # Specific error classes
  class ConfigValidationError < Error; end
  class GitCloneError < Error; end
  class DnsServerError < Error; end
  class WebServerStartError < Error; end

  # Service classes will be defined in their respective files
end