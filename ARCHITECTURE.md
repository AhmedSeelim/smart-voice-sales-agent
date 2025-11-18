# System Architecture

This document explains the complete architecture of the Smart Hardware Sales Agent, detailing how LiveKit, Gemini Live API, and RAG technology work together to create a voice-powered shopping assistant.

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                              │
│                      (React + LiveKit Client)                       │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │  • User speaks in Arabic                                    │   │
│  │  • Microphone captures audio                                │   │
│  │  • LiveKit components handle WebRTC                         │   │
│  │  • Real-time voice status updates                           │   │
│  └────────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ WebRTC Audio Stream
                           │ (Low latency < 100ms)
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│                       LIVEKIT MEDIA SERVER                          │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │  • Real-time audio routing                                  │   │
│  │  • WebRTC signaling and media transport                     │   │
│  │  • Adaptive bitrate control                                 │   │
│  │  • Room management and participant handling                 │   │
│  └────────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ Agent Audio Stream
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      PYTHON AGENT (Backend)                         │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │              GEMINI LIVE API INTEGRATION                    │   │
│  │                                                              │   │
│  │  ┌──────────────────────────────────────────────────────┐ │   │
│  │  │  1. Speech-to-Text (Arabic)                          │ │   │
│  │  │     • Real-time transcription                        │ │   │
│  │  │     • Arabic language optimization                   │ │   │
│  │  └──────────────────────────────────────────────────────┘ │   │
│  │                           ↓                                 │   │
│  │  ┌──────────────────────────────────────────────────────┐ │   │
│  │  │  2. Natural Language Understanding                   │ │   │
│  │  │     • Intent recognition                             │ │   │
│  │  │     • Entity extraction                              │ │   │
│  │  │     • Context maintenance                            │ │   │
│  │  └──────────────────────────────────────────────────────┘ │   │
│  │                           ↓                                 │   │
│  │  ┌──────────────────────────────────────────────────────┐ │   │
│  │  │  3. Function Calling Decision                        │ │   │
│  │  │     • Determine if tools are needed                  │ │   │
│  │  │     • Select appropriate function                    │ │   │
│  │  │     • Extract parameters                             │ │   │
│  │  └──────────────────────────────────────────────────────┘ │   │
│  └────────────────────────┬────────────────────────────────────┘   │
│                           │                                         │
│                           ↓                                         │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                   FUNCTION TOOLS LAYER                      │   │
│  │                                                              │   │
│  │  • search_products(query, top_k)                            │   │
│  │  • make_product_request(user, address, product_id)          │   │
│  │  • make_product_request_by_name(user, address, name)        │   │
│  │  • get_product_details(product_id)                          │   │
│  │  • get_product_details_by_name(product_name)                │   │
│  └────────────────────────┬────────────────────────────────────┘   │
│                           │                                         │
│                           ↓                                         │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                DATABASE MANAGER                             │   │
│  │           (Unified Interface Layer)                         │   │
│  │                                                              │   │
│  │  ┌────────────────────┐         ┌────────────────────┐    │   │
│  │  │   VECTOR DATABASE  │         │   SQL DATABASE     │    │   │
│  │  │      (FAISS)       │         │    (SQLite)        │    │   │
│  │  │                    │         │                    │    │   │
│  │  │ • Product          │         │ • Product table    │    │   │
│  │  │   embeddings       │         │ • Inventory        │    │   │
│  │  │ • 768-dim vectors  │         │ • Requests table   │    │   │
│  │  │ • Cosine           │         │ • ACID             │    │   │
│  │  │   similarity       │         │   transactions     │    │   │
│  │  │ • Fast search      │         │ • Real-time qty    │    │   │
│  │  │   (< 50ms)         │         │                    │    │   │
│  │  └────────────────────┘         └────────────────────┘    │   │
│  └────────────────────────────────────────────────────────────┘   │
│                           │                                         │
│                           │ Results returned                        │
│                           ↓                                         │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │              GEMINI RESPONSE GENERATION                     │   │
│  │                                                              │   │
│  │  • Integrate tool results with conversation context         │   │
│  │  • Generate natural Arabic response                         │   │
│  │  • Text-to-Speech synthesis                                 │   │
│  │  • Voice character (Puck)                                   │   │
│  └────────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ Voice Audio Response
                           │
                           ↓
                    Back to User via LiveKit
```

## 🔄 Request Flow Diagram

### Scenario: User asks "أحتاج معالج قوي للألعاب" (I need a powerful gaming processor)

```
1. VOICE INPUT
   User → Microphone → React App → LiveKit Client
   
2. AUDIO TRANSMISSION
   LiveKit Client → WebRTC Stream → LiveKit Server → Python Agent
   
3. GEMINI PROCESSING
   Audio → Gemini Live API → Arabic Speech Recognition
   
   Transcription: "أحتاج معالج قوي للألعاب"
   
4. INTENT UNDERSTANDING
   Gemini NLU determines:
   - Intent: Search for products
   - Entities: {category: "processor", requirement: "gaming", performance: "powerful"}
   - Action: Call search_products()
   
5. FUNCTION EXECUTION
   Agent executes: search_products("معالج قوي للألعاب", top_k=2)
   
6. RAG PIPELINE
   a) Query Embedding:
      "معالج قوي للألعاب" → Transformer Model → 768-dim vector
   
   b) Vector Search:
      Query vector → FAISS Index → Cosine similarity
      
   c) Top Results Retrieved:
      - AMD Ryzen 9 7950X (score: 0.87)
      - Intel Core i9-13900K (score: 0.85)
   
   d) Inventory Enrichment:
      Product IDs → SQLite Query → Real-time quantities
      - Ryzen 9: 15 units available
      - i9-13900K: 10 units available
   
7. CONTEXT RETURN
   Formatted results → Gemini context:
   "Found 2 products:
    1. AMD Ryzen 9 7950X - 16 cores, gaming optimized - 15 in stock
    2. Intel i9-13900K - 24 cores, professional gaming - 10 in stock"
   
8. RESPONSE GENERATION
   Gemini synthesizes natural response:
   "وجدت لك معالجين ممتازين للألعاب..."
   
9. VOICE SYNTHESIS
   Text → Gemini TTS → Arabic audio (Puck voice)
   
10. AUDIO DELIVERY
    Agent → LiveKit Server → Client → User's speakers
```

## 🧩 Component Details

### 1. Frontend (React + LiveKit Client)

**Technology Stack:**
- React 18
- Vite (build tool)
- @livekit/components-react
- @livekit/components-styles

**Key Components:**

```javascript
// App.jsx structure
LiveKitRoom
├── Token authentication
├── Audio/video configuration
├── Connection management
└── VoiceAgent component
    ├── Voice status display
    ├── Visual feedback (wave animation)
    └── useVoiceAssistant() hook
        ├── state: "listening" | "thinking" | "speaking"
        └── audioTrack: MediaStreamTrack
```

**Responsibilities:**
- Capture user microphone input
- Display connection and voice status
- Handle WebRTC session lifecycle
- Render audio output from agent

**Data Flow:**
```
User Voice → getUserMedia() → MediaStream → LiveKit Track → 
→ Publish to Room → Agent receives

Token Generation:
User enters name → Frontend requests token from backend (http://localhost:5001/getToken) →
→ FastAPI server generates JWT → Frontend connects to LiveKit with token
```

### 2. LiveKit Media Server

**Architecture:**
- SFU (Selective Forwarding Unit) architecture
- WebRTC STUN/TURN servers
- Signaling server for room management

**Features:**
- Low-latency audio routing (< 100ms)
- Adaptive bitrate control
- Network resilience (jitter buffer, packet loss recovery)
- Room-based isolation
- Participant management

**Connection Flow:**
```
1. User enters name in frontend
2. Frontend sends GET request to http://localhost:5001/getToken?name=<username>
3. FastAPI server (server.py) receives request
4. Server creates LiveKit access token with room permissions
5. Token sent back to frontend as JSON
6. Frontend connects to LiveKit server with token
7. WebRTC negotiation (SDP offer/answer)
8. Media tracks established
9. Agent joins same room as participant
10. Bidirectional audio streaming active
```

### 3. Python Agent (Backend Core)

**Technology Stack:**
- livekit-agents SDK
- livekit-plugins-google (Gemini integration)
- Python asyncio for concurrent operations

**Agent Lifecycle:**

```python
async def entrypoint(ctx: JobContext):
    # 1. Connect to LiveKit room
    await ctx.connect()
    
    # 2. Initialize agent with Gemini LLM
    agent = HardwareSalesAgent()
    
    # 3. Create session
    session = AgentSession()
    
    # 4. Start session (begins listening)
    await session.start(room=ctx.room, agent=agent)
    
    # Session runs until disconnect
```

**Agent States:**
- `listening`: Capturing user voice input
- `thinking`: Processing request (LLM + tools)
- `speaking`: Generating and playing voice response

### 4. Gemini Live API Integration

**Model Configuration:**
```python
llm = google.realtime.RealtimeModel(
    model="gemini-2.5-flash-native-audio-preview-09-2025",
    voice="Puck",
    temperature=0.8,
    instructions="<system_prompt>"
)
```

**Capabilities:**

1. **Native Audio Processing:**
   - Direct audio-to-audio processing
   - No intermediate text conversion required
   - Lower latency than STT → LLM → TTS pipeline

2. **Multilingual Support:**
   - Optimized for Arabic language
   - Natural pronunciation
   - Cultural context awareness

3. **Function Calling:**
   - Automatic tool selection based on user intent
   - Parameter extraction from natural language
   - Structured output formatting

4. **Context Management:**
   - Maintains conversation history
   - References previous interactions
   - Understands follow-up questions

**System Prompt Strategy:**
```
Instructions include:
- Role definition (sales assistant)
- Communication style (friendly, professional)
- Tool usage guidelines
- Response formatting (voice-optimized)
- Error handling approaches
```

### 5. RAG System Architecture

**Component Layers:**

```
┌─────────────────────────────────────────┐
│         Query Processing                 │
│  • Text normalization                    │
│  • Language detection                    │
│  • Query expansion (optional)            │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│      Embedding Generation                │
│  Model: Alibaba-NLP/gte-multilingual    │
│  • 768-dimensional vectors               │
│  • Multilingual (Arabic + English)       │
│  • Semantic understanding                │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│       Vector Similarity Search           │
│  • FAISS IndexFlatIP                     │
│  • Cosine similarity (after L2 norm)     │
│  • Top-K retrieval (typically K=2-3)     │
│  • Score threshold: 0.5                  │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│      Result Enrichment                   │
│  • Fetch real-time inventory (SQLite)    │
│  • Add similarity scores                 │
│  • Format for LLM consumption            │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│      Context Injection                   │
│  • Format as natural language            │
│  • Include availability status           │
│  • Return to Gemini for response         │
└─────────────────────────────────────────┘
```

**Embedding Model Details:**

- **Model**: `Alibaba-NLP/gte-multilingual-base`
- **Architecture**: Transformer-based encoder
- **Dimensions**: 768
- **Training**: Contrastive learning on multilingual pairs
- **Strengths**:
  - Excellent cross-lingual retrieval
  - Semantic similarity capture
  - Robust to typos and variations

**FAISS Index:**
```python
dimension = 768
index = faiss.IndexFlatIP(dimension)  # Inner Product

# Embeddings are L2-normalized for cosine similarity
faiss.normalize_L2(embeddings)

# Search returns (scores, indices)
scores, indices = index.search(query_embedding, top_k)
```

**Why Inner Product after normalization?**
- Equivalent to cosine similarity: `cos(a,b) = (a·b) / (||a|| ||b||)`
- When ||a|| = ||b|| = 1: `cos(a,b) = a·b`
- Faster than computing cosine directly

### 6. Database Architecture

**Two-Database Design:**

**Vector Database (FAISS):**
- **Purpose**: Semantic product search
- **Storage**: In-memory index + disk persistence
- **Structure**: Dense vectors (float32[768])
- **Query**: Similarity search (< 50ms for 10K products)
- **Use case**: "Find products like X"

**SQL Database (SQLite):**
- **Purpose**: Inventory and order management
- **Storage**: Persistent file-based database
- **Structure**: Relational tables (products, requests)
- **Query**: CRUD operations with ACID guarantees
- **Use case**: "Update quantity, create order"

**Hybrid Query Example:**
```python
# 1. Vector search finds similar products
similar_products = vector_db.search("gaming processor", top_k=3)

# 2. For each result, fetch real-time inventory
for product in similar_products:
    inventory = sql_db.get_product_info(product['id'])
    product['quantity'] = inventory['quantity']  # Real-time data
```

**Why Both?**
- Vector DB: Handles fuzzy, semantic matching
- SQL DB: Ensures data consistency and transactions
- Together: Best of both worlds

### 7. Function Tools Layer

**Tool Registration:**
```python
@function_tool
async def search_products(query: str, top_k: int = 2):
    """Gemini can call this automatically"""
    results = db_manager.search_products(query, top_k)
    return formatted_results
```

**How Gemini Calls Tools:**

1. User says: "أريد مثقاب كهربائي"
2. Gemini determines tool needed: `search_products`
3. Gemini extracts parameters: `query="مثقاب كهربائي"`
4. Agent executes function
5. Results returned to Gemini
6. Gemini incorporates results in response

**Available Tools:**
- `search_products`: Semantic product search
- `make_product_request`: Order by product ID
- `make_product_request_by_name`: Order by fuzzy name
- `get_product_details`: Get specific product info
- `get_product_details_by_name`: Get info by fuzzy name

## 🔁 Complete Conversation Flow

### Example: User Orders a Product

```
USER: "أريد AMD Ryzen 9"
      ↓
[FRONTEND]
  • Microphone captures audio
  • LiveKit publishes to room
      ↓
[LIVEKIT SERVER]
  • Routes audio to agent
      ↓
[AGENT - GEMINI]
  • Transcribes: "أريد AMD Ryzen 9"
  • Understands: User wants to order
  • Needs: User name, address, product confirmation
      ↓
GEMINI: "ممتاز! ما اسمك من فضلك؟"
      ↓
USER: "أحمد محمد"
      ↓
GEMINI: "وما هو عنوانك؟"
      ↓
USER: "شارع التحرير، القاهرة"
      ↓
[AGENT - FUNCTION CALL]
  • Calls: make_product_request_by_name(
      user_name="أحمد محمد",
      address="شارع التحرير، القاهرة",
      product_name="AMD Ryzen 9"
    )
      ↓
[DATABASE MANAGER]
  • Searches vector DB for best match
  • Finds: AMD Ryzen 9 7950X (score: 0.95)
  • Checks SQLite for availability: 15 units
  • Creates order record
  • Reduces quantity to 14
  • Returns success
      ↓
[AGENT - GEMINI]
  • Receives: "Success. Matched to AMD Ryzen 9 7950X. 14 remaining."
  • Generates: "تم تأكيد الطلب! سيصلك AMD Ryzen 9 7950X قريباً..."
  • Synthesizes voice
      ↓
[LIVEKIT SERVER]
  • Streams audio to client
      ↓
[FRONTEND]
  • Plays audio through speakers
      ↓
USER HEARS: Confirmation in natural Arabic voice
```

## 🎯 Key Design Decisions

### 1. Why LiveKit?
- **Low latency**: < 100ms for voice
- **Scalability**: SFU architecture handles multiple participants
- **Reliability**: Built-in reconnection and quality adaptation
- **Developer experience**: Excellent React components

### 2. Why Gemini Live API?
- **Native audio**: No STT/TTS overhead
- **Arabic optimization**: Excellent pronunciation
- **Function calling**: Seamless tool integration
- **Context retention**: Maintains conversation state

### 3. Why FAISS + SQLite?
- **FAISS**: Fast semantic search (< 50ms)
- **SQLite**: ACID transactions for orders
- **Separation of concerns**: Search vs. data integrity
- **Flexibility**: Can scale each independently

### 4. Why Multilingual Embeddings?
- **Arabic support**: Critical for target market
- **Cross-lingual**: User can mix Arabic/English
- **Robustness**: Handles typos and variations
- **Quality**: State-of-the-art retrieval accuracy
