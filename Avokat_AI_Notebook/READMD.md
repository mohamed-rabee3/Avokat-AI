# Legal AI Chatbot

A **Graph-based Retrieval-Augmented Generation (RAG) system** designed for legal documents.  
It combines a **Neo4j knowledge graph** with a **large language model (LLM)** to answer legal questions accurately, providing context-aware responses.

---

## 🔗 Live Demo

Access the deployed chatbot here: [Legal AI Chatbot](https://26175c46c778.ngrok-free.app/)

Watch the demo video here: [Demo Video](https://drive.google.com/drive/folders/1i3-EAcbnvX6kA27oiIy9cHtP2WGO4TZP?usp=sharing)

---

## 📝 Core Components

### 1. Document Ingestion and Chunking
- Legal PDF documents are loaded using `PyPDFLoader`.
- Documents are split into smaller chunks using `RecursiveCharacterTextSplitter` for better retrieval.
- Each chunk includes metadata (`id`, `source`, `page`, etc.) for traceability.

**Purpose:** Manage large legal documents efficiently and prepare them for semantic search.

---

### 2. Embedding and Vector Store
- Chunks are converted into **dense vector embeddings** using `HuggingFaceEmbeddings`.
- Embeddings are stored in **Neo4j** as a **vector store** to enable semantic retrieval.

**Purpose:** Allows retrieval based on semantic similarity instead of simple keyword matching.

---

### 3. Neo4j Knowledge Graph
- `Neo4jVector` and `Neo4jGraph` manage the knowledge graph.
- Each chunk is represented as a **node**, with optional relationships to connect related chunks.
- Queries retrieve relevant chunks using **keywords or semantic similarity**.

**Purpose:** Provides structured context for RAG, forming the retrieval backbone.

---

### 4. Large Language Model (LLM)
- LLM is loaded using HuggingFace (`AutoModelForCausalLM` and `pipeline`).
- Answers are generated based on retrieved chunks from Neo4j.
- Prompts include:
  - Knowledge graph context
  - Document context
  - User question

**Purpose:** Generates human-like, context-aware answers grounded in the legal documents.

---

### 5. Retrieval-Augmented Generation (RAG) Pipeline
**Workflow:**
1. User submits a question.
2. Relevant chunks are retrieved from Neo4j using semantic search.
3. LLM generates an answer conditioned on retrieved context.

Optional: `RetrievalQAWithSourcesChain` can provide answers with source citations.

---

### 6. Chat History
- Questions and answers are stored in a local SQLite database (`chat_history.db`).
- History is retrievable and displayed to maintain context across sessions.

**Purpose:** Maintains conversation continuity and allows users to review past interactions.

---

## ⚙️ Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/mohamed-rabee3/Avokat-AI.git
cd Avokat-AI
```
2. Create and switch to a new branch:
```bash
git checkout -b ahmed_eltokhy_branch
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Large Language Model (LLM) Used

- **Model:** `NousResearch/Nous-Hermes-13b`  
- **Type:** Causal Language Model  
- **Purpose:** Generates answers based on retrieved document and knowledge graph context.

---

## References and Tutorials

- [RAG Tutorial: How to Build a RAG System on a Knowledge Graph](https://neo4j.com/blog/developer/rag-tutorial/)  
- [What is GraphRAG?](https://neo4j.com/blog/genai/what-is-graphrag/)  
- [LangChain Full Support with Neo4j Vector Index](https://neo4j.com/blog/developer/langchain-library-full-support-neo4j-vector-index/)

---

## Key Takeaways

- Neo4j is the **retrieval backend** for semantic search.  
- LLM is the **generative backend** for human-like answers.  
- The RAG system ensures answers are **accurate, concise, and grounded in legal documents**.

---

## Hugging Face Model Link

- **Model Used:** [NousResearch/Nous-Hermes-13b](https://huggingface.co/NousResearch/Nous-Hermes-13b)  
- **Purpose:** Provides powerful causal language generation to answer questions based on retrieved documents and knowledge graph context.
