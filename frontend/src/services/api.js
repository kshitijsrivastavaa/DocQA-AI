const API = 'http://localhost:8000'

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export const fetchDocuments = () => request('/api/documents/')

export const fetchDocument = (id) => request(`/api/documents/${id}`)

export const uploadDocument = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  const response = await fetch(`${API}/api/documents/upload`, {
    method: 'POST',
    body: formData,
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Upload failed' }))
    throw new Error(error.detail || 'Upload failed')
  }
  return response.json()
}

export const createChatSession = (documentId) =>
  request('/api/chat/sessions', {
    method: 'POST',
    body: JSON.stringify({ document_id: documentId }),
  })

export const getMessages = (sessionId) =>
  request(`/api/chat/sessions/${sessionId}/messages`)

export const streamChat = async (sessionId, message, onChunk) => {
  const response = await fetch(`${API}/api/chat/sessions/${sessionId}/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Chat failed' }))
    throw new Error(error.detail || 'Chat failed')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let fullContent = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const text = decoder.decode(value)
    const lines = text.split('\n')

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6)
        if (data === '[DONE]') continue
        onChunk(data)
        fullContent += data
      }
    }
  }

  return fullContent
}
