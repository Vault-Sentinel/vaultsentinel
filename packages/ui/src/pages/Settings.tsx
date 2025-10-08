import React, { useState, useEffect } from 'react'
import { 
  Settings as SettingsIcon, 
  Shield, 
  Database, 
  Bell, 
  Key,
  Save,
  RefreshCw,
} from 'lucide-react'
import { getHealth } from '../services/api'
import { HealthStatus } from '../types'

const Settings: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadHealth()
  }, [])

  const loadHealth = async () => {
    try {
      setLoading(true)
      const data = await getHealth()
      setHealth(data)
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
                onClick={loadHealth}
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
          Configure VaultSentinel agent and monitoring settings
        </p>
      </div>

      <div className="space-y-8">
        {/* Agent Configuration */}
        <div className="card p-6">
          <div className="flex items-center mb-4">
            <Shield className="h-6 w-6 text-primary-600 mr-3" />
            <h2 className="text-xl font-semibold text-gray-900">Agent Configuration</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Agent Status
              </label>
              <div className="flex items-center">
                <div className={`w-3 h-3 rounded-full mr-2 ${
                  health?.agent_status.running ? 'bg-success-500' : 'bg-danger-500'
                }`} />
                <span className="text-sm font-medium text-gray-900">
                  {health?.agent_status.running ? 'Running' : 'Stopped'}
                </span>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Version
              </label>
              <p className="text-sm text-gray-900">{health?.version}</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Uptime
              </label>
              <p className="text-sm text-gray-900">
                {health?.uptime ? `${Math.round(health.uptime / 60)} minutes` : 'Unknown'}
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Last Scan
              </label>
              <p className="text-sm text-gray-900">
                {health?.agent_status.last_scan 
                  ? new Date(health.agent_status.last_scan).toLocaleString()
                  : 'Never'
                }
              </p>
            </div>
          </div>
        </div>

        {/* Repository Configuration */}
        <div className="card p-6">
          <div className="flex items-center mb-4">
            <Database className="h-6 w-6 text-primary-600 mr-3" />
            <h2 className="text-xl font-semibold text-gray-900">Repository Configuration</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                GitHub Repository
              </label>
              <p className="text-sm text-gray-900">
                {health?.agent_status.config.github_repo || 'Not configured'}
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Poll Interval
              </label>
              <p className="text-sm text-gray-900">
                {health?.agent_status.config.poll_interval_seconds || 120} seconds
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Scan Depth
              </label>
              <p className="text-sm text-gray-900">
                {health?.agent_status.config.scan_depth_commits || 10} commits
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Entropy Threshold
              </label>
              <p className="text-sm text-gray-900">
                {health?.agent_status.config.detection_entropy_threshold || 4.5}
              </p>
            </div>
          </div>
        </div>

        {/* Notification Configuration */}
        <div className="card p-6">
          <div className="flex items-center mb-4">
            <Bell className="h-6 w-6 text-primary-600 mr-3" />
            <h2 className="text-xl font-semibold text-gray-900">Notification Configuration</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Slack Webhook
              </label>
              <p className="text-sm text-gray-900">
                {health?.agent_status.config.slack_webhook_url 
                  ? `${health.agent_status.config.slack_webhook_url.substring(0, 20)}...`
                  : 'Not configured'
                }
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Remediation Enabled
              </label>
              <p className="text-sm text-gray-900">
                {health?.agent_status.config.remediation_enabled ? 'Yes' : 'No'}
              </p>
            </div>
          </div>
        </div>

        {/* Security Configuration */}
        <div className="card p-6">
          <div className="flex items-center mb-4">
            <Key className="h-6 w-6 text-primary-600 mr-3" />
            <h2 className="text-xl font-semibold text-gray-900">Security Configuration</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Database URL
              </label>
              <p className="text-sm text-gray-900">
                {health?.agent_status.config.database_url || 'Not configured'}
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Log Level
              </label>
              <p className="text-sm text-gray-900">
                {health?.agent_status.config.log_level || 'INFO'}
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                API Host
              </label>
              <p className="text-sm text-gray-900">
                {health?.agent_status.config.api_host || '0.0.0.0'}
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                API Port
              </label>
              <p className="text-sm text-gray-900">
                {health?.agent_status.config.api_port || 8000}
              </p>
            </div>
          </div>
        </div>


        {/* Plugin Status */}
        <div className="card p-6">
          <div className="flex items-center mb-4">
            <SettingsIcon className="h-6 w-6 text-primary-600 mr-3" />
            <h2 className="text-xl font-semibold text-gray-900">Plugin Status</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-3">Detectors</h3>
              <div className="space-y-2">
                {health?.agent_status.registered_plugins.detectors.map((detector) => (
                  <div key={detector} className="flex items-center">
                    <div className="w-2 h-2 bg-success-500 rounded-full mr-2" />
                    <span className="text-sm text-gray-700">{detector}</span>
                  </div>
                ))}
              </div>
            </div>
            
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-3">Connectors</h3>
              <div className="space-y-2">
                {health?.agent_status.registered_plugins.connectors.map((connector) => (
                  <div key={connector} className="flex items-center">
                    <div className="w-2 h-2 bg-success-500 rounded-full mr-2" />
                    <span className="text-sm text-gray-700">{connector}</span>
                  </div>
                ))}
              </div>
            </div>
            
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-3">Remediation Handlers</h3>
              <div className="space-y-2">
                {health?.agent_status.registered_plugins.remediation_handlers.map((handler) => (
                  <div key={handler} className="flex items-center">
                    <div className="w-2 h-2 bg-success-500 rounded-full mr-2" />
                    <span className="text-sm text-gray-700">{handler}</span>
                  </div>
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
                Manage agent operations and configuration
              </p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={loadHealth}
                className="btn btn-secondary"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </button>
              <button className="btn btn-primary">
                <Save className="h-4 w-4 mr-2" />
                Save Changes
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Settings
