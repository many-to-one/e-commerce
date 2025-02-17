import React, { useEffect, useState } from 'react'
import MaterialIcon from '@material/react-material-icon';
import useAxios from '../../utils/useAxios';
import { useAuthStore } from '../../store/auth';
import { useNavigate } from 'react-router-dom';

function Cart () {

    const navigate = useNavigate();
    const axios_ = useAxios();
    const user = useAuthStore((state) => state.allUserData);
    const [cart, setCart] = useState([]);
    const [count, setCount] = useState<string>('');
    const [orderPay, setOrderPay] = useState<number>(0.00);
    
    const fetchData = async () => {
        try {
          const resp = await axios_.get(`api/store/cart/${user.user_id}`);
          console.log('Cart', resp, resp.data.cart.length);
          setCart(resp.data.cart);
          setCount(resp.data.cart.length);
          await getOrderPay(resp.data.cart);
        } catch (error) {
          console.log('Cart-error', error);
        }
    }

    const getOrderPay = async (cart) => {
      let count = 0;
      cart.map((c) => count += Number(c.total))
      console.log('getOrderPay', count)
      setOrderPay(count);
    }
    
    useEffect(() => {
        fetchData();
    }, [user])

    const goToCart = () => {
      navigate('/order', {state: {cart: cart, orderPay: orderPay}})
    }

  return (
    <div className="Cursor" onClick={goToCart}>
        <MaterialIcon icon="shopping_cart" />
        {count}
    </div>
  )
}

export default Cart