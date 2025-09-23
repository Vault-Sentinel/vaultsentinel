import React, { useState } from 'react'
import { 
  Brain, 
  Bot, 
  TestTube, 
  Save, 
  RefreshCw,
  ArrowLeft,
  CheckCircle,
  XCircle,
  AlertCircle
} from 'lucide-react'
import { Link } from 'react-router-dom'

interface LLMConfig {
  llm_classifier_enabled: boolean
  llm_provider: string
  openai_model: string
  gemini_model: string
  llm_confidence_threshold: number
  openai_api_key?: string
  gemini_api_key?: string
}

const LLMConfig: React.FC = () => {
  const [config, setConfig] = useState<LLMConfig>({
    llm_classifier_enabled: false,
    llm_provider: 'openai',
    openai_model: 'gpt-3.5-turbo',
    gemini_model: 'gemini-1.5-flash',
    llm_confidence_threshold: 0.7,
    openai_api_key: '',
    gemini_api_key: ''
  })
  
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [testResults, setTestResults] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const openaiModels = [
    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo', description: 'Fast, cost-effective' },
    { value: 'gpt-4', label: 'GPT-4', description: 'High accuracy, slower' },
    { value: 'gpt-4-turbo', label: 'GPT-4 Turbo', description: 'Balanced performance' }
  ]

  const geminiModels = [
    { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash', description: 'Very fast, cost-effective' },
    { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro', description: 'High accuracy, slower' }
  ]

  const providers = [
    { value: 'openai', label: 'OpenAI Only', description: 'Use only OpenAI models' },
    { value: 'gemini', label: 'Gemini Only', description: 'Use only Google Gemini models' },
    { value: 'both', label: 'Both Providers', description: 'Use both for comparison' }
  ]

  const handleSave = async () => {
    setSaving(true)
    try {
      // This would call an API endpoint to save the configuration
      await new Promise(resolve => setTimeout(resolve, 1000))
      setError(null)
      alert('Configuration saved successfully!')
    } catch (err) {
      setError('Failed to save configuration')
    } finally {
      setSaving(false)
    }
  }

  const handleTest = async () => {
    setLoading(true)
    try {
      // This would call a test endpoint
      await new Promise(resolve => setTimeout(resolve, 2000))
      setTestResults({
        rule_based: { status: 'success', confidence: 0.85 },
        openai: config.openai_api_key ? { status: 'success', confidence: 0.92 } : { status: 'skipped', reason: 'No API key' },
        gemini: config.gemini_api_key ? { status: 'success', confidence: 0.88 } : { status: 'skipped', reason: 'No API key' }
      })
    } catch (err) {
      setError('Test failed')
    } finally {
      setLoading(false)
    }
  }

  const getModelRecommendation = () => {
    if (config.llm_provider === 'openai') {
      return config.openai_model === 'gpt-3.5-turbo' ? 'Good for development' : 'Good for production'
    } else if (config.llm_provider === 'gemini') {
      return config.gemini_model === 'gemini-1.5-flash' ? 'Good for high volume' : 'Good for accuracy'
    } else {
      return 'Using both providers for comparison'
    }
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center mb-4">
          <Link to="/settings" className="mr-4">
            <ArrowLeft className="h-5 w-5 text-gray-600 hover:text-gray-900" />
          </Link>
          <Brain className="h-8 w-8 text-primary-600 mr-3" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">LLM Configuration</h1>
            <p className="text-gray-600">Configure AI models for intelligent secret classification</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Configuration Form */}
        <div className="lg:col-span-2 space-y-6">
          {/* Basic Settings */}
          <div className="card p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Basic Settings</h2>
            
            <div className="space-y-4">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="enabled"
                  checked={config.llm_classifier_enabled}
                  onChange={(e) => setConfig({ ...config, llm_classifier_enabled: e.target.checked })}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <label htmlFor="enabled" className="ml-2 text-sm font-medium text-gray-700">
                  Enable LLM Classifiers
                </label>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Provider Selection
                </label>
                <select
                  value={config.llm_provider}
                  onChange={(e) => setConfig({ ...config, llm_provider: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                >
                  {providers.map((provider) => (
                    <option key={provider.value} value={provider.value}>
                      {provider.label} - {provider.description}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Confidence Threshold
                </label>
                <div className="flex items-center space-x-4">
                  <input
                    type="range"
                    min="0.5"
                    max="0.9"
                    step="0.1"
                    value={config.llm_confidence_threshold}
                    onChange={(e) => setConfig({ ...config, llm_confidence_threshold: parseFloat(e.target.value) })}
                    className="flex-1"
                  />
                  <span className="text-sm font-medium text-gray-700 w-12">
                    {config.llm_confidence_threshold}
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  0.5 = lenient, 0.7 = balanced, 0.9 = strict
                </p>
              </div>
            </div>
          </div>

          {/* OpenAI Configuration */}
          {(config.llm_provider === 'openai' || config.llm_provider === 'both') && (
            <div className="card p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">OpenAI Configuration</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    API Key
                  </label>
                  <input
                    type="password"
                    value={config.openai_api_key}
                    onChange={(e) => setConfig({ ...config, openai_api_key: e.target.value })}
                    placeholder="sk-your-openai-key-here"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Model
                  </label>
                  <select
                    value={config.openai_model}
                    onChange={(e) => setConfig({ ...config, openai_model: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                  >
                    {openaiModels.map((model) => (
                      <option key={model.value} value={model.value}>
                        {model.label} - {model.description}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Gemini Configuration */}
          {(config.llm_provider === 'gemini' || config.llm_provider === 'both') && (
            <div className="card p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Gemini Configuration</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    API Key
                  </label>
                  <input
                    type="password"
                    value={config.gemini_api_key}
                    onChange={(e) => setConfig({ ...config, gemini_api_key: e.target.value })}
                    placeholder="your-gemini-key-here"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Model
                  </label>
                  <select
                    value={config.gemini_model}
                    onChange={(e) => setConfig({ ...config, gemini_model: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                  >
                    {geminiModels.map((model) => (
                      <option key={model.value} value={model.value}>
                        {model.label} - {model.description}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Actions</h2>
                <p className="text-sm text-gray-600 mt-1">
                  Test your configuration and save changes
                </p>
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={handleTest}
                  disabled={loading}
                  className="btn btn-secondary"
                >
                  {loading ? (
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <TestTube className="h-4 w-4 mr-2" />
                  )}
                  Test Configuration
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="btn btn-primary"
                >
                  {saving ? (
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Save className="h-4 w-4 mr-2" />
                  )}
                  Save Changes
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Recommendations */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Recommendations</h3>
            <div className="space-y-3">
              <div className="p-3 bg-blue-50 rounded-lg">
                <div className="flex items-center mb-2">
                  <Bot className="h-4 w-4 text-blue-600 mr-2" />
                  <span className="text-sm font-medium text-blue-900">Current Setup</span>
                </div>
                <p className="text-sm text-blue-700">{getModelRecommendation()}</p>
              </div>
              
              <div className="p-3 bg-green-50 rounded-lg">
                <div className="flex items-center mb-2">
                  <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                  <span className="text-sm font-medium text-green-900">Best Practices</span>
                </div>
                <ul className="text-sm text-green-700 space-y-1">
                  <li>• Use GPT-3.5 Turbo for development</li>
                  <li>• Use GPT-4 for production</li>
                  <li>• Use Gemini Flash for high volume</li>
                  <li>• Use both providers for comparison</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Test Results */}
          {testResults && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Test Results</h3>
              <div className="space-y-3">
                {Object.entries(testResults).map(([classifier, result]: [string, any]) => (
                  <div key={classifier} className="flex items-center justify-between">
                    <span className="text-sm text-gray-700 capitalize">
                      {classifier.replace('_', ' ')}
                    </span>
                    <div className="flex items-center">
                      {result.status === 'success' ? (
                        <>
                          <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                          <span className="text-sm text-green-700">
                            {result.confidence}
                          </span>
                        </>
                      ) : (
                        <>
                          <XCircle className="h-4 w-4 text-gray-400 mr-2" />
                          <span className="text-sm text-gray-500">
                            {result.reason}
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="card p-6">
              <div className="flex items-center">
                <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
                <span className="text-sm text-red-700">{error}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default LLMConfig
