import React, { useEffect, useState } from 'react'
import axios from '../../utils/axios';
import '../../styles/product.css';
import HotSail from '../../components/product/HotSail';
import Likes from '../../components/product/Likes';
import Product from '../../components/product/Product';


const Products: React.FC = () => {

    const [products, setProducts] = useState<ProductType[]>([]);

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

    return (
        <div>
            {products?.map((product, index) => (
                <Product key={index} product={product} />
            ))}
        </div>
    )
}

export default Products
