import React, { FC } from 'react'
import { useAuthStore } from "../../store/auth";
import { Link } from 'react-router-dom';
import Products from '../../views/shop/Products';

const Home: React.FC = () => {

  const isLoggedIn = useAuthStore((state) => state.isLoggedIn);
  const user = useAuthStore((state) => state.allUserData);

  console.log('isLoggedIn', isLoggedIn)
  console.log('user', user)

  return (
    <div>
      {isLoggedIn()
        ? <div>
            <h1>Hello, {user?.username}</h1>
            <Products />
            <Link to={'/logout'}>logout</Link>
          </div>
        : <div>
            <h1>Home</h1>
            <Link to={'/login'}>login</Link>
          </div>
      }
    </div>    
  )
}

export default Home