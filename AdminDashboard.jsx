import { useEffect, useState } from 'react'
import client from '../../api/client'

export default function AdminDashboard() {
  const [stats, setStats] = useState(null)
  useEffect(() => { client.get('/admin/analytics').then((r) => setStats(r.data)) }, [])

  return (
    <div>
      <div className="page-header"><h1>Platform Analytics</h1><p>System-wide overview for administrators.</p></div>
      <div className="grid grid-4">
        <div className="card"><div className="stat-num">{stats?.total_users ?? '—'}</div><div className="stat-label">Total users</div></div>
        <div className="card"><div className="stat-num">{stats?.job_seekers ?? '—'}</div><div className="stat-label">Job seekers</div></div>
        <div className="card"><div className="stat-num">{stats?.recruiters ?? '—'}</div><div className="stat-label">Recruiters</div></div>
        <div className="card"><div className="stat-num">{stats?.total_jobs ?? '—'}</div><div className="stat-label">Total jobs</div></div>
        <div className="card"><div className="stat-num" style={{ color: 'var(--danger)' }}>{stats?.flagged_jobs ?? '—'}</div><div className="stat-label">Flagged / fake jobs</div></div>
        <div className="card"><div className="stat-num">{stats?.total_applications ?? '—'}</div><div className="stat-label">Applications</div></div>
        <div className="card"><div className="stat-num">{stats?.open_reports ?? '—'}</div><div className="stat-label">Open reports</div></div>
      </div>
    </div>
  )
}
