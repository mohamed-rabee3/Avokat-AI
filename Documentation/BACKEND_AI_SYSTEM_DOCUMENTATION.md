# Avokat AI - Backend and AI System Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Components](#architecture-components)
3. [Data Flow Diagrams](#data-flow-diagrams)
4. [Backend Services](#backend-services)
5. [AI System Components](#ai-system-components)
6. [Database Architecture](#database-architecture)
7. [API Endpoints](#api-endpoints)
8. [Multilingual Support](#multilingual-support)
9. [Configuration](#configuration)
10. [Deployment](#deployment)

## System Overview

Avokat AI is a legal document analysis system that combines PDF processing, knowledge graph construction, and multilingual AI-powered chat capabilities. The system is designed to provide grounded legal assistance by analyzing uploaded documents and creating session-isolated knowledge graphs.

### Key Features
- **Session Isolation**: Each chat session maintains its own knowledge graph and document context
- **Multilingual Support**: Automatic language detection for Arabic, English, and mixed-language documents
- **Knowledge Graph**: Neo4j-based graph storage with entity and relationship extraction
- **Streaming Chat**: Real-time response generation with Server-Sent Events (SSE)
- **Document Processing**: PyMuPDF-based PDF text extraction and chunking
- **Legal Disclaimer**: Built-in legal disclaimers in all responses

## Architecture Components

### High-Level Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        UI[React Frontend]
    end
    
    subgraph "API Layer"
        API[FastAPI Backend]
        CORS[CORS Middleware]
    end
    
    subgraph "Service Layer"
        PDF[PDF Processor]
        LD[Language Detector]
        KG[Knowledge Graph Builder]
        LLM[LLM Service]
        RET[Retrieval Service]
        EMB[Embedding Service]
    end
    
    subgraph "Data Layer"
        SQLITE[(SQLite Database)]
        NEO4J[(Neo4j Aura Cloud)]
        FILES[File Storage]
    end
    
    subgraph "External Services"
        GEMINI[Gemini 2.5 Flash]
    end
    
    UI -->|HTTPS/SSE| API
    API --> CORS
    API --> PDF
    API --> LD
    API --> KG
    API --> LLM
    API --> RET
    API --> EMB
    
    PDF --> FILES
    LD --> KG
    KG --> NEO4J
    KG --> GEMINI
    LLM --> GEMINI
    RET --> NEO4J
    EMB --> KG
    
    API --> SQLITE
    
    classDef client fill:#e1f5fe
    classDef api fill:#f3e5f5
    classDef service fill:#e8f5e8
    classDef data fill:#fff3e0
    classDef external fill:#ffebee
    
    class UI client
    class API,CORS api
    class PDF,LD,KG,LLM,RET,EMB service
    class SQLITE,NEO4J,FILES data
    class GEMINI external
```

## Data Flow Diagrams

### Complete System Data Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as FastAPI
    participant S as SQLite
    participant P as PDF Processor
    participant L as Language Detector
    participant K as KG Builder
    participant N as Neo4j
    participant G as Gemini LLM
    participant R as Retrieval Service
    participant E as Embedding Service

    Note over U,E: Session Creation Flow
    U->>F: Create Session
    F->>A: POST /sessions
    A->>S: Create session record
    S-->>A: Session ID
    A-->>F: {session_id}
    F-->>U: Session created

    Note over U,E: Document Upload & Processing Flow
    U->>F: Upload PDF
    F->>A: POST /ingest (multipart)
    A->>S: Validate session
    A->>P: Process PDF
    P->>P: Extract text & chunk
    P-->>A: Document chunks
    A->>L: Detect language
    L-->>A: Language (arabic/english/mixed)
    A->>K: Extract knowledge graph
    K->>G: Generate entities/relationships
    G-->>K: Structured data
    K->>N: Store nodes & relationships
    K->>E: Generate embeddings
    E-->>K: Embedding vectors
    K->>N: Store document chunks with embeddings
    A->>S: Record upload metadata
    A-->>F: Processing complete
    F-->>U: Upload successful

    Note over U,E: Chat Flow
    U->>F: Send message
    F->>A: POST /chat
    A->>S: Store user message
    A->>R: Retrieve relevant context
    R->>N: Query knowledge graph
    N-->>R: Entities & relationships
    R->>N: Get document chunks
    N-->>R: Context chunks
    R-->>A: Retrieval result
    A->>L: Detect query language
    L-->>A: Query language
    A->>G: Generate response (streaming)
    G-->>A: Response chunks
    A->>S: Store assistant message
    A-->>F: Stream response
    F-->>U: Display response
```

### Document Processing Pipeline

```mermaid
flowchart TD
    START[PDF Upload] --> VALIDATE{Validate File}
    VALIDATE -->|Invalid| ERROR[Return Error]
    VALIDATE -->|Valid| EXTRACT[Extract Text with PyMuPDF]
    
    EXTRACT --> CHUNK[Chunk Documents]
    CHUNK --> DETECT[Detect Language]
    
    DETECT --> ARABIC{Language?}
    ARABIC -->|Arabic| ARABIC_PROMPT[Enhanced Arabic Prompts]
    ARABIC -->|English| ENGLISH_PROMPT[Standard English Prompts]
    ARABIC -->|Mixed| MIXED_PROMPT[Mixed Language Prompts]
    
    ARABIC_PROMPT --> LLM_EXTRACT[Gemini LLM Extraction]
    ENGLISH_PROMPT --> LLM_EXTRACT
    MIXED_PROMPT --> LLM_EXTRACT
    
    LLM_EXTRACT --> PARSE[Parse JSON Response]
    PARSE --> VALIDATE_JSON{Valid JSON?}
    VALIDATE_JSON -->|No| FALLBACK[Use Fallback Extraction]
    VALIDATE_JSON -->|Yes| CREATE_NODES[Create Graph Nodes]
    FALLBACK --> CREATE_NODES
    
    CREATE_NODES --> ADD_METADATA[Add Session & Language Metadata]
    ADD_METADATA --> STORE_NEO4J[Store in Neo4j]
    
    STORE_NEO4J --> GENERATE_EMB[Generate Embeddings]
    GENERATE_EMB --> STORE_CHUNKS[Store Document Chunks]
    STORE_CHUNKS --> SUCCESS[Processing Complete]
    
    classDef process fill:#e3f2fd
    classDef decision fill:#fff3e0
    classDef error fill:#ffebee
    classDef success fill:#e8f5e8
    
    class EXTRACT,CHUNK,DETECT,LLM_EXTRACT,PARSE,CREATE_NODES,ADD_METADATA,STORE_NEO4J,GENERATE_EMB,STORE_CHUNKS process
    class VALIDATE,ARABIC,VALIDATE_JSON decision
    class ERROR,FALLBACK error
    class SUCCESS success
```

### Knowledge Graph Construction Flow

```mermaid
flowchart TD
    DOCUMENT[Document Chunk] --> LANGUAGE[Language Detection]
    LANGUAGE --> PROMPT_ENHANCE[Prompt Enhancement]
    
    PROMPT_ENHANCE --> GEMINI[Gemini 2.5 Flash]
    GEMINI --> EXTRACT_ENTITIES[Extract Entities]
    GEMINI --> EXTRACT_RELATIONS[Extract Relationships]
    
    EXTRACT_ENTITIES --> VALIDATE_ENTITIES[Validate Entity Structure]
    EXTRACT_RELATIONS --> VALIDATE_RELATIONS[Validate Relationship Structure]
    
    VALIDATE_ENTITIES --> ADD_SESSION_META[Add Session Metadata]
    VALIDATE_RELATIONS --> ADD_SESSION_META
    
    ADD_SESSION_META --> CREATE_NODES[Create Neo4j Nodes]
    ADD_SESSION_META --> CREATE_EDGES[Create Neo4j Relationships]
    
    CREATE_NODES --> INDEX_NODES[Create Node Indexes]
    CREATE_EDGES --> INDEX_EDGES[Create Relationship Indexes]
    
    INDEX_NODES --> EMBED_CHUNK[Generate Chunk Embedding]
    INDEX_EDGES --> EMBED_CHUNK
    
    EMBED_CHUNK --> STORE_CHUNK[Store Document Chunk]
    STORE_CHUNK --> COMPLETE[Knowledge Graph Complete]
    
    classDef input fill:#e1f5fe
    classDef process fill:#e3f2fd
    classDef storage fill:#e8f5e8
    classDef complete fill:#c8e6c9
    
    class DOCUMENT input
    class LANGUAGE,PROMPT_ENHANCE,GEMINI,EXTRACT_ENTITIES,EXTRACT_RELATIONS,VALIDATE_ENTITIES,VALIDATE_RELATIONS,ADD_SESSION_META,CREATE_NODES,CREATE_EDGES,INDEX_NODES,INDEX_EDGES,EMBED_CHUNK,STORE_CHUNK process
    class COMPLETE complete
```

### Chat Response Generation Flow

```mermaid
flowchart TD
    USER_MSG[User Message] --> VALIDATE_SESSION[Validate Session]
    VALIDATE_SESSION --> STORE_USER[Store User Message]
    
    STORE_USER --> GET_HISTORY[Get Chat History]
    GET_HISTORY --> RETRIEVE_CONTEXT[Retrieve Knowledge Context]
    
    RETRIEVE_CONTEXT --> SEMANTIC_SEARCH[Semantic Search Chunks]
    RETRIEVE_CONTEXT --> GRAPH_TRAVERSAL[Graph Traversal Search]
    RETRIEVE_CONTEXT --> EXPAND_CONTEXT[Expand Context by Relationships]
    
    SEMANTIC_SEARCH --> COMBINE_RESULTS[Combine Retrieval Results]
    GRAPH_TRAVERSAL --> COMBINE_RESULTS
    EXPAND_CONTEXT --> COMBINE_RESULTS
    
    COMBINE_RESULTS --> DETECT_QUERY_LANG[Detect Query Language]
    DETECT_QUERY_LANG --> BUILD_PROMPT[Build Multilingual Prompt]
    
    BUILD_PROMPT --> SYSTEM_PROMPT[System Prompt with Disclaimer]
    BUILD_PROMPT --> CONTEXT_PROMPT[Context from Knowledge Graph]
    BUILD_PROMPT --> HISTORY_PROMPT[Recent Chat History]
    BUILD_PROMPT --> USER_PROMPT[User Question]
    
    SYSTEM_PROMPT --> GEMINI_STREAM[Gemini Streaming Response]
    CONTEXT_PROMPT --> GEMINI_STREAM
    HISTORY_PROMPT --> GEMINI_STREAM
    USER_PROMPT --> GEMINI_STREAM
    
    GEMINI_STREAM --> STREAM_CHUNKS[Stream Response Chunks]
    STREAM_CHUNKS --> STORE_ASSISTANT[Store Assistant Response]
    STORE_ASSISTANT --> EXTRACT_SOURCES[Extract Sources for Citations]
    EXTRACT_SOURCES --> RETURN_RESPONSE[Return Response with Sources]
    
    classDef input fill:#e1f5fe
    classDef process fill:#e3f2fd
    classDef ai fill:#f3e5f5
    classDef output fill:#e8f5e8
    
    class USER_MSG input
    class VALIDATE_SESSION,STORE_USER,GET_HISTORY,RETRIEVE_CONTEXT,SEMANTIC_SEARCH,GRAPH_TRAVERSAL,EXPAND_CONTEXT,COMBINE_RESULTS,DETECT_QUERY_LANG,BUILD_PROMPT,STORE_ASSISTANT,EXTRACT_SOURCES process
    class SYSTEM_PROMPT,CONTEXT_PROMPT,HISTORY_PROMPT,USER_PROMPT,GEMINI_STREAM,STREAM_CHUNKS ai
    class RETURN_RESPONSE output
```

## Backend Services

### 1. FastAPI Application (`main.py`)

The main FastAPI application orchestrates all services and provides the REST API endpoints.

**Key Features:**
- CORS middleware for cross-origin requests
- Lifespan management for service initialization
- Router inclusion for modular API structure
- Health check endpoints

**Service Initialization Order:**
1. SQLite database initialization
2. Neo4j connection establishment
3. Retrieval service setup
4. Embedding service initialization
5. LLM service configuration

### 2. Session Management (`routers/sessions.py`)

Manages chat sessions with full CRUD operations and session isolation.

**Endpoints:**
- `POST /sessions` - Create new session
- `GET /sessions` - List all sessions
- `GET /sessions/{id}` - Get specific session
- `PUT /sessions/{id}` - Update session
- `DELETE /sessions/{id}` - Delete session and all associated data

**Session Isolation:**
- Each session maintains separate knowledge graphs
- Cascade deletion removes all related data
- Neo4j data clearing on session deletion

### 3. Document Ingestion (`routers/ingest.py`)

Handles PDF upload, processing, and knowledge graph creation.

**Processing Pipeline:**
1. File validation and storage
2. PDF text extraction with PyMuPDF
3. Document chunking with configurable parameters
4. Language detection for multilingual support
5. Knowledge graph extraction with Gemini LLM
6. Neo4j storage with session isolation
7. Embedding generation and storage

**Rate Limiting:**
- 4-second delay between LLM requests
- Configurable chunk processing limits
- Error handling with graceful degradation

### 4. Chat Interface (`routers/chat.py`)

Provides streaming and non-streaming chat capabilities with knowledge graph integration.

**Features:**
- Server-Sent Events (SSE) for real-time streaming
- Non-streaming fallback option
- Chat history management
- Source extraction for citations
- Error handling with user-friendly messages

**Response Generation:**
1. Store user message in SQLite
2. Retrieve recent chat history
3. Query knowledge graph for relevant context
4. Generate response with Gemini LLM
5. Stream response chunks to client
6. Store assistant response

## AI System Components

### 1. Language Detection Service (`services/language_detector.py`)

**Purpose:** Automatic language detection for multilingual document processing.

**Supported Languages:**
- Arabic (Unicode ranges: \u0600-\u06FF, \u0750-\u077F, etc.)
- English (Latin characters)
- Mixed (combination of Arabic and English)

**Detection Algorithm:**
```python
def detect_language(self, text: str) -> str:
    arabic_chars = len(arabic_pattern.findall(text))
    english_chars = len(english_pattern.findall(text))
    total_chars = arabic_chars + english_chars
    
    arabic_ratio = arabic_chars / total_chars
    english_ratio = english_chars / total_chars
    
    if arabic_ratio > 0.3:
        return 'arabic' if english_ratio <= 0.2 else 'mixed'
    elif english_ratio > 0.5:
        return 'english'
    else:
        return 'mixed'
```

**Language-Specific Enhancements:**
- Arabic: Enhanced prompts with Arabic legal terminology
- Mixed: Preservation of both language contexts
- English: Standard processing

### 2. PDF Processing Service (`services/pdf_processor.py`)

**Technology:** PyMuPDF (fitz) for high-quality text extraction.

**Features:**
- Page-by-page text extraction
- Metadata preservation (page numbers, file info)
- Document chunking with RecursiveCharacterTextSplitter
- Error handling for corrupted PDFs

**Chunking Configuration:**
- Default chunk size: 1000 characters
- Default overlap: 100 characters
- Separators: ["\n\n", "\n", " ", ""]

### 3. Knowledge Graph Builder (`services/kg_builder.py`)

**Technology:** LangChain + Neo4j + Gemini LLM

**Entity Extraction:**
- Legal entities (persons, organizations, contracts, cases)
- Legal relationships (agreements, obligations, rights)
- Key legal concepts and terms
- Dates, amounts, and important details

**Graph Construction Process:**
1. Language-specific prompt enhancement
2. Gemini LLM-based entity extraction
3. JSON response parsing and validation
4. Neo4j node and relationship creation
5. Session and language metadata addition
6. Document chunk storage with embeddings

**Error Handling:**
- JSON parsing fallbacks
- Graceful degradation on LLM failures
- Comprehensive logging for debugging

### 4. LLM Service (`services/llm.py`)

**Model:** Gemini 2.5 Flash Lite

**Features:**
- Multilingual prompt building
- Streaming and non-streaming responses
- Context-aware response generation
- Legal disclaimer integration

**Prompt Structure:**
```
System Prompt (with disclaimer)
+ 
Context from Knowledge Graph
+ 
Recent Chat History
+ 
User Question
```

**Language-Specific Enhancements:**
- Arabic: Cultural and legal context awareness
- Mixed: Preservation of both language contexts
- English: Standard legal assistance

### 5. Retrieval Service (`services/retrieval.py`)

**Purpose:** Enhanced knowledge graph querying with multilingual support.

**Retrieval Strategy:**
1. **Semantic Search:** Retrieve all document chunks for comprehensive context
2. **Graph Traversal:** Search entities and relationships based on query terms
3. **Context Expansion:** Follow relationships to find connected entities
4. **Language Filtering:** Support for language-specific queries

**Search Features:**
- Meaningful term extraction with Arabic compound word handling
- Comprehensive Cypher queries across all node properties
- Relevance scoring based on content type
- Relationship traversal for context expansion

### 6. Embedding Service (`services/embedding_service.py`)

**Technology:** Sentence Transformers with fallback options

**Models (in order of preference):**
1. `paraphrase-MiniLM-L6-v2` (384 dimensions)
2. `distilbert-base-nli-mean-tokens` (768 dimensions)
3. `all-mpnet-base-v2` (768 dimensions)
4. `all-MiniLM-L12-v2` (384 dimensions)

**Fallback Strategy:**
- Simple local embedding using word hashing
- Fixed 100-dimensional vectors
- Basic text processing for reliability

**Features:**
- Batch embedding generation
- Cosine similarity computation
- Text cleaning and normalization
- Embedding serialization for storage

## Database Architecture

### SQLite Database (`db/sqlite.py`)

**Tables:**
- `sessions`: Chat session metadata
- `messages`: Chat history with token counts
- `uploads`: File upload records

**Features:**
- WAL mode for better concurrency
- Async SQLAlchemy integration
- Automatic timestamp management
- Cascade deletion for data integrity

### Neo4j Knowledge Graph (`db/neo4j.py`)

**Node Types:**
- `Entity`: Legal entities with properties
- `Fact`: Legal facts and evidence
- `Document`: Document metadata
- `LegalConcept`: Legal terms and concepts
- `Case`: Legal cases and proceedings
- `DocumentChunk`: Text chunks with embeddings

**Relationship Types:**
- `ABOUT`: Facts about entities
- `CONTAINS`: Documents containing facts
- `MENTIONS`: Documents mentioning entities
- `RELATED_TO`: Entity relationships
- `APPLIES_TO`: Legal concepts applying to entities
- `INVOLVES`: Cases involving entities

**Indexes:**
- Session isolation indexes on all node types
- Language-specific indexes for multilingual support
- Entity type and relationship type indexes
- Performance optimization indexes

**Session Isolation:**
- All nodes and relationships tagged with `session_id`
- All queries filtered by session ID
- Automatic cleanup on session deletion

## API Endpoints

### Session Management
```
POST   /sessions                    # Create session
GET    /sessions                   # List sessions
GET    /sessions/{id}              # Get session
PUT    /sessions/{id}              # Update session
DELETE /sessions/{id}              # Delete session
GET    /sessions/{id}/messages     # Get session messages
GET    /sessions/{id}/uploads      # Get session uploads
GET    /sessions/{id}/full         # Get complete session data
```

### Document Processing
```
POST   /ingest                     # Upload and process PDF
```

### Chat Interface
```
POST   /chat                       # Streaming chat
POST   /chat/non-streaming         # Non-streaming chat
GET    /chat/history/{session_id}  # Get chat history
```

### Neo4j Operations
```
POST   /neo4j/query                # Execute Cypher query
GET    /neo4j/stats/{session_id}   # Get session statistics
```

## Multilingual Support

### Language Detection
- Automatic detection using Unicode character analysis
- Support for Arabic, English, and mixed-language content
- Language-specific prompt enhancements

### Arabic Language Features
- Enhanced prompts with Arabic legal terminology
- Cultural context awareness
- Right-to-left text handling considerations
- Arabic compound word mapping

### Mixed Language Support
- Preservation of original language in entities
- Cross-language relationship detection
- Language-specific indexing for efficient queries

### Language-Specific Processing
- Arabic documents receive enhanced prompts
- English documents use standard processing
- Mixed-language documents maintain both contexts

## Configuration

### Environment Variables
```bash
# Database Configuration
DATABASE_URL=sqlite+aiosqlite:///./avokat.db
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j

# AI Services
GEMINI_API_KEY=your-gemini-api-key

# API Configuration
API_TITLE=Avokat AI API
API_VERSION=1.0.0
DEBUG=false
```

### Service Configuration
- **PDF Processing:** Configurable chunk size and overlap
- **LLM Service:** Rate limiting and error handling
- **Embedding Service:** Model selection and fallback options
- **Retrieval Service:** Search limits and language filtering

## Deployment

### Prerequisites
- Python 3.8+
- Neo4j Aura Cloud instance
- Gemini API key
- PyMuPDF installation

### Setup Steps
1. **Environment Setup:**
   ```bash
   py -m venv venv
   venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. **Configuration:**
   - Set environment variables
   - Configure Neo4j Aura connection
   - Set Gemini API key

3. **Database Initialization:**
   - SQLite tables created automatically
   - Neo4j indexes created on startup

4. **Service Startup:**
   ```bash
   uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
   ```

### Health Checks
- `/health` endpoint for service status
- Database connectivity verification
- External service availability checks

### Monitoring
- Comprehensive logging throughout the system
- Error tracking and graceful degradation
- Performance metrics for key operations

---

This documentation provides a comprehensive overview of the Avokat AI backend and AI system architecture. The system is designed for scalability, multilingual support, and robust error handling while maintaining session isolation and legal compliance through built-in disclaimers.
