import { useState, useRef, useEffect } from 'react'
import client from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function ChatWidget() {
  const { user } = useAuth()
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([
    { role: 'bot', content: "Hi! I'm CareerBot 👋 I can help with job search, resume feedback, interview prep, career guidance, skills, and salary insights. What's on your mind?", suggestions: ['Search Jobs', 'Analyze my resume', 'Practice interview'] },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bodyRef = useRef(null)

  useEffect(() => {
    if (bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight
  }, [messages, open])

  if (!user) return null

  const send = async (text) => {
    const msg = (text ?? input).trim()
    if (!msg) return
    setMessages((m) => [...m, { role: 'user', content: msg }])
    setInput('')
    setLoading(true)
    try {
      const res = await client.post('/chatbot/message', { message: msg })
      setMessages((m) => [...m, { role: 'bot', content: res.data.reply, suggestions: res.data.suggestions }])
    } catch {
      setMessages((m) => [...m, { role: 'bot', content: "Sorry, I hit a snag. Please try again." }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      {open && (
        <div className="chat-panel">
          <div className="chat-header">
            <span>CareerBot</span>
            <button className="btn-ghost" style={{ color: '#fff', padding: 4 }} onClick={() => setOpen(false)}>✕</button>
          </div>
          <div className="chat-body" ref={bodyRef}>
            {messages.map((m, i) => (
              <div key={i} className={`chat-bubble ${m.role}`}>{m.content}</div>
            ))}
            {loading && <div className="chat-bubble bot">Typing…</div>}
          </div>
          {messages[messages.length - 1]?.suggestions?.length > 0 && (
            <div className="chat-suggestions">
              {messages[messages.length - 1].suggestions.map((s) => (
                <button key={s} onClick={() => send(s)}>{s}</button>
              ))}
            </div>
          )}
          <div className="chat-input-row">
            <input
              placeholder="Ask CareerBot anything…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && send()}
            />
            <button className="btn btn-accent btn-sm" onClick={() => send()}>Send</button>
          </div>
        </div>
      )}
      <button className="chat-fab" onClick={() => setOpen((o) => !o)}>{open ? '✕' : '💬'}</button>
    </>
  )
}
