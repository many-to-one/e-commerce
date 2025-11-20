import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import HotSail from './HotSail';
import Likes from './Likes';
import '../../styles/product.css';
import { useNavigate } from 'react-router-dom';
import '../../types/ProductType';
import { API_BASE_URL, IMG_BASE_URL } from '../../utils/constants';

interface ProductProps {
    product: ProductType;
  }


const Product: React.FC<ProductProps> = ({product}) => {

  console.log('Product props', product)
  const navigate = useNavigate();

  // useEffect(() => {
  //   if (product.gallery.length === 1 ) {

  //   }
  // }, [])


  // const thumb = product.thumbnail?.replace('http://', 'http://'); // Development
  const thumb = product.thumbnail?.replace('http://', 'https://'); // Production
  // console.log('thumb-------', thumb)

  return (
    <div
      className='product-card product-info' 
      onClick={() => navigate(`/product-details/${product.slug}`, {state:{ id: product.id, catId: product.category}})}
     >
        <div>

         {thumb ? (
            <picture>
              <source srcSet={thumb} type="image/webp" />
              <img
                src={thumb}
                alt="Product"
                width={200}
                height={200}
                loading="lazy"
                // style={{ objectFit: 'cover' }}
                draggable={false}
                onDragStart={(e) => e.preventDefault()}
                style={{
                  touchAction: 'pan-y',       // allow vertical page scroll, allow horizontal swipes
                  // WebkitUserDrag: 'none',
                  userSelect: 'none',
                }}
              />
            </picture>
          ) : (
            <picture>
              <source
                srcSet={`${API_BASE_URL}api/store/resize?url=${product.img_links[1]}&w=200&h=200`}
                type="image/webp"
              />
              <source
                srcSet={`${API_BASE_URL}api/store/resize?url=${product.img_links[1]}&w=200&h=200&format=jpg`}
                type="image/jpeg"
              />
              <img
                src={product.img_links[0]}
                alt="Product"
                width={200}
                height={200}
                loading="lazy"
                // style={{ objectFit: 'cover' }}
                draggable={false}
                onDragStart={(e) => e.preventDefault()}
                style={{
                  touchAction: 'pan-y',       // allow vertical page scroll, allow horizontal swipes
                  // WebkitUserDrag: 'none',
                  userSelect: 'none',
                }}
              />
            </picture>
          )}
    
        </div>
        {/* <h3>{product.title}</h3> */}
        <h3>
          {product.title.length > 30 
            ? product.title.slice(0, 30) + "..." 
            : product.title}
        </h3>

          <div className='price'>
            {product.old_price !== '0.00' && <p className='oldPrice'>{product.old_price} PLN</p>}
            <p>{product.price_brutto} PLN</p>
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