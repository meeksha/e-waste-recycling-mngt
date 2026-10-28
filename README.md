# E-Waste Recycling Management System

A database-driven application for managing electronic waste collection, recycling operations, collection center capacity, and IoT-based weight scan analytics. The system combines relational data management with document-based logging to support end-to-end e-waste tracking.

## Overview

Electronic waste requires proper collection, storage, and disposal to reduce environmental harm. This project provides a centralized interface for citizens and collection center administrators to manage e-waste pickup requests, monitor collection center utilization, track recycling batches, and analyze IoT weight scan data.

The application uses **MySQL** for structured operational data and **MongoDB** for activity logs and IoT analytics, with **Streamlit** providing the interactive user interface.

## Features

### Citizen Portal
- Submit e-waste pickup requests with an address, city, and preferred time slot.
- View pickup requests using a registered email address.
- Track request details and their current status.

### Collection Center Administration
- View collection center capacity, current load, and utilization percentage.
- Add e-waste items with category, brand, model, weight, condition, and intake type.
- Automatically update collection center load using MySQL triggers.
- View recycling batches, treatment types, and batch statuses.
- Inspect recycling event logs stored in MongoDB.
- Visualize daily IoT weight totals and scan counts.
- View records from the application's main MySQL tables.

### Database Automation and Analytics
- **Stored procedures:** Create pickup requests and support database reporting.
- **Triggers:** Set default pickup request values and update collection center load.
- **Relational integrity:** Use primary keys and foreign keys to connect users, requests, centers, items, and recycling batches.
- **MongoDB logging:** Record pickup request activity and retrieve recycling and IoT scan data.
- **Data visualization:** Display IoT weight trends and daily scan counts using Streamlit charts.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application logic |
| Streamlit | Interactive web interface |
| MySQL | Structured data storage |
| MongoDB | Activity logs and IoT scan analytics |
| Pandas | Data processing |
| `mysql-connector-python` | Python–MySQL connectivity |
| `pymongo` | Python–MongoDB connectivity |
| SQL | Schema design, stored procedures, triggers, and queries |

## System Architecture

```text
             Citizen / Center Admin
                      |
                      v
              Streamlit Interface
                      |
                Python Application
                  /           \
                 v             v
              MySQL          MongoDB
                |               |
          Operational       Activity Logs
              Data          Recycling Logs
                |           IoT Scan Data
                v
        Procedures & Triggers
                |
                v
       Center Load Management
```

## Database Design

### MySQL — `ewaste_db`

The SQL setup script creates the following tables:

| Table | Purpose |
|---|---|
| `users` | Stores citizen and administrator details |
| `collection_center` | Stores center information, capacity, and current load |
| `ewaste_category` | Defines e-waste categories and hazard levels |
| `pickup_request` | Stores pickup requests and scheduling details |
| `ewaste_item` | Stores collected or dropped-off e-waste items |
| `recycling_batch` | Tracks recycling batches and treatment status |
| `batch_item` | Links e-waste items to recycling batches |

The setup script also defines three triggers and three stored procedures.

**Triggers**
- `trg_before_pickup_insert` — assigns a default request status and date when missing.
- `trg_after_item_insert` — increases a collection center's load when an item is inserted.
- `trg_after_batch_update` — reduces the center load when a batch is closed.

**Stored procedures**
- `sp_create_pickup_request` — creates a pickup request.
- `sp_center_load_report` — reports center utilization by city.
- `sp_user_recycling_summary` — summarizes recycled items and their weight for a user.

### MongoDB — `ewaste_mongo`

The application accesses these collections:

- `user_activity_logs` — records pickup request activity.
- `recycling_logs` — stores recycling batch event logs.
- `iot_weight_scans` — stores weight scan records used for analytics.

## Prerequisites

Install the following before running the project:

- Python 3.10 or later recommended
- MySQL Server
- MongoDB Server
- Git
- A Python package manager such as `pip`

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

Replace the placeholders with your GitHub username and repository name.

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

On macOS or Linux:

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install streamlit mysql-connector-python pymongo pandas
```

### 4. Configure MySQL

Start your MySQL server and execute `mysql_setup.sql` using MySQL Workbench or the MySQL command-line client.

For example:

```bash
mysql -u root -p < mysql_setup.sql
```

**Important:** The SQL script drops and recreates the project's tables when rerun. Back up any existing project data before executing it again.

### 5. Configure database connections

The current application expects the following local services:

| Service | Configuration |
|---|---|
| MySQL | Host: `localhost`, database: `ewaste_db` |
| MongoDB | URI: `mongodb://localhost:27017/` |
| MongoDB database | `ewaste_mongo` |

Update the MySQL credentials in `app.py` to match your local configuration. Ensure both database servers are running before launching the application.

For a safer configuration, store database credentials in environment variables rather than hardcoding passwords in source code. Never commit real credentials or `.env` files to GitHub.

### 6. Run the application

```bash
streamlit run app.py
```

Streamlit will display a local URL in the terminal, typically:

```text
http://localhost:8501
```

Open the URL in your browser to use the application.

## Usage

1. Launch the application.
2. Select **Citizen** or **Center Admin** from the sidebar.
3. Citizens can submit pickup requests and look up existing requests.
4. Administrators can view center statistics, add e-waste items, inspect recycling batches, and analyze IoT scan data.
5. Use the database tables and sample records to explore the application's functionality.

The SQL script inserts sample users, collection centers, e-waste categories, and a pickup request. Additional data may be required to demonstrate every dashboard and analytics feature.

## Project Structure

```text
E-Waste-Recycling-Management-System/
├── app.py
├── mysql_setup.sql
├── README.md
└── .gitignore
```

## Future Enhancements

- Implement secure authentication and role-based authorization.
- Replace manual user and center ID entry with validated user selection.
- Add pickup request status updates and scheduling management.
- Integrate live IoT devices for automatic weight capture.
- Add recycling reports, environmental impact metrics, and waste diversion statistics.
- Introduce configuration management and deployment support.
- Add automated tests and error handling for database failures.

## Learning Outcomes

This project demonstrates practical application of:

- Relational database design and normalization.
- SQL joins, constraints, stored procedures, and triggers.
- Integration of MySQL and MongoDB in a single application.
- Python-based database connectivity.
- Interactive dashboards and data visualization.
- Basic tracking and analytics for e-waste management workflows.

