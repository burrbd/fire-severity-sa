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

1. **`DNBRAnalysis`** - Pure metadata class (ULID, status, raster_urls)
2. **`AnalysisService`** - Single point of database access (DynamoDB)
3. **`AnalysisPublisher`** - Handles S3 uploads and data processing
4. **Generators** - Kick off analysis and create metadata objects

### **Data Flow:**
1. **Generate** → Creates analysis metadata
2. **Store** → Saves to DynamoDB via AnalysisService
3. **Publish** → Uploads data to S3 via AnalysisPublisher
4. **Map** → Reads from S3 URLs for visualization

## 📍 Current Implementation Status

### ✅ **Completed:**
- **Clean Architecture** - Simplified to single `DNBRAnalysis` class
- **Infrastructure-Agnostic** - `raster_urls` not tied to specific storage
- **AnalysisService** - Shell implementation ready for DynamoDB
- **AnalysisPublisher** - Shell implementation ready for S3
- **Comprehensive Tests** - Tests passing with clean coverage
- **GitHub Actions** - Automated workflows for analysis generation

### 🔄 **In Progress:**
- **DynamoDB Integration** - AnalysisService ready for implementation
- **S3 Integration** - AnalysisPublisher ready for implementation

### 📋 **Next Steps:**
1. **AWS Setup** - Configure DynamoDB table and S3 bucket
2. **Implement DynamoDB** - Complete AnalysisService methods
3. **Implement S3** - Complete AnalysisPublisher methods
4. **Update GitHub Actions** - Use new services instead of local files
5. **GEE Integration** - Replace dummy generator with real GEE analysis

## 🚀 Quick Start

### Setup
```bash
git clone https://github.com/burrbd/fire-severity-sa.git
cd fire-severity-sa
pip install -r requirements.txt
```

### Run Analysis (Current - Local Files)
```bash
# Generate analysis (creates metadata, stores locally)
python scripts/generate_dnbr_analysis.py data/fire.geojson dummy

# Download data and generate map (uses local files)
python scripts/download_dnbr_analysis.py --analysis-id <ANALYSIS_ID> --generator-type dummy
```

### View Results
Open `docs/outputs/fire_severity_map.html` in your browser.

## 🧪 Testing

### Run Tests
```bash
python -m pytest tests/ -v --cov=dnbr --cov=scripts
```

### Test Coverage
- **Tests passing** ✅
- **Core architecture** - Analysis, Service, Publisher
- **Script integration** - GitHub Actions workflows
- **Map generation** - Leaflet visualization

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
│   ├── analysis.py         # DNBRAnalysis ABC (metadata only)
│   ├── analysis_service.py # DynamoDB operations (shell)
│   ├── publisher.py        # S3 publishing (shell)
│   └── generators.py       # Analysis generation (legacy)
├── scripts/                # GitHub Actions entry points
│   ├── generate_dnbr_analysis.py    # Analysis generation
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
│   ├── test_generate_dnbr.py
│   └── test_scripts.py
├── requirements.txt       # Python dependencies
├── pytest.ini           # Test configuration
└── README.md
```

## 🔄 Development Workflow

### **Current Architecture:**
1. **Analysis Generation** → Creates metadata, stores locally
2. **Data Download** → Reads local files, generates maps
3. **Map Generation** → Creates Leaflet visualization

### **Target Architecture:**
1. **Analysis Generation** → Creates metadata, stores in DynamoDB
2. **Data Publishing** → Uploads to S3, updates metadata
3. **Map Generation** → Reads from S3 URLs



## 📝 License

MIT License - see LICENSE file for details.
