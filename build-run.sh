docker build -t enhanced-crawler .

docker run -v ./crawl.yml:/crawl.yml -it enhanced-crawler ruby bin/crawler crawl /crawl.yml