FROM python:3.10-alpine


WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN python -m pip install -r ./requirements.txt
COPY . /app

CMD [ "python", "__main__.py" ]
