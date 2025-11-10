import React, { useCallback, useEffect, useState } from 'react'
import '../../types/ProductType'
import '../../types/CategoryType'
import { useLocation, useParams } from 'react-router-dom';
import axios from '../../utils/axios';
import Product from '../../components/product/Product';
import DotsLoader from '../../components/DotsLoader';


const ProductsByCat: React.FC = () => {

  const [products, setProducts] = useState<ProductType[]>([]);
  const [category, setCategory] = useState<CategoryType | null>(null);
  const { slug } = useParams();
  const location = useLocation();
  const catId = location.state.catId;

  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchData = async (endpoint) => {

    // console.log('catId----------------', catId)

    setIsLoading(false);

    try {
        const response = await axios.get(endpoint);
        // console.log(`${endpoint}`, response.data)
        setProducts(response.data.products);
        setCategory(response.data.category);
        setIsLoading(true);
    } catch (error) {
        console.log('Products error', error)
    }

  };

  useEffect(() => {
      fetchData(`/api/store/category-products/${catId}`)
  }, [])


  return (
    <>
    {isLoading ? (
      <div className='products-page'>
        <h2>{category?.title}</h2>
        <div className='flexRowStart productCont'>
          {products?.map((product, index) => (
              <Product key={index} product={product} />
          ))}
        </div>
      </div>
    ):(
      <div className="flexColumnCenter gap-15">
        <DotsLoader />
      </div>
    )}
    
    </>
  )
}

export default ProductsByCat