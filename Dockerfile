FROM python:3.8-slim-buster
RUN apt-get update && apt-get install -y git
RUN git clone https://github.com/obrigg/ise-cleaning-services.git
WORKDIR /ise-cleaning-services/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
ENTRYPOINT ["python", "syslog_triggered_cleanup.py"]
