import { useEffect, useMemo, useState } from 'react'
import {
  Bell,
  BriefcaseBusiness,
  CheckCircle2,
  FileText,
  LayoutDashboard,
  MessageSquareText,
  MoonStar,
  Search,
  Settings,
  Sparkles,
  SunMedium,
} from 'lucide-react'
import { Link, NavLink, Route, Routes } from 'react-router-dom'
import DocumentsPage from './pages/DocumentsPage.jsx'
import InterviewPage from './pages/InterviewPage.jsx'
import JobMatcherPage from './pages/JobMatcher.jsx'

const navItems = [
  { label: 'Overview', icon: LayoutDashboard, path: '/' },
  { label: 'Career Blueprint', icon: BriefcaseBusiness, path: '/jobs' },
  { label: 'Skills', icon: Sparkles, path: '/settings' },
  { label: 'Documents', icon: FileText, path: '/documents' },
  { label: 'Interview Coach', icon: MessageSquareText, path: '/interview' },
  { label: 'Settings', icon: Settings, path: '/settings' },
]

const statCards = [
  { label: 'Profile score', value: '87%', detail: '+8% this month', tone: 'teal' },
  { label: 'Role matches', value: '14', detail: '3 high-fit matches', tone: 'violet' },
  { label: 'Application streak', value: '6 days', detail: 'Consistent momentum', tone: 'amber' },
]

const focusAreas = [
  { name: 'Product Analytics', progress: 82, status: 'Strong fit' },
  { name: 'Data Storytelling', progress: 74, status: 'Improving' },
  { name: 'AI Product Thinking', progress: 68, status: 'Growing' },
]

const tasks = [
  'Polish resume summary around measurable impact',
  'Refresh LinkedIn headline for PM/Analytics roles',
  'Add a case study for the AI workflow project',
]

const opportunities = [
  { title: 'Senior Product Analyst', company: 'Northstar Labs', fit: '92%', type: 'Remote' },
  { title: 'Growth Data Manager', company: 'Signal Harbor', fit: '88%', type: 'Hybrid' },
  { title: 'AI Product Specialist', company: 'Elevate Studio', fit: '84%', type: 'On-site' },
]

const backendUrl = 'http://localhost:8000'

function PlaceholderPage({ title, description }) {
  return (
    <section className="panel" style={{ marginTop: 18 }}>
      <div className="panel-header">
        <h3>{title}</h3>
      </div>
      <p className="helper-text">{description}</p>
    </section>
  )
}

function DashboardPage() {
  const [theme, setTheme] = useState('dark')
  const [healthStatus, setHealthStatus] = useState('Checking backend...')
  const [question, setQuestion] = useState('How can I position my analytics background for a product role?')
  const [reply, setReply] = useState('')
  const [chatSources, setChatSources] = useState([])
  const [isSending, setIsSending] = useState(false)
  const [uploadStatus, setUploadStatus] = useState('')
  const [isUploading, setIsUploading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('career planning and job matching')
  const [searchResults, setSearchResults] = useState([])
  const [isSearching, setIsSearching] = useState(false)
  const [resumeText, setResumeText] = useState(
    'Python, SQL, analytics, dashboards, stakeholder communication, project planning, experimentation',
  )
  const [matchResults, setMatchResults] = useState([])
  const [isMatching, setIsMatching] = useState(false)

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(`${backendUrl}/api/health`)
        if (!response.ok) {
          throw new Error('Backend unavailable')
        }
        const data = await response.json()
        setHealthStatus(`${data.service} • ${data.status}`)
      } catch (error) {
        setHealthStatus('Backend offline')
      }
    }

    checkHealth()
  }, [])

  const handleAsk = async () => {
    if (!question.trim()) return

    setIsSending(true)
    setReply('')

    try {
      const response = await fetch(`${backendUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: question }),
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Chat request failed')
      }

      setReply(data.reply || 'No reply returned.')
      setChatSources(data.sources || [])
    } catch (error) {
      setReply(error.message || 'The assistant is currently unavailable. Please make sure the backend is running on port 8000.')
      setChatSources([])
    } finally {
      setIsSending(false)
    }
  }

  const handleUpload = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)
    setIsUploading(true)
    setUploadStatus('Uploading document...')

    try {
      const response = await fetch(`${backendUrl}/api/documents/upload`, {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Upload failed')
      }

      setUploadStatus(`Uploaded ${data.filename} • ${data.chunks} chunks indexed`)
    } catch (error) {
      setUploadStatus(error.message || 'Could not upload the file.')
    } finally {
      setIsUploading(false)
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) return

    setIsSearching(true)
    setSearchResults([])

    try {
      const response = await fetch(`${backendUrl}/api/documents/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery }),
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Search failed')
      }

      setSearchResults(data.results || [])
    } catch (error) {
      setSearchResults([])
      setUploadStatus(error.message || 'Search failed.')
    } finally {
      setIsSearching(false)
    }
  }

  const handleCareerMatch = async () => {
    if (!resumeText.trim()) return

    setIsMatching(true)
    setMatchResults([])

    const jobs = [
      { title: 'Senior Product Analyst', requirements: 'SQL analytics dashboards product metrics stakeholder communication' },
      { title: 'Data Storytelling Lead', requirements: 'Python SQL data visualization reporting communication strategy' },
      { title: 'AI Product Specialist', requirements: 'AI product strategy stakeholder communication experimentation roadmaps' },
    ]

    try {
      const response = await fetch(`${backendUrl}/api/career/match`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resume_text: resumeText, jobs }),
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Match failed')
      }

      setMatchResults(data.matches || [])
    } catch (error) {
      setMatchResults([])
      setUploadStatus(error.message || 'Career match failed.')
    } finally {
      setIsMatching(false)
    }
  }

  const themeLabel = useMemo(() => (theme === 'dark' ? 'Light mode' : 'Dark mode'), [theme])

  return (
    <div className={`app-shell ${theme}`}>
      <aside className="sidebar">
        <div className="brand-block">
          <div className="brand-mark">CP</div>
          <div>
            <div className="eyebrow">CareerPilot</div>
            <h2>AI Workspace</h2>
          </div>
        </div>

        <nav className="nav">
          {navItems.map(({ label, icon: Icon, path }) => (
            <NavLink key={label} to={path} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <Icon size={18} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="upgrade-card">
          <p className="eyebrow">Next upgrade</p>
          <h3>Interview rehearsal</h3>
          <p>Unlock mock Q&A and role-specific coaching for your top matches.</p>
          <button type="button">Preview</button>
        </div>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div className="search-box">
            <Search size={16} />
            <input type="text" value="Search roles, skills, resources" readOnly />
          </div>

          <div className="header-actions">
            <button type="button" className="icon-button" aria-label="Notifications">
              <Bell size={18} />
            </button>
            <button
              type="button"
              className="icon-button"
              aria-label={themeLabel}
              onClick={() => setTheme((current) => (current === 'dark' ? 'light' : 'dark'))}
            >
              {theme === 'dark' ? <SunMedium size={18} /> : <MoonStar size={18} />}
            </button>
            <div className="user-badge">
              <span>AR</span>
            </div>
          </div>
        </header>

        <section className="hero-card">
          <div>
            <p className="eyebrow accent">Career momentum</p>
            <h1>Build the next step in your professional story.</h1>
            <p className="hero-copy">
              Your roadmap is balanced toward product, analytics, and AI-driven roles that match your skills and experience.
            </p>
            <div className="hero-actions">
              <button type="button" className="primary-btn">Review strategy</button>
              <button type="button" className="secondary-btn">Explore roles</button>
            </div>
          </div>

          <div className="hero-panel">
            <div className="mini-card blue">
              <span>Strongest fit</span>
              <strong>Product Analyst</strong>
              <small>92% alignment</small>
            </div>
            <div className="mini-card">
              <span>Recommended focus</span>
              <strong>AI storytelling</strong>
              <small>3 portfolio gaps</small>
            </div>
          </div>
        </section>

        <section className="stats-grid">
          {statCards.map(({ label, value, detail, tone }) => (
            <article key={label} className={`stat-card ${tone}`}>
              <span>{label}</span>
              <strong>{value}</strong>
              <small>{detail}</small>
            </article>
          ))}
        </section>

        <section className="content-grid">
          <div className="panel">
            <div className="panel-header">
              <h3>Skill readiness</h3>
              <button type="button">View all</button>
            </div>

            <div className="progress-list">
              {focusAreas.map(({ name, progress, status }) => (
                <div key={name} className="progress-item">
                  <div className="meta-line">
                    <span>{name}</span>
                    <span>{status}</span>
                  </div>
                  <div className="progress-bar">
                    <span style={{ width: `${progress}%` }} />
                  </div>
                  <small>{progress}%</small>
                </div>
              ))}
            </div>
          </div>

          <div className="panel">
            <div className="panel-header">
              <h3>Action checklist</h3>
              <button type="button">Open plan</button>
            </div>

            <ul className="task-list">
              {tasks.map((task) => (
                <li key={task}>
                  <CheckCircle2 size={18} />
                  <span>{task}</span>
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section className="panel live-panel">
          <div className="panel-header">
            <h3>Career assistant</h3>
            <span className={`status-pill ${healthStatus === 'Backend offline' ? 'offline' : 'online'}`}>
              {healthStatus}
            </span>
          </div>

          <div className="chat-box">
            <textarea
              aria-label="Career question"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              rows={4}
            />
            <div className="chat-actions">
              <button type="button" className="primary-btn" onClick={handleAsk} disabled={isSending}>
                {isSending ? 'Thinking...' : 'Ask assistant'}
              </button>
            </div>
          </div>

          {reply && (
            <div className="assistant-response">
              <strong>AI response</strong>
              <p>{reply}</p>
              {chatSources.length > 0 && (
                <div className="source-list" style={{ marginTop: 12 }}>
                  <strong>Sources</strong>
                  <ul>
                    {chatSources.map((source, index) => (
                      <li key={`${source.source}-${source.page ?? index}`}>
                        {source.source} {source.page ? `• Page ${source.page}` : ''}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </section>

        <section className="panel doc-panel">
          <div className="panel-header">
            <h3>Document intelligence</h3>
          </div>

          <div className="document-upload-box">
            <label className="uploader">
              <span>Upload PDF</span>
              <input type="file" accept="application/pdf" onChange={handleUpload} />
            </label>
            {uploadStatus && <p className="helper-text">{uploadStatus}</p>}
            {isUploading && <p className="helper-text">Processing document...</p>}
          </div>

          <div className="document-search-box">
            <input
              type="text"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Search uploaded documents..."
            />
            <button type="button" className="secondary-btn" onClick={handleSearch} disabled={isSearching}>
              {isSearching ? 'Searching...' : 'Search'}
            </button>
          </div>

          <div className="search-results">
            {searchResults.length > 0 ? (
              searchResults.map((result, index) => (
                <article key={`${result.metadata?.chunk_id || index}`} className="result-item">
                  <p>{result.page_content}</p>
                  <small>
                    Page {result.metadata?.page ?? 'n/a'} • {result.metadata?.source ?? 'unknown'}
                  </small>
                </article>
              ))
            ) : (
              <p className="helper-text">Search the indexed document store for the most relevant chunks.</p>
            )}
          </div>
        </section>

        <section className="panel match-panel">
          <div className="panel-header">
            <h3>Career fit matcher</h3>
          </div>

          <div className="match-box">
            <textarea
              aria-label="Resume summary"
              value={resumeText}
              onChange={(event) => setResumeText(event.target.value)}
              rows={4}
            />
            <button type="button" className="primary-btn" onClick={handleCareerMatch} disabled={isMatching}>
              {isMatching ? 'Scoring roles...' : 'Match roles'}
            </button>
          </div>

          <div className="search-results">
            {matchResults.length > 0 ? (
              matchResults.map((result, index) => (
                <article key={`${result.title || index}`} className="result-item">
                  <div className="result-header">
                    <h4>{result.title}</h4>
                    <span className="fit-pill">{Number(result.score ?? 0).toFixed(1)}%</span>
                  </div>
                  <p>{result.matched_skills?.join(', ') || 'Relevant skills identified.'}</p>
                  <small>{result.match_count ?? 0} matched skills</small>
                </article>
              ))
            ) : (
              <p className="helper-text">Compare your resume against sample roles to see your strongest matches.</p>
            )}
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <h3>High-fit opportunities</h3>
            <button type="button">See all</button>
          </div>

          <div className="opportunity-list">
            {opportunities.map(({ title, company, fit, type }) => (
              <article key={title} className="opportunity-item">
                <div>
                  <h4>{title}</h4>
                  <p>{company}</p>
                </div>
                <div className="opportunity-meta">
                  <span className="fit-pill">{fit}</span>
                  <span>{type}</span>
                </div>
              </article>
            ))}
          </div>
        </section>
      </main>
    </div>
  )
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<DashboardPage />} />
      <Route path="/dashboard" element={<DashboardPage />} />
      <Route path="/documents" element={<DocumentsPage />} />
      <Route path="/chat" element={<PlaceholderPage title="Chat" description="Chat is not implemented in Phase 2." />} />
      <Route path="/jobs" element={<JobMatcherPage />} />
      <Route path="/interview" element={<InterviewPage />} />
      <Route path="/settings" element={<PlaceholderPage title="Settings" description="This route remains available for future phases." />} />
    </Routes>
  )
}

export default App
