FROM python:3.12-slim

WORKDIR /usr/src/app

ADD festival_bot festival_bot
ADD main.py .
ADD requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD python -B -O main.py
