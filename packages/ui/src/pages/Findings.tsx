import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { 
  AlertTriangle, 
  Search, 
  ChevronDown, 
  Shield,
  Clock,
  FileText
} from 'lucide-react'
import api from '../services/api'

interface Finding {
  id: string
  type: string
  severity: string
  confidence: number
  repo: string
  file_path: string
  start_line: number
  end_line: number
  description: string
  remediation_text: string
  created_at: string
}

const Findings: React.FC = () => {
  const [findings, setFindings] = useState<Finding[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null)
  const [filters, setFilters] = useState({
    repo: '',
    severity: '',
    type: '',
    search: ''
  })

  useEffect(() => {
    fetchFindings()
  }, [filters])

  const fetchFindings = async () => {
    try {
      const params = new URLSearchParams()
      if (filters.repo) params.append('repo', filters.repo)
      if (filters.severity) params.append('severity', filters.severity)
      if (filters.type) params.append('finding_type', filters.type)

      const response = await api.get(`/api/findings?${params.toString()}`)
      setFindings(response.data)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return 'bg-red-100 text-red-800'
      case 'HIGH': return 'bg-orange-100 text-orange-800'
      case 'MEDIUM': return 'bg-yellow-100 text-yellow-800'
      case 'LOW': return 'bg-green-100 text-green-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return '🔴'
      case 'HIGH': return '🟠'
      case 'MEDIUM': return '🟡'
      case 'LOW': return '🟢'
      default: return '⚪'
    }
  }

  const filteredFindings = findings.filter(finding => {
    if (filters.search) {
      const searchLower = filters.search.toLowerCase()
      return (
        finding.type.toLowerCase().includes(searchLower) ||
        finding.description.toLowerCase().includes(searchLower) ||
        finding.file_path.toLowerCase().includes(searchLower) ||
        finding.repo.toLowerCase().includes(searchLower)
      )
    }
    return true
  })

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

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Security Findings</h1>
        <Link
          to="/"
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          New Scan
        </Link>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={filters.search}
                onChange={(e) => setFilters({...filters, search: e.target.value})}
                placeholder="Search findings..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Repository</label>
            <input
              type="text"
              value={filters.repo}
              onChange={(e) => setFilters({...filters, repo: e.target.value})}
              placeholder="Filter by repo..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Severity</label>
            <select
              value={filters.severity}
              onChange={(e) => setFilters({...filters, severity: e.target.value})}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Type</label>
            <input
              type="text"
              value={filters.type}
              onChange={(e) => setFilters({...filters, type: e.target.value})}
              placeholder="Filter by type..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>
      </div>

      {/* Findings Table */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="px-6 py-4 border-b">
          <h3 className="text-lg font-semibold text-gray-900">
            {filteredFindings.length} Finding{filteredFindings.length !== 1 ? 's' : ''}
          </h3>
        </div>
        
        {filteredFindings.length === 0 ? (
          <div className="px-6 py-12 text-center">
            <Shield className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No findings found</h3>
            <p className="text-gray-500">Try adjusting your filters or start a new scan.</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredFindings.map((finding) => (
              <div
                key={finding.id}
                className="px-6 py-4 hover:bg-gray-50 cursor-pointer"
                onClick={() => setSelectedFinding(finding)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      <span className="text-2xl">{getSeverityIcon(finding.severity)}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <h4 className="text-sm font-medium text-gray-900 truncate">
                          {finding.type.replace('_', ' ').toUpperCase()}
                        </h4>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSeverityColor(finding.severity)}`}>
                          {finding.severity}
                        </span>
                        <span className="text-xs text-gray-500">
                          {Math.round(finding.confidence * 100)}% confidence
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{finding.description}</p>
                      <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                        <span className="flex items-center">
                          <FileText className="w-3 h-3 mr-1" />
                          {finding.file_path}:{finding.start_line}
                        </span>
                        <span className="flex items-center">
                          <Shield className="w-3 h-3 mr-1" />
                          {finding.repo}
                        </span>
                        <span className="flex items-center">
                          <Clock className="w-3 h-3 mr-1" />
                          {new Date(finding.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                      View Details
                    </button>
                    <ChevronDown className="w-4 h-4 text-gray-400" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Finding Detail Modal */}
      {selectedFinding && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="px-6 py-4 border-b">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">Finding Details</h3>
                <button
                  onClick={() => setSelectedFinding(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
            </div>
            
            <div className="px-6 py-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Type</label>
                  <p className="text-sm text-gray-900">{selectedFinding.type.replace('_', ' ').toUpperCase()}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Severity</label>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSeverityColor(selectedFinding.severity)}`}>
                    {selectedFinding.severity}
                  </span>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Confidence</label>
                  <p className="text-sm text-gray-900">{Math.round(selectedFinding.confidence * 100)}%</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Repository</label>
                  <p className="text-sm text-gray-900">{selectedFinding.repo}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">File</label>
                  <p className="text-sm text-gray-900">{selectedFinding.file_path}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Line</label>
                  <p className="text-sm text-gray-900">{selectedFinding.start_line}-{selectedFinding.end_line}</p>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <p className="text-sm text-gray-900 mt-1">{selectedFinding.description}</p>
              </div>

              {selectedFinding.remediation_text && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Remediation</label>
                  <div className="mt-1 p-3 bg-blue-50 rounded-md">
                    <p className="text-sm text-blue-800">{selectedFinding.remediation_text}</p>
                  </div>
                </div>
              )}

              <div className="flex justify-end space-x-3 pt-4 border-t">
                <button
                  onClick={() => setSelectedFinding(null)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Close
                </button>
                <button className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700">
                  Generate Patch
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Findings