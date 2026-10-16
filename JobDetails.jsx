import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import client from '../../api/client'
import ScoreRing from '../../components/ScoreRing'

export default function JobDetails() {
  const { id } = useParams()
  const [job, setJob] = useState(null)
  const [match, setMatch] = useState(null)
  const [matchError, setMatchError] = useState('')
  const [applied, setApplied] = useState(false)
  const [coverLetter, setCoverLetter] = useState('')
  const [generating, setGenerating] = useState(false)

  useEffect(() => {
    client.get(`/jobs/${id}`).then((r) => setJob(r.data))
    client.get(`/jobs/${id}/match`).then((r) => setMatch(r.data)).catch((e) => setMatchError(e?.response?.data?.detail || ''))
  }, [id])

  const apply = async (withCoverLetter) => {
    await client.post('/applications', { job_id: Number(id), status: 'applied', cover_letter: withCoverLetter ? coverLetter : undefined })
    setApplied(true)
  }

  const genCoverLetter = async () => {
    setGenerating(true)
    try {
      const res = await client.post('/cover-letter', { job_id: Number(id) })
      setCoverLetter(res.data.cover_letter)
    } finally {
      setGenerating(false)
    }
  }

  if (!job) return <p>Loading…</p>

  return (
    <div>
      <div className="card">
        <div className="flex-between">
          <div>
            <h1 style={{ fontSize: 22 }}>{job.title}</h1>
            <p>{job.company} · {job.location} · {job.employment_type}</p>
          </div>
          {job.is_flagged_scam && <span className="badge badge-danger">⚠ Flagged as potential scam</span>}
        </div>

        {job.is_flagged_scam && (
          <div className="card" style={{ background: 'var(--danger-light)', border: 'none' }}>
            <strong style={{ color: 'var(--danger)' }}>AI Job Safety Analysis found concerns:</strong>
            <ul>{job.scam_reasons.map((r, i) => <li key={i} style={{ fontSize: 13.5 }}>{r}</li>)}</ul>
          </div>
        )}

        <div className="flex-gap mt-16">
          <span className="badge badge-muted">Quality score: {job.quality_score}/100</span>
          {job.salary_min && <span className="badge badge-teal">${job.salary_min.toLocaleString()} - ${job.salary_max?.toLocaleString()}</span>}
        </div>

        <div className="section-title mt-24">Description</div>
        <p style={{ whiteSpace: 'pre-wrap', color: 'var(--ink)' }}>{job.description}</p>

        <div className="section-title mt-16">Requirements</div>
        <p style={{ whiteSpace: 'pre-wrap', color: 'var(--ink)' }}>{job.requirements}</p>

        <div>{(job.skills_required || []).map((s) => <span className="tag" key={s}>{s}</span>)}</div>

        <div className="flex-gap mt-24">
          <button className="btn btn-primary" onClick={() => apply(false)} disabled={applied}>
            {applied ? 'Applied ✓' : 'Apply for Job'}
          </button>
          <button className="btn btn-outline" onClick={genCoverLetter} disabled={generating}>
            {generating ? 'Generating…' : 'Generate Cover Letter'}
          </button>
        </div>

        {coverLetter && (
          <div className="card mt-16" style={{ background: '#fafbff' }}>
            <div className="section-title">AI-Generated Cover Letter</div>
            <p style={{ whiteSpace: 'pre-wrap', color: 'var(--ink)' }}>{coverLetter}</p>
            <button className="btn btn-accent btn-sm mt-8" onClick={() => apply(true)} disabled={applied}>
              {applied ? 'Applied ✓' : 'Apply with this cover letter'}
            </button>
          </div>
        )}
      </div>

      {match && (
        <div className="card mt-16">
          <div className="flex-between">
            <div>
              <div className="section-title">AI Job Matching</div>
              <p>Based on your most recent resume.</p>
            </div>
            <ScoreRing score={match.match_score} label="Match" />
          </div>

          <div className="card" style={{ background: match.advice.verdict === 'improve_first' ? 'var(--warn-light)' : 'var(--teal-light)', border: 'none' }}>
            <strong>{match.advice.message}</strong>
          </div>

          <div className="grid grid-2 mt-16">
            <div>
              <div className="section-title" style={{ color: 'var(--teal)' }}>Matched Skills</div>
              {match.matched_skills.map((s) => <span className="tag matched" key={s}>{s}</span>)}
              {match.matched_skills.length === 0 && <p className="muted">None found yet.</p>}
            </div>
            <div>
              <div className="section-title" style={{ color: 'var(--danger)' }}>Missing Skills</div>
              {match.missing_skills.map((s) => <span className="tag missing" key={s}>{s}</span>)}
              {match.missing_skills.length === 0 && <p className="muted">None — great fit!</p>}
            </div>
          </div>

          {match.advice.roadmap.length > 0 && (
            <div className="mt-16">
              <div className="section-title">Skill Gap & Learning Roadmap</div>
              <table>
                <thead><tr><th>Skill</th><th>Resource</th><th>Est. time</th></tr></thead>
                <tbody>
                  {match.advice.roadmap.map((r) => (
                    <tr key={r.skill}><td>{r.skill}</td><td>{r.recommended_resource}</td><td>{r.estimated_time}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
      {matchError && <div className="card mt-16"><p>{matchError} — <a href="/resumes">Add a resume</a> to see your match score.</p></div>}
    </div>
  )
}
