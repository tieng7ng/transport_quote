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
import ProtectedRoute from './components/auth/ProtectedRoute';
import { AuthProvider } from './context/AuthContext';
import { CustomerQuoteProvider } from './context/CustomerQuoteContext';

import ErrorBoundary from './components/common/ErrorBoundary';

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

                  {/* Role based implementation needed in components or here if strict separation */}
                  <Route element={<ProtectedRoute allowedRoles={['ADMIN', 'COMMERCIAL']} />}>
                    <Route path="customer-quotes/:id/edit" element={<CustomerQuoteEditor />} />
                  </Route>

                  <Route element={<ProtectedRoute allowedRoles={['ADMIN', 'OPERATOR']} />}>
                    <Route path="partners" element={<Partners />} />
                    <Route path="imports" element={<Imports />} />
                  </Route>

                  <Route element={<ProtectedRoute allowedRoles={['ADMIN', 'SUPER_ADMIN']} />}>
                    <Route path="users" element={<Users />} />
                  </Route>
                </Route>
              </Route>
            </Routes>
          </BrowserRouter>
        </CustomerQuoteProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
