import { Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Console } from './pages/Console'
import { Home } from './pages/Home'
import { Knowledge } from './pages/Knowledge'
import { Scenarios } from './pages/Scenarios'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/scenarios" element={<Scenarios />} />
        <Route path="/console/:sessionId" element={<Console />} />
        <Route path="/knowledge" element={<Knowledge />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
