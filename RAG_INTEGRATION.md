# RAG Integration with Gemini Live API

This document provides an in-depth explanation of how Retrieval-Augmented Generation (RAG) is implemented and integrated with Google's Gemini Live API in the Smart Hardware Sales Agent.

## 📚 What is RAG?

**Retrieval-Augmented Generation** is a technique that enhances Large Language Models (LLMs) by providing them with relevant external knowledge retrieved from a database at query time.

### Traditional LLM Approach
```
User Query → LLM → Response (based only on training data)
```
**Limitation**: LLM can only use information from its training period.

### RAG Approach
```
User Query → Retrieve Relevant Docs → LLM + Retrieved Context → Response
```
**Advantage**: LLM has access to current, domain-specific information.

## 🏗️ Our RAG Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INPUT                               │
│         "أحتاج معالج قوي للألعاب والمونتاج"                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                   GEMINI LIVE API                               │
│                                                                  │
│  1. Speech-to-Text (Arabic)                                     │
│     "أحتاج معالج قوي للألعاب والمونتاج"                       │
│                                                                  │
│  2. Intent Understanding                                        │
│     Intent: SEARCH_PRODUCTS                                     │
│     Entities: {category: "processor", use: ["gaming", "editing"]}│
│                                                                  │
│  3. Function Calling Decision                                   │
│     Tool: search_products                                       │
│     Parameters: {query: "معالج قوي للألعاب والمونتاج", top_k: 2}│
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    FUNCTION TOOL LAYER                          │
│                                                                  │
│  @function_tool                                                 │
│  async def search_products(query: str, top_k: int):             │
│      results = db_manager.search_products(query, top_k)         │
│      return formatted_results                                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                  RAG RETRIEVAL PIPELINE                         │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ STEP 1: QUERY EMBEDDING                                  │  │
│  │                                                           │  │
│  │ Input: "معالج قوي للألعاب والمونتاج"                    │  │
│  │                                                           │  │
│  │ Model: Alibaba-NLP/gte-multilingual-base                 │  │
│  │ - Tokenization                                           │  │
│  │ - Transformer encoding                                   │  │
│  │ - Mean pooling                                           │  │
│  │                                                           │  │
│  │ Output: Float32[768] vector                              │  │
│  │ [0.023, -0.145, 0.389, ..., 0.091]                       │  │
│  │                                                           │  │
│  │ Normalization: L2 norm (for cosine similarity)           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ STEP 2: VECTOR SIMILARITY SEARCH                         │  │
│  │                                                           │  │
│  │ FAISS Index: IndexFlatIP (Inner Product)                 │  │
│  │ - 1,000+ product embeddings pre-computed                 │  │
│  │ - Normalized vectors                                     │  │
│  │                                                           │  │
│  │ Search Algorithm:                                        │  │
│  │   for each product_vector in index:                      │  │
│  │     similarity = query_vector · product_vector           │  │
│  │                                                           │  │
│  │ Results (Top-2):                                         │  │
│  │   1. AMD Ryzen 9 7950X     → 0.87 similarity            │  │
│  │   2. Intel Core i9-13900K  → 0.85 similarity            │  │
│  │                                                           │  │
│  │ Time: ~25ms for 1,000 products                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ STEP 3: METADATA ENRICHMENT                              │  │
│  │                                                           │  │
│  │ For each retrieved product:                              │  │
│  │   - Fetch full details from SQLite                       │  │
│  │   - Get real-time inventory quantity                     │  │
│  │   - Calculate availability status                        │  │
│  │                                                           │  │
│  │ Enriched Results:                                        │  │
│  │   Product 1:                                             │  │
│  │     id: 1001                                             │  │
│  │     name: "AMD Ryzen 9 7950X"                            │  │
│  │     description: "معالج 16 نواة..."                      │  │
│  │     quantity: 15  ← Real-time from SQL                   │  │
│  │     similarity_score: 0.87                               │  │
│  │                                                           │  │
│  │   Product 2: [similar structure]                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ STEP 4: CONTEXT FORMATTING                               │  │
│  │                                                           │  │
│  │ Format for LLM consumption:                              │  │
│  │                                                           │  │
│  │ "I found 2 products for you. Option 1 is the AMD        │  │
│  │  Ryzen 9 7950X. معالج قوي 16 نواة، 32 خيط، مناسب        │  │
│  │  للألعاب والإنتاجية العالية. We have 15 units in       │  │
│  │  stock. This is an excellent match for what you're       │  │
│  │  looking for. Option 2 is the Intel Core i9-13900K..."   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│               GEMINI RESPONSE GENERATION                        │
│                                                                  │
│  Context Injection:                                             │
│    - Original query                                             │
│    - Conversation history                                       │
│    - Retrieved product information ← RAG context                │
│    - System instructions                                        │
│                                                                  │
│  Generation:                                                    │
│    "وجدت لك معالجين ممتازين! الخيار الأول هو AMD Ryzen 9      │
│     7950X، معالج قوي جداً بـ16 نواة مثالي للألعاب والمونتاج.   │
│     متوفر عندنا 15 قطعة. الخيار الثاني..."                     │
│                                                                  │
│  Text-to-Speech:                                                │
│    Arabic voice synthesis (Puck voice)                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
                    Spoken Response to User
```

## 🔬 Deep Dive: Embedding Model

### Model: Alibaba-NLP/gte-multilingual-base

**Architecture**:
```
Input Text → Tokenizer → Transformer Encoder → Pooling → Output Embedding
```

**Specifications**:
- **Type**: Transformer-based encoder (BERT-like)
- **Parameters**: ~110M
- **Layers**: 12 transformer layers
- **Hidden Size**: 768 dimensions
- **Max Sequence Length**: 512 tokens
- **Languages**: 50+ languages including Arabic and English

**Training Objective**:
- Contrastive learning on parallel text pairs
- Optimized for semantic similarity
- Cross-lingual alignment

### Why This Model?

**1. Multilingual Support**
```python
# Works seamlessly with mixed languages
query_ar = "معالج قوي"  # Arabic
query_en = "powerful processor"  # English
# Both map to similar embeddings!
```

**2. Semantic Understanding**
```python
# Captures meaning, not just keywords
"معالج للألعاب"          → [0.12, 0.89, ...]
"CPU for gaming"          → [0.14, 0.91, ...]  # Similar!
"مكونات كمبيوتر"          → [0.45, 0.23, ...]  # Different
```

**3. Robustness to Variations**
```python
# Handles typos and variations
"معالج قوى"  # Typo in Arabic
"معالج قوي"  # Correct
# Still finds the right product!
```

### Embedding Generation Process

**Code Implementation**:
```python
from sentence_transformers import SentenceTransformer

# Initialize model
model = SentenceTransformer(
    "Alibaba-NLP/gte-multilingual-base",
    trust_remote_code=True
)

# Generate embedding
query = "معالج قوي للألعاب"
embedding = model.encode(
    [query],
    convert_to_numpy=True,
    normalize_embeddings=True  # L2 normalization
)

# Result: numpy array of shape (1, 768)
# dtype: float32
```

**Under the Hood**:
1. **Tokenization**: Text → Token IDs
   ```
   "معالج قوي" → [101, 1234, 5678, 102]
   ```

2. **Token Embeddings**: IDs → Vectors
   ```
   Each token → 768-dim vector
   ```

3. **Transformer Encoding**: 
   ```
   12 layers of self-attention
   Contextual representations
   ```

4. **Pooling**: 
   ```
   Mean pooling over token embeddings
   → Single 768-dim vector
   ```

5. **Normalization**:
   ```
   embedding = embedding / ||embedding||
   ```

## 🔍 Deep Dive: FAISS Vector Search

### Index Type: IndexFlatIP

**IP = Inner Product**

After L2 normalization, inner product equals cosine similarity:
```
cos(a, b) = (a · b) / (||a|| × ||b||)

If ||a|| = ||b|| = 1:
cos(a, b) = a · b
```

**Why Inner Product?**
- Faster than computing norms at query time
- Mathematically equivalent after normalization
- Better hardware optimization

### Index Creation

```python
import faiss
import numpy as np

# Product embeddings (all products encoded)
product_embeddings = np.array([
    [0.12, 0.45, ..., 0.89],  # Product 1
    [0.34, 0.67, ..., 0.23],  # Product 2
    # ... 1000+ products
], dtype='float32')

# Normalize for cosine similarity
faiss.normalize_L2(product_embeddings)

# Create index
dimension = 768
index = faiss.IndexFlatIP(dimension)

# Add embeddings to index
index.add(product_embeddings)

# Index now ready for search!
```

### Search Process

```python
# Query embedding (already normalized)
query_embedding = np.array([[0.45, 0.23, ..., 0.78]], dtype='float32')
faiss.normalize_L2(query_embedding)

# Search for top-K similar products
top_k = 3
scores, indices = index.search(query_embedding, top_k)

# scores: similarity scores (0.0 to 1.0)
# indices: product indices in original array
```

**Time Complexity**:
- **Index Creation**: O(n) where n = number of products
- **Search**: O(n × d) where d = dimension (768)
- **Practical**: ~25ms for 1,000 products on CPU

### Similarity Score Interpretation

```
Score > 0.8:  Excellent match (same product or very similar)
Score 0.6-0.8: Good match (related products)
Score 0.4-0.6: Moderate match (same category)
Score < 0.4:  Weak match (consider rejecting)
```

**Example**:
```python
Query: "معالج AMD للألعاب"

Results:
1. AMD Ryzen 9 7950X     → 0.89  # Excellent!
2. AMD Ryzen 7 5800X     → 0.82  # Great alternative
3. Intel Core i9-13900K  → 0.67  # Different brand but similar use
```

## 🔗 Integration with Gemini Live API

### Function Tool Registration

Gemini Live API supports **function calling**, allowing the LLM to invoke Python functions when needed.

**How It Works**:

1. **Tool Definition**:
```python
from livekit.agents import function_tool

@function_tool
async def search_products(query: str, top_k: int = 2):
    """
    Search for products in the hardware store based on customer's needs.
    
    Args:
        query: A concise, fully formed search query describing what 
               the customer needs. Examples: "cordless drill with battery"
        top_k: Number of similar products to return (default: 2)
    
    Returns:
        Formatted string with product information including names, 
        descriptions, availability, and match scores.
    """
    # RAG retrieval happens here
    results = db_manager.search_products(query, top_k)
    return format_for_voice(results)
```

2. **Gemini's Decision Process**:
```
User: "أحتاج معالج قوي"

Gemini analyzes:
- Intent: User needs product recommendation
- Required info: Don't have product details in context
- Decision: Call search_products function
- Parameters: Extract from user's natural language
  → query = "معالج قوي"
  → top_k = 2 (default)
```

3. **Function Execution**:
```python
# Gemini triggers this automatically
result = await search_products(
    query="معالج قوي",
    top_k=2
)
# RAG pipeline executes
# Results returned to Gemini
```

4. **Context Injection**:
```
Gemini's context now includes:
- Original user message
- Function call
- Function results ← RAG-retrieved information
- System instructions
```

5. **Response Generation**:
```
Gemini synthesizes natural response using:
- Retrieved product details
- Conversational tone
- Arabic language
- Voice-optimized formatting
```

### Prompt Engineering for RAG

**System Instructions** guide how Gemini uses retrieved information:

```python
instructions = """
You are a helpful hardware store sales assistant.

CRITICAL RULES:
- When a customer describes what they need, use search_products 
  to find relevant items
- Present product options clearly in natural language
- Include key details: name, description, availability
- Be enthusiastic about products in stock
- Suggest alternatives if items are unavailable

Example interaction:
User: "أحتاج مثقاب كهربائي"
You: [Call search_products("مثقاب كهربائي")]
You: "وجدت لك مثقابين ممتازين! الأول هو DeWalt 20V..."

Remember: Use tools proactively to help customers.
"""
```

**Why This Works**:
- Clear tool usage guidelines
- Examples demonstrate expected behavior
- Emphasizes natural language presentation
- Handles edge cases (out of stock)

## 🎯 RAG-Enhanced Conversation Flows

### Flow 1: Simple Product Search

```
┌─────────────────────────────────────────────┐
│ User: "ابحث عن كارت شاشة"                  │
└───────────────────┬─────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ Gemini:                                     │
│ - Understands: Search intent                │
│ - Extracts: "كارت شاشة" (graphics card)     │
│ - Calls: search_products("كارت شاشة", 2)   │
└───────────────────┬─────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ RAG Pipeline:                               │
│ 1. Embed query                              │
│ 2. Search vector DB                         │
│ 3. Retrieve: NVIDIA RTX 4090, AMD RX 7900   │
│ 4. Fetch quantities from SQL                │
│ 5. Format results                           │
└───────────────────┬─────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ Gemini receives:                            │
│ "Found 2 products. Option 1 is NVIDIA RTX   │
│  4090... 8 units in stock. Option 2 is..."  │
└───────────────────┬─────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ Gemini responds:                            │
│ "وجدت لك كارتين شاشة ممتازين! الأول هو    │
│  NVIDIA RTX 4090، كارت قوي جداً للألعاب..."│
└─────────────────────────────────────────────┘
```

### Flow 2: Multi-Turn Order Processing

```
Turn 1:
User: "سآخذ AMD Ryzen 9"
  ↓
Gemini: Understands order intent, needs more info
  ↓
Response: "ممتاز! ما اسمك من فضلك؟"

Turn 2:
User: "أحمد محمد"
  ↓
Gemini: Stored name, needs address
  ↓
Response: "وما هو عنوانك؟"

Turn 3:
User: "شارع التحرير، القاهرة"
  ↓
Gemini: Has all info, ready to process
  ↓
Calls: make_product_request_by_name(
  user_name="أحمد محمد",
  address="شارع التحرير، القاهرة",
  product_name="AMD Ryzen 9"
)
  ↓
RAG finds best match: AMD Ryzen 9 7950X (score: 0.95)
  ↓
SQL transaction: Create order, reduce quantity
  ↓
Returns: Success message
  ↓
Gemini: "تم تأكيد الطلب! سيصلك AMD Ryzen 9 7950X قريباً..."
```

### Flow 3: Fuzzy Matching

```
User: "أريد مثقاب ديوالت"  (DeWalt drill, with typo)
  ↓
Gemini calls: search_products("مثقاب ديوالت", 2)
  ↓
RAG Pipeline:
- Embedding captures semantic meaning
- Typo doesn't significantly affect vector
- Matches: "DeWalt 20V Cordless Drill"
- Score: 0.78 (good match despite variation)
  ↓
Gemini presents options confidently
```

## 📊 Performance Optimization

### Embedding Caching

**Problem**: Re-encoding the same queries is wasteful

**Solution**: Cache embeddings
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_embedding(query: str):
    return model.encode([query])
```

### Batch Processing

**During setup**, embed all products at once:
```python
# More efficient
all_descriptions = [f"{p['name']} {p['description']}" 
                    for p in products]
embeddings = model.encode(all_descriptions, batch_size=32)

# vs. one-by-one (slower)
for product in products:
    embedding = model.encode([product['name']])
```

### Index Persistence

**Save index to disk** to avoid re-encoding:
```python
# Save
faiss.write_index(index, "product_index.faiss")

# Load (much faster than rebuilding)
index = faiss.read_index("product_index.faiss")
```

### GPU Acceleration

```python
# Use GPU for embedding (if available)
model = SentenceTransformer(model_name).to('cuda')

# Use GPU FAISS (requires faiss-gpu)
import faiss
res = faiss.StandardGpuResources()
index = faiss.index_cpu_to_gpu(res, 0, index)
```

## 🧪 Testing RAG Quality

### Test Cases

**1. Exact Match**:
```python
query = "AMD Ryzen 9 7950X"
results = search_products(query, top_k=1)
assert results[0]['name'] == "AMD Ryzen 9 7950X"
assert results[0]['similarity_score'] > 0.9
```

**2. Semantic Match**:
```python
query = "معالج قوي للألعاب"  # Powerful gaming processor
results = search_products(query, top_k=3)
# Should return high-end CPUs
assert all("AMD Ryzen 9" in r['name'] or 
           "Intel Core i9" in r['name'] 
           for r in results)
```

**3. Cross-Lingual**:
```python
query_ar = "كارت شاشة"
query_en = "graphics card"
results_ar = search_products(query_ar)
results_en = search_products(query_en)
# Should return similar products
assert results_ar[0]['id'] == results_en[0]['id']
```

**4. Robustness**:
```python
query_typo = "معلج قوى"  # Typo
query_correct = "معالج قوي"
results_typo = search_products(query_typo)
results_correct = search_products(query_correct)
# Should still find relevant products
assert results_typo[0]['similarity_score'] > 0.6
```

### Evaluation Metrics

**Relevance Score**:
```python
def evaluate_relevance(query, results, expected_category):
    relevant_count = sum(1 for r in results 
                        if expected_category in r['description'])
    return relevant_count / len(results)

# Example
score = evaluate_relevance("معالج", results, "processor")
print(f"Relevance: {score:.2%}")  # Should be high
```

**Ranking Quality (NDCG)**:
```python
from sklearn.metrics import ndcg_score

# Ground truth relevance scores
y_true = [1, 0.8, 0.3]  # Perfect, good, weak match
y_pred = [r['similarity_score'] for r in results]

ndcg = ndcg_score([y_true], [y_pred])
print(f"NDCG: {ndcg:.2%}")  # Higher is better
```

## 🎓 Best Practices

### 1. Query Formulation

**Good queries are concise and descriptive**:
```python
✅ Good: "معالج قوي للألعاب"
❌ Bad: "أنا أحتاج شيء للكمبيوتر ربما معالج أو حاجة كده"

✅ Good: "كارت شاشة RTX"
❌ Bad: "حاجة للجيمنج"
```

**Let Gemini extract the essence**:
```python
# Gemini receives: "أحتاج حاجة تشغل الجيمز بتاعي لأن الكمبيوتر بطيء"
# Gemini extracts: "كارت شاشة للألعاب"
# RAG searches with clean query
```

### 2. Top-K Selection

```python
# Simple queries: top_k=1-2
"معالج AMD"  → top_k=1  # User knows what they want

# Broad queries: top_k=3-5
"معالج للألعاب"  → top_k=3  # Show options


```

### 3. Threshold Management

```python
# Set minimum similarity threshold
MIN_SIMILARITY = 0.5

results = [r for r in search_results 
           if r['similarity_score'] >= MIN_SIMILARITY]

if not results:
    return "لم أجد منتجات مطابقة. هل يمكنك توضيح أكثر؟"
```

### 4. Response Formatting

**Voice-optimized**:
```python
# ❌ Bad for voice
"Product: AMD Ryzen 9 7950X\n- Cores: 16\n- Price: 3200 EGP"

# ✅ Good for voice
"AMD Ryzen 9 7950X، معالج قوي بـ16 نواة، السعر 3200 جنيه"
```

### 5. Error Handling

```python
try:
    results = db_manager.search_products(query, top_k)
    if not results:
        return "عذراً، لم أجد منتجات مطابقة. جرب وصف آخر؟"
except Exception as e:
    logger.error(f"RAG error: {e}")
    return "حدث خطأ في البحث. حاول مرة أخرى من فضلك."
```

## 🎯 Key Takeaways

1. **RAG extends LLM capabilities** with real-time, domain-specific knowledge
2. **Embedding models** convert text to semantic vectors
3. **FAISS enables fast** similarity search at scale
4. **Function calling** seamlessly integrates RAG with Gemini
5. **Hybrid approach** (vector + SQL) provides both intelligence and reliability
6. **Careful prompt engineering** guides how LLM uses retrieved information
7. **Monitoring and testing** ensure RAG quality over time

**The magic of RAG**: Gemini can answer "What gaming processors do you have?" even though it was never trained on your specific product catalog, because RAG retrieves that information at runtime! 🎉

---

**For questions or improvements, please open an issue on GitHub.**