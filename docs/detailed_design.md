# **Technical Design Document: Cecil Data Sanitizer & Cost Optimizer (v3.1)**

## **1\. System Architecture: The "Safe-Pipe" Framework**

The architecture follows a **Local-First, Cloud-Optional** model. The CLI provides immediate utility by generating sanitized data locally, then offers an "Upgrade Path" to cloud-based analytics.

### **1.1 High-Level Component Flow**

\[Source (Cloud/Local)\] \-\> \[Ingestion Provider\] \-\> \[Sanitization Engine\] \-\> \[Local Sanitized Output\] \-\> \[Opt-in: SaaS Analysis\]

### **1.2 Multi-Mode Execution**

1. **AI-Optimization Mode:** Pre-configured for LLM logs to extract cost metadata.  
2. **Generic Mode:** User-defined schemas for sanitizing arbitrary structured data.  
3. **Audit Mode:** Forced local output; telemetry is blocked until explicit user consent is provided.

## **2\. Detailed Technical Engineering**

### **2.1 Modular Ingestion (The Provider Pattern)**

The DataProvider interface supports streaming from various sources:

* **CloudConnectors:** AWS CloudWatch/S3, Azure Monitor, GCP Logging.  
* **GenericConnectors:** Local files (JSONL, CSV, Parquet), stdin, and database streams.

### **2.2 Schema-Aware Sanitization (Deep Interceptor)**

The engine traverses data structures using a **Mapping Strategy**:

* **Strict Mode:** Only keeps explicitly mapped fields.  
* **Deep Interceptor:** Recursively redacts sensitive keywords (e.g., api\_key, secret) detected in nested keys.

### **2.3 Local-First Workflow & "Upgrade" Path**

The CLI prioritizes local utility to build trust:

* **Immediate Local Output:** Upon completion of a scan, the CLI generates a sanitized version of the data in the user's preferred format (.jsonl, .csv) at a specified local path.  
* **The "Value Gap" Notification:** After generating the local file, the CLI outputs a high-visibility terminal message:"✅ Sanitized data saved to ./sanitized\_logs.jsonl. 📊 Want to see how much you could save? Run cecil report to get a Free Cost Analysis PDF."  
* **The Conversion Button (Mapping UI):** In the Web-based mapping interface, a prominent button labeled **"Generate Free Cost Analysis Report"** appears once the local sanitization preview is approved.

## **3\. Real-World Use Cases & Simulations**

### **3.1 Use Case A: AI Cost Optimization (LLM Logs)**

* **Local Utility:** User gets a scrubbed version of their logs for internal debugging.  
* **SaaS Hook:** User submits the anonymized "Cost Fingerprint" to receive a PDF highlighting $X,XXX in potential savings from model switching or prompt optimization.

### **3.2 Use Case B: Generic Data Sanitization**

* **Local Utility:** Developers sanitize production data for local development.  
* **Incentive:** The tool remains useful even if the user never connects to the SaaS backend.

## **4\. SaaS Integration & Lead Capture**

### **4.1 Hybrid Lead Capture**

The SaaS backend triggers only when the user opts in:

1. **Metadata Push:** CLI sends only non-sensitive cost fingerprints (Token counts, Model IDs).  
2. **Lead Capture:** User provides an email address via the CLI prompt or Web UI.  
3. **Delivery:** SaaS generates the PDF and emails it to the user, establishing the sales lead.

### **4.2 Security Verification Signature**

The SaaS backend verifies that data was processed by the Cecil engine by checking a "Policy Hash" included in the metadata, ensuring the user actually used the sanitization rules.

## **5\. Engineering Edge Cases & Robustness**

| Scenario | Architectural Response |
| :---- | :---- |
| **User Denies Upload** | CLI respects privacy; local files are generated, and no network requests are made to the SaaS backend. |
| **Upload Failure** | If the SaaS report request fails, the local sanitized data remains available to the user; the report request is queued for retry. |
| **Inconsistent Formats** | A "Normalizer" layer casts data types based on the mapping strategy before final output. |

## **6\. Deployment & References**

### **6.1 Distribution**

* **Single-Binary:** Bundled via PyInstaller containing all providers, the React UI, and the NLP engine.  
* **Signed Artifacts:** Binaries are signed for Windows/MacOS to ensure enterprise trust.

### **6.2 Implementation References**

* **Video Guide:** [Protecting User Data in AI Agents & Log Sanitization](https://m.youtube.com/watch?v=2HZ9c089jM8) \- Implementing the "Safe-Pipe" and "Deep Interceptor" patterns.