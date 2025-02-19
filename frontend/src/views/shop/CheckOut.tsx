// import axios from 'axios';
import React, { useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom'
import Swal from 'sweetalert2';
import useAxios from '../../utils/useAxios';
import { showToast } from '../../utils/toast';
import { useAuthStore } from '../../store/auth';
import '../../types/CourierType';

const CheckOut: React.FC = () => {

    const user = useAuthStore((state) => state.allUserData);
    const axios = useAxios();
    const navigate = useNavigate();
    const location = useLocation();
    const cart = location.state.cart;
    const orderPay = location.state.orderPay;
    console.log('CheckOut', cart)

    const [fullName, setFullName] = useState<string>('');
    const [email, setEmail] = useState<string>('');
    const [mobile, setMobile] = useState<string>('');
    const [street, setStreet] = useState<string>('');
    const [number, setNumber] = useState<string>('');
    const [postCode, setPostCode] = useState<string>('');
    const [city, setCity] = useState<string>('');
    const [couriers, setCouriers] = useState<CourierType[]>([]);
    const [totalOrderPrice, setTotalOrderPrice] = useState<number>(orderPay);

    useEffect(() => {
        fetchData('api/store/couriers')
    }, [])

    const fetchData = async (endpoint) => {
        try {
            const resp = await axios.get(endpoint)
            setCouriers(resp.data.couriers)
            console.log('couriers', resp)
        } catch (error) {
            showToast("error", error)
        }
    }

    const makeOrder = () => {

        console.log('makeOrder', cart)

        if ( totalOrderPrice === orderPay ) {
            showToast("warning", "Please chouse the delivery")
        }

        if (!fullName || !email || !mobile || !street || !postCode || !number || !city) {
            // If any required field is missing, show an error message or take appropriate action
            showToast("warning", "Missing Fields!")
            return;
        } else {

            const data = {
                user_id: user.user_id,
                full_name: fullName,
                email: email,
                mobile: mobile,
                street: street,
                number: number,
                post_code: postCode,
                city: city,
                sub_total: orderPay,
                shipping_amount: totalOrderPrice - orderPay,
                total: totalOrderPrice 
            }
            
            try {
                const resp = axios.post('api/store/create-order', data)
            } catch (error) {
                showToast("error", error)
            }
        }
    }

    const handleCourierChange = (e) => {
        setTotalOrderPrice(orderPay)
        console.log("handleCourierChange", e.target.value)
        setTotalOrderPrice(orderPay + Number(e.target.value))
    }

  return (
    <div>
        {cart?.map((order, index) => (
           <div key={index}>
                <div>
                    <div className='flexRowStart'>
                        <img src={order.product.image} alt="" width={100}/>
                        <p>Product: {order.product.title}</p>
                    </div>
                    <div className='flexRowBetween'>
                        <p>Price: {order.price}$</p>
                    </div>
                    <div className='flexRowBetween'>
                        <p>Quantity: {order.qty} pcs.</p>
                        <p>{order.total}</p>
                    </div>
                    <hr />
                </div>
           </div>
        ))}
        <br />

        <div className='flexRowBetween'>
            <button onClick={() => navigate('/order')}>
                Edit Cart
            </button>

            <div>
                <h3>Courier:</h3>
                <select name="" id="Select" onChange={handleCourierChange}>
                    <option value="">Select:</option>
                    {couriers?.map((courier, index) => (
                        <option key={index} value={courier.price}>
                            {courier.name}
                        </option>
                    ))}
                </select>
            </div>
        </div>

        <br />
        <hr />
        <div className='flexRowBetween'>
            <p><b>TOTAL:</b></p>
            <p>{orderPay}$</p>
        </div>
        <hr />
        <div className='flexRowBetween'>
            <p><b>TOTAL + DELIVERY:</b></p>
            <p><b>{totalOrderPrice}$</b></p>
        </div>
        <hr />

        <div className='flexColumnCenter'>
            <h3>Delivery Information:</h3>
            <input type="text" placeholder='Full Name' className='fullNameInput w-535' onChange={(e) => setFullName(e.target.value)} />
            <div className='flexRowStart'>
                <input type="email" placeholder='Email' className='authInput' onChange={(e) => setEmail(e.target.value)}/>
                <input type="text" placeholder='Mobile' className='authInput' onChange={(e) => setMobile(e.target.value)}/>
            </div>
            <div className='flexRowStart'>
                <input type="text" placeholder='Street' className='authInput' onChange={(e) => setStreet(e.target.value)}/>
                <input type="text" placeholder='Number' className='authInput' onChange={(e) => setNumber(e.target.value)}/>
            </div>
            <div className='flexRowStart'>
                <input type="text" placeholder='Post Code' className='authInput' onChange={(e) => setPostCode(e.target.value)}/>
                <input type="text" placeholder='City' className='authInput' onChange={(e) => setCity(e.target.value)}/>
            </div>
            <button onClick={makeOrder}>Order</button>
        </div>
        
    </div>
  )
}

export default CheckOut