import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import HotSail from './HotSail';
import Likes from './Likes';
import '../../styles/product.css';
import { useNavigate } from 'react-router-dom';
import '../../types/ProductType';
import { API_BASE_URL } from '../../utils/constants';

interface ProductProps {
    product: ProductType;
  }


const Product: React.FC<ProductProps> = ({product}) => {

  // console.log('Product props', product)
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

         {product.thumbnail ? (
            <picture>
              <source srcSet={product.thumbnail} type="image/webp" />
              <img
                src={product.thumbnail}
                alt="Product"
                width={200}
                height={200}
                loading="lazy"
                style={{ objectFit: 'cover' }}
              />
            </picture>
          ) : (
            <picture>
              <source
                srcSet={`${API_BASE_URL}api/store/resize?url=${product.img_links[0]}&w=200&h=200`}
                type="image/webp"
              />
              <source
                srcSet={`${API_BASE_URL}api/store/resize?url=${product.img_links[0]}&w=200&h=200&format=jpg`}
                type="image/jpeg"
              />
              <img
                src={product.img_links[0]}
                alt="Product"
                width={200}
                height={200}
                loading="lazy"
                style={{ objectFit: 'cover' }}
              />
            </picture>
          )}
    
        </div>
        <p>{product.title}</p>
          <div className='flexRowStart gap-15'>
            {product.old_price !== '0.00' && <p className='oldPrice'>{product.old_price} PLN</p>}
            <p>{product.price} PLN</p>
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