import React, { useEffect } from 'react'
import Cart from '../components/product/Cart'
import useAxios from '../utils/useAxios';
import { useAuthStore } from '../store/auth';

function Header() {

    const axios_ = useAxios();
    const user = useAuthStore((state) => state.allUserData);
    console.log('user', user);
    
    const fetchData = async () => {
        const resp = axios_.get(`api/shop/cart/${user.user_id}`);
        console.log('Cart', resp);
    }
    
    useEffect(() => {
        fetchData();
    }, [user])

  return (
    <div>
        Header
        <Cart />
    </div>
  )
}

export default Header