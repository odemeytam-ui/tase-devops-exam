# tase-devops-exam

A small **Flask + PostgreSQL** application used to demonstrate an end-to-end DevOps workflow. The homepage displays a `Hello World` message and a page-view counter. Each visit increments the counter in PostgreSQL, so the value survives application and container restarts.

The repository brings together **Docker and Docker Compose** for containerization, **Jenkins** for continuous integration and artifact packaging, **Ansible** for deployment to a remote Debian/Ubuntu host, and a **Bash** utility for extracting compressed archives.

| | Result |
|---|---|
| Application | Flask web application backed by PostgreSQL 16 |
| Container setup | Docker image for the app; Compose services for the app and database |
| Automated tests | **3 tests** covering the health endpoint, homepage, and persistent page counter |
| CI pipeline | **5 stages**: Checkout, Prepare Environment, Build, Test, Package |
| Artifact | `artifact.zip`, archived by Jenkins with fingerprinting |
| Deployment | Ansible playbook installs Docker, copies the application, starts Compose, and checks `/health` |

## Repository layout

```text
tase-devops-exam/
├── app/
│   ├── app.py
│   ├── dockerfile
│   └── requirements.txt
├── ansible/
│   ├── compose.yaml
│   ├── deploy.yml
│   └── requirements.yml
├── bash/
│   └── extract
├── jenkins/
│   ├── controller/
│   │   ├── Dockerfile
│   │   └── docker-compose.yaml
│   ├── jenkinsfile
│   └── shared-library/
│       └── vars/
│           └── prepareEnv.groovy
├── tests/
│   ├── requirements.txt
│   └── test_app.py
├── .gitignore
└── README.md
```

The local environment file (`ansible/.env`) and the Ansible inventory (`ansible/inventory.ini`) are configuration files created on the machine running the project; they should not be committed to the repository.

## Build and run locally

Requirements: Docker Engine or Docker Desktop with the Docker Compose plugin. The commands below are run from the repository root unless stated otherwise.

### 1. Configure the environment

Create `ansible/.env` with the database settings and the host port for the web application:

```dotenv
POSTGRES_DB=flask_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=replace-with-a-strong-password
WEB_PORT=8080
```

`WEB_PORT` is the port exposed on the host. The default is `8080`; the application listens on port `5000` inside the container. Keep the real `.env` file out of Git.

### 2. Build and start the application

```bash
cd ansible
docker compose up -d --build
```

Open the application at `http://localhost:8080` (or the port configured in `WEB_PORT`). Refreshing the page increments the counter stored in PostgreSQL.

### 3. Check application health

```bash
curl http://localhost:8080/health
```

Expected response:

```json
{"status":"ok"}
```

The Compose configuration waits for PostgreSQL's health check before starting the web application. The web container also has a health check that calls the Flask `/health` endpoint.

### 4. Stop the application

```bash
docker compose down
```

To remove the PostgreSQL data volume as well:

```bash
docker compose down -v
```

**Warning:** `down -v` deletes the stored page counter and all other data in the Compose PostgreSQL volume.

## Automated tests

The tests are in [`tests/test_app.py`](tests/test_app.py). They verify:

1. `/health` returns HTTP 200 and `{"status":"ok"}` when the application can query PostgreSQL.
2. The homepage returns HTTP 200 and contains `Hello World!`.
3. Each homepage request increments the page-view counter by exactly one.

Run the tests from the repository root:

```bash
cd ansible
docker compose --profile test run --build --rm test
```

The test service uses the same application image and starts PostgreSQL as a dependency. It installs the packages listed in `tests/requirements.txt` and runs `pytest` inside the container. The three tests passed in the local verification run.

## Jenkins CI pipeline

The pipeline is defined in [`jenkins/jenkinsfile`](jenkins/jenkinsfile) and uses the `my-shared-library` Jenkins Shared Library.

| Stage | What it does |
|---|---|
| **Checkout** | Checks out the repository using the job's SCM configuration |
| **Prepare Environment** | Calls `prepareEnv()` to collect the current commit ID, committer, email, and commit message |
| **Build** | Checks that required application and test files exist, then validates Python syntax with `compileall` |
| **Test** | Starts the application and PostgreSQL containers, copies tests into the existing Flask container, and executes pytest |
| **Package** | Creates `artifact.zip` from `app/` and archives it in Jenkins with fingerprinting |

The Test stage generates a temporary database password and uses a unique Compose project name for each build. A shell trap runs Compose cleanup when the test stage exits, including when it fails.

The pipeline also polls the configured SCM repository using:

```groovy
pollSCM('H/2 * * * *')
```

This checks for changes approximately every two minutes; Jenkins may schedule the actual check within its polling interval.

### Jenkins Shared Library

The shared-library function is [`jenkins/shared-library/vars/prepareEnv.groovy`](jenkins/shared-library/vars/prepareEnv.groovy). It gathers Git metadata and returns it as a map for the pipeline to use.

