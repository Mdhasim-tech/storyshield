import { useEffect, useMemo, useState } from 'react'

const API_BASE = 'http://localhost:5000/api'

const initialForm = {
  name: '',
  email: '',
  password: ''
}

function App() {
  const [isAuthView, setIsAuthView] = useState(true)
  const [form, setForm] = useState(initialForm)
  const [token, setToken] = useState(localStorage.getItem('storyshield_token') || '')
  const [user, setUser] = useState(null)
  const [books, setBooks] = useState([])
  const [selectedBookId, setSelectedBookId] = useState('')
  const [currentPosition, setCurrentPosition] = useState({ chapter_order: 1, page: 1 })
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [messages, setMessages] = useState([])
  const [status, setStatus] = useState('')

  const pdfUrl = selectedBookId ? `${API_BASE.replace('/api', '')}/uploads/${selectedBookId}.pdf` : ''

  const authHeaders = useMemo(() => ({
    'Content-Type': 'application/json',
    Authorization: token ? `Bearer ${token}` : ''
  }), [token])

  useEffect(() => {
    if (!token) {
      setUser(null)
      return
    }

    fetch(`${API_BASE}/auth/me`, {
      headers: authHeaders
    })
      .then((res) => res.ok ? res.json() : Promise.reject(res))
      .then((data) => setUser(data.user))
      .catch(() => {
        setUser(null)
        setToken('')
        localStorage.removeItem('storyshield_token')
      })
  }, [token])

  useEffect(() => {
    if (!token) {
      setBooks([])
      return
    }

    fetch(`${API_BASE}/books`, {
      headers: authHeaders
    })
      .then((res) => res.ok ? res.json() : Promise.reject(res))
      .then((data) => {
        const nextBooks = Array.isArray(data) ? data : []
        setBooks(nextBooks)
        if (nextBooks.length && !nextBooks.some((book) => book._id === selectedBookId)) {
          setSelectedBookId(nextBooks[0]._id)
        }
      })
      .catch(() => setBooks([]))
  }, [token])

  useEffect(() => {
    if (!selectedBookId || !token) return

    fetch(`${API_BASE}/books/${selectedBookId}/progress`, {
      headers: authHeaders
    })
      .then((res) => res.ok ? res.json() : Promise.reject(res))
      .then((data) => {
        const nextPosition = {
          chapter_order: Math.max(Number(data.chapter_order || 1), 1),
          page: Math.max(Number(data.page || 1), 1)
        }
        setCurrentPosition(nextPosition)
        setMessages([])
        setAnswer('')
      })
      .catch(() => setCurrentPosition({ chapter_order: 1, page: 1 }))
  }, [selectedBookId, token])

  const saveProgress = async (nextPosition) => {
    if (!selectedBookId || !token) return

    const payload = {
      chapter_order: Math.max(Number(nextPosition.chapter_order || 1), 1),
      page: Math.max(Number(nextPosition.page || 1), 1)
    }

    await fetch(`${API_BASE}/books/${selectedBookId}/progress`, {
      method: 'PUT',
      headers: authHeaders,
      body: JSON.stringify(payload)
    })
  }

  const moveReaderPosition = (chapterDelta = 0, pageDelta = 0) => {
    setCurrentPosition((prev) => {
      const next = {
        chapter_order: Math.max(Number(prev.chapter_order || 1) + chapterDelta, 1),
        page: Math.max(Number(prev.page || 1) + pageDelta, 1)
      }

      saveProgress(next)
      return next
    })
  }

  const handleAuthSubmit = async (event) => {
    event.preventDefault()
    const endpoint = isAuthView ? '/auth/login' : '/auth/register'
    const body = isAuthView ? { email: form.email, password: form.password } : form

    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })

    const data = await response.json()
    if (!response.ok) {
      setStatus(data.error || 'Authentication failed')
      return
    }

    setToken(data.token)
    localStorage.setItem('storyshield_token', data.token)
    setUser(data.user)
    setStatus(isAuthView ? 'Logged in successfully' : 'Account created successfully')
    setForm(initialForm)
  }

  const handleBookUpload = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)
    formData.append('title', file.name)

    const response = await fetch(`${API_BASE}/books/upload`, {
      method: 'POST',
      headers: { Authorization: token ? `Bearer ${token}` : '' },
      body: formData
    })

    const data = await response.json()
    if (!response.ok) {
      setStatus(data.error || 'Upload failed')
      return
    }

    setStatus(`Book uploaded successfully: ${data.book_id}`)
    const refreshed = await fetch(`${API_BASE}/books`, { headers: authHeaders })
    const list = await refreshed.json()
    setBooks(list)

    if (list.length) {
      const uploadedBook = list.find((book) => book._id === data.book_id) || list[list.length - 1]
      if (uploadedBook) {
        setSelectedBookId(uploadedBook._id)
      }
    }
  }

  const handleAskQuestion = async () => {
    if (!selectedBookId || !question.trim()) return

    const userQuestion = question.trim()
    setMessages((prev) => [...prev, { role: 'user', text: userQuestion }])
    setQuestion('')

    const response = await fetch(`${API_BASE}/books/${selectedBookId}/ask`, {
      method: 'POST',
      headers: authHeaders,
      body: JSON.stringify({
        question: userQuestion,
        chapter_order: currentPosition.chapter_order,
        page: currentPosition.page
      })
    })

    const data = await response.json()
    if (!response.ok) {
      setStatus(data.error || 'Unable to answer question')
      return
    }

    const nextAnswer = data.answer || 'No answer available yet'
    setAnswer(nextAnswer)
    setMessages((prev) => [...prev, { role: 'assistant', text: nextAnswer }])
    setStatus(data.blocked ? 'This information is beyond your current reading position.' : 'Answer generated from your current reading context.')
  }

  const handleProgressSave = async () => {
    if (!selectedBookId) return

    const response = await fetch(`${API_BASE}/books/${selectedBookId}/progress`, {
      method: 'PUT',
      headers: authHeaders,
      body: JSON.stringify(currentPosition)
    })

    if (response.ok) {
      setStatus('Reading progress saved.')
    } else {
      setStatus('Unable to save reading progress.')
    }
  }

  if (!token || !user) {
    return (
      <div className="auth-shell">
        <div className="auth-card">
          <h1>StoryShield</h1>
          <p>{isAuthView ? 'Sign in to continue reading' : 'Create your reading account'}</p>
          <form onSubmit={handleAuthSubmit} className="auth-form">
            {!isAuthView && (
              <input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Full name"
              />
            )}
            <input
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              placeholder="Email"
            />
            <input
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              placeholder="Password"
            />
            <button type="submit">{isAuthView ? 'Log in' : 'Create account'}</button>
          </form>
          <button className="toggle-btn" onClick={() => setIsAuthView((val) => !val)}>
            {isAuthView ? 'Need an account? Sign up' : 'Already have an account? Log in'}
          </button>
          {status && <p className="status">{status}</p>}
        </div>
      </div>
    )
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-header">
          <h2>StoryShield</h2>
          <button
            className="logout-btn"
            onClick={() => {
              setToken('')
              setUser(null)
              localStorage.removeItem('storyshield_token')
            }}
          >
            Logout
          </button>
        </div>

        <div className="profile-box">
          <h3>{user.name}</h3>
          <p>{user.email}</p>
        </div>

        <label className="upload-box">
          <span>Upload a book</span>
          <input type="file" accept="application/pdf" onChange={handleBookUpload} />
        </label>

        <div className="book-list">
          {books.map((book) => (
            <button
              key={book._id}
              className={selectedBookId === book._id ? 'book-item active' : 'book-item'}
              onClick={() => setSelectedBookId(book._id)}
            >
              {book.title}
            </button>
          ))}
        </div>
      </aside>

      <main className="reader-panel">
        <div className="reader-header">
          <h3>Reading view</h3>
          <div className="progress-controls">
            <div className="reader-tools">
              <button type="button" onClick={() => moveReaderPosition(0, -1)}>Prev page</button>
              <button type="button" onClick={() => moveReaderPosition(1, 0)}>Next chapter</button>
              <button type="button" onClick={() => moveReaderPosition(0, 1)}>Next page</button>
            </div>
            <label>
              Chapter
              <input
                type="number"
                min="1"
                value={currentPosition.chapter_order}
                onChange={(e) => {
                  const next = { ...currentPosition, chapter_order: Math.max(Number(e.target.value || 1), 1) }
                  setCurrentPosition(next)
                  saveProgress(next)
                }}
              />
            </label>
            <label>
              Page
              <input
                type="number"
                min="1"
                value={currentPosition.page}
                onChange={(e) => {
                  const next = { ...currentPosition, page: Math.max(Number(e.target.value || 1), 1) }
                  setCurrentPosition(next)
                  saveProgress(next)
                }}
              />
            </label>
            <button onClick={handleProgressSave}>Save progress</button>
          </div>
        </div>

        {selectedBookId ? (
          <div className="pdf-reader-shell">
            <iframe
              title="Book reader"
              src={pdfUrl}
              className="pdf-frame"
              loading="lazy"
            />
            <div className="reader-meta">
              <span>Current chapter: {currentPosition.chapter_order}</span>
              <span>Current page: {currentPosition.page}</span>
            </div>
          </div>
        ) : (
          <div className="pdf-placeholder">
            <p>Select a book to open it in the reader.</p>
          </div>
        )}

        <div className="chat-panel">
          <div className="chat-header">
            <h4>Reading assistant</h4>
          </div>
          <div className="chat-box">
            {messages.length ? (
              messages.map((message, index) => (
                <div key={`${message.role}-${index}`} className={`message ${message.role}`}>
                  <strong>{message.role === 'assistant' ? 'Assistant' : 'You'}:</strong>
                  <span>{message.text}</span>
                </div>
              ))
            ) : (
              <p>{answer || 'Ask about the story while staying within your current reading position.'}</p>
            )}
          </div>
          <div className="chat-input-row">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask a spoiler-safe question"
            />
            <button onClick={handleAskQuestion}>Ask</button>
          </div>
          {status && <p className="status">{status}</p>}
        </div>
      </main>
    </div>
  )
}

export default App
