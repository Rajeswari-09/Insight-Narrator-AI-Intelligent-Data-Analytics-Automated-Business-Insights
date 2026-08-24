# Insight Narrator AI

An intelligent multi-agent data analytics application that transforms structured datasets into statistical insights, visual analytics, anomaly detection, forecasting, and human-readable data narratives.

## Overview

**Insight Narrator AI** is a Data Science and AI application designed to simplify exploratory data analysis and transform raw datasets into understandable insights.

Users can upload CSV or Excel datasets through a web interface. The backend processes the uploaded data through a coordinated set of specialized analysis agents. The system automatically identifies data characteristics, performs statistical analysis, generates visualizations, detects anomalies, performs forecasting when suitable time-series data is available, and produces a narrative summary of the findings.

The narrative layer can use OpenAI for AI-generated explanations when an API key is configured, while a rule-based fallback allows the application to continue functioning without an API key.

## Key Features

* Upload CSV and Excel datasets
* Automatic dataset and column-type analysis
* Descriptive statistical analysis
* Missing-value analysis
* Categorical data analysis
* Correlation analysis
* Trend analysis for datetime-based datasets
* IQR-based outlier detection
* Machine-learning-based anomaly detection
* Time-series forecasting using Prophet
* Automatic chart generation
* AI-assisted narrative generation using OpenAI
* Rule-based narrative fallback when OpenAI is unavailable
* Interactive web-based dashboard
* Multi-agent analysis pipeline
* API health-check endpoint
* Support for datasets up to 50,000 rows

## System Architecture

The application follows a multi-agent processing architecture:

```text
                         ┌─────────────────────┐
                         │     User / Browser   │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Frontend Dashboard │
                         │ HTML / CSS / JS      │
                         └──────────┬──────────┘
                                    │
                              File Upload
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │      FastAPI        │
                         │      Backend        │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Orchestrator      │
                         │      Agent          │
                         └──────────┬──────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
       ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
       │  Analyzer   │       │ Visualizer  │       │  Narrator   │
       │    Agent    │       │    Agent    │       │    Agent    │
       └─────────────┘       └─────────────┘       └─────────────┘
              │                     │                     │
              │                     │              ┌──────┴──────┐
              │                     │              │             │
              │                     │              ▼             ▼
              │                     │          OpenAI       Rule-Based
              │                     │          Narrative      Fallback
              │                     │
              └──────────────┬──────┘
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
             ┌─────────────┐   ┌─────────────┐
             │   Anomaly   │   │  Forecast   │
             │    Agent    │   │    Agent    │
             └─────────────┘   └─────────────┘
                    │                 │
                    ▼                 ▼
             Isolation Forest       Prophet
```

## Agent Architecture

### 1. Analyzer Agent

The Analyzer Agent performs the core statistical analysis of the uploaded dataset.

It evaluates:

* Dataset dimensions
* Column types
* Numeric variables
* Categorical variables
* Datetime variables
* Missing values
* Descriptive statistics
* Correlations
* Trends
* Outliers
* Categorical distributions
* Top-level derived insights

### 2. Visualizer Agent

The Visualizer Agent automatically generates charts based on the structure and content of the uploaded dataset.

It uses:

* Matplotlib
* Seaborn
* Pandas

The generated visualizations are returned to the frontend for interactive display.

### 3. Forecast Agent

When an appropriate datetime column and numeric value column are available, the Forecast Agent performs time-series forecasting using **Prophet**.

Forecasting is conditionally executed based on the structure of the uploaded dataset.

### 4. Anomaly Agent

The Anomaly Agent identifies unusual observations using **Isolation Forest** from Scikit-learn.

This provides a machine-learning-based approach to identifying potentially abnormal data points.

### 5. Narrator Agent

The Narrator Agent converts analytical results into a human-readable report.

It has two execution paths:

**OpenAI mode**

When `OPENAI_API_KEY` is configured, the system uses OpenAI to generate a structured narrative containing:

* Executive Summary
* Key Trends
* Notable Patterns
* Recommendations

**Rule-based mode**

If an API key is unavailable or the OpenAI request fails, the application automatically falls back to a rule-based narrative generator.

This allows the application to remain usable without depending entirely on an external AI service.

### 6. Orchestrator Agent

The Orchestrator Agent coordinates the complete analysis pipeline.

The general workflow is:

```text
Upload Dataset
      ↓
Load & Validate Dataset
      ↓
Analyzer Agent
      ↓
Visualizer Agent
      ↓
Forecast Agent ────────┐
      ↓                │
Anomaly Agent ─────────┤
      ↓                │
Narrator Agent         │
      ↓                │
Consolidated Results ←─┘
      ↓
Frontend Dashboard
```

Forecasting and anomaly detection are executed when the uploaded dataset contains suitable datetime and numeric information.

## Technology Stack

### Backend

