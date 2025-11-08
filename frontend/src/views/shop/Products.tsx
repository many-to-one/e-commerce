import React, { useEffect, useState } from 'react'
import axios from '../../utils/axios';
import { useAuthStore } from "../../store/auth";
import HotSail from '../../components/product/HotSail';
import Likes from '../../components/product/Likes';
import Product from '../../components/product/Product';
import '../../types/ProductType';
import '../../types/CategoryType';
import Category from '../../components/category/Category';
import Swal from 'sweetalert2';
import KeyboardArrowLeftRoundedIcon from '@mui/icons-material/KeyboardArrowLeftRounded';
import KeyboardArrowRightRoundedIcon from '@mui/icons-material/KeyboardArrowRightRounded';
import { useProductStore } from '../../store/products';


const Products: React.FC = () => {

    const isLoggedIn = useAuthStore((state) => state.isLoggedIn);
    // console.log('isLoggedIn', isLoggedIn)
    // console.log('user', user)

    // const [products, setProducts] = useState<ProductType[]>([]);
    // const [categories, setCategories] = useState<CategoryType[]>([]);
    const [nextPage, setNextPage] = useState(null);
    const [prevPage, setPrevPage] = useState(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    const {
        allProducts,
        filteredProducts,
        setProducts,
        setLoading,
        searchTerm,
        setSearchTerm,
        searchProducts,
    } = useProductStore();


    // const fetchProducts = async ( url ) => {

    //     // const timestampedUrl = `${url}&t=${Date.now()}`
    //     // console.log(`timestampedUrl`, timestampedUrl);
    //     console.log(`fetchProducts url --------`, url);
    //     console.log(`currentPage`, currentPage);

    //     try {
    //         const response = await axios.get(url);

    //         console.log(`${url}`, response.data)
    //         setProducts(response.data.results);
    //         setNextPage(response.data.next);
    //         setPrevPage(response.data.previous);
    //         console.log(`nextPage`, nextPage);
    //         console.log(`prevPage`, prevPage);

    //         // Calculate total pages
    //         const total = Math.ceil(response.data.count / 50);  // Since page_size = 50
    //         setTotalPages(total);
    //     } catch (error) {
    //         console.log('Products error', error)
    //     }

    // };


    // -------------------- Zustang logic for search -------------------- //
    const fetchProducts = async (url: string) => {
        console.log('allProducts', allProducts)
        setLoading(true);
        try {
        const response = await axios.get(url);
        const products = response.data.results;
        console.log('fetchProducts', products)
        setProducts(products);
        setNextPage(response.data.next);
        setPrevPage(response.data.previous);
        setTotalPages(Math.ceil(response.data.count / 50));
        } catch (error) {
        console.error('Products error', error);
        } finally {
        setLoading(false);
        }
    };

    useEffect(() => {
    if (allProducts) {
        // console.log('✅ Products loaded:', allProducts.length);
        searchProducts(); // optional: trigger initial search
    }
    }, [allProducts]);

    useEffect(() => {
    if (allProducts) {
        searchProducts();
    }
    }, [allProducts]);

 // -------------------- End of Zustang logic for search -------------------- //


    useEffect(() => {
        fetchProducts('/api/store/products?page=1')
    }, [])
    
    

    return (
        <div>
            <div className='flexRowCenter productCont'>

                {/* {products?.map((product, index) => (
                     <Product key={index} product={product} />
                ))} */}
                {filteredProducts.map(product => (
                    <Product key={product.id} product={product} />
                    ))}
            </div>
            <div className='flexRowCenter gap-15 mt-20'>
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
    )
}

export default Products
