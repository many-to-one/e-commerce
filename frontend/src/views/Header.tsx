import React, { useEffect } from 'react'
import Cart from '../components/product/Cart'
import useAxios from '../utils/useAxios';
import { useAuthStore } from '../store/auth';

function Header() {

  const user = useAuthStore((state) => state.allUserData);

  console.log('Header-user', user);

  return (
    <div>
        Header, {user?.username}
        <Cart />
    </div>
  )
}

export default Header