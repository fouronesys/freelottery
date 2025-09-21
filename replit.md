# Quiniela Loteka Statistical Analysis System

## Overview

This is a comprehensive lottery analysis system specifically designed for the Dominican Republic's Quiniela Loteka game. The application combines web scraping, statistical analysis, and machine learning techniques to analyze historical lottery data and generate predictions. Built with Python and Streamlit, it provides an interactive dashboard for users to visualize lottery patterns, analyze number frequencies, and receive data-driven predictions for future draws.

The system operates on a 0-99 number range typical for Quiniela games and offers multiple prediction methodologies including frequency-based analysis, trend analysis, and combined approaches.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit-based web application with interactive dashboard
- **Visualization**: Plotly for dynamic charts and graphs showing frequency distributions, trends, and statistical analysis
- **Layout**: Wide layout with expandable sidebar for configuration controls
- **Caching**: Streamlit's `@st.cache_resource` decorator for component initialization to improve performance

### Backend Architecture
- **Core Components**:
  - `DatabaseManager`: SQLite database operations and schema management
  - `QuinielaScraperManager`: Web scraping engine for historical lottery data
  - `StatisticalAnalyzer`: Statistical analysis and frequency calculations
  - `LotteryPredictor`: Machine learning-based prediction engine
- **Design Pattern**: Component-based architecture with clear separation of concerns
- **Data Flow**: Scraper → Database → Analyzer → Predictor → Frontend

### Data Storage
- **Database**: SQLite with two main tables:
  - `draw_results`: Historical lottery results with date, number, position, and prize information
  - `metadata`: System configuration and last update tracking
- **Indexing**: Optimized with indexes on date and number fields for fast queries
- **Data Integrity**: UNIQUE constraints to prevent duplicate entries

### Prediction System
- **Multi-Method Approach**: 
  - Frequency-based predictions using historical occurrence rates
  - Trend analysis for recent pattern detection
  - Combined weighted scoring system
- **Classification System**: Numbers categorized as "Hot", "Cold", or "Normal" based on statistical thresholds
- **Confidence Scoring**: Each prediction includes confidence levels and reasoning

### Data Collection Strategy
- **Multi-Source Scraping**: Three different lottery websites for data redundancy
- **Fallback System**: Realistic sample data generation when live data is unavailable
- **Pattern Recognition**: Multiple regex patterns to extract numbers from various website formats
- **Rate Limiting**: Built-in delays and randomization to respect website policies

## External Dependencies

### Core Libraries
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computations and statistical operations
- **streamlit**: Web application framework and UI components
- **plotly**: Interactive data visualization and charting
- **requests**: HTTP client for web scraping
- **beautifulsoup4**: HTML parsing for web scraping
- **trafilatura**: Advanced web content extraction

### Web Scraping Targets
- **Primary Sources**:
  - loteka.com.do (official Loteka website)
  - loteriasdominicanas.com (lottery results aggregator)
  - resultadosrd.com (Dominican Republic results portal)
- **User Agent Rotation**: Mimics real browser behavior to avoid detection
- **Content Extraction**: Multiple parsing strategies for different website structures

### Database
- **SQLite**: Embedded database for local data persistence
- **No External Dependencies**: Self-contained database solution requiring no external server setup
- **Automatic Schema Management**: Database tables and indexes created automatically on first run