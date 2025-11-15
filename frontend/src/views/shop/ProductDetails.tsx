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
import DotsLoader from '../../components/DotsLoader';


const ProductDetails: React.FC = () => {

    const imageRef = useRef<HTMLImageElement | null>(null);

    const [isLoading, setIsLoading] = useState<boolean>(true);

    const [product, setProduct] = useState<ProductType | null>(null);
    const [products, setProducts] = useState<ProductType[]>([]);
    const [mainImg, setMainImg] = useState<string>('');
    const [gallery, setGallery] = useState<GalleryType[]>([]);
    const [orderQuantity, setOrderQuantity] = useState<number>(1);

    const { slug } = useParams();
    const location = useLocation();
    const prodId = location.state.id;
    const catId = location.state.catId;
    // console.log('catId', catId)

    useEffect(() => {
        window.scrollTo(0, 0); // Scroll to top
    }, [slug]);

    const fetchData = async (endpoint) => {

        setIsLoading(false);

        try {
            const response = await axios.get(endpoint);
            // console.log(`${endpoint}`, response.data, response.data.gallery.length)
            // console.log('---- Image Link -----', `${API_BASE_URL}media/default.jpg`)
            setProduct(response.data.product);
            
            // const originalUrl = response.data.product.image;
            // const galleryUrl = originalUrl.replace('product_', 'gallery_');
            // setMainImg(galleryUrl);

            setMainImg(response.data.product.img_links[0])
            setGallery(response.data.gallery);
            setIsLoading(true);
            // console.log(' --****-- mainImg -----****---- ', mainImg)
        } catch (error) {
            console.log('Products error', error)
        }
    };


    useEffect(() => {
        fetchData(`/api/store/product/${prodId}`)
    }, [slug])

    const catProducts = async () => {

        setIsLoading(false);

        try {
            const response = await axios.get(`/api/store/category-products/${catId}`);
            console.log(`catProducts---------------*****----`, response.data)
            setProducts(response.data.results)
            setIsLoading(true);
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
        // console.log('handleQuantityChange', newQuantity)
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
    <>
    
    {isLoading === true ? (

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
                            {/* <picture>
                                <source
                                    srcSet={`${mainImg}.webp`}
                                    type="image/webp"
                                />
                                <img
                                    src={mainImg}
                                    alt="ProductDetail"
                                    className="mainGalleryImage" 
                                    ref={imageRef}
                                    onMouseMove={scaleImg} 
                                    onMouseOut={resetImg}
                                    loading="lazy"
                                />
                            </picture> */}
                        </div>

                        <div className='flexRowCenter w-400'>
                            <Swiper
                                grabCursor={true}
                                spaceBetween={10}
                                // modules={[Navigation]}
                                slidesPerView={6}
                                navigation//</div>={true}
                                pagination={true}
                                className="gallerySwiper"
                            >
                                {gallery?.length === 1 ? (
                                    product?.img_links.map((image, index) => (
                                        <SwiperSlide key={index}>
                                            {/* <img src={image} alt="" className="galleryImage" key={index} onMouseOver={() => updateMainImg(image)} /> */}
                                            <picture>
                                                <source
                                                    srcSet={`${image}.jpeg`}
                                                    type="image/webp"
                                                />
                                                <img
                                                    src={image}
                                                    alt="ProductImgGallery"
                                                    className="galleryImage" 
                                                    key={index}
                                                    onMouseOver={() => updateMainImg(image)}
                                                    loading="lazy"
                                                />
                                            </picture>
                                        </SwiperSlide>
                                    ))
                                ) : (
                                    gallery.map((gall, index) => (
                                        <SwiperSlide key={index}>
                                            <img 
                                                src={gall.image} alt="" 
                                                className="galleryImage" 
                                                key={index} 
                                                onMouseOver={() => updateMainImg(gall.image)} 
                                                loading="lazy" 
                                            />
                                            {/* <picture>
                                                <source
                                                    srcSet={`${gall.image}.webp`}
                                                    type="image/webp"
                                                />
                                                <img
                                                    src={gall.image}
                                                    alt="ProductImgGallery"
                                                    className="galleryImage" 
                                                    key={index}
                                                    onMouseOver={() => updateMainImg(gall.image)}
                                                    loading="lazy"
                                                />
                                            </picture> */}
                                        </SwiperSlide>
                                    ))
                                )}

                            </Swiper>
                        </div>

                    </div>
                    <div className='w-50'>
                        <h2>{product?.title}</h2>
                        {/* <p>Brand: {product?.brand}</p> */}
                        <div className='flexRowCenter'>Cena: {product?.old_price !== '0.00' && <p className='oldPrice'>{product?.old_price} PLN</p> } {product?.price} PLN</div>
                        <p>Dostawa: {product?.shipping_amount} PLN</p>
                        <p>Ilość: {product?.stock_qty} szt.</p>
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
                <div className='flexRowStart'>

                    <Swiper
                        // grabCursor={true}
                        // spaceBetween={30}
                        // modules={[Navigation]}
                        // slidesPerView={3}
                        // navigation={true}
                        // pagination={true}
                        // className="mySwiper"
                        
                        grabCursor={true}
                        spaceBetween={30}
                        modules={[Navigation]}
                        slidesPerView={3}
                        navigation={true}
                        pagination={{ clickable: true }}
                        className="mySwiper"

                        /* touch / sensitivity */
                        allowTouchMove={true}
                        simulateTouch={true}
                        touchRatio={1}
                        threshold={5}                // smaller = more sensitive
                        touchStartPreventDefault={false}
                        touchMoveStopPropagation={false}
                        preventClicks={false}
                        preventClicksPropagation={false}
                        


                    >
                        {/* {products.map((product, index) => {
                        return (
                            <SwiperSlide key={index}>
                            <Product product={product} />
                            </SwiperSlide>
                        );
                        })} */}

                        {products.map((product, index) => (
                            <SwiperSlide key={index}>
                            <Product product={product} />
                            </SwiperSlide>
                        ))}
                    </Swiper>

                </div>
            {/* </div> */}
            <br />

            {product?.description ? (
                <div 
                    className='productDetailCont' 
                    dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(product?.description.slice(2, product.description.length-2)).replace(/[',]/g, '') }} 
                />
            ):(
                <p></p>
            )}

            <br />
        </div>

    ) : (
        <div className='flexColumnCenter gap-15'>
            <DotsLoader />
        </div>
    ) }
    
    </>
    
  )
}

export default ProductDetails