FROM python:3.12-alpine

COPY requirements.txt /
RUN pip install --no-cache-dir -r requirements.txt

COPY default.toml /
COPY src /src

VOLUME /db

EXPOSE 80/tcp

CMD ["uvicorn", "store.main:app", "--host", "0.0.0.0", "--port", "80", "--app-dir", "src/"]
