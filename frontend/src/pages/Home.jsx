import React, { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { uploadDocument } from '../services/api'

const ACCEPTED = {
  'application/pdf': ['.pdf'],
  'audio/*': ['.mp3', '.wav', '.m4a', '.ogg'],
  'video/*': ['.mp4', '.mov', '.avi', '.webm', '.mkv'],
}

const FEATURES = [
  { icon: '📄', title: 'PDF Analysis', desc: 'Extract and search through document content' },
  { icon: '🎵', title: 'Audio Q&A', desc: 'Transcribe and query audio recordings' },
  { icon: '🎬', title: 'Video Q&A', desc: 'Understand video content with timestamps' },
  { icon: '🔍', title: 'Semantic Search', desc: 'FAISS-powered vector similarity search' },
]

export default function Home() {
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const handleFile = useCallback(async (file) => {
    if (!file) return
    setError('')
    setUploading(true)
    try {
      const doc = await uploadDocument(file)
      await queryClient.invalidateQueries({ queryKey: ['documents'] })
      navigate(`/doc/${doc.id}`)
    } catch (err) {
      setError(err.message || 'Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }, [navigate, queryClient])

  const onDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }, [handleFile])

  const onInputChange = (e) => {
    const file = e.target.files[0]
    if (file) handleFile(file)
  }

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px 24px', animation: 'fadeUp 0.4s ease' }}>
      {/* Hero */}
      <div style={{ textAlign: 'center', maxWidth: 560, marginBottom: 48 }}>
        <div style={{ fontSize: 56, marginBottom: 16 }}>🧠</div>
        <h1 style={{ fontSize: 40, fontWeight: 800, marginBottom: 12, background: 'linear-gradient(135deg, #e8e8f0, var(--accent))', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          Ask Anything About Your Files
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: 17, lineHeight: 1.6 }}>
          Upload PDFs, audio recordings, or videos — then chat with an AI that understands every word.
        </p>
      </div>

      {/* Drop Zone */}
      <div
        onDragEnter={(e) => { e.preventDefault(); setDragging(true) }}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        style={{
          width: '100%', maxWidth: 520,
          border: `2px dashed ${dragging ? 'var(--accent)' : 'var(--border)'}`,
          borderRadius: 16,
          padding: '48px 32px',
          textAlign: 'center',
          background: dragging ? 'var(--accent-glow)' : 'var(--surface)',
          transition: 'all 0.2s',
          cursor: uploading ? 'not-allowed' : 'pointer',
          position: 'relative',
          marginBottom: 16,
        }}
      >
        <input
          type="file"
          accept=".pdf,.mp3,.wav,.m4a,.ogg,.mp4,.mov,.avi,.webm,.mkv"
          onChange={onInputChange}
          disabled={uploading}
          style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer', zIndex: 1 }}
        />
        
        {uploading ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
            <div className="spinner" style={{ width: 32, height: 32, borderWidth: 3 }} />
            <div style={{ color: 'var(--text-muted)' }}>Uploading and processing...</div>
          </div>
        ) : (
          <>
            <div style={{ fontSize: 40, marginBottom: 12 }}>📂</div>
            <div style={{ fontFamily: 'Syne', fontWeight: 700, fontSize: 20, marginBottom: 8 }}>
              Drop your file here
            </div>
            <div style={{ color: 'var(--text-muted)', fontSize: 14, marginBottom: 20 }}>
              or click to browse
            </div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'center', flexWrap: 'wrap' }}>
              {['PDF', 'MP3', 'WAV', 'MP4', 'MOV', 'WebM'].map(ext => (
                <span key={ext} style={{
                  padding: '3px 10px', borderRadius: 99,
                  background: 'var(--surface-2)', border: '1px solid var(--border)',
                  fontSize: 12, color: 'var(--text-muted)', fontWeight: 500
                }}>.{ext}</span>
              ))}
            </div>
          </>
        )}
      </div>

      {error && (
        <div style={{
          maxWidth: 520, width: '100%',
          padding: '12px 16px', borderRadius: 8,
          background: 'rgba(255,107,107,0.1)', border: '1px solid rgba(255,107,107,0.3)',
          color: 'var(--red)', fontSize: 14, marginBottom: 16,
        }}>
          ⚠️ {error}
        </div>
      )}

      {/* Feature pills */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12, maxWidth: 520, width: '100%', marginTop: 8 }}>
        {FEATURES.map(f => (
          <div key={f.title} style={{
            background: 'var(--surface)', border: '1px solid var(--border)',
            borderRadius: 12, padding: '14px 16px',
            display: 'flex', gap: 12, alignItems: 'flex-start',
          }}>
            <span style={{ fontSize: 22 }}>{f.icon}</span>
            <div>
              <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 2 }}>{f.title}</div>
              <div style={{ color: 'var(--text-muted)', fontSize: 12 }}>{f.desc}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
