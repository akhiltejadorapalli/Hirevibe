import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import client from '../../api/client'
import { useAuth } from '../../context/AuthContext'

export default function RecruiterDashboard() {
  const { user } = useAuth()
  const [stats, setStats] = useState(null)

  useEffect(() => { client.get('/recruiter/analytics').then((r) => setStats(r.data)) }, [])

  return (
    <div>
      <div className="page-header">
        <h1>Welcome, {user.name.split(' ')[0]}</h1>
        <p>{user.company_name} {user.company_verified ? <span className="badge badge-teal">Verified</span> : <span className="badge badge-warn">Pending verification</span>}</p>
      </div>

      <div className="grid grid-4">
        <div className="card"><div className="stat-num">{stats?.total_jobs ?? '—'}</div><div className="stat-label">Total jobs posted</div></div>
        <div className="card"><div className="stat-num">{stats?.active_jobs ?? '—'}</div><div className="stat-label">Active jobs</div></div>
        <div className="card"><div className="stat-num">{stats?.total_applicants ?? '—'}</div><div className="stat-label">Total applicants</div></div>
        <div className="card"><div className="stat-num">{stats?.applicants_by_status?.selected ?? 0}</div><div className="stat-label">Candidates selected</div></div>
      </div>

      <div className="card mt-24">
        <div className="flex-between">
          <h2 style={{ fontSize: 18 }}>Quick actions</h2>
        </div>
        <div className="flex-gap mt-8">
          <Link to="/recruiter/post" className="btn btn-primary">Post a New Job</Link>
          <Link to="/recruiter/jobs" className="btn btn-outline">Manage Jobs</Link>
        </div>
      </div>
    </div>
  )
}
