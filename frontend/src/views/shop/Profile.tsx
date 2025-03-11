import React from 'react';
import MaterialIcon from '@material/react-material-icon';
import { useAuthStore } from '../../store/auth';
import { useNavigate } from 'react-router-dom';
import OrderHistory from './OrderHistory';

function Profile() {

    const user = useAuthStore((state) => state.allUserData);
    const navigate = useNavigate();

  return (
    <div className='flexColumnCenter'>
        {user.username === 'admin' &&
            <button className='Cursor fileUpload' onClick={()=> navigate('/upload-files')}>Importuj oferty allegro</button>
        }
        <p>Historia zamówień:</p>
        <OrderHistory />
    </div>
  )
}

export default Profile