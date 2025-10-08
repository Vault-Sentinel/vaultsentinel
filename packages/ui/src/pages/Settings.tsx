import React, { useState, useEffect } from 'react'
import { 
  Settings as SettingsIcon, 
  Shield, 
  Database, 
  Key,
  RefreshCw,
  Server,
  Cloud,
  Scan,
} from 'lucide-react'
import { getSettings } from '../services/api'

interface SettingsData {
  version: string
  mode: string
  database: {
    type: string
    url: string
  }
  mcp: {
    enabled: boolean
    base_url: string
    api_key_configured: boolean
  }
  gcs: {
    enabled: boolean
    bucket: string | null
  }
  api: {
    host: string
    port: number
    cors_origins: string[]
  }
  scanning: {
    max_files: number
    max_bytes_per_file: number
    include_patterns: string[]
    exclude_patterns: string[]
  }
}

const Settings: React.FC = () => {
  const [settings, setSettings] = useState<SettingsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      setLoading(true)
      const data = await getSettings()
      setSettings(data)
      setError(null)
    } catch (err) {
      setError('Failed to load settings')
      console.error('Settings error:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-danger-50 border border-danger-200 rounded-md p-4">
          <div className="flex">
            <SettingsIcon className="h-5 w-5 text-danger-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-danger-800">Error</h3>
              <p className="mt-1 text-sm text-danger-700">{error}</p>
              <button
                onClick={loadSettings}
                className="mt-2 btn btn-primary"
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="mt-2 text-gray-600">
          VaultSentinel API Configuration and Status
        </p>
      </div>

      <div className="space-y-8">
        {/* Application Status */}
        <div className="card p-6">
          <div className="flex items-center mb-4">
            <Server className="h-6 w-6 text-primary-600 mr-3" />
            <h2 className="text-xl font-semibold text-gray-900">Application Status</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Version
              </label>
              <p className="text-sm text-gray-900">{settings?.version}</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Mode
              </label>
              <div className="flex items-center">
                <div className="w-3 h-3 rounded-full mr-2 bg-success-500" />
                <span className="text-sm font-medium text-gray-900 capitalize">
                  {settings?.mode.replace('_', ' ')}
                </span>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                API Host
              </label>
              <p className="text-sm text-gray-900">{settings?.api.host}</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                API Port
              </label>
              <p className="text-sm text-gray-900">{settings?.api.port}</p>
            </div>
          </div>
        </div>

        {/* Database Configuration */}
        <div className="card p-6">
          <div className="flex items-center mb-4">
            <Database className="h-6 w-6 text-primary-600 mr-3" />
            <h2 className="text-xl font-semibold text-gray-900">Database Configuration</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Database Type
              </label>
              <p className="text-sm text-gray-900 capitalize">{settings?.database.type}</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Database File
              </label>
              <p className="text-sm text-gray-900">{settings?.database.url}</p>
            </div>
          </div>
        </div>

        {/* MCP Configuration */}
        <div className="card p-6">
          <div className="flex items-center mb-4">
            <Shield className="h-6 w-6 text-primary-600 mr-3" />
            <h2 className="text-xl font-semibold text-gray-900">MCP Configuration</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                MCP Status
              </label>
              <div className="flex items-center">
                <div className={`w-3 h-3 rounded-full mr-2 ${
                  settings?.mcp.enabled ? 'bg-success-500' : 'bg-danger-500'
                }`} />
                <span className="text-sm font-medium text-gray-900">
                  {settings?.mcp.enabled ? 'Enabled' : 'Disabled'}
                </span>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                MCP Base URL
              </label>
              <p className="text-sm text-gray-900">{settings?.mcp.base_url}</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                API Key Status
              </label>
              <div className="flex items-center">
                <div className={`w-3 h-3 rounded-full mr-2 ${
                  settings?.mcp.api_key_configured ? 'bg-success-500' : 'bg-warning-500'
                }`} />
                <span className="text-sm font-medium text-gray-900">
                  {settings?.mcp.api_key_configured ? 'Configured' : 'Not Configured'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Cloud Storage Configuration */}
        <div className="card p-6">
          <div className="flex items-center mb-4">
            <Cloud className="h-6 w-6 text-primary-600 mr-3" />
            <h2 className="text-xl font-semibold text-gray-900">Cloud Storage Configuration</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                GCS Status
              </label>
              <div className="flex items-center">
                <div className={`w-3 h-3 rounded-full mr-2 ${
                  settings?.gcs.enabled ? 'bg-success-500' : 'bg-gray-400'
                }`} />
                <span className="text-sm font-medium text-gray-900">
                  {settings?.gcs.enabled ? 'Enabled' : 'Disabled'}
                </span>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                GCS Bucket
              </label>
              <p className="text-sm text-gray-900">
                {settings?.gcs.bucket || 'Not configured'}
              </p>
            </div>
          </div>
        </div>

        {/* Scanning Configuration */}
        <div className="card p-6">
          <div className="flex items-center mb-4">
            <Scan className="h-6 w-6 text-primary-600 mr-3" />
            <h2 className="text-xl font-semibold text-gray-900">Scanning Configuration</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Max Files
              </label>
              <p className="text-sm text-gray-900">{settings?.scanning.max_files.toLocaleString()}</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Max File Size
              </label>
              <p className="text-sm text-gray-900">
                {settings?.scanning.max_bytes_per_file ? (settings.scanning.max_bytes_per_file / 1024).toFixed(0) : '0'} KB
              </p>
            </div>
            
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Include Patterns
              </label>
              <div className="flex flex-wrap gap-2">
                {settings?.scanning.include_patterns.map((pattern, index) => (
                  <span key={index} className="px-2 py-1 bg-success-100 text-success-800 text-xs rounded">
                    {pattern}
                  </span>
                ))}
              </div>
            </div>
            
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Exclude Patterns
              </label>
              <div className="flex flex-wrap gap-2">
                {settings?.scanning.exclude_patterns.map((pattern, index) => (
                  <span key={index} className="px-2 py-1 bg-warning-100 text-warning-800 text-xs rounded">
                    {pattern}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* CORS Configuration */}
        <div className="card p-6">
          <div className="flex items-center mb-4">
            <Key className="h-6 w-6 text-primary-600 mr-3" />
            <h2 className="text-xl font-semibold text-gray-900">CORS Configuration</h2>
          </div>
          
          <div className="grid grid-cols-1 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Allowed Origins
              </label>
              <div className="flex flex-wrap gap-2">
                {settings?.api.cors_origins.map((origin, index) => (
                  <span key={index} className="px-2 py-1 bg-primary-100 text-primary-800 text-xs rounded">
                    {origin}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Actions</h2>
              <p className="text-sm text-gray-600 mt-1">
                Refresh settings and configuration
              </p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={loadSettings}
                className="btn btn-secondary"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Settings
