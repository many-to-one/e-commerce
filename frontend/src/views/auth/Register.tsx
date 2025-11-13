import React, { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom';
import { login, register } from '../../utils/auth';
import { useAuthStore } from '../../store/auth';
import '../../styles/auth.css';
import DotsLoader from '../../components/DotsLoader';
// import axios from '../../utils/axios';
import apiInstance from '../../utils/axios';
import axios from 'axios';
import { API_BASE_URL } from '../../utils/constants';

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
        // setIsLoading(true);

        // const { error } = await register(fullName, email, phone, password, password2);
        // if (error) {
        //     alert(error);
        // } else {
        //     navigate('/');
        //     resetForm();
        // }

        // console.log('REGISTER RESP', response.data);
        // setIsLoading(false);

        // try {
        //     const response = await axios.post(
        //     "http://127.0.0.1:8100/api/users/register",
        //     {
        //         fullName,
        //         email,
        //         phone,
        //         password,
        //         password2,
        //     },
        //     {
        //         headers: {
        //         "Content-Type": "application/json",
        //         Accept: "application/json",
        //         },
        //     }
        //     );

        //     return response.data;
        // } catch (error) {
        //     // console.log("REGISTER ERROR:", error.response.data.full_name[0] || error);
        //     return {
        //         error: error.response.data?.full_name?.[0] || 
        //            error.response.data?.phone || 
        //            'Something went wrong',
        //     }
        // }

// console.log('fullName', fullName)

setIsLoading(true);

        try {
    const response = await axios.post(
        
        // "http://127.0.0.1:8100/api/users/register",
        `${API_BASE_URL}api/users/register`,
        {
            full_name: fullName,
            email,
            phone,
            password,
            password2,
        },
        {
            headers: {
                "Content-Type": "application/json",
                Accept: "application/json",
            },
        }
    );

    await login(email, password);

    setIsLoading(false);

    navigate('/');
    resetForm();

    return response.data;


} catch (error) {

    // 1. Extract DRF validation errors safely
    const data = error?.response?.data;

    // 2. Convert DRF field-errors into readable text
    let message = "Something went wrong";

    if (data && typeof data === "object") {
        message = Object.entries(data)
            .map(([field, msgs]) => `${field}: ${Array.isArray(msgs) ? msgs.join(", ") : msgs}`)
            .join("\n");
    }

    // 3. Show alert
    alert(message);
    setIsLoading(false);

    // 4. Return structured error to the caller if needed
    return { error: message };
}

    }


  return (
    <>
    {!isLoading ? (
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