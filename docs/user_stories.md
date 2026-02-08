# **User Stories: Cecil Data Sanitizer & Cost Optimizer**

This document outlines granular user stories for the Cecil hybrid solution. It focuses on the transition from a local-first utility to a SaaS-powered financial analysis engine.

## **User Personas**

### **P1: The Security Operations Engineer (SOE) / Developer**

* **Role:** Responsible for data privacy compliance and technical infrastructure maintenance.  
* **Primary Goal:** Sanitize sensitive data (PII/PHI) locally to ensure zero data leakage while maintaining high system performance.  
* **Key Needs:** A powerful CLI, clear visibility into what is being redacted, and a generic tool that works across various log formats and cloud providers.

### **P2: The CFO / Financial Manager**

* **Role:** Oversees organizational spending on AI and high-cost cloud infrastructure.  
* **Primary Goal:** Gain visibility into LLM token usage and identify cost-saving opportunities (e.g., model switching, prompt optimization).  
* **Key Needs:** Professional, high-fidelity reports, executive-level dashboards, and clear ROI metrics delivered through a secure SaaS interface.

## **1\. Data Ingestion (The "Collector")**

### **US.1: Local File Ingestion**

**User Story:** As an SOE, I want to ingest data from local files (JSONL, CSV, Parquet) so that I can sanitize developer-generated logs or database exports before they leave my machine.

* **Acceptance Criteria:**  
  * \[ \] CLI supports \--source local://path/to/file.  
  * \[ \] Auto-detects file extension and handles parsing errors gracefully.  
  * \[ \] Supports "Streaming" mode for files larger than available RAM.

### **US.2: Generic Cloud Integration**

**User Story:** As an SOE, I want to connect to major cloud providers (AWS, Azure, GCP) so that I can sanitize logs directly from the source without manual downloads.

* **Acceptance Criteria:**  
  * \[ \] Supports aws://log-group-name (CloudWatch) and aws://s3-bucket-name.  
  * \[ \] Supports GCP Cloud Logging and Azure Monitor via respective SDKs.  
  * \[ \] Implements a modular DataProvider interface for easy addition of future providers.

### **US.3: AI-Specific Schema Detection**

**User Story:** As an SOE, I want the tool to automatically recognize common AI provider log schemas (OpenAI, Anthropic, Azure OpenAI) so that I don't have to manually map fields for standard AI logs.

* **Acceptance Criteria:**  
  * \[ \] CLI identifies OpenAI "Chat Completion" and Anthropic "Message" JSON structures.  
  * \[ \] Automatically suggests which fields are "Prompts" (Sensitive) vs "Usage" (Metadata).

## **2\. Sanitization & Mapping (The "Privacy Guard")**

### **US.4: Manual Schema Mapping (Mapping.yaml)**

**User Story:** As an SOE, I want to provide a custom mapping.yaml for non-standard data so that I can define exactly which fields should be Masked, Hashed, or Redacted.

* **Acceptance Criteria:**  
  * \[ \] Supports actions: REDACT (remove), MASK (partial hide), HASH (consistent anonymization), and KEEP.  
  * \[ \] Validates mapping against a sample record before processing the full batch.

### **US.5: Automated PII & Sensitive Key Detection**

**User Story:** As an SOE, I want the system to use NLP (Presidio) and Regex to catch PII even in unmapped unstructured fields so that I am protected from "unknown" sensitive data.

* **Acceptance Criteria:**  
  * \[ \] Deep Interceptor traverses nested JSON keys.  
  * \[ \] Auto-redacts fields matching sensitive patterns (e.g., api\_key, secret, ssn) even if not in the mapping file.

## **3\. Local Audit & Persistence**

### **US.6: Local Persistence (The Verified File)**

**User Story:** As an SOE, I want the sanitized data saved locally to a new file so that I have a clean dataset ready for internal use or debugging.

* **Acceptance Criteria:**  
  * \[ \] Generates a local file (e.g., output\_sanitized.jsonl) by default.  
  * \[ \] Ensures the output file matches the structure of the input file (preserves JSON keys/CSV headers).

### **US.7: Web-Based Audit View**

**User Story:** As an SOE, I want to launch a local Web UI to inspect a sample of the sanitized data so that I can verify that no PII "leaked" through the filters.

* **Acceptance Criteria:**  
  * \[ \] CLI command cecil map launches a local FastAPI \+ React server.  
  * \[ \] UI displays "Before vs After" comparison of redacted fields.  
  * \[ \] No data is sent to the cloud while in this audit mode.

## **4\. AI Cost Analysis (The "CFO Value")**

### **US.8: Anonymized Metadata Extraction**

**User Story:** As a CFO, I want the tool to extract model names and token counts during sanitization so that I have the raw ingredients for a cost analysis without seeing the private text.

* **Acceptance Criteria:**  
  * \[ \] CLI calculates total token usage (Input vs Output) per model locally.  
  * \[ \] Aggregates usage by hashed\_user\_id to identify high-cost users anonymously.

### **US.9: The "Value-First" Conversion CTA**

**User Story:** As a user, I want to receive a prompt after a successful local scan inviting me to get a free report so that I can realize the financial value of my logs.

* **Acceptance Criteria:**  
  * \[ \] Prints a clear terminal message: *"✅ Sanitization complete. Get your Free Cost Analysis PDF: Run cecil report."*  
  * \[ \] Web UI displays a "Generate Report" button after audit verification.

### **US.10: Lead Capture & PDF Generation (SaaS Handshake)**

**User Story:** As a CFO, I want to exchange my contact details for a professional PDF report so that I can share cost-saving insights with my stakeholders.

* **Acceptance Criteria:**  
  * \[ \] CLI/Web UI collects email and company\_name.  
  * \[ \] Telemetry sends *only* anonymized metadata to the SaaS backend.  
  * \[ \] SaaS generates and emails a PDF containing "Projected Savings" and "Risk Mitigation" scores.

## **5\. Reliability & Verification**

### **US.11: Error Resilience & Quarantine**

**User Story:** As a developer, I want logs that fail sanitization (e.g., corrupted JSON) to be moved to a quarantine area so that the main job continues to run.

* **Acceptance Criteria:**  
  * \[ \] CLI implements exponential backoff for cloud service throttling.  
  * \[ \] Failed records are written to quarantine.log for manual review.

### **US.12: Policy Verification (Privacy Integrity)**

**User Story:** As a Security Lead, I want the SaaS report to include a verification of the local policy used so that I know the report is based on fully sanitized data.

* **Acceptance Criteria:**  
  * \[ \] CLI includes a SHA-256 hash of the mapping.yaml in the metadata upload.  
  * \[ \] SaaS backend verifies this hash against "Secure Defaults" and flags if critical PII filters were disabled.