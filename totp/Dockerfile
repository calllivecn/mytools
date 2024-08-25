FROM alpine-py3:latest AS builder

RUN mkdir /app

COPY requireuments.txt /app/
COPY crypto.py /app/
COPY totplib.py /app/
COPY totpv2.py /app/

FROM alpine-py3:latest

COPY --from=builder /app /app

RUN pip install --break-system-packages -r /app/requireuments.txt \
&& cp -v /app/crypto.py /usr/bin/

WORKDIR /app

VOLUME /data

ENTRYPOINT ["python", "totpv2.py"]
CMD ["--config", "/data/totp.a"]

EXPOSE 12201


