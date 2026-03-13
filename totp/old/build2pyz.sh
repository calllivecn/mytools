
set -e

CWD=$(pwd -P)
TMP=$(mktemp -d -p "$CWD")

#DEPEND_CACHE="${CWD}/depend-cache"

#if [ -d "$DEPEND_CACHE" ];then
#	echo "使用depend-cache～"
#	cp -r "$DEPEND_CACHE"/* "$TMP"
#else
#	mkdir -v "${DEPEND_CACHE}"
#	pip install --no-compile --target "$DEPEND_CACHE" -r requirements.txt
#	cp -r "$DEPEND_CACHE"/* "$TMP"
#fi

NAME="totp"
EXT=".pyz"

clean(){
	echo "clean... ${TMP}"
	rm -rf "${TMP}"
	echo "done"
}

trap clean SIGINT SIGTERM EXIT ERR

cp totplib.py totp.py "$TMP"

#find "$TMP" -type d -name "__pycache__" -exec rm -r "{}" "+"
#shiv --site-packages "$TMP" --compressed -p '/usr/bin/python3 -sE' -o "${NAME}.pyz" -e "client:main"

python -m zipapp --compress --python '/usr/bin/python -sE' -o "${NAME}.pyz" --main "totp:main" "$TMP"

