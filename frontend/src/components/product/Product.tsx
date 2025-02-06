import React from 'react';
import HotSail from './HotSail';
import Likes from './Likes';

interface ProductProps {
    product: ProductType;
  }


const Product: React.FC<ProductProps> = ({product}) => {

    console.log('Product props', product)
  return (
    <div className='productCard'>
        <img src={product.image} alt="" width={200} />
        <p>{product.title}</p>
        {product.old_price && <p className='oldPrice'>{product.old_price}</p>}
        <p>{product.price}</p>
        {product.hot_deal && <HotSail />}  
        {product.product_rating && <Likes rating={String(product.product_rating)}/>}
    </div>
  )
}

export default Product