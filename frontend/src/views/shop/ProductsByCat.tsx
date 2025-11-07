import React, { useCallback, useEffect, useState } from 'react'
import '../../types/ProductType'
import '../../types/CategoryType'
import { useLocation, useParams } from 'react-router-dom';
import axios from '../../utils/axios';
import Product from '../../components/product/Product';


const ProductsByCat: React.FC = () => {

  const [products, setProducts] = useState<ProductType[]>([]);
  const [category, setCategory] = useState<CategoryType | null>(null);
  const { slug } = useParams();
  const location = useLocation();
  const catId = location.state.catId;

  const fetchData = async (endpoint) => {

    // console.log('catId----------------', catId)

    try {
        const response = await axios.get(endpoint);
        console.log(`${endpoint}`, response.data)
        setProducts(response.data.products);
        setCategory(response.data.category);
    } catch (error) {
        console.log('Products error', error)
    }

  };

  useEffect(() => {
      fetchData(`/api/store/category-products/${catId}`)
  }, [])


  return (
    <div>
      <h2>{category?.title}</h2>
        <div className='flexRowStart productCont'>
          {products?.map((product, index) => (
              <Product key={index} product={product} />
          ))}
        </div>
    </div>
  )
}

export default ProductsByCat