# TASE DevOps Exam

This repository contains the implementation of the DevOps assignment. It
brings together a Jenkins CI/CD pipeline, a Groovy Shared Library, an
Ansible-managed Docker Compose deployment, a small Flask application
backed by PostgreSQL, and a Bash archive-extraction utility.

## Repository contents

``` text
.
├── app/
│   ├── app.py
│   ├── requirements.txt
│   └── dockerfile
├── ansible/
│   ├── compose.yaml
│   ├── deploy.yml
│   ├── requirements.yml
│   └── .env.example
├── bash/
│   └── extract
├── jenkins/
│   ├── jenkinsfile
│   └── shared-library/
│       └── vars/
│           └── prepareEnv.groovy
└── tests/
    ├── requirements.txt
    └── test_app.py
```

## 1. Application

The application is a small Flask web server connected to PostgreSQL.

-   `GET /` displays a Hello World page and increments the hit counter.
-   `GET /health` checks the application's database connection.
-   The hit counter is stored in PostgreSQL, so it survives
    application/container restarts when the database volume is retained.
-   The counter update is performed atomically in the database.

The application dependencies are listed in `app/requirements.txt`. The
Docker image is built from `app/dockerfile`.

## 2. Docker Compose

The Compose configuration is in `ansible/compose.yaml` and defines two
services:

  Service   Purpose
  --------- ---------------------------------------------
  `web`     Builds and runs the Flask application
  `db`      Runs PostgreSQL and stores application data

The web service waits for the database health check before starting.
PostgreSQL uses a named Docker volume for persistent data.

### Configure environment variables

Create the local environment file from the example:

``` bash
cp ansible/.env.example ansible/.env
```

Edit `ansible/.env` and set a strong password for `POSTGRES_PASSWORD`.

The example file contains these settings:

``` dotenv
POSTGRES_DB=flask_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=replace-with-a-strong-password
WEB_PORT=8080
```

Keep `ansible/.env` private. It contains deployment configuration and
should not be committed to Git. The `.env.example` file is safe to
commit because it contains a placeholder password.

### Run with Docker Compose

From the repository root:

``` bash
docker compose --env-file ansible/.env -f ansible/compose.yaml up -d --build
```

Open the application at:

``` text
http://localhost:5000
```

Check its health endpoint:

``` text
http://localhost:5000/health
```

To stop the services:

``` bash
docker compose --env-file ansible/.env -f ansible/compose.yaml down
```

To also remove the PostgreSQL data volume (this permanently deletes the
stored counter and database data):

``` bash
docker compose --env-file ansible/.env -f ansible/compose.yaml down -v
```

If you change `WEB_PORT` in `ansible/.env`, use the corresponding port
when opening the application.

## 3. Ansible deployment

The playbook `ansible/deploy.yml` automates deployment to an
Ubuntu/Debian target host.

It: 1. Checks that the local `ansible/.env` file exists. 2. Configures
the official Docker package repository and installs Docker Engine and
the Compose plugin. 3. Creates the application directories on the
target. 4. Copies the application, Compose configuration, and
environment file to the target. 5. Validates the Compose configuration.
6. Deploys the services with the Docker Compose Ansible collection. 7.
Checks the application's `/health` endpoint.

### Install Ansible dependencies

Install Ansible on the machine from which you will run the playbook,
then install the required collection:

``` bash
ansible-galaxy collection install -r ansible/requirements.yml
```

### Run the playbook

Configure an Ansible inventory for your target host and make sure SSH
access and privilege escalation are configured. Then run:

``` bash
ansible-playbook -i <your-inventory-file> ansible/deploy.yml
```

Replace `<your-inventory-file>` with the path to your inventory.

The playbook expects `ansible/.env` to exist on the machine running
Ansible. The file is copied to the target with restricted permissions.

## 4. Jenkins CI/CD pipeline

The pipeline is defined in `jenkins/jenkinsfile`. It uses the Groovy
Shared Library function `prepareEnv`, located at:

``` text
jenkins/shared-library/vars/prepareEnv.groovy
```

The Jenkinsfile loads the library using:

``` groovy
@Library('my-shared-library') _
```

Configure a Jenkins Global Pipeline Library named `my-shared-library`
and point its SCM configuration to this repository. The library root
should be `jenkins/shared-library`, so Jenkins can find the
`vars/prepareEnv.groovy` global variable.

