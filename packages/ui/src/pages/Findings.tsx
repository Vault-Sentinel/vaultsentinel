import React, { useState, useEffect } from 'react'
import { 
  Search, 
  RefreshCw, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  Eye
} from 'lucide-react'
import { getFindings, updateFinding } from '../services/api'
import { Finding } from '../types'
import { format } from 'date-fns'

const Findings: React.FC = () => {
  const [findings, setFindings] = useState<Finding[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filters, setFilters] = useState({
    status: '',
    kind: '',
    repo: '',
    search: ''
  })
  const [pagination, setPagination] = useState({
    limit: 20,
    offset: 0,
    total: 0
  })

  useEffect(() => {
    loadFindings()
  }, [filters, pagination.offset])

  const loadFindings = async () => {
    try {
      setLoading(true)
      const response = await getFindings({
        ...filters,
        limit: pagination.limit,
        offset: pagination.offset
      })
      
      setFindings((response as any).findings || [])
      setPagination(prev => ({ ...prev, total: response.total || 0 }))
      setError(null)
    } catch (err) {
      setError('Failed to load findings')
      console.error('Findings error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleStatusUpdate = async (id: string, status: string) => {
    try {
      await updateFinding(id, { status })
      loadFindings()
    } catch (err) {
      console.error('Failed to update finding:', err)
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

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'NEW':
        return <AlertTriangle className="h-4 w-4" />
      case 'ACKNOWLEDGED':
        return <Clock className="h-4 w-4" />
      case 'RESOLVED':
        return <CheckCircle className="h-4 w-4" />
      default:
        return <Eye className="h-4 w-4" />
    }
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Findings</h1>
        <p className="mt-2 text-gray-600">
          Manage and review detected secrets
        </p>
      </div>

      {/* Filters */}
      <div className="card p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Status
            </label>
            <select
              value={filters.status}
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            >
              <option value="">All Status</option>
              <option value="NEW">New</option>
              <option value="ACKNOWLEDGED">Acknowledged</option>
              <option value="RESOLVED">Resolved</option>
              <option value="FALSE_POSITIVE">False Positive</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Secret Type
            </label>
            <select
              value={filters.kind}
              onChange={(e) => setFilters(prev => ({ ...prev, kind: e.target.value }))}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            >
              <option value="">All Types</option>
              <option value="aws_access_key">AWS Access Key</option>
              <option value="aws_secret_key">AWS Secret Key</option>
              <option value="github_token">GitHub Token</option>
              <option value="slack_webhook">Slack Webhook</option>
              <option value="jwt_token">JWT Token</option>
              <option value="rsa_private_key">RSA Private Key</option>
              <option value="database_url">Database URL</option>
              <option value="bearer_token">Bearer Token</option>
              <option value="high_entropy_string">High Entropy String</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Repository
            </label>
            <input
              type="text"
              value={filters.repo}
              onChange={(e) => setFilters(prev => ({ ...prev, repo: e.target.value }))}
              placeholder="Filter by repository"
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                value={filters.search}
                onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                placeholder="Search findings..."
                className="w-full pl-10 rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
              />
            </div>
          </div>
        </div>
        
        <div className="mt-4 flex justify-between items-center">
          <button
            onClick={loadFindings}
            className="btn btn-primary"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </button>
          
          <div className="text-sm text-gray-500">
            Showing {findings.length} of {pagination.total} findings
          </div>
        </div>
      </div>

      {/* Findings List */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      ) : error ? (
        <div className="bg-danger-50 border border-danger-200 rounded-md p-4">
          <div className="flex">
            <AlertTriangle className="h-5 w-5 text-danger-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-danger-800">Error</h3>
              <p className="mt-1 text-sm text-danger-700">{error}</p>
            </div>
          </div>
        </div>
      ) : findings.length === 0 ? (
        <div className="card p-12 text-center">
          <AlertTriangle className="h-12 w-12 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No findings found</h3>
          <p className="text-gray-500">Try adjusting your filters or check back later.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {findings.map((finding) => (
            <div key={finding.id} className="card p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-3">
                    <span className="text-lg font-medium text-gray-900">
                      {finding.kind.replace(/_/g, ' ').toUpperCase()}
                    </span>
                    <span className={`badge ${getStatusColor(finding.status)}`}>
                      {getStatusIcon(finding.status)}
                      <span className="ml-1">{finding.status}</span>
                    </span>
                    <span className={`text-sm font-medium ${getConfidenceColor(finding.confidence)}`}>
                      {Math.round(finding.confidence * 100)}% confidence
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                      <p className="text-sm text-gray-600">
                        <span className="font-medium">File:</span> {finding.file_path}
                      </p>
                      <p className="text-sm text-gray-600">
                        <span className="font-medium">Lines:</span> {finding.line_start}-{finding.line_end}
                      </p>
                      <p className="text-sm text-gray-600">
                        <span className="font-medium">Repository:</span> {finding.repo}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">
                        <span className="font-medium">Preview:</span> {finding.preview_masked}
                      </p>
                      <p className="text-sm text-gray-600">
                        <span className="font-medium">Commit:</span> {finding.commit_sha.substring(0, 8)}
                      </p>
                      <p className="text-sm text-gray-600">
                        <span className="font-medium">First seen:</span>{' '}
                        {format(new Date(finding.first_seen_at), 'MMM d, yyyy HH:mm')}
                      </p>
                    </div>
                  </div>
                  
                  {finding.notes && (
                    <div className="mt-3 p-3 bg-gray-50 rounded-md">
                      <p className="text-sm text-gray-700">
                        <span className="font-medium">Notes:</span> {finding.notes}
                      </p>
                    </div>
                  )}
                </div>
                
                <div className="flex items-center space-x-2 ml-4">
                  {finding.status === 'NEW' && (
                    <button
                      onClick={() => handleStatusUpdate(finding.id, 'ACKNOWLEDGED')}
                      className="btn btn-secondary"
                    >
                      Acknowledge
                    </button>
                  )}
                  {finding.status === 'ACKNOWLEDGED' && (
                    <button
                      onClick={() => handleStatusUpdate(finding.id, 'RESOLVED')}
                      className="btn btn-primary"
                    >
                      Mark Resolved
                    </button>
                  )}
                  <button
                    onClick={() => handleStatusUpdate(finding.id, 'FALSE_POSITIVE')}
                    className="btn btn-secondary"
                  >
                    False Positive
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default Findings
