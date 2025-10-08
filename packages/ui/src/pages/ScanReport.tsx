import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { 
  AlertTriangle, 
  Clock, 
  FileText,
  Download,
  Copy,
  GitBranch
} from 'lucide-react'

interface ScanReport {
  scan: {
    id: string
    repo_url: string
    branch: string
    status: string
    risk_score: number
    total_files: number
    scanned_files: number
    started_at: string
    finished_at: string
    duration_ms: number
  }
  findings: Array<{
    id: string
    type: string
    severity: string
    confidence: number
    file_path: string
    start_line: number
    end_line: number
    description: string
    remediation_text: string
  }>
}

const ScanReport: React.FC = () => {
  const { scanId } = useParams<{ scanId: string }>()
  const [report, setReport] = useState<ScanReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (scanId) {
      fetchScanReport()
    }
  }, [scanId])

  const fetchScanReport = async () => {
    try {
      // First get the scan details
      const scanResponse = await fetch(`/api/scans/${scanId}/details`)
      if (!scanResponse.ok) {
        throw new Error('Failed to fetch scan details')
      }
      const scanData = await scanResponse.json()
      
      // Then get the findings
      const findingsResponse = await fetch(`/api/findings?scan_id=${scanId}`)
      if (!findingsResponse.ok) {
        throw new Error('Failed to fetch findings')
      }
      const findingsData = await findingsResponse.json()
      
      // Get the HTML report
      const reportResponse = await fetch(`/api/scans/${scanId}/report`)
      if (!reportResponse.ok) {
        throw new Error('Failed to fetch scan report')
      }
      
      // Extract scan details from the HTML or use the API data
      setReport({
        scan: {
          id: scanId!,
          repo_url: scanData.repo_url || 'Unknown',
          branch: scanData.branch || 'main',
          status: scanData.status || 'unknown',
          risk_score: scanData.risk_score || 0,
          total_files: scanData.total_files || 0,
          scanned_files: scanData.scanned_files || 0,
          started_at: scanData.started_at || new Date().toISOString(),
          finished_at: scanData.finished_at || new Date().toISOString(),
          duration_ms: scanData.duration_ms || 0
        },
        findings: findingsData.findings || []
      })
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

  const getRiskScoreColor = (score: number) => {
    if (score >= 80) return 'text-red-600'
    if (score >= 60) return 'text-orange-600'
    if (score >= 40) return 'text-yellow-600'
    return 'text-green-600'
  }

  const getRiskScoreLabel = (score: number) => {
    if (score >= 80) return 'Critical Risk'
    if (score >= 60) return 'High Risk'
    if (score >= 40) return 'Medium Risk'
    return 'Low Risk'
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

  if (!report) {
    return <div>Report not found</div>
  }

  const severityCounts = report.findings.reduce((acc, finding) => {
    acc[finding.severity] = (acc[finding.severity] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Scan Report</h1>
          <p className="text-gray-600 mt-1">{report.scan.repo_url}</p>
        </div>
        <div className="flex space-x-3">
          <Link
            to="/dashboards"
            className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700"
          >
            Back to Dashboard
          </Link>
          <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
            <Download className="w-4 h-4 mr-2 inline" />
            Download PDF
          </button>
        </div>
      </div>

      {/* Scan Overview */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Scan Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div>
            <dt className="text-sm font-medium text-gray-500">Repository</dt>
            <dd className="mt-1 text-sm text-gray-900 flex items-center">
              <GitBranch className="w-4 h-4 mr-2" />
              {report.scan.repo_url}
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Branch</dt>
            <dd className="mt-1 text-sm text-gray-900">{report.scan.branch}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Scan Duration</dt>
            <dd className="mt-1 text-sm text-gray-900 flex items-center">
              <Clock className="w-4 h-4 mr-2" />
              {(report.scan.duration_ms / 1000).toFixed(1)}s
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Files Scanned</dt>
            <dd className="mt-1 text-sm text-gray-900 flex items-center">
              <FileText className="w-4 h-4 mr-2" />
              {report.scan.scanned_files}
            </dd>
          </div>
        </div>
      </div>

      {/* Risk Score */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Risk Assessment</h2>
        <div className="flex items-center justify-center">
          <div className="relative w-32 h-32">
            <svg className="w-32 h-32 transform -rotate-90" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="40" stroke="#e5e7eb" strokeWidth="8" fill="none"/>
              <circle 
                cx="50" 
                cy="50" 
                r="40" 
                stroke={report.scan.risk_score >= 80 ? "#dc2626" : report.scan.risk_score >= 60 ? "#ea580c" : report.scan.risk_score >= 40 ? "#d97706" : "#16a34a"}
                strokeWidth="8" 
                fill="none" 
                strokeDasharray={`${report.scan.risk_score * 2.51}`}
                strokeDashoffset="0" 
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-2xl font-bold text-gray-900">{report.scan.risk_score.toFixed(1)}</span>
            </div>
          </div>
          <div className="ml-6">
            <h3 className="text-lg font-semibold text-gray-900">Risk Score</h3>
            <p className={`text-sm font-medium ${getRiskScoreColor(report.scan.risk_score)}`}>
              {getRiskScoreLabel(report.scan.risk_score)}
            </p>
          </div>
        </div>
      </div>

      {/* KPI Tiles */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                <span className="text-red-600 font-semibold text-sm">C</span>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Critical</p>
              <p className="text-2xl font-semibold text-gray-900">{severityCounts.CRITICAL || 0}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
                <span className="text-orange-600 font-semibold text-sm">H</span>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">High</p>
              <p className="text-2xl font-semibold text-gray-900">{severityCounts.HIGH || 0}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                <span className="text-yellow-600 font-semibold text-sm">M</span>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Medium</p>
              <p className="text-2xl font-semibold text-gray-900">{severityCounts.MEDIUM || 0}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                <span className="text-green-600 font-semibold text-sm">L</span>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Low</p>
              <p className="text-2xl font-semibold text-gray-900">{severityCounts.LOW || 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Findings by Severity */}
      {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map(severity => {
        const severityFindings = report.findings.filter(f => f.severity === severity)
        if (severityFindings.length === 0) return null

        return (
          <div key={severity} className="bg-white rounded-lg shadow-sm border">
            <div className="px-6 py-4 border-b">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center">
                <span className={`w-3 h-3 rounded-full mr-3 ${
                  severity === 'CRITICAL' ? 'bg-red-500' :
                  severity === 'HIGH' ? 'bg-orange-500' :
                  severity === 'MEDIUM' ? 'bg-yellow-500' : 'bg-green-500'
                }`}></span>
                {severity} ({severityFindings.length})
              </h2>
            </div>
            <div className="divide-y divide-gray-200">
              {severityFindings.map((finding) => (
                <div key={finding.id} className="px-6 py-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center">
                        <h3 className="text-sm font-medium text-gray-900">{finding.type.replace('_', ' ').toUpperCase()}</h3>
                        <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSeverityColor(finding.severity)}`}>
                          {finding.severity}
                        </span>
                        <span className="ml-2 text-xs text-gray-500">Confidence: {Math.round(finding.confidence * 100)}%</span>
                      </div>
                      <p className="mt-1 text-sm text-gray-600">{finding.description}</p>
                      <p className="mt-2 text-sm text-gray-500">
                        <span className="font-medium">File:</span> {finding.file_path}:{finding.start_line}
                      </p>
                      {finding.remediation_text && (
                        <div className="mt-3 p-3 bg-blue-50 rounded-md">
                          <h4 className="text-sm font-medium text-blue-900">Remediation</h4>
                          <p className="mt-1 text-sm text-blue-800">{finding.remediation_text}</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )
      })}

      {/* Actions */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="px-6 py-4 border-b">
          <h2 className="text-lg font-semibold text-gray-900">Actions</h2>
        </div>
        <div className="px-6 py-4">
          <div className="flex flex-wrap gap-4">
            <button className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
              <Download className="w-4 h-4 mr-2" />
              Download PDF
            </button>
            <button className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
              <Download className="w-4 h-4 mr-2" />
              Download SARIF
            </button>
            <button className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
              <Copy className="w-4 h-4 mr-2" />
              Copy PR Body
            </button>
            <button className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
              <Copy className="w-4 h-4 mr-2" />
              Copy Commands
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ScanReport
