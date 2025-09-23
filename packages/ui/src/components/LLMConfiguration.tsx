import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { Brain, Bot, Settings, TestTube, RefreshCw } from 'lucide-react'

interface LLMConfig {
  llm_classifier_enabled: boolean
  llm_provider: string
  openai_model: string
  gemini_model: string
  llm_confidence_threshold: number
  openai_api_key?: string
  gemini_api_key?: string
}

interface LLMConfigurationProps {
  config: LLMConfig
}

const LLMConfiguration: React.FC<LLMConfigurationProps> = ({ config }) => {
  const [loading, setLoading] = useState(false)
  const [testResults, setTestResults] = useState<any>(null)

  const handleTestClassifiers = async () => {
    setLoading(true)
    try {
      // This would call a test endpoint
      // For now, we'll simulate the test
      await new Promise(resolve => setTimeout(resolve, 2000))
      setTestResults({
        rule_based: { status: 'success', confidence: 0.85 },
        openai: config.openai_api_key ? { status: 'success', confidence: 0.92 } : { status: 'skipped', reason: 'No API key' },
        gemini: config.gemini_api_key ? { status: 'success', confidence: 0.88 } : { status: 'skipped', reason: 'No API key' }
      })
    } catch (error) {
      console.error('Test failed:', error)
    } finally {
      setLoading(false)
    }
  }

  const getProviderDisplayName = (provider: string) => {
    switch (provider) {
      case 'openai': return 'OpenAI'
      case 'gemini': return 'Google Gemini'
      case 'both': return 'Both Providers'
      default: return provider
    }
  }

  const getModelDisplayName = (model: string) => {
    switch (model) {
      case 'gpt-3.5-turbo': return 'GPT-3.5 Turbo'
      case 'gpt-4': return 'GPT-4'
      case 'gpt-4-turbo': return 'GPT-4 Turbo'
      case 'gemini-1.5-flash': return 'Gemini 1.5 Flash'
      case 'gemini-1.5-pro': return 'Gemini 1.5 Pro'
      default: return model
    }
  }

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Brain className="h-6 w-6 text-primary-600 mr-3" />
          <h2 className="text-xl font-semibold text-gray-900">LLM Configuration</h2>
        </div>
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${
            config.llm_classifier_enabled ? 'bg-success-500' : 'bg-gray-400'
          }`} />
          <span className="text-sm font-medium text-gray-900">
            {config.llm_classifier_enabled ? 'Enabled' : 'Disabled'}
          </span>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            LLM Provider
          </label>
          <p className="text-sm text-gray-900">
            {getProviderDisplayName(config.llm_provider || 'Not configured')}
          </p>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Confidence Threshold
          </label>
          <p className="text-sm text-gray-900">
            {config.llm_confidence_threshold || 0.7}
          </p>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            OpenAI Model
          </label>
          <p className="text-sm text-gray-900">
            {config.openai_model ? getModelDisplayName(config.openai_model) : 'Not configured'}
          </p>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Gemini Model
          </label>
          <p className="text-sm text-gray-900">
            {config.gemini_model ? getModelDisplayName(config.gemini_model) : 'Not configured'}
          </p>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            OpenAI API Key
          </label>
          <p className="text-sm text-gray-900">
            {config.openai_api_key 
              ? `${config.openai_api_key.substring(0, 8)}...`
              : 'Not configured'
            }
          </p>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Gemini API Key
          </label>
          <p className="text-sm text-gray-900">
            {config.gemini_api_key 
              ? `${config.gemini_api_key.substring(0, 8)}...`
              : 'Not configured'
            }
          </p>
        </div>
      </div>
      
      {/* Model Recommendations */}
      <div className="mb-6 p-4 bg-blue-50 rounded-lg">
        <div className="flex items-start">
          <Bot className="h-5 w-5 text-blue-600 mt-0.5 mr-3" />
          <div>
            <h3 className="text-sm font-medium text-blue-900">Model Recommendations</h3>
            <div className="mt-2 text-sm text-blue-700">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <strong>Development:</strong> GPT-3.5 Turbo (fast, cost-effective)
                </div>
                <div>
                  <strong>Production:</strong> GPT-4 (high accuracy)
                </div>
                <div>
                  <strong>High Volume:</strong> Gemini 1.5 Flash (very fast)
                </div>
                <div>
                  <strong>Best Accuracy:</strong> Gemini 1.5 Pro (excellent results)
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Test Results */}
      {testResults && (
        <div className="mb-6 p-4 bg-green-50 rounded-lg">
          <h3 className="text-sm font-medium text-green-900 mb-3">Test Results</h3>
          <div className="space-y-2">
            {Object.entries(testResults).map(([classifier, result]: [string, any]) => (
              <div key={classifier} className="flex items-center justify-between">
                <span className="text-sm text-green-700 capitalize">
                  {classifier.replace('_', ' ')} Classifier
                </span>
                <div className="flex items-center">
                  {result.status === 'success' ? (
                    <>
                      <div className="w-2 h-2 bg-green-500 rounded-full mr-2" />
                      <span className="text-sm text-green-700">
                        {result.confidence} confidence
                      </span>
                    </>
                  ) : (
                    <>
                      <div className="w-2 h-2 bg-gray-400 rounded-full mr-2" />
                      <span className="text-sm text-gray-600">
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
      
      {/* Actions */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-600">
          Configure LLM models for intelligent secret classification
        </div>
        <div className="flex space-x-3">
          <Link to="/settings/llm" className="btn btn-sm btn-primary">
            <Settings className="h-4 w-4 mr-1" />
            Configure Models
          </Link>
          <button
            onClick={handleTestClassifiers}
            disabled={loading}
            className="btn btn-sm btn-secondary"
          >
            {loading ? (
              <RefreshCw className="h-4 w-4 mr-1 animate-spin" />
            ) : (
              <TestTube className="h-4 w-4 mr-1" />
            )}
            Test Classifiers
          </button>
        </div>
      </div>
    </div>
  )
}

export default LLMConfiguration
