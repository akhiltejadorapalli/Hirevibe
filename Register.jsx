import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [role, setRole] = useState('job_seeker')
  const [form, setForm] = useState({ name: '', email: '', password: '', company_name: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register({ ...form, role })
      navigate('/')
    } catch (err) {
      setError(err?.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-wrap">
      <div className="auth-card">
        <div className="brand" style={{ color: 'var(--primary)', marginBottom: 18 }}>
          <span className="dot" style={{ background: 'var(--accent)' }} /> CareerAI
        </div>
        <h2>Create your account</h2>
        <div className="auth-tabs">
          <button type="button" className={role === 'job_seeker' ? 'active' : ''} onClick={() => setRole('job_seeker')}>Job Seeker</button>
          <button type="button" className={role === 'recruiter' ? 'active' : ''} onClick={() => setRole('recruiter')}>Recruiter</button>
        </div>
        <form onSubmit={submit}>
          <div className="field">
            <label>Full name</label>
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          </div>
          <div className="field">
            <label>Email</label>
            <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
          </div>
          {role === 'recruiter' && (
            <div className="field">
              <label>Company name</label>
              <input value={form.company_name} onChange={(e) => setForm({ ...form, company_name: e.target.value })} required />
            </div>
          )}
          <div className="field">
            <label>Password</label>
            <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required minLength={6} />
          </div>
          {error && <div className="error-text">{error}</div>}
          <button className="btn btn-primary btn-block mt-16" disabled={loading}>
            {loading ? <span className="spinner" /> : 'Create Account'}
          </button>
        </form>
        <p className="mt-16" style={{ textAlign: 'center' }}>
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </div>
    </div>
  )
}
