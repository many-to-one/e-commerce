import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from "react-router-dom";
import '../../types/ProductType';
import MaterialIcon from '@material/react-material-icon';
import useAxios from '../../utils/useAxios';
import { useAuthStore } from '../../store/auth';
import { API_BASE_URL } from '../../utils/constants';
import axios from 'axios';
import Cookies from 'js-cookie';

interface OrderProps {
    id: number,
    price: string,
    product: ProductType,
    qty: number,
    total: string,
    user: number,
}

const Order: React.FC<OrderProps> = () => {

    const axios_ = useAxios();
    const navigate = useNavigate();
    const user = useAuthStore((state) => state.allUserData);
    const count = useAuthStore((state) => state.cartCount);
    const accessToken = Cookies.get('access_token');

    const [cart, setCart] = useState<OrderProps[]>([]);
    const [orderPay, setOrderPay] = useState<number>(0.00);
    const [inputQty, setInputQty] = useState({});

    const fetchData = async () => {
        try {
          const resp = await axios_.get(`api/store/cart/${user.user_id}`);
          console.log('Cart', resp.data.cart);
          setCart(resp.data.cart);
          useAuthStore.getState().updateCartCount(resp.data.cart.length); 
          await getOrderPay(resp.data.cart);
        } catch (error) {
          console.log('Cart-error', error);
          navigate('/login');
        }
    }
    
    const getOrderPay = async (cart) => {
        let count = 0;
        cart.map((c) => count += Number(c.total))
        count = Number(count.toFixed(2));
        console.log('getOrderPay', count)
        setOrderPay(count);
    }
        
    useEffect(() => {
        fetchData();
    }, [user])    

    useEffect(() => {
        console.log("Updated Cart:", cart);
    }, [cart]);

    const deleteItem = (id) => {
        try {
            const resp = axios_.delete(`api/store/cart/${id}`)
            setCart((prevCart) => {
                const updatedCart = prevCart.filter(item => item.id !== id);
                getOrderPay(updatedCart);
                return updatedCart;
            });
            useAuthStore.getState().minusCartCount();
        } catch (error) {
            console.log('deleteItem-error', error)
        }
    }


    const handleInputChange = (id, value) => {
        setInputQty((prev) => ({ ...prev, [id]: value }));
    };


    const updateQty = async (id) => {
        const newQty = parseInt(inputQty[id], 10) || 1;
        
        setCart((prevCart) => {
            const updatedCart = prevCart.map((item) =>
                item.id === id
                    ? { ...item, qty: newQty, total: (newQty * Number(item.price)).toFixed(2) }
                    : item
            );
    
            getOrderPay(updatedCart);
            return updatedCart;
        });
    
        setInputQty((prev) => ({ ...prev, [id]: newQty })); 
    
        await sendUpdateQty(id, newQty);
    };
    


    const sendUpdateQty = async (id, quantity) => {

        console.log('updateQty - id, quantity', id, quantity)
        const body = {
          user_id: user.user_id || null,
          cart_id: id,
          quantity: quantity
        }

        try {
            const link = `${API_BASE_URL}api/store/cart/${id}`
            console.log('sendUpdateQty link', link)
            const resp = await axios.put(link, body,
                {
                    headers: {
                        'Content-Type': 'application/json',
                        Accept: 'application/json', 
                        Authorization: `Bearer ${accessToken}`
                    },
                },
            )
            console.log('sendUpdateQty***', resp.data.cart)
          } catch (error) {
            console.log('sendUpdateQty error', error)
          }
    }

  return (
    <div>
        {cart?.map((order, index) => (
           <div key={index}>
                <div className='cartItem'>
                    <div>
                        <div className='flexRowCenter'>
                            <img src={order.product.image} width={100} alt="" />
                            <p>{order.product.title}</p>
                        </div>
                        <div className='flexRowBetween'>
                            <p>Price: {order.price}$</p>
                            <div className='Cursor' onClick={() => deleteItem(order.id)}>
                                <MaterialIcon icon="delete" />
                            </div>
                        </div>
                        <div className='flexRowBetween'>
                            <p>Quantity: 
                                <input 
                                    type="number" 
                                    value={inputQty[order.id] ?? order.qty} 
                                    onChange={(e) => handleInputChange(order.id, e.target.value)} 
                                    onBlur={() => updateQty(order.id)}
                                /> pcs.   
                            </p>
                            <p>{order.total}</p>
                        </div>
                        <hr />
                    </div>
                </div>
           </div>
        ))}
        <br />
        <div className='flexRowBetween cartItem'>
            <p><b>TOTAL:</b></p>
            <p><b>{orderPay}$</b></p>
        </div>
        <div className='flexRowBetween mt-20'>
            <button onClick={() => navigate('/')}>
                Go back
            </button>
            <button onClick={() => navigate('/checkout', {state:{ cart: cart, orderPay: orderPay }})}>
                Checkout
            </button>
        </div>
    </div>
  )
}

export default Order