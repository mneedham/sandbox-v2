FROM debian:latest
MAINTAINER Ryan Boyd, <ryan@neo4j.com>

RUN apt-get update
RUN apt-get install -y python python-pip
RUN pip install neo4j-driver
RUN pip install futures
RUN pip install retrying

ADD import_data.py /
RUN chmod +x /import_data.py

ENTRYPOINT ["python", "-u", "/import_data.py"]
