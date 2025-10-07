import React, { useState, useEffect } from 'react'
import { 
  Search, 
  RefreshCw, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  Eye,
  Shield,
  Key,
  Database,
  Globe,
  Lock,
  AlertCircle,
  Info,
  ExternalLink,
  Copy,
  RotateCcw
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

  // Group findings by repository
  const groupFindingsByRepo = (findings: Finding[]) => {
    const grouped = findings.reduce((acc, finding) => {
      const repo = finding.repo
      if (!acc[repo]) {
        acc[repo] = []
      }
      acc[repo].push(finding)
      return acc
    }, {} as Record<string, Finding[]>)
    
    return Object.entries(grouped).map(([repo, repoFindings]) => ({
      repo,
      findings: repoFindings,
      count: repoFindings.length
    }))
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

  const getSecretTypeInfo = (kind: string) => {
    const typeInfo = {
      'aws_access_key': {
        icon: <Key className="h-5 w-5" />,
        title: 'AWS Access Key',
        description: 'Amazon Web Services access key for API authentication',
        risk: 'HIGH',
        impact: 'Full AWS account access, potential data breach, service disruption',
        remediation: [
          'Immediately rotate the access key in AWS IAM console',
          'Review CloudTrail logs for unauthorized usage',
          'Implement least-privilege access policies',
          'Enable MFA for all AWS accounts'
        ],
        prevention: [
          'Use IAM roles instead of access keys when possible',
          'Implement key rotation policies',
          'Monitor access key usage with CloudTrail',
          'Use AWS Secrets Manager for key storage'
        ]
      },
      'aws_secret_key': {
        icon: <Lock className="h-5 w-5" />,
        title: 'AWS Secret Key',
        description: 'Amazon Web Services secret access key (paired with access key)',
        risk: 'CRITICAL',
        impact: 'Full AWS account compromise, data exfiltration, service takeover',
        remediation: [
          'Immediately rotate the secret key in AWS IAM',
          'Revoke all sessions using this key',
          'Audit all AWS resources for unauthorized changes',
          'Notify security team and stakeholders'
        ],
        prevention: [
          'Never commit secrets to version control',
          'Use environment variables or secret managers',
          'Implement pre-commit hooks to detect secrets',
          'Regular security training for developers'
        ]
      },
      'github_token': {
        icon: <Globe className="h-5 w-5" />,
        title: 'GitHub Personal Access Token',
        description: 'GitHub API token for repository access and automation',
        risk: 'HIGH',
        impact: 'Repository access, code modification, CI/CD pipeline compromise',
        remediation: [
          'Revoke the token in GitHub Settings > Developer settings',
          'Review repository access logs',
          'Check for unauthorized commits or pull requests',
          'Rotate any dependent service tokens'
        ],
        prevention: [
          'Use fine-grained personal access tokens',
          'Implement token expiration policies',
          'Use GitHub Apps instead of personal tokens',
          'Regular token audit and rotation'
        ]
      },
      'slack_webhook': {
        icon: <Globe className="h-5 w-5" />,
        title: 'Slack Webhook URL',
        description: 'Slack incoming webhook for posting messages to channels',
        risk: 'MEDIUM',
        impact: 'Spam messages, channel disruption, potential data leakage',
        remediation: [
          'Regenerate the webhook URL in Slack app settings',
          'Review message history for unauthorized posts',
          'Update all applications using this webhook',
          'Implement webhook authentication'
        ],
        prevention: [
          'Use Slack apps with proper permissions',
          'Implement webhook validation',
          'Regular webhook audit and cleanup',
          'Use environment variables for webhook URLs'
        ]
      },
      'jwt_token': {
        icon: <Shield className="h-5 w-5" />,
        title: 'JWT Token',
        description: 'JSON Web Token for authentication and authorization',
        risk: 'HIGH',
        impact: 'Authentication bypass, privilege escalation, session hijacking',
        remediation: [
          'Invalidate the JWT token immediately',
          'Force re-authentication for all users',
          'Review JWT signing key security',
          'Implement token blacklisting'
        ],
        prevention: [
          'Use short-lived JWT tokens',
          'Implement proper token validation',
          'Use secure signing algorithms (RS256)',
          'Regular token rotation'
        ]
      },
      'rsa_private_key': {
        icon: <Key className="h-5 w-5" />,
        title: 'RSA Private Key',
        description: 'RSA private key for cryptographic operations',
        risk: 'CRITICAL',
        impact: 'Encryption compromise, digital signature forgery, secure communication breach',
        remediation: [
          'Immediately revoke the associated certificate',
          'Generate new key pair and certificate',
          'Update all systems using this key',
          'Audit all encrypted data and signatures'
        ],
        prevention: [
          'Use hardware security modules (HSM)',
          'Implement key rotation policies',
          'Store keys in secure key management systems',
          'Never commit private keys to version control'
        ]
      },
      'database_url': {
        icon: <Database className="h-5 w-5" />,
        title: 'Database Connection String',
        description: 'Database connection URL with credentials',
        risk: 'HIGH',
        impact: 'Database access, data breach, data manipulation',
        remediation: [
          'Change database passwords immediately',
          'Review database access logs',
          'Check for unauthorized data access',
          'Update all application configurations'
        ],
        prevention: [
          'Use connection string encryption',
          'Implement database access controls',
          'Use environment variables for credentials',
          'Regular database security audits'
        ]
      },
      'bearer_token': {
        icon: <Shield className="h-5 w-5" />,
        title: 'Bearer Token',
        description: 'OAuth bearer token for API authentication',
        risk: 'MEDIUM',
        impact: 'API access, data retrieval, service impersonation',
        remediation: [
          'Revoke the bearer token',
          'Review API access logs',
          'Check for unauthorized API calls',
          'Update client applications'
        ],
        prevention: [
          'Use short-lived tokens',
          'Implement token refresh mechanisms',
          'Monitor token usage patterns',
          'Use secure token storage'
        ]
      },
      'high_entropy_string': {
        icon: <AlertCircle className="h-5 w-5" />,
        title: 'High Entropy String',
        description: 'Random-looking string that might be a secret',
        risk: 'LOW',
        impact: 'Potential secret exposure, security risk if confirmed',
        remediation: [
          'Verify if this is actually a secret',
          'Check if it\'s a false positive',
          'If confirmed, follow appropriate remediation',
          'Update detection rules if needed'
        ],
        prevention: [
          'Implement proper secret management',
          'Use secure random generators',
          'Regular security training',
          'Code review for secret handling'
        ]
      }
    }
    
    return typeInfo[kind as keyof typeof typeInfo] || {
      icon: <AlertTriangle className="h-5 w-5" />,
      title: 'Unknown Secret Type',
      description: 'Unidentified secret type',
      risk: 'UNKNOWN',
      impact: 'Unknown security impact',
      remediation: ['Investigate the secret type', 'Determine appropriate remediation'],
      prevention: ['Implement general security practices']
    }
  }

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'CRITICAL': return 'text-red-600 bg-red-100'
      case 'HIGH': return 'text-orange-600 bg-orange-100'
      case 'MEDIUM': return 'text-yellow-600 bg-yellow-100'
      case 'LOW': return 'text-blue-600 bg-blue-100'
      default: return 'text-gray-600 bg-gray-100'
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
        <div className="space-y-8">
          {groupFindingsByRepo(findings).map((repoGroup) => (
            <div key={repoGroup.repo} className="space-y-4">
              {/* Repository Header */}
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-primary-100 rounded-lg">
                      <Database className="h-5 w-5 text-primary-600" />
                    </div>
                    <div>
                      <h2 className="text-xl font-semibold text-gray-900">{repoGroup.repo}</h2>
                      <p className="text-sm text-gray-600">{repoGroup.count} security findings</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="badge bg-primary-100 text-primary-800">
                      {repoGroup.count} findings
                    </span>
                  </div>
                </div>
              </div>
              
              {/* Repository Findings */}
              <div className="space-y-4">
                {repoGroup.findings.map((finding) => {
            const secretInfo = getSecretTypeInfo(finding.kind)
            return (
              <div key={finding.id} className="card p-6 border-l-4 border-l-primary-500">
                {/* Header Section */}
                <div className="flex items-start justify-between mb-6">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-primary-100 rounded-lg">
                      {secretInfo.icon}
                    </div>
                    <div>
                      <h3 className="text-xl font-semibold text-gray-900">
                        {secretInfo.title}
                      </h3>
                      <p className="text-sm text-gray-600">{secretInfo.description}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <span className={`badge ${getStatusColor(finding.status)}`}>
                      {getStatusIcon(finding.status)}
                      <span className="ml-1">{finding.status}</span>
                    </span>
                    <span className={`badge ${getRiskColor(secretInfo.risk)}`}>
                      {secretInfo.risk} RISK
                    </span>
                    <span className={`text-sm font-medium ${getConfidenceColor(finding.confidence)}`}>
                      {Math.round(finding.confidence * 100)}% confidence
                    </span>
                  </div>
                </div>

                {/* Risk Assessment */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div className="flex items-center mb-2">
                      <AlertTriangle className="h-5 w-5 text-red-600 mr-2" />
                      <h4 className="font-semibold text-red-800">Security Impact</h4>
                    </div>
                    <p className="text-sm text-red-700">{secretInfo.impact}</p>
                  </div>
                  
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-center mb-2">
                      <Info className="h-5 w-5 text-blue-600 mr-2" />
                      <h4 className="font-semibold text-blue-800">Detection Details</h4>
                    </div>
                    <div className="space-y-1 text-sm text-blue-700">
                      <p><span className="font-medium">File:</span> {finding.file_path}</p>
                      <p><span className="font-medium">Lines:</span> {finding.line_start}-{finding.line_end}</p>
                      <p><span className="font-medium">Repository:</span> {finding.repo}</p>
                      <p><span className="font-medium">Commit:</span> {finding.commit_sha.substring(0, 8)}</p>
                    </div>
                  </div>
                </div>

                {/* Secret Preview */}
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-6">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-gray-800">Secret Preview</h4>
                    <button
                      onClick={() => navigator.clipboard.writeText(finding.preview_masked)}
                      className="flex items-center text-sm text-gray-600 hover:text-gray-800"
                    >
                      <Copy className="h-4 w-4 mr-1" />
                      Copy
                    </button>
                  </div>
                  <code className="text-sm font-mono bg-white p-2 rounded border block">
                    {finding.preview_masked}
                  </code>
                </div>

                {/* Remediation Steps */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                  <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                    <div className="flex items-center mb-3">
                      <RotateCcw className="h-5 w-5 text-orange-600 mr-2" />
                      <h4 className="font-semibold text-orange-800">Immediate Remediation</h4>
                    </div>
                    <ul className="space-y-2 text-sm text-orange-700">
                      {secretInfo.remediation.map((step: string, index: number) => (
                        <li key={index} className="flex items-start">
                          <span className="inline-block w-2 h-2 bg-orange-400 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                          {step}
                        </li>
                      ))}
                    </ul>
                  </div>
                  
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div className="flex items-center mb-3">
                      <Shield className="h-5 w-5 text-green-600 mr-2" />
                      <h4 className="font-semibold text-green-800">Prevention Measures</h4>
                    </div>
                    <ul className="space-y-2 text-sm text-green-700">
                      {secretInfo.prevention.map((step: string, index: number) => (
                        <li key={index} className="flex items-start">
                          <span className="inline-block w-2 h-2 bg-green-400 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                          {step}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Metadata */}
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-6">
                  <h4 className="font-semibold text-gray-800 mb-3">Detection Metadata</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="font-medium text-gray-600">First Detected:</span>
                      <p className="text-gray-900">{format(new Date(finding.first_seen_at), 'MMM d, yyyy HH:mm')}</p>
                    </div>
                    <div>
                      <span className="font-medium text-gray-600">Last Seen:</span>
                      <p className="text-gray-900">{format(new Date(finding.last_seen_at), 'MMM d, yyyy HH:mm')}</p>
                    </div>
                    <div>
                      <span className="font-medium text-gray-600">Fingerprint:</span>
                      <p className="text-gray-900 font-mono text-xs">{finding.fingerprint.substring(0, 16)}...</p>
                    </div>
                  </div>
                </div>

                {/* Notes */}
                {finding.notes && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
                    <h4 className="font-semibold text-yellow-800 mb-2">Notes</h4>
                    <p className="text-sm text-yellow-700">{finding.notes}</p>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => window.open(`https://github.com/${finding.repo}/blob/main/${finding.file_path}#L${finding.line_start}`, '_blank')}
                      className="btn btn-secondary flex items-center"
                    >
                      <ExternalLink className="h-4 w-4 mr-2" />
                      View in GitHub
                    </button>
                    <button
                      onClick={() => navigator.clipboard.writeText(finding.file_path)}
                      className="btn btn-secondary flex items-center"
                    >
                      <Copy className="h-4 w-4 mr-2" />
                      Copy File Path
                    </button>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    {finding.status === 'NEW' && (
                      <button
                        onClick={() => handleStatusUpdate(finding.id, 'ACKNOWLEDGED')}
                        className="btn btn-primary"
                      >
                        Acknowledge
                      </button>
                    )}
                    {finding.status === 'ACKNOWLEDGED' && (
                      <button
                        onClick={() => handleStatusUpdate(finding.id, 'RESOLVED')}
                        className="btn btn-success"
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
            )
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default Findings
