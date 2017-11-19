#!/bin/bash

PROXY='socks5://127.0.0.1:1080'


using(){
    local str
    str='Using : youtube-dl [-d] [-o outfilename] <URL>
-d    使用 youtube-dl 默认视频选项
-o    输入文件名
-h    help
'
    echo "$str"

}

while getopts ':o:dh' opt;do
case $opt in
    o)
        OUT='-o '"$OPTARG"
        OUT_FILENAME="$OPTARG"
        ;;
    d)
        DEFAULT=true
        ;;
    h)
        using
        exit 0
        ;;
    \:)
        echo "-${OPTARG} 需要一个参数！"
        exit 2
    ;;
    \?)
        echo "不认得的选项 $OPTARG"
        exit 2
    ;;
esac
done

shift $[OPTIND - 1]

if [ $# -lt 1 ];then
    echo "视频地址呢？"
    exit 2
fi

set -e

#. ~/py_script/bin/activate


YOU='youtube-dl --proxy '"$PROXY"


if [ $DEFAULT ];then
    $YOU $OUT "$1"
else
    $YOU -F "$1"
    echo -n "输入下载视频和音频编号(如137+140): "
    read number
    number=${number:-'137+140'}
    echo $YOU -f "$number" $OUT "$1"
    $YOU -f "$number" $OUT "$1"
fi

if [ -n "$OUT_FILENAME" ];then
    notify-send "$OUT_FILENAME 下载完成"
else
    notify-send "${1##*/} 下载完成"
fi
