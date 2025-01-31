import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../store/auth';


const PrivateRoute = ({ children }) => {
    // Use the 'useAuthStore' hook to check the user's authentication status. 
    const loggedIn = useAuthStore((state) => state.isLoggedIn)();
    return loggedIn ? <>{children}</> : <Navigate to="/login" />;
};

export default PrivateRoute;