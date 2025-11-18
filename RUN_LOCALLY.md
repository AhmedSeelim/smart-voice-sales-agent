# Running the Application Locally

This guide will walk you through running the Smart Hardware Sales Agent on your local machine.

## ✅ Prerequisites Checklist

Before starting, ensure you have completed:

- [ ] Installed Python 3.8+ and Node.js 16+
- [ ] Created Google Gemini API key
- [ ] Set up LiveKit Cloud account
- [ ] Configured backend `.env` file
- [ ] Configured frontend `.env` file
- [ ] Installed all dependencies
- [ ] Run `python setup.py` to initialize databases

If you haven't completed these steps, please refer to `README.md` first.

## 🚀 Quick Start (3 Terminal Windows)

You'll need **three separate terminal windows** running simultaneously:

```
Terminal 1: Backend Agent (Python)
Terminal 2: Token Server (FastAPI)
Terminal 3: Frontend App (React)
```

## 📝 Step-by-Step Instructions

### Terminal 1: Start the Backend Agent

**Purpose**: Runs the Python agent that connects to LiveKit and handles AI processing.

#### 1. Navigate to Backend Directory

```bash
cd backend
```

#### 2. Activate Virtual Environment (if using one)

**On Windows:**
```bash
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
source venv/bin/activate
```

#### 3. Verify Environment Variables

```bash
# Quick check (optional)
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Gemini Key:', os.getenv('GOOGLE_API_KEY')[:20] + '...'); print('LiveKit URL:', os.getenv('LIVEKIT_URL'))"
```

Expected output:
```
Gemini Key: AIzaSyXXXXXXXXXXXXXX...
LiveKit URL: wss://your-project.livekit.cloud
```

#### 4. Start the Agent

```bash
python agent.py dev
```

**Expected Output:**
```
🏗️ Starting Hardware Sales Agent Worker...
Loading embedding model...
Downloading model files... (first time only)
Model loaded on device: cuda  # or 'cpu' if no GPU
Attempting to load saved indexes...
✅ Loaded saved indexes successfully
Index loaded from ./product_db/faiss_index.bin
Products data loaded from ./product_db/data.json

INFO:livekit.agents:Starting agent worker
INFO:livekit.agents:Connecting to LiveKit server: wss://your-project.livekit.cloud
INFO:livekit.agents:Worker registered successfully
INFO:hardware-agent:Waiting for participant to join...
```

**What this means:**
- ✅ Agent is running
- ✅ Connected to LiveKit
- ✅ Databases loaded
- ✅ Waiting for user connection

**Leave this terminal running!**

---

### Terminal 2: Start the Token Server

**Purpose**: Generates LiveKit access tokens for frontend clients using FastAPI.

#### 1. Open a New Terminal

#### 2. Navigate to Backend Directory

```bash
cd backend
```

#### 3. Activate Virtual Environment (if using one)

**On Windows:**
```bash
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
source venv/bin/activate
```

#### 4. Start Token Server

```bash
python server.py
```

**Or using uvicorn directly**:
```bash
uvicorn server:app --host 0.0.0.0 --port 5001 --reload
```

**Expected Output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5001 (Press CTRL+C to quit)
```

**What this means:**
- ✅ FastAPI server listening on port 5001
- ✅ Ready to generate tokens at `/getToken` endpoint
- ✅ Frontend can now authenticate

**Test the token server (optional):**

Open a browser to:
```
http://localhost:5001/getToken?name=TestUser
```

You should see JSON response:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Leave this terminal running!**

---

### Terminal 3: Start the Frontend Application

**Purpose**: Runs the React user interface.

#### 1. Open a Third Terminal

#### 2. Navigate to Frontend Directory

```bash
cd frontend
```

#### 3. Start Development Server

```bash
npm run dev
```

**Expected Output:**
```
  VITE v5.x.x  ready in 300 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

#### 4. Open Browser

