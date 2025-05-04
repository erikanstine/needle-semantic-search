FROM python:alpine

WORKDIR /app

COPY setup.py .
COPY common/ ./common
COPY backend/ ./backend

RUN pip install --upgrade pip && \
    pip install .

RUN pip install -r backend/requirements.txt

EXPOSE 8000

CMD [ "uvicorn", "backend.src.main:app", "--host", "0.0.0.0", "--port", "8000" ]