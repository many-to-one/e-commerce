import React, { useEffect, useState } from 'react';
import axios from 'axios';
import useAxios from '../../utils/useAxios';

function AllegroAuth() {
    const [authCode, setAuthCode] = useState(null);

    const axios_ = useAxios();

    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        const code = params.get('code');
        if (code) {
            setAuthCode(code);
            getAccessToken(code) 
        }
    }, []);

    async function getAccessToken(code) {

        axios_.post(`api/store/allegro-token/${code}`)
            .then(response => {
            console.log('DRF allegro-token responce', response.data.access_token);
            })
            .catch(error => {
            console.error('DRF allegro-token Axios error:', error);
        });

    }


    return (
        <div>
            <h1>AllegroAuth</h1>
            {authCode ? <p>Authorization Code: {authCode}</p> : <p>No code found</p>}
        </div>
    );
}

export default AllegroAuth;
