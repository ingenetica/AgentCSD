import type { Session, Persona, ModelConfig } from './types'

const BASE = '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const body = await res.text()
    throw new Error(`API error ${res.status}: ${body}`)
  }
  return res.json()
}

export const api = {
  // Sessions
  listSessions: () => request<Session[]>('/sessions'),
  getSession: (id: string) => request<{ session: Session; messages: any[]; mood_and_criteria: any }>(`/sessions/${id}`),
  deleteSession: (id: string) => request<{ ok: boolean }>(`/sessions/${id}`, { method: 'DELETE' }),

  // Personas
  listPersonas: () => request<Persona[]>('/personas'),
  getPersona: (filename: string) => request<Persona>(`/personas/${filename}`),
  updatePersona: (filename: string, content: string) =>
    request<{ ok: boolean }>(`/personas/${filename}`, {
      method: 'PUT',
      body: JSON.stringify({ content }),
    }),
  createPersona: (filename: string, content: string) =>
    request<{ ok: boolean }>('/personas', {
      method: 'POST',
      body: JSON.stringify({ filename, content }),
    }),
  deletePersona: (filename: string) =>
    request<{ ok: boolean }>(`/personas/${filename}`, { method: 'DELETE' }),

  // Config
  getConfig: () => request<ModelConfig>('/config'),
  updateConfig: (model_config: ModelConfig) =>
    request<ModelConfig>('/config', {
      method: 'PUT',
      body: JSON.stringify({ model_config }),
    }),
}
