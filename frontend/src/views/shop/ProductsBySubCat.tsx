import React, { useCallback, useEffect, useState } from 'react'
import '../../types/ProductType'
import '../../types/CategoryType'
import { useLocation, useParams, useSearchParams } from 'react-router-dom';
import axios from '../../utils/axios';
import Product from '../../components/product/Product';
import DotsLoader from '../../components/DotsLoader';
import KeyboardArrowLeftRoundedIcon from '@mui/icons-material/KeyboardArrowLeftRounded';
import KeyboardArrowRightRoundedIcon from '@mui/icons-material/KeyboardArrowRightRounded';


const ProductsBySubCat: React.FC = () => {

  // const [products, setProducts] = useState<ProductType[]>([]);
  // const [category, setCategory] = useState<CategoryType | null>(null);
  // const { slug } = useParams();
  // const location = useLocation();
  // const subCat = location.state.subCat;
  // const subCat = location.state?.subCat || slug;



  // const fetchData = async (endpoint) => {

  //   try {
  //       const response = await axios.get(endpoint);
  //       // console.log(`${endpoint}`, response.data)
  //       setProducts(response.data.products);
  //       setCategory(response.data.category);
  //   } catch (error) {
  //       console.log('Products error', error)
  //   }

  // };

  // useEffect(() => {
  //     fetchData(`/api/store/sub-category-products/${subCat}`)
  //   // console.log('subCat', subCat)
  // }, [])


  // return (
  //   <div>
  //     <h2>{subCat}</h2>
  //       <div className='flexRowStart productCont'>
  //         {products?.map((product, index) => (
  //             <Product key={index} product={product} />
  //         ))}
  //       </div>
  //   </div>
  // )




  const [products, setProducts] = useState<ProductType[]>([]);
  const [category, setCategory] = useState<CategoryType | null>(null);
  const { slug } = useParams();
  const location = useLocation();
  const subCat = location.state.subCat;
  const [searchParams] = useSearchParams();
  const search = searchParams.get('search') || '';
  const [nextPage, setNextPage] = useState(null);
  const [prevPage, setPrevPage] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);
  const [isLoading, setIsLoading] = useState<boolean>(true);


  const fetchProducts = async ( url ) => {

        // console.log(`currentPage`, currentPage);
        setIsLoading(false);

        try {
           // const _url = search ? `${url}?search=${encodeURIComponent(search)}` : url;
            const hasQuery = url.includes('?');
            const _url = search
            ? `${url}${hasQuery ? '&' : '?'}search=${encodeURIComponent(search)}`
            : url;

            // console.log(`fetchProducts url --------`, _url);
            const response = await axios.get(_url);
            console.log(`fetchProducts response --------`, response);

            console.log(`${url}`, response.data)
            setProducts(response.data.results);
            setCategory(response.data.category);
            setNextPage(response.data.next);
            setPrevPage(response.data.previous);
            setIsLoading(true);
            // console.log(`nextPage`, nextPage);
            // console.log(`prevPage`, prevPage);

            // Calculate total pages
            const total = Math.ceil(response.data.count / 20);  // Since page_size = 50
            setTotalPages(total);
        } catch (error) {
            console.log('Products error', error)
        }

    };

  useEffect(() => {
      fetchProducts(`/api/store/sub-category-products/${subCat}?page=1`)
  }, [])

  useEffect(() => {
          const handleResize = () => setIsMobile(window.innerWidth <= 768);
          window.addEventListener('resize', handleResize);
          return () => window.removeEventListener('resize', handleResize);
      }, []);



  return (

        <>

        {isLoading === true ? (

          <div>

            <div className='flexRowCenter productCont'>

                {products?.map((product, index) => (
                     <Product key={index} product={product} /> 
                ))}
            </div>
            <div className='flexRowCenter footer-cont gap-15'>
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

        ):(

            <div className='flexColumnCenter gap-15'>
                <DotsLoader />
            </div>

        )} 

    </>
    )

}

export default ProductsBySubCat;
