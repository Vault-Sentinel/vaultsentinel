import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Findings from './pages/Findings'
import Metrics from './pages/Metrics'
import Settings from './pages/Settings'
import LLMConfig from './pages/LLMConfig'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/findings" element={<Findings />} />
          <Route path="/metrics" element={<Metrics />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/settings/llm" element={<LLMConfig />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App
