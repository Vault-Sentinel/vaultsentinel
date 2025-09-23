import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { 
  Shield, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  RefreshCw,
  ExternalLink
} from 'lucide-react'
import { getHealth, getFindings, getMetrics } from '../services/api'
import { Finding, HealthStatus, Metrics } from '../types'
import { format } from 'date-fns'

const Dashboard: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [recentFindings, setRecentFindings] = useState<Finding[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadDashboardData()
    const interval = setInterval(loadDashboardData, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      const [healthData, metricsData, findingsData] = await Promise.all([
        getHealth(),
        getMetrics(),
        getFindings({ limit: 10 })
      ])
      
      setHealth(healthData)
      setMetrics(metricsData)
      setRecentFindings((findingsData as any).findings || [])
      setError(null)
    } catch (err) {
      setError('Failed to load dashboard data')
      console.error('Dashboard error:', err)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'NEW':
        return 'text-danger-600 bg-danger-100'
      case 'ACKNOWLEDGED':
        return 'text-warning-600 bg-warning-100'
      case 'RESOLVED':
        return 'text-success-600 bg-success-100'
      case 'FALSE_POSITIVE':
        return 'text-gray-600 bg-gray-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-danger-600'
    if (confidence >= 0.5) return 'text-warning-600'
    return 'text-success-600'
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
                onClick={loadDashboardData}
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
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Continuous secrets shielding for your repositories
        </p>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Shield className="h-8 w-8 text-primary-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Agent Status</p>
              <p className="text-2xl font-semibold text-gray-900">
                {health?.agent_status.running ? 'Running' : 'Stopped'}
              </p>
            </div>
          </div>
        </div>

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
              <p className="text-sm font-medium text-gray-500">Last Scan</p>
              <p className="text-sm font-semibold text-gray-900">
                {metrics?.last_scan_at 
                  ? format(new Date(metrics.last_scan_at), 'MMM d, HH:mm')
                  : 'Never'
                }
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Findings */}
      <div className="card">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-medium text-gray-900">Recent Findings</h2>
            <div className="flex items-center space-x-2">
              <button
                onClick={loadDashboardData}
                className="btn btn-secondary"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </button>
              <Link to="/findings" className="btn btn-primary">
                View All
              </Link>
            </div>
          </div>
        </div>
        
        <div className="divide-y divide-gray-200">
          {recentFindings.length === 0 ? (
            <div className="p-6 text-center text-gray-500">
              <Shield className="h-12 w-12 mx-auto text-gray-400 mb-4" />
              <p>No findings detected</p>
            </div>
          ) : (
            recentFindings.map((finding) => (
              <div key={finding.id} className="p-6 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="text-sm font-medium text-gray-900">
                        {finding.kind}
                      </span>
                      <span className={`badge ${getStatusColor(finding.status)}`}>
                        {finding.status}
                      </span>
                      <span className={`text-sm font-medium ${getConfidenceColor(finding.confidence)}`}>
                        {Math.round(finding.confidence * 100)}% confidence
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-1">
                      <span className="font-medium">File:</span> {finding.file_path}
                    </p>
                    <p className="text-sm text-gray-600 mb-1">
                      <span className="font-medium">Preview:</span> {finding.preview_masked}
                    </p>
                    <p className="text-sm text-gray-500">
                      <span className="font-medium">First seen:</span>{' '}
                      {format(new Date(finding.first_seen_at), 'MMM d, yyyy HH:mm')}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Link
                      to={`/findings/${finding.id}`}
                      className="btn btn-secondary"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </Link>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

export default Dashboard
