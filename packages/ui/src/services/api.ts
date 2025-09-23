import axios from 'axios'
import { Finding, Metrics, HealthStatus, ApiResponse } from '../types'

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
})

// Health check
export const getHealth = async (): Promise<HealthStatus> => {
  const response = await api.get('/healthz')
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
  const response = await api.get('/findings', { params })
  return response.data
}

export const updateFinding = async (
  id: string,
  data: { status?: string; notes?: string }
): Promise<{ message: string }> => {
  const response = await api.patch(`/findings/${id}`, data)
  return response.data
}

// Metrics
export const getMetrics = async (): Promise<Metrics> => {
  const response = await api.get('/metrics')
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
