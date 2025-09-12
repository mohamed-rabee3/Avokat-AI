## Legal Chatbot MVP – Full Documentation Plan (LlamaIndex + Graphiti, with Embeddings)

### 1. Objectives and Scope
- **Primary goals**:
  - **Per-chat isolation**: Each chat session uses only its own uploaded documents; no cross-session leakage.
  - **Grounded answers**: Retrieval-augmented responses using session-scoped knowledge and recent chat history.
  - **Safety**: Prominent disclaimer in UI and in every model response: “This is not legal advice.”
  - **Simplicity**: Single-user assumption; 1–2 PDFs per session; minimal UI; shippable in 1 day.
- **Non-goals (MVP)**:
  - Multi-user auth/roles/ACLs; enterprise SSO.
  - Cross-session search, merges, or content sharing.
  - Production observability (full tracing/metrics), rate limiting, or advanced security hardening.

### 2. Architecture Overview
- **Frontend (React)**: Session creation/selection, per-session file upload, chat UI with citations and history.
- **Backend (FastAPI)**: Session management, ingestion, retrieval, LLM calls, history persistence, isolation enforcement.
- **RAG (LlamaIndex)**: PDF/text loading, chunking, embeddings, retrieval orchestration.
- **Knowledge Graph (Graphiti + Neo4j)**: Session-scoped facts/snippets and relationships; temporal metadata optional.
- **Persistence**: SQLite for sessions/messages/uploads; Neo4j for KG; both keyed by `session_id`.
- **LLM (Gemini)**: Answer synthesis from KG facts + chat history (low temperature, deterministic, with disclaimer).

#### 2.1 Data Flow (High Level)
```mermaid
sequenceDiagram
    autonumber
    participant F as Frontend (React)
    participant A as API (FastAPI)
    participant LI as LlamaIndex (Ingestion/Retrieval)
    participant G as Graphiti/Neo4j (KG)
    participant DB as SQLite (Sessions/History)
    participant LLM as Gemini (Vertex AI)

    F->>A: POST /sessions (name?)
    A->>DB: Create session (id, timestamps)
    A-->>F: {session_id}

    F->>A: POST /ingest (multipart: session_id, file)
    A->>LI: Load, chunk, embed
    LI->>G: Add episodes with session_id (Graphiti creates entities/edges)
    A-->>F: {status: success, stats}

    F->>A: POST /chat {session_id, message}
    A->>DB: Load recent history (token-limited)
    A->>G: Retrieve facts filtered by session_id
    A->>LLM: Prompt = disclaimer + facts + clipped history + user message
    LLM-->>A: Response (stream or final)
    A->>DB: Append user + assistant messages
    A-->>F: Stream/final response (+sources)
```

#### 2.2 Context and Components
```mermaid
graph TD
    subgraph Client
        UI[React Frontend]
    end
    subgraph Server
        API[FastAPI Backend]
        RAG[LlamaIndex Pipeline]
        KG[Graphiti + Neo4j]
        DB[SQLite]
        LLM[Gemini]
    end

    UI -->|HTTPS JSON/SSE| API
    API -->|Ingest/Retrieve| RAG
    RAG -->|Facts/Edges (session_id)| KG
    API -->|History CRUD| DB
    API -->|Prompt/Response| LLM
```

### 3. Storage, Data Model, and Isolation
- **Global principle**: All KG entities and edges carry `session_id`. Every query and write is scoped by `session_id`.

#### 3.1 SQLite (sessions, messages, uploads)
- **Tables**:
  - `sessions(id, name, created_at, updated_at)`
  - `messages(id, session_id, role, content, token_count, created_at)`
  - `uploads(id, session_id, file_name, size_bytes, created_at)`
- **Settings**: WAL enabled; index on `messages.session_id` for fast history retrieval.
- **History policy**: Maintain token counts to clip history by token budget, not message count.

#### 3.2 Neo4j (Graphiti-backed KG)
- **Isolation**: Add `session_id` property to all nodes and relationships. All Cypher includes `WHERE ... session_id = $session_id`.
- **Indices**: Create indices on session property for labels used (e.g., entity/fact labels). One-time creation on backend startup.
- **Temporal metadata**: Set `reference_time` when ingesting episodes to enable time-aware queries later (optional for MVP).
- **Startup tasks (local Graphiti)**: On backend startup, call Graphiti’s utility to build indices and constraints (once), then proceed with ingestion.

