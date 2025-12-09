# Apache Airflow Setup Guide

This guide will help you set up and run Apache Airflow using Docker Compose on Windows.

## Prerequisites

- Docker Desktop installed and running
- PowerShell or Command Prompt

## Quick Start

### 1. Clean Up Previous Setup
```powershell
# Stop and remove any old containers & volumes
docker-compose down -v
```

### 2. Pull Latest Images
```powershell
# Pull the latest images (ensures your airflow/postgres/redis images are up to date)
docker-compose pull
```

### 3. Initialize Database
```powershell
# Run the init service once (this will upgrade the DB and create the admin user)
docker-compose up airflow-init
```

**Important**: Let it run until you see logs ending with:
```
airflow already exist in the db
2.4.2
```

Then press `Ctrl+C` after it finishes. This means init succeeded.

### 4. Start Full Airflow Stack
```powershell
# Start the full stack in detached mode
docker-compose up -d
```

### 5. Verify Services Are Running
```powershell
# Check that all services are running
docker-compose ps
```

**Expected output:**
- `airflow-init` → `Exited (0)`
- `airflow-webserver`, `airflow-scheduler`, `airflow-worker`, `airflow-triggerer`, `postgres`, `redis` → `Up` (and healthy after ~1 min)

## Access Airflow Web UI

🌐 **Open your browser and go to:** http://localhost:8080

**Login credentials:**
- **Username:** `airflow`
- **Password:** `airflow`

## Project Structure

```
E:\Materials\
├── dags/                           # Your Airflow DAGs go here
│   ├── upload_data_to_s3.py       # Upload individual CSV files to S3
│   ├── combine_multilingual_data.py # Combine multilingual data
│   ├── master_pipeline.py         # Orchestrates the complete pipeline
│   └── snowflake_etl_pipeline.py  # Snowflake ETL with data cleaning
├── data/                           # Data files (multilingual MMLU datasets)
├── logs/                           # Airflow logs
├── plugins/                        # Custom Airflow plugins
├── docker-compose.yaml             # Docker Compose configuration
├── README.md                       # This file
└── SNOWFLAKE_SETUP.md             # Snowflake setup guide
```

## Available Services

| Service | Port | Description |
|---------|------|-------------|
| airflow-webserver | 8080 | Web UI for Airflow |
| airflow-scheduler | - | Schedules and monitors DAGs |
| airflow-worker | - | Executes tasks |
| airflow-triggerer | - | Handles deferred tasks |
| postgres | 5432 | Database backend |
| redis | 6379 | Message broker |

## Useful Commands

### View Logs
```powershell
# View logs for all services
docker-compose logs

# View logs for specific service
docker-compose logs airflow-webserver
docker-compose logs airflow-scheduler
```

### Stop Airflow
```powershell
# Stop all services
docker-compose down

# Stop and remove volumes (clears database)
docker-compose down -v
```

### Restart Services
```powershell
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart airflow-webserver
```

### Access Airflow CLI
```powershell
# Run Airflow CLI commands
docker-compose run --rm airflow-cli airflow dags list
docker-compose run --rm airflow-cli airflow tasks list <dag_id>
docker-compose run --rm airflow-cli airflow dags state master_pipeline

# Unpause DAGs (required before running)
docker-compose run --rm airflow-cli airflow dags unpause master_pipeline
docker-compose run --rm airflow-cli airflow dags unpause snowflake_etl_pipeline

# Trigger DAGs manually
docker-compose run --rm airflow-cli airflow dags trigger master_pipeline
docker-compose run --rm airflow-cli airflow dags trigger snowflake_etl_pipeline
```

## Troubleshooting

### Issue: Init container keeps restarting
**Solution**: The init container should have `restart: "no"` in the docker-compose.yaml file. This ensures it runs once and exits.

### Issue: Permission errors on Windows
**Solution**: The configuration has been optimized for Windows. The `chown` commands are skipped to avoid permission issues.

### Issue: Services show as unhealthy
**Solution**: Wait 1-2 minutes for services to fully initialize. Check logs with `docker-compose logs <service-name>`.

### Issue: Cannot access http://localhost:8080
**Solution**: 
1. Ensure Docker Desktop is running
2. Check if port 8080 is available: `netstat -an | findstr 8080`
3. Verify webserver is running: `docker-compose ps`

## Adding Your Own DAGs

1. Place your Python DAG files in the `dags/` directory
2. Airflow will automatically detect and load them
3. Refresh the web UI to see your new DAGs

## Available DAGs

Your project includes a complete data pipeline with the following DAGs:

### 1. `upload_data_to_s3.py`
- Uploads individual multilingual CSV files to S3 bucket
- Processes files from the local `data/` directory

### 2. `combine_multilingual_data.py`
- Combines all language-specific CSV files into a single dataset
- Applies encoding fixes and adds language metadata
- Uploads the combined file to S3

### 3. `snowflake_etl_pipeline.py`
- Downloads combined data from S3
- Performs comprehensive data cleaning and validation
- Loads cleaned data into Snowflake database
- Includes outlier detection, deduplication, and quality scoring

### 4. `master_pipeline.py`
- Orchestrates the complete pipeline in sequence
- Triggers all other DAGs and waits for completion
- Provides end-to-end automation

## Snowflake Integration

For Snowflake setup and configuration, see the detailed guide in `SNOWFLAKE_SETUP.md`. This includes:
- Database and schema creation
- User permissions setup
- Airflow connection configuration
- Data quality features and monitoring

## Support

For issues with this setup:
1. Check the logs: `docker-compose logs`
2. Verify Docker Desktop is running
3. Ensure no other services are using port 8080
4. Try the clean setup process again

---

**Happy Airflowing! 🚀**
