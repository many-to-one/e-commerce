import { useState } from 'react';
import { Route, Routes, BrowserRouter, useLocation } from 'react-router-dom';
import './App.css';
import './styles/product.css';
import './styles/cart.css';
import './styles/width.css';
import './styles/customSwiper.css';
import './styles/loader.css';
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
import Order from './views/shop/Order';
import CheckOut from './views/shop/CheckOut';
import SuccessPayment from './views/shop/SuccessPayment';
import UploadAllegro from './views/admin/UploadAllegro';
import Profile from './views/shop/Profile';
import OrderHistory from './views/shop/OrderHistory';
import Returns from './views/shop/Returns';
import InitialReturn from './views/shop/InitialReturn';
import ProductsBySubCat from './views/shop/ProductsBySubCat';
import AllegroAuth from './views/admin/AllegroAuth';


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
        <Route path='/' element={<Products />} />
        <Route path='/product-details/:slug' element={<ProductDetails />} />
        <Route path='/category-products/:slug' element={<ProductsByCat />} />
        <Route path='/sub-category-products/:slug' element={<ProductsBySubCat />} />
        <Route path='/order' element={<Order />} />
        <Route path='/checkout' element={<CheckOut />} />
        {/* <Route path='/payment-success/:oid' element={<SuccessPayment />} /> */}
        <Route path="/payment-success" element={<SuccessPayment />} />

        {/* ADMIN */}
        <Route path='/profile' element={<Profile />} />
        <Route path='/orders-history' element={<OrderHistory />} />
        <Route path='/upload-files' element={<UploadAllegro />} />
        <Route path='/initial-return' element={<InitialReturn />} />
        <Route path='/returns' element={<Returns />} />
        {/* <Route path='/allegro-auth-code-:vendorName' element={<AllegroAuth />} /> */}
         <Route path='/allegro-auth-code/:vendorName' element={<AllegroAuth />} />

      </Routes>
    </>
  );
}

export default App
