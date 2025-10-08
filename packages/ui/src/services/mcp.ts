import axios from 'axios'
import { MCPHealthResponse, MCPChatResponse, MCPChatMessage } from '../types'

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || ''

const mcpApi = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 second timeout for MCP requests
})

// MCP Health Check
export const getMCPHealth = async (): Promise<MCPHealthResponse> => {
  try {
    const response = await mcpApi.get('/api/mcp/health')
    return response.data
  } catch (error: any) {
    console.error('MCP Health Check Error:', error)
    throw new Error(
      error.response?.data?.details?.error || 
      error.message || 
      'Failed to check MCP health'
    )
  }
}

// MCP Chat
export const sendMCPChat = async (
  messages: MCPChatMessage[],
  provider: 'gemini' | 'openai' = 'gemini'
): Promise<MCPChatResponse> => {
  try {
    const response = await mcpApi.post('/api/mcp/chat', {
      messages,
      provider
    })
    return response.data
  } catch (error: any) {
    console.error('MCP Chat Error:', error)
    throw new Error(
      error.response?.data?.result?.error || 
      error.message || 
      'Failed to send chat request to MCP'
    )
  }
}

// Error handling interceptor
mcpApi.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('MCP API Error:', error)
    return Promise.reject(error)
  }
)

export default mcpApi
