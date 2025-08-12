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
- [ ] Load AOI into GEE as FeatureCollection
- [ ] Select pre- and post-fire satellite images
- [ ] Apply cloud masks
- [ ] Calculate NBR and dNBR
- [ ] Classify severity zones

#### 3. **Export and Visualisation**
- [ ] Export processed raster (e.g. GeoTIFF)
- [ ] Render real output in Leaflet map

#### 4. **Documentation**
- [ ] Write Substack article explaining method and impact

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

# Run the steel rod pipeline
python src/process_aoi.py data/fire.geojson
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

## 📁 Project Structure

```
fire-severity-sa/
├── data/                   # Input data (AOI files, etc.)
│   └── fire.geojson  # Real fire area of interest
├── src/                    # Source code
│   └── process_aoi.py
├── outputs/               # Generated outputs
│   ├── fire_severity.tif  # Raster output
│   └── fire_severity_map.html  # Leaflet visualization
├── .github/               # GitHub Actions
│   └── workflows/
│       └── process_fire.yml
├── tests/                 # Test suite
│   └── test_process_aoi.py
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
