import React, { useEffect, useRef, useState } from 'react'
import { useLocation, useParams } from "react-router-dom";

import { Swiper, SwiperSlide } from 'swiper/react';
import 'swiper/css';
import 'swiper/css/navigation';
import "swiper/css/pagination";
import { Navigation } from 'swiper/modules';

import DOMPurify from 'dompurify'; // for safelly rendering HTML from string in product description


import '../../types/ProductType';
import '../../types/GalleryType'
import axios from '../../utils/axios';
import { API_BASE_URL } from '../../utils/constants';
import Likes from '../../components/product/Likes';
import StockCounter from '../../components/product/StockCounter';
import AddToCard from '../../components/product/AddToCard';
import DoLike from '../../components/product/DoLike';
import ProductsByCat from './ProductsByCat';
import Product from '../../components/product/Product';


const ProductDetails: React.FC = () => {

    const imageRef = useRef<HTMLImageElement | null>(null);

    const [product, setProduct] = useState<ProductType | null>(null);
    const [products, setProducts] = useState<ProductType[]>([]);
    const [mainImg, setMainImg] = useState<string>('');
    const [gallery, setGallery] = useState<GalleryType[]>([]);
    const [orderQuantity, setOrderQuantity] = useState<number>(1);

    const { slug } = useParams();
    const location = useLocation();
    const prodId = location.state.id;
    const catId = location.state.catId;
    console.log('catId', catId)

    useEffect(() => {
        window.scrollTo(0, 0); // Scroll to top
    }, [slug]);

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
        fetchData(`/api/store/product/${prodId}`)
    }, [slug])

    const catProducts = async () => {

        try {
            const response = await axios.get(`/api/store/category-products/${catId}`);
            console.log(`catProducts`, response.data)
            setProducts(response.data.products)
        } catch (error) {
            console.log('Products error', error)
        }

    }

    useEffect(() => {
          catProducts()
      }, [catId])


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
    <div className='flexColumnCenter'>

        <div className='productDetailCont'>
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

                    {/* <div className='flexRowCenter'>
                        {gallery?.map((gall, index) => (
                            <img src={gall.image} alt="" className="galleryImage" key={index} onMouseOver={() => updateMainImg(gall.image)} />
                        ))}
                    </div> */}

                    <div className='flexRowCenter'>
                        <Swiper
                            grabCursor={true}
                            spaceBetween={10}
                            // modules={[Navigation]}
                            slidesPerView={3}
                            navigation={true}
                            pagination={true}
                            className="gallerySwiper"
                        >
                            {gallery.map((gall, index) => {
                            return (
                                <SwiperSlide key={index}>
                                    <img src={gall.image} alt="" className="galleryImage" key={index} onMouseOver={() => updateMainImg(gall.image)} />
                                </SwiperSlide>
                            );
                            })}
                        </Swiper>
                    </div>

                </div>
                <div className='w-50'>
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
        </div>
        <br />

        {/* <div> */}
            <h3>Inne z tej kategorii:</h3>
            <div className='flexRowStart productCont'>

                <Swiper
                    grabCursor={true}
                    spaceBetween={30}
                    modules={[Navigation]}
                    slidesPerView={3}
                    navigation={true}
                    pagination={true}
                    className="mySwiper"
                >
                    {products.map((product, index) => {
                    return (
                        <SwiperSlide key={index}>
                        <Product product={product} />
                        </SwiperSlide>
                    );
                    })}
                </Swiper>

            </div>
        {/* </div> */}
        <br />

        {product?.description ? (
            <div className='productDetailCont' dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(product?.description.slice(2, product.description.length-2)) }} />
        ):(
            <p></p>
        )}

        <br />
    </div>
  )
}

export default ProductDetails