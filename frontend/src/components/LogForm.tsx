import { useState } from 'react'

interface Props {
  onSubmit: (data: any) => void
}

export default function LogForm({ onSubmit }: Props) {
  const [formData, setFormData] = useState({
    start_time: '',
    end_time: '',
    status: 'ON',
    location_city: '',
    location_state: 'VA'
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.start_time || !formData.end_time) {
      alert('Please enter start and end times')
      return
    }
    onSubmit({
      ...formData,
      start_time: new Date(formData.start_time).toISOString().replace('.000Z', 'Z'),
      end_time: new Date(formData.end_time).toISOString().replace('.000Z', 'Z')
    })
    setFormData({
      start_time: '',
      end_time: '',
      status: 'ON',
      location_city: '',
      location_state: 'VA'
    })
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '20px' }}>
      <input
        type="datetime-local"
        value={formData.start_time}
        onChange={(e) => setFormData({...formData, start_time: e.target.value})}
        style={{ padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
        required
      />
      <input
        type="datetime-local"
        value={formData.end_time}
        onChange={(e) => setFormData({...formData, end_time: e.target.value})}
        style={{ padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
        required
      />
      <select
        value={formData.status}
        onChange={(e) => setFormData({...formData, status: e.target.value})}
        style={{ padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
      >
        <option value="OFF">Off Duty</option>
        <option value="SB">Sleeper Berth</option>
        <option value="D">Driving</option>
        <option value="ON">On Duty (Not Driving)</option>
      </select>
      <input
        type="text"
        value={formData.location_city}
        onChange={(e) => setFormData({...formData, location_city: e.target.value})}
        placeholder="City"
        style={{ padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
        required
      />
      <select
        value={formData.location_state}
        onChange={(e) => setFormData({...formData, location_state: e.target.value})}
        style={{ padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
      >
        <option value="VA">VA</option>
        <option value="MD">MD</option>
        <option value="DC">DC</option>
        <option value="PA">PA</option>
        <option value="NJ">NJ</option>
      </select>
      <button type="submit" style={{ padding: '8px 16px', background: '#3b82f6', color: 'white', border: 'none', borderRadius: '4px' }}>
        Add Activity
      </button>
    </form>
  )
}