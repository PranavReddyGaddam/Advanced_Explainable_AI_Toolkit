from __future__ import annotations

import os
import tempfile
import pandas as pd
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

# Configuration
BUCKET_NAME = "finalprojectxai"
DATA_DIR = "/opt/airflow/data"
AWS_CONN_ID = "S3_access"
COMBINED_FILE_NAME = "combined_multilingual_mmlu.csv"

# Language mapping
LANGUAGE_MAPPING = {
    "mmlu_DE-DE.csv": "German",
    "mmlu_FR-FR.csv": "French", 
    "mmlu_AR-XY.csv": "Arabic",
    "mmlu_ES-LA.csv": "Spanish",
    "mmlu_ID-ID.csv": "Indonesian",
    "mmlu_IT-IT.csv": "Italian",
    "mmlu_JA-JP.csv": "Japanese",
    "mmlu_KO-KR.csv": "Korean",
    "mmlu_PT-BR.csv": "Portuguese",
    "mmlu_SW-KE.csv": "Swahili",
    "mmlu_YO-NG.csv": "Yorùbá",
    "mmlu_ZH-CN.csv": "Chinese"
}

def fix_encoding(text):
    """
    Fix encoding issues by re-encoding from mistaken Latin-1 to UTF-8
    """
    if isinstance(text, str):
        try:
            # Try to encode as latin1 then decode as utf-8
            return text.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            # If that fails, return original text
            return text
    return text

def apply_encoding_fix_to_dataframe(df):
    """
    Apply encoding fix to all string columns in the dataframe
    """
    for column in df.columns:
        if df[column].dtype == 'object':  # String columns
            df[column] = df[column].apply(fix_encoding)
    return df

def combine_multilingual_data():
    """
    Combine all multilingual MMLU files into one unified dataset
    """
    combined_data = []
    
    for filename, language in LANGUAGE_MAPPING.items():
        file_path = os.path.join(DATA_DIR, filename)
        
        if os.path.exists(file_path):
            print(f"Processing {filename} as {language}")
            
            try:
                # Read the CSV file
                df = pd.read_csv(file_path)
                
                # Apply encoding fix
                df = apply_encoding_fix_to_dataframe(df)
                
                # Add language column
                df["Language"] = language
                
                # Add source file column for tracking
                df["Source_File"] = filename
                
                combined_data.append(df)
                print(f"Successfully processed {filename}: {len(df)} rows")
                
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
                continue
        else:
            print(f"Warning: File {filename} not found in {DATA_DIR}")
    
    if not combined_data:
        raise ValueError("No data files were successfully processed!")
    
    # Combine all dataframes
    print("Combining all dataframes...")
    final_df = pd.concat(combined_data, ignore_index=True)
    
    # Add metadata columns
    final_df["Combined_Date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    final_df["Total_Languages"] = len(LANGUAGE_MAPPING)
    
    print(f"Combined dataset created: {len(final_df)} total rows")
    print(f"Languages included: {final_df['Language'].unique()}")
    print(f"Columns: {list(final_df.columns)}")
    
    # DATA CLEANING
    print("\n=== STARTING DATA CLEANING ===")
    
    # 1. CHECK FOR NULL VALUES
    print("Checking for null values...")
    null_counts = final_df.isnull().sum()
    null_summary = {col: count for col, count in null_counts.items() if count > 0}
    if null_summary:
        print(f"Found null values: {null_summary}")
        # Fill nulls with "Unknown"
        final_df = final_df.fillna("Unknown")
        print("Null values replaced with 'Unknown'")
    else:
        print("No null values found")
    
    # 2. CHECK FOR DUPLICATES
    print("Checking for duplicates...")
    total_duplicates = final_df.duplicated().sum()
    if total_duplicates > 0:
        print(f"Found {total_duplicates} duplicate rows")
        # Remove duplicates
        initial_count = len(final_df)
        final_df = final_df.drop_duplicates()
        final_count = len(final_df)
        duplicates_removed = initial_count - final_count
        print(f"Removed {duplicates_removed} duplicate rows")
    else:
        print("No duplicates found")
    
    # 3. Add processing timestamp
    final_df["processed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"\nCleaned dataset: {len(final_df)} total rows")
    print("=== DATA CLEANING COMPLETED ===\n")
    
    # Save cleaned file locally first - with fallback for permission issues
    local_output_path = os.path.join(DATA_DIR, COMBINED_FILE_NAME)
    
    try:
        # Try to save to the original location first
        final_df.to_csv(local_output_path, index=False, encoding='utf-8')
        print(f"Cleaned file saved locally: {local_output_path}")
    except PermissionError:
        # If permission denied, use a temporary file instead
        print(f"Permission denied for {local_output_path}. Using temporary file instead.")
        temp_dir = tempfile.gettempdir()
        local_output_path = os.path.join(temp_dir, COMBINED_FILE_NAME)
        final_df.to_csv(local_output_path, index=False, encoding='utf-8')
        print(f"Cleaned file saved to temporary location: {local_output_path}")
    except Exception as e:
        # For any other file-related errors, also use temporary file
        print(f"Error saving to {local_output_path}: {str(e)}. Using temporary file instead.")
        temp_dir = tempfile.gettempdir()
        local_output_path = os.path.join(temp_dir, COMBINED_FILE_NAME)
        final_df.to_csv(local_output_path, index=False, encoding='utf-8')
        print(f"Cleaned file saved to temporary location: {local_output_path}")
    
    # Upload to S3
    try:
        hook = S3Hook(aws_conn_id=AWS_CONN_ID)
        hook.load_file(
            filename=local_output_path,
            key=COMBINED_FILE_NAME,
            bucket_name=BUCKET_NAME,
            replace=True,
        )
        print(f"Cleaned file uploaded to S3: s3://{BUCKET_NAME}/{COMBINED_FILE_NAME}")
    except Exception as e:
        print(f"Error uploading to S3: {str(e)}")
        # Continue execution even if S3 upload fails
        print("Continuing execution despite S3 upload failure...")
    
    # Return summary statistics
    summary = {
        "total_rows": len(final_df),
        "languages": list(final_df['Language'].unique()),
        "total_languages": len(final_df['Language'].unique()),
        "columns": list(final_df.columns),
        "output_file": COMBINED_FILE_NAME
    }
    
    print("Summary:", summary)
    return summary

with DAG(
    dag_id="combine_multilingual_data",
    start_date=datetime(2023, 1, 1),
    schedule=None,  # Manual trigger only
    catchup=False,
    tags=["s3", "combine", "multilingual", "data-processing"],
    description="Combine all multilingual MMLU files into one unified dataset",
) as dag:
    
    combine_task = PythonOperator(
        task_id="combine_multilingual_files",
        python_callable=combine_multilingual_data,
    )
