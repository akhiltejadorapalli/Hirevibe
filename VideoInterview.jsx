import { useEffect, useRef, useState } from 'react'
import client from '../../api/client'

const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition

export default function VideoInterview() {
  const [role, setRole] = useState('Software Engineer')
  const [session, setSession] = useState(null)
  const [current, setCurrent] = useState(0)
  const [starting, setStarting] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const [cameraOn, setCameraOn] = useState(false)
  const [cameraError, setCameraError] = useState('')
  const [speaking, setSpeaking] = useState(false)
  const [listening, setListening] = useState(false)
  const [recording, setRecording] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [recordings, setRecordings] = useState({}) // { questionIndex: blobUrl }

  const videoRef = useRef(null)
  const streamRef = useRef(null)
  const recognitionRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])

  const speechSupported = !!SpeechRecognitionAPI

  // Re-attach the live camera stream whenever the <video> element (re)mounts
  // (it moves between the pre-interview and in-interview layouts).
  useEffect(() => {
    if (videoRef.current && streamRef.current) {
      videoRef.current.srcObject = streamRef.current
    }
  }, [cameraOn, session])

  // Speak the first question aloud as soon as the interview starts.
  useEffect(() => {
    if (session && current === 0) {
      const t = setTimeout(() => speakQuestion(session.questions[0]), 400)
      return () => clearTimeout(t)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session])

  useEffect(() => {
    return () => {
      stopEverything()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const stopEverything = () => {
    if (recognitionRef.current) { try { recognitionRef.current.stop() } catch { /* noop */ } }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try { mediaRecorderRef.current.stop() } catch { /* noop */ }
    }
    window.speechSynthesis?.cancel()
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop())
      streamRef.current = null
    }
  }

  const startCamera = async () => {
    setCameraError('')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
      }
      setCameraOn(true)
    } catch (err) {
      setCameraError('Could not access camera/microphone. Check browser permissions, or type answers manually below.')
    }
  }

  const startInterview = async () => {
    setStarting(true)
    try {
      const res = await client.post('/interview/start', { role, num_questions: 5, mode: 'video' })
      setSession(res.data)
      setCurrent(0)
      setTranscript('')
      setRecordings({})
    } finally {
      setStarting(false)
    }
  }

  const speakQuestion = (text) => {
    if (!window.speechSynthesis) return
    window.speechSynthesis.cancel()
    const utter = new SpeechSynthesisUtterance(text)
    utter.rate = 0.95
    utter.onstart = () => setSpeaking(true)
    utter.onend = () => setSpeaking(false)
    window.speechSynthesis.speak(utter)
  }

  const startAnswer = () => {
    setTranscript('')
    chunksRef.current = []

    // Live speech-to-text
    if (speechSupported) {
      const recognition = new SpeechRecognitionAPI()
      recognition.continuous = true
      recognition.interimResults = true
      recognition.lang = 'en-US'
      recognition.onresult = (event) => {
        let finalText = ''
        for (let i = 0; i < event.results.length; i++) {
          finalText += event.results[i][0].transcript + ' '
        }
        setTranscript(finalText.trim())
      }
      recognition.onerror = () => setListening(false)
      recognition.onend = () => setListening(false)
      recognitionRef.current = recognition
      recognition.start()
      setListening(true)
    }

    // Record the video answer, if camera is on
    if (streamRef.current) {
      try {
        const recorder = new MediaRecorder(streamRef.current)
        recorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data) }
        recorder.onstop = () => {
          const blob = new Blob(chunksRef.current, { type: 'video/webm' })
          const url = URL.createObjectURL(blob)
          setRecordings((r) => ({ ...r, [current]: url }))
        }
        mediaRecorderRef.current = recorder
        recorder.start()
        setRecording(true)
      } catch {
        // MediaRecorder not supported — transcript-only still works
      }
    }
  }

  const stopAnswer = () => {
    if (recognitionRef.current) { try { recognitionRef.current.stop() } catch { /* noop */ } }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try { mediaRecorderRef.current.stop() } catch { /* noop */ }
    }
    setListening(false)
    setRecording(false)
  }

  const submitAnswer = async () => {
    if (!transcript.trim()) return
    setSubmitting(true)
    try {
      const res = await client.post('/interview/answer', { session_id: session.id, question_index: current, answer: transcript })
      setSession(res.data)
      if (current < session.questions.length - 1) {
        const next = current + 1
        setCurrent(next)
        setTranscript('')
        setTimeout(() => speakQuestion(session.questions[next]), 300)
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>AI Video Interview</h1>
        <p>CareerBot reads each question aloud — answer on camera and your speech is transcribed and scored live.</p>
      </div>

      {!speechSupported && (
        <div className="card" style={{ background: 'var(--warn-light)', border: 'none', marginBottom: 16 }}>
          <strong>Live speech-to-text isn't supported in this browser.</strong>
          <p style={{ marginTop: 4 }}>Try Chrome or Edge for automatic transcription, or type your answers manually below — video recording will still work.</p>
        </div>
      )}

      {!session && (
        <div className="card">
          <div className="field">
            <label>Target role</label>
            <input value={role} onChange={(e) => setRole(e.target.value)} placeholder="e.g. Software Engineer, Data Analyst, Product Manager" />
          </div>

          <div className="flex-gap">
            <button className="btn btn-outline" onClick={startCamera} disabled={cameraOn}>
              {cameraOn ? 'Camera ready ✓' : 'Enable Camera & Mic'}
            </button>
            <button className="btn btn-primary" onClick={startInterview} disabled={starting}>
              {starting ? 'Preparing…' : 'Start Video Interview'}
            </button>
          </div>

          {cameraOn && (
            <video ref={videoRef} autoPlay muted playsInline style={{ width: 280, borderRadius: 12, marginTop: 16, background: '#000' }} />
          )}
          {cameraError && <div className="error-text">{cameraError}</div>}
        </div>
      )}

      {session && (
        <div className="grid grid-2">
          <div className="card">
            <div className="section-title">Live Camera</div>
            <video ref={videoRef} autoPlay muted playsInline style={{ width: '100%', borderRadius: 12, background: '#000', aspectRatio: '4/3', objectFit: 'cover' }} />
            {!cameraOn && (
              <button className="btn btn-outline btn-sm mt-8" onClick={startCamera}>Enable Camera & Mic</button>
            )}
            {recording && <div className="badge badge-danger mt-8">● Recording</div>}
            {listening && <div className="badge badge-teal mt-8" style={{ marginLeft: 6 }}>🎤 Listening…</div>}
          </div>

          <div className="card">
            <div className="flex-between">
              <div className="section-title">Question {current + 1} of {session.questions.length}</div>
              {session.overall_score > 0 && <span className="badge badge-teal">Overall: {session.overall_score}/100</span>}
            </div>
            <p style={{ fontSize: 16, color: 'var(--ink)', fontWeight: 600 }}>
              {session.questions[current]} {speaking && <span className="muted">🔊 speaking…</span>}
            </p>

            <div className="flex-gap">
              <button className="btn btn-outline btn-sm" onClick={() => speakQuestion(session.questions[current])}>🔊 Hear question again</button>
              {!listening && !recording ? (
                <button className="btn btn-accent btn-sm" onClick={startAnswer}>● Start answering</button>
              ) : (
                <button className="btn btn-danger btn-sm" onClick={stopAnswer}>■ Stop</button>
              )}
            </div>

            <div className="field mt-16">
              <label>Live transcript (editable before submitting)</label>
              <textarea rows={5} value={transcript} onChange={(e) => setTranscript(e.target.value)} placeholder="Your spoken answer will appear here as you talk — or type it manually." />
            </div>

            <button className="btn btn-primary" onClick={submitAnswer} disabled={submitting || !transcript.trim()}>
              {submitting ? 'Scoring…' : 'Submit Answer'}
            </button>

            {recordings[current] && (
              <div className="mt-16">
                <div className="section-title">Your recorded answer</div>
                <video src={recordings[current]} controls style={{ width: '100%', borderRadius: 10 }} />
                <a href={recordings[current]} download={`answer-${current + 1}.webm`} className="btn btn-outline btn-sm mt-8">Download recording</a>
              </div>
            )}

            {session.feedback[current] && (
              <div className="card mt-16" style={{ background: 'var(--teal-light)', border: 'none' }}>
                <strong>Feedback — Score: {session.feedback[current].score}/100</strong>
                <ul>{session.feedback[current].tips.map((t, i) => <li key={i} style={{ fontSize: 13.5 }}>{t}</li>)}</ul>
              </div>
            )}

            <div className="flex-gap mt-16">
              {session.questions.map((_, i) => (
                <button key={i} className={`btn btn-sm ${i === current ? 'btn-primary' : 'btn-outline'}`} onClick={() => { setCurrent(i); setTranscript(session.answers[i] || '') }}>
                  Q{i + 1} {session.feedback[i] ? '✓' : ''}
                </button>
              ))}
            </div>

            <button className="btn btn-ghost mt-16" onClick={() => { stopEverything(); setSession(null); setCameraOn(false) }}>
              End interview
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