### 4. RAG Pipeline (with Embeddings)

#### 4.1 Ingestion (LlamaIndex)
- **Readers**: Use LlamaIndex PDF/text readers to extract text from uploaded files.
- **Chunking**: Sentence-level splitter with moderate chunk size and small overlap (optimize for recall and synthesis).
- **Embeddings**: Use a single embedding model provider for consistency across:
  - LlamaIndex chunk vectors (per-session vector index)
  - Graphiti fact/entity vectors (if enabled)
- **Mapping to KG**: Convert chunks to facts/snippets with citations (doc name, section), attach `session_id` and optional `reference_time`, and upsert via Graphiti.
- **Idempotency**: Upserts keyed by `doc_id` + `section_id` + `session_id` to avoid duplicates.

#### 4.2 Retrieval (Hybrid recommended)
- **Scope first (local Graphiti)**: Enforce `session_id` filtering in all Neo4j/Graphiti-backed queries. If high-level search doesn’t expose `session_id`, run a scoped Cypher or use Graphiti methods that respect session metadata.
- **Top‑K strategy**: Retrieve semantically similar facts/snippets via embeddings; optionally combine with keyword/BM25 and rerank.
- **Diversity**: Favor coverage across relevant document sections; avoid redundant snippets.
- **Context pack**: Build a compact set of facts + citations for prompt augmentation.

#### 4.3 Prompting (Gemini)
- **System instruction**: The assistant must use only session KG context and recent chat history; include the legal disclaimer.
- **Prompt structure** (token-aware):
  - Disclaimer (fixed)
  - Session KG facts (bulleted, concise, with citations)
  - Recent chat history (role-labeled, clipped by tokens)
  - User message
- **Parameters**: Low temperature; conservative safety settings as available.

### 5. API Design and Contracts

#### 5.1 Endpoints
- **POST `/sessions`**
  - Body: optional `name`
  - Response: `session_id`
- **POST `/ingest`**
  - Multipart: `session_id`, `file`
  - Validates file type/size; runs ingestion; persists upload metadata
  - Response: `status`, ingestion stats (e.g., nodes/facts count)
- **POST `/chat`**
  - Body: `session_id`, `message`
  - Behavior: load recent history (token-limited), retrieve KG facts (scoped), call LLM, append messages
  - Response: streaming text or final `{response, sources}` with citations
- **GET `/history/{session_id}`**: Returns ordered messages.
- **GET `/history/list`**: Returns `{id, name, last_updated}` for all sessions.

#### 5.2 Errors
- 400: missing/invalid fields; invalid file type/size.
- 404: session not found.
- 409: optional duplicate upload conflict.
- 500: ingestion/LLM errors (return friendly message; log diagnostics).

#### 5.3 Streaming
- **Preferred**: Server-Sent Events (SSE) for incremental tokens.
- **Fallback**: Poll for final response if SSE is not feasible on Day‑1.

### 6. Frontend (React) Specification

#### 6.1 Views and Components
- **SessionList**: Create new session; select existing sessions.
- **ChatView**: Header shows current session; messages list; input box; citations under assistant replies.
- **UploadModal**: Upload documents to the current session.
- **HistoryPanel**: Collapsible; shows prior messages with timestamps.

#### 6.2 State and Integration
- Maintain `session_id` in app state (persist in localStorage for resume).
- On session switch: load history and show upload stats.
- Chat submission: add optimistic user message; stream or show loading until assistant reply completes.

#### 6.3 UX
- Show session badge to avoid confusion.
- Disable chat input until at least one document ingested; show guidance to upload.
- Toasts for upload/ingestion status and errors.

#### 6.4 Component Tree and Responsibilities
```mermaid
graph TD
    App[App Root] --> Nav[TopBar]
    App --> Sidebar[SessionList]
    App --> Main[ChatView]
    Main --> Header[ChatHeader]
    Main --> Messages[MessageList]
    Main --> Composer[MessageComposer]
    Main --> HP[HistoryPanel]
    App --> Modal[UploadModal]

    Sidebar:::panel
    Main:::panel
    Modal:::overlay

    classDef panel fill:#f6f8fa,stroke:#d0d7de,color:#24292f
    classDef overlay fill:#fff7ed,stroke:#f59e0b,color:#92400e
```

- **App Root**: Holds global state (current `session_id`, cached sessions, messages, uploads, UI flags). Persists `session_id` in localStorage for resume.
- **TopBar**: Shows product name and global disclaimer (always visible).
- **SessionList**: Displays sessions with name and `last_updated`; actions: New Session, Select Session (loads history and uploads), optional delete/rename.
- **ChatView**: Main workspace for active session.
  - **ChatHeader**: Session name/badge; Upload button (opens `UploadModal`); small info on uploaded files count.
  - **MessageList**: Renders user/assistant bubbles; assistant messages show citations list (collapsible per message).
  - **MessageComposer**: Multiline input with send button; disabled until documents are ingested; shows token/char limit feedback.
  - **HistoryPanel**: Optional side drawer with chronological messages and quick navigation; can be hidden on small screens.
- **UploadModal**: File input (accept PDF/text). Shows validation, upload progress, and ingestion result summary.

#### 6.5 Detailed Screen States and Behaviors
- **SessionList**
  - Empty state: “No sessions yet. Create a new chat to begin.”
  - Card/list entries: name, last updated, files count, messages count.
  - Actions: New Session (creates and selects); Select (loads history); optional Delete (danger/confirm).

- **ChatView**
  - Empty state (no uploads): Info banner with CTA “Upload documents to this session to enable grounded answers.” Composer disabled.
  - Ready state (after ingestion): Composer enabled; header shows file count; MessageList shows history if any.
  - Streaming state: Assistant bubble reserves space and appends tokens incrementally; show typing indicator.
  - Error state: Non-blocking alert at top of ChatView; composer remains enabled unless error is fatal.

- **UploadModal**
  - Validates MIME and file size before POST.
  - Progress bar for upload; then “Processing/ingesting…” step with spinner.
  - Success summary: nodes/facts ingested; Close returns to ChatView with updated state.
  - Failure: Show error details and retry option.

- **Message rendering**
  - Assistant messages display citations (document, section/page). Citations are clickable and collapsible per message.
  - Long content is clamped with “Show more.” Keyboard accessible toggles.

#### 6.6 State Management
- **Global state shape (conceptual)**
  - `currentSessionId: string | null`
  - `sessions: Array<{ id, name, lastUpdated }>` (lazy-loaded)
  - `messagesBySession: Map<session_id, Array<{ id, role, content, createdAt, sources? }>>`
  - `uploadsBySession: Map<session_id, Array<{ id, fileName, sizeBytes, createdAt }>>`
  - `ui: { isUploading: boolean, isStreaming: boolean, error?: string }`
- **Persistence**: Store only `currentSessionId` in localStorage; cache lists in memory.
- **History loading**: On session select, fetch recent history and merge into `messagesBySession`.

#### 6.7 Networking and Integration
- **Base URL**: Use relative API URLs for all calls [[memory:8655365]].
- **Sessions**
  - POST `/sessions` → select returned `session_id` and persist.
  - GET `/history/list` to populate SessionList (optional for MVP; can build list manually in memory as sessions are created).
- **Ingestion**
  - POST `/ingest` (multipart): include `session_id` and `file`.
  - On success: update `uploadsBySession` and enable composer; show toast.
- **Chat**
  - POST `/chat`: body `{ session_id, message }`.
  - Streaming (SSE) recommended: append tokens to the in-flight assistant bubble; fallback to non-streaming request/response if SSE unsupported.
  - On completion: persist assistant message with `sources`.
- **Error mapping**: 400/404 errors show user-friendly messages (“Invalid file,” “Session not found”); 500 shows fallback guidance.

#### 6.8 Streaming UX (SSE) and Fallback
- **SSE**
  - On send: create a placeholder assistant bubble.
  - On each event: append content; keep scroll pinned to bottom unless the user scrolled up.
  - Heartbeat/keepalive messages ignored; handle stream end and error events.
- **Fallback**
  - If SSE not available, display a spinner and poll (or use non-streaming endpoint) until completion.

#### 6.9 Accessibility and Keyboard Support
- Keyboard
  - Enter to send; Shift+Enter for newline.
  - Escape to close `UploadModal`.
  - Tab order: SessionList → ChatHeader → MessageList → Composer.
- ARIA
  - Assign roles/labels to modal, lists, and buttons; use `aria-expanded` for citation toggles.
  - Respect “Reduce Motion” preference; avoid aggressive auto-scrolling.

#### 6.10 Responsiveness
- Breakpoints: 
  - Mobile: stacked layout; HistoryPanel hidden by default; modal is full-screen.
  - Tablet: collapsible SessionList; ChatView takes majority width.
  - Desktop: 3‑pane feel (SessionList, ChatView, optional HistoryPanel).

