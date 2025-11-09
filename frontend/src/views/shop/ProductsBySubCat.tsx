import React, { useCallback, useEffect, useState } from 'react'
import '../../types/ProductType'
import '../../types/CategoryType'
import { useLocation, useParams } from 'react-router-dom';
import axios from '../../utils/axios';
import Product from '../../components/product/Product';


const ProductsBySubCat: React.FC = () => {

  const [products, setProducts] = useState<ProductType[]>([]);
  const [category, setCategory] = useState<CategoryType | null>(null);
  const { slug } = useParams();
  const location = useLocation();
  // const subCat = location.state.subCat;
  const subCat = location.state?.subCat || slug;



  const fetchData = async (endpoint) => {

    try {
        const response = await axios.get(endpoint);
        // console.log(`${endpoint}`, response.data)
        setProducts(response.data.products);
        setCategory(response.data.category);
    } catch (error) {
        console.log('Products error', error)
    }

  };

  useEffect(() => {
      fetchData(`/api/store/sub-category-products/${subCat}`)
    // console.log('subCat', subCat)
  }, [])


  return (
    <div>
      <h2>{subCat}</h2>
        <div className='flexRowStart productCont'>
          {products?.map((product, index) => (
              <Product key={index} product={product} />
          ))}
        </div>
    </div>
  )
}

export default ProductsBySubCat;
