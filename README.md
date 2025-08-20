# 🔥 Fire Severity Mapping — South Australia

[![Tests](https://github.com/burrbd/fire-severity-sa/workflows/Tests/badge.svg)](https://github.com/burrbd/fire-severity-sa/actions)
[![Coverage](https://codecov.io/gh/burrbd/fire-severity-sa/branch/main/graph/badge.svg)](https://codecov.io/gh/burrbd/fire-severity-sa)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An open, automated mapping pipeline to generate and publish **fire severity maps** (dNBR) for South Australian wildfires and prescribed burns.

## 🎯 Purpose

Deliver accessible fire severity data for researchers, agencies, and the public

## 📍 Current Milestone: Map v1

> A minimal working pipeline that processes one fire scar, produces a dummy raster via GitHub Actions, and displays it on a Leaflet map. This is a "steel rod" prototype.

### 🧱 Epics & Stories

#### 1. **Steel Rod Pipeline** *(end-to-end test harness)*
- [x] Create dummy AOI GeoJSON
- [x] Build `process_aoi.py` that takes AOI path
- [x] Set up GitHub Action to invoke script with input
- [x] Output placeholder raster
- [x] Visualise in Leaflet
- [x] Document in README
- [x] Add comprehensive test suite with 100% coverage

#### 2. **Earth Engine Pipeline** *(actual processing pipeline)*
- [x] **GEE Job Management System** - ULID-based job tracking with S3
- [x] **Manual GEE Job Submission** - GitHub Actions workflow for submitting jobs
- [ ] **GEE Authentication & Setup** - Configure Earth Engine API access
- [ ] **AOI Loading to GEE** - Convert GeoJSON to GEE FeatureCollection
- [ ] **Mock dNBR Generation** - Use elevation data as proxy for dNBR
- [ ] **GEE Export Pipeline** - Async job submission and status tracking
- [ ] **Job Status Monitoring** - Check and download completed GEE jobs
- [ ] **Real dNBR Calculation** - Replace mock with actual pre/post-fire analysis
- [ ] **Cloud Masking & Image Selection** - Automated satellite image processing
- [ ] **Severity Classification** - Classify dNBR values into severity zones

#### 3. **Export and Visualisation**
- [ ] Export processed raster (e.g. GeoTIFF)
- [ ] Render real output in Leaflet map

#### 4. **Documentation**
- [ ] Write Substack article explaining method and impact

## 🔄 Current Workflow & Next Steps

### **Current State (Phase 1: Manual GEE Integration)**
We've implemented a **dual-branch deployment strategy** with manual GEE job submission:

#### **Workflow Components:**
1. **Job Tracking System** - ULID-based job IDs with S3 storage
2. **Manual Job Submission** - GitHub Actions workflow for submitting GEE jobs
3. **Noop Functions** - Placeholder implementations for testing workflow structure

#### **Current Workflows:**
- **`generate-pages.yml`** - Updates GitHub Pages with existing data (automatic)
- **`submit-gee-job.yml`** - Manual GEE job submission (manual trigger)

#### **Job Tracking:**
- **ULIDs** for unique, sortable job identification
- **S3 storage** for job metadata (avoiding Git conflicts)
- **Audit trail** linking jobs to commit hashes and timestamps

### **Next Steps (Phase 2: Real GEE Integration)**
1. **Replace noop functions** with actual GEE API calls
2. **Implement S3 job tracking** (currently noop)
3. **Add GEE authentication** to GitHub Actions
4. **Create mock dNBR** using elevation data
5. **Test async job submission** and status monitoring

### **Future Automation (Phase 3: Full Pipeline)**
1. **Daily job status checking** workflow
2. **Automatic job triggering** on new fire data
3. **Real dNBR calculation** with satellite imagery
4. **Automated map updates** when jobs complete

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Git

### Setup
```bash
# Clone the repository
git clone https://github.com/burrbd/fire-severity-sa.git
cd fire-severity-sa

# Install dependencies
pip install -r requirements.txt

# Set up pre-commit hooks (optional but recommended)
./setup-pre-commit.sh

# Run the steel rod pipeline
python __main__.py data/fire.geojson
```

### View Results
Open `outputs/fire_severity_map.html` in your browser to see the Leaflet visualization.

## 🧪 Testing

This project includes comprehensive tests with 100% code coverage.

### Run Tests
```bash
# Run all tests with coverage
python -m pytest tests/ -v --cov=src --cov-report=term-missing

# Run specific test
python -m pytest tests/test_process_aoi.py::TestGenerateDNBRRaster::test_generate_dnbr_raster_success -v

# Generate HTML coverage report
python -m pytest tests/ --cov=src --cov-report=html
```

### Test Coverage
- **100% code coverage** required for all source files
- Tests cover all functions, edge cases, and error conditions
- Integration tests verify the complete pipeline
- Mock tests ensure isolated unit testing

### Pre-commit Hooks
This project includes pre-commit hooks that automatically run tests before each commit:
- Tests must pass before commits are allowed
- Ensures code quality and prevents broken commits
- Runs the same test suite as CI/CD pipeline
- **100% code coverage required** - commits will fail if coverage drops below 100%

To set up pre-commit hooks:
```bash
./setup-pre-commit.sh
```

To skip pre-commit hooks (not recommended):
```bash
git commit --no-verify -m "your message"
```

## 📁 Project Structure

```
fire-severity-sa/
├── data/                   # Input data (AOI files, etc.)
│   └── fire.geojson  # Real fire area of interest
├── src/                    # Source code
│   ├── process_aoi.py      # Main processing pipeline
│   └── gee_jobs.py         # GEE job management and tracking
├── docs/                   # Documentation and outputs
│   ├── index.html         # Main GitHub Pages site
│   └── outputs/           # Generated outputs (auto-committed to gh-pages)
│       ├── fire_severity.tif  # Raster output
│       ├── fire_severity_overlay.png  # Image overlay
│       └── fire_severity_map.html  # Leaflet visualization
├── .github/               # GitHub Actions
│   └── workflows/
│       ├── generate-pages.yml  # Main deployment workflow
│       └── submit-gee-job.yml  # Manual GEE job submission
├── tests/                 # Test suite
│   ├── test_process_aoi.py
│   └── test_gee_jobs.py   # GEE job management tests
├── requirements.txt       # Python dependencies
├── requirements.in        # Source dependencies for pip-tools
├── pytest.ini           # Test configuration
└── README.md
```

## 🔄 Future Direction

- Automate detection of new fires (e.g. via SA Gov shapefiles)
- Use GEE REST API to remove manual steps
- Expand to fire history/temporal analysis

## 📝 License

MIT License - see LICENSE file for details.
