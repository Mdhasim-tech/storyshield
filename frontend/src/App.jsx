import { useEffect, useMemo, useState } from 'react'

const API_BASE = 'http://localhost:5000/api'

const initialForm = {
  name: '',
  email: '',
  password: ''
}

function BrandLockup({ compact = false }) {
  return (
    <div className={compact ? 'brand-lockup compact' : 'brand-lockup'}>
      <span className="brand-mark" aria-hidden="true">
        <svg viewBox="0 0 32 32" fill="none">
          <path d="M5 7.5c4.5-1.6 8.2-.8 11 1.7v17c-2.8-2.5-6.5-3.3-11-1.7v-17Z" />
          <path d="M27 7.5c-4.5-1.6-8.2-.8-11 1.7v17c2.8-2.5 6.5-3.3 11-1.7v-17Z" />
          <path d="M16 9.3v16.9" />
        </svg>
      </span>
      <span className="brand-wordmark">
        <strong>StoryShield</strong>
        {!compact && <small>READ AT YOUR PACE</small>}
      </span>
    </div>
  )
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
  const [summary, setSummary] = useState('')
  const [summaryLoading, setSummaryLoading] = useState(false)
  const [asking, setAsking] = useState(false)
  const [allowFuture, setAllowFuture] = useState(false)
  const [messages, setMessages] = useState([])
  const [status, setStatus] = useState('')

  const selectedBook = books.find((book) => book._id === selectedBookId)
  const readingBooks = books.filter((book) => !['failed', 'processing'].includes(book.status))
  const readBookCount = readingBooks.filter((book) => book.reading_status === 'read').length
  const pendingBookCount = readingBooks.length - readBookCount
  const pdfUrl = selectedBookId
    ? `${API_BASE.replace('/api', '')}/uploads/${selectedBookId}.pdf#page=${currentPosition.page}`
    : ''

  const authHeaders = useMemo(() => ({
    'Content-Type': 'application/json',
    Authorization: token ? `Bearer ${token}` : ''
  }), [token])

  useEffect(() => {
    if (!token) {
      setUser(null)
      setAllowFuture(false)
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
        setSummary('')
      })
      .catch(() => setCurrentPosition({ chapter_order: 1, page: 1 }))
  }, [selectedBookId, token])

  const saveProgress = async (nextPosition, announce = false) => {
    if (!selectedBookId || !token) return

    const payload = {
      chapter_order: Math.max(Number(nextPosition.chapter_order || 1), 1),
      page: Math.max(Number(nextPosition.page || 1), 1)
    }

    try {
      const response = await fetch(`${API_BASE}/books/${selectedBookId}/progress`, {
        method: 'PUT',
        headers: authHeaders,
        body: JSON.stringify(payload)
      })
      if (!response.ok) throw new Error('Unable to save reading progress')
      if (announce) setStatus('Reading bookmark saved.')
    } catch {
      setStatus('Unable to save reading bookmark.')
    }
  }

  const moveReaderPosition = (chapterDelta = 0, pageDelta = 0) => {
    const next = {
      chapter_order: Math.max(Number(currentPosition.chapter_order || 1) + chapterDelta, 1),
      page: Math.max(Number(currentPosition.page || 1) + pageDelta, 1)
    }
    setCurrentPosition(next)
    saveProgress(next)
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
    setAllowFuture(false)
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

    setAsking(true)
    try {
      const response = await fetch(`${API_BASE}/books/${selectedBookId}/ask`, {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify({
          question: userQuestion,
          chapter_order: currentPosition.chapter_order,
          page: currentPosition.page,
          allow_future: allowFuture
        })
      })

      const data = await response.json().catch(() => ({}))
      if (!response.ok) {
        throw new Error(data.error || `The server returned ${response.status}. Please try again.`)
      }

      const nextAnswer = typeof data.answer === 'string' ? data.answer.trim() : ''
      if (!nextAnswer) throw new Error('The assistant returned an empty response. Please try again.')

      setMessages((prev) => [...prev, { role: 'assistant', text: nextAnswer }])
      setStatus(data.blocked
        ? 'This information is beyond your current reading position.'
        : allowFuture
          ? 'Spoiler mode is on; this answer may include future plot details.'
          : 'Answer generated from your current reading context.')
    } catch (error) {
      setStatus(error.message || 'Unable to answer question. Please try again.')
    } finally {
      setAsking(false)
    }
  }

  const handleGenerateSummary = async () => {
    if (!selectedBookId) return

    setSummaryLoading(true)
    try {
      const response = await fetch(`${API_BASE}/books/${selectedBookId}/ask`, {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify({
          question: 'Summarize what I have read so far.',
          chapter_order: currentPosition.chapter_order,
          page: currentPosition.page,
          allow_future: false
        })
      })

      const data = await response.json().catch(() => ({}))
      if (!response.ok) {
        throw new Error(data.error || `The server returned ${response.status}. Please try again.`)
      }
      const nextSummary = typeof data.answer === 'string' ? data.answer.trim() : ''
      if (!nextSummary) throw new Error('The assistant returned an empty summary. Please try again.')
      setSummary(nextSummary)
      setStatus('Summary covers your current reading position; future plot details are excluded.')
    } catch (error) {
      setStatus(error.message || 'Unable to generate summary.')
    } finally {
      setSummaryLoading(false)
    }
  }

  const handleReadingStatusToggle = async () => {
    if (!selectedBook) return

    const readingStatus = selectedBook.reading_status === 'read' ? 'pending' : 'read'
    try {
      const response = await fetch(`${API_BASE}/books/${selectedBookId}/reading-status`, {
        method: 'PUT',
        headers: authHeaders,
        body: JSON.stringify({ reading_status: readingStatus })
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.error || 'Unable to update book status')

      setBooks((previous) => previous.map((book) => (
        book._id === selectedBookId
          ? { ...book, reading_status: data.reading_status }
          : book
      )))
      setStatus(readingStatus === 'read' ? 'Book marked as read.' : 'Book moved to pending.')
    } catch (error) {
      setStatus(error.message || 'Unable to update book status.')
    }
  }

  const handleProgressSave = () => saveProgress(currentPosition, true)

  if (!token || !user) {
    return (
      <div className="auth-shell">
        <section className="auth-story">
          <BrandLockup />
          <div className="auth-story-copy">
            <p className="eyebrow">A READING SPACE THAT GETS YOU</p>
            <h1>Stay close to the story. <em>Leave spoilers behind.</em></h1>
            <p className="auth-story-description">
              A thoughtful reading companion that remembers your place and keeps every answer in step with you.
            </p>
            <div className="auth-promise-list">
              <div><span>01</span><p>Your place is saved as you read.</p></div>
              <div><span>02</span><p>Future plot details stay tucked away.</p></div>
              <div><span>03</span><p>Open the door to spoilers only when you choose.</p></div>
            </div>
          </div>
          <p className="auth-story-footer">MADE FOR THE MOMENTS BETWEEN THE PAGES</p>
        </section>

        <section className="auth-form-side">
          <div className="auth-card">
            <p className="eyebrow">{isAuthView ? 'WELCOME BACK' : 'A NEW CHAPTER'}</p>
            <h2>{isAuthView ? 'Sign in to your library' : 'Create your account'}</h2>
            <p className="auth-card-description">
              {isAuthView ? 'Pick up right where you left off.' : 'Your reading space is just a few details away.'}
            </p>
            <form onSubmit={handleAuthSubmit} className="auth-form">
              {!isAuthView && (
                <label className="field-group">
                  <span>Your name</span>
                  <input
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    placeholder="Full name"
                    autoComplete="name"
                    required
                  />
                </label>
              )}
              <label className="field-group">
                <span>Email address</span>
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  placeholder="you@example.com"
                  autoComplete="email"
                  required
                />
              </label>
              <label className="field-group">
                <span>Password</span>
                <input
                  type="password"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  placeholder="Enter your password"
                  autoComplete={isAuthView ? 'current-password' : 'new-password'}
                  required
                />
              </label>
              <button className="primary-button auth-submit" type="submit">
                {isAuthView ? 'Sign in' : 'Create account'}
                <span aria-hidden="true">→</span>
              </button>
            </form>
            <div className="auth-switch">
              <span>{isAuthView ? 'New to StoryShield?' : 'Already have an account?'}</span>
              <button type="button" onClick={() => setIsAuthView((val) => !val)}>
                {isAuthView ? 'Create an account' : 'Sign in'}
              </button>
            </div>
            {status && <p className="status auth-status" role="status">{status}</p>}
          </div>
          <p className="auth-form-footer">A quieter, more personal way to read.</p>
        </section>
      </div>
    )
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-main">
          <BrandLockup />
          <div className="library-heading">
            <div>
              <p className="sidebar-eyebrow">YOUR SPACE</p>
              <h2>My library</h2>
            </div>
            <span className="library-total">{readingBooks.length}</span>
          </div>

          <label className="upload-box">
            <span className="upload-mark" aria-hidden="true">+</span>
            <span className="upload-copy">
              <strong>Add a book</strong>
              <small>Choose a PDF to get started</small>
            </span>
            <input type="file" accept="application/pdf" onChange={handleBookUpload} />
          </label>

          <section className="library-summary" aria-label="Reading list counts">
            <div>
              <strong>{readBookCount}</strong>
              <span>Read</span>
            </div>
            <div>
              <strong>{pendingBookCount}</strong>
              <span>To read</span>
            </div>
          </section>

          <div className="book-list-heading">
            <span>YOUR BOOKS</span>
            <span>{readingBooks.length} titles</span>
          </div>
          <div className="book-list">
            {books.map((book) => (
              <button
                key={book._id}
                className={selectedBookId === book._id ? 'book-item active' : 'book-item'}
                onClick={() => setSelectedBookId(book._id)}
                aria-current={selectedBookId === book._id ? 'true' : undefined}
              >
                <span className="book-cover" aria-hidden="true">
                  <span />
                </span>
                <span className="book-item-copy">
                  <strong>{book.title}</strong>
                  <small>{book.reading_status === 'read' ? 'Finished' : 'In your list'}</small>
                </span>
                <span className={book.reading_status === 'read' ? 'book-status read' : 'book-status'}>
                  {book.reading_status === 'read' ? 'Read' : 'Pending'}
                </span>
              </button>
            ))}
            {!books.length && (
              <p className="empty-library">Your books will find a home here. Add a PDF to begin.</p>
            )}
          </div>
        </div>

        <div className="sidebar-footer">
          <span className="user-avatar" aria-hidden="true">
            {(user.name || user.email || 'R').charAt(0).toUpperCase()}
          </span>
          <span className="sidebar-user-copy">
            <strong>{user.name}</strong>
            <small>{user.email}</small>
          </span>
          <button
            type="button"
            className="logout-btn"
            aria-label="Log out"
            title="Log out"
            onClick={() => {
              setToken('')
              setUser(null)
              setAllowFuture(false)
              localStorage.removeItem('storyshield_token')
            }}
          >
            ↗
          </button>
        </div>
      </aside>

      <main className="reader-panel">
        <header className="workspace-header">
          <div>
            <p className="workspace-kicker"><span className="online-dot" /> YOUR READING ROOM</p>
            <p className="workspace-welcome">Welcome back, {user.name || 'reader'}</p>
          </div>
          <div className="workspace-date">A little more story, at your pace.</div>
        </header>

        <div className="workspace-content">
          {status && <p className="workspace-status" role="status">{status}</p>}

          <section className="book-heading">
            <div>
              <p className="eyebrow">NOW READING</p>
              <h1>{selectedBook?.title || 'Your next chapter starts here'}</h1>
              <p className="book-heading-caption">
                {selectedBook
                  ? 'Settle in. Your place is saved as you read.'
                  : 'Choose a book from your library or add a new one to begin.'}
              </p>
            </div>
            <button
              type="button"
              className={selectedBook?.reading_status === 'read' ? 'reading-status-btn marked-read' : 'reading-status-btn'}
              disabled={!selectedBook}
              onClick={handleReadingStatusToggle}
            >
              <span aria-hidden="true">{selectedBook?.reading_status === 'read' ? '✓' : '○'}</span>
              {selectedBook?.reading_status === 'read' ? 'Move to to-read' : 'Mark as finished'}
            </button>
          </section>

          <div className="reader-layout">
            <section className="reading-column" aria-label="Book reader">
              <div className="reader-card">
                <div className="reader-card-header">
                  <div>
                    <p className="eyebrow">THE BOOK</p>
                    <h2>Reading view</h2>
                  </div>
                  <div className="bookmark-indicator">
                    <span className="bookmark-indicator-icon" aria-hidden="true">⌑</span>
                    <span>
                      <small>YOUR BOOKMARK</small>
                      <strong>Page {currentPosition.page}</strong>
                    </span>
                  </div>
                </div>

                <div className="reader-controls">
                  <div className="reader-tools">
                    <button
                      type="button"
                      className="icon-button"
                      aria-label="Previous page"
                      disabled={!selectedBookId || currentPosition.page <= 1}
                      onClick={() => moveReaderPosition(0, -1)}
                    >
                      ←
                    </button>
                    <button
                      type="button"
                      className="icon-button"
                      aria-label="Next page"
                      disabled={!selectedBookId}
                      onClick={() => moveReaderPosition(0, 1)}
                    >
                      →
                    </button>
                    <span className="reader-control-divider" />
                    <button
                      type="button"
                      className="chapter-button"
                      disabled={!selectedBookId}
                      onClick={() => moveReaderPosition(1, 0)}
                    >
                      Next chapter <span aria-hidden="true">→</span>
                    </button>
                  </div>
                  <div className="position-inputs">
                    <label>
                      <span>CHAPTER</span>
                      <input
                        type="number"
                        min="1"
                        value={currentPosition.chapter_order}
                        disabled={!selectedBookId}
                        onChange={(e) => {
                          const next = { ...currentPosition, chapter_order: Math.max(Number(e.target.value || 1), 1) }
                          setCurrentPosition(next)
                          saveProgress(next)
                        }}
                      />
                    </label>
                    <label>
                      <span>PAGE</span>
                      <input
                        type="number"
                        min="1"
                        value={currentPosition.page}
                        disabled={!selectedBookId}
                        onChange={(e) => {
                          const next = { ...currentPosition, page: Math.max(Number(e.target.value || 1), 1) }
                          setCurrentPosition(next)
                          saveProgress(next)
                        }}
                      />
                    </label>
                    <button
                      type="button"
                      className="bookmark-button"
                      disabled={!selectedBookId}
                      onClick={handleProgressSave}
                    >
                      Save bookmark
                    </button>
                  </div>
                </div>

                {selectedBookId ? (
                  <div className="pdf-reader-shell">
                    <iframe
                      title={`Reading ${selectedBook?.title || 'book'}`}
                      src={pdfUrl}
                      className="pdf-frame"
                      loading="lazy"
                    />
                    <div className="reader-meta">
                      <span>Use the page controls to update your bookmark.</span>
                      <span>Chapter {currentPosition.chapter_order} · Page {currentPosition.page}</span>
                    </div>
                  </div>
                ) : (
                  <div className="pdf-placeholder">
                    <span className="placeholder-book" aria-hidden="true">
                      <BrandLockup compact />
                    </span>
                    <h3>A good book is waiting</h3>
                    <p>Select a title from your library or add a PDF to open your reading space.</p>
                  </div>
                )}
              </div>
            </section>

            <aside className="companion-column">
              <section className="summary-panel">
                <div className="panel-heading">
                  <span className="panel-number">01</span>
                  <div>
                    <p className="eyebrow">CATCH UP</p>
                    <h2>Summary so far</h2>
                  </div>
                </div>
                <p className={summary ? 'summary-content has-summary' : 'summary-content'}>
                  {summary || 'A gentle recap of everything up to your current page.'}
                </p>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={handleGenerateSummary}
                  disabled={!selectedBookId || summaryLoading}
                >
                  {summaryLoading ? 'Putting it together…' : 'Generate summary'}
                  {!summaryLoading && <span aria-hidden="true">→</span>}
                </button>
                <p className="summary-footnote">Future plot details stay out of this recap.</p>
              </section>

              <section className="chat-panel">
                <div className="chat-heading">
                  <div className="assistant-title-mark" aria-hidden="true">S</div>
                  <div>
                    <h2>Reading companion</h2>
                    <p>Curious about something?</p>
                  </div>
                </div>
                <label className={allowFuture ? 'spoiler-toggle enabled' : 'spoiler-toggle'}>
                  <input
                    type="checkbox"
                    checked={allowFuture}
                    onChange={(event) => setAllowFuture(event.target.checked)}
                  />
                  <span className="toggle-track" aria-hidden="true"><span /></span>
                  <span className="spoiler-toggle-copy">
                    <strong>Allow future spoilers</strong>
                    <small>{allowFuture ? 'Future plot details may appear.' : 'Your answers stay spoiler-safe.'}</small>
                  </span>
                </label>
                <div className="chat-box" aria-live="polite">
                  {messages.length ? (
                    messages.map((message, index) => (
                      <div key={`${message.role}-${index}`} className={`message ${message.role}`}>
                        <strong>{message.role === 'assistant' ? 'StoryShield' : 'You'}</strong>
                        <span>{message.text}</span>
                      </div>
                    ))
                  ) : (
                    <div className="assistant-empty">
                      <span aria-hidden="true">“</span>
                      <p>Ask me about a character, a detail, or what you’ve read so far.</p>
                    </div>
                  )}
                </div>
                <form
                  className="chat-input-row"
                  onSubmit={(event) => {
                    event.preventDefault()
                    handleAskQuestion()
                  }}
                >
                  <input
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="Ask your question…"
                    aria-label="Ask the reading companion"
                    disabled={!selectedBookId || asking}
                  />
                  <button type="submit" disabled={!selectedBookId || !question.trim() || asking} aria-label="Send question">
                    <span aria-hidden="true">{asking ? '…' : '↑'}</span>
                  </button>
                </form>
              </section>
            </aside>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
