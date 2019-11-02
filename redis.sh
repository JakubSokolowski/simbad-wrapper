#!/bin/bash
if [ ! -d redis-stable/src ]; then
    curl -O http://download.redis.io/redis-stable.tar.gz
    tar xvzf redis-stable.tar.gz
    rm redis-stable.tar.gz
    cd redis-stable || exit
    make
    cd ..
fi

cd redis-stable/src || exit
./redis-server
