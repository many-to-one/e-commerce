import React, { useState } from 'react';
import useAxios from '../../utils/useAxios';
import { showToast } from '../../utils/toast';
import { useLocation, useNavigate } from 'react-router-dom';

function InitialReturn() {

    const axios_ = useAxios();
    const location = useLocation();
    const navigate = useNavigate();

    const oid = location.state.oid;
    const date = location.state.date;
    const payment_status = location.state.payment_status;
    const order_status = location.state.order_status;
    const tracking_id = location.state.tracking_id;
    const total_price = location.state.total_price;
    const item = location.state.orderitem;

    const [qty, setQty] = useState(item.qty);
    const [total, setTotal] = useState(total_price);

    // console.log('InitialReturn', item)

    const handleQtyChange = (e) => {

        const newQty = Number(e.target.value);

        if ( newQty > item.qty ) {
            showToast('error', 'Wskazana ilość jest większa niż w zamówieniu');
            return
        } else if ( newQty === 0 ) {
            showToast('error', 'Wskazana ilość nie może być 0');
            return
        } else {
            setQty(newQty);
            let newTotal = newQty * item.price
            setTotal(newTotal)
        }
    };

    const initialReturn = async (product) => {
            console.log('initialReturn called', oid, product.id)
    
            const body = {
                orderId: oid,
                prodId: product.id,
                qty: qty,
            }
            try {
                const resp = await axios_.post('api/store/return-item', body)
                console.log('initialReturn', resp)
            } catch (error) {
                showToast("error", error)
            }
        }

  return (
    <div className='cartItem'>
                    <div>
                        <div className='flexColumnStart'>
                            <p className='flexRowBetween'><b>ID zamówienie:</b> {oid}</p>
                            <p className='flexRowBetween'><b>Data złożenia:</b> {date}</p>
                            <p className='flexRowBetween'><b>Status opłaty:</b> {payment_status}</p>
                            <p className='flexRowBetween'><b>Status dostawy:</b> {order_status}</p> 
                            { tracking_id &&
                                <p className='flexRowBetween'><b>Numer śledzenia:</b> {tracking_id}</p>
                            }
                        </div>

                           <div>
                                <div className='flexRowBetween'>
                                    <div>
                                        <img src={item.product.image} alt="" width={100}/>
                                        <p>{item.product.title}</p>
                                    </div>
                                </div>
                                <p className='flexRowBetween'><b>Cena:</b> {item.price} zł</p>
                                <p className='flexRowBetween'><b>Ilość:</b> 
                                    <input 
                                        type="number" 
                                        value={qty} 
                                        onChange={handleQtyChange}
                                    /> szt.
                                </p>
                                <p className='flexRowBetween'><b>Razem:</b> {total} zł</p>
                                <hr />
                                <button onClick={() => initialReturn(item.product)} className='mainBtn'>Zwrot</button>
                            </div>
                        <hr /> 
                    </div>
                </div>
  )
}

export default InitialReturn