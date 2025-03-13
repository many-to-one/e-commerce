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
import MaterialIcon from '@material/react-material-icon';


const Products: React.FC = () => {

    const isLoggedIn = useAuthStore((state) => state.isLoggedIn);
    const user = useAuthStore((state) => state.user);
    // console.log('isLoggedIn', isLoggedIn)
    // console.log('user', user)

    const [products, setProducts] = useState<ProductType[]>([]);
    // const [categories, setCategories] = useState<CategoryType[]>([]);
    const [nextPage, setNextPage] = useState(null);
    const [prevPage, setPrevPage] = useState(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);


    const fetchProducts = async (url) => {

        console.log(`url`, url);
        console.log(`currentPage`, currentPage);

        try {
            const response = await axios.get(url);
            console.log(`${url}`, response.data)
            setProducts(response.data.results);
            setNextPage(response.data.next);
            setPrevPage(response.data.previous);
            console.log(`nextPage`, nextPage);
            console.log(`prevPage`, prevPage);

            // Calculate total pages
            const total = Math.ceil(response.data.count / 50);  // Since page_size = 50
            setTotalPages(total);
        } catch (error) {
            console.log('Products error', error)
        }

    };

    useEffect(() => {
        fetchProducts('/api/store/products?page=1')
    }, [])
    
    

    return (
        <div>
            <div className='flexRowStart productCont'>
                {products?.map((product, index) => (
                     <Product key={index} product={product} />
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
                    <MaterialIcon icon="arrow_back_ios"/>
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
                    <MaterialIcon icon="arrow_forward_ios"/>
                </button>
            </div>
        </div>
    )
}

export default Products
