export interface Finding {
  id: string
  fingerprint: string
  kind: string
  confidence: number
  location: string
  preview_masked: string
  repo: string
  commit_sha: string
  file_path: string
  line_start: number
  line_end: number
  status: 'NEW' | 'ACKNOWLEDGED' | 'RESOLVED' | 'FALSE_POSITIVE'
  first_seen_at: string
  last_seen_at: string
  notes: string
}

export interface ScanRun {
  id: string
  repo: string
  started_at: string
  ended_at: string | null
  status: string
  new_findings_count: number
  commit_range: string | null
}

export interface Metrics {
  findings: {
    counts_by_status: Record<string, number>
    counts_by_kind: Record<string, number>
    total_findings: number
  }
  last_scan_at: string | null
  agent_status: {
    running: boolean
    config: Record<string, any>
    last_scan: string | null
    registered_plugins: {
      detectors: string[]
      connectors: string[]
      remediation_handlers: string[]
    }
  }
}

export interface HealthStatus {
  status: string
  version: string
  uptime: number
  agent_status: {
    running: boolean
    config: Record<string, any>
    last_scan: string | null
    registered_plugins: {
      detectors: string[]
      connectors: string[]
      remediation_handlers: string[]
    }
  }
}

export interface ApiResponse<T> {
  data: T
  total?: number
  limit?: number
  offset?: number
}

// MCP Types
export interface MCPChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
}

export interface MCPHealthResponse {
  status: 'ok' | 'error'
  details?: Record<string, any>
  request_id?: string
}

export interface MCPChatResponse {
  status: 'ok' | 'error'
  result?: Record<string, any>
  request_id?: string
  mcp_meta?: Record<string, any>
}
