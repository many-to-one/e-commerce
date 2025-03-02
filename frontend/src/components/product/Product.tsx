import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import HotSail from './HotSail';
import Likes from './Likes';
import '../../styles/product.css';
import { useNavigate } from 'react-router-dom';
import '../../types/ProductType';

interface ProductProps {
    product: ProductType;
  }


const Product: React.FC<ProductProps> = ({product}) => {

  console.log('Product props', product)
  const navigate = useNavigate();

  useEffect(() => {
    if (product.gallery.length === 1 ) {

    }
  }, [])

  return (
    <div
      className='productCard' 
      onClick={() => navigate(`/product-details/${product.slug}`, {state:{ id: product.id, catId: product.category}})}
     >
        <div className='productImageCont'>

          { product.gallery.length === 0 ? (
            <img src={product.img_links[0]} alt="" className='productImage'/>
          ):(
            <img src={product.image} alt="" className='productImage'/>
          )}
    
        </div>
        <p>{product.title}</p>
          <div className='flexRowStart gap-15'>
            {product.old_price !== '0.00' && <p className='oldPrice'>{product.old_price}$</p>}
            <p>{product.price}$</p>
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