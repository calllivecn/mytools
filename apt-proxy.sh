#!/bin/bash
# date 2019-06-11 14:52:06
# author calllivecn <c-all@qq.com>


proxy_addr="http://127.0.0.1:9999"


apt -o Acquire::http::Proxy::ppa.launchpad.net="$proxy_addr" "$@"
