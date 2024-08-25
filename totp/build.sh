
cp -v $(type -p crypto.py) .

podman build -t totp:$(date +%F) .

rm -v crypto.py

