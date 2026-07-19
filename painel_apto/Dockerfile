FROM python:3.12-alpine

WORKDIR /opt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ /opt/app/
COPY run.sh /run.sh
RUN chmod +x /run.sh

EXPOSE 8234
CMD ["/run.sh"]
