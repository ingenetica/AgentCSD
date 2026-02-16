import { useState, useEffect } from 'react'
import { useConfigStore } from '../stores/configStore'
import { api } from '../lib/api'
import { Modal } from './ui/Modal'
import { Button } from './ui/Button'
import { Input, Select } from './ui/Input'
import type { ModelConfig, ModelLayerConfig } from '../lib/types'

interface ConfigPanelProps {
  open: boolean
  onClose: () => void
  onUpdateConfig: (config: ModelConfig) => void
}

function LayerConfig({
  label, config, onChange,
}: {
  label: string
  config: ModelLayerConfig
  onChange: (config: ModelLayerConfig) => void
}) {
  return (
    <div className="space-y-2">
      <h4 className="text-xs font-semibold text-gray-300">{label}</h4>
      <div>
        <label className="text-[10px] text-gray-500">Backend</label>
        <Select
          value={config.backend}
          onChange={e => onChange({ ...config, backend: e.target.value })}
          className="w-full"
        >
          <option value="claude_code_cli">Claude Code CLI</option>
          <option value="anthropic_api">Anthropic API</option>
          <option value="openai_compatible">OpenAI Compatible</option>
        </Select>
      </div>
      <div>
        <label className="text-[10px] text-gray-500">Model</label>
        <Input value={config.model} onChange={e => onChange({ ...config, model: e.target.value })} />
      </div>
      <div>
        <label className="text-[10px] text-gray-500">Max Tokens</label>
        <Input
          type="number"
          value={config.max_tokens}
          onChange={e => onChange({ ...config, max_tokens: parseInt(e.target.value) || 4096 })}
        />
      </div>
      {config.backend === 'openai_compatible' && (
        <div>
          <label className="text-[10px] text-gray-500">Endpoint URL</label>
          <Input
            value={config.endpoint || ''}
            onChange={e => onChange({ ...config, endpoint: e.target.value })}
            placeholder="http://localhost:1234/v1"
          />
        </div>
      )}
      {config.backend === 'anthropic_api' && (
        <div>
          <label className="text-[10px] text-gray-500">API Key</label>
          <Input
            type="password"
            value={config.api_key || ''}
            onChange={e => onChange({ ...config, api_key: e.target.value })}
            placeholder="sk-..."
          />
        </div>
      )}
    </div>
  )
}

export function ConfigPanel({ open, onClose, onUpdateConfig }: ConfigPanelProps) {
  const storeConfig = useConfigStore(s => s.config)
  const setStoreConfig = useConfigStore(s => s.setConfig)
  const [config, setConfig] = useState<ModelConfig>(storeConfig)

  useEffect(() => {
    if (open) {
      api.getConfig().then(c => {
        setConfig(c as ModelConfig)
        setStoreConfig(c as ModelConfig)
      }).catch(() => {})
    }
  }, [open])

  const handleSave = async () => {
    await api.updateConfig(config)
    setStoreConfig(config)
    onUpdateConfig(config)
    onClose()
  }

  return (
    <Modal open={open} onClose={onClose} title="Model Configuration">
      <div className="space-y-4">
        <LayerConfig
          label="C_model (Internal Dialog)"
          config={config.c_model}
          onChange={c_model => setConfig({ ...config, c_model })}
        />
        <div className="border-t border-gray-700" />
        <LayerConfig
          label="S_model (Subconscious)"
          config={config.s_model}
          onChange={s_model => setConfig({ ...config, s_model })}
        />
        <Button variant="primary" className="w-full" onClick={handleSave}>
          Save Configuration
        </Button>
      </div>
    </Modal>
  )
}
