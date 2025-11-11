import React, { useCallback, useEffect, useState } from 'react';
import axios from '../../utils/axios';
import { useAuthStore } from "../../store/auth";
import Product from '../../components/product/Product';
import '../../types/ProductType';
import '../../types/CategoryType';
import KeyboardArrowLeftRoundedIcon from '@mui/icons-material/KeyboardArrowLeftRounded';
import KeyboardArrowRightRoundedIcon from '@mui/icons-material/KeyboardArrowRightRounded';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { debounce } from 'lodash';
import DotsLoader from '../../components/DotsLoader';
// import Swiper core and required modules
import { Swiper, SwiperSlide } from 'swiper/react';
import { Navigation, Pagination, Scrollbar, A11y } from 'swiper/modules';
import 'swiper/css';
import '../../styles/products.css'; // new styles for layout and Swiper
import CustomSwiper from "../../components/CustomSwiper";

const Products: React.FC = () => {
  const isLoggedIn = useAuthStore((state) => state.isLoggedIn);
  const [searchParams] = useSearchParams();
  const search = searchParams.get('search') || '';

  const [products, setProducts] = useState<ProductType[]>([]);
  const [recommended, setRecommended] = useState<ProductType[]>([]);
  const [discounts, setDiscounts] = useState<ProductType[]>([]);
  const [news, setNews] = useState<ProductType[]>([]);

  const [nextPage, setNextPage] = useState<string | null>(null);
  const [prevPage, setPrevPage] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);

  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const navigate = useNavigate();

  const fetchProducts = async (url: string) => {
    setIsLoading(false);
    try {
      const hasQuery = url.includes('?');
      const _url = search
        ? `${url}${hasQuery ? '&' : '?'}search=${encodeURIComponent(search)}`
        : url;

      const response = await axios.get(_url);
      setProducts(response.data.results);
      setNextPage(response.data.next);
      setPrevPage(response.data.previous);
      setIsLoading(true);

      const total = Math.ceil(response.data.count / 20);
      setTotalPages(total);
    } catch (error) {
      console.log('Products error', error);
    }
  };

  const fetchSections = async () => {
    try {
      const [rec, disc, newp] = await Promise.all([
        axios.get('/api/store/popular'),
        axios.get('/api/store/discounts'),
        axios.get('/api/store/news'),
      ]);
      setRecommended(rec.data.results || []);
      setDiscounts(disc.data.results || []);
      setNews(newp.data.results || []);
    //   console.log('setRecommended-----', rec.data.results)
    } catch (err) {
      console.log('Section fetch error:', err);
    }
  };

  useEffect(() => {
    fetchProducts('/api/store/products?page=1');
    fetchSections();
  }, []);


  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);



  const renderSwiperSection = (title: string, data: ProductType[]) => (
    <section className="product-section">
      <h2>{title}</h2>
      <Swiper
      modules={[Navigation, Pagination, Scrollbar, A11y]}
        spaceBetween={15}
        slidesPerView={3}
        preventClicks={false}
        preventClicksPropagation={false}
        navigation
        pagination={{ clickable: true }}
        scrollbar={{ draggable: true }}
        // onSwiper={(swiper) => console.log(swiper)}
        // onSlideChange={() => console.log('slide change')}
        breakpoints={{
          748: { slidesPerView: 3 },
          1024: { slidesPerView: 4 },
          1400: { slidesPerView: 5 },
        }}
      >
        {data.map((product, index) => (
          <SwiperSlide key={product.id ?? index}>
              <Product product={product} />
          </SwiperSlide>
        ))}
      </Swiper>

    </section>
  );


  return (
    <>
      {isLoading ? (
        <div className="products-page">

          {/* Swiper sections */}
          {/* {renderSwiperSection('Polecane produkty', recommended)}
          {renderSwiperSection('Promocje', discounts)}
          {renderSwiperSection('Nowości', news)} */}



          {/* Regular paginated product list */}
          <div className="flexRowCenter productCont">
            {products?.map((product, index) => (
              <Product key={index} product={product} />
            ))}
          </div>

          {/* Pagination controls */}
          <div className="flexRowCenter gap-15 mt-20">
            <button
              onClick={() => {
                if (prevPage) {
                  fetchProducts(prevPage);
                  setCurrentPage((prev) => prev - 1);
                }
              }}
              disabled={!prevPage}
            >
              <KeyboardArrowLeftRoundedIcon />
            </button>

            <span>{currentPage}</span>
            <span>...</span>
            <span>{totalPages}</span>

            <button
              onClick={() => {
                if (nextPage) {
                  fetchProducts(nextPage);
                  setCurrentPage((prev) => prev + 1);
                }
              }}
              disabled={!nextPage}
            >
              <KeyboardArrowRightRoundedIcon />
            </button>
          </div>
        </div>
      ) : (
        <div className="flexColumnCenter gap-15">
          <DotsLoader />
        </div>
      )}
    </>
  );
};

export default Products;
