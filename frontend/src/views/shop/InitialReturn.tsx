import React, { useState } from 'react';
import useAxios from '../../utils/useAxios';
import { showToast } from '../../utils/toast';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/auth';

function InitialReturn() {

    const user = useAuthStore((state) => state.allUserData);
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
    const return_reasons = location.state.return_reasons

    const [qty, setQty] = useState(item.qty);
    const [total, setTotal] = useState(total_price);
    const [returnReason, setReturnReason] = useState('');

    console.log('InitialReturn', item, return_reasons)

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

            if (returnReason === 'Powód zwrotu' || returnReason === '') {
                showToast('error', 'Wybierz powód zwrotu')
                return
            }
    
            const body = {
                userId: user.user_id,
                orderId: oid,
                prodId: product.id,
                qty: qty,
                returnReason: returnReason,
            }
            try {
                const resp = await axios_.post('api/store/return-item', body)
                console.log('initialReturn', resp)
                navigate('/returns')
            } catch (error) {
                showToast("error", error)
            }
        }


    const handleReason = (e) => {
        console.log('handleReason---', e.target.value)
        setReturnReason(e.target.value)
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
                                <select name="" id="Select" onChange={handleReason}>
                                    <option selected>Powód zwrotu</option>
                                    {return_reasons?.map((reason, index) => (
                                        <option key={index} value={reason[0]}>{reason[0]}</option>
                                    ))}
                                </select>
                                <hr />
                                <button onClick={() => initialReturn(item.product)} className='mainBtn'>Zwrot</button>
                            </div>
                        <hr /> 
                    </div>
                </div>
  )
}

export default InitialReturn