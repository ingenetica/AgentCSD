import { useEffect } from 'react'
import { Layout } from './components/Layout'
import { useConfigStore } from './stores/configStore'

export default function App() {
  const fetchConfig = useConfigStore(s => s.fetchConfig)

  useEffect(() => {
    fetchConfig()
  }, [fetchConfig])

  return <Layout />
}
