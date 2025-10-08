import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import Dashboards from './pages/Dashboards'
import Findings from './pages/Findings'
import ScanReport from './pages/ScanReport'
import Settings from './pages/Settings'
import McpPanel from './pages/McpPanel'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/dashboards" element={<Dashboards />} />
          <Route path="/findings" element={<Findings />} />
          <Route path="/scans/:scanId/report" element={<ScanReport />} />
          <Route path="/mcp" element={<McpPanel />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App
