import { useEffect, useState } from 'react'
import client from '../../api/client'

const STAGES = [
  ['saved', 'Saved'], ['applied', 'Applied'], ['shortlisted', 'Shortlisted'],
  ['interview', 'Interview'], ['selected', 'Selected'], ['rejected', 'Rejected'],
]

export default function ApplicationTracker() {
  const [apps, setApps] = useState([])

  const load = () => client.get('/applications').then((r) => setApps(r.data))
  useEffect(() => { load() }, [])

  const updateStatus = async (id, status) => {
    await client.put(`/applications/${id}`, { status })
    load()
  }

  const updateNotes = async (id, notes) => {
    await client.put(`/applications/${id}`, { notes })
  }

  return (
    <div>
      <div className="page-header">
        <h1>Application Tracker</h1>
        <p>Track every application from saved through to an offer.</p>
      </div>

      <div className="tracker-board">
        {STAGES.map(([key, label]) => (
          <div className="tracker-col" key={key}>
            <h4>{label} ({apps.filter((a) => a.status === key).length})</h4>
            {apps.filter((a) => a.status === key).map((a) => (
              <div className="tracker-item" key={a.id}>
                <strong>{a.job?.title}</strong>
                <div className="muted">{a.job?.company}</div>
                {a.match_score > 0 && <div className="badge badge-teal mt-8">{a.match_score}% match</div>}
                <select value={a.status} onChange={(e) => updateStatus(a.id, e.target.value)}>
                  {STAGES.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
                </select>
                <textarea
                  placeholder="Notes / follow-up reminders…"
                  defaultValue={a.notes}
                  rows={2}
                  style={{ marginTop: 6, fontSize: 12 }}
                  onBlur={(e) => updateNotes(a.id, e.target.value)}
                />
              </div>
            ))}
            {apps.filter((a) => a.status === key).length === 0 && <p className="muted" style={{ fontSize: 12 }}>Nothing here yet.</p>}
          </div>
        ))}
      </div>
    </div>
  )
}
