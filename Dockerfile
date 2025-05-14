FROM python:3.13.3-slim-bullseye
EXPOSE 5000
WORKDIR /app

COPY ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt
COPY . .
ARG HACKETON_SECRET_KEY
ENV HACKETON_SECRET_KEY=${HACKETON_SECRET_KEY}
CMD ["flask", "run", "--host", "0.0.0.0"]