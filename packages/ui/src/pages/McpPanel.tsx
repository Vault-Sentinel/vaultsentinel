import React, { useState, useEffect } from 'react'
import { getMCPHealth, sendMCPChat } from '../services/mcp'
import { MCPHealthResponse, MCPChatResponse, MCPChatMessage } from '../types'
import { CheckCircle, XCircle, Loader2, Send, RefreshCw } from 'lucide-react'

const McpPanel: React.FC = () => {
  const [healthStatus, setHealthStatus] = useState<MCPHealthResponse | null>(null)
  const [isHealthLoading, setIsHealthLoading] = useState(false)
  const [chatMessages, setChatMessages] = useState<MCPChatMessage[]>([])
  const [currentMessage, setCurrentMessage] = useState('')
  const [selectedProvider, setSelectedProvider] = useState<'gemini' | 'openai'>('gemini')
  const [isChatLoading, setIsChatLoading] = useState(false)
  const [chatResponse, setChatResponse] = useState<MCPChatResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Check MCP health on component mount
  useEffect(() => {
    checkHealth()
  }, [])

  const checkHealth = async () => {
    setIsHealthLoading(true)
    setError(null)
    try {
      const health = await getMCPHealth()
      setHealthStatus(health)
    } catch (err: any) {
      setError(err.message)
      setHealthStatus({
        status: 'error',
        details: { error: err.message },
        request_id: undefined
      })
    } finally {
      setIsHealthLoading(false)
    }
  }

  const sendMessage = async () => {
    if (!currentMessage.trim()) return

    const newMessage: MCPChatMessage = {
      role: 'user',
      content: currentMessage.trim()
    }

    setChatMessages(prev => [...prev, newMessage])
    setCurrentMessage('')
    setIsChatLoading(true)
    setError(null)

    try {
      const response = await sendMCPChat([...chatMessages, newMessage], selectedProvider)
      setChatResponse(response)
      
      if (response.status === 'ok' && response.result) {
        // Add assistant response if available
        const assistantMessage: MCPChatMessage = {
          role: 'assistant',
          content: Array.isArray(response.result) 
            ? response.result.map((item: any) => item.text || JSON.stringify(item)).join('\n')
            : JSON.stringify(response.result, null, 2)
        }
        setChatMessages(prev => [...prev, assistantMessage])
      }
    } catch (err: any) {
      setError(err.message)
    } finally {
      setIsChatLoading(false)
    }
  }

  const clearChat = () => {
    setChatMessages([])
    setChatResponse(null)
    setError(null)
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">MCP Integration Panel</h1>
        <button
          onClick={checkHealth}
          disabled={isHealthLoading}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {isHealthLoading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <RefreshCw className="w-4 h-4" />
          )}
          Refresh Health
        </button>
      </div>

      {/* Health Status */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          MCP Health Status
          {healthStatus && (
            healthStatus.status === 'ok' ? (
              <CheckCircle className="w-5 h-5 text-green-500" />
            ) : (
              <XCircle className="w-5 h-5 text-red-500" />
            )
          )}
        </h2>
        
        {healthStatus && (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="font-medium">Status:</span>
              <span className={`px-2 py-1 rounded text-sm ${
                healthStatus.status === 'ok' 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-red-100 text-red-800'
              }`}>
                {healthStatus.status}
              </span>
            </div>
            {healthStatus.request_id && (
              <div className="text-sm text-gray-600">
                Request ID: {healthStatus.request_id}
              </div>
            )}
            {healthStatus.details && (
              <div className="mt-3">
                <details className="text-sm">
                  <summary className="cursor-pointer font-medium">Details</summary>
                  <pre className="mt-2 p-3 bg-gray-100 rounded text-xs overflow-auto">
                    {JSON.stringify(healthStatus.details, null, 2)}
                  </pre>
                </details>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Chat Interface */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">MCP Chat Test</h2>
          <div className="flex items-center gap-4">
            <select
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value as 'gemini' | 'openai')}
              className="px-3 py-1 border border-gray-300 rounded text-sm"
            >
              <option value="gemini">Gemini</option>
              <option value="openai">OpenAI</option>
            </select>
            <button
              onClick={clearChat}
              className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800"
            >
              Clear Chat
            </button>
          </div>
        </div>

        {/* Chat Messages */}
        <div className="border border-gray-200 rounded-lg h-64 overflow-y-auto p-4 mb-4 bg-gray-50">
          {chatMessages.length === 0 ? (
            <div className="text-gray-500 text-center py-8">
              Start a conversation with the MCP server...
            </div>
          ) : (
            <div className="space-y-3">
              {chatMessages.map((message, index) => (
                <div
                  key={index}
                  className={`p-3 rounded-lg ${
                    message.role === 'user'
                      ? 'bg-blue-100 ml-8'
                      : 'bg-gray-100 mr-8'
                  }`}
                >
                  <div className="text-xs font-medium text-gray-600 mb-1">
                    {message.role}
                  </div>
                  <div className="text-sm whitespace-pre-wrap">
                    {message.content}
                  </div>
                </div>
              ))}
              {isChatLoading && (
                <div className="flex items-center gap-2 text-gray-500">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm">Sending message...</span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Message Input */}
        <div className="flex gap-2">
          <textarea
            value={currentMessage}
            onChange={(e) => setCurrentMessage(e.target.value)}
            placeholder="Enter your message here..."
            className="flex-1 p-3 border border-gray-300 rounded-lg resize-none"
            rows={3}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault()
                sendMessage()
              }
            }}
          />
          <button
            onClick={sendMessage}
            disabled={!currentMessage.trim() || isChatLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
          >
            {isChatLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            Send
          </button>
        </div>
        <div className="text-xs text-gray-500 mt-2">
          Press Ctrl+Enter (or Cmd+Enter) to send
        </div>
      </div>

      {/* Response Details */}
      {chatResponse && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Last Response</h2>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="font-medium">Status:</span>
              <span className={`px-2 py-1 rounded text-sm ${
                chatResponse.status === 'ok' 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-red-100 text-red-800'
              }`}>
                {chatResponse.status}
              </span>
            </div>
            {chatResponse.request_id && (
              <div className="text-sm text-gray-600">
                Request ID: {chatResponse.request_id}
              </div>
            )}
            <details className="mt-3">
              <summary className="cursor-pointer font-medium">Full Response</summary>
              <pre className="mt-2 p-3 bg-gray-100 rounded text-xs overflow-auto">
                {JSON.stringify(chatResponse, null, 2)}
              </pre>
            </details>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2 text-red-800">
            <XCircle className="w-5 h-5" />
            <span className="font-medium">Error</span>
          </div>
          <p className="text-red-700 mt-1">{error}</p>
        </div>
      )}
    </div>
  )
}

export default McpPanel
