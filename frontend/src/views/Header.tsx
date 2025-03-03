import React, { useEffect, useState } from 'react'
import Cart from '../components/product/Cart'
import useAxios from '../utils/useAxios';
import { useAuthStore } from '../store/auth';
import { useNavigate } from 'react-router-dom';
import Category from '../components/category/Category';

function Header() {

  const user = useAuthStore((state) => state.allUserData);
  const navigate = useNavigate()
  const axios = useAxios();
  const [categories, setCategories] = useState<CategoryType[]>([]);
  const [showCategories, setShowCategories] = useState(false);

  console.log('Header-user', user);

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