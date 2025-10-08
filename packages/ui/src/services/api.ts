import axios from 'axios'
import { Finding, HealthStatus, ApiResponse } from '../types'

// Get API URL from environment or use default
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://vaultsentinel-backend-fgain323oq-uw.a.run.app'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
})

// Health check
export const getHealth = async (): Promise<HealthStatus> => {
  const response = await api.get('/healthz')
  return response.data
}

// Settings
export const getSettings = async (): Promise<any> => {
  const response = await api.get('/api/settings')
  return response.data
}

// Findings
export const getFindings = async (params?: {
  status?: string
  kind?: string
  since?: string
  repo?: string
  limit?: number
  offset?: number
}): Promise<ApiResponse<Finding[]>> => {
  const response = await api.get('/api/findings', { params })
  return response.data
}

export const updateFinding = async (
  id: string,
  data: { status?: string; notes?: string }
): Promise<{ message: string }> => {
  const response = await api.patch(`/api/findings/${id}`, data)
  return response.data
}


// Error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default api
