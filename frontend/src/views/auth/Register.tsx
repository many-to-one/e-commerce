import React, { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom';
import { register } from '../../utils/auth';
import { useAuthStore } from '../../store/auth';
import '../../styles/auth.css';
import DotsLoader from '../../components/DotsLoader';

function Register() {
    const [fullName, setFullName] = useState<string>("");
    const [email, setEmail] = useState<string>("");
    const [phone, setPhone] = useState<string>("");
    const [password, setPassword] = useState<string>("");
    const [password2, setPassword2] = useState<string>("");
    const [isLoading, setIsLoading] = useState<boolean>(false);

    const isLoggedIn = useAuthStore((state) => state.isLoggedIn);
    const navigate = useNavigate();

    useEffect(() => {
        if ( isLoggedIn() ) {
            navigate('/');
        } 
    }, [])

    const resetForm = () => {
        setFullName('')
        setEmail('');
        setPhone('');
        setPassword('');
        setPassword2('');
    };

    const handleRegister = async (e) => {
        e.preventDefault();
        setIsLoading(true);

        const { error } = await register(fullName, email, phone, password, password2);
        if (error) {
            alert(error);
        } else {
            navigate('/');
            resetForm();
        }
        setIsLoading(false);
    }


  return (
    <>
    {isLoading === true ? (
        <div>
        <form onSubmit={handleRegister} className='flexColumnCenter'>
            <img src="/register.jpg" alt="register" width={560}/>
            <input 
                className='fullNameInput'
                placeholder='Full Name...'
                type="text" 
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
            />
            <div>
                <input 
                    className='authInput'
                    placeholder='Email...'
                    type="text" 
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                />
                <input 
                    className='authInput'
                    placeholder='Phone...'
                    type="text" 
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                />
            </div>
            <div>
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
            </div>

            <button type='submit'>Sing up</button>
            <br />
            <p>
                Already have an account? <Link to={'/login'}>Back to Login page</Link>
            </p>
        </form>
    </div>
    ):(
        <div className='flexColumnCenter gap-15'>
            <DotsLoader />
        </div>
    )}
    </>
  )
}

export default Register