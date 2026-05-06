import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  }
})

export const deleteSegment = async (id: number) => {
  await api.delete(`/segments/${id}/`)
}

export const fetchSegments = async (logDayId?: number) => {
  const url = logDayId ? `/segments/?log_day_id=${logDayId}` : '/segments/'
  const response = await api.get(url)
  return response.data
}

export const createSegment = async (segmentData: any) => {
  const response = await api.post('/segments/', segmentData)
  return response.data
}

export const getOrCreateLogDay = async (driverId: number, date: string) => {
  const response = await api.get(`/logdays/?driver_id=${driverId}&date=${date}`)
  if (response.data.length > 0) {
    return response.data[0]
  } else {
    const createResponse = await api.post('/logdays/', {
      driver: driverId,
      date: date,
      driver_number: 'D001',
      initials: 'JD',
      signature: 'John Doe',
      co_driver: 'N/A',
      home_terminal: 'Richmond, VA',
      truck_license: 'ABC123',
      shipper: 'Test Shipper',
      commodity: 'Test Commodity'
    })
    return createResponse.data
  }
}