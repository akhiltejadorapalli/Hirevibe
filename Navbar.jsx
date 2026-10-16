import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const NAV = {
  job_seeker: [
    ['/', 'Dashboard'], ['/resumes', 'Resume Center'], ['/jobs', 'Job Search'],
    ['/tracker', 'Applications'], ['/interview', 'Mock Interview'], ['/video-interview', 'Video Interview'],
  ],
  recruiter: [
    ['/', 'Dashboard'], ['/recruiter/jobs', 'My Jobs'], ['/recruiter/post', 'Post a Job'],
  ],
  admin: [
    ['/', 'Dashboard'], ['/admin/users', 'Users'], ['/admin/jobs', 'Jobs & Reports'],
  ],
}

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  if (!user) return null

  return (
    <div className="navbar">
      <div className="navbar-inner">
        <div className="brand"><span className="dot" /> CareerAI</div>
        <div className="nav-links">
          {(NAV[user.role] || []).map(([to, label]) => (
            <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) => (isActive ? 'active' : '')}>
              {label}
            </NavLink>
          ))}
        </div>
        <div className="nav-right">
          <div className="avatar-chip">
            <span className="avatar-circle">{user.name?.[0]?.toUpperCase() || '?'}</span>
            {user.name} <span style={{ opacity: 0.6 }}>· {user.role.replace('_', ' ')}</span>
          </div>
          <button className="btn btn-ghost btn-sm" style={{ color: '#fff' }} onClick={() => { logout(); navigate('/login') }}>
            Log out
          </button>
        </div>
      </div>
    </div>
  )
}
