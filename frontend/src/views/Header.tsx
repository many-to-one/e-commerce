import React, { useEffect } from 'react'
import Cart from '../components/product/Cart'
import useAxios from '../utils/useAxios';
import { useAuthStore } from '../store/auth';
import { useNavigate } from 'react-router-dom';

function Header() {

  const user = useAuthStore((state) => state.allUserData);
  const navigate = useNavigate()

  console.log('Header-user', user);

  return (
    <div className='Header flexRowStart gap-15'>
        <p className='Cursor' onClick={() => navigate('/')}>Główna</p>
        {user ? (
          <>
            <p>Hello, {user.username}</p>
            <div className='Cursor loginSt'>
              {user.username === 'admin' &&
                <p className='Cursor' onClick={()=> navigate('/upload-files')}>Załaduj oferty</p>
              }
              <Cart/>
            </div>
          </>
        ): (
          <p className='Cursor loginSt' onClick={() => navigate('/login')}>Zaloguj</p>
        )}
    </div>
  )
}

export default Header