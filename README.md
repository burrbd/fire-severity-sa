# 🔥 Fire Severity Mapping — South Australia

[![Tests](https://github.com/burrbd/fire-severity-sa/workflows/Tests/badge.svg)](https://github.com/burrbd/fire-severity-sa/actions)
[![Coverage](https://codecov.io/gh/burrbd/fire-severity-sa/branch/main/graph/badge.svg)](https://codecov.io/gh/burrbd/fire-severity-sa)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An open, automated mapping pipeline to generate and publish **fire severity maps** (dNBR) for South Australian wildfires and prescribed burns.

## 🎯 Purpose

Generate and publish fire severity maps for South Australian wildfires using a clean, scalable architecture with cloud storage and database persistence.

## 🏗️ Architecture Overview

### **Clean Separation of Concerns:**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Generators    │    │   Analysis       │    │   Publishers    │
│                 │    │   Service        │    │                 │
│ • Kick off      │───▶│ • Store/Retrieve │───▶│ • Upload to S3  │
│   analysis      │    │   metadata       │    │ • Generate PNG  │
│ • Return        │    │ • Database ops   │    │ • Extract bounds│
│   Analysis obj  │    │ • Single DB      │    │ • Make available│
│                 │    │   access point   │    │   for maps      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### **Core Components:**

1. **`DNBRAnalysis`** - Concrete metadata class (ULID, status, raster_urls, generator_type)
2. **`AnalysisService`** - Single point of database access (DynamoDB) with dependency injection
3. **`AnalysisPublisher`** - Handles S3 uploads and data processing
4. **Generators** - Kick off analysis and create metadata objects (dummy, GEE)

### **Data Flow:**
1. **Generate** → Creates analysis metadata with generator type
2. **Store** → Saves to DynamoDB via AnalysisService
3. **Publish** → Uploads data to S3 via AnalysisPublisher
4. **Map** → Reads from S3 URLs for visualization

## 📍 Current Implementation Status

### ✅ **Completed:**
- **Clean Architecture** - Single `DNBRAnalysis` class with generator type metadata
- **DynamoDB Integration** - Full implementation with dependency injection
- **Generator Simplification** - Dummy and GEE generators return clean Analysis objects
- **100% Test Coverage** - Core business logic fully tested

### 🔄 **In Progress:**
- **S3 Integration** - AnalysisPublisher ready for implementation

### 📋 **Next Steps:**
1. **S3 Integration** - Complete AnalysisPublisher implementation
2. **GEE Integration** - Replace dummy generator with real GEE analysis
3. **Production Deployment** - Move from development to production environment

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
  --table-name fire-severity-analyses-dev \
  --attribute-definitions AttributeName=analysis_id,AttributeType=S \
  --key-schema AttributeName=analysis_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region ap-southeast-2
```

### Run Analysis (Current - DynamoDB)
```bash
# Generate analysis (creates metadata, stores in DynamoDB)
python scripts/generate_dnbr_analysis.py data/fire.geojson dummy

# Download data and generate map (retrieves from DynamoDB)
python scripts/download_dnbr_analysis.py --analysis-id <ANALYSIS_ID>
```

### View Results
Open `docs/outputs/fire_severity_map.html` in your browser.

## 🧪 Testing

### Run Tests
```bash
python -m pytest tests/ -v --cov=dnbr --cov=scripts
```

### Test Coverage
- **Core `dnbr` module: 100%** ✅
- **Main script: 100%** ✅
- **Overall coverage: 79%** ✅
- **All tests passing** ✅

### Coverage Breakdown:
- **`analysis.py`**: 100% - Metadata class fully tested
- **`analysis_service.py`**: 100% - DynamoDB operations fully tested
- **`dummy_generator.py`**: 100% - Dummy generator fully tested
- **`gee_generator.py`**: 100% - GEE generator fully tested
- **`generators.py`**: 100% - Factory functions fully tested
- **`publisher.py`**: 100% - Publisher interface fully tested
- **`generate_dnbr_analysis.py`**: 100% - Main script fully tested

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
│   ├── analysis.py         # DNBRAnalysis concrete class (metadata + generator_type)
│   ├── analysis_service.py # DynamoDB operations (complete implementation)
│   ├── publisher.py        # S3 publishing (shell)
│   ├── dummy_generator.py  # Dummy analysis generator
│   ├── gee_generator.py    # GEE analysis generator
│   └── generators.py       # Factory functions
├── scripts/                # GitHub Actions entry points
│   ├── generate_dnbr_analysis.py    # Analysis generation + DynamoDB storage
│   ├── download_dnbr_analysis.py    # Data download & map generation
│   ├── generate_map_shell.py        # Map generation
│   ├── generate_dnbr_utils.py       # Raster processing utilities
│   └── generate_leaflet_utils.py    # Map generation utilities
├── data/                   # Input data
│   ├── fire.geojson        # Area of interest
│   └── dummy/              # Test data
│       └── fire_severity.tif
├── docs/                   # Documentation and outputs
│   ├── index.html         # GitHub Pages site
│   └── outputs/           # Generated outputs
│       ├── fire_severity_overlay.png
│       └── fire_severity_map.html
├── .github/               # GitHub Actions
│   └── workflows/
│       ├── generate-pages.yml
│       ├── generate_dnbr_analysis.yml
│       └── download_dnbr_analysis.yml
├── tests/                 # Test suite
│   ├── test_analysis_metadata.py
│   ├── test_analysis_service.py
│   ├── test_publisher.py
│   ├── test_generators.py
│   └── test_scripts.py
├── requirements.txt       # Python dependencies
├── pytest.ini           # Test configuration
└── README.md
```

## 🔄 Development Workflow

### **Current Architecture:**
1. **Analysis Generation** → Creates metadata, stores in DynamoDB
2. **Data Download** → Retrieves from DynamoDB, generates maps
3. **Map Generation** → Creates Leaflet visualization

### **Target Architecture:**
1. **Analysis Generation** → Creates metadata, stores in DynamoDB
2. **Data Publishing** → Uploads to S3, updates metadata
3. **Map Generation** → Reads from S3 URLs

## 🔧 Technical Details

### **DynamoDB Schema:**
```json
{
  "analysis_id": "string (ULID)",
  "status": "string (PENDING|COMPLETED|FAILED)",
  "generator_type": "string (dummy|gee)",
  "raster_urls": ["string"],
  "created_at": "string (ISO timestamp)",
  "updated_at": "string (ISO timestamp)"
}
```

### **AWS Authentication:**
- GitHub Actions uses AWS credentials from repository secrets
- Local development uses AWS CLI configuration
- IAM user requires DynamoDB and S3 permissions

### **Generator Types:**
- **`dummy`** - Test/development analysis with no real processing
- **`gee`** - Google Earth Engine analysis (placeholder for real implementation)

## 📝 License

MIT License - see LICENSE file for details.
