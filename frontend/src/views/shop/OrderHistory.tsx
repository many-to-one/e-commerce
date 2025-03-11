import React, { useEffect, useState } from 'react'
import { useAuthStore } from '../../store/auth';
import useAxios from '../../utils/useAxios';
import '../../types/OrderItemType';

function OrderHistory() {

    const user = useAuthStore((state) => state.allUserData);
    const axios_ = useAxios();

    const [products, setProducts] = useState<OrderItemType[]>([]);

    useEffect(() => {
            fetchData('api/store/order-history')
        }, [])


    const fetchData = async (endpoint) => {
            try {
                const resp = await axios_.get(endpoint)
                setProducts(resp.data.results)
                console.log('OrderHistory', resp)
            } catch (error) {
                // showToast("error", error)
            }
        }

    return (
      <div>
        {products?.map((item, index) => (
            <div key={index}>
                <div className='cartItem'>
                    <div>
                        <div className='flexColumnStart'>
                            <p className='flexRowBetween'><b>ID zamówienie:</b> {item.oid}</p>
                            <p className='flexRowBetween'><b>Data złożenia:</b> {item.date}</p>
                            <p className='flexRowBetween'><b>Status opłaty:</b> {item.payment_status}</p>
                            <p className='flexRowBetween'><b>Status dostawy:</b> {item.order_status}</p>
                            <p className='flexRowBetween'><b>Numer śledzenia:</b> {item.tracking_id}</p>
                        </div>
                        {item.orderitem.map((order, index) => (
                           <div>
                                <div className='flexRowBetween'>
                                    <img src={order.product.image} alt="" width={100}/>
                                    <p>{order.product.title}</p>
                                </div>
                                <p className='flexRowBetween'><b>Cena:</b> {order.price}$</p>
                                <p className='flexRowBetween'><b>Ilość:</b> {order.qty} szt.</p>
                                <hr />
                            </div>
                        ))}
                        <div className='flexRowBetween'>
                            <p><b>RAZEM:</b></p>
                            <p><b>{item.total} PLN</b></p>
                        </div>
                        <hr /> 
                    </div>
                </div>
            </div>
        ))}
        <br />
        <br />
        <br />
        <br />
      </div>
    )
}

export default OrderHistory