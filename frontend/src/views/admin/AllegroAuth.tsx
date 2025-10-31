import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import useAxios from '../../utils/useAxios';

function AllegroAuth() {
    const [authCode, setAuthCode] = useState(null);

    const axios_ = useAxios();
    const { vendorName } = useParams();

    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        const code = params.get('code');
        console.log('codeL-------------:', code);
        console.log('Vendor Name from URL-------------:', vendorName);
        if (code) {
            setAuthCode(code);
            getAccessToken(code) 
        }
    }, []);

    async function getAccessToken(code) {

        axios_.post(`api/store/allegro-token/${code}/${vendorName}/`)
            .then(response => {
            console.log('DRF allegro-token responce', response.data);
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
