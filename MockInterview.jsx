import { useState } from 'react'
import client from '../../api/client'

export default function MockInterview() {
  const [role, setRole] = useState('Software Engineer')
  const [session, setSession] = useState(null)
  const [current, setCurrent] = useState(0)
  const [answer, setAnswer] = useState('')
  const [starting, setStarting] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const start = async () => {
    setStarting(true)
    try {
      const res = await client.post('/interview/start', { role, num_questions: 5 })
      setSession(res.data)
      setCurrent(0)
      setAnswer('')
    } finally {
      setStarting(false)
    }
  }

  const submitAnswer = async () => {
    setSubmitting(true)
    try {
      const res = await client.post('/interview/answer', { session_id: session.id, question_index: current, answer })
      setSession(res.data)
      setAnswer('')
      if (current < session.questions.length - 1) setCurrent(current + 1)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>AI Mock Interview</h1>
        <p>Practice role-specific questions and get instant feedback on your answers.</p>
      </div>

      {!session && (
        <div className="card">
          <div className="field">
            <label>Target role</label>
            <input value={role} onChange={(e) => setRole(e.target.value)} placeholder="e.g. Software Engineer, Data Analyst, Product Manager" />
          </div>
          <button className="btn btn-primary" onClick={start} disabled={starting}>{starting ? 'Preparing…' : 'Start Mock Interview'}</button>
        </div>
      )}

      {session && (
        <div className="card">
          <div className="flex-between">
            <div className="section-title">Question {current + 1} of {session.questions.length}</div>
            {session.overall_score > 0 && <span className="badge badge-teal">Overall: {session.overall_score}/100</span>}
          </div>
          <p style={{ fontSize: 16, color: 'var(--ink)', fontWeight: 600 }}>{session.questions[current]}</p>

          <textarea rows={5} placeholder="Type your answer…" value={answer} onChange={(e) => setAnswer(e.target.value)} />
          <button className="btn btn-primary mt-8" onClick={submitAnswer} disabled={submitting || !answer.trim()}>
            {submitting ? 'Scoring…' : 'Submit Answer'}
          </button>

          {session.feedback[current] && (
            <div className="card mt-16" style={{ background: 'var(--teal-light)', border: 'none' }}>
              <strong>Feedback — Score: {session.feedback[current].score}/100</strong>
              <ul>{session.feedback[current].tips.map((t, i) => <li key={i} style={{ fontSize: 13.5 }}>{t}</li>)}</ul>
            </div>
          )}

          <div className="flex-gap mt-16">
            {session.questions.map((_, i) => (
              <button key={i} className={`btn btn-sm ${i === current ? 'btn-primary' : 'btn-outline'}`} onClick={() => { setCurrent(i); setAnswer(session.answers[i] || '') }}>
                Q{i + 1} {session.feedback[i] ? '✓' : ''}
              </button>
            ))}
          </div>

          <button className="btn btn-ghost mt-16" onClick={() => setSession(null)}>Start a new interview</button>
        </div>
      )}
    </div>
  )
}
