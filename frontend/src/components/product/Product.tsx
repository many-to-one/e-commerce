import React from 'react';
import { Link } from 'react-router-dom';
import HotSail from './HotSail';
import Likes from './Likes';
import '../../styles/product.css';
import { useNavigate } from 'react-router-dom';

interface ProductProps {
    product: ProductType;
  }


const Product: React.FC<ProductProps> = ({product}) => {

  console.log('Product props', product)
  const navigate = useNavigate();

  return (
    <div
      className='productCard' 
      onClick={() => navigate(`/product-details/${product.slug}`)} //{state: {slug: product.slug}}
     >
        <img src={product.image} alt="" className='productImage'/>
        <p>{product.title}</p>
        <div>
          {product.old_price !== '0.00' && <p className='oldPrice'>{product.old_price}</p>}
          <p>{product.price}</p>
        </div>
        {product.hot_deal  && <HotSail />}  
        {product.product_rating !== null ? (
          <Likes rating={String(product.product_rating)}/>
        ) : (
          <Likes rating={String(0)}/>
        )}
    </div>
  )
}

export default Product