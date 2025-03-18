import React, { useCallback, useEffect, useState } from 'react'
import Cart from '../components/product/Cart'
import useAxios from '../utils/useAxios';
import { useAuthStore } from '../store/auth';
import { useNavigate } from 'react-router-dom';
import Category from '../components/category/Category';
import Profile from './shop/Profile';
import MaterialIcon from '@material/react-material-icon';
import { __userId, logout } from '../utils/auth';

function Header() {

  const user = __userId() //useAuthStore((state) => state.allUserData);
  const navigate = useNavigate()
  const axios = useAxios();
  const [categories, setCategories] = useState<CategoryType[]>([]);
  const [showCategories, setShowCategories] = useState(false);

  // console.log('Header-user', user);

  const fetchData = async (endpoint, state) => {

    try {
        const response = await axios.get(endpoint);
        console.log(`${endpoint}`, response.data)
        state(response.data.results);
    } catch (error) {
        console.log('Products error', error)
    }

};

  useEffect(() => {
        fetchData('/api/store/categories', setCategories)
    }, [])


  return (
    <div className='Header flexRowStart gap-15'>
        <p className='Cursor' onClick={() => navigate('/')}>Główna</p>
        <p 
          className='Cursor showCat'
          onMouseEnter={() => setShowCategories(true)}
          onMouseLeave={() => setShowCategories(false)}
        >
          Kategorie
          { showCategories && 
            <div className='categoriesGrid'>
              {categories?.map((category, index) => (
                  <Category key={index} category={category} />
              ))}
            </div>
          }
        </p>
        {user ? (
          <>
            <div className='Cursor loginSt flexRowBetween gap-15'>
              <p>Witaj, {user['username']}</p>
              <MaterialIcon icon="person" onClick={() => navigate('/profile')}/>
              <Cart />
              <MaterialIcon icon="logout" onClick={logout} className='ml-30'/>
            </div>
          </>
        ): (
          <p className='Cursor loginSt' onClick={() => navigate('/login')}>Zaloguj</p>
        )}
    </div>
  )
}

export default Header