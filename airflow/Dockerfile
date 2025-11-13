FROM apache/airflow:2.7.3-python3.11

USER root
RUN apt-get update && apt-get install -y gcc python3-dev

USER airflow

# Install additional Python packages
RUN pip install --no-cache-dir \
    apache-airflow-providers-postgres \
    apache-airflow-providers-apache-spark \
    psycopg2-binary \
    pandas \
    requests

# Initialize Airflow database
RUN airflow db init