### Pipeline stages

1.  **Checkout** -- checks out the repository.
2.  **Prepare Environment** -- calls `prepareEnv()` to collect the
    checked-out commit ID, committer name, committer email, and commit
    message. The function exposes these values through environment
    variables and returns them to the pipeline.
3.  **Build** -- validates required application/test files, compiles the
    Python files, checks Docker/Compose availability, and builds the web
    image.
4.  **Test** -- starts PostgreSQL and the web service, runs the
    integration tests inside the web container, and cleans up the test
    containers and volume.
5.  **Package** -- creates `artifact.zip` from the application files,
    excluding Python cache files, and archives it in Jenkins.
6.  **Upload to GitHub Release** -- creates a GitHub Release for the
    build and uploads `artifact.zip` as a release asset.

### Trigger

The Jenkinsfile uses `pollSCM('H/2 * * * *')` to check the SCM
repository for changes approximately every two minutes, using Jenkins'
hashed schedule.

### Jenkins configuration requirements

The Jenkins environment needs: - Access to this Git repository. - Python
3 and the tools used by the pipeline, including Docker CLI, Docker
Compose, `zip`, and `curl`. - Docker access so the pipeline can build
and run containers. - A Jenkins **Secret text** credential with ID
`github-token`, containing a GitHub token that has permission to create
releases and upload release assets to this repository. - The Shared
Library configured as described above.

The GitHub token is read from Jenkins Credentials at runtime; it should
never be hard-coded in the Jenkinsfile or committed to the repository.

## 5. Integration tests

The tests are in `tests/test_app.py` and cover:

-   The health endpoint.
-   The Hello World response.
-   The hit counter incrementing between requests.

Install the test dependencies with:

``` bash
python3 -m pip install -r tests/requirements.txt
```

The integration tests expect the application and its PostgreSQL database
to be running and configured. The Jenkins pipeline starts the required
services before executing them.

## 6. Bash archive extraction utility

The script is located at `bash/extract`.

It identifies archive formats using the `file` command rather than
relying on file extensions. It supports:

-   gzip
-   bzip2
-   ZIP
-   compress (`.Z`)

It accepts multiple files and directories, can recursively traverse
directories, overwrites existing extracted files, and leaves unsupported
or uncompressed files untouched. It reports the number of successfully
decompressed archives and returns the number of files that were not
decompressed as its exit status.

### Usage

``` text
extract [-h] [-r] [-v] file [file...]
```

Options:

-   `-h` --- display help.
-   `-r` --- recursively process directories.
-   `-v` --- print each successfully decompressed file and warn about
    files that could not be decompressed.

Examples:

``` bash
./bash/extract archive.tar.gz
./bash/extract -v first.gz second.zip
./bash/extract -r ./archives
./bash/extract -h
```

The script requires Bash and the relevant system utilities (`file`,
`gunzip`, `bunzip2`, `unzip`, and `uncompress`).

## Security and configuration notes

-   Do not commit `ansible/.env` or any file containing real
    credentials.
-   Use a strong, unique PostgreSQL password in the local environment
    file.
-   Store the GitHub token in Jenkins Credentials, not in source code.
-   The Jenkins Docker socket grants the Jenkins process powerful access
    to the Docker host. This is suitable for a controlled lab
    environment, but should be carefully restricted in shared or
    production environments.
-   Removing the Compose stack with `down -v` deletes the persistent
    PostgreSQL volume.

## Assignment summary

This project demonstrates:

-   CI/CD pipeline creation with Jenkins.
-   Reusable pipeline logic through a Groovy Shared Library.
-   SCM polling and commit metadata collection.
-   Application build, integration testing, artifact packaging, and
    release upload.
-   Containerized application deployment with Docker Compose.
-   Infrastructure automation with Ansible.
-   Persistent application state using PostgreSQL.
-   Bash scripting for archive detection and extraction.

## What I would improve next

- Add a database migration tool such as Flask-Migrate/Alembic instead of relying on `create_all()` at application startup.
- Add dedicated CI reporting and publish test results in Jenkins.
- Add TLS and a reverse proxy for deployments that need external access.
- Move secrets to a dedicated secrets manager for anything beyond a local or exam environment.
- Add automated linting and static analysis to the Jenkins pipeline.