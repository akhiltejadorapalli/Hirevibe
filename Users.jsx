import { useEffect, useState } from 'react'
import client from '../../api/client'

export default function Users() {
  const [users, setUsers] = useState([])
  const [role, setRole] = useState('')

  const load = () => client.get('/admin/users', { params: { role: role || undefined } }).then((r) => setUsers(r.data))
  useEffect(() => { load() }, [role])

  const ban = async (id, banned) => { await client.put(`/admin/users/${id}/ban`, null, { params: { banned } }); load() }
  const verify = async (id, verified) => { await client.put(`/admin/recruiters/${id}/verify`, null, { params: { verified } }); load() }

  return (
    <div>
      <div className="page-header"><h1>Manage Users</h1><p>Manage job seekers, recruiters, and company verification.</p></div>
      <div className="pill-nav">
        {['', 'job_seeker', 'recruiter', 'admin'].map((r) => (
          <a key={r} className={role === r ? 'active' : ''} onClick={() => setRole(r)}>{r ? r.replace('_', ' ') : 'All'}</a>
        ))}
      </div>
      <div className="card">
        <table>
          <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Company</th><th>Status</th><th>Actions</th></tr></thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>{u.name}</td>
                <td>{u.email}</td>
                <td>{u.role.replace('_', ' ')}</td>
                <td>{u.company_name || '—'} {u.role === 'recruiter' && (u.company_verified ? <span className="badge badge-teal">Verified</span> : <span className="badge badge-warn">Unverified</span>)}</td>
                <td>{u.is_banned ? <span className="badge badge-danger">Banned</span> : <span className="badge badge-teal">Active</span>}</td>
                <td className="flex-gap">
                  {u.role === 'recruiter' && (
                    <button className="btn btn-sm btn-outline" onClick={() => verify(u.id, !u.company_verified)}>
                      {u.company_verified ? 'Unverify' : 'Verify'}
                    </button>
                  )}
                  {u.role !== 'admin' && (
                    <button className="btn btn-sm btn-danger" onClick={() => ban(u.id, !u.is_banned)}>
                      {u.is_banned ? 'Unban' : 'Ban'}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