Configure a **Global Pipeline Library** in Jenkins with these values:

| Setting | Value |
|---|---|
| Name | `my-shared-library` |
| Default version | `main` |
| Retrieval method | Modern SCM |
| SCM | Git |
| Repository URL | `https://github.com/odemeytam-ui/tase-devops-exam.git` |
| Library path | `jenkins/shared-library` |

Create a Pipeline job using **Pipeline script from SCM**:

| Setting | Value |
|---|---|
| SCM | Git |
| Repository URL | `https://github.com/odemeytam-ui/tase-devops-exam.git` |
| Branch specifier | `*/main` |
| Script path | `jenkins/jenkinsfile` |

### Run the Jenkins controller with Docker Compose

The controller definition is in [`jenkins/controller/docker-compose.yaml`](jenkins/controller/docker-compose.yaml). From the repository root:

```bash
cd jenkins/controller
docker compose up -d --build
```

Open Jenkins at `http://localhost:8081`. The Compose configuration stores Jenkins data in the named `jenkins_home` volume and exposes the inbound-agent port `50000`.

The controller mounts `/var/run/docker.sock` so pipeline jobs can use the host's Docker engine. This grants Jenkins powerful access to the Docker host; use this configuration only in a trusted environment and do not expose the Jenkins controller publicly without additional security controls.

## Ansible deployment

The deployment playbook is [`ansible/deploy.yml`](ansible/deploy.yml). It currently supports **Debian and Ubuntu** targets and performs the following tasks:

- Checks the target operating system and verifies that the local `ansible/.env` file exists.
- Adds Docker's official APT repository and installs Docker Engine, Buildx, and the Compose plugin.
- Creates `/opt/flask-postgres-app/` on the target host.
- Copies the Flask application, Compose file, and environment file to the target.
- Starts the application stack and waits for the services.
- Checks that the application's `/health` endpoint returns HTTP 200.

Install the collection used by the playbook:

```bash
ansible-galaxy collection install -r ansible/requirements.yml
```

Create `ansible/inventory.ini` on the Ansible control machine. Replace the example address and SSH user with the details of your target host:

```ini
[app_servers]
app-host ansible_host=192.0.2.10 ansible_user=ubuntu
```

Make sure SSH access and privilege escalation are configured for the target. Then run the playbook from the repository root:

```bash
ansible-playbook -i ansible/inventory.ini ansible/deploy.yml
```

The playbook's health-check port defaults to `8080`. If `WEB_PORT` in `ansible/.env` is different, pass the same port to Ansible. For example, when `WEB_PORT=5000`:

```bash
ansible-playbook -i ansible/inventory.ini ansible/deploy.yml -e "web_port=5000"
```

The playbook copies the environment file to the remote host with file mode `0600` and suppresses that task's output with `no_log`.

## Bash archive extraction utility

The utility is [`bash/extract`](bash/extract). It detects archive formats using the `file` command rather than relying only on file extensions. Supported formats are:

- gzip
- bzip2
- ZIP
- compress (`.Z`)

Show its built-in help:

```bash
./bash/extract -h
```

Use `-r` to search directories recursively and `-v` for verbose output. For example:

```bash
./bash/extract -v ./downloads
./bash/extract -r -v ./archive-folder
```

The script requires `file`, `gunzip`, `bunzip2`, `unzip`, and `uncompress` to be installed.

## Security and configuration notes

- The Flask application requires `POSTGRES_PASSWORD` from the environment; it has no hard-coded password fallback.
- PostgreSQL is used by the Compose network and its port is not published directly to the host in the supplied Compose file.
- Store real database credentials in the local `ansible/.env` file and keep that file out of version control. If credentials have ever been committed to a public repository, remove them from the repository and rotate them; adding a file to `.gitignore` does not remove a file that Git already tracks.
- The Ansible playbook writes the remote environment file with restrictive permissions (`0600`).
- Access to the Docker socket gives the Jenkins container substantial control over the Docker host.

## What this project demonstrates

- Building a Python web application that persists data in PostgreSQL.
- Creating and running application and database containers with Docker Compose.
- Defining a CI pipeline with Jenkins and a reusable Shared Library.
- Running automated integration tests as part of the pipeline.
- Packaging and archiving a build artifact.
- Provisioning Docker and deploying an application to a remote Linux host with Ansible.
- Writing a Bash utility that identifies and extracts several archive formats.

## What I would improve next

- Add a database migration tool such as Flask-Migrate/Alembic instead of relying on `create_all()` at application startup.
- Add dedicated CI reporting and publish test results in Jenkins.
- Add TLS and a reverse proxy for deployments that need external access.
- Move secrets to a dedicated secrets manager for anything beyond a local or exam environment.
- Add automated linting and static analysis to the Jenkins pipeline.