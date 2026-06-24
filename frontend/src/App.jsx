import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useUser } from './context/UserContext';

// Layouts
import DashboardLayout from './layouts/DashboardLayout';
import AuthLayout from './layouts/AuthLayout';
import AdminLayout from './layouts/AdminLayout';
import PublicLayout from './layouts/PublicLayout';

// Public
import LandingPage from './pages/LandingPage';

// Auth
import Login from './pages/Login';
import Register from './pages/Register';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';

// User App
import Dashboard from './pages/Dashboard';
import AiChat from './pages/AiChat';
import MedicineSearch from './pages/MedicineSearch';
import MedicineDetail from './pages/MedicineDetail';
import DiseaseSearch from './pages/DiseaseSearch';
import DiseaseDetail from './pages/DiseaseDetail';
import InteractionChecker from './pages/InteractionChecker';
import Settings from './pages/Settings';
import EditAccount from './pages/EditAccount';
import SavedItems from './pages/SavedItems';

// Admin
import AdminDashboard from './pages/AdminDashboard';
import AdminUserManagement from './pages/AdminUserManagement';
import AdminMedicines from './pages/AdminMedicines';
import AdminDiseases from './pages/AdminDiseases';
import AdminAILogs from './pages/AdminAILogs';
import AdminReports from './pages/AdminReports';

// Placeholder
const Placeholder = ({ title }) => (
  <div className="flex flex-col items-center justify-center h-full gap-4 text-center py-20">
    <div className="w-16 h-16 rounded-2xl bg-secondary flex items-center justify-center">
      <iconify-icon icon="lucide:construction" class="text-3xl text-muted-foreground"></iconify-icon>
    </div>
    <h1 className="text-2xl font-bold text-foreground">{title}</h1>
    <p className="text-muted-foreground">This page is under construction.</p>
  </div>
);

// Loading spinner
const LoadingScreen = () => (
  <div className="min-h-screen flex items-center justify-center bg-background">
    <div className="flex flex-col items-center gap-3">
      <div className="w-10 h-10 border-4 border-primary/30 border-t-primary rounded-full animate-spin"></div>
      <p className="text-sm text-muted-foreground">Loading...</p>
    </div>
  </div>
);

// Route guard: Requires logged-in user
const RequireAuth = ({ children }) => {
  const { user, loading } = useUser();
  const location = useLocation();
  if (loading) return <LoadingScreen />;
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />;
  return children;
};

// Route guard: Requires superuser/admin
const RequireAdmin = ({ children }) => {
  const { user, loading } = useUser();
  const location = useLocation();
  if (loading) return <LoadingScreen />;
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />;
  if (!user.is_superuser) return <Navigate to="/app" replace />;
  return children;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes without Auth */}
        <Route element={<PublicLayout />}>
          <Route path="/" element={<LandingPage />} />
          <Route path="/chat" element={<AiChat />} />
          <Route path="/medicines" element={<MedicineSearch />} />
          <Route path="/medicines/:id" element={<MedicineDetail />} />
          <Route path="/diseases" element={<DiseaseSearch />} />
          <Route path="/diseases/:id" element={<DiseaseDetail />} />
        </Route>

        {/* Auth Routes */}
        <Route element={<AuthLayout />}>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
        </Route>

        {/* User App Routes - requires login */}
        <Route path="/app" element={<RequireAuth><DashboardLayout /></RequireAuth>}>
          <Route index element={<Dashboard />} />
          <Route path="chat" element={<AiChat />} />
          <Route path="medicines" element={<MedicineSearch />} />
          <Route path="medicines/:id" element={<MedicineDetail />} />
          <Route path="diseases" element={<DiseaseSearch />} />
          <Route path="diseases/:id" element={<DiseaseDetail />} />
          <Route path="interactions" element={<InteractionChecker />} />
          <Route path="saved" element={<SavedItems />} />
          <Route path="settings" element={<Settings />} />
          <Route path="settings/edit" element={<EditAccount />} />
        </Route>

        {/* Admin Routes - requires superuser */}
        <Route path="/admin" element={<RequireAdmin><AdminLayout /></RequireAdmin>}>
          <Route index element={<AdminDashboard />} />
          <Route path="users" element={<AdminUserManagement />} />
          <Route path="medicines" element={<AdminMedicines />} />
          <Route path="diseases" element={<AdminDiseases />} />
          <Route path="ai" element={<AdminAILogs />} />
          <Route path="reports" element={<AdminReports />} />
          <Route path="settings" element={<Settings />} />
        </Route>

        {/* Catch-all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
