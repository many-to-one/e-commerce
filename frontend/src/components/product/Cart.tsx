import React, { useEffect, useState } from 'react'
import MaterialIcon from '@material/react-material-icon';
import useAxios from '../../utils/useAxios';
import { useAuthStore } from '../../store/auth';
import { useNavigate } from 'react-router-dom';
import { __userId } from '../../utils/auth';

function Cart () {

    const navigate = useNavigate();
    const axios_ = useAxios();
    const count = useAuthStore((state) => state.cartCount)
    const user = __userId(); //useAuthStore((state) => state.allUserData);

    const [countData, setCountData] = useState('')

    const fetchData = async () => {
      try {
        const resp = await axios_.get(`api/store/cart_count/${user['user_id']}`)
        console.log("CountData:", resp.data["cart_count "]);
        setCountData(resp.data["cart_count "])
        useAuthStore.getState().updateCartCount(resp.data["cart_count "]); 
      } catch (error) {
        
      }
    }

    useEffect(() => {
      fetchData();
    }, [user])

    useEffect(() => {
        console.log("Updated countData:", countData);
    }, [countData]);

    const goToCart = () => {
      navigate('/order')
    }

  return (
    <div className="cart-container Cursor" onClick={goToCart}>
      <MaterialIcon icon="shopping_cart" />
        { count !== null ? (
          <span className="cart-badge">{count}</span>
        ):(
          <span className="cart-badge">{countData}</span>
        )}
    </div>
  )
}

export default Cart