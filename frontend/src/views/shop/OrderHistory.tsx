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
    const [returnReasons, setReturnReasons] = useState<[]>([]);

    useEffect(() => {
        fetchHistory()
        }, [])


    const fetchHistory = async () => {

            try {
                const resp = await axios_.get('api/store/order-history')
                setProducts(resp.data.results)
                setReturnReasons(resp.data.return_reasons)
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

                                    { order.initial_return === true ?
                                        (
                                            <div>
                                                {/* <p className='flexRowBetween'><b>Otwarty zwrot</b> {order.return_delivery_courier}</p> */}
                                                <a onClick={() => navigate('/returns')} className='Cursor'>Otwarty zwrot</a>
                                                {order.return_tracking_id !== null &&
                                                    <p className='flexRowBetween'><b>Numer śledzenia zwrotu:</b> {order.return_tracking_id}</p>
                                                }
                                            </div>
                                        ) :
                                        (
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
                                                        return_reasons: returnReasons,
                                                    }}
                                                )} className='mainBtn'>
                                                Zwrot
                                            </button>
                                        )
                                    }

                                    {/* <button 
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
                                    </button> */}
                                </div>
                                <p className='flexRowBetween'><b>Cena:</b> {order.price}$</p>
                                <p className='flexRowBetween'><b>Ilość:</b> {order.qty} szt.</p>
                                <p className='flexRowBetween'><b>Razem:</b> {item.sub_total}$</p>
                                <p className='flexRowBetween'><b>Dostawa:</b> {item.shipping_amount}$</p>
                                <hr />
                            </div>
                        ))}
                        <div className='flexRowBetween'>
                            <p><b>KOSZT CAŁKOWITY:</b></p>
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