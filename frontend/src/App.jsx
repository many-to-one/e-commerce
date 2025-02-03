import { useState } from 'react'
import { Route, Routes, BrowserRouter } from 'react-router-dom';
import './App.css'
import Login from './views/auth/Login'
import Home from './views/auth/Home';
import Register from './views/auth/Register';
import Logout from './views/auth/Logout';
import ForgotPassword from './views/auth/ForgotPassword';
import CreatePassword from './views/auth/CreatePassword';

function App() {
  const [count, setCount] = useState(0)

  return (
    <BrowserRouter>
        <Routes>
          <Route path='/register' element={<Register />} />
            <Route path='/login' element={<Login />} />
            <Route path='/logout' element={<Logout />} />
            <Route path='/' element={<Home />} />
            <Route path='/forgot-password' element={<ForgotPassword />} />
            <Route path='/create-new-password' element={<CreatePassword />} />
        </Routes>
      </BrowserRouter>
  )
}

export default App
