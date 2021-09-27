FROM python:3

RUN mkdir -p /opt/src/admin
WORKDIR /opt/src/admin

COPY applications/admin/migrate.py ./migrate.py
COPY applications/admin/configuration.py ./configuration.py
COPY applications/admin/admin_decorator.py ./admin_decorator.py
COPY applications/admin/models.py ./models.py
COPY applications/admin/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt
RUN rm -rf ./migrations

ENTRYPOINT ["python", "./migrate.py"]