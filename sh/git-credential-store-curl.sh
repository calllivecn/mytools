#!/bin/bash
# date 2020-05-06 09:53:10
# author calllivecn <c-all@qq.com>


curl -X POST -H "AUTH: token-access-token" "http://localhost:11540" \
	-d '{"protocol": "https", "host": "github.com"}'
