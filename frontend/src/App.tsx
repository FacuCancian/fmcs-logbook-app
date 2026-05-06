import { useState, useEffect } from 'react'
import LogForm from './components/LogForm'
import LogGrid from './components/LogGrid'
import { fetchSegments, createSegment, getOrCreateLogDay, deleteSegment } from './api/logbookApi'
interface DutySegment {
  id: number
  start_time: string
  end_time: string
  status: 'OFF' | 'SB' | 'D' | 'ON'
  location_city: string
  location_state: string
}

function App() {
  const [segments, setSegments] = useState<DutySegment[]>([])
  const [loading, setLoading] = useState(true)
  const [logDayId, setLogDayId] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadData = async () => {
      try {
        const today = new Date().toISOString().split('T')[0]
        const logDay = await getOrCreateLogDay(1, today)
        setLogDayId(logDay.id)
        const segmentsData = await fetchSegments(logDay.id)
        setSegments(segmentsData)
      } catch (err) {
        console.error('Error loading data:', err)
        setError('Could not connect to server. Is Django running?')
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])
   const handleReset = async () => {
     if (!confirm('Clear all segments for today?')) return
     try {
       for (const seg of segments) {
         await deleteSegment(seg.id)
       }
       setSegments([])
       alert('All segments cleared')
     } catch (err) {
       console.error('Error clearing segments:', err)
       alert('Error clearing segments')
     }
   }

    <button onClick={handleReset} style={{
      padding: '6px 12px', background: '#ef4444', color: 'white',
      border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '12px'
    }}>
      🗑️ Clear Day
    </button>
  const handleAddSegment = async (newSegment: any) => {
    if (!logDayId) {
      alert('LogDay not initialized yet, wait a moment')
      return
    }
    try {
      const segmentWithLogDay = { ...newSegment, log_day: logDayId }
      const savedSegment = await createSegment(segmentWithLogDay)
      setSegments(prev => [...prev, savedSegment])
    } catch (err: any) {
      const errors = err.response?.data
      const msg =
        errors?.non_field_errors?.[0] ||
        errors?.start_time?.[0] ||
        errors?.end_time?.[0] ||
        JSON.stringify(errors) ||
        'Error saving segment'
      alert(`❌ ${msg}`)
    }
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <p>Loading...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: 'red' }}>
        <p>{error}</p>
      </div>
    )
  }

  const drivingHours = segments
    .filter(s => s.status === 'D')
    .reduce((acc, s) => {
      const diff = (new Date(s.end_time).getTime() - new Date(s.start_time).getTime()) / 3600000
      return acc + diff
    }, 0)

  const onDutyHours = segments
    .filter(s => s.status === 'D' || s.status === 'ON')
    .reduce((acc, s) => {
      const diff = (new Date(s.end_time).getTime() - new Date(s.start_time).getTime()) / 3600000
      return acc + diff
    }, 0)

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto', fontFamily: 'sans-serif' }}>
      <h1 style={{ textAlign: 'center', fontSize: '24px', fontWeight: 'bold', marginBottom: '4px' }}>
        📋 FMCSA Driver's Daily Log
      </h1>
      <p style={{ textAlign: 'center', color: '#666', marginBottom: '24px' }}>
        Electronic Logging Device (ELD) — Hours of Service
      </p>

      {/* HOS Summary */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '20px', flexWrap: 'wrap' }}>
        {[
          { label: 'Driving', value: drivingHours, max: 11, color: '#3b82f6' },
          { label: 'On Duty', value: onDutyHours, max: 14, color: '#f59e0b' },
        ].map(item => (
          <div key={item.label} style={{
            flex: 1, minWidth: '160px', background: '#f9fafb',
            border: '1px solid #e5e7eb', borderRadius: '8px', padding: '12px'
          }}>
            <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>{item.label}</div>
            <div style={{ fontSize: '20px', fontWeight: 'bold', color: item.value > item.max ? 'red' : item.color }}>
              {item.value.toFixed(1)}h
            </div>
            <div style={{ fontSize: '11px', color: '#9ca3af' }}>of {item.max}h max</div>
            <div style={{
              marginTop: '6px', height: '4px', background: '#e5e7eb', borderRadius: '2px'
            }}>
              <div style={{
                height: '100%', borderRadius: '2px',
                width: `${Math.min((item.value / item.max) * 100, 100)}%`,
                background: item.value > item.max ? 'red' : item.color,
                transition: 'width 0.3s'
              }} />
            </div>
          </div>
        ))}
      </div>

      <LogForm onSubmit={handleAddSegment} />
      <LogGrid segments={segments} onClear={handleReset} />

      {segments.length > 0 && (
        <div style={{
          marginTop: '20px', background: '#f9fafb',
          border: '1px solid #e5e7eb', padding: '16px', borderRadius: '8px'
        }}>
          <h3 style={{ fontWeight: 'bold', marginBottom: '8px' }}>📝 Remarks</h3>
          <div style={{ fontSize: '13px', color: '#374151' }}>
            {[...segments]
              .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
              .map(seg => (
                <div key={seg.id} style={{ padding: '4px 0', borderBottom: '1px solid #f3f4f6' }}>
                  <span style={{ fontWeight: 500 }}>
                    {new Date(seg.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    {' → '}
                    {new Date(seg.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                  {' '}
                  <span style={{ color: '#6b7280' }}>
                    {seg.status === 'D' ? '🚛 Driving' :
                     seg.status === 'ON' ? '📋 On Duty' :
                     seg.status === 'SB' ? '🛏️ Sleeper Berth' : '⏸️ Off Duty'}
                  </span>
                  {' — '}
                  {seg.location_city}, {seg.location_state}
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default App