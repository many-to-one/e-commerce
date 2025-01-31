import axios from '../../utils/axios';
import React, { useState } from 'react'

const ForgotPassword: React.FC = () => {

    const [email, setEmail] = useState<string>('');

    const resetForm = () => {
        setEmail('');
    };

    const handleEmailReset = async (e) => {
        e.preventDefault()
        try {
            await axios.get(`api/users/password-reset/${email}`)
            .then((res) => {
                console.log('response', res)
            });
        } catch (error) {
            console.log('error-handleEmailReset', error)
        }
    }

  return (
    <form onSubmit={handleEmailReset}>
        <input 
            placeholder='Email'
            type="text"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
        />
        <button type='submit'>Reset</button>
    </form>

  )
}

export default ForgotPassword