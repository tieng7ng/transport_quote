import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { Partners } from './pages/Partners';
import { Quotes } from './pages/Quotes';
import { Imports } from './pages/Imports';
import { Search } from './pages/Search';
import { Results } from './pages/Results';
import { CustomerQuotes } from './pages/CustomerQuotes';
import { CustomerQuoteDetail } from './pages/CustomerQuoteDetail';
import { CustomerQuoteEditor } from './pages/CustomerQuoteEditor';
import Login from './pages/Login';
import Register from './pages/Register';
import Users from './pages/Users';
import Profile from './pages/Profile';
import ActivityLogs from './pages/ActivityLogs';
import Statistics from './pages/Statistics';
import ProtectedRoute from './components/auth/ProtectedRoute';
import { AuthProvider, useAuth } from './context/AuthContext';
import { CustomerQuoteProvider } from './context/CustomerQuoteContext';
import ErrorBoundary from './components/common/ErrorBoundary';
import ChangePasswordModal from './components/auth/ChangePasswordModal';

const PasswordEnforcement = () => {
  const { user, mustChangePassword } = useAuth();
  const shouldShow = (!!user && user.must_change_password === true) || !!mustChangePassword;
  return <ChangePasswordModal isOpen={shouldShow} />;
};

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <CustomerQuoteProvider>
          <BrowserRouter basename={import.meta.env.BASE_URL}>
            <Routes>
              {/* Public Routes */}
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />

              {/* Protected Routes */}
              <Route element={<ProtectedRoute />}>
                <Route path="/" element={<Layout />}>
                  <Route index element={<Dashboard />} />

                  {/* Available to all authenticated users */}
                  <Route path="search" element={<Search />} />
                  <Route path="results" element={<Results />} />
                  <Route path="quotes" element={<Quotes />} />
                  <Route path="customer-quotes" element={<CustomerQuotes />} />
                  <Route path="customer-quotes/:id" element={<CustomerQuoteDetail />} />
                  <Route path="profile" element={<Profile />} />

                  {/* Partners available to all authenticated */}
                  <Route path="partners" element={<Partners />} />

                  <Route element={<ProtectedRoute allowedRoles={['ADMIN', 'COMMERCIAL', 'OPERATOR']} />}>
                    <Route path="customer-quotes/:id/edit" element={<CustomerQuoteEditor />} />
                  </Route>

                  {/* Imports restricted to SUPER_ADMIN */}
                  <Route element={<ProtectedRoute allowedRoles={['SUPER_ADMIN']} />}>
                    <Route path="imports" element={<Imports />} />
                  </Route>

                  {/* Admin pages — ADMIN + SUPER_ADMIN */}
                  <Route element={<ProtectedRoute allowedRoles={['SUPER_ADMIN', 'ADMIN']} />}>
                    <Route path="users" element={<Users />} />
                    <Route path="admin/activity" element={<ActivityLogs />} />
                    <Route path="admin/statistics" element={<Statistics />} />
                  </Route>
                </Route>
              </Route>
            </Routes>
            <PasswordEnforcement />
          </BrowserRouter>
        </CustomerQuoteProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
