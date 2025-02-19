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


const Products: React.FC = () => {

    const isLoggedIn = useAuthStore((state) => state.isLoggedIn);
    const user = useAuthStore((state) => state.user);
    // console.log('isLoggedIn', isLoggedIn)
    // console.log('user', user)

    const [products, setProducts] = useState<ProductType[]>([]);
    const [categories, setCategories] = useState<CategoryType[]>([]);

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
        fetchData('/api/store/products', setProducts)
    }, [])

    useEffect(() => {
        fetchData('/api/store/categories', setCategories)
    }, [])

    return (
        <div>
            {/* <h3>{user}</h3> */}
            <div className='flexRowStart'>
                {categories?.map((category, index) => (
                    <Category key={index} category={category} />
                ))}
            </div>
            <div className='flexRowStart productCont'>
                {products?.map((product, index) => (
                     <Product key={index} product={product} />
                ))}
            </div>
        </div>
    )
}

export default Products
