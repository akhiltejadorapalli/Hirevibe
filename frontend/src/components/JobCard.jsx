import { Link } from 'react-router-dom'

export default function JobCard({ job, matchScore, onSave, saved, extra }) {
  return (
    <div className="card job-card">
      <div style={{ flex: 1 }}>
        <div className="flex-gap" style={{ marginBottom: 4 }}>
          <h3>{job.title}</h3>
          {job.is_flagged_scam && <span className="badge badge-danger">⚠ Flagged</span>}
          {typeof matchScore === 'number' && (
            <span className={`badge ${matchScore >= 70 ? 'badge-teal' : matchScore >= 40 ? 'badge-warn' : 'badge-danger'}`}>
              {matchScore}% match
            </span>
          )}
        </div>
        <div className="job-meta">{job.company} · {job.location} · {job.employment_type}</div>
        <p style={{ fontSize: 13.5 }}>{job.description?.slice(0, 160)}{job.description?.length > 160 ? '…' : ''}</p>
        <div>
          {(job.skills_required || []).slice(0, 6).map((s) => <span className="tag" key={s}>{s}</span>)}
        </div>
        {extra}
      </div>
      <div className="job-card-actions">
        {onSave && (
          <button className="btn btn-outline btn-sm" onClick={() => onSave(job)}>
            {saved ? '★ Saved' : '☆ Save'}
          </button>
        )}
        <Link to={`/jobs/${job.id}`} className="btn btn-primary btn-sm">View</Link>
      </div>
    </div>
  )
}
