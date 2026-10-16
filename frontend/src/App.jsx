import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Navbar from './components/Navbar'
import ChatWidget from './components/ChatWidget'
import ProtectedRoute from './components/ProtectedRoute'

import Login from './pages/Login'
import Register from './pages/Register'

import Dashboard from './pages/seeker/Dashboard'
import ResumeCenter from './pages/seeker/ResumeCenter'
import JobSearch from './pages/seeker/JobSearch'
import JobDetails from './pages/seeker/JobDetails'
import ApplicationTracker from './pages/seeker/ApplicationTracker'
import MockInterview from './pages/seeker/MockInterview'
import VideoInterview from './pages/seeker/VideoInterview'

import RecruiterDashboard from './pages/recruiter/RecruiterDashboard'
import PostJob from './pages/recruiter/PostJob'
import ManageJobs from './pages/recruiter/ManageJobs'

import AdminDashboard from './pages/admin/AdminDashboard'
import Users from './pages/admin/Users'
import JobsReports from './pages/admin/JobsReports'

function HomeRouter() {
  const { user } = useAuth()
  if (user.role === 'recruiter') return <RecruiterDashboard />
  if (user.role === 'admin') return <AdminDashboard />
  return <Dashboard />
}

export default function App() {
  const { user } = useAuth()

  return (
    <div className="app-shell">
      <Navbar />
      <div className="app-main">
        <Routes>
          <Route path="/login" element={user ? <Navigate to="/" /> : <Login />} />
          <Route path="/register" element={user ? <Navigate to="/" /> : <Register />} />

          <Route path="/" element={<ProtectedRoute><HomeRouter /></ProtectedRoute>} />

          {/* Job seeker */}
          <Route path="/resumes" element={<ProtectedRoute roles={['job_seeker']}><ResumeCenter /></ProtectedRoute>} />
          <Route path="/jobs" element={<ProtectedRoute roles={['job_seeker']}><JobSearch /></ProtectedRoute>} />
          <Route path="/jobs/:id" element={<ProtectedRoute roles={['job_seeker']}><JobDetails /></ProtectedRoute>} />
          <Route path="/tracker" element={<ProtectedRoute roles={['job_seeker']}><ApplicationTracker /></ProtectedRoute>} />
          <Route path="/interview" element={<ProtectedRoute roles={['job_seeker']}><MockInterview /></ProtectedRoute>} />
          <Route path="/video-interview" element={<ProtectedRoute roles={['job_seeker']}><VideoInterview /></ProtectedRoute>} />

          {/* Recruiter */}
          <Route path="/recruiter/jobs" element={<ProtectedRoute roles={['recruiter']}><ManageJobs /></ProtectedRoute>} />
          <Route path="/recruiter/post" element={<ProtectedRoute roles={['recruiter']}><PostJob /></ProtectedRoute>} />

          {/* Admin */}
          <Route path="/admin/users" element={<ProtectedRoute roles={['admin']}><Users /></ProtectedRoute>} />
          <Route path="/admin/jobs" element={<ProtectedRoute roles={['admin']}><JobsReports /></ProtectedRoute>} />

          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </div>
      {user && user.role === 'job_seeker' && <ChatWidget />}
    </div>
  )
}
