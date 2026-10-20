FROM alpine:3.22
RUN apk add --no-cache python3 py3-numpy py3-pillow py3-websockets tzdata ca-certificates \
    && adduser -D -u 1000 meteo \
    && mkdir /state && chown meteo:meteo /state
WORKDIR /app
COPY . .
USER meteo
ENV TZ=Atlantic/Canary PYTHONDONTWRITEBYTECODE=1
EXPOSE 8080
CMD ["python3", "-m", "lpa.serve", "--directory", "/tmp/meteo-lpa", "--bind", "0.0.0.0", "--port", "8080", "--state-dir", "/state"]
