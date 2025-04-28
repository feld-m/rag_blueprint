# Task 1: HackerNews Datasource Implementation: Approach and Key Decisions

## Approach

My approach was to integrate HackerNews as a new data source by strictly adhering to the existing RAG blueprint framework's modular architecture and established conventions. This involved creating the standard set of components:
**Configuration, Client,Document,Reader,Parser,Manager and init.py to resgister** for the new Datasource HackerNews

It should seamlessly plug into the existing framework and pipelines.

## Key Decisions
1.  **Framework Alignment**:
    Prioritize adherence to the blueprint's patterns.
    Ensures compatibility and maintainability within the larger system. This involved inheriting from provided base classes and using the Factory pattern for component instantiation (`SingletonFactory` for the client), and integrating with the Registry system via the `register()` function.

2.  **Asynchronous Operations (`httpx` & `asyncio`)**:
    Utilize `httpx` and `asyncio` for fetching data in the `Reader`. HackerNews requires fetching a list of story IDs and then fetching details for each ID. Performing these detail fetches concurrently significantly speeds up the data retrieval process compared to sequential requests. `httpx` provides a modern async API.
    Use Sessions/aka client in httpx with SingletonFactory. 

3.  **Configuration Handling**: Make API interaction parameters (`stories_limit`, `fetch_batch_size`, `request_timeout`) configurable via `HackerNewsDatasourceConfiguration`. Allows users to tune performance and data volume.

4.  **Parsing Strategy**: The `Parser` transforms the raw JSON dictionary into a `HackerNewsStoryDocument`. Standardize metadata keys and format timestamps. Incorporate key metadata into the document text.


  # Task 2: Improving the RAG Blueprint
  
  This proposal outlines strategies for enhancing the RAG blueprint's deployment capabilities by moving to the cloud and improving its extensibility for easier maintenance and feature additions.

  ## 1. Deployment: Moving to the Cloud
  
  The current `build/workstation/runner.py` orchestrates local deployment using Docker Compose. A cloud deployment requires replacing this with cloud-native tools and practices.

### 1.1. Recommended Toolstack
*   **Cloud Provider** **AWS/GCP/Azure**. AWS for this one can use other based on expertise and tooling required and available. 
*   **Containerization:** **Docker** (Existing Dockerfiles can be reused).
*   **Orchestration:** **Kubernetes (AWS EKS - Elastic Kubernetes Service)**. Provides robust scaling, high availability, service discovery, and automated deployments, replacing Docker Compose orchestration.
*   **Workflow Orchestration:** **Airflow or CronJob (AWS MWAA or self hosted- Elastic Kubernetes Service)**. Replaces manual triggering. if the jobs aren't too complex and not heavily dependeny Cron Jobs are fine. Otherise Ariflow is better for scalability, complexity and robustness. 
*   **Infrastructure as Code (IaC):** **Terraform** (Cloud-agnostic) For declarative, repeatable, and version-controlled management of all cloud resources
*   **CI/CD Pipeline:** **GitHub Actions** (if using GitHub) Automates building Docker images, running tests, pushing images to a registry (ECR), and deploying applications to EKS
*   **Secrets Management:** **AWS Secrets Manager**. Securely stores and injects sensitive configuration (API keys, DB passwords) needed by application containers, replacing the local `.env` file approach.
*   **Monitoring & Logging:** **AWS CloudWatch** (Logs, Metrics, Alarms) potentially integrated with **Grafana**. Provides centralized observability, replacing the local file/console logger.
*   **(Optional) Message Queue:** **AWS SQS/KAFKA(AWS MSK or self hosted)**. To decouple long-running processes like embedding from synchronous API calls or triggers. If the sources are growing, volume and velocity, veracity is growing, kafka would be beneficial. It provides many gurantees. It's a scalable, streaming/batch and robust approach. If you have other data pipelines which also fit the use-case(streaming/events/queuing). This is a good option.


### 1.2. Key Scalability and Performance Considerations
- Run extraction tasks in parallel one per datasource (Ariflow/Kubernetes Job)
- Implement retry logic but within api rate-limit
- Rag Querying can use wbe scaling, kubernetes deployments with horizontal pod aurscaling(HPA) based on resources. 
- Employ load balancing via Kubernetes Ingress AWS ALB 
- Implement caching where needed



### 1.3. High-Level Deployment Strategy
1.  **Containerize:** Leverage existing `Dockerfile`s.
2.  **Define Infrastructure (IaC):** Use Terraform to provision AWS resources
3.  **CI/CD Pipeline Setup:**
    * Trigger pipeline on commit/merge
    * build docker images, Run Unit tests, push images to ECR, configure and inject secrets and deploy via helm/kubectl to EKS 
 4. **Monitoring Configuration:** Set up CloudWatch agents, dashboards, and alarms.


## 2. Extensibility: Making the System More Modular

The framework's modularity is good. Enhancements can improve developer experience and code reuse.
### 2.2. Improved Data Extraction Methods
*  Introduce a **Core HTTP Client Wrapper** (`core.http.AsyncHttpClient`) using `httpx`.
    *   *Implementation:* Provides standardized async requests with `tenacity` retries, rate limit handling, common auth, centralized logging/error handling. Readers use this wrapper
    reate 
*  **Core Cleaning Utilities** and **Core Parsers** for common formats (JSON, HTML, XML).
    *   *Implementation:* Reusable functions for advanced HTML cleaning, boilerplate removal, regex cleaning, etc., usable within custom `Cleaner` classes. Datasource-specific parsers can delegate common structural parsing.

*   **Benefit:** Reduces code duplication, improves robustness (standardized retries/cleaning), simplifies implementation of new readers/parsers/cleaners.
