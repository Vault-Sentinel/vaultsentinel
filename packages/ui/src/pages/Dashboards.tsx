import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { 
  Shield, 
  AlertTriangle, 
  TrendingUp, 
  FileText, 
  GitBranch,
  Activity
} from 'lucide-react'

interface DashboardStats {
  total_scans: number
  total_findings: number
  severity_breakdown: Record<string, number>
  top_secret_types: Record<string, number>
  recent_scans: Array<{
    id: string
    repo_url: string
    status: string
    risk_score: number
    started_at: string
  }>
}

const Dashboards: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchDashboardStats()
  }, [])

  const fetchDashboardStats = async () => {
    try {
      const response = await fetch('/api/dashboard/stats')
      if (!response.ok) {
        throw new Error('Failed to fetch dashboard stats')
      }
      const data = await response.json()
      setStats(data)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }


  const getRiskScoreColor = (score: number) => {
    if (score >= 80) return 'text-red-600'
    if (score >= 60) return 'text-orange-600'
    if (score >= 40) return 'text-yellow-600'
    return 'text-green-600'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <AlertTriangle className="w-5 h-5 text-red-600 mr-2" />
          <span className="text-red-800">{error}</span>
        </div>
      </div>
    )
  }

  if (!stats) {
    return <div>No data available</div>
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Security Dashboard</h1>
        <Link
          to="/"
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          New Scan
        </Link>
      </div>

      {/* KPI Tiles */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                <FileText className="w-5 h-5 text-blue-600" />
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Scans</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.total_scans}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-red-600" />
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Findings</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.total_findings}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                <Shield className="w-5 h-5 text-red-600" />
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Critical</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.severity_breakdown.CRITICAL || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-orange-600" />
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">High</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.severity_breakdown.HIGH || 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Severity Breakdown */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Findings by Severity</h3>
          <div className="space-y-3">
            {Object.entries(stats.severity_breakdown).map(([severity, count]) => (
              <div key={severity} className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className={`w-3 h-3 rounded-full mr-3 ${
                    severity === 'CRITICAL' ? 'bg-red-500' :
                    severity === 'HIGH' ? 'bg-orange-500' :
                    severity === 'MEDIUM' ? 'bg-yellow-500' : 'bg-green-500'
                  }`}></div>
                  <span className="text-sm font-medium text-gray-900">{severity}</span>
                </div>
                <span className="text-sm text-gray-500">{count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Top Secret Types */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Secret Types</h3>
          <div className="space-y-3">
            {Object.entries(stats.top_secret_types).slice(0, 5).map(([type, count]) => (
              <div key={type} className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-900">{type.replace('_', ' ').toUpperCase()}</span>
                <span className="text-sm text-gray-500">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Scans */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="px-6 py-4 border-b">
          <h3 className="text-lg font-semibold text-gray-900">Recent Scans</h3>
        </div>
        <div className="divide-y divide-gray-200">
          {stats.recent_scans.map((scan) => (
            <div key={scan.id} className="px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <GitBranch className="w-5 h-5 text-gray-400 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">{scan.repo_url}</p>
                    <p className="text-xs text-gray-500">
                      {new Date(scan.started_at).toLocaleString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    scan.status === 'done' ? 'bg-green-100 text-green-800' :
                    scan.status === 'running' ? 'bg-blue-100 text-blue-800' :
                    scan.status === 'error' ? 'bg-red-100 text-red-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {scan.status}
                  </span>
                  {scan.risk_score > 0 && (
                    <span className={`text-sm font-medium ${getRiskScoreColor(scan.risk_score)}`}>
                      Risk: {scan.risk_score.toFixed(1)}
                    </span>
                  )}
                  <Link
                    to={`/scans/${scan.id}/report`}
                    className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                  >
                    View Report
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link
          to="/findings"
          className="bg-white rounded-lg shadow-sm border p-6 hover:shadow-md transition-shadow"
        >
          <div className="flex items-center">
            <AlertTriangle className="w-8 h-8 text-red-600 mr-4" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">View Findings</h3>
              <p className="text-sm text-gray-500">Browse all security findings</p>
            </div>
          </div>
        </Link>

        <Link
          to="/mcp"
          className="bg-white rounded-lg shadow-sm border p-6 hover:shadow-md transition-shadow"
        >
          <div className="flex items-center">
            <Activity className="w-8 h-8 text-blue-600 mr-4" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Quick Classify</h3>
              <p className="text-sm text-gray-500">Test text classification</p>
            </div>
          </div>
        </Link>

        <Link
          to="/"
          className="bg-white rounded-lg shadow-sm border p-6 hover:shadow-md transition-shadow"
        >
          <div className="flex items-center">
            <Shield className="w-8 h-8 text-green-600 mr-4" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">New Scan</h3>
              <p className="text-sm text-gray-500">Start a new repository scan</p>
            </div>
          </div>
        </Link>
      </div>
    </div>
  )
}

export default Dashboards
