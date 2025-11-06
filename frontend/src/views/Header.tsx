import React, { useCallback, useEffect, useState } from 'react'
import Cart from '../components/product/Cart'
import useAxios from '../utils/useAxios';
import { useAuthStore } from '../store/auth';
import { useNavigate } from 'react-router-dom';
import Category from '../components/category/Category';
import Profile from './shop/Profile';
// import MaterialIcon from '@material/react-material-icon';
import { __userId, logout } from '../utils/auth';
import '../types/SortCategory';

import AccountCircleRoundedIcon from '@mui/icons-material/AccountCircleRounded';
import LogoutRoundedIcon from '@mui/icons-material/LogoutRounded';
import HomeRoundedIcon from '@mui/icons-material/HomeRounded';
import ContactMailRoundedIcon from '@mui/icons-material/ContactMailRounded';
import MenuIcon from '@mui/icons-material/Menu';

import CategoryType from '../types/CategoryType';
import { useProductStore } from '../store/products';

type SortCategory = {
  title: string;
  category_hierarchy: string[];
}

type CatCatalog = {
  title: string;
  category_hierarchy: string[]
}

function Header() {

  const user = __userId() //useAuthStore((state) => state.allUserData);
  const navigate = useNavigate()
  const axios = useAxios();
  const [categories, setCategories] = useState<CategoryType[]>([]) 
  const [showCategories, setShowCategories] = useState(false);
  const [sortCat, setSortCat] = useState<SortCategory[]>([]);
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);
  const [showHeader, setShowHeader] = useState(false);

  // console.log('Header-user', user);

  type Category_ = {
    title: string;
  };

  const {
    allProducts,
    filteredProducts,
    setProducts,
    setLoading,
    searchTerm,
    setSearchTerm,
    searchProducts,
  } = useProductStore();

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const closeMenuAndNavigate = (path: string, action?: () => void) => {
    navigate(path);
    setShowHeader(false);
    if (action) action();
  };

  const fetchData = async (endpoint, state) => {

    try {

        const response = await axios.get(endpoint);
        // console.log(`${endpoint}`, response.data);
        // state(response.data.results);
        console.log(`CATEGORIES`, response.data.results);
        const allCats: Category_[] = response.data.results; // Explicitly type `allCats`

        const uniqueTitles = Array.from(
            new Set(allCats.map((cat) => cat.title)) // Ensure `cat.title` is a string
        );

        let arr_: { 
          id: number | 0;
          title: string;
          category_hierarchy: string[];
          allegro_cat_id: string;
          slug: string;
          image: string;
        }[] = [];

        uniqueTitles.forEach((cat) => {
          arr_.push({
            id: 0,
            title: cat,
            category_hierarchy: [],
            allegro_cat_id: '',
            slug: '',
            image: '',
          });
        })

        // console.log(`uniqueTitles`, uniqueTitles);

        uniqueTitles.forEach((cat) => {
          for (let i = 0; i < allCats.length; i++) {
              if (cat === allCats[i]['title']) {
                // console.log('/////////////////', arr_[cat])
                const obj = arr_.find((item) => item.title === cat);
                if (obj) {
                  // console.log('allCats[category_hierarchy]', allCats[i]['category_hierarchy']);
                    obj.category_hierarchy.push(allCats[i]['category_hierarchy']); // Update category_hierarchy
                    obj.slug = allCats[i]['slug'];
                    obj.id = allCats[i]['id'];
                    obj.allegro_cat_id = allCats[i]['allegro_cat_id'];
                    obj.image = allCats[i]['image'];
                }
              }
          }
        });

      setCategories(arr_)

      console.log('arr_', arr_)
        
    } catch (error) {
        console.log('Products error', error)
    }

};

  useEffect(() => {
        fetchData('/api/store/categories', setCategories)
    }, [])


  return (
    <>
      {isMobile && (
        <button onClick={() => setShowHeader(prev => !prev)} className="menuButton">
          <MenuIcon />
        </button>
      )}

      {(!isMobile || showHeader) && (
        <div className="Header flexColumn gap-15">
          {isMobile ? (
            <>
              <div className="Cursor flexRowStart" onClick={() => closeMenuAndNavigate('/')}>
                <HomeRoundedIcon />
                <span className="ml-10">Głowna</span>
              </div>
              <div className="Cursor flexRowStart" onClick={() => closeMenuAndNavigate('/contact')}>
                <ContactMailRoundedIcon className="ml-5" />
                <span className="ml-10">Kontakt</span>
              </div>
              <div className="Cursor flexRowStart" onClick={() => closeMenuAndNavigate('/profile')}>
                <AccountCircleRoundedIcon className="ml-5" />
                <span className="ml-10">Profil</span>
              </div>
              <div className="Cursor flexRowStart" onClick={() => closeMenuAndNavigate('/cart')}>
                <Cart />
                {/* <span className="ml-10">Koszyk</span> */}
              </div>
              {user && (
                <LogoutRoundedIcon
                  onClick={() => {
                    logout();
                    setShowHeader(false);
                  }}
                  className="ml-15 Cursor"
                />
              )}
            </>
          ) : (
            <>
              <div className='flexRowStartHeader'>

                <div className="Cursor flexRowStart" onClick={() => navigate('/')}>
                  <HomeRoundedIcon />
                  <span>Kidnetic</span>
                </div>

                <div className="flexRowCenterHeader mr-30 ">
                  <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => {
                      setSearchTerm(e.target.value);
                      searchProducts();
                    }}
                    placeholder="Szukaj produktów..."
                    className="SearchInput w-400"
                  />
                </div>

                <div className='flexRowCenterHeader'>
                  <div className="Cursor " onClick={() => navigate('/contact')}>
                    <ContactMailRoundedIcon className="ml-5" />
                  </div>
                  <div className="Cursor " onClick={() => navigate('/profile')}>
                    <AccountCircleRoundedIcon className="ml-5" />
                  </div>
                  <div className="Cursor " onClick={() => navigate('/cart')}>
                    <Cart />
                  </div>
                  {user && (
                    <LogoutRoundedIcon
                      onClick={() => {
                        logout();
                        setShowHeader(false);
                      }}
                      className="ml-15 Cursor"
                    />
                  )}
                </div>

              </div>
            </>
          )}
        </div>
      )}
    </>
  );
}

export default Header