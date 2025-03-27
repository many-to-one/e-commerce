import React, { useCallback, useEffect, useState } from 'react'
import Cart from '../components/product/Cart'
import useAxios from '../utils/useAxios';
import { useAuthStore } from '../store/auth';
import { useNavigate } from 'react-router-dom';
import Category from '../components/category/Category';
import Profile from './shop/Profile';
import MaterialIcon from '@material/react-material-icon';
import { __userId, logout } from '../utils/auth';
import '../types/SortCategory';

function Header() {

  const user = __userId() //useAuthStore((state) => state.allUserData);
  const navigate = useNavigate()
  const axios = useAxios();
  const [categories, setCategories] = useState<CategoryType[]>([]);
  const [showCategories, setShowCategories] = useState(false);

  const [sortCat, setSortCat] = useState<SortCategory[]>([]);

  // console.log('Header-user', user);

  type Category_ = {
    title: string;
};

  const fetchData = async (endpoint, state) => {

    try {

        const response = await axios.get(endpoint);
        // console.log(`${endpoint}`, response.data);
        state(response.data.results);
        console.log(`CATEGORIES`, response.data.results);
        const allCats: Category_[] = response.data.results; // Explicitly type `allCats`

        const uniqueTitles = Array.from(
            new Set(allCats.map((cat) => cat.title)) // Ensure `cat.title` is a string
        );

        console.log(`uniqueTitles`, uniqueTitles);
        let arr_ = []

        // response.data.results.map((cat) => {
        //   if (cat.category_hierarchy[0].trim() === cat.title) {
        //     console.log(`sortCat`, cat.category_hierarchy.slice(1, cat.category_hierarchy.length));
        //   //   setSortCat((prevSortCat) => [
        //   //     ...prevSortCat, // Spread the existing sortCat array
        //   //     {
        //   //         title: cat.title,
        //   //         sub_cat: cat.category_hierarchy.slice(1, cat.category_hierarchy.length),
        //   //     },
        //   // ]);
        //   }
        // })

        // console.log(`sortCat`, sortCat);
        
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