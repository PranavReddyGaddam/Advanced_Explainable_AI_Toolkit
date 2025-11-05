# Snowflake Setup Guide for Airflow ETL Pipeline

This guide will help you set up Snowflake connection and configure the ETL pipeline to load multilingual MMLU data into your Snowflake database.

## Prerequisites

1. **Snowflake Account**: You need access to a Snowflake account
2. **Database & Schema**: Create the target database and schema in Snowflake
3. **User & Permissions**: Create a dedicated user with appropriate permissions
4. **Airflow Connection**: Configure the Snowflake connection in Airflow

## Step 1: Create Snowflake Database and Schema

Connect to your Snowflake account and run the following SQL:

```sql
-- Create the database
CREATE DATABASE IF NOT EXISTS ANALYTICS_DB;

-- Create the schema
CREATE SCHEMA IF NOT EXISTS ANALYTICS_DB.CURATED;

-- Verify the setup
SHOW DATABASES;
SHOW SCHEMAS IN DATABASE ANALYTICS_DB;
```

## Step 2: Create Snowflake User and Role

```sql
-- Create a dedicated role for ETL operations
CREATE ROLE IF NOT EXISTS ETL_ROLE;

-- Create a user for Airflow ETL
CREATE USER IF NOT EXISTS airflow_etl_user
    PASSWORD = 'your_secure_password_here'
    DEFAULT_ROLE = ETL_ROLE
    DEFAULT_WAREHOUSE = COMPUTE_WH
    DEFAULT_NAMESPACE = ANALYTICS_DB.CURATED;

-- Grant necessary privileges to the role
GRANT USAGE ON DATABASE ANALYTICS_DB TO ROLE ETL_ROLE;
GRANT USAGE ON SCHEMA ANALYTICS_DB.CURATED TO ROLE ETL_ROLE;
GRANT CREATE TABLE ON SCHEMA ANALYTICS_DB.CURATED TO ROLE ETL_ROLE;
GRANT CREATE STAGE ON SCHEMA ANALYTICS_DB.CURATED TO ROLE ETL_ROLE;
GRANT CREATE FILE FORMAT ON SCHEMA ANALYTICS_DB.CURATED TO ROLE ETL_ROLE;

-- Grant table privileges
GRANT SELECT, INSERT, UPDATE, DELETE ON FUTURE TABLES IN SCHEMA ANALYTICS_DB.CURATED TO ROLE ETL_ROLE;

-- Assign role to user
GRANT ROLE ETL_ROLE TO USER airflow_etl_user;

-- Verify the setup
SHOW USERS;
SHOW ROLES;
SHOW GRANTS TO ROLE ETL_ROLE;
```

## Step 3: Configure Airflow Connection

### Option A: Using Airflow Web UI

1. Go to **Admin** → **Connections** in the Airflow web UI
2. Click **+** to add a new connection
3. Fill in the connection details:

```
Connection Id: snowflake_default
Connection Type: Snowflake
Host: your_account.snowflakecomputing.com
Schema: CURATED
Login: airflow_etl_user
Password: your_secure_password_here
Database: ANALYTICS_DB
Warehouse: COMPUTE_WH
Role: ETL_ROLE
```

### Option B: Using Airflow CLI

```bash
docker-compose run --rm airflow-cli airflow connections add snowflake_default \
    --conn-type snowflake \
    --conn-host your_account.snowflakecomputing.com \
    --conn-schema CURATED \
    --conn-login airflow_etl_user \
    --conn-password your_secure_password_here \
    --conn-extra '{"database": "ANALYTICS_DB", "warehouse": "COMPUTE_WH", "role": "ETL_ROLE"}'
```

## Step 4: Install Required Python Packages

Add the Snowflake provider to your Airflow installation:

```bash
# Add to your docker-compose.yaml environment
_PIP_ADDITIONAL_REQUIREMENTS: 'apache-airflow-providers-snowflake[common.sql]'
```

Or install manually:

```bash
docker-compose run --rm airflow-cli pip install apache-airflow-providers-snowflake[common.sql]
```

## Step 5: Verify Connection

Test the Snowflake connection:

```bash
docker-compose run --rm airflow-cli airflow connections test snowflake_default
```

## Step 6: Run the ETL Pipeline

### Unpause the DAGs

```bash
docker-compose run --rm airflow-cli airflow dags unpause snowflake_etl_pipeline
docker-compose run --rm airflow-cli airflow dags unpause master_pipeline
```

### Trigger the Pipeline

