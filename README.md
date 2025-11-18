# Smart Hardware Sales Agent - Setup Guide

A voice-powered AI sales assistant for hardware stores with Arabic language support, built using LiveKit, Google Gemini Live API, and RAG technology.

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8 or higher**
- **Node.js 16 or higher**
- **pip** (Python package manager)
- **npm** (Node package manager)
- **Git** (for cloning the repository)

## 🔑 Required API Keys and Accounts

### 1. Google Gemini API Key

**Step-by-step instructions:**

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click on "Get API Key" in the left sidebar
4. Click "Create API Key"
5. Copy the generated API key (starts with `AIza...`)
6. Save it securely - you'll need it for the backend configuration

**Note**: The Gemini API has a free tier with generous limits suitable for development and testing.

### 2. LiveKit Cloud Account

**Step-by-step instructions:**

1. Go to [LiveKit Cloud](https://cloud.livekit.io/)
2. Sign up for a free account
3. Create a new project by clicking "New Project"
4. Give your project a name (e.g., "Hardware Sales Agent")
5. Once created, go to **Settings → Keys**
6. You'll see three important values:
   - **WebSocket URL** (e.g., `wss://your-project.livekit.cloud`)
   - **API Key** (e.g., `APIxxxxxxxxxxxxxxx`)
   - **API Secret** (e.g., `secretxxxxxxxxxxxxxxxxxxxxxxx`)
7. Copy all three values - you'll need them for both backend and frontend

**Note**: LiveKit free tier includes 50GB of traffic per month, which is sufficient for development.

## 🛠️ Installation Steps

### Backend Setup

#### 1. Navigate to Backend Directory

```bash
cd backend
```

#### 2. Create Python Virtual Environment (Recommended)

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install livekit livekit-agents livekit-plugins-google
pip install sentence-transformers torch torchvision torchaudio
pip install faiss-cpu numpy python-dotenv
pip install fastapi uvicorn  # For token server
```

**Note**: If you have a CUDA-compatible GPU, you can install `faiss-gpu` instead of `faiss-cpu` for better performance.

**For CUDA/GPU support:**
```bash
pip install faiss-gpu
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### 4. Create Backend Environment File

Create a file named `.env` in the `backend` directory with the following content:

```env
# Google Gemini API Configuration
GOOGLE_API_KEY=AIzaXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# LiveKit Server Configuration
LIVEKIT_URL=wss://your-project-name.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxxxxxxxx
LIVEKIT_API_SECRET=secretxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Replace the placeholder values with your actual credentials:**
- `GOOGLE_API_KEY`: Your Gemini API key from Google AI Studio
- `LIVEKIT_URL`: Your LiveKit WebSocket URL
- `LIVEKIT_API_KEY`: Your LiveKit API Key
- `LIVEKIT_API_SECRET`: Your LiveKit API Secret

#### 5. Prepare Product Data

Ensure you have a `data.json` file in the backend directory with your product catalog. Example structure:

```json
[
  {
    "id": 1001,
    "name": "AMD Ryzen 9 7950X",
    "description": "معالج قوي 16 نواة، 32 خيط، مناسب للألعاب والإنتاجية العالية",
    "quantity": 15
  },
  {
    "id": 1002,
    "name": "Intel Core i9-13900K",
    "description": "معالج عالي الأداء 24 نواة، مثالي للألعاب الاحترافية والعمل الشاق",
    "quantity": 10
  }
]
```

#### 6. Initialize Databases

Run the setup script to create and populate the vector and SQL databases:

```bash
python setup.py
```

This script will:
- Load products from `data.json`
- Generate embeddings using the multilingual transformer model
- Create FAISS vector index for semantic search
- Create SQLite database for inventory management
- Save indexes to disk for fast loading

**Expected output:**
```
Starting database setup...
Found data.json with 10 products
Initializing database manager...
Loading embedding model...
Model loaded on device: cuda
Loading products into databases...
Generating embeddings...
Building FAISS index...
Vector database created with 10 products.
Database setup completed successfully!
```

### Frontend Setup

#### 1. Navigate to Frontend Directory

```bash
cd frontend
```

#### 2. Install Node Dependencies

```bash
npm install
```

This will install:
- React and Vite
- LiveKit React components
- Other frontend dependencies

#### 3. Create Frontend Environment File

Create a file named `.env` in the `frontend` directory:

```env
VITE_LIVEKIT_URL=wss://your-project-name.livekit.cloud
```

**Replace** `wss://your-project-name.livekit.cloud` with your actual LiveKit WebSocket URL.


## 🎥 Project Demo (YouTube)

[![Watch the demo](https://img.youtube.com/vi/m1kpPRuh6WM/0.jpg)](https://youtu.be/m1kpPRuh6WM)

