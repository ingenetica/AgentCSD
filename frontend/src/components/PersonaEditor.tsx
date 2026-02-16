import { useState, useEffect } from 'react'
import { api } from '../lib/api'
import { Modal } from './ui/Modal'
import { Button } from './ui/Button'
import { Input, TextArea } from './ui/Input'
import type { Persona } from '../lib/types'

interface PersonaEditorProps {
  open: boolean
  onClose: () => void
}

export function PersonaEditor({ open, onClose }: PersonaEditorProps) {
  const [personas, setPersonas] = useState<Persona[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [content, setContent] = useState('')
  const [newFilename, setNewFilename] = useState('')
  const [saving, setSaving] = useState(false)

  const load = async () => {
    const list = await api.listPersonas()
    setPersonas(list)
    if (list.length > 0 && !selected) {
      setSelected(list[0].filename)
    }
  }

  useEffect(() => {
    if (open) load()
  }, [open])

  useEffect(() => {
    if (selected) {
      api.getPersona(selected).then(p => setContent(p.content || ''))
    }
  }, [selected])

  const handleSave = async () => {
    if (!selected) return
    setSaving(true)
    await api.updatePersona(selected, content)
    setSaving(false)
  }

  const handleCreate = async () => {
    const name = newFilename.trim()
    if (!name) return
    const filename = name.endsWith('.md') ? name : name + '.md'
    await api.createPersona(filename, '# Persona Core\n\nDescribe identity, values, and criteria here.\n')
    setNewFilename('')
    await load()
    setSelected(filename)
  }

  const handleDelete = async (filename: string) => {
    await api.deletePersona(filename)
    if (selected === filename) {
      setSelected(null)
      setContent('')
    }
    await load()
  }

  return (
    <Modal open={open} onClose={onClose} title="Persona Core Editor">
      <div className="space-y-3">
        {/* Persona list */}
        <div className="flex gap-2">
          <select
            value={selected || ''}
            onChange={e => setSelected(e.target.value)}
            className="flex-1 bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm text-gray-100"
          >
            {personas.map(p => (
              <option key={p.filename} value={p.filename}>{p.filename}</option>
            ))}
          </select>
          {selected && selected !== 'default.md' && (
            <Button variant="danger" size="sm" onClick={() => handleDelete(selected)}>
              Delete
            </Button>
          )}
        </div>

        {/* Editor */}
        <TextArea
          rows={15}
          value={content}
          onChange={e => setContent(e.target.value)}
          className="font-mono text-xs"
        />

        <Button variant="primary" className="w-full" onClick={handleSave} disabled={saving}>
          {saving ? 'Saving...' : 'Save'}
        </Button>

        {/* Create new */}
        <div className="border-t border-gray-700 pt-3">
          <label className="text-xs text-gray-400 block mb-1">Create New Persona</label>
          <div className="flex gap-2">
            <Input
              value={newFilename}
              onChange={e => setNewFilename(e.target.value)}
              placeholder="filename.md"
            />
            <Button variant="secondary" size="sm" onClick={handleCreate}>
              Create
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  )
}
