import { useEffect, useState } from 'react'
import client from '../../api/client'
import JobCard from '../../components/JobCard'

export default function JobSearch() {
  const [q, setQ] = useState('')
  const [location, setLocation] = useState('')
  const [jobs, setJobs] = useState([])
  const [savedIds, setSavedIds] = useState(new Set())
  const [loading, setLoading] = useState(true)

  const search = async () => {
    setLoading(true)
    const res = await client.get('/jobs', { params: { q: q || undefined, location: location || undefined } })
    setJobs(res.data)
    setLoading(false)
  }

  const loadSaved = async () => {
    const res = await client.get('/saved-jobs')
    setSavedIds(new Set(res.data.map((j) => j.id)))
  }

  useEffect(() => { search(); loadSaved() }, [])

  const toggleSave = async (job) => {
    if (savedIds.has(job.id)) {
      await client.delete(`/jobs/${job.id}/save`)
      setSavedIds((s) => { const n = new Set(s); n.delete(job.id); return n })
    } else {
      await client.post(`/jobs/${job.id}/save`)
      setSavedIds((s) => new Set(s).add(job.id))
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Search Jobs</h1>
        <p>Every listing here has passed AI job safety and quality analysis.</p>
      </div>

      <div className="card flex-gap" style={{ marginBottom: 20 }}>
        <input placeholder="Title, company, or keyword" value={q} onChange={(e) => setQ(e.target.value)} style={{ flex: 2 }} onKeyDown={(e) => e.key === 'Enter' && search()} />
        <input placeholder="Location" value={location} onChange={(e) => setLocation(e.target.value)} style={{ flex: 1 }} onKeyDown={(e) => e.key === 'Enter' && search()} />
        <button className="btn btn-primary" onClick={search}>Search</button>
      </div>

      {loading && <p>Loading jobs…</p>}
      {!loading && jobs.length === 0 && <div className="card empty-state">No jobs matched your search.</div>}
      {jobs.map((job) => (
        <JobCard key={job.id} job={job} onSave={toggleSave} saved={savedIds.has(job.id)} />
      ))}
    </div>
  )
}
