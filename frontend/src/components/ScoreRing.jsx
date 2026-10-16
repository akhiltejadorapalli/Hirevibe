export default function ScoreRing({ score = 0, size = 92, label }) {
  const radius = (size - 10) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (Math.min(100, Math.max(0, score)) / 100) * circumference
  const color = score >= 75 ? '#2fa896' : score >= 45 ? '#e8912b' : '#d64550'

  return (
    <div className="score-ring" style={{ width: size, height: size }}>
      <svg width={size} height={size}>
        <circle cx={size / 2} cy={size / 2} r={radius} stroke="#eef0f7" strokeWidth="8" fill="none" />
        <circle
          cx={size / 2} cy={size / 2} r={radius} stroke={color} strokeWidth="8" fill="none"
          strokeDasharray={circumference} strokeDashoffset={offset} strokeLinecap="round"
        />
      </svg>
      <div className="num">{score}</div>
      {label && <div style={{ position: 'absolute', top: size + 2, width: size, textAlign: 'center', fontSize: 11, color: 'var(--muted)' }}>{label}</div>}
    </div>
  )
}
