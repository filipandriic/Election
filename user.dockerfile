FROM python:3

RUN mkdir -p /opt/src/applications/admin
WORKDIR /opt/src/applications/admin

COPY applications/user/application.py ./application.py
COPY applications/user/configuration.py ./configuration.py
COPY applications/user/admin_decorator.py ./admin_decorator.py
COPY applications/user/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENTRYPOINT ["python", "./application.py"]