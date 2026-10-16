import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('seeker@careerai.com')
  const [password, setPassword] = useState('seeker123')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      navigate('/')
    } catch (err) {
      setError(err?.response?.data?.detail || 'Login failed')
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
        <h2>Welcome back</h2>
        <p>Log in to continue your job search.</p>
        <form onSubmit={submit}>
          <div className="field">
            <label>Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div className="field">
            <label>Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          {error && <div className="error-text">{error}</div>}
          <button className="btn btn-primary btn-block mt-16" disabled={loading}>
            {loading ? <span className="spinner" /> : 'Log In'}
          </button>
        </form>
        <div className="demo-hint">
          <strong>Demo accounts</strong> (run <code>python seed.py</code> first):<br />
          seeker@careerai.com / seeker123 · recruiter@careerai.com / recruiter123 · admin@careerai.com / admin123
        </div>
        <p className="mt-16" style={{ textAlign: 'center' }}>
          Don't have an account? <Link to="/register">Sign up</Link>
        </p>
      </div>
    </div>
  )
}
