
if [ -f crypto.py ];then
    :
else
    echo "需要cp -v crypto.py 到当前目录"
    exit 1
fi

#cp -v $(type -p crypto.py) .

podman build -t totp:$(date +%F) .

#rm -v crypto.py

