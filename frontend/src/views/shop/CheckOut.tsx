// import axios from 'axios';
import React, { useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom'
import Swal from 'sweetalert2';
import useAxios from '../../utils/useAxios';
import { showToast } from '../../utils/toast';
import { useAuthStore } from '../../store/auth';
import '../../types/CourierType';
import { __userId } from '../../utils/auth';
import MaterialIcon from '@material/react-material-icon';

const CheckOut: React.FC = () => {

    const user = __userId(); //useAuthStore((state) => state.allUserData);
    const axios = useAxios();
    const navigate = useNavigate();
    const location = useLocation();
    const cart = location.state.cart;
    const orderPay = location.state.orderPay;
    // console.log('CheckOut', cart)
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
    const [isHovered, setIsHovered] = useState(false);
    const [freeCity, setFreeCity] = useState('');

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
                user_id: user ? (user['user_id']):(null),
                full_name: fullName,
                email: email,
                mobile: mobile,
                street: street,
                number: number,
                post_code: postCode,
                city: city,
                sub_total: orderPay,
                shipping_amount: totalOrderPrice - orderPay,
                total: totalOrderPrice, 
                delivery: selectedCourier
            }

            try {
                const resp = await axios.post('api/store/create-order', data)
                if ( resp.status === 200 ) {
                    const payment = await axios.post(`api/store/stripe-payment`, {
                        order_oid: resp.data.order.oid
                    })
                    console.log('payment', payment)
                    if ( payment.status === 200 ) {
                        await finishOrder(resp.data.order.oid)
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
            user_id: user ? (user['user_id']):(null),
        })
    }

    const handleCourierChange = (e) => {

        if ( e === "Darmowa" ) {
            console.log("handleCourierChange=Darmowa", e)
            setSelectedCourier(e);
            setTotalOrderPrice(orderPay)
        } else {
            console.log("handleCourierChange", e)
            const { name } = JSON.parse(e);
            console.log("handleCourierChange name", name)
            setSelectedCourier(name);
            const { price } = JSON.parse(e);
            console.log("handleCourierChange price", price)
            setTotalOrderPrice(orderPay + Number(price))
        }
    }

    const checkCity = (city) => {
        setCity(city);
    
        const foundCity = free.find((c) => c === city);
    
        if (foundCity) {
            setSelectedCourier("Darmowa");
            if (foundCity) {
                setSelectedCourier("Darmowa"); // Update the selected courier state
                const selectElement = document.getElementById('Select') as HTMLSelectElement; // Get the select element
                if (selectElement) {
                    selectElement.value = "Darmowa"; // Set its value to "Darmowa"
                }
            }
        }
    };
    
    

    const free = [
        "Wschowa",
        "Świdnica",
        "Nowa Wieś",
        "Przyczyna Dolna",
        "Przyczyna Górna",
        "Telewice",
        "Osowa Sień",
        "Hetmanice",
        "Lgiń", 
        "Radomyśl",
        "Wjewo",
        "Wieleń",
        "Kaszczor",
        "Mochy",
        "Solec",
        "Wolsztyn",
    ]


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

            <div 
                className="flexRowBetween gap-15"
                // onMouseEnter={() => setIsHovered(true)}
                // onMouseLeave={() => setIsHovered(false)}
            >

                <select
                    id="Select"
                    name="courier"
                    // value={selectedCourier || ""}
                    onChange={(e) => handleCourierChange(e.target.value)}
                >
                    <option value="">Courier:</option>
                    <option value="Darmowa">Darmowa</option>
                    {couriers?.map((courier, index) => (
                        <option key={index} value={JSON.stringify({ price: courier.price, name: courier.name })}>
                            {courier.name}
                        </option>
                        // <option key={index} value={courier.name}>
                        //     {courier.name}
                        // </option>
                    ))}
                </select>
             
                    <div
                        onMouseEnter={() => setIsHovered(true)} 
                        onMouseLeave={() => setIsHovered(false)}
                    >
                        <MaterialIcon icon="info"  className="Cursor" />
                        {isHovered && (
                            <div
                                className="free-shipping" 
                                onMouseEnter={() => setIsHovered(true)} 
                                onMouseLeave={() => setIsHovered(false)}
                            >
                                {free.map((city, index) => (
                                    <p key={index}>{city}</p>
                                ))}
                            </div>
                        )}

                    </div>
                
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
                <input type="text" placeholder='City' className='authInput' onChange={(e) => checkCity(e.target.value)}/>
            </div>
            <button onClick={makeOrder}>Kupuję</button>
        </div>
        
    </div>
  )
}

export default CheckOut