import { useState } from 'react';
import { Route, Routes, BrowserRouter, useLocation } from 'react-router-dom';
import './App.css';
import './styles/product.css'
import Login from './views/auth/Login';
import Home from './views/auth/Home';
import Register from './views/auth/Register';
import Logout from './views/auth/Logout';
import ForgotPassword from './views/auth/ForgotPassword';
import CreatePassword from './views/auth/CreatePassword';
import Products from './views/shop/Products';
import Product from './components/product/Product';
import ProductDetails from './views/shop/ProductDetails';
import ProductsByCat from './views/shop/ProductsByCat';
import Header from './views/Header';


function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

function AppContent() {
  const location = useLocation();
  const isLoginPage = location.pathname === '/login';

  return (
    <>
      {!isLoginPage && <Header />}
      <Routes>
        {/* AUTH */}
        <Route path='/register' element={<Register />} />
        <Route path='/login' element={<Login />} />
        <Route path='/logout' element={<Logout />} />
        <Route path='/dashboard' element={<Home />} />
        <Route path='/forgot-password' element={<ForgotPassword />} />
        <Route path='/create-new-password' element={<CreatePassword />} />

        {/* STORE */}
        <Route path='/' element={<Home />} />
        <Route path='/product-details/:slug' element={<ProductDetails />} />
        <Route path='/category-products/:slug' element={<ProductsByCat />} />
      </Routes>
    </>
  );
}

export default App
