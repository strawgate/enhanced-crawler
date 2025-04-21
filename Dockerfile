FROM ghcr.io/strawgate/es-crawler:main

USER 0

RUN apt-get update && apt-get install -y --no-install-recommends \
    git && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /var/app/web/repos
RUN mkdir -p /var/app/web/directories
RUN mkdir -p /var/app/temp
RUN chown -R 451:451 /var/app/web

USER 451

COPY bin/enhanced-crawler bin/enhanced-crawler
