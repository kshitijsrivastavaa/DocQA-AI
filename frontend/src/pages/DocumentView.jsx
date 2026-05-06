import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchDocument, createChatSession, streamChat, getMessages } from '../services/api'

const API = 'http://localhost:8000'

function formatTime(secs) {
  if (!secs && secs !== 0) return ''
  const m = Math.floor(secs / 60)
  const s = Math.floor(secs % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function StatusBadge({ status }) {
  const colors = {
    completed: { bg: 'rgba(67,217,173,0.15)', color: '#43d9ad', dot: '#43d9ad' },
    processing: { bg: 'rgba(255,204,102,0.15)', color: '#ffcc66', dot: '#ffcc66' },
    pending: { bg: 'rgba(112,112,160,0.15)', color: '#7070a0', dot: '#7070a0' },
    failed: { bg: 'rgba(255,107,107,0.15)', color: '#ff6b6b', dot: '#ff6b6b' },
  }
  const c = colors[status] || colors.pending
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      padding: '3px 10px', borderRadius: 99,
      background: c.bg, color: c.color,
      fontSize: 12, fontWeight: 600,
    }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: c.dot, animation: status === 'processing' ? 'pulse 1.2s infinite' : 'none' }} />
      {status}
    </span>
  )
}

function MediaPlayer({ docId, fileType, timestamps, seekTo }) {
  const mediaRef = useRef(null)
  const [playing, setPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)

  useEffect(() => {
    if (seekTo !== null && mediaRef.current) {
      mediaRef.current.currentTime = seekTo
      mediaRef.current.play()
    }
  }, [seekTo])

  const toggle = () => {
    if (!mediaRef.current) return
    playing ? mediaRef.current.pause() : mediaRef.current.play()
  }

  const onTimeUpdate = () => setCurrentTime(mediaRef.current?.currentTime || 0)
  const onLoadedMetadata = () => setDuration(mediaRef.current?.duration || 0)

  const progress = duration ? (currentTime / duration) * 100 : 0

  const seekBar = (e) => {
    const rect = e.currentTarget.getBoundingClientRect()
    const pct = (e.clientX - rect.left) / rect.width
    if (mediaRef.current) {
      mediaRef.current.currentTime = pct * duration
    }
  }

  const isVideo = fileType === 'video'

  return (
    <div style={{
      background: 'var(--surface-2)', borderRadius: 12, overflow: 'hidden',
      border: '1px solid var(--border)',
    }}>
      {isVideo ? (
        <video
          ref={mediaRef}
          src={`${API}/api/media/${docId}/stream`}
          style={{ width: '100%', maxHeight: 280, display: 'block', background: '#000' }}
          onTimeUpdate={onTimeUpdate}
          onLoadedMetadata={onLoadedMetadata}
          onPlay={() => setPlaying(true)}
          onPause={() => setPlaying(false)}
          controls
        />
      ) : (
        <audio
          ref={mediaRef}
          src={`${API}/api/media/${docId}/stream`}
          onTimeUpdate={onTimeUpdate}
          onLoadedMetadata={onLoadedMetadata}
          onPlay={() => setPlaying(true)}
          onPause={() => setPlaying(false)}
        />
      )}

      {!isVideo && (
        <div style={{ padding: '16px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
            <button
              onClick={toggle}
              style={{
                width: 40, height: 40, borderRadius: '50%',
                background: 'var(--accent)', color: '#fff',
                fontSize: 16, display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0,
              }}
            >
              {playing ? '⏸' : '▶'}
            </button>
            <div style={{ flex: 1 }}>
              <div
                onClick={seekBar}
                style={{
                  height: 4, background: 'var(--border)', borderRadius: 99, cursor: 'pointer',
                  position: 'relative',
                }}
              >
                <div style={{
                  height: '100%', width: `${progress}%`,
                  background: 'var(--accent)', borderRadius: 99,
                  transition: 'width 0.1s',
                }} />
              </div>
            </div>
            <span style={{ color: 'var(--text-muted)', fontSize: 12, flexShrink: 0 }}>
              {formatTime(currentTime)} / {formatTime(duration)}
            </span>
          </div>
        </div>
      )}

      {/* Timestamps */}
      {timestamps && timestamps.length > 0 && (
        <div style={{ padding: '0 16px 16px', borderTop: '1px solid var(--border)' }}>
          <div style={{ fontSize: 11, color: 'var(--text-dim)', padding: '12px 0 8px', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
            Relevant Timestamps
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {timestamps.map((ts, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'flex-start', gap: 10,
                padding: '8px 10px', borderRadius: 8,
                background: 'var(--surface)', border: '1px solid var(--border)',
              }}>
                <button
                  onClick={() => mediaRef.current && ((mediaRef.current.currentTime = ts.start), mediaRef.current.play())}
                  style={{
                    flexShrink: 0, padding: '3px 8px', borderRadius: 6,
                    background: 'var(--accent-glow)', color: 'var(--accent)',
                    fontSize: 12, fontWeight: 600, fontFamily: 'monospace',
                    border: '1px solid rgba(108,99,255,0.3)',
                    cursor: 'pointer',
                  }}
                >
                  {formatTime(ts.start)}
                </button>
                <span style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.4 }}>{ts.text}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function ChatBubble({ msg, onSeek }) {
  const isUser = msg.role === 'user'
  return (
    <div style={{
      display: 'flex',
      justifyContent: isUser ? 'flex-end' : 'flex-start',
      marginBottom: 12,
      animation: 'fadeUp 0.3s ease',
    }}>
      {!isUser && (
        <div style={{
          width: 28, height: 28, borderRadius: '50%',
          background: 'linear-gradient(135deg, var(--accent), var(--accent-2))',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 14, flexShrink: 0, marginRight: 8, alignSelf: 'flex-end',
        }}>🧠</div>
      )}
      <div style={{
        maxWidth: '75%',
        background: isUser ? 'var(--accent)' : 'var(--surface-2)',
        color: isUser ? '#fff' : 'var(--text)',
        borderRadius: isUser ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
        padding: '10px 14px',
        fontSize: 14, lineHeight: 1.6,
        border: isUser ? 'none' : '1px solid var(--border)',
      }}>
        <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>

        {msg.relevant_timestamps && msg.relevant_timestamps.length > 0 && onSeek && (
          <div style={{ marginTop: 10, display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {msg.relevant_timestamps.map((ts, i) => (
              <button
                key={i}
                onClick={() => onSeek(ts.start)}
                style={{
                  padding: '3px 9px', borderRadius: 6,
                  background: 'rgba(255,255,255,0.15)', color: '#fff',
                  fontSize: 12, fontWeight: 600, fontFamily: 'monospace',
                  border: '1px solid rgba(255,255,255,0.2)',
                  cursor: 'pointer',
                }}
              >
                ▶ {formatTime(ts.start)}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default function DocumentView() {
  const { id } = useParams()
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [activeTab, setActiveTab] = useState('chat')
  const [seekTo, setSeekTo] = useState(null)
  const [currentTimestamps, setCurrentTimestamps] = useState(null)
  const chatEndRef = useRef(null)
  const queryClient = useQueryClient()

  const { data: doc, isLoading } = useQuery({
    queryKey: ['document', id],
    queryFn: () => fetchDocument(id),
    refetchInterval: (data) => data?.status === 'completed' ? false : 2000,
  })

  // Create chat session when doc is ready
  useEffect(() => {
    if (doc?.status === 'completed' && !sessionId) {
      createChatSession(id).then(s => setSessionId(s.session_id))
    }
  }, [doc?.status, id, sessionId])

  // Load messages when session exists
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
    const aiMsg = { role: 'assistant', content: '', id: Date.now() + 1, relevant_timestamps: null }
    setMessages(prev => [...prev, userMsg, aiMsg])

    try {
      const finalMsg = await streamChat(sessionId, text, (chunk) => {
        setMessages(prev => {
          const copy = [...prev]
          copy[copy.length - 1] = { ...copy[copy.length - 1], content: copy[copy.length - 1].content + chunk }
          return copy
        })
      })

      // Refresh messages to get timestamps
      const updated = await getMessages(sessionId)
      const msgs = updated.messages || []
      setMessages(msgs)
      const lastAI = [...msgs].reverse().find(m => m.role === 'assistant')
      if (lastAI?.relevant_timestamps) {
        setCurrentTimestamps(lastAI.relevant_timestamps)
      }
    } catch (err) {
      setMessages(prev => {
        const copy = [...prev]
        copy[copy.length - 1] = { ...copy[copy.length - 1], content: '⚠️ Error: ' + (err.message || 'Something went wrong') }
        return copy
      })
    } finally {
      setStreaming(false)
    }
  }, [input, sessionId, streaming])

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const isMedia = doc?.file_type === 'audio' || doc?.file_type === 'video'

  if (isLoading) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="spinner" style={{ width: 32, height: 32, borderWidth: 3 }} />
      </div>
    )
  }

  if (!doc) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
        Document not found
      </div>
    )
  }

  const fileEmoji = doc.file_type === 'pdf' ? '📄' : doc.file_type === 'audio' ? '🎵' : '🎬'

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      {/* Header */}
      <div style={{
        padding: '16px 24px', borderBottom: '1px solid var(--border)',
        background: 'var(--surface)', display: 'flex', alignItems: 'center', gap: 12,
        flexShrink: 0,
      }}>
        <span style={{ fontSize: 24 }}>{fileEmoji}</span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontFamily: 'Syne', fontWeight: 700, fontSize: 17, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {doc.original_filename}
          </div>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginTop: 2 }}>
            <StatusBadge status={doc.status} />
            <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>
              {(doc.file_size / 1024).toFixed(0)} KB
            </span>
            {doc.duration_seconds && (
              <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>
                {formatTime(doc.duration_seconds)} duration
              </span>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: 4, background: 'var(--surface-2)', borderRadius: 8, padding: 3 }}>
          {['chat', 'summary', ...(isMedia ? ['media'] : [])].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                padding: '5px 14px', borderRadius: 6, fontSize: 13, fontWeight: 500,
                background: activeTab === tab ? 'var(--border)' : 'transparent',
                color: activeTab === tab ? 'var(--text)' : 'var(--text-muted)',
                transition: 'all 0.15s', textTransform: 'capitalize',
              }}
            >{tab}</button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {/* Processing state */}
        {doc.status !== 'completed' && (
          <div style={{ padding: '32px 24px', textAlign: 'center' }}>
            <div style={{ fontSize: 40, marginBottom: 16 }}>
              {doc.status === 'failed' ? '❌' : '⚙️'}
            </div>
            <div style={{ fontFamily: 'Syne', fontWeight: 700, fontSize: 20, marginBottom: 8 }}>
              {doc.status === 'failed' ? 'Processing Failed' : 'Processing your file...'}
            </div>
            <div style={{ color: 'var(--text-muted)', fontSize: 14 }}>
              {doc.status === 'failed' ? doc.error_message || 'An error occurred' : 'Extracting content, generating embeddings...'}
            </div>
            {doc.status !== 'failed' && (
              <div style={{ marginTop: 20, display: 'flex', justifyContent: 'center' }}>
                <div className="spinner" style={{ width: 28, height: 28, borderWidth: 2 }} />
              </div>
            )}
          </div>
        )}

        {/* Media Tab */}
        {activeTab === 'media' && isMedia && doc.status === 'completed' && (
          <div style={{ padding: 24, overflow: 'auto', flex: 1 }}>
            <MediaPlayer
              docId={id}
              fileType={doc.file_type}
              timestamps={currentTimestamps}
              seekTo={seekTo}
            />
          </div>
        )}

        {/* Summary Tab */}
        {activeTab === 'summary' && doc.status === 'completed' && (
          <div style={{ padding: 24, overflow: 'auto', flex: 1 }}>
            <div style={{
              background: 'var(--surface)', border: '1px solid var(--border)',
              borderRadius: 12, padding: 24,
            }}>
              <div style={{ fontFamily: 'Syne', fontWeight: 700, fontSize: 18, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                <span>📝</span> Content Summary
              </div>
              <p style={{ color: 'var(--text-muted)', lineHeight: 1.8, fontSize: 15 }}>
                {doc.summary || 'No summary available.'}
              </p>
            </div>
          </div>
        )}

        {/* Chat Tab */}
        {activeTab === 'chat' && doc.status === 'completed' && (
          <>
            <div style={{ flex: 1, overflow: 'auto', padding: '20px 24px' }}>
              {messages.length === 0 && (
                <div style={{ textAlign: 'center', color: 'var(--text-muted)', marginTop: 40 }}>
                  <div style={{ fontSize: 40, marginBottom: 12 }}>💬</div>
                  <div style={{ fontFamily: 'Syne', fontWeight: 700, fontSize: 18, marginBottom: 8 }}>Start a conversation</div>
                  <div style={{ fontSize: 14 }}>Ask anything about <strong>{doc.original_filename}</strong></div>
                  <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginTop: 20, flexWrap: 'wrap' }}>
                    {['Summarize this', 'What are the main topics?', 'Give me key insights'].map(q => (
                      <button key={q} onClick={() => setInput(q)} style={{
                        padding: '8px 16px', borderRadius: 99,
                        background: 'var(--surface-2)', border: '1px solid var(--border)',
                        color: 'var(--text-muted)', fontSize: 13, cursor: 'pointer',
                        transition: 'all 0.15s',
                      }}>{q}</button>
                    ))}
                  </div>
                </div>
              )}
              {messages.map((msg, i) => (
                <ChatBubble
                  key={msg.id || i}
                  msg={msg}
                  onSeek={isMedia ? (t) => { setSeekTo(t); setActiveTab('media') } : null}
                />
              ))}
              {streaming && messages[messages.length - 1]?.role === 'assistant' && messages[messages.length - 1]?.content === '' && (
                <div style={{ display: 'flex', gap: 4, paddingLeft: 36, marginBottom: 12 }}>
                  {[0, 1, 2].map(i => (
                    <div key={i} style={{
                      width: 8, height: 8, borderRadius: '50%',
                      background: 'var(--accent)',
                      animation: `pulse 1s ease ${i * 0.2}s infinite`,
                    }} />
                  ))}
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Input */}
            <div style={{
              padding: '16px 24px', borderTop: '1px solid var(--border)',
              background: 'var(--surface)', flexShrink: 0,
            }}>
              <div style={{ display: 'flex', gap: 10 }}>
                <textarea
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={onKeyDown}
                  placeholder="Ask a question about this document..."
                  rows={1}
                  disabled={streaming}
                  style={{
                    flex: 1, resize: 'none', padding: '10px 14px',
                    borderRadius: 10, fontSize: 14, lineHeight: 1.5,
                    maxHeight: 120, overflowY: 'auto',
                  }}
                />
                <button
                  onClick={sendMessage}
                  disabled={!input.trim() || streaming}
                  style={{
                    padding: '10px 20px', borderRadius: 10,
                    background: input.trim() && !streaming ? 'var(--accent)' : 'var(--surface-2)',
                    color: input.trim() && !streaming ? '#fff' : 'var(--text-dim)',
                    fontWeight: 600, fontSize: 14, flexShrink: 0,
                    transition: 'all 0.2s',
                  }}
                >
                  {streaming ? <span className="spinner" /> : 'Send ↑'}
                </button>
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 6 }}>
                Enter to send · Shift+Enter for newline
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
