TASE DevOps Exam

Project Overview

This project demonstrates a DevOps workflow for a containerized Flask application backed by a PostgreSQL database.

The application displays a simple Hello World page and maintains a page-view counter. Each time the homepage is accessed, the counter is incremented and stored in PostgreSQL.

The project demonstrates application development, Docker containerization, CI automation with Jenkins, and deployment automation with Ansible.

Architecture

The project consists of the following components:

Flask: Python web application.

PostgreSQL: Database used to store the page-view counter.

Docker: Containerizes the application and database.

Docker Compose: Runs the application and database together.

Jenkins: Automates checkout, environment preparation, build, and artifact packaging.

Jenkins Shared Library: Provides reusable pipeline functionality.

Ansible: Automates application deployment.

Bash: Provides an archive extraction utility.

Repository Structure

tase-devops-exam/
│
├── app/
│   ├── app.py
│   ├── dockerfile
│   └── requirements.txt
│
├── ansible/
│   ├── compose.yaml
│   └── deploy.yml
│
├── bash/
│   ├── extract
│   └── extract.sh
│
├── jenkins/
│   ├── jenkinsfile
│   └── shared-library/
│       └── vars/
│           └── prepareEnv.groovy
│
├── .gitignore
└── README.md

Application

The Flask application provides a homepage that displays a page-view counter.

The counter is stored in PostgreSQL, allowing the value to persist across application restarts.

Technologies

Python 3.11

Flask

Flask-SQLAlchemy

PostgreSQL 16

Gunicorn

Running the Application with Docker Compose

Prerequisites

Docker

Docker Compose

1. Configure environment variables

Create an .env file inside the ansible directory.

Example:

POSTGRES_DB=flask_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=replace-with-a-secure-password
WEB_PORT=8080

Do not commit the actual .env file to GitHub.

2. Start the application

From the repository root:

cd ansible
docker compose up -d --build

3. Access the application

Open:

http://localhost:8080

4. Stop the application

docker compose down

To also remove the PostgreSQL data volume:

docker compose down -v

Warning: Removing the volume deletes the stored database data.

Jenkins CI Pipeline

The Jenkins pipeline is defined in:

jenkins/jenkinsfile

The pipeline contains the following stages:

Checkout: Retrieves the source code from GitHub.

Prepare Environment: Uses the shared library to collect Git commit information.

Build: Checks required application files and validates Python syntax.

Package: Creates artifact.zip containing the application files and archives it in Jenkins.

Jenkins Shared Library

The shared library is located at:

jenkins/shared-library/vars/prepareEnv.groovy

It collects and exposes the following Git information:

Commit ID

Committer name

Committer email

Commit message

Jenkins Configuration

Configure the following Global Pipeline Library in Jenkins:

Setting

Value

Name

my-shared-library

Default version

main

Retrieval method

Modern SCM

SCM

Git

Repository URL

https://github.com/odemeytam-ui/tase-devops-exam.git

Library path

jenkins/shared-library

Create a Pipeline job using Pipeline script from SCM with:

Repository: https://github.com/odemeytam-ui/tase-devops-exam.git
Branch: */main
Script path: jenkins/jenkinsfile

Ansible Deployment

The Ansible deployment configuration is located in:

ansible/deploy.yml

The deployment automation is intended to:

Prepare the target Linux host.

Install Docker and Docker Compose.

Create the application deployment directory.

Copy the application and Compose configuration.

Start the application and PostgreSQL containers.

Deployment requires an Ansible control machine, a reachable Linux target host, and the required Ansible collections.

Bash Archive Extraction Utility

The archive extraction script is located in:

bash/extract.sh

It supports extracting common archive formats, including:

gzip

bzip2

ZIP

compress

Run the script with:

./bash/extract.sh -h

Use the help output to see the available options.

Project Goals

This project demonstrates the use of DevOps tools and practices to automate the software lifecycle:

Source code management with Git and GitHub.

Continuous integration using Jenkins.

Reusable pipeline logic using Jenkins Shared Libraries.

Application containerization using Docker.

Multi-container orchestration using Docker Compose.

Deployment automation using Ansible.

Linux automation using Bash.
