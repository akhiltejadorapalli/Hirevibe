import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '../../api/client'
import { useAuth } from '../../context/AuthContext'

export default function PostJob() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    title: '', company: user.company_name || '', location: 'Remote', category: 'Engineering',
    employment_type: 'Full-time', description: '', requirements: '', skills_required: '',
    salary_min: '', salary_max: '',
  })
  const [result, setResult] = useState(null)
  const [saving, setSaving] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      const payload = {
        ...form,
        skills_required: form.skills_required.split(',').map((s) => s.trim()).filter(Boolean),
        salary_min: form.salary_min ? Number(form.salary_min) : null,
        salary_max: form.salary_max ? Number(form.salary_max) : null,
      }
      const res = await client.post('/recruiter/jobs', payload)
      setResult(res.data)
      if (!res.data.is_flagged_scam) {
        setTimeout(() => navigate('/recruiter/jobs'), 1200)
      }
    } finally {
      setSaving(false)
    }
  }

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  return (
    <div>
      <div className="page-header"><h1>Post a Job</h1><p>Your listing runs through AI safety and quality checks automatically.</p></div>
      <form className="card" onSubmit={submit}>
        <div className="grid grid-2">
          <div className="field"><label>Job title</label><input value={form.title} onChange={set('title')} required /></div>
          <div className="field"><label>Company</label><input value={form.company} onChange={set('company')} required /></div>
          <div className="field"><label>Location</label><input value={form.location} onChange={set('location')} /></div>
          <div className="field"><label>Category</label><input value={form.category} onChange={set('category')} /></div>
          <div className="field"><label>Employment type</label>
            <select value={form.employment_type} onChange={set('employment_type')}>
              <option>Full-time</option><option>Part-time</option><option>Contract</option><option>Internship</option>
            </select>
          </div>
          <div className="field"><label>Skills required (comma-separated)</label><input value={form.skills_required} onChange={set('skills_required')} placeholder="python, sql, aws" /></div>
          <div className="field"><label>Salary min</label><input type="number" value={form.salary_min} onChange={set('salary_min')} /></div>
          <div className="field"><label>Salary max</label><input type="number" value={form.salary_max} onChange={set('salary_max')} /></div>
        </div>
        <div className="field"><label>Description</label><textarea rows={4} value={form.description} onChange={set('description')} required /></div>
        <div className="field"><label>Requirements</label><textarea rows={3} value={form.requirements} onChange={set('requirements')} /></div>
        <button className="btn btn-primary" disabled={saving}>{saving ? 'Publishing…' : 'Publish Job'}</button>
      </form>

      {result && (
        <div className="card mt-16" style={{ background: result.is_flagged_scam ? 'var(--danger-light)' : 'var(--teal-light)', border: 'none' }}>
          {result.is_flagged_scam ? (
            <>
              <strong style={{ color: 'var(--danger)' }}>This listing was flagged by AI Job Safety Analysis and sent for review:</strong>
              <ul>{result.scam_reasons.map((r, i) => <li key={i}>{r}</li>)}</ul>
            </>
          ) : (
            <strong style={{ color: 'var(--teal)' }}>Job published! Quality score: {result.quality_score}/100. Redirecting…</strong>
          )}
        </div>
      )}
    </div>
  )
}