```bash
# Run the complete pipeline (S3 → Combine → Snowflake)
docker-compose run --rm airflow-cli airflow dags trigger master_pipeline

# Or run just the Snowflake ETL
docker-compose run --rm airflow-cli airflow dags trigger snowflake_etl_pipeline
```

## Data Quality Features

The ETL pipeline includes comprehensive data quality checks:

### 1. **Data Cleaning**
- **Missing Values**: 
  - Text columns → "Unknown"
  - Numeric columns → Median values
- **Type Casting**: Automatic conversion to proper data types
- **Timestamp Parsing**: ISO-8601 format validation

### 2. **Data Validation**
- **Deduplication**: Based on `user_id` + `ts` combination
- **Outlier Detection**: IQR method with configurable threshold
- **Range Validation**: Score (0-100), Difficulty (1-10), etc.
- **Constraint Enforcement**: NOT NULL, CHECK constraints

### 3. **Data Enrichment**
- **Quality Scores**: Based on data completeness and outlier status
- **Processing Metadata**: ETL timestamps and batch IDs
- **Language Distribution**: Automatic language categorization

### 4. **Snowflake Schema**

The target table includes:

```sql
CREATE TABLE ANALYTICS_DB.CURATED.MMLU_MULTILINGUAL_DATA (
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    explanation TEXT,
    score NUMBER(10,2) CHECK (score >= 0 AND score <= 100),
    difficulty NUMBER(10,2) CHECK (difficulty >= 1 AND difficulty <= 10),
    Language VARCHAR(50) NOT NULL,
    Source_File VARCHAR(100) NOT NULL,
    Combined_Date TIMESTAMP_NTZ NOT NULL,
    Total_Languages NUMBER(10,0) CHECK (Total_Languages > 0),
    user_id NUMBER(20,0) NOT NULL,
    ts TIMESTAMP_NTZ NOT NULL,
    is_outlier BOOLEAN DEFAULT FALSE,
    data_quality_score NUMBER(3,2) CHECK (data_quality_score >= 0 AND data_quality_score <= 1),
    etl_processed_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    etl_batch_id VARCHAR(100),
    
    -- Constraints
    CONSTRAINT unique_user_timestamp UNIQUE (user_id, ts),
    CONSTRAINT valid_timestamp CHECK (ts >= '2020-01-01'::TIMESTAMP_NTZ)
);
```

## Monitoring and Troubleshooting

### Check Pipeline Status

```bash
# Check DAG status
docker-compose run --rm airflow-cli airflow dags state snowflake_etl_pipeline

# View task logs
docker-compose run --rm airflow-cli airflow tasks logs snowflake_etl_pipeline clean_and_validate_data
```

### Verify Data in Snowflake

```sql
-- Check total rows
SELECT COUNT(*) FROM ANALYTICS_DB.CURATED.MMLU_MULTILINGUAL_DATA;

-- Check data quality
SELECT 
    Language,
    COUNT(*) as count,
    AVG(data_quality_score) as avg_quality,
    SUM(CASE WHEN is_outlier THEN 1 ELSE 0 END) as outliers
FROM ANALYTICS_DB.CURATED.MMLU_MULTILINGUAL_DATA
GROUP BY Language;

-- Check recent loads
SELECT 
    etl_batch_id,
    COUNT(*) as rows_loaded,
    MIN(etl_processed_at) as load_start,
    MAX(etl_processed_at) as load_end
FROM ANALYTICS_DB.CURATED.MMLU_MULTILINGUAL_DATA
GROUP BY etl_batch_id
ORDER BY load_start DESC;
```

## Security Best Practices

1. **Use Strong Passwords**: Generate secure passwords for database users
2. **Principle of Least Privilege**: Only grant necessary permissions
3. **Network Security**: Use Snowflake's IP whitelist if needed
4. **Audit Logging**: Enable Snowflake audit logs
5. **Key Rotation**: Regularly rotate user passwords

## Performance Optimization

1. **Warehouse Sizing**: Use appropriate warehouse size for your data volume
2. **Batch Processing**: Process data in reasonable batch sizes
3. **Indexing**: Consider creating indexes on frequently queried columns
4. **Clustering**: Use clustering keys for large tables

## Support

For issues with the Snowflake ETL pipeline:

1. Check Airflow logs: `docker-compose logs airflow-scheduler`
2. Verify Snowflake connection: `airflow connections test snowflake_default`
3. Check Snowflake query history in the web UI
4. Review the data quality reports in the pipeline logs

---

**Your multilingual MMLU data is now ready for analytics in Snowflake! 🚀**
