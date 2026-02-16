import { create } from 'zustand'
import type { ModelConfig } from '../lib/types'
import { api } from '../lib/api'

interface ConfigState {
  config: ModelConfig
  setConfig: (config: ModelConfig) => void
  fetchConfig: () => Promise<void>
}

const defaultConfig: ModelConfig = {
  c_model: { backend: 'claude_code_cli', model: 'claude-sonnet-4-5-20250929', max_tokens: 4096 },
  s_model: { backend: 'claude_code_cli', model: 'claude-haiku-4-5-20251001', max_tokens: 2048 },
}

export const useConfigStore = create<ConfigState>((set) => ({
  config: defaultConfig,
  setConfig: (config) => set({ config }),
  fetchConfig: async () => {
    try {
      const config = await api.getConfig()
      set({ config })
    } catch {
      // Server not ready yet, keep defaults
    }
  },
}))
