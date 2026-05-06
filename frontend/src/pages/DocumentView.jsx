import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchDocument, createChatSession, streamChat, getMessages } from '../services/api'

// ✅ FIXED: production-safe API URL
const API = "https://docqa-ai-production.up.railway.app"

function formatTime(secs) {
  if (!secs && secs !== 0) return ''
  const m = Math.floor(secs / 60)
  const s = Math.floor(secs % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

export default function DocumentView() {
  const { id } = useParams()
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const chatEndRef = useRef(null)

  const { data: doc, isLoading } = useQuery({
    queryKey: ['document', id],
    queryFn: () => fetchDocument(id),
  })

  useEffect(() => {
    if (doc?.status === 'completed' && !sessionId) {
      createChatSession(id).then(s => setSessionId(s.session_id))
    }
  }, [doc?.status, id, sessionId])

  useEffect(() => {
    if (sessionId) {
      getMessages(sessionId).then(data => setMessages(data.messages || []))
    }
  }, [sessionId])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = useCallback(async () => {
    if (!input.trim() || !sessionId || streaming) return

    const text = input.trim()
    setInput('')
    setStreaming(true)

    const userMsg = { role: 'user', content: text, id: Date.now() }
    const aiMsg = { role: 'assistant', content: '', id: Date.now() + 1 }

    setMessages(prev => [...prev, userMsg, aiMsg])

    try {
      await streamChat(sessionId, text, (chunk) => {
        setMessages(prev => {
          const copy = [...prev]
          copy[copy.length - 1].content += chunk
          return copy
        })
      })
    } catch (err) {
      setMessages(prev => {
        const copy = [...prev]
        copy[copy.length - 1].content = '⚠️ Error: ' + err.message
        return copy
      })
    } finally {
      setStreaming(false)
    }
  }, [input, sessionId, streaming])

  if (isLoading) return <div>Loading...</div>
  if (!doc) return <div>Document not found</div>

  return (
    <div style={{ padding: 20 }}>
      <h2>{doc.original_filename}</h2>

      {/* ✅ MEDIA FIXED */}
      {(doc.file_type === 'audio' || doc.file_type === 'video') && (
        <div>
          {doc.file_type === 'video' ? (
            <video
              controls
              width="100%"
              src={`${API}/api/media/${id}/stream`}
            />
          ) : (
            <audio
              controls
              src={`${API}/api/media/${id}/stream`}
            />
          )}
        </div>
      )}

      {/* CHAT */}
      <div style={{ marginTop: 20 }}>
        {messages.map((m, i) => (
          <div key={i} style={{ marginBottom: 10 }}>
            <b>{m.role}:</b> {m.content}
          </div>
        ))}
        <div ref={chatEndRef} />
      </div>

      <textarea
        value={input}
        onChange={e => setInput(e.target.value)}
        placeholder="Ask something..."
        style={{ width: '100%', marginTop: 10 }}
      />

      <button onClick={sendMessage} disabled={streaming}>
        Send
      </button>
    </div>
  )
}