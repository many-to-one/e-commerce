import React, { FC } from 'react'
import { useAuthStore } from "../../store/auth";
import { Link } from 'react-router-dom';

const Home: React.FC = () => {

  const isLoggedIn = useAuthStore((state) => state.isLoggedIn);
  const user = useAuthStore((state) => state.user);

  // const [isLoggedIn, user] = useAuthStore((state) => [
  //   state.isLoggedIn,
  //   state.user,
  // ]);

  // const { isLoggedIn, user } = useAuthStore(state => ({
  //   isLoggedIn: state.isLoggedIn,
  //   user: state.user
  // }));

  console.log('isLoggedIn', isLoggedIn)
  console.log('user', user)

  return (
    <div>
      {isLoggedIn()
        ? <div>
            <h1>Hello, {user.username}</h1>
            <Link to={'/logout'}>logout</Link>
          </div>
        : <div>
            <h1>Home</h1>
            <Link to={'/login'}>login</Link>
          </div>
      }
    </div>
  )
}

export default Home