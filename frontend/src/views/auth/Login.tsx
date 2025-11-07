import React, { useEffect, useState } from 'react'
import { useAuthStore } from '../../store/auth';
import { Link, useNavigate } from 'react-router-dom';
import { login } from '../../utils/auth';
import '../../styles/auth.css'

const Login: React.FC = () => {

    const [email, setEmail] = useState<string>("");
    const [password, setPassword] = useState<string>("");
    const [isLoading, setIsLoading] = useState<boolean>(false);

    const isLoggedIn = useAuthStore((state) => state.isLoggedIn);
    console.log('Login', isLoggedIn)
    const navigate = useNavigate();

    useEffect(() => {
        if ( isLoggedIn() ) {
            navigate('/');
        } 
    }, [])

    const resetForm = () => {
        setEmail('');
        setPassword('');
    };

    const handleLogin = async (e) => {
        e.preventDefault();
        setIsLoading(true);

        const { error } = await login(email, password);
        if (error) {
            alert(error);
        } else {
            navigate('/');
            resetForm();
        }
        setIsLoading(false);
    }


  return (
    <div>
        <form onSubmit={handleLogin} className='flexColumnCenter'>
            <img src="/login.jpg" alt="login" width={300}/>
            <input 
                className='authInput'
                placeholder='Email...'
                type="text" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
            />
            <input 
                className='authInput'
                placeholder='Hasło...'
                type="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
            />

            <button type='submit'>Zaloguj</button>
            <br />
            <p>
                Don't have an account? 
                <Link to={'/register'}>Rejestracja</Link>
            </p>
            <br />
            <p>
                <Link to={'/forgot-password'}>Niepamiętasz hasła?</Link>
            </p>
        </form>
    </div>
  )
}

export default Login