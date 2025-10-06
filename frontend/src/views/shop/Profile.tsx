import React from 'react';
import MaterialIcon from '@material/react-material-icon';
import { useAuthStore } from '../../store/auth';
import { useNavigate } from 'react-router-dom';
import OrderHistory from './OrderHistory';
import { __userId } from '../../utils/auth';

function Profile() {

    // const user = useAuthStore((state) => state.allUserData);
    const user = __userId(); 
    console.log('user', user['username']);
    const navigate = useNavigate();

    const loginAllegro = () => {
        // navigate('/allegro-auth');
        window.location.href = 'https://allegro.pl.allegrosandbox.pl/auth/oauth/authorize?response_type=code&client_id=73b22f6b7a47415598faf4b57c2f0f45&redirect_uri=http://localhost:5173/allegro-auth-code'
    }

  return (
    <div className='flexColumnCenter'>
        {user['username'] === 'admin' &&
            <button className='Cursor fileUpload' onClick={()=> navigate('/upload-files')}>Importuj oferty allegro</button>
            // <button className='Cursor fileUpload' onClick={()=> navigate('/allegro-auth')}>Zaloguj się do allegro</button>
        }
         <button className='Cursor fileUpload' onClick={()=> loginAllegro()}>Zaloguj się do allegro</button>
        <button className='Cursor' onClick={()=> navigate('/returns')}>Zwroty</button>
        <p>Historia zamówień:</p>
        <OrderHistory />
    </div>
  )
}

export default Profile