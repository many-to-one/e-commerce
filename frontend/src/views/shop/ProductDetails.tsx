import React, { useEffect, useState } from 'react'
import { useLocation, useParams } from "react-router-dom";
import '../../types/ProductType';
import '../../types/GalleryType'
import axios from '../../utils/axios';
import { API_BASE_URL } from '../../utils/constants';
import Likes from '../../components/product/Likes';
import StockCounter from '../../components/product/StockCounter';


const ProductDetails: React.FC = () => {

    const [product, setProduct] = useState<ProductType | null>(null);
    const [gallery, setgallery] = useState<GalleryType[]>([]);
    const [orderQuantity, setOrderQuantity] = useState<number>(1);

    const { slug } = useParams();

    const fetchData = async (endpoint) => {

        try {
            const response = await axios.get(endpoint);
            console.log(`${endpoint}`, response.data)
            setProduct(response.data.product);
            setgallery(response.data.gallery);
        } catch (error) {
            console.log('Products error', error)
        }

    };

    useEffect(() => {
        fetchData(`/api/store/product/${slug}`)
    }, [slug])


    const handleQuantityChange = (newQuantity) => {
        setOrderQuantity(newQuantity);
        // You can also perform additional actions here, such as updating the total price
        console.log('handleQuantityChange', newQuantity)
      };

  return (
    <div className='flexColumnCenter'>
        <div className='flexRowStart gap-50'>
            <div className='flexColumnCenter'>
                <img src={`${API_BASE_URL}${product?.image}`} alt="" className="mainGalleryImage" />
                <div className='flexRowStart'>
                    {gallery?.map((gall, index) => (
                        <img src={`${API_BASE_URL}${gall.image}`} alt="" className="galleryImage" key={index} />
                    ))}
                </div>
            </div>
            <div>
                <h2>{product?.title}</h2>
                <p>Brand: {product?.brand}</p>
                <p className='flexRowCenter'>Price: {product?.old_price !== '0.00' && <p className='oldPrice'>{product?.old_price}$</p> } {product?.price}$</p>
                <p>Shipping: {product?.shipping_amount}$</p>
                <p>Stock: {product?.stock_qty} pcs.</p>
                {product?.product_rating !== null ? (
                    <Likes rating={String(product?.product_rating)}/>
                    ) : (
                    <Likes rating={String(0)}/>
                )}

                <StockCounter initialQty={orderQuantity} onQuantityChange={handleQuantityChange}/>

            </div>
        </div>
        <p>{product?.description}</p>
    </div>
  )
}

export default ProductDetails