import React, { useEffect, useState } from 'react'
import { useAuthStore } from '../../store/auth';
import useAxios from '../../utils/useAxios';
import '../../types/OrderItemType';
import { showToast } from '../../utils/toast';
import { useNavigate } from 'react-router-dom';
import '../../types/OrderItemType';

function OrderHistory() {

    const user = useAuthStore((state) => state.allUserData);
    const axios_ = useAxios();
    const navigate = useNavigate();

    const [products, setProducts] = useState<OrderItemType[]>([]);

    useEffect(() => {
        fetchHistory()
        }, [])


    const fetchHistory = async () => {
            try {
                const resp = await axios_.get('api/store/order-history')
                setProducts(resp.data.results)
                console.log('OrderHistory', resp)
            } catch (error) {
                showToast("error", error)
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
                                    <div>
                                        <img src={order.product.image} alt="" width={100}/>
                                        <p>{order.product.title}</p>
                                    </div>

                                    { item.initial_return &&
                                        <p className='flexRowBetween'><b>Zwrot:</b> {item.return_delivery_courier}</p>
                                    }
                                    { item.return_tracking_id &&
                                        <p className='flexRowBetween'><b>Numer śledzenia zwrotu:</b> {item.return_tracking_id}</p>
                                    }

                                    <button 
                                        onClick={() => navigate(
                                            '/initial-return', 
                                            {state: {
                                                oid: item.oid, 
                                                date: item.date,
                                                payment_status: item.payment_status,
                                                order_status: item.order_status,
                                                tracking_id: item.tracking_id,
                                                total_price: item.sub_total,
                                                orderitem: order,
                                            }}
                                        )} className='mainBtn'>
                                        Zwrot
                                    </button>
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