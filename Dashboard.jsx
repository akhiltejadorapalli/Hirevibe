import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import client from '../../api/client'
import ScoreRing from '../../components/ScoreRing'
import JobCard from '../../components/JobCard'
import { useAuth } from '../../context/AuthContext'

export default function Dashboard() {
  const { user } = useAuth()
  const [readiness, setReadiness] = useState(null)
  const [recommended, setRecommended] = useState([])
  const [notifications, setNotifications] = useState([])
  const [hasResume, setHasResume] = useState(true)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    (async () => {
      try {
        const r = await client.get('/readiness-score')
        setReadiness(r.data)
        setHasResume(r.data.ats_score > 0)
      } catch { /* noop */ }
      try {
        const j = await client.get('/jobs-recommended')
        setRecommended(j.data.slice(0, 4))
      } catch { /* noop */ }
      try {
        const n = await client.get('/notifications')
        setNotifications(n.data.slice(0, 5))
      } catch { /* noop */ }
      setLoading(false)
    })()
  }, [])

  return (
    <div>
      <div className="page-header">
        <h1>Welcome back, {user.name.split(' ')[0]} 👋</h1>
        <p>Here's where your job search stands today.</p>
      </div>

      {!loading && !hasResume && (
        <div className="card" style={{ background: 'var(--warn-light)', border: 'none', marginBottom: 16 }}>
          <div className="flex-between">
            <div>
              <strong>Add a resume to unlock AI matching, scoring, and recommendations.</strong>
              <p style={{ marginTop: 4 }}>Upload an existing resume or build one from scratch in the Resume Center.</p>
            </div>
            <Link to="/resumes" className="btn btn-accent">Go to Resume Center</Link>
          </div>
        </div>
      )}

      <div className="grid grid-3">
        <div className="card" style={{ textAlign: 'center' }}>
          <div className="section-title">Job Readiness Score</div>
          <div className="flex" style={{ justifyContent: 'center', marginTop: 8 }}>
            <ScoreRing score={readiness?.readiness_score || 0} />
          </div>
          <p className="mt-16">Combines resume quality, skill breadth, and application activity.</p>
        </div>
        <div className="card">
          <div className="section-title">Resume ATS Score</div>
          <div className="stat-num">{readiness?.ats_score ?? '—'}</div>
          <div className="stat-label">out of 100</div>
          <p className="mt-16">{readiness?.num_skills ?? 0} skills detected on your latest resume.</p>
        </div>
        <div className="card">
          <div className="section-title">Applications</div>
          <div className="stat-num">{readiness?.applications ?? 0}</div>
          <div className="stat-label">total tracked</div>
          <p className="mt-16"><Link to="/tracker">View application tracker →</Link></p>
        </div>
      </div>

      <div className="grid grid-2 mt-24">
        <div>
          <div className="flex-between">
            <h2 style={{ fontSize: 18 }}>Recommended for you</h2>
            <Link to="/jobs" className="muted">See all jobs →</Link>
          </div>
          {recommended.length === 0 && (
            <div className="card empty-state">No recommendations yet — add a resume to get matched jobs.</div>
          )}
          {recommended.map((r) => (
            <JobCard key={r.job.id} job={r.job} matchScore={r.match_score} />
          ))}
        </div>
        <div>
          <h2 style={{ fontSize: 18 }}>Notifications</h2>
          <div className="card">
            {notifications.length === 0 && <p>No notifications yet.</p>}
            {notifications.map((n) => (
              <div key={n.id} style={{ padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                <div style={{ fontSize: 13.5 }}>{n.message}</div>
                <div className="muted">{new Date(n.created_at).toLocaleString()}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
