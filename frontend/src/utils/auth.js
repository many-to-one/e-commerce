import { useAuthStore } from "../store/auth";
import axios from './axios';
import { jwtDecode } from "jwt-decode";
import Cookies from 'js-cookie';

export const login = async (email, password) => {

    console.log('LOGIN---', email, password)

    try {
        const { data, status } = await axios.post('api/users/token', {
            email,
            password,
        });

        if (status === 200) {
            console.log('data', data)
            setAuthUser(data.access, data.refresh);
        }

        return { data, error: null }

    } catch (error) {

        console.log('Error', error)
        return {
            data: null,
            error: error.response.data?.detail || 'Something went wrong',
        };
    }
};


export const register = async (full_name, email, phone, password, password2) => {
    try {
        console.log(full_name, email, phone, password, password2)
        const { data } = await axios.post('api/users/register', {
            full_name,
            email,
            phone,
            password,
            password2
        });

        console.log('register data', data)

        await login(email, password);

        return { data, error: null }

    } catch (error) {
        return {
            data: null,
            error: error.response.data?.password?.[0] || 
                   error.response.data?.detail || 
                   'Something went wrong',
        };
    }
};


export const logout = async () => {
    Cookies.remove('access_token');
    Cookies.remove('refresh_token');
    useAuthStore.getState().setUser(null);
};


export const isAccessTokenExpired = (accessToken) => {
    try {
        // Decoding the access token and checking if it has expired
        const decodedToken = jwtDecode(accessToken);
        return decodedToken.exp < Date.now() / 1000;
    } catch (err) {
        return true;
    }
};


export const __userId = () => {
    try {
        const decodedToken = jwtDecode(Cookies.get('access_token'));
        console.log('__userId', decodedToken);
        return decodedToken;
    } catch (error) {
        console.log('__userId--error', error);
    }
}


// Function to refresh the access token using the refresh token
export const getRefreshToken = async () => {
    // Retrieving refresh token from cookies and making a POST request to refresh the access token
    const refresh_token = Cookies.get('refresh_token');
    const response = await axios.post('api/users/token/refresh', {
        refresh: refresh_token,
    });

    // console.log('getRefreshToken', response)

    // Returning the refreshed access token
    return response.data;
};


export const setUser = async () => {
    const accessToken = Cookies.get('access_token');
    const refreshToken = Cookies.get('refresh_token');

    if (!accessToken || !refreshToken) {
        return;
    };

    if (isAccessTokenExpired(accessToken)) {
        const response = await getRefreshToken(refreshToken);
        setAuthUser(response.access, response.refresh);
    } else {
        setAuthUser(accessToken, refreshToken);
    }
};


export const setAuthUser = (access_token, refresh_token) => {

    Cookies.set('access_token', access_token, {
        expires: 1,  // Access token expires in 1 day
        secure: true,
    });

    Cookies.set('refresh_token', refresh_token, {
        expires: 7,  // Refresh token expires in 7 days
        secure: true,
    });

    // Decoding access token to get user information
    const user = jwtDecode(access_token) ?? null;
    console.log('setAuthUser', user)

    // If user information is present, update user state; otherwise, set loading state to false
    if (user) {
        useAuthStore.getState().setUser(user); 
    }
    useAuthStore.getState().setLoading(false);
};


export const createNewPass = async (otp, uidb64, reset_token, password) => {
    try {
        console.log(otp, uidb64, reset_token, password)
        const { data } = await axios.post('api/users/new-password', {
            otp,
            uidb64,
            reset_token,
            password,
        });

        console.log('register data', data)

        // await login(email, password);

        return { data, error: null }

    } catch (error) {
        return {
            data: null,
            error: error.response.data?.password?.[0] || 
                   error.response.data?.detail || 
                   'Something went wrong',
        };
        // return {
        //     data: null,
        //     error: 
        //            'Something went wrong',
        // };
    }
};