from __future__ import annotations

import os
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

BUCKET_NAME = "finalprojectxai"        
DATA_DIR = "/opt/airflow/data"            # comes from the compose volume
AWS_CONN_ID = "S3_access"                 # set up in Airflow Connections

def upload_folder_to_s3():
    hook = S3Hook(aws_conn_id=AWS_CONN_ID)
    for root, _dirs, files in os.walk(DATA_DIR):
        for file_name in files:
            local_path = os.path.join(root, file_name)
            rel_path = os.path.relpath(local_path, DATA_DIR).replace("\\", "/")
            hook.load_file(
                filename=local_path,
                key=rel_path,                  # put files at the bucket root; add a prefix if you like
                bucket_name=BUCKET_NAME,
                replace=True,
            )

with DAG(
    dag_id="upload_data_to_s3",
    start_date=datetime(2023, 1, 1),
    schedule=None,
    catchup=False,
    tags=["s3", "upload"],
) as dag:
    PythonOperator(
        task_id="upload_folder",
        python_callable=upload_folder_to_s3,
    )