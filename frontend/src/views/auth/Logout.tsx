import React, { useEffect } from 'react';
import { logout } from '../../utils/auth';
import '../../styles/auth.css';
import { Link } from 'react-router-dom';

const Logout =() => {

    useEffect(() => {
        logout();
    }, [])

  return (
    <div className='flexColumnCenter'>
      <img src="/logout.jpg" alt="logout" width={500} />
      <h3>Logout</h3>
      <p>
        <Link to={'/login'}>Back to Login page</Link>
      </p>
    </div>
  )
}

export default Logout