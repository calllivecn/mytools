#!/bin/bash
# date 2017-11-27 13:11:46
# author calllivecn <c-all@qq.com>

set -e


PROXY='socks5://127.0.0.1:10000'
YOU='youtube-dl --proxy '"$PROXY"

program="${0##*/}"

using(){
	echo "Using : $program queue"
	echo "start download."
	echo
    echo "Using : $program [-dh] [-o outfilename] <URL>"
	echo "add download queue."
	echo
	echo "queue 启动队列下载."
	echo "-d    使用 youtube-dl 默认视频选项"
	echo "-o    输出文件名"
	echo "-h    help"
}

YOUTUBE_QUEUE=

check_YOUTUBE_QUEUE(){
	if [ -w youtube.queue ];then
		YOUTUBE_QUEUE=youtube.queue
	elif [ -w ~/youtube.queue ];then
		YOUTUBE_QUEUE=~/youtube.queue
	elif [ -w /tmp/youtube.queue ];then
		YOUTUBE_QUEUE=/tmp/youtube.queue
	else
		YOUTUBE_QUEUE='/tmp/youtube.queue'
		:> "$YOUTUBE_QUEUE"
	fi
	#echo "YOUTUBE_QUEUE is $YOUTUBE_QUEUE"
}

number=
OUT=
URL=
getqueue(){
	sed -n '1p' "$YOUTUBE_QUEUE"
	sed -i '1d' "$YOUTUBE_QUEUE"
}

YOUTUBE_QUEUE_download(){
while :
do
	number=
	OUT=
	URL=

	eval $(getqueue)

	if [ "$URL"x = ""x ];then
		#echo "$YOUTUBE_QUEUE queue in empty,sleep 5"
		sleep 5
		continue
	fi

	if [ "$number"x != ""x ];then
		number="-f ""$number"
	else
		number=
	fi

	if [ "$OUT"x != ""x ];then
		OUT="-o ""$OUT"
	else
		OUT=
	fi
	echo "execoute:" $YOU "$URL" $OUT "$number"
	$YOU "$URL" $OUT "$number" || echo "$URL" $OUT "$number" "下载出错."
done
}

if [ "$1"x = "queue"x ];then
	shift
	check_YOUTUBE_QUEUE
	echo "$program start YOUTUBE_QUEUE --> $YOUTUBE_QUEUE"
	YOUTUBE_QUEUE_download
	exit 0
fi

if [ $# -eq 1 ];then
	echo "$1" |grep -E "^https://"
fi


check_YOUTUBE_QUEUE

while getopts ':o:dh' opt;do
case $opt in
    o)
        OUT="$OPTARG"
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



if [ $DEFAULT ];then
    echo URL="$1" OUT="$OUT" 'number=' '-->' "$YOUTUBE_QUEUE"
    echo URL='"'"$1"'"' OUT='"'"$OUT"'"' 'number=' >> "$YOUTUBE_QUEUE"
else
    $YOU -F "$1"
    echo -n "输入下载视频和音频编号(如137+140): "
    read number
    number=${number:-'137+140'}
    echo URL='"'"$1"'"' OUT='"'"$OUT"'"' number='"'"$number"'"' '-->' "$YOUTUBE_QUEUE"
    echo URL='"'"$1"'"' OUT='"'"$OUT"'"' number='"'"$number"'"' >> "$YOUTUBE_QUEUE"
fi


