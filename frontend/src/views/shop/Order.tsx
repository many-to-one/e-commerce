import React, { useState } from 'react';
import { useLocation } from "react-router-dom";
import '../../types/ProductType';
import MaterialIcon from '@material/react-material-icon';
import useAxios from '../../utils/useAxios';

interface OrderProps {
    id: number,
    price: string,
    product: ProductType,
    qty: number,
    total: string,
    user: number,
}

const Order: React.FC<OrderProps> = () => {

    const location = useLocation();
    const orderData_ = location.state.cart;
    const orderPay = location.state.orderPay;
    console.log('Order', orderData_, orderPay)

    // const [orderData, setOrderData] = useState(location.state?.orderData_ || []);

    const axios_ = useAxios();

    const deleteItem = (id) => {
        try {
            const resp = axios_.delete(`api/store/cart/${id}`)
            // setOrderData((prevOrderData) => prevOrderData.filter(item => item.id !== id));
        } catch (error) {
            
        }
    }

  return (
    <div>
        {orderData_?.map((order, index) => (
           <div key={index}>
             <p>Product: {order.product.title}</p>
             <div className='flexRowBetween'>
                <p>Price: {order.price}$</p>
                <div className='Cursor' onClick={() => deleteItem(order.id)}>
                    <MaterialIcon icon="delete" />
                </div>
             </div>
             <div className='flexRowBetween'>
                <p>Quantity: {order.qty} pcs.</p>
                <p>{order.total}</p>
             </div>
             <hr />
           </div>
        ))}
        <br />
        <div className='flexRowBetween'>
            <p><b>TOTAL:</b></p>
            <p>{orderPay}$</p>
        </div>
    </div>
  )
}

export default Order