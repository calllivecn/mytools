#!/bin/sh

#path=$(which $0)

#cd ${path%/*}

tmp=`mktemp`


if [ -z $1 ];then


		wget -q -O $tmp 'http://city.ip138.com/ip2city.asp'

		tail -1 $tmp |awk '-F[' '{print $2}' |awk '-F]' '{print $1}'


else

		http='http://ip.chinaz.com/?IP='

		wget -q -O $tmp ${http}$1

		str=$(grep -E  '您的IP' $tmp)
		s=$(echo $str |awk '-F>' '{print $3}')
		ip=$(echo ${s%%<*})
		#echo your IP : $s
		s=$(echo $str |awk '-F>' '{print $5}')
		s=$(echo ${s%%<*})
		echo 您的IP: $ip $s
		
		grep -E '查询结果' $tmp |sed -e 's/<strong class="red">//g' -e 's/<\/strong><br \/>//g' -e 's/://g' -e 's/  //g'
	
		#for s in $(grep -E '查询结果' $tmp |sed -e 's/<strong class="red">//g' -e 's/<\/strong><br \/>//g' -e 's/://g');
		#do
		#s=$(echo ${s#*:})
		#s=$(echo ${s%%<*})
		#echo $1 : $s
		#done
fi

rm $tmp
