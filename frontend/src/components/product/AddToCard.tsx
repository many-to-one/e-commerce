import React, { useEffect } from 'react';
// import axios from'../../utils/axios';
import axios from 'axios';
import { Link, useNavigate } from 'react-router-dom';
import Cookies from 'js-cookie';
import { API_BASE_URL } from '../../utils/constants';
import { showToast } from '../../utils/toast';
import { useAuthStore } from '../../store/auth';
import Swal from 'sweetalert2';
import { __userId } from '../../utils/auth';


const Toast = Swal.mixin({
    toast: true,
    position: "top",
    showConfirmButton: false,
    timer: 1500,
    timerProgressBar: true,
})

interface AddToCardProps {
    id: number,
    quantity: number,
}

const AddToCard: React.FC<AddToCardProps> = ({id, quantity}) => {

  const navigate = useNavigate()
  const accessToken = Cookies.get('access_token');
  const user = __userId(); //useAuthStore((state) => state.allUserData);
  const isLoggedIn = useAuthStore((state) => state.isLoggedIn);
  console.log('AddToCard user', user)

    const sendToCard = async () => {
        console.log('AddToCard', id, quantity)

        if ( user === null ) {
          navigate('/login')
        } else {

          const body = {
            user_id: user['user_id'] || null,
            product_id: id,
            quantity: quantity
          }
        
          try {
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
            // console.log('sendToCard***', resp)
            useAuthStore.getState().addCartCount();
            showToast("success", "Added product to cart")
          } catch (error) {
            console.log('sendToCard error', error)
            if ( error.status === 403 ) {
              navigate('/login')
            }
          }
        }

    }

  return (
    <div>
      {/* {isLoggedIn()
      ? <button className='mainBtn' onClick={sendToCard}>Add to Card</button>
      :<div>
                  <h1>Home</h1>
                  <Link to={'/login'}>login</Link>
                </div>
      } */}
      <button className='mainBtn' onClick={sendToCard}>Add to Card</button>
    </div>
  )
}

export default AddToCard