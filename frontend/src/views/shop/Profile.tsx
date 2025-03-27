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

  return (
    <div className='flexColumnCenter'>
        {user['username'] === 'admin' &&
            <button className='Cursor fileUpload' onClick={()=> navigate('/upload-files')}>Importuj oferty allegro</button>
        }
        <button className='Cursor' onClick={()=> navigate('/returns')}>Zwroty</button>
        <p>Historia zamówień:</p>
        <OrderHistory />
    </div>
  )
}

export default Profile