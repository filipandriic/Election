FROM python:3

RUN mkdir -p /opt/src/applications
WORKDIR /opt/src/applications

COPY applications/dameon/application.py ./application.py
COPY applications/dameon/configuration.py ./configuration.py
COPY applications/dameon/requirements.txt ./requirements.txt
COPY applications/admin/models.py ./admin/models.py

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src"

ENTRYPOINT ["python", "./application.py"]