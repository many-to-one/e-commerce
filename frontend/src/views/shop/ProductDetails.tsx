import React, { useEffect, useRef, useState } from 'react'
import { useLocation, useParams } from "react-router-dom";
import '../../types/ProductType';
import '../../types/GalleryType'
import axios from '../../utils/axios';
import { API_BASE_URL } from '../../utils/constants';
import Likes from '../../components/product/Likes';
import StockCounter from '../../components/product/StockCounter';
import AddToCard from '../../components/product/AddToCard';
import DoLike from '../../components/product/DoLike';


const ProductDetails: React.FC = () => {

    const imageRef = useRef<HTMLImageElement | null>(null);

    const [product, setProduct] = useState<ProductType | null>(null);
    const [mainImg, setMainImg] = useState<string>('');
    const [gallery, setGallery] = useState<GalleryType[]>([]);
    const [orderQuantity, setOrderQuantity] = useState<number>(1);

    const { slug } = useParams();

    const fetchData = async (endpoint) => {

        try {
            const response = await axios.get(endpoint);
            console.log(`${endpoint}`, response.data)
            setProduct(response.data.product);
            setMainImg(response.data.product.image)
            setGallery(response.data.gallery);
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

    const updateMainImg = (image) => {
        setMainImg('');
        setMainImg(image);
    }

    const scaleImg = (event: React.MouseEvent<HTMLImageElement, MouseEvent>) => {
        if (imageRef.current) {
            const { offsetX, offsetY, target } = event.nativeEvent;
            const { clientWidth, clientHeight } = event.currentTarget;

            const moveX = ((offsetX / clientWidth) - 0.1) * 100; 
            const moveY = ((offsetY / clientHeight) - 0.1) * 100

            imageRef.current.style.transform = `scale(1.8) translate(${moveX}px, ${moveY}px)`;
        }
    };

    const resetImg = () => {
        if (imageRef.current) {
            imageRef.current.style.transform = "scale(1)"; // Resets back to 100%
        }
    };

  return (
    <div className='flexColumnCenter productDetailCont'>
        <div className='flexRowStart gap-50'>
            <div className='flexColumnCenter'>
                <div className='miGallCont'>
                    <img 
                        src={mainImg} 
                        alt="" 
                        className="mainGalleryImage" 
                        ref={imageRef}
                        onMouseMove={scaleImg} 
                        onMouseOut={resetImg} 
                    />
                </div>
                <div className='flexRowStart'>
                    {gallery?.map((gall, index) => (
                        <img src={gall.image} alt="" className="galleryImage" key={index} onMouseOver={() => updateMainImg(gall.image)} />
                    ))}
                </div>
            </div>
            <div>
                <h2>{product?.title}</h2>
                <p>Brand: {product?.brand}</p>
                <div className='flexRowCenter'>Price: {product?.old_price !== '0.00' && <p className='oldPrice'>{product?.old_price}$</p> } {product?.price}$</div>
                <p>Shipping: {product?.shipping_amount}$</p>
                <p>Stock: {product?.stock_qty} pcs.</p>
                {product?.product_rating !== null ? (
                    <Likes rating={String(product?.product_rating)}/>
                    ) : (
                    <Likes rating={String(0)}/>
                )}

                <StockCounter initialQty={orderQuantity} onQuantityChange={handleQuantityChange}/>
                <br />

                {product?.id && 
                    <AddToCard id={product.id} quantity={orderQuantity} />
                }
                <br />

                <DoLike />

            </div>
        </div>
        <p>{product?.description}</p>
    </div>
  )
}

export default ProductDetails