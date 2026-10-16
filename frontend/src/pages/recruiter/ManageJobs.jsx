import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import client from '../../api/client'

export default function ManageJobs() {
  const [jobs, setJobs] = useState([])
  const [applicantsByJob, setApplicantsByJob] = useState({})
  const [rankings, setRankings] = useState({})
  const [expanded, setExpanded] = useState(null)

  const load = () => client.get('/recruiter/jobs').then((r) => setJobs(r.data))
  useEffect(() => { load() }, [])

  const toggle = async (jobId) => {
    if (expanded === jobId) { setExpanded(null); return }
    setExpanded(jobId)
    const [apps, ranked] = await Promise.all([
      client.get(`/recruiter/jobs/${jobId}/applicants`),
      client.get(`/recruiter/jobs/${jobId}/rank-candidates`),
    ])
    setApplicantsByJob((s) => ({ ...s, [jobId]: apps.data }))
    setRankings((s) => ({ ...s, [jobId]: ranked.data }))
  }

  const updateStatus = async (jobId, appId, status) => {
    await client.put(`/recruiter/applications/${appId}/status`, null, { params: { status } })
    const apps = await client.get(`/recruiter/jobs/${jobId}/applicants`)
    setApplicantsByJob((s) => ({ ...s, [jobId]: apps.data }))
  }

  const setJobStatus = async (jobId, status) => {
    await client.put(`/recruiter/jobs/${jobId}/status`, null, { params: { status } })
    load()
  }

  return (
    <div>
      <div className="page-header">
        <h1>Manage Jobs</h1>
        <p><Link to="/recruiter/post">+ Post a new job</Link></p>
      </div>

      {jobs.map((job) => (
        <div className="card" key={job.id}>
          <div className="flex-between">
            <div>
              <h3>{job.title} {job.is_flagged_scam && <span className="badge badge-danger">Under review</span>}</h3>
              <div className="job-meta">{job.company} · {job.location} · Quality {job.quality_score}/100</div>
            </div>
            <div className="flex-gap">
              <select value={job.status} onChange={(e) => setJobStatus(job.id, e.target.value)}>
                <option value="active">Active</option>
                <option value="closed">Closed</option>
                <option value="under_review">Under review</option>
              </select>
              <button className="btn btn-outline btn-sm" onClick={() => toggle(job.id)}>
                {expanded === job.id ? 'Hide applicants' : 'View applicants'}
              </button>
            </div>
          </div>

          {expanded === job.id && (
            <div className="mt-16">
              <div className="section-title">AI-Ranked Candidates</div>
              {(rankings[job.id] || []).length === 0 && <p className="muted">No applicants yet.</p>}
              <table>
                <thead><tr><th>Candidate</th><th>Match</th><th>Matched skills</th><th>Status</th><th>Action</th></tr></thead>
                <tbody>
                  {(rankings[job.id] || []).map((c) => (
                    <tr key={c.application_id}>
                      <td>{c.applicant_name}</td>
                      <td><span className="badge badge-teal">{c.match_score}%</span></td>
                      <td>{(c.matched_skills || []).slice(0, 4).join(', ') || '—'}</td>
                      <td>{c.current_status}</td>
                      <td>
                        <select defaultValue={c.current_status} onChange={(e) => updateStatus(job.id, c.application_id, e.target.value)}>
                          <option value="applied">Applied</option>
                          <option value="shortlisted">Shortlisted</option>
                          <option value="interview">Interview</option>
                          <option value="selected">Selected</option>
                          <option value="rejected">Rejected</option>
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ))}
      {jobs.length === 0 && <div className="card empty-state">No jobs posted yet.</div>}
    </div>
  )
}
