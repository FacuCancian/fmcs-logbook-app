import { useEffect, useRef } from 'react'

interface DutySegment {
  id: number
  start_time: string
  end_time: string
  status: 'OFF' | 'SB' | 'D' | 'ON'
  location_city: string
  location_state: string
}

interface Props {
  segments: DutySegment[]
  onClear?: () => void
}

const STATUS_ROW: Record<string, number> = {
  OFF: 0,
  SB: 1,
  D: 2,
  ON: 3,
}

const STATUS_COLOR: Record<string, string> = {
  OFF: '#6b7280',
  SB: '#8b5cf6',
  D: '#2563eb',
  ON: '#dc2626',
}

const STATUS_LABEL: Record<string, string> = {
  OFF: 'Off Duty',
  SB: 'Sleeper Berth',
  D: 'Driving',
  ON: 'On Duty (Not Driving)',
}

export default function LogGrid({ segments, onClear }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    drawGrid()
  }, [segments])

  const getHourDecimal = (dateStr: string) => {
    const d = new Date(dateStr)
    return d.getHours() + d.getMinutes() / 60 + d.getSeconds() / 3600
  }

  const drawGrid = () => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const width = canvas.width
    const height = canvas.height
    const rowHeight = height / 4
    const hourWidth = width / 24

    ctx.clearRect(0, 0, width, height)

    const rowColors = ['#f0fdf4', '#faf5ff', '#eff6ff', '#fff7ed']
    for (let row = 0; row < 4; row++) {
      ctx.fillStyle = rowColors[row]
      ctx.fillRect(0, row * rowHeight, width, rowHeight)
    }

    for (let hour = 0; hour <= 24; hour++) {
      const x = hour * hourWidth
      ctx.beginPath()
      ctx.moveTo(x, 0)
      ctx.lineTo(x, height)
      ctx.strokeStyle = hour % 6 === 0 ? '#9ca3af' : '#d1d5db'
      ctx.lineWidth = hour % 6 === 0 ? 1 : 0.5
      ctx.stroke()


      if (hour % 2 === 0) {
        ctx.fillStyle = '#374151'
        ctx.font = 'bold 9px monospace'
        ctx.textAlign = 'center'
        let label = hour.toString()
        if (hour === 0) label = 'M'
        if (hour === 12) label = 'N'
        if (hour === 24) label = 'M'
        ctx.fillText(label, x, 12)
      }
    }

    for (let row = 0; row <= 4; row++) {
      const y = row * rowHeight
      ctx.beginPath()
      ctx.moveTo(0, y)
      ctx.lineTo(width, y)
      ctx.strokeStyle = '#6b7280'
      ctx.lineWidth = row === 0 || row === 4 ? 1.5 : 1
      ctx.stroke()
    }

    for (const seg of segments) {
      const startH = getHourDecimal(seg.start_time)
      const endH = getHourDecimal(seg.end_time)
      const row = STATUS_ROW[seg.status]
      const color = STATUS_COLOR[seg.status]
      const x1 = startH * hourWidth
      const x2 = endH * hourWidth
      const y = row * rowHeight


      ctx.fillStyle = color + '30'
      ctx.fillRect(x1, y + 1, x2 - x1, rowHeight - 2)


      const lineY = y + rowHeight / 2
      ctx.beginPath()
      ctx.moveTo(x1, lineY)
      ctx.lineTo(x2, lineY)
      ctx.strokeStyle = color
      ctx.lineWidth = 3
      ctx.stroke()
    }

    if (segments.length === 0) return


    const sorted = [...segments].sort(
      (a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
    )

    interface Point { x: number; y: number }

    const points: Point[] = []
    const offDutyY = 0 * rowHeight + rowHeight / 2

    points.push({ x: 0, y: offDutyY })

    let lastTime = 0

    for (const seg of sorted) {
      const startH = getHourDecimal(seg.start_time)
      const endH = getHourDecimal(seg.end_time)
      const currentRowY = STATUS_ROW[seg.status] * rowHeight + rowHeight / 2

      if (startH > lastTime) {
        points.push({ x: lastTime * hourWidth, y: offDutyY })
        points.push({ x: startH * hourWidth, y: offDutyY })
      }


      points.push({ x: startH * hourWidth, y: currentRowY })
      points.push({ x: endH * hourWidth, y: currentRowY })

      lastTime = endH
    }

    if (points.length > 1) {
      ctx.beginPath()
      ctx.moveTo(points[0].x, points[0].y)

      for (let i = 1; i < points.length; i++) {
        const prev = points[i - 1]
        const curr = points[i]

        if (prev.y !== curr.y) {
          ctx.lineTo(prev.x, curr.y)
          ctx.lineTo(curr.x, curr.y)
        } else {
          ctx.lineTo(curr.x, curr.y)
        }
      }

      ctx.strokeStyle = '#374151'
      ctx.lineWidth = 2.5
      ctx.stroke()
    }

    for (let i = 1; i < points.length - 1; i++) {
      const p = points[i]
      if (p.x === 0 || p.x === 24 * hourWidth) continue

      ctx.beginPath()
      ctx.arc(p.x, p.y, 3.5, 0, 2 * Math.PI)
      ctx.fillStyle = '#ef4444'
      ctx.fill()
      ctx.strokeStyle = 'white'
      ctx.lineWidth = 1
      ctx.stroke()
    }
  }

  return (
    <div style={{ marginTop: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <h2 style={{ fontWeight: 'bold', fontSize: '16px' }}>24-Hour Log Grid</h2>
        {onClear && (
          <button
            onClick={onClear}
            style={{
              padding: '4px 12px',
              background: '#ef4444',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            🗑️ Clear All
          </button>
        )}
      </div>

      <div style={{ display: 'flex', gap: '0' }}>
        {/* Row labels */}
        <div style={{ width: '120px', flexShrink: 0 }}>
          {Object.entries(STATUS_LABEL).map(([key, label]) => (
            <div key={key} style={{
              height: '80px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'flex-end',
              paddingRight: '10px',
              fontSize: '11px',
              fontWeight: '600',
              color: STATUS_COLOR[key],
              borderBottom: '1px solid #e5e7eb',
            }}>
              {label}
            </div>
          ))}
        </div>

        <div style={{ flex: 1 }}>
          <canvas
            ref={canvasRef}
            width={960}
            height={320}
            style={{
              border: '1px solid #9ca3af',
              width: '100%',
              height: 'auto',
              display: 'block',
            }}
          />
        </div>
      </div>
    </div>
  )
}