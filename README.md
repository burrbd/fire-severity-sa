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
- [x] Build `generate_dnbr.py` that takes AOI path
- [x] Set up GitHub Action to invoke script with input
- [x] Output placeholder raster
- [x] Visualise in Leaflet
- [x] Document in README
- [x] Add comprehensive test suite with 100% coverage

#### 2. **Earth Engine Pipeline** *(actual processing pipeline)*
- [x] **Analysis Architecture** - Polymorphic dNBR analysis system (dummy/GEE)
- [x] **ULID-based Analysis IDs** - Unique, sortable analysis identification
- [x] **Manual Analysis Submission** - GitHub Actions workflow for generating analyses
- [x] **Dual-step Workflow** - Separate analysis generation and data download
- [ ] **GEE Authentication & Setup** - Configure Earth Engine API access
- [ ] **AOI Loading to GEE** - Convert GeoJSON to GEE FeatureCollection
- [ ] **Mock dNBR Generation** - Use elevation data as proxy for dNBR
- [ ] **GEE Export Pipeline** - Async analysis submission and status tracking
- [ ] **Analysis Status Monitoring** - Check and download completed GEE analyses
- [ ] **Real dNBR Calculation** - Replace mock with actual pre/post-fire analysis
- [ ] **Cloud Masking & Image Selection** - Automated satellite image processing
- [ ] **Severity Classification** - Classify dNBR values into severity zones

#### 3. **Export and Visualisation**
- [ ] Export processed raster (e.g. GeoTIFF)
- [ ] Render real output in Leaflet map

#### 4. **Documentation**
- [ ] Write Substack article explaining method and impact

## 🔄 Current Workflow & Next Steps

### **Current State (Phase 1: Analysis Architecture)**
We've implemented a **polymorphic analysis system** with clean separation of concerns:

#### **Architecture Components:**
1. **Analysis Domain** - `dnbr/` module with analysis and generator classes
2. **Scripts** - `scripts/` directory for GitHub Actions entry points
3. **Dummy Implementation** - Pre-committed raster data for testing
4. **GEE Implementation** - Placeholder for Google Earth Engine integration

#### **Current Workflows:**
- **`generate-pages.yml`** - Updates GitHub Pages HTML shell (automatic)
- **`generate-dnbr-job.yml`** - Manual analysis generation (manual trigger)
- **`download-dnbr-job.yml`** - Manual data download and map regeneration (manual trigger)

#### **Analysis Tracking:**
- **ULIDs** for unique, sortable analysis identification
- **Polymorphic design** supporting dummy and GEE implementations
- **Two-step workflow** for async analysis processing

### **Next Steps (Phase 2: Real GEE Integration)**
1. **Implement GEE authentication** in GitHub Actions
2. **Add real GEE processing** to `GEEAnalysis` and `GEEDNBRGenerator`
3. **Create mock dNBR** using elevation data for testing
4. **Test async analysis submission** and status monitoring
5. **Implement cloud storage** for GEE results

### **Future Automation (Phase 3: Full Pipeline)**
1. **Automatic analysis triggering** on new fire data
2. **Real dNBR calculation** with satellite imagery
3. **Automated map updates** when analyses complete

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

# Run the dNBR analysis pipeline
python __main__.py data/fire.geojson dummy

# Or run specific scripts
python scripts/generate_dnbr.py data/fire.geojson dummy
python scripts/download_data.py --analysis-id <ANALYSIS_ID> --generator-type dummy
```

### View Results
Open `outputs/fire_severity_map.html` in your browser to see the Leaflet visualization.

## 🧪 Testing

This project includes comprehensive tests with 100% code coverage.

### Run Tests
```bash
# Run all tests with coverage
python -m pytest tests/ -v --cov=dnbr --cov=scripts --cov-report=term-missing

# Run specific test
python -m pytest tests/test_generate_dnbr.py::TestDNBRAnalysis::test_generate_dnbr_dummy -v

# Generate HTML coverage report
python -m pytest tests/ --cov=dnbr --cov=scripts --cov-report=html
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
├── dnbr/                   # dNBR analysis domain
│   ├── __init__.py
│   ├── analysis.py         # DNBRAnalysis ABC
│   ├── dummy_analysis.py   # DummyAnalysis implementation
│   ├── gee_analysis.py     # GEEAnalysis implementation
│   ├── generators.py       # DNBRGenerator ABC + factories
│   ├── dummy_generator.py  # DummyDNBRGenerator
│   └── gee_generator.py    # GEEDNBRGenerator
├── scripts/                # GitHub Actions entry points
│   ├── generate_dnbr.py    # Main analysis generation script
│   ├── download_data.py    # Download and map regeneration script
│   ├── generate_map.py     # Map generation script
│   ├── generate_dnbr_utils.py # Legacy raster generation utilities
│   └── generate_leaflet_utils.py # Legacy map generation utilities
├── data/                   # Input data
│   ├── fire.geojson        # Real fire area of interest
│   └── dummy/              # Pre-committed dummy data
│       └── fire_severity.tif # Dummy raster for testing
├── docs/                   # Documentation and outputs
│   ├── index.html         # Main GitHub Pages site
│   └── outputs/           # Generated outputs (auto-committed to gh-pages)
│       ├── fire_severity_overlay.png  # Image overlay
│       └── fire_severity_map.html  # Leaflet visualization
├── .github/               # GitHub Actions
│   └── workflows/
│       ├── generate-pages.yml      # Main deployment workflow
│       ├── generate-dnbr-job.yml   # Manual analysis generation
│       └── download-dnbr-job.yml   # Manual data download
├── tests/                 # Test suite
│   └── test_generate_dnbr.py # Analysis and generator tests
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