#### 6.11 Visual and Content Guidelines
- Display the legal disclaimer in the header and before the first assistant response in each session.
- Use clear, muted styling for citations; provide copy-to-clipboard for citation entries.
- Provide consistent empty state illustrations/text to guide users.

#### 6.12 UI Flows (Mermaid)
Upload Flow
```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant UI as UploadModal
    participant API as /ingest
    U->>UI: Select file + Confirm
    UI->>API: POST multipart (session_id, file)
    API-->>UI: 202/201 ingesting → success stats
    UI-->>U: Toast success + close modal
```

Chat Flow
```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant C as Composer
    participant API as /chat
    participant ML as Messages
    U->>C: Type message + Send
    C-->>ML: Add user bubble (optimistic)
    C->>API: POST { session_id, message }
    API-->>ML: SSE tokens (stream) / final response
    ML-->>ML: Render assistant bubble with citations
```


### 7. Configuration, Security, and Logging
- **Configuration (env)**: Neo4j URI/user/pass; embedding provider config; Gemini model and auth; SQLite path.
- **Security**: Never expose secrets to frontend; validate file types and sizes; limit message length.
- **CORS**: Restrict to local/frontend origin during MVP.
- **Logging**: Log request IDs, `session_id`, timings; do not log document content. For Neo4j driver calls, explicitly set the target database for efficiency and determinism.

### 8. Setup and Operations (Day‑1)
- **Prerequisites**: Running Neo4j (Docker or Desktop) with credentials; internet for LLM/embeddings.
- **Environment**: Set required variables for backend services and providers.
- **Virtual environment**: On Windows, create with "py -m venv venv" and activate with "venv\Scripts\Activate.ps1".
- **Startup order**: Neo4j → Backend (ensures indices/constraints created) → Frontend.
- **Sanity checks**: Create session; upload a small PDF; ingestion returns stats; ask a question; verify citations.

### 9. Testing and Validation
- **Isolation test**: Two sessions with different PDFs; ensure answers only cite the active session’s docs.
- **No-doc test**: Chat without uploads yields a helpful prompt to upload first; no hallucinated content.
- **Follow-up coherence**: Multi-turn dialog where the second question references the first answer; verify continuity.
- **Citations**: Validate that cited docs/sections correspond to retrieved context.
- **Performance**: Ingestion ≤ ~60s for a 10–20 page PDF; chat p50 ≤ ~5s (short prompts).

### 10. KPIs and Acceptance Criteria
- **Functional**: ≥90% answers include correct citations; 0 cross-session leakage in tests; coherent follow-ups ≥80%.
- **Performance**: Ingestion and chat latency targets met for small PDFs and short prompts.
- **Reliability**: Error rate ≤2% over a small demo load (ingest+chat).

### 11. Risks and Fallbacks
- **PDF parsing quality**: If extraction is poor, pre-convert PDFs to text before ingestion; keep pipeline identical.
- **Graphiti integration**: If blocked, store/retrieve chunks directly via Neo4j with `session_id` and simple Cypher; add Graphiti later.
- **Streaming complexity**: If SSE is unstable, use non-streaming responses for MVP while preserving the endpoint.

### 12. Operational Playbook
- **Daily ops**: Keep PDFs small for demos; rotate logs; monitor basic timings.
- **Troubleshooting**:
  - Ingestion failures → check file type/size; embedding credentials; chunking parameters.
  - Slow retrieval → verify Neo4j indices; reduce top‑K; reduce chunk size.
  - Cross-session leakage → audit all queries for `session_id` filters.
  - LLM errors → verify credentials/model; reduce token load by trimming facts/history.

### 13. Delivery Checklist
- **Backend**: Env documented; indices/constraints created on startup; `session_id` filters in all KG queries; consistent errors; prompt contains disclaimer.
- **Frontend**: New Chat flow; per-session uploads; chat with citations; visible disclaimer; streaming or polling implemented.
- **RAG/Storage**: LlamaIndex ingestion configured with embeddings; Neo4j indices verified; SQLite in WAL mode.
- **Tests**: Isolation, no-doc, follow-up, and citation accuracy validated.

### 14. Roadmap (Post-MVP)
- Multi-user auth and per-user isolation.
- Richer entity/relation extraction and temporal queries.
- Document versioning and session merge/export.
- Observability (metrics, tracing) and safety evaluations.


