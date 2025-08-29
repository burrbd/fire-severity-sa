# 🔥 Fire Severity Mapping — South Australia

[![Tests](https://github.com/burrbd/fire-severity-sa/workflows/Tests/badge.svg)](https://github.com/burrbd/fire-severity-sa/actions)
[![Coverage](https://codecov.io/gh/burrbd/fire-severity-sa/branch/main/graph/badge.svg)](https://codecov.io/gh/burrbd/fire-severity-sa)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An open, automated mapping pipeline to generate and publish **fire severity maps** (dNBR) for South Australian wildfires and prescribed burns.

## 🎯 Purpose

Generate and publish fire severity maps for South Australian wildfires using a clean, scalable architecture with cloud storage and database persistence.

## 🏗️ Architecture Overview

### **Job-Based Polymorphic Architecture:**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Job Classes   │    │   Job Service    │    │   Publishers    │
│                 │    │                  │    │                 │
│ • DummyJob      │───▶│ • Store/Retrieve │───▶│ • Upload to S3  │
│ • GEEJob        │    │   jobs           │    │ • Generate STAC │
│ • execute()     │    │ • CRUD ops       │    │ • Make available│
│   returns Job   │    │ • Single DB      │    │   for maps      │
│                 │    │   access point   │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### **Core Components:**

1. **`DNBRAnalysisJob`** - Batch job containing multiple analyses with single ULID
2. **`Job` (Abstract)** - Polymorphic job classes (DummyJob, GEEJob) with execute() method
3. **`JobService`** - Simple CRUD operations for job storage (DynamoDB)
4. **`DNBRAnalysis`** - Individual analysis objects within a job
5. **`S3AnalysisPublisher`** - Handles S3 uploads with STAC structure

### **Data Flow:**
1. **Execute Job** → Creates job with multiple analyses for batch processing
2. **Store Job** → Saves to DynamoDB via JobService
3. **Publish Job** → Uploads all analyses to S3 with STAC metadata
4. **Map** → Reads from S3 URLs for visualization

## 📍 Current Implementation Status

### ✅ **Completed:**
- **Job-Based Architecture** - Polymorphic job classes with batch processing
- **DynamoDB Integration** - JobService with simple CRUD operations
- **S3 Integration** - Complete STAC-compliant publishing with job-based structure
- **GitHub Actions** - Automated job execution and publishing workflows
- **89% Test Coverage** - Comprehensive behavior-focused testing

### 🔄 **In Progress:**
- **STAC API Lambda** - Serverless API for querying published data

### 📋 **Next Steps:**
1. **STAC API Lambda** - Create serverless API for data discovery
2. **TiTiler Integration** - Dynamic COG tiling for map visualization
3. **Frontend Development** - Simple web interface for data exploration
4. **GEE Integration** - Replace dummy generator with real GEE analysis

## 🚀 Quick Start

### Setup
```bash
git clone https://github.com/burrbd/fire-severity-sa.git
cd fire-severity-sa
pip install -r requirements.txt
```

### AWS Configuration
```bash
# Configure AWS credentials
aws configure

# Create DynamoDB table (if not exists)
aws dynamodb create-table \
  --table-name fire-severity-jobs-dev \
  --attribute-definitions AttributeName=job_id,AttributeType=S \
  --key-schema AttributeName=job_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region ap-southeast-2
```

### Run Analysis (Job-Based)
```bash
# Execute job (creates job with multiple analyses, stores in DynamoDB)
python scripts/dnbr_analysis_job.py data/dummy_data/fires.geojson dummy

# Publish job to S3 (retrieves from DynamoDB, uploads to S3 with STAC)
python scripts/publish_dnbr_job.py --job-id <JOB_ID>
```

### GitHub Actions Workflow
1. **Execute dNBR Job** → Creates job with analyses
2. **Publish dNBR Job** → Publishes to S3 with STAC structure

## 🧪 Testing

### Run Tests
```bash
python -m pytest tests/ -v --cov=dnbr --cov-report=term-missing
```

### Pre-commit Hooks
Tests run automatically before commits. Set up with:
```bash
./setup-pre-commit.sh
```

## 📁 Project Structure

```
fire-severity-sa/
├── dnbr/                   # Core domain logic
│   ├── __init__.py
│   ├── analysis.py         # DNBRAnalysis class (individual analyses)
│   ├── job.py              # DNBRAnalysisJob class (batch jobs)
│   ├── jobs.py             # Polymorphic Job classes (DummyJob, GEEJob)
│   ├── job_service.py      # DynamoDB operations for jobs
│   ├── publisher.py        # S3 publishing with STAC structure
│   └── fire_metadata.py    # Fire metadata extraction
├── scripts/                # GitHub Actions entry points
│   ├── dnbr_analysis_job.py    # Job execution (replaces generate_dnbr_analysis.py)
│   ├── publish_dnbr_job.py     # Job publishing (replaces publish_dnbr_analysis.py)
│   ├── generate_map_shell.py   # Map generation
│   └── generate_dnbr_utils.py  # Raster processing utilities
├── data/                   # Input data
│   └── dummy_data/         # Test data
│       ├── fires.geojson   # Multiple AOIs (2 features)
│       ├── fire.geojson    # Single AOI (1 feature)
│       └── raw_dnbr.tif    # Dummy raster data
├── docs/                   # Documentation and outputs
│   ├── index.html         # GitHub Pages site
│   └── outputs/           # Generated outputs
├── .github/               # GitHub Actions
│   └── workflows/
│       ├── execute_dnbr_job.yml      # Job execution workflow
│       ├── publish_dnbr_job.yml      # Job publishing workflow
│       ├── generate_map_shell.yml    # Map generation
│       └── tests.yml                 # Test suite
├── tests/                 # Test suite
│   ├── test_analysis.py              # DNBRAnalysis tests
│   ├── test_job_execution.py         # Job execution tests
│   ├── test_job_service_integration.py # JobService integration tests
│   ├── test_job_status.py            # Job status tests
│   ├── test_publisher.py             # Publisher tests
│   ├── test_s3_integration.py        # S3 integration tests
│   └── test_scripts.py               # Script tests
├── requirements.txt       # Python dependencies
├── pytest.ini           # Test configuration
└── README.md
```

## 🔄 Development Workflow

### **Current Architecture:**
1. **Job Execution** → Creates job with multiple analyses, stores in DynamoDB
2. **Job Publishing** → Retrieves job, uploads analyses to S3 with STAC
3. **Map Generation** → Reads from S3 URLs for visualization

### **S3 Structure:**
```
s3://bucket/
├── jobs/
│   └── {job_id}/
│       ├── {aoi_id}/
│       │   ├── {aoi_id}_dnbr.cog.tif
│       │   └── {aoi_id}_aoi.geojson
│       └── {aoi_id2}/
│           ├── {aoi_id2}_dnbr.cog.tif
│           └── {aoi_id2}_aoi.geojson
└── stac/
    ├── collections/
    │   └── fires.json
    └── items/
        └── {job_id}/
            ├── {aoi_id}.json
            └── {aoi_id2}.json
```

## 🔧 Technical Details

### **DynamoDB Schema:**
```json
{
  "job_id": "string (ULID)",
  "generator_type": "string (dummy|gee)",
  "created_at": "string (ISO timestamp)",
  "updated_at": "string (ISO timestamp)",
  "analysis_count": "number",
  "analyses": "string (JSON array of analysis data)"
}
```

### **Job Types:**
- **`DummyJob`** - Synchronous test/development job with immediate completion
- **`GEEJob`** - Asynchronous Google Earth Engine job with pending status

### **Analysis Status:**
- **`PENDING`** - Analysis created, waiting for processing (GEE)
- **`COMPLETED`** - Analysis finished, ready for publishing
- **`FAILED`** - Analysis failed, needs investigation

### **AWS Authentication:**
- GitHub Actions uses AWS credentials from repository secrets
- Local development uses AWS CLI configuration
- IAM user requires DynamoDB and S3 permissions

## 🚀 Next Steps

### **Immediate:**
1. **STAC API Lambda** - Serverless API for data discovery
2. **TiTiler Integration** - Dynamic COG tiling for map visualization
3. **Simple Frontend** - Web interface for data exploration

### **Medium Term:**
1. **GEE Integration** - Real Google Earth Engine analysis
2. **Production Deployment** - Move from development to production
3. **Monitoring & Alerting** - Job status monitoring and notifications

### **Long Term:**
1. **Multi-Provider Support** - Support for different data providers
2. **Advanced Analytics** - Additional fire severity metrics
3. **Real-time Processing** - Near real-time fire severity mapping

## 📝 License

MIT License - see LICENSE file for details.
