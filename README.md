# 🔥 Fire Severity Mapping — South Australia

[![Tests](https://github.com/burrbd/fire-severity-sa/workflows/Tests/badge.svg)](https://github.com/burrbd/fire-severity-sa/actions)
[![Coverage](https://codecov.io/gh/burrbd/fire-severity-sa/branch/main/graph/badge.svg)](https://codecov.io/gh/burrbd/fire-severity-sa)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An open, automated mapping pipeline to generate and publish **fire severity maps** (dNBR) for South Australian wildfires and prescribed burns.

## 🎯 Purpose

Generate and publish fire severity maps for South Australian wildfires.

## 📍 Current Milestone: Map v1

> A working pipeline that processes fire scars and displays results on a Leaflet map.

### 🧱 Epics & Stories

#### 1. **Basic Pipeline**
- [x] AOI processing and dummy raster generation
- [x] GitHub Actions automation
- [x] Leaflet visualization
- [x] Test suite

#### 2. **Earth Engine Pipeline**
- [x] Analysis architecture and job tracking
- [x] Manual analysis submission workflow
- [ ] GEE authentication and setup
- [ ] AOI processing in GEE
- [ ] dNBR calculation
- [ ] Cloud masking and image selection
- [ ] Severity classification

#### 3. **Documentation**
- [ ] Write article explaining method and impact

## 🔄 Current Workflow & Next Steps

### **Current State**
- **Analysis system** with dummy and GEE implementations
- **GitHub Actions workflows** for automation
- **ULID-based tracking** for analysis identification

### **Next Steps**
1. GEE authentication and setup
2. Real dNBR calculation with satellite imagery
3. Automated processing pipeline

## 🚀 Quick Start

### Setup
```bash
git clone https://github.com/burrbd/fire-severity-sa.git
cd fire-severity-sa
pip install -r requirements.txt

# Run analysis
python scripts/generate_dnbr_analysis.py data/fire.geojson dummy

# Or run other scripts (used by GitHub Actions)
python scripts/download_dnbr_analysis.py --analysis-id <ANALYSIS_ID> --generator-type dummy  # Download and regenerate map
```

### View Results
Open `docs/outputs/fire_severity_map.html` in your browser.

## 🧪 Testing

### Run Tests
```bash
python -m pytest tests/ -v --cov=dnbr --cov=scripts
```

### Pre-commit Hooks
Tests run automatically before commits. Set up with:
```bash
./setup-pre-commit.sh
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
│   ├── generate_dnbr_analysis.py    # Main analysis generation script
│   ├── download_dnbr_analysis.py    # Download and map regeneration script
│   ├── generate_map_shell.py     # Map generation script
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
│       ├── generate_dnbr_analysis.yml   # Manual analysis generation
│       └── download_dnbr_analysis.yml   # Manual data download
├── tests/                 # Test suite
│   └── test_generate_dnbr.py # Analysis and generator tests
├── requirements.txt       # Python dependencies
├── requirements.in        # Source dependencies for pip-tools
├── pytest.ini           # Test configuration
└── README.md
```

## 🔄 Future Direction

- Automated fire detection
- GEE REST API integration
- Expand to fire history/temporal analysis

## 📝 License

MIT License - see LICENSE file for details.
