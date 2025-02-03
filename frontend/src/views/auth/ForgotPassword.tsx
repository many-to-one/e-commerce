import { Link, useNavigate } from 'react-router-dom';
import axios from '../../utils/axios';
import React, { useState } from 'react';
import '../../styles/auth.css';

const ForgotPassword: React.FC = () => {

    const [email, setEmail] = useState<string>('');
    const navigate = useNavigate();

    const resetForm = () => {
        setEmail('');
    };

    const handleEmailReset = async (e) => {
        e.preventDefault()
        try {
            await axios.get(`api/users/password-reset/${email}`)
            .then((res) => {
                console.log('response', res)
                alert('Email has been sent to you');
                navigate(`/${res.data.link}`);
            });
        } catch (error) {
            console.log('error-handleEmailReset', error)
        }
    }

  return (
    <form onSubmit={handleEmailReset} className='flexColumnCenter'>
        <img src="/forgot_psw.jpg" alt="forgot_psw" width={300} />
        <input 
            className='authInput'
            placeholder='Email...'
            type="text"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
        />
        <button type='submit'>Reset</button>
        <p>
          <Link to={'/login'}>Back to Login page</Link>
        </p>
    </form>

  )
}

export default ForgotPassword