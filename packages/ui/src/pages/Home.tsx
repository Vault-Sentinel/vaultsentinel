import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shield, Search, AlertTriangle, CheckCircle, Loader2 } from 'lucide-react'

const Home: React.FC = () => {
  const navigate = useNavigate()
  const [repoUrl, setRepoUrl] = useState('')
  const [branch, setBranch] = useState('main')
  const [isScanning, setIsScanning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const validateRepoUrl = (url: string): boolean => {
    const githubPattern = /^https:\/\/github\.com\/[^\/]+\/[^\/]+$/
    return githubPattern.test(url)
  }

  const handleScan = async () => {
    if (!validateRepoUrl(repoUrl)) {
      setError('Please enter a valid GitHub repository URL')
      return
    }

    setIsScanning(true)
    setError(null)

    try {
      const response = await fetch('/api/scans', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          repo_url: repoUrl,
          branch: branch,
          mode: 'full',
          include: ['**/*.py', '**/*.js', '**/*.env', '**/*.yml', '**/*.yaml', '**/*.json'],
          exclude: ['**/node_modules/**', '**/dist/**', '.git/**', '**/__pycache__/**'],
          max_files: 2000,
          max_bytes_per_file: 200000,
          timeout_sec: 120
        })
      })

      if (!response.ok) {
        throw new Error('Failed to start scan')
      }

      const data = await response.json()
      
      // Start polling for scan status
      pollScanStatus(data.scan_id)
    } catch (err: any) {
      setError(err.message)
      setIsScanning(false)
    }
  }

  const pollScanStatus = async (scanId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/api/scans/${scanId}/status`)
        const data = await response.json()

        if (data.status === 'done') {
          clearInterval(pollInterval)
          setIsScanning(false)
          // Navigate to report
          navigate(`/scans/${scanId}/report`)
        } else if (data.status === 'error') {
          clearInterval(pollInterval)
          setIsScanning(false)
          setError(data.message || 'Scan failed')
        }
      } catch (err) {
        console.error('Error polling scan status:', err)
      }
    }, 2000) // Poll every 2 seconds
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center">
          <div className="flex justify-center mb-8">
            <div className="bg-white rounded-full p-4 shadow-lg">
              <Shield className="w-16 h-16 text-blue-600" />
            </div>
          </div>
          
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            Scan a public GitHub repo for{' '}
            <span className="text-blue-600">secrets & code risks</span>
          </h1>
          
          <p className="text-xl text-gray-600 mb-12 max-w-3xl mx-auto">
            VaultSentinel uses hybrid detection (regex + AI) to find secrets, vulnerabilities, 
            and security risks in your repositories. Get detailed reports with remediation guidance.
          </p>
        </div>

        {/* Scan Form */}
        <div className="max-w-2xl mx-auto">
          <div className="bg-white rounded-lg shadow-xl p-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">Start a Security Scan</h2>
            
            <div className="space-y-6">
              <div>
                <label htmlFor="repo-url" className="block text-sm font-medium text-gray-700 mb-2">
                  Repository URL
                </label>
                <input
                  type="url"
                  id="repo-url"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  placeholder="https://github.com/owner/repo"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={isScanning}
                />
                {repoUrl && !validateRepoUrl(repoUrl) && (
                  <p className="mt-1 text-sm text-red-600">Please enter a valid GitHub repository URL</p>
                )}
              </div>

              <div>
                <label htmlFor="branch" className="block text-sm font-medium text-gray-700 mb-2">
                  Branch (optional)
                </label>
                <input
                  type="text"
                  id="branch"
                  value={branch}
                  onChange={(e) => setBranch(e.target.value)}
                  placeholder="main"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={isScanning}
                />
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-center">
                    <AlertTriangle className="w-5 h-5 text-red-600 mr-2" />
                    <span className="text-red-800">{error}</span>
                  </div>
                </div>
              )}

              {isScanning && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-center">
                    <Loader2 className="w-5 h-5 text-blue-600 animate-spin mr-2" />
                    <span className="text-blue-800">Scanning repository...</span>
                  </div>
                </div>
              )}

              <button
                onClick={handleScan}
                disabled={!repoUrl || !validateRepoUrl(repoUrl) || isScanning}
                className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {isScanning ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin mr-2" />
                    Scanning...
                  </>
                ) : (
                  <>
                    <Search className="w-5 h-5 mr-2" />
                    Start Scan
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Features */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="bg-white rounded-full p-4 w-16 h-16 mx-auto mb-4 shadow-lg">
              <Search className="w-8 h-8 text-blue-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Hybrid Detection</h3>
            <p className="text-gray-600">
              Combines regex patterns with AI-powered classification for comprehensive secret detection.
            </p>
          </div>

          <div className="text-center">
            <div className="bg-white rounded-full p-4 w-16 h-16 mx-auto mb-4 shadow-lg">
              <Shield className="w-8 h-8 text-green-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Secure Analysis</h3>
            <p className="text-gray-600">
              Secrets never leave our secure environment. All analysis happens server-side.
            </p>
          </div>

          <div className="text-center">
            <div className="bg-white rounded-full p-4 w-16 h-16 mx-auto mb-4 shadow-lg">
              <CheckCircle className="w-8 h-8 text-purple-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Actionable Reports</h3>
            <p className="text-gray-600">
              Get detailed reports with remediation steps, risk scores, and export options.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Home
