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
    // console.log('user', user.user_id)

    const [fullName, setFullName] = useState<string>('');
    const [email, setEmail] = useState<string>('');
    const [mobile, setMobile] = useState<string>('');
    const [street, setStreet] = useState<string>('');
    const [number, setNumber] = useState<string>('');
    const [postCode, setPostCode] = useState<string>('');
    const [city, setCity] = useState<string>('');
    const [couriers, setCouriers] = useState<CourierType[]>([]);
    const [selectedCourier, setSelectedCourier] = useState<string>('');
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

    const makeOrder = async () => {

        console.log('makeOrder, courier', selectedCourier)

        if ( selectedCourier === '' ) {
            showToast("warning", "Please chouse the delivery")
            return;
        }

        // if ( totalOrderPrice === orderPay ) {
        //     showToast("warning", "Please chouse the delivery")
        //     return;
        // }

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
                const resp = await axios.post('api/store/create-order', data)
                if ( resp.status === 200 ) {
                    const payment = await axios.post(`api/store/stripe-payment`, {
                        order_oid: resp.data.order.oid
                    })
                    console.log('payment', payment)
                    if ( payment.status === 200 ) {
                        // await finishOrder(resp.data.order.oid)
                        window.location.href = payment.data.checkout_session
                    } else {
                        showToast("error", 'Problems with payment')
                    }

                } else {
                    showToast("error", 'Problems with payment')
                }
            } catch (error) {
                showToast("error", error)
            }
        }
    }

    const finishOrder = async (oid) => {
        axios.post('api/store/finish-order', {
            oid: oid,
            user_id: user.user_id,
        })
    }

    const handleCourierChange = (e) => {
        // setTotalOrderPrice(orderPay)
        console.log("handleCourierChange", e.target.value)
        const { name } = JSON.parse(e.target.value);
        console.log("handleCourierChange name", name)
        setSelectedCourier(name);
        const { price } = JSON.parse(e.target.value);
        console.log("handleCourierChange price", price)
        setTotalOrderPrice(orderPay + Number(price))
    }

  return (
    <div className='mt-20'>
        {cart?.map((order, index) => (
           <div key={index} className='cartItem'>
                <div>
                    <div className='flexRowCenter'>
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
                <select name="" id="Select" onChange={handleCourierChange}>
                    <option value="">Courier:</option>
                    {couriers?.map((courier, index) => (
                        <option key={index} value={JSON.stringify({ price: courier.price, name: courier.name })}>
                            {courier.name}
                        </option>
                    ))}
                </select>
            </div>
        </div>

        <br />
        <div className='flexRowBetween cartItem'>
            <p><b>TOTAL:</b></p>
            <p>{orderPay}$</p>
        </div>
        <div className='flexRowBetween cartItem'>
            <p><b>TOTAL + DELIVERY:</b></p>
            <p><b>{totalOrderPrice}$</b></p>
        </div>

        <div className='flexColumnCenter'>
            <h3>Delivery Information:</h3>
            <input type="text" placeholder='Full Name' className='fullNameInput w-535' onChange={(e) => setFullName(e.target.value)} />
            <div className='flexRowCenter'>
                <input type="email" placeholder='Email' className='authInput' onChange={(e) => setEmail(e.target.value)}/>
                <input type="text" placeholder='Mobile' className='authInput' onChange={(e) => setMobile(e.target.value)}/>
            </div>
            <div className='flexRowCenter'>
                <input type="text" placeholder='Street' className='authInput' onChange={(e) => setStreet(e.target.value)}/>
                <input type="text" placeholder='Number' className='authInput' onChange={(e) => setNumber(e.target.value)}/>
            </div>
            <div className='flexRowCenter'>
                <input type="text" placeholder='Post Code' className='authInput' onChange={(e) => setPostCode(e.target.value)}/>
                <input type="text" placeholder='City' className='authInput' onChange={(e) => setCity(e.target.value)}/>
            </div>
            <button onClick={makeOrder}>Order</button>
        </div>
        
    </div>
  )
}

export default CheckOut