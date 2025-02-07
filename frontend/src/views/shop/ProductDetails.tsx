import React, { useEffect, useState } from 'react'
import { useLocation } from "react-router-dom";
import '../../types/ProductType'
import axios from '../../utils/axios';
import { API_BASE_URL } from '../../utils/constants';

const ProductDetails: React.FC = () => {

    const [products, setProducts] = useState<ProductType[]>([]);

    const location = useLocation();
    let product_ = location.state.slug

    // console.log('ProductDetails props', product)

    const fetchData = async (endpoint, state) => {

        try {
            const response = await axios.get(endpoint);
            console.log(`${endpoint}`, response.data)
            setProducts(response.data.results);
        } catch (error) {
            console.log('Products error', error)
        }

    };

    useEffect(() => {
        fetchData(`/api/store/product/${product_}`, setProducts)
    }, [product_])

    console.log('ProductDetails', products)

  return (
    <div>
        {products?.map((product, index) => (
            <div key={index}>
                <img src={`${API_BASE_URL}${product.image}`} alt="" className="productImage" />
                <p>{product.title}</p>
            </div>
            ))}
    </div>
  )
}

export default ProductDetails