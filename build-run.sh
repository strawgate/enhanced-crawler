docker build -t enhanced-crawler .

docker run -v ./crawl.yml:/crawl.yml -it enhanced-crawler ruby bin/enhanced-crawler crawl /crawl.yml