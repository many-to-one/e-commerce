import React, { useEffect, useState } from 'react';

function AllegroAuth() {
    const [authCode, setAuthCode] = useState(null);

    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        const code = params.get('code');
        if (code) {
            setAuthCode(code);
            getAccessToken(code) 
        }
    }, []);

    async function getAccessToken(code) {
    const TOKEN_URL = 'https://allegro.pl.allegrosandbox.pl/auth/oauth/token'; // Replace with actual token URL
    const CLIENT_ID = '';
    const CLIENT_SECRET = '';
    const REDIRECT_URI = 'http://localhost:5173';

    const credentials = btoa(`${CLIENT_ID}:${CLIENT_SECRET}`); // Base64 encode client credentials

    const data = new URLSearchParams({
        grant_type: 'authorization_code',
        code: code,
        redirect_uri: REDIRECT_URI
    });

    try {
        const response = await fetch(TOKEN_URL, {
            method: 'POST',
            headers: {
                'Authorization': `Basic ${credentials}`,
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: data
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP error ${response.status}: ${errorText}`);
        }

        const tokens = await response.json();
        console.log('Access Token:', tokens);
        return tokens.access_token;
    } catch (err) {
        console.error('Failed to fetch access token:', err);
        throw err;
    }
}


    return (
        <div>
            <h1>AllegroAuth</h1>
            {authCode ? <p>Authorization Code: {authCode}</p> : <p>No code found</p>}
        </div>
    );
}

export default AllegroAuth;
