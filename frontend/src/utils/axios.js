import axios from 'axios';
import { API_BASE_URL } from './constants';
import Cookies from 'js-cookie';

const accessToken = Cookies.get('access_token');

const apiInstance = axios.create({
    baseURL: API_BASE_URL,

    // Set a timeout for requests made using this instance. If a request takes longer than 5 seconds to complete, it will be canceled.
    timeout: 100000, // timeout after 5 seconds
    
    headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json', 
        Authorization: `Bearer ${accessToken}`
    },
});

export default apiInstance;