* Python
* FastAPI
* Uvicorn
* Pandas
* NumPy
* SciPy
* Scikit-learn
* Prophet
* Matplotlib
* Seaborn
* OpenPyXL
* Python Dotenv

### AI

* OpenAI API
* Multi-agent analysis architecture
* Rule-based narrative generation fallback

### Frontend

* HTML5
* CSS3
* JavaScript
* Fetch API
* Interactive dashboard components

### Data Processing

* CSV
* Excel
* Pandas DataFrame processing

## Project Structure

```text
insight-narrator-ai/
│
├── backend/
│   ├── agents/
│   │   ├── analyzer.py
│   │   ├── anomaly_agent.py
│   │   ├── forecast_agent.py
│   │   ├── narrator.py
│   │   ├── orchestrator.py
│   │   └── visualizer.py
│   │
│   └── utils/
│       └── data_utils.py
│
├── frontend/
│   ├── app.js
│   ├── index.html
│   └── style.css
│
├── data/
│   ├── DailyDelhiClimateTest.csv
│   ├── global_sports_footwear_sales_2018_2026.csv
│   └── sample_sales.csv
│
├── main.py
├── requirements.txt
├── .gitignore
└── README.md
```

## API Endpoints

### Health Check

```http
GET /health
```

Returns the service status.

Example response:

```json
{
  "status": "ok",
  "service": "insight-narrator-ai"
}
```

### Dataset Analysis

```http
POST /api/analyze
```

Accepts:

* `.csv`
* `.xls`
* `.xlsx`

The endpoint processes the uploaded dataset through the complete analysis pipeline and returns the generated insights, charts, forecasting results, anomaly results, narrative, and pipeline execution information.

### Frontend

```http
GET /
```

Serves the Insight Narrator AI dashboard.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Rajeswari-09/Insight-Narrator-AI-Intelligent-Data-Analytics-Automated-Business-Insights.git
cd Insight-Narrator-AI-Intelligent-Data-Analytics-Automated-Business-Insights
```

### 2. Create a virtual environment

#### Windows

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell execution policy prevents activation, you can use:

```powershell
.venv\Scripts\activate.bat
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

## OpenAI Configuration

OpenAI is optional.

Without an API key, the application uses its built-in rule-based narrative generation.

To enable AI-generated narratives, create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_api_key_here
```

**Do not commit the `.env` file to GitHub.**

The `.gitignore` file is configured to exclude environment files.

## Running the Application

Start the FastAPI server:

```powershell
python main.py
```

Alternatively:

```powershell
uvicorn main:app --reload --port 8000
```

Open the application in your browser:

```text
http://127.0.0.1:8000
```

API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

## Dataset Input

The application supports:

* CSV files
* Excel `.xls` files
* Excel `.xlsx` files

The current application accepts datasets with fewer than 50,000 rows.

Example datasets included in the repository demonstrate different analytical scenarios, including:

* Climate/time-series data
* Sports footwear sales data
* Sample sales data

Users can also upload their own compatible datasets through the dashboard.

## Analysis Workflow

A typical analysis follows this process:

```text
1. User uploads dataset
          ↓
2. File validation
          ↓
3. DataFrame creation
          ↓
4. Automatic column classification
          ↓
5. Statistical analysis
          ↓
6. Visualization generation
          ↓
7. Conditional anomaly detection
          ↓
8. Conditional time-series forecasting
          ↓
9. Narrative generation
          ↓
10. Results displayed in dashboard
```

## Example Use Cases

Insight Narrator AI can be used for exploratory analysis across datasets such as:

* Sales analytics
* Business performance analysis
* Time-series datasets
* Climate and environmental data
* Product analytics
* Operational datasets
* Customer and transaction data
* General structured CSV/Excel datasets

## Design Goals

The project focuses on reducing the manual effort required for initial data exploration.

Instead of requiring users to independently perform:

```text
Data Cleaning
    ↓
Statistical Analysis
    ↓
Visualization
    ↓
Anomaly Detection
    ↓
Forecasting
    ↓
Insight Interpretation
```

the system coordinates these analytical stages through specialized agents and presents the results through a single web application.

## Future Enhancements

Potential future improvements include:

* More advanced data-quality validation
* Additional machine-learning analysis agents
* Support for larger datasets
* More forecasting models
* User-selectable analysis modules
* Persistent analysis history
* Database-backed analytics
* Authentication and user management
* Cloud deployment
* Containerized deployment with Docker
* Expanded business-domain-specific recommendations
* More interactive visual exploration

## Project Status

**Status: Active Development / Portfolio Project**

The current version provides an end-to-end workflow from dataset upload to automated analysis, visualization, anomaly detection, forecasting, and narrative generation.

## Author

**Rajeswari**

MSc Data Science

This project was developed as an AI and Data Science portfolio project demonstrating data analysis, machine learning, multi-agent architecture, backend API development, and frontend integration.

## License

This project is intended for educational and portfolio purposes.
