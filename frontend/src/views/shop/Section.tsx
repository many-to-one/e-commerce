import { useEffect } from "react";
import Product from "../../components/product/Product";
import Swiper from "swiper/bundle";
import { useNavigate } from "react-router-dom";

interface ProductProps {
    product: ProductType;
  }

// function Section({ products }) {
const Section: React.FC<ProductProps> = ({className, product}) => {

  // console.log('Product props', product)
  const navigate = useNavigate();

  useEffect(() => {
    new Swiper(`.${className}`, {
      slidesPerView: 4,
      spaceBetween: 16,
      breakpoints: {
        0: { slidesPerView: 2 },
        748: { slidesPerView: 3 },
        1024: { slidesPerView: 4 },
      },
    });
  }, [className]);

  return (
    <section>
      <h2>{title}</h2>
      <div className={`swiper ${className}`}>
        <div className="swiper-wrapper">
          {/* {product.map((p, i) => (
            <div className="swiper-slide" key={i}>
              <Product {...p} />
            </div>
          ))} */}
          <div className='flexRowCenter productCont'>
          
                          {product?.map((p, index) => (
                               <Product key={index} product={p} />
                          ))}
                      </div>
        </div>
      </div>
    </section>
  );
}