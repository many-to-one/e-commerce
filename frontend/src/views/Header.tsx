import React, { useCallback, useEffect, useState } from 'react'
import Cart from '../components/product/Cart'
import useAxios from '../utils/useAxios';
import axios from 'axios';
import { useAuthStore } from '../store/auth';
import { useNavigate } from 'react-router-dom';
import Category from '../components/category/Category';
import Profile from './shop/Profile';
// import MaterialIcon from '@material/react-material-icon';
import { __userId, login, logout } from '../utils/auth';
import '../types/SortCategory';

import AccountCircleRoundedIcon from '@mui/icons-material/AccountCircleRounded';
import LogoutRoundedIcon from '@mui/icons-material/LogoutRounded';
import LoginRoundedIcon from '@mui/icons-material/LoginRounded';
import HomeRoundedIcon from '@mui/icons-material/HomeRounded';
import ContactMailRoundedIcon from '@mui/icons-material/ContactMailRounded';
import MenuIcon from '@mui/icons-material/Menu';

import CategoryType from '../types/CategoryType';
import { useProductStore } from '../store/products';
import { API_BASE_URL } from '../utils/constants';

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
  const _axios = useAxios();
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

    // const isLoggedIn = useAuthStore((state) => state.isLoggedIn);
    // console.log('Header-isLoggedIn', isLoggedIn);

  const fetchDataAuth = async (endpoint: string, state: (data: any) => void) => {
    try {
      const response = await _axios.get(endpoint);
      // console.log(`CATEGORIES (auth)`, response.data.results);
      processCategories(response.data.results, state);
    } catch (error) {
      console.log('Products error (auth)', error);
    }
  };


  const fetchDataPublic = async (endpoint: string, state: (data: any) => void) => {
    try {
      const response = await axios.get(endpoint);
      // console.log(`CATEGORIES (public)`, response.data.results);
      processCategories(response.data.results, state);
    } catch (error) {
      console.log('Products error (public)', error);
    }
  };


  const processCategories = (allCats: Category_[], state: (data: any) => void) => {
    const uniqueTitles = Array.from(new Set(allCats.map((cat) => cat.title)));

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
    });

    uniqueTitles.forEach((cat) => {
      for (let i = 0; i < allCats.length; i++) {
        if (cat === allCats[i]['title']) {
          const obj = arr_.find((item) => item.title === cat);
          if (obj) {
            obj.category_hierarchy.push(allCats[i]['category_hierarchy']);
            obj.slug = allCats[i]['slug'];
            obj.id = allCats[i]['id'];
            obj.allegro_cat_id = allCats[i]['allegro_cat_id'];
            obj.image = allCats[i]['image'];
          }
        }
      }
    });

    state(arr_);
    console.log('arr_', arr_);
  };


  useEffect(() => {
    const endpoint = '/api/store/categories';
    const publicEndpoint = `${API_BASE_URL}api/store/categories`;
    if (user) {
      fetchDataAuth(endpoint, setCategories);
    } else {
      fetchDataPublic(publicEndpoint, setCategories);
    }
  }, [user]);



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

                <div className="Cursor showCat" 
                    onMouseEnter={() => setShowCategories(true)} 
                    onMouseLeave={() => setShowCategories(false)} 
                  > 
                    Kategorie 
                    {showCategories && (
                      <div className="categoryTitles"> 
                        {categories?.map((category, index) => ( 
                          <Category key={index} category={category} /> 
                        ))} 
                      </div> 
                      )} 
                  </div>

              </div>
              <div className="Cursor flexRowStart" onClick={() => closeMenuAndNavigate('/contact')}>
                <ContactMailRoundedIcon className="ml-5" />
                <span className="ml-10">Kontakt</span>
              </div>
              <div className="Cursor flexRowStart" onClick={() => closeMenuAndNavigate('/profile')}>
                <AccountCircleRoundedIcon className="ml-5" />
                <span className="ml-10">Profil</span>
              </div>
              <div className="Cursor flexRowStart" onClick={() => closeMenuAndNavigate('/order')}>
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
              {!user && (
                <LoginRoundedIcon
                  onClick={() => {
                    navigate('/login');
                    setShowHeader(true);
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

                <div className="Cursor Cat showCat" 
                    onMouseEnter={() => setShowCategories(true)} 
                    onMouseLeave={() => setShowCategories(false)} 
                  > 
                    Kategorie 
                    {showCategories && (
                      <div className="categoryTitles"> 
                        {categories?.map((category, index) => ( 
                          <Category key={index} category={category} /> 
                        ))} 
                      </div> 
                      )} 
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
                  <div className="Cursor " onClick={() => navigate('/order')}>
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
                  {!user && (
                    <LoginRoundedIcon
                      onClick={() => {
                        navigate('/login');
                        setShowHeader(true);
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