import { useEffect, useState } from 'react'
import client from '../../api/client'

export default function JobsReports() {
  const [jobs, setJobs] = useState([])
  const [flaggedOnly, setFlaggedOnly] = useState(false)
  const [reports, setReports] = useState([])

  const loadJobs = () => client.get('/admin/jobs', { params: { flagged_only: flaggedOnly } }).then((r) => setJobs(r.data))
  const loadReports = () => client.get('/admin/reports').then((r) => setReports(r.data))

  useEffect(() => { loadJobs() }, [flaggedOnly])
  useEffect(() => { loadReports() }, [])

  const setStatus = async (id, status) => { await client.put(`/admin/jobs/${id}/status`, null, { params: { status } }); loadJobs() }
  const resolveReport = async (id, status) => { await client.put(`/admin/reports/${id}`, null, { params: { status } }); loadReports() }

  return (
    <div>
      <div className="page-header"><h1>Jobs & Reports</h1><p>Review flagged listings and user-submitted reports.</p></div>

      <div className="flex-between">
        <div className="section-title">Job Listings</div>
        <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 500 }}>
          <input type="checkbox" style={{ width: 'auto' }} checked={flaggedOnly} onChange={(e) => setFlaggedOnly(e.target.checked)} /> Flagged only
        </label>
      </div>
      <div className="card">
        <table>
          <thead><tr><th>Title</th><th>Company</th><th>Status</th><th>Flagged</th><th>Quality</th><th>Action</th></tr></thead>
          <tbody>
            {jobs.map((j) => (
              <tr key={j.id}>
                <td>{j.title}</td>
                <td>{j.company || '—'}</td>
                <td>{j.status}</td>
                <td>{j.is_flagged_scam ? <span className="badge badge-danger">Yes</span> : <span className="badge badge-teal">No</span>}</td>
                <td>{j.quality_score}</td>
                <td className="flex-gap">
                  <button className="btn btn-sm btn-outline" onClick={() => setStatus(j.id, 'active')}>Approve</button>
                  <button className="btn btn-sm btn-danger" onClick={() => setStatus(j.id, 'closed')}>Close</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="section-title mt-24">User Reports</div>
      <div className="card">
        {reports.length === 0 && <p className="muted">No reports filed.</p>}
        {reports.map((r) => (
          <div key={r.id} style={{ padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
            <div className="flex-between">
              <strong>{r.target_type} #{r.target_id} — {r.status}</strong>
              <div className="flex-gap">
                <button className="btn btn-sm btn-outline" onClick={() => resolveReport(r.id, 'resolved')}>Resolve</button>
                <button className="btn btn-sm btn-ghost" onClick={() => resolveReport(r.id, 'dismissed')}>Dismiss</button>
              </div>
            </div>
            <p style={{ marginTop: 4 }}>{r.reason}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
