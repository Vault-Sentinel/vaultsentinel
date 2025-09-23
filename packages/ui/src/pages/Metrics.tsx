import React, { useState, useEffect } from 'react'
import { 
  Clock, 
  Shield, 
  AlertTriangle,
  CheckCircle,
  RefreshCw
} from 'lucide-react'
import { getMetrics } from '../services/api'
import { Metrics as MetricsType } from '../types'
import { format } from 'date-fns'

const Metrics: React.FC = () => {
  const [metrics, setMetrics] = useState<MetricsType | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadMetrics()
    const interval = setInterval(loadMetrics, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const loadMetrics = async () => {
    try {
      setLoading(true)
      const data = await getMetrics()
      setMetrics(data)
      setError(null)
    } catch (err) {
      setError('Failed to load metrics')
      console.error('Metrics error:', err)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'NEW':
        return 'text-danger-600'
      case 'ACKNOWLEDGED':
        return 'text-warning-600'
      case 'RESOLVED':
        return 'text-success-600'
      case 'FALSE_POSITIVE':
        return 'text-gray-600'
      default:
        return 'text-gray-600'
    }
  }

  const getKindColor = (kind: string) => {
    const colors = [
      'text-primary-600',
      'text-success-600',
      'text-warning-600',
      'text-danger-600',
      'text-purple-600',
      'text-indigo-600',
      'text-pink-600',
      'text-blue-600'
    ]
    const index = kind.length % colors.length
    return colors[index]
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
            <AlertTriangle className="h-5 w-5 text-danger-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-danger-800">Error</h3>
              <p className="mt-1 text-sm text-danger-700">{error}</p>
              <button
                onClick={loadMetrics}
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
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Metrics</h1>
            <p className="mt-2 text-gray-600">
              Performance and detection statistics
            </p>
          </div>
          <button
            onClick={loadMetrics}
            className="btn btn-primary"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <AlertTriangle className="h-8 w-8 text-danger-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Findings</p>
              <p className="text-2xl font-semibold text-gray-900">
                {metrics?.findings.total_findings || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CheckCircle className="h-8 w-8 text-success-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Resolved</p>
              <p className="text-2xl font-semibold text-gray-900">
                {metrics?.findings.counts_by_status.RESOLVED || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Clock className="h-8 w-8 text-warning-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Acknowledged</p>
              <p className="text-2xl font-semibold text-gray-900">
                {metrics?.findings.counts_by_status.ACKNOWLEDGED || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Shield className="h-8 w-8 text-primary-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">New</p>
              <p className="text-2xl font-semibold text-gray-900">
                {metrics?.findings.counts_by_status.NEW || 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Status Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Findings by Status</h3>
          <div className="space-y-3">
            {Object.entries(metrics?.findings.counts_by_status || {}).map(([status, count]) => (
              <div key={status} className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className={`w-3 h-3 rounded-full mr-3 ${
                    status === 'NEW' ? 'bg-danger-500' :
                    status === 'ACKNOWLEDGED' ? 'bg-warning-500' :
                    status === 'RESOLVED' ? 'bg-success-500' :
                    'bg-gray-500'
                  }`} />
                  <span className="text-sm font-medium text-gray-900">
                    {status.replace(/_/g, ' ')}
                  </span>
                </div>
                <span className={`text-sm font-semibold ${getStatusColor(status)}`}>
                  {count}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Findings by Type</h3>
          <div className="space-y-3">
            {Object.entries(metrics?.findings.counts_by_kind || {}).map(([kind, count]) => (
              <div key={kind} className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className={`w-3 h-3 rounded-full mr-3 ${
                    kind === 'aws_access_key' ? 'bg-primary-500' :
                    kind === 'aws_secret_key' ? 'bg-danger-500' :
                    kind === 'github_token' ? 'bg-gray-500' :
                    kind === 'slack_webhook' ? 'bg-purple-500' :
                    kind === 'jwt_token' ? 'bg-indigo-500' :
                    kind === 'rsa_private_key' ? 'bg-red-500' :
                    kind === 'database_url' ? 'bg-green-500' :
                    kind === 'bearer_token' ? 'bg-blue-500' :
                    kind === 'high_entropy_string' ? 'bg-yellow-500' :
                    'bg-gray-500'
                  }`} />
                  <span className="text-sm font-medium text-gray-900">
                    {kind.replace(/_/g, ' ').toUpperCase()}
                  </span>
                </div>
                <span className={`text-sm font-semibold ${getKindColor(kind)}`}>
                  {count}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Agent Status */}
      <div className="card p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Agent Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div>
            <p className="text-sm font-medium text-gray-500">Status</p>
            <p className="text-lg font-semibold text-gray-900">
              {metrics?.agent_status.running ? 'Running' : 'Stopped'}
            </p>
          </div>
          
          <div>
            <p className="text-sm font-medium text-gray-500">Last Scan</p>
            <p className="text-lg font-semibold text-gray-900">
              {metrics?.last_scan_at 
                ? format(new Date(metrics.last_scan_at), 'MMM d, yyyy HH:mm')
                : 'Never'
              }
            </p>
          </div>
          
          <div>
            <p className="text-sm font-medium text-gray-500">Repository</p>
            <p className="text-lg font-semibold text-gray-900">
              {metrics?.agent_status.config.github_repo || 'Not configured'}
            </p>
          </div>
        </div>
        
        <div className="mt-6">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Registered Plugins</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Detectors</p>
              <div className="mt-1 space-y-1">
                {metrics?.agent_status.registered_plugins.detectors.map((detector) => (
                  <span key={detector} className="inline-block bg-primary-100 text-primary-800 text-xs px-2 py-1 rounded-full mr-1">
                    {detector}
                  </span>
                ))}
              </div>
            </div>
            
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Connectors</p>
              <div className="mt-1 space-y-1">
                {metrics?.agent_status.registered_plugins.connectors.map((connector) => (
                  <span key={connector} className="inline-block bg-success-100 text-success-800 text-xs px-2 py-1 rounded-full mr-1">
                    {connector}
                  </span>
                ))}
              </div>
            </div>
            
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Remediation</p>
              <div className="mt-1 space-y-1">
                {metrics?.agent_status.registered_plugins.remediation_handlers.map((handler) => (
                  <span key={handler} className="inline-block bg-warning-100 text-warning-800 text-xs px-2 py-1 rounded-full mr-1">
                    {handler}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Metrics
