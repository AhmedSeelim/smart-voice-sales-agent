import { useState, useCallback } from 'react'
import { LiveKitRoom, RoomAudioRenderer, useVoiceAssistant } from "@livekit/components-react"
import "@livekit/components-styles"
import './App.css'

function VoiceAgent() {
  const { state, audioTrack } = useVoiceAssistant()

  const getStateText = () => {
    switch (state) {
      case "listening": return "🎤 جاري الاستماع..."
      case "thinking": return "🤔 جاري التفكير..."
      case "speaking": return "💬 جاري التحدث..."
      default: return "✓ متصل"
    }
  }

  return (
    <div className="agent-container">
      <div className="status">{getStateText()}</div>
      <div className="wave">
        <div className="wave-bar"></div>
        <div className="wave-bar"></div>
        <div className="wave-bar"></div>
        <div className="wave-bar"></div>
        <div className="wave-bar"></div>
      </div>
    </div>
  )
}

function App() {
  const [name, setName] = useState('')
  const [token, setToken] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const getToken = useCallback(async (userName) => {
    setIsLoading(true)
    setError(null)

    try {
      console.log('طلب التوكن للمستخدم:', userName)

      const response = await fetch(
        `http://localhost:5001/getToken?name=${encodeURIComponent(userName)}`
      )

      if (!response.ok) {
        throw new Error('فشل في الحصول على التوكن')
      }

      const data = await response.json()
      console.log('تم استلام التوكن:', data)

      setToken(data.token)
    } catch (error) {
      console.error('خطأ:', error)
      setError('فشل الاتصال. تأكد من تشغيل السيرفر')
    } finally {
      setIsLoading(false)
    }
  }, [])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (name.trim()) {
      getToken(name)
    }
  }

  const handleDisconnect = () => {
    setToken(null)
    setName('')
    setError(null)
  }

  // إذا لم يكن هناك توكن، اعرض نموذج الإدخال
  if (!token) {
    return (
      <div className="app">
        <div className="form-container">
          <div className="header">
            <h1>🛠️ مساعد المبيعات الذكي</h1>
            <p>تحدث معنا للحصول على أفضل المنتجات</p>
          </div>

          <form onSubmit={handleSubmit} className="form">
            <div className="input-group">
              <label>الاسم</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="أدخل اسمك"
                required
                disabled={isLoading}
                autoFocus
              />
            </div>

            {error && (
              <div className="error">⚠️ {error}</div>
            )}

            <button type="submit" disabled={isLoading || !name.trim()}>
              {isLoading ? '⏳ جاري الاتصال...' : '🎤 ابدأ المحادثة'}
            </button>
          </form>

          <div className="features">
            <div className="feature">✓ بحث ذكي عن المنتجات</div>
            <div className="feature">✓ توصيات فورية</div>
            <div className="feature">✓ محادثة طبيعية</div>
          </div>
        </div>
      </div>
    )
  }

  // إذا كان هناك توكن، اعرض غرفة LiveKit
  return (
    <div className="app">
      <LiveKitRoom
        serverUrl={import.meta.env.VITE_LIVEKIT_URL}
        token={token}
        connect={true}
        video={false}
        audio={true}
        onDisconnected={() => {
          console.log('انقطع الاتصال')
          handleDisconnect()
        }}
        onConnected={() => {
          console.log('تم الاتصال بنجاح')
        }}
      >
        <div className="room-container">
          <div className="room-header">
            <h2>مرحباً {name} 👋</h2>
            <button onClick={handleDisconnect} className="disconnect-btn">
              ✕ إنهاء المحادثة
            </button>
          </div>

          <VoiceAgent />

          <div className="instructions">
            <h3>جرب أن تقول:</h3>
            <div className="examples">
              <div className="example">💡 أحتاج كارت شاشة مناسب للالعاب</div>
              <div className="example">💡 عندك ماوس RGB</div>
              <div className="example">💡 سآخذ كيبورد Redragon </div>
            </div>
          </div>

          <RoomAudioRenderer />
        </div>
      </LiveKitRoom>
    </div>
  )
}

export default App