import { useEffect, useState } from 'react'
import client from '../../api/client'
import ScoreRing from '../../components/ScoreRing'

export default function ResumeCenter() {
  const [tab, setTab] = useState('upload')
  const [resumes, setResumes] = useState([])
  const [active, setActive] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')

  const load = async () => {
    const res = await client.get('/resumes')
    setResumes(res.data)
    if (res.data.length && !active) setActive(res.data[0])
  }

  useEffect(() => { load() }, [])

  const onUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setUploading(true)
    setError('')
    const fd = new FormData()
    fd.append('file', file)
    try {
      const res = await client.post('/resumes/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      setActive(res.data)
      await load()
    } catch (err) {
      setError(err?.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Resume Center</h1>
        <p>Upload an existing resume or build a new one — then get instant AI scoring and suggestions.</p>
      </div>

      <div className="pill-nav">
        <a className={tab === 'upload' ? 'active' : ''} onClick={() => setTab('upload')}>Upload Resume</a>
        <a className={tab === 'build' ? 'active' : ''} onClick={() => setTab('build')}>Build Resume</a>
        <a className={tab === 'history' ? 'active' : ''} onClick={() => setTab('history')}>My Resumes ({resumes.length})</a>
      </div>

      {tab === 'upload' && (
        <div className="card">
          <div className="section-title">Upload your resume</div>
          <p>Supported formats: PDF, DOCX, or TXT.</p>
          <input type="file" accept=".pdf,.docx,.txt" onChange={onUpload} disabled={uploading} />
          {uploading && <p className="mt-8"><span className="spinner" style={{ borderTopColor: 'var(--primary)', borderColor: 'rgba(45,50,80,0.2)' }} /> Analyzing…</p>}
          {error && <div className="error-text">{error}</div>}
        </div>
      )}

      {tab === 'build' && <ResumeBuilder onCreated={(r) => { setActive(r); load(); setTab('analysis') }} />}

      {tab === 'history' && (
        <div className="grid grid-2">
          {resumes.map((r) => (
            <div key={r.id} className="card" style={{ cursor: 'pointer' }} onClick={() => { setActive(r); setTab('analysis') }}>
              <div className="flex-between">
                <strong>{r.filename || 'Untitled Resume'}</strong>
                <span className="badge badge-teal">{r.ats_score}</span>
              </div>
              <div className="muted">{new Date(r.created_at).toLocaleDateString()}</div>
            </div>
          ))}
          {resumes.length === 0 && <div className="card empty-state">No resumes yet.</div>}
        </div>
      )}

      {active && tab !== 'build' && (
        <div className="mt-24">
          <ResumeAnalysis resume={active} />
        </div>
      )}
    </div>
  )
}

function ResumeAnalysis({ resume }) {
  return (
    <div className="card">
      <div className="flex-between">
        <div>
          <div className="section-title">AI Resume Analysis — {resume.filename}</div>
          <p className="muted">{resume.structured?.email || 'No email detected'} · {resume.structured?.phone || 'No phone detected'}</p>
        </div>
        <ScoreRing score={resume.ats_score} label="ATS Score" />
      </div>

      <div className="grid grid-2 mt-24">
        <div>
          <div className="section-title" style={{ color: 'var(--danger)' }}>Issues Found</div>
          <ul style={{ paddingLeft: 18 }}>
            {resume.mistakes.map((m, i) => <li key={i} style={{ marginBottom: 6, fontSize: 13.5 }}>{m}</li>)}
          </ul>
        </div>
        <div>
          <div className="section-title" style={{ color: 'var(--teal)' }}>Suggestions to Improve</div>
          <ul style={{ paddingLeft: 18 }}>
            {resume.suggestions.map((s, i) => <li key={i} style={{ marginBottom: 6, fontSize: 13.5 }}>{s}</li>)}
          </ul>
        </div>
      </div>

      <div className="mt-16">
        <div className="section-title">Detected Skills</div>
        {(resume.structured?.skills || []).map((s) => <span className="tag matched" key={s}>{s}</span>)}
        {(!resume.structured?.skills || resume.structured.skills.length === 0) && <p>No skills detected — add a Skills section.</p>}
      </div>
    </div>
  )
}

function ResumeBuilder({ onCreated }) {
  const [form, setForm] = useState({
    full_name: '', email: '', phone: '', summary: '', skills: '',
    exp_title: '', exp_company: '', exp_dates: '', exp_description: '',
    edu_degree: '', edu_school: '', edu_dates: '',
  })
  const [saving, setSaving] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    const payload = {
      full_name: form.full_name, email: form.email, phone: form.phone, summary: form.summary,
      skills: form.skills.split(',').map((s) => s.trim()).filter(Boolean),
      experience: form.exp_title ? [{ title: form.exp_title, company: form.exp_company, dates: form.exp_dates, description: form.exp_description }] : [],
      education: form.edu_degree ? [{ degree: form.edu_degree, school: form.edu_school, dates: form.edu_dates }] : [],
      projects: [], certifications: [],
    }
    try {
      const res = await client.post('/resumes/build', payload)
      onCreated(res.data)
    } finally {
      setSaving(false)
    }
  }

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  return (
    <form className="card" onSubmit={submit}>
      <div className="section-title">Build your resume</div>
      <div className="grid grid-2">
        <div className="field"><label>Full name</label><input value={form.full_name} onChange={set('full_name')} required /></div>
        <div className="field"><label>Email</label><input value={form.email} onChange={set('email')} /></div>
        <div className="field"><label>Phone</label><input value={form.phone} onChange={set('phone')} /></div>
        <div className="field"><label>Skills (comma-separated)</label><input value={form.skills} onChange={set('skills')} placeholder="python, sql, react" /></div>
      </div>
      <div className="field"><label>Professional summary</label><textarea rows={3} value={form.summary} onChange={set('summary')} /></div>

      <div className="section-title mt-16">Most recent experience</div>
      <div className="grid grid-2">
        <div className="field"><label>Job title</label><input value={form.exp_title} onChange={set('exp_title')} /></div>
        <div className="field"><label>Company</label><input value={form.exp_company} onChange={set('exp_company')} /></div>
        <div className="field"><label>Dates</label><input value={form.exp_dates} onChange={set('exp_dates')} placeholder="2022 - Present" /></div>
      </div>
      <div className="field"><label>Description (achievements, quantify where possible)</label><textarea rows={3} value={form.exp_description} onChange={set('exp_description')} /></div>

      <div className="section-title mt-16">Education</div>
      <div className="grid grid-3">
        <div className="field"><label>Degree</label><input value={form.edu_degree} onChange={set('edu_degree')} /></div>
        <div className="field"><label>School</label><input value={form.edu_school} onChange={set('edu_school')} /></div>
        <div className="field"><label>Dates</label><input value={form.edu_dates} onChange={set('edu_dates')} /></div>
      </div>

      <button className="btn btn-primary mt-16" disabled={saving}>{saving ? 'Saving…' : 'Generate Resume & Analyze'}</button>
    </form>
  )
}
