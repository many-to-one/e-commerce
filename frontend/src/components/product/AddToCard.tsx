import React from 'react';
// import axios from'../../utils/axios';
import axios from 'axios';
import { Link, useNavigate } from 'react-router-dom';
import Cookies from 'js-cookie';
import { API_BASE_URL } from '../../utils/constants';
import { useAuthStore } from '../../store/auth';

interface AddToCardProps {
    id: number,
    quantity: number,
}

const AddToCard: React.FC<AddToCardProps> = ({id, quantity}) => {

  const navigate = useNavigate()
  const accessToken = Cookies.get('access_token');
  const user = useAuthStore((state) => state.allUserData);
  const isLoggedIn = useAuthStore((state) => state.isLoggedIn);
  console.log('AddToCard user', user)

    const sendToCard = async () => {
        console.log('AddToCard', id, quantity)
        const body = {
          user_id: user.user_id || null,
          product_id: id,
          quantity: quantity
        }
        try {
          // const resp = await axios.post(`/api/store/add-to-cart/${id}`)
          const link = `${API_BASE_URL}api/store/add-to-cart`
          console.log('AddToCard link', link)
          const resp = await axios.post(link, body,
            {
              headers: {
                'Content-Type': 'application/json',
                Accept: 'application/json', 
                Authorization: `Bearer ${accessToken}`
            },
          },
          )
          console.log('sendToCard***', resp)
        } catch (error) {
          console.log('sendToCard error', error)
          if ( error.status === 403 ) {
            navigate('/login')
          }
        }
    }

  return (
    <div>
      {isLoggedIn()
      ? <button className='mainBtn' onClick={sendToCard}>Add to Card</button>
      :<div>
                  <h1>Home</h1>
                  <Link to={'/login'}>login</Link>
                </div>
      }
    </div>
  )
}

export default AddToCard