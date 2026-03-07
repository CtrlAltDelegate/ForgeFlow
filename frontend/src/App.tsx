import { Routes, Route, Navigate } from 'react-router-dom'
import { AppLayout } from './layouts/AppLayout'
import { Dashboard } from './pages/Dashboard'
import { Opportunities } from './pages/Opportunities'
import { ProductDetail } from './pages/ProductDetail'
import { Placeholder } from './pages/Placeholder'
import { DataImports } from './pages/DataImports'
import { ProductCreate } from './pages/ProductCreate'
import { CadGenerator } from './pages/CadGenerator'

function App() {
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="opportunities" element={<Opportunities />} />
        <Route path="product/new" element={<ProductCreate />} />
        <Route path="product/:idOrSlug" element={<ProductDetail />} />
        <Route path="cad" element={<CadGenerator />} />
        <Route path="simulator" element={<Placeholder />} />
        <Route path="listings" element={<Placeholder />} />
        <Route path="imports" element={<DataImports />} />
        <Route path="settings" element={<Placeholder />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

export default App
