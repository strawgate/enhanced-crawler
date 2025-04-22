# Enhanced Crawler

This project is a wrapper around the Elastic Crawler project. The Elastic Crawler project can only crawl web pages. This tool serves local directories and Git repositories as web pages for crawling, allowing you to use the Crawler to index local files and Git content as if they were web pages.

## Serving Local Directories for Crawling

The Enhanced Crawler can serve local directories from your host machine for crawling by mounting them into the Docker container and providing the appropriate configuration. The crawler automatically handles serving them via a webpage.

Here's how you can serve a local directory (e.g., `/path/to/your/local/data`) for crawling:

1.  **Mount the local directory:** When running the Docker container, use the `-v` flag to mount your local directory into the container. For example:
    ```bash
    docker run -v /path/to/your/local/data:/app/crawling_data enhanced-crawler
    ```
    This mounts `/path/to/your/local/data` on your host machine to `/app/crawling_data` inside the container.

2.  **Provide the 'directories' configuration:** In your `crawl.yml` file, add a `directories` block specifying the mounted path and the desired URL within the crawler.

    ```yaml
    directories:
    - url: https://filesystem.local
      mounts:
        - /data: https://filesystem.local/path/where/you/want/to/serve
      crawl_rules:
        - policy: allow
          type: begins
          pattern: /path/where/you/want/to/serve
        - pattern: .*
          policy: deny
          type: regex
    ```
    This configuration tells the crawler to serve the directory mounted at `/app/crawling_data` inside the container under the `https://filesystem.local/path/where/you/want/to/serve` URL for crawling.

You can then access the content of your local directory within the crawler at `https://filesystem.local/path/where/you/want/to/serve`. The enhanced crawler translates these mount points into seed_urls for the underling crawler, as if there was actually a web server there. All other extraction and crawling logic remains the same as with regular web pages.

## Crawling Git Repositories

The Enhanced Crawler can also crawl content from Git repositories by providing their URLs in the configuration. The crawler will automatically handle cloning and serving these repositories.

Here's an example configuration snippet for crawling Git repositories (e.g., in your `crawl.yml`):

```yaml
repositories:
  - url: https://github.com
    git_urls:
      - https://github.com/strawgate/mcp-many-files.git
      - https://github.com/strawgate/fastmcp.git
    crawl_rules:
      - policy: allow
        type: begins
        pattern: /strawgate/fastmcp.git
      - policy: allow
        type: begins
        pattern: /strawgate/mcp-many-files.git
      - pattern: .*
        policy: deny
        type: regex
```
This configuration tells the crawler to fetch the specified Git repositories and make their content available for crawling.

## Getting Started

More detailed instructions on setting up the development environment and running the project can be found in the [DEVELOPING.md](DEVELOPING.md) file.
