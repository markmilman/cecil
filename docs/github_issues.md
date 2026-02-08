# **GitHub Issues Backlog: Engineering Foundation (Cecil)**

This document contains formatted issues and tasks ready to be copied into GitHub Issues or a Project Board.

## **🏗️ Epic: Infrastructure & DevOps Foundation**

### **Issue \#1: \[TS.1\] Repository Initialization & Coding Standards**

**Description:** Establish the core repository structure and automated linting/formatting standards to ensure consistency across the fleet of AI agents.

**Tasks:**

* \[ \] Create directory structure: /src/cecil, /ui, /tests, /scripts.  
* \[ \] Configure .gitignore to exclude venv/, \_\_pycache\_\_, node\_modules/, and .exe/.bin artifacts.  
* \[ \] Initialize pre-commit configuration with:  
  * ruff for linting and formatting.  
  * mypy for strict type checking.  
* \[ \] Set up GitHub Branch Protection for main (require PR and status checks).  
* \[ \] Create CONTRIBUTING.md defining the branching strategy (feat/, fix/, refactor/).

**Assignment:** @DevOps-Agent

**Status:** Ready for Implementation

### **Issue \#2: \[TS.2\] Automated CI Pipeline (Validation)**

**Description:** Implement a GitHub Actions workflow to validate code quality and security on every Pull Request to the develop branch.

**Tasks:**

* \[ \] Create .github/workflows/ci-validation.yml.  
* \[ \] Implement python-lint-test job:  
  * Run ruff check.  
  * Run pytest with coverage report.  
* \[ \] Implement frontend-lint-test job:  
  * Run npm run lint.  
  * Run npm test.  
* \[ \] Add security-scan job using bandit or safety.  
* \[ \] Configure PR status check requirement in GitHub settings.

**Assignment:** @DevOps-Agent

**Dependencies:** \#1

**Status:** Backlog

## **🛠️ Epic: Core Architecture (Safe-Pipe)**

### **Issue \#3: \[TS.3\] Provider Interface & Streaming ABCs**

**Description:** Define the core BaseDataProvider interface. This is the foundational contract for all cloud and local data ingestion.

**Tasks:**

* \[ \] Define cecil.core.providers.base.BaseDataProvider as an ABC.  
* \[ \] Implement abstract methods: connect(), close(), and fetch\_metadata().  
* \[ \] Implement stream\_records() as a Python Generator (Yielding chunks).  
* \[ \] Create a MockDataProvider for testing the pipeline without external dependencies.  
* \[ \] Add unit tests for the streaming generator to verify memory usage stays below 50MB for large simulated inputs.

**Assignment:** @Backend-Agent

**Status:** Ready for Implementation

### **Issue \#4: \[TS.4\] Internal Inter-Process Communication (IPC)**

**Description:** Setup the FastAPI backend and ServerManager to allow the CLI binary to communicate with the bundled Web UI via a local loopback address.

**Tasks:**

* \[ \] Create cecil.api.server.ServerManager to manage the Uvicorn process.  
* \[ \] Implement /health heartbeat endpoint.  
* \[ \] Configure strict CORS settings (Localhost/127.0.0.1 only).  
* \[ \] Implement a dynamic port selection logic to avoid 8080/3000 conflicts.  
* \[ \] Create a shutdown signal handler to ensure the server dies if the CLI is killed.

**Assignment:** @Systems-Agent

**Status:** Ready for Implementation

## **🎨 Epic: Frontend & Distribution**

### **Issue \#5: \[TS.5\] React Boilerplate & Design System Integration**

**Description:** Initialize the React frontend using Vite and configure Tailwind CSS with Cecil’s professional CFO-centric design tokens.

**Tasks:**

* \[ \] Initialize Vite/React project in /ui.  
* \[ \] Configure tailwind.config.js with primary colors: Slate-900 (Primary), Indigo-600 (Accent), Emerald-500 (Success/Savings).  
* \[ \] Install lucide-react for iconography.  
* \[ \] Build ApiClient.js wrapper using Axios with base URL configured for the local FastAPI server.  
* \[ \] Create a "Shell" layout with navigation placeholders for Mapping and Audit.

**Assignment:** @Frontend-Agent

**Assignment (Design):** @UX-Design-Agent

**Status:** Ready for Implementation

### **Issue \#6: \[TS.6\] Single-Binary Build Script (PyInstaller)**

**Description:** Create a unified build script to package the entire application into a single executable, ensuring asset path resolution works in the \_MEIPASS environment.

**Tasks:**

* \[ \] Create scripts/build.py orchestrator.  
* \[ \] Implement logic to run npm run build and move assets to src/cecil/ui\_dist.  
* \[ \] Configure PyInstaller .spec file to include:  
  * ui\_dist/ folder.  
  * NLP models (spacy/presidio assets).  
* \[ \] Create cecil.utils.paths.get\_resource\_path() to handle runtime vs. dev asset resolution.  
* \[ \] Generate a test binary and verify the UI loads from within the executable.

**Assignment:** @Systems-Agent

**Dependencies:** \#4, \#5

**Status:** Backlog

## **🧪 Epic: Quality & Reliability**

### **Issue \#7: \[TS.7\] E2E Testing Harness & Leak Detection**

**Description:** Set up Playwright and a "Safe-Pipe" verification suite to ensure that no sensitive data ever leaves the local environment.

**Tasks:**

* \[ \] Initialize Playwright in /tests/e2e.  
* \[ \] Create a "Data Fixture" generator that creates logs with known PII (fake emails/SSNs).  
* \[ \] Write a test that:  
  1. Ingests a mock log.  
  2. Verifies the Web UI displays redactions.  
  3. Asserts that the "Telemetry Payload" sent to the SaaS mock endpoint contains 0% of the PII strings.  
* \[ \] Implement a basic performance benchmark (records processed per second).

**Assignment:** @QA-Agent

**Dependencies:** \#3, \#4

**Status:** Backlog