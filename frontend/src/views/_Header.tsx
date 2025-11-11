import React, { useCallback, useEffect, useRef, useState } from 'react';
import Cart from '../components/product/Cart';
import useAxios from '../utils/useAxios';
import axios from 'axios';
import { debounce } from 'lodash';
import { useNavigate } from 'react-router-dom';
import Category from '../components/category/Category';
import { __userId, login, logout } from '../utils/auth';
import '../styles/header.css'; // new colorful design
import AccountCircleRoundedIcon from '@mui/icons-material/AccountCircleRounded';
import LogoutRoundedIcon from '@mui/icons-material/LogoutRounded';
import LoginRoundedIcon from '@mui/icons-material/LoginRounded';
import HomeRoundedIcon from '@mui/icons-material/HomeRounded';
import ContactMailRoundedIcon from '@mui/icons-material/ContactMailRounded';
import MenuIcon from '@mui/icons-material/Menu';
import ArticleRoundedIcon from '@mui/icons-material/ArticleRounded';
import { API_BASE_URL } from '../utils/constants';

function _Header() {
  const user = __userId();
  const navigate = useNavigate();
  const _axios = useAxios();
  const [categories, setCategories] = useState([]);
  const [showCategories, setShowCategories] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);
  const [showHeader, setShowHeader] = useState(false);


  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const closeMenuAndNavigate = (path, action) => {
    navigate(path);
    setShowHeader(false);
    if (action) action();
    window.location.reload();
  };

  const goMainPage = () => {
    navigate('/')
    window.location.reload();
  }

  const fetchData = async () => {
    const endpoint = user ? '/api/store/categories' : `${API_BASE_URL}api/store/categories`;
    try {
      const response = user ? await _axios.get(endpoint) : await axios.get(endpoint);
      setCategories(response.data.results || []);
    } catch (error) {
      console.log('Category fetch error', error);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

// 1️⃣ Create the debounced function inside useRef
const debouncedSearchRef = useRef(
  debounce((value: string) => {
    navigate(`/?search=${encodeURIComponent(value)}`);
    window.location.reload();
  }, 1500)
);

// 2️⃣ Handler calls the debounced function
const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
  debouncedSearchRef.current(e.target.value);
};

  return (
    <header className="toy-header">
      <div className="toy-header-inner">
        <div className="toy-logo" onClick={() => goMainPage()}>
          <HomeRoundedIcon /> <span>Kidnetic</span>
        </div>


          {!isMobile && (
            <div className="Cursor Cat showCat" 
                    onMouseEnter={() => setShowCategories(true)} 
                    onMouseLeave={() => setShowCategories(false)} 
                  > 
                    <ArticleRoundedIcon /> Kategorie 
                    {showCategories && (
                      <div className="categoryTitles"> 
                        {categories?.map((category, index) => ( 
                          <Category key={index} category={category} /> 
                        ))} 
                      </div> 
                      )} 
                  </div>
          )}

        <div className="toy-search">
            <input
                type="text"
                // onChange={(e) => debouncedSearch(e.target.value)}
                onChange={handleInputChange}
                placeholder="Szukaj produktów.."
                className="SearchInput w-400"
              />
          </div>
          

        <div className="toy-actions">
          <div className="toy-icon" onClick={() => navigate('/contact')}>
            <ContactMailRoundedIcon />
          </div>
          <div className="toy-icon" onClick={() => navigate('/profile')}>
            <AccountCircleRoundedIcon />
          </div>
          <div className="toy-icon" onClick={() => navigate('/order')}>
            <Cart />
          </div>
          {user ? (
            <LogoutRoundedIcon onClick={logout} className="toy-icon" />
          ) : (
            <LoginRoundedIcon onClick={() => navigate('/login')} className="toy-icon" />
          )}
        </div>

        <button className="toy-menu-btn" onClick={() => setShowHeader(!showHeader)}>
          <MenuIcon />
        </button>
      </div>

      {showHeader && isMobile && (
        <div className="toy-mobile-menu">
          <div className="toy-mobile-link" onClick={() => closeMenuAndNavigate('/')}>
            <HomeRoundedIcon /> Strona główna
          </div>
          <div
            className="toy-mobile-link"
            onClick={() => setShowCategories((prev) => !prev)}
          >
            <ArticleRoundedIcon /> Kategorie
          </div>
          {showCategories && (
            <div className="toy-mobile-categories">
              {categories.map((c, i) => (
                <Category key={i} category={c} />
              ))}
            </div>
          )}

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
        </div>
      )}
    </header>
  );
}

export default _Header;