Navigate to: **http://localhost:5173**

You should see the application interface:
- Title: "🛠️ مساعد المبيعات الذكي"
- Input field for name
- "ابدأ المحادثة" button

**Leave this terminal running!**

---

## 🎤 Using the Application

### Step 1: Enter Your Name

1. Type your name in the input field (e.g., "أحمد")
2. Click "🎤 ابدأ المحادثة"

**Behind the scenes:**
```
1. Frontend requests token from http://localhost:5001
2. Token server generates JWT with your name
3. Frontend connects to LiveKit with token
4. Backend agent detects new participant
5. Agent sends greeting
```

### Step 2: Allow Microphone Access

Your browser will request microphone permission:
- Click "Allow" or "السماح"

**Troubleshooting**: If you don't see the prompt:
- Check browser URL bar for blocked icon
- Click and enable microphone
- Refresh the page

### Step 3: Wait for Greeting

You should hear the agent's voice:
> "أهلاً بك! أنا مساعد المبيعات في متجر الأدوات. كيف أقدر أساعدك النهارده؟"

**Check Backend Terminal**: You should see:
```
INFO:hardware-agent:Agent entering session - sending greeting
INFO:hardware-agent:🎯 Agent session started successfully
INFO:hardware-agent:Current Agent: 🛠️ Hardware Sales Agent 🛠️
```

### Step 4: Start Speaking!

Try these example queries:

**Product Search:**
```
User: "أحتاج معالج قوي للألعاب"
Agent: Calls search_products("معالج قوي للألعاب")
Agent: "وجدت لك معالجين ممتازين..."
```

**Backend logs:**
```
INFO:hardware-agent:🔍 Searching products: 'معالج قوي للألعاب' (top_k=2)
INFO:hardware-agent:✅ Found 2 products
```

**Product Details:**
```
User: "قول لي أكتر عن AMD Ryzen 9"
Agent: Calls get_product_details_by_name("AMD Ryzen 9")
Agent: Provides detailed description
```

**Place Order:**
```
User: "سآخذ AMD Ryzen 9"
Agent: "ممتاز! ما اسمك من فضلك؟"
User: "أحمد محمد"
Agent: "وما هو عنوانك؟"
User: "شارع التحرير، القاهرة"
Agent: Calls make_product_request_by_name(...)
Agent: "تم تأكيد الطلب! سيصلك المنتج قريباً..."
```

**Backend logs:**
```
INFO:hardware-agent:📦 Processing request by name - User: أحمد محمد
INFO:database-manager:Finding product by name: 'AMD Ryzen 9'
INFO:database-manager:Matched to product: AMD Ryzen 9 7950X (ID: 1001)
INFO:hardware-agent:✅ Request created successfully with name matching
```

### Step 5: Monitor All Terminals

**Terminal 1 (Agent)** shows:
- Tool calls (search, orders)
- Database queries
- AI processing steps

**Terminal 2 (Token Server)** shows:
- Token generation requests (when users connect)

**Terminal 3 (Frontend)** shows:
- Vite hot module replacement
- Browser console logs (open DevTools to see)

---

## 🔍 Verification & Testing

### Test 1: Voice Status Indicator

Watch the status text in the UI:
- 🎤 "جاري الاستماع..." - Agent is listening
- 🤔 "جاري التفكير..." - Processing your request
- 💬 "جاري التحدث..." - Agent is speaking

### Test 2: Search Functionality

**Say**: "ابحث عن كارت شاشة"

**Expected**:
1. Agent state changes to "thinking"
2. Backend logs show: `🔍 Searching products`
3. Agent responds with product options
4. State changes to "speaking"

### Test 3: Order Processing

**Say**: "أريد [product name]"

**Expected**:
1. Agent asks for your name
2. Agent asks for address
3. Agent confirms order
4. Backend logs show: `📦 Processing request`
5. Database quantity decreases

Verify in backend:
```bash
cd backend
sqlite3 products.db "SELECT name, quantity FROM products WHERE id=1001;"
```

### Test 4: Multiple Conversations

Try disconnecting and reconnecting:
1. Click "✕ إنهاء المحادثة"
2. Enter a different name
3. Click "ابدأ المحادثة" again
4. Each session should be independent

---

## 🛑 Stopping the Application

### Graceful Shutdown

**Stop in this order:**

1. **Terminal 3 (Frontend)**:
   - Press `Ctrl+C`
   - Vite server stops

2. **Terminal 2 (Token Server - FastAPI)**:
   - Press `Ctrl+C`
   - Uvicorn server stops

3. **Terminal 1 (Agent)**:
   - Press `Ctrl+C`
   - Agent disconnects from LiveKit
   - Python process terminates

### Verify Shutdown

```bash
# Check no processes on ports
# On macOS/Linux:
lsof -ti:5173  # Should return nothing
lsof -ti:5001  # Should return nothing

# On Windows:
netstat -ano | findstr :5173
netstat -ano | findstr :5001
```

---

## 🐛 Troubleshooting

### Issue: Agent Won't Start

**Error**: `ModuleNotFoundError: No module named 'livekit'`

**Solution**:
```bash
cd backend
pip install -r requirements.txt
```

---

**Error**: `FileNotFoundError: Index or data file not found`

**Solution**:
```bash
cd backend
python setup.py  # Regenerate databases
```

---

**Error**: `RuntimeError: CUDA out of memory`

**Solution**: Force CPU usage in `vector_db.py`:
```python
self.device = torch.device("cpu")
```

---

### Issue: Token Server Fails

**Error**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**:
```bash
cd backend
pip install fastapi uvicorn python-multipart
```

---

**Error**: `Address already in use :::5001`

**Solution**: Kill the process using port 5001:
```bash
# macOS/Linux:
lsof -ti:5001 | xargs kill -9

# Windows:
netstat -ano | findstr :5001
taskkill /PID <PID> /F
```

---

**Error**: `LIVEKIT_API_KEY or LIVEKIT_API_SECRET not found`

**Solution**: Verify your backend `.env` file has these variables:
```bash
cd backend
cat .env | grep LIVEKIT
```

---

### Issue: Frontend Build Errors

**Error**: `Failed to resolve import "@livekit/components-react"`

**Solution**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

---

### Issue: No Voice Output

**Checklist**:
- [ ] Check browser console for errors (F12)
- [ ] Verify audio output device is working
- [ ] Check volume isn't muted
- [ ] Try different browser (Chrome recommended)
- [ ] Check agent terminal for errors

**Debug in Browser Console**:
```javascript
// Check if audio is playing
document.querySelectorAll('audio').forEach(a => console.log(a.paused, a.currentTime))
```

---

### Issue: Microphone Not Working

**Checklist**:
- [ ] Grant microphone permission in browser
- [ ] Check microphone works in other apps
- [ ] Use HTTPS if possible (WebRTC prefers secure context)
- [ ] Check browser compatibility (Chrome/Edge recommended)

**Browser Settings**:
- Chrome: `chrome://settings/content/microphone`
- Edge: `edge://settings/content/microphone`
- Firefox: `about:preferences#privacy` → Permissions

---

### Issue: Agent Not Responding

**Symptoms**: Voice is captured but no response

**Debug Steps**:

1. **Check backend logs** for errors:
```
ERROR:hardware-agent:❌ Error searching products
```

2. **Verify Gemini API key**:
```bash
cd backend
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(len(os.getenv('GOOGLE_API_KEY')))"
# Should print: 39 (typical length)
```

3. **Test Gemini API directly**:
```bash
curl https://generativelanguage.googleapis.com/v1/models?key=YOUR_API_KEY
```

4. **Check LiveKit connection**:
```
INFO:livekit.agents:Worker registered successfully
```
If you don't see this, check `LIVEKIT_URL` in `.env`

---

### Issue: High Latency

**Symptoms**: Long delays between speaking and response

**Optimizations**:

1. **Use GPU for embeddings** (if available):
```bash
pip uninstall faiss-cpu
pip install faiss-gpu
```

2. **Reduce top_k** in searches:
```python
# In function tools, change:
top_k=2  # Instead of 3 or more
```

3. **Check network latency**:
```bash
ping your-livekit-server.livekit.cloud
```

4. **Monitor backend performance**:
```bash
# Install psutil
pip install psutil

# Add to agent.py
import psutil
print(f"CPU: {psutil.cpu_percent()}%, Memory: {psutil.virtual_memory().percent}%")
```

---

## 📊 Monitoring & Logs

### Backend Logs

**Logging levels**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)  # More verbose
logging.basicConfig(level=logging.INFO)   # Default
logging.basicConfig(level=logging.WARNING)  # Less verbose
```

**Key log patterns**:
- `🔍` = Search operation
- `📦` = Order processing
- `✅` = Success
- `⚠️` = Warning
- `❌` = Error
- `🎯` = Agent lifecycle event

### Frontend Logs

**Open Browser DevTools** (F12):
- Console tab shows JavaScript logs
- Network tab shows API calls
- Application tab shows LiveKit connection state

**Useful console commands**:
```javascript
// Check LiveKit room state
window.livekit_room

// Check connection quality
window.livekit_room.engine.getConnectedServerAddress()
```

### LiveKit Dashboard

Visit: https://cloud.livekit.io/projects/[your-project]

Monitor:
- Active rooms
- Participant count
- Bandwidth usage
- Connection quality

---

## 🔄 Restarting After Changes

### Code Changes

**Backend Python changes**:
```bash
# Terminal 1: Restart agent
Ctrl+C
python agent.py dev
```

**Token Server changes (server.py)**:
```bash
# Terminal 2: Restart token server
Ctrl+C
python server.py
```

**Frontend React changes**:
- Vite hot-reloads automatically
- No restart needed (usually)

### Database Changes

**After modifying `data.json`**:
```bash
cd backend
python setup.py  # Regenerate indexes
python agent.py dev  # Restart agent
```

**After modifying schema**:
```bash
cd backend
rm products.db  # Delete old database
python setup.py  # Recreate
```

---

## ✅ Success Checklist

Your application is running correctly when:

- [ ] All three terminals show no errors
- [ ] Frontend loads at http://localhost:5173
- [ ] You can enter your name and connect
- [ ] Agent greets you in Arabic
- [ ] Voice status indicator updates correctly
- [ ] You can ask questions and get responses
- [ ] Product searches work and return results
- [ ] Orders can be placed successfully
- [ ] Backend logs show function calls
- [ ] No console errors in browser DevTools

---

## 🎉 Next Steps

Now that your application is running:

1. **Read `RAG_INTEGRATION.md`** to understand how RAG works
2. **Customize `data.json`** with your actual products
3. **Modify system prompts** in `agent.py` for your use case
4. **Test edge cases** (out of stock, unclear queries)
5. **Prepare for deployment** (see deployment section in README)

---

## 💡 Pro Tips

1. **Use tmux/screen** to manage multiple terminals:
```bash
tmux new-session -s hardware-agent
# Split panes with Ctrl+B then "
```

2. **Create a startup script**:
```bash
#!/bin/bash
# start.sh
cd backend && python agent.py dev &
cd backend && python server.py &
cd frontend && npm run dev &
```

3. **Monitor resource usage**:
```bash
# Watch GPU usage (if CUDA)
watch nvidia-smi

# Watch CPU/memory
htop
```

4. **Keep logs for debugging**:
```bash
python agent.py dev 2>&1 | tee agent.log
```

---

**Happy building! 🚀**