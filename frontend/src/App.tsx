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

import { CustomerQuoteProvider } from './context/CustomerQuoteContext';

function App() {
  return (
    <CustomerQuoteProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="partners" element={<Partners />} />
            <Route path="quotes" element={<Quotes />} />
            <Route path="imports" element={<Imports />} />
            <Route path="search" element={<Search />} />
            <Route path="results" element={<Results />} />
            <Route path="customer-quotes" element={<CustomerQuotes />} />
            <Route path="customer-quotes/:id" element={<CustomerQuoteDetail />} />
            <Route path="customer-quotes/:id/edit" element={<CustomerQuoteEditor />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </CustomerQuoteProvider>
  );
}

export default App;
