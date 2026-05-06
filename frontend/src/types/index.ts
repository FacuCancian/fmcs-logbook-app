export interface DutySegment {
  id: number
  start_time: string
  end_time: string
  status: 'OFF' | 'SB' | 'D' | 'ON'
  location_city: string
  location_state: string
  remarks_extra?: string
  duration_hours?: number
}

export interface LogDay {
  id: number
  driver: number
  date: string
  driver_number: string
  initials: string
  signature: string
  co_driver: string
  home_terminal: string
  truck_license: string
  trailer_1?: string
  trailer_2?: string
  trailer_3?: string
  trailer_4?: string
  shipper: string
  commodity: string
  load_id_1?: string
  load_id_2?: string
  load_id_3?: string
  load_id_4?: string
  total_driving_hours?: number
  total_on_duty_hours?: number
}

export interface Driver {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  driver_number: string
  home_terminal: string
  truck_license: string
  uses_70hour_8day?: boolean
}