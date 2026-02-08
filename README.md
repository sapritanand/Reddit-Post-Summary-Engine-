# Reddit Post Summary Engine (RPSE)

**RPSE** is a robust, production-ready asynchronous engine designed to bridge the gap between massive social media datasets and actionable insights. By leveraging the **Reddit API (PRAW)** and state-of-the-art **Large Language Models (LLMs)**, this engine automates the extraction, cleaning, and abstractive summarization of complex, multi-threaded community discussions.

---

### 🛡️ Core Value Proposition
*   **Noise Reduction**: Filters out low-signal comments to focus on high-engagement insights.
*   **Scalable Intelligence**: Modular backend support for OpenAI, local Transformers, or proprietary LLMs.
*   **Architectural Flexibility**: Operates as a CLI tool, a portable Docker microservice, or a Python library integrated into larger data pipelines.

---

### 🏗️ System Architecture

The following diagram illustrates the flow from raw data ingestion to the final summary generation:

```mermaid
graph TD
    A[User/CLI Input] --> B[Environment Config]
    B --> C[Reddit Client Layer]
    C --> D{PRAW Ingestion}
    
    subgraph "Data Processing Pipeline"
    D --> E[Thread Flattening]
    E --> F[Content Sanitization]
    F --> G[Token Optimization]
    end
    
    G --> H[LLM Orchestrator]
    
    subgraph "Summarization Backend"
    H --> I[OpenAI API]
    H --> J[Local LLM / HuggingFace]
    end
    
    I & J --> K[Output Formatter]
    K --> L[Final Summary: Short/Detailed]
    L --> M[Cache/Database]
