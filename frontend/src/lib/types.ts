export interface ModelLayerConfig {
  backend: string
  model: string
  max_tokens: number
  endpoint?: string
  api_key?: string
}

export interface ModelConfig {
  c_model: ModelLayerConfig
  s_model: ModelLayerConfig
}

export interface Session {
  id: string
  name: string
  persona_core_path: string
  model_config: ModelConfig
  status: string
  summary_frequency: number
  created_at: string
  updated_at: string
}

export interface Message {
  id: number
  session_id: string
  layer: string
  tag: string
  content: string
  cycle_number: number | null
  created_at: string
}

export interface MoodAndCriteria {
  mood: string
  criteria: string
  cycle_number: number
}

export interface Persona {
  filename: string
  content?: string
  size?: number
}

// WebSocket message types
export interface WSMessage {
  type: string
  content?: string
  timestamp?: string
  cycle?: number
  mood?: string
  criteria?: string
  session_id?: string
  name?: string
  history?: {
    messages: Message[]
    mood_and_criteria: MoodAndCriteria | null
    cycle: number
  }
  message?: string
  subconscious_running?: boolean
  internal_only?: boolean
  // Input context fields
  ed_user?: string
  ed_agent?: string
  id_loud?: string
  id_quiet?: string
  s_loud_entries?: { cycle?: number; content: string }[]
}
