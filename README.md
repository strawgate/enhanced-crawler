# enhanced-crawler
Wrapper around Crawler to support additional capabilities

## Features

- Takes the same docker / command line parameters as crawler

- Prepare for Crawl
  - Can point it at a file, directory, or git repository
  - Will download the repository if it is a git repository
  - Will serve the file or directory via a Web Server over HTTP
  - Will translate the required configuration from file paths to web server URLs
  - Will support multiple files, directories, or git repositories
- Crawl
  - Starts the crawl process
  - Exits when the crawl is complete
