FROM alpine-py3:latest AS builder

RUN mkdir /app

COPY requirements.txt /app/
COPY src/ /app/

FROM alpine-py3:latest

COPY --from=builder /app /app

RUN pip install --break-system-packages -r /app/requirements.txt

WORKDIR /app

VOLUME /data

ENTRYPOINT ["python", "uvicorn-run.py"]
CMD ["--db", "/data/totp.db"]

EXPOSE 12201


