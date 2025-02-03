import React, { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { createNewPass } from '../../utils/auth';
import '../../styles/auth.css';

const CreatePassword: React.FC = () => {

    const [password, setPassword] = useState<string>("");
    const [password2, setPassword2] = useState<string>("");
    const [error, setError] = useState<string>("");
    const [searchParams] = useSearchParams();
    const otp = searchParams.get('otp');
    const uidb64 = searchParams.get('uidb64');
    const reset_token = searchParams.get('reset_token');

    const navigation = useNavigate();

    const handleLogin = async (e) => {
        e.preventDefault();

        if ( password === password2 ) {
            const res = await createNewPass(otp, uidb64, reset_token, password);
            console.log('newPass', res);
            if ( res.data.status === 200 ) {
                navigation('/login');
            }
        } else {
            alert('Password does not match!');
        }
    }

  return (
    <div>
        <h1>Create New Password</h1>
        <img src="/create_psw.jpg" alt="login" width={500}/>
        <form onSubmit={handleLogin} className='flexColumnCenter'>
            <input 
                className='authInput'
                placeholder='Password...'
                type="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
            />
            <input 
                className='authInput'
                placeholder='Repeat password...'
                type="password" 
                value={password2}
                onChange={(e) => setPassword2(e.target.value)}
            />
    
            <button type='submit'>Send</button>
            <br />
            <p>
                <Link to={'/login'}>Back to Login</Link>
            </p>
        </form>
    </div>
  )
}

export default CreatePassword