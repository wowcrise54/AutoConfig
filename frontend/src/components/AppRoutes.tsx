import { Route, Routes, Navigate } from 'react-router-dom';
import Dashboard from '../pages/Dashboard';
import Simulations from '../pages/Simulations';
import Templates from '../pages/Templates';
import Reports from '../pages/Reports';
import Settings from '../pages/Settings';
import Layout from './Layout';

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="simulations" element={<Simulations />} />
        <Route path="templates" element={<Templates />} />
        <Route path="reports" element={<Reports />} />
        <Route path="settings" element={<Settings />} />
        <Route path="*" element={<div>404</div>} />
      </Route>
    </Routes>
  );
}
