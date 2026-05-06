import React from 'react'
import { Outlet, NavLink } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchDocuments } from '../services/api'

// ❌ removed: styled import (file doesn't exist)
// ❌ removed: useNavigate (not used)

const fileIcon = (type) => {
  if (type === 'pdf') return '📄'
  if (type === 'audio') return '🎵'
  if (type === 'video') return '🎬'
  return '📁'
}

const statusColor = (status) => {
  if (status === 'completed') return '#43d9ad'
  if (status === 'failed') return '#ff6b6b'
  if (status === 'processing') return '#ffcc66'
  return '#7070a0'
}

export default function Layout() {
  const { data: docs = [] } = useQuery({
    queryKey: ['documents'],
    queryFn: fetchDocuments,
    refetchInterval: 3000,
  })

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>

      {/* Sidebar */}
      <aside style={{
        width: 260,
        background: 'var(--surface)',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        flexShrink: 0,
        overflow: 'hidden',
      }}>

        {/* Logo */}
        <div style={{ padding: '20px 20px 16px', borderBottom: '1px solid var(--border)' }}>
          <NavLink to="/" style={{ textDecoration: 'none', color: 'inherit' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{
                width: 32, height: 32,
                background: 'linear-gradient(135deg, var(--accent), var(--accent-2))',
                borderRadius: 8,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 16,
              }}>🧠</div>
              <div>
                <div style={{ fontFamily: 'Syne', fontWeight: 800, fontSize: 18, lineHeight: 1 }}>
                  DocQA
                </div>
                <div style={{ color: 'var(--text-muted)', fontSize: 11 }}>
                  AI Document Assistant
                </div>
              </div>
            </div>
          </NavLink>
        </div>

        {/* Upload nav */}
        <div style={{ padding: '12px 12px 8px' }}>
          <NavLink to="/" style={({ isActive }) => ({
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '8px 12px',
            borderRadius: 'var(--radius-sm)',
            background: isActive ? 'var(--accent-glow)' : 'transparent',
            color: isActive ? 'var(--accent)' : 'var(--text-muted)',
            fontSize: 14,
            fontWeight: 500,
            transition: 'all 0.15s',
          })}>
            <span>➕</span> Upload New File
          </NavLink>
        </div>

        {/* Documents list */}
        <div style={{ flex: 1, overflow: 'auto', padding: '0 12px 12px' }}>
          {docs.length > 0 && (
            <div style={{
              fontSize: 11,
              color: 'var(--text-dim)',
              padding: '8px 4px 6px',
              fontWeight: 600,
              letterSpacing: '0.08em',
              textTransform: 'uppercase'
            }}>
              Documents ({docs.length})
            </div>
          )}

          {docs.map(doc => (
            <NavLink
              key={doc.id}
              to={`/doc/${doc.id}`}
              style={({ isActive }) => ({
                display: 'flex',
                flexDirection: 'column',
                gap: 2,
                padding: '8px 12px',
                borderRadius: 'var(--radius-sm)',
                background: isActive ? 'var(--surface-2)' : 'transparent',
                marginBottom: 2,
                transition: 'background 0.15s',
                borderLeft: isActive ? '2px solid var(--accent)' : '2px solid transparent',
                textDecoration: 'none',
                color: 'inherit',
              })}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ fontSize: 14 }}>{fileIcon(doc.file_type)}</span>
                <span style={{
                  fontSize: 13,
                  fontWeight: 500,
                  flex: 1,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap'
                }}>
                  {doc.original_filename}
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 6, paddingLeft: 20 }}>
                <span style={{
                  width: 6,
                  height: 6,
                  borderRadius: '50%',
                  background: statusColor(doc.status),
                  flexShrink: 0
                }} />
                <span style={{
                  fontSize: 11,
                  color: 'var(--text-muted)',
                  textTransform: 'capitalize'
                }}>
                  {doc.status}
                </span>
              </div>
            </NavLink>
          ))}

          {docs.length === 0 && (
            <div style={{
              textAlign: 'center',
              color: 'var(--text-dim)',
              fontSize: 13,
              padding: '24px 8px'
            }}>
              No files uploaded yet
            </div>
          )}
        </div>
      </aside>

      {/* Main content */}
      <main style={{
        flex: 1,
        overflow: 'auto',
        display: 'flex',
        flexDirection: 'column'
      }}>
        <Outlet />
      </main>

    </div>
  )
}
