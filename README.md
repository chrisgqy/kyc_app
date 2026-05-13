# KYC Rule Evaluation and Data Source Optimization Engine

## Overview

This project is a rule-based KYC (Know Your Customer) evaluation and optimization engine designed to simulate and analyze identity verification workflows across multiple data sources.

The application allows users to:

- Upload KYC datasource matching results
- Define custom KYC verification rules
- Evaluate whether records satisfy those rules
- Analyze datasource utilization
- Optimize datasource selection using Integer Linear Programming (ILP)
- Explore optimization tradeoffs between verification coverage and datasource cost

The project is built as an interactive Streamlit application with a modular Python backend architecture.


# Project Motivation

Modern KYC systems often aggregate verification signals from multiple third-party data providers. While additional datasources may improve verification coverage, they also introduce operational and financial cost.

This project explores:

- Rule-based identity verification
- Datasource assignment constraints
- Cost-aware datasource optimization
- Verification coverage tradeoffs
- Operational analytics for KYC systems

The optimization engine attempts to minimize datasource cost while maintaining a target verification rate.

# Tech Stack

## Frontend

- Streamlit

## Backend / Core Logic

- Python
- pandas
- NumPy

## Optimization

- PuLP

## Testing

- pytest
- pytest-cov

## Containerization

- Docker


# Repository Structure

```text
kyc_app/
│
├── app/
│   ├── app.py
│   └── pages/
│
├── core/
│   ├── models.py
│   ├── engine_processor.py
│   ├── evaluator.py
│   ├── rule_processor.py
│   ├── engine_analyzer.py
│   └── engine_optimizer.py
│
├── tests/
│
├── data/
│
├── requirements.txt
├── dockerfile
└── README.md
```

# Core Components

## 1. Data Processing Engine

The processor module:

- Cleans uploaded KYC data
- Validates required columns
- Validates allowed match states
- Builds structured record objects for evaluation

## 2. Rule Processing Engine

The rule processor:

- Parses user-defined KYC rules
- Converts rule text into structured rule trees
- Supports:
  - AND
  - OR
  - Parentheses
  - notnomatch logic

Example rule:

```text
(firstname or firstinitial) and notnomatch lastname
```

## 3. Rule Evaluation Engine

The evaluator:

- Applies rules against datasource match results
- Determines which datasources satisfy each rule
- Enforces datasource uniqueness constraints
- Produces record-level verification outputs

## 4. Analyzer Engine

The analyzer:

- Aggregates datasource utilization statistics
- Measures datasource assignment frequency
- Supports operational analysis of verification workflows

## 5. Optimization Engine

The optimizer uses Integer Linear Programming (ILP) to:

- Minimize datasource cost
- Maintain target verification coverage
- Enforce datasource uniqueness constraints
- Select the minimal datasource set needed for verification

The optimization model is implemented using PuLP.

# Input Data Format

The uploaded dataset should contain:

## Required Columns

| Column | Description |
|---|---|
| `recordid` | Unique record identifier |
| `datasource` | Datasource identifier |
| `trumatch_confidence` | Match confidence score |

## Match Fields

Examples:

- firstname
- lastname
- taxid
- address1
- postalcode
- gender

## Allowed Match States

- `match`
- `nomatch`
- `missing`
- `unknown`

# Running the Application Locally

## 1. Create Environment

```bash
conda create -n kyc_app python=3.12
conda activate kyc_app
```


## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

## 3. Launch Streamlit App

From repository root:

```bash
streamlit run app/app.py
```

Application will be available at:

```text
http://localhost:8501
```

# Running Tests

Run all tests:

```bash
python -m pytest -v
```

Run coverage:

```bash
python -m pytest --cov=core
```

# Docker Usage

## Build Docker Image

```bash
docker build -t kyc-app:v1.0 .
```

## Run Docker Container

```bash
docker run -p 8501:8501 kyc-app:v1.0
```

Then open:

```text
http://localhost:8501
```

# Application Workflow

## Step 1 — Upload Data

Upload KYC datasource match results CSV.

## Step 2 — Define Rules

Input one or more KYC verification rules.

Example:

```text
(firstname or firstinitial) and lastname
(firstname and taxid)
```

## Step 3 — Evaluate Rules

The engine evaluates:

- Which datasources satisfy each rule
- Whether records are verifiable
- Valid datasource assignments


## Step 4 — Analyze Results

Analyze:

- Datasource utilization
- Verification rates
- Assignment distribution


## Step 5 — Optimize Datasource Selection

Configure:

- Datasource costs
- Minimum verification rate

The optimizer returns:

- Optimal datasource subset
- Verification coverage
- Record assignments
- Estimated cost reduction


# Notes

- The optimization engine only optimizes records initially marked as verifiable.
- Datasource uniqueness constraints are enforced per record.
- Rule parsing currently supports AND / OR logic and `notnomatch`.
- The project is currently implemented as an MVP/prototype system.


# Future Enhancements

Potential future improvements include:

- Authentication and access control
- Persistent storage layer
- API deployment
- AWS ECS/Fargate deployment
- HTTPS support
- Advanced optimization strategies
- Real-time analytics dashboard
- Rule management UI
- Audit logging
- Parallel optimization execution


# License

MIT License
