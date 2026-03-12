
CRYPTO="$1"

if [ -f $CRYPTO ];then
    cp -v $CRYPTO src/
else
    echo "需要cp -v crypto.py 到当前目录"
    exit 1
fi


podman build -t totp:$(date +%F) .

rm -v src/crypto.py

