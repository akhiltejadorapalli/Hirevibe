import { createContext, useContext, useState, useCallback } from 'react'
import client from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem('careerai_user')
    return raw ? JSON.parse(raw) : null
  })

  const persist = (token, u) => {
    localStorage.setItem('careerai_token', token)
    localStorage.setItem('careerai_user', JSON.stringify(u))
    setUser(u)
  }

  const login = useCallback(async (email, password) => {
    const res = await client.post('/auth/login', { email, password })
    persist(res.data.access_token, res.data.user)
    return res.data.user
  }, [])

  const register = useCallback(async (payload) => {
    const res = await client.post('/auth/register', payload)
    persist(res.data.access_token, res.data.user)
    return res.data.user
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('careerai_token')
    localStorage.removeItem('careerai_user')
    setUser(null)
  }, [])

  const refreshUser = useCallback(async () => {
    const res = await client.get('/auth/me')
    localStorage.setItem('careerai_user', JSON.stringify(res.data))
    setUser(res.data)
    return res.data
  }, [])

  return (
    <AuthContext.Provider value={{ user, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
