from __future__ import annotations

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.operators.dummy import DummyOperator
from airflow.sensors.filesystem import FileSensor

BUCKET_NAME = "finalprojectxai"
DATA_DIR = "/opt/airflow/data"

def check_upload_completion():
    """
    Check if the upload DAG completed successfully
    """
    print("Checking if upload_data_to_s3 DAG completed successfully...")
    # This function can be expanded to check S3 bucket contents
    # or database records to verify upload completion
    return True

def check_combine_completion():
    """
    Check if the combine DAG completed successfully
    """
    print("Checking if combine_multilingual_data DAG completed successfully...")
    # This function can be expanded to check for the combined file in S3
    return True


with DAG(
    dag_id="master_pipeline",
    start_date=datetime(2023, 1, 1),
    schedule=None,  # Manual trigger only
    catchup=False,
    tags=["master", "pipeline", "orchestration"],
    description="Master pipeline that orchestrates upload and combine DAGs in sequence",
    default_args={
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
) as dag:
    
    # Start task
    start = DummyOperator(
        task_id="start_pipeline",
    )
    
    # Step 1: Trigger upload DAG
    trigger_upload = TriggerDagRunOperator(
        task_id="trigger_upload_data_to_s3",
        trigger_dag_id="upload_data_to_s3",
        wait_for_completion=True,  # Wait for upload to complete before proceeding
        poke_interval=30,  # Check every 30 seconds
    )
    
    # Step 2: Verify upload completion
    verify_upload = PythonOperator(
        task_id="verify_upload_completion",
        python_callable=check_upload_completion,
    )
    
    # Step 3: Trigger combine DAG
    trigger_combine = TriggerDagRunOperator(
        task_id="trigger_combine_multilingual_data",
        trigger_dag_id="combine_multilingual_data",
        wait_for_completion=True,  # Wait for combine to complete
        poke_interval=30,  # Check every 30 seconds
    )
    
    # Step 4: Verify combine completion
    verify_combine = PythonOperator(
        task_id="verify_combine_completion",
        python_callable=check_combine_completion,
    )
    
    
    # End task
    end = DummyOperator(
        task_id="end_pipeline",
    )
    
    # Define the pipeline flow
    start >> trigger_upload >> verify_upload >> trigger_combine >> verify_combine >> end
