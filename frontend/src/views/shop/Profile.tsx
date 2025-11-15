import React, { useEffect } from 'react';
import StorefrontRoundedIcon from '@mui/icons-material/StorefrontRounded';
import { useAuthStore } from '../../store/auth';
import { useNavigate } from 'react-router-dom';
import OrderHistory from './OrderHistory';
import { __userId } from '../../utils/auth';
import useAxios from '../../utils/useAxios';

function Profile() {

    // const user = useAuthStore((state) => state.allUserData);
    const user = __userId(); 
    // console.log('user', user['username']);
    // console.log('user', user);
    const navigate = useNavigate();
    const axios_ = useAxios();

    const [vendors, setVendors] = React.useState([])

    // useEffect(() => {
    //   axios_.get(`api/store/vendors/${user['email']}`)
    //     .then(response => {
    //       setVendors(response.data.vendors)
    //       console.log('DRF vendors responce -------------:', response.data);
    //     })
    //     .catch(error => {
    //       console.error('DRF vendors Axios error ----------:', error);
    //       navigate('/login');
    //     });
    //   }, []);

    useEffect(() => {
  const fetchVendors = async () => {
    if (!user) {
      console.warn('User email not defined, redirecting to login');
      navigate('/login');
      return;
    }

    try {
      const response = await axios_.get(`api/store/vendors/${user['email']}`);
      setVendors(response.data.vendors);
      console.log('DRF vendors response -------------:', response.data);
    } catch (error) {
      console.error('DRF vendors Axios error ----------:', error);
      navigate('/login');
    }
  };

  fetchVendors();
}, []); //user



    

    const loginAllegro = ( client_id, vendor_name ) => {
        // navigate('/allegro-auth');
        // DEVELOPMENT
        window.location.href = `https://allegro.pl.allegrosandbox.pl/auth/oauth/authorize?response_type=code&client_id=${encodeURIComponent(client_id)}&redirect_uri=http://localhost:5173/allegro-auth-code/${vendor_name}`;
        // PRODUCTION
        window.location.href = `https://allegro.pl/auth/oauth/authorize?response_type=code&client_id=${encodeURIComponent(client_id)}&redirect_uri=http://kidnetic.pl/allegro-auth-code/${vendor_name}`;


//   return (
//     <div className='flexColumnCenter'>

//         <p>Adres e-mail: {user['email']}</p>
//         <p>Imię i nazwisko: {user['first_name']} {user['last_name']}</p>

//         {user['user_id'] === 1 &&
//             <button className='Cursor fileUpload' onClick={()=> navigate('/upload-files')}>Importuj oferty allegro</button>
//             // <button className='Cursor fileUpload' onClick={()=> navigate('/allegro-auth')}>Zaloguj się do allegro</button>
//         }
//          {/* <button className='Cursor fileUpload' onClick={()=> loginAllegro()}>Zaloguj się do allegro</button> */}

//         {vendors.length > 0 && 
//             <div className='flexColumnCenter'>
//                 <p>Twoje sklepy:</p>
//                 {vendors.map((vendor, index) => (
//                     <div key={index} className='flexRowCenter gap10px border1px p5px m5px Cursor'>
//                         {/* <MaterialIcon icon="store" onClick={()=> loginAllegro(vendor.client_id, vendor.name)} /> */}
//                         <StorefrontRoundedIcon onClick={()=> loginAllegro(vendor.client_id, vendor.name)} />
//                         <p>{vendor.marketplace} - {vendor.name}</p>
//                     </div>
//                 ))}
//             </div>
//         }

//         {/* <button className='Cursor' onClick={()=> navigate('/profile-edit')}>Edytuj profil</button> */}
//         <button className='Cursor' onClick={()=> navigate('/returns')}>Zwroty</button>
//         <p>Historia zamówień:</p>
//         <OrderHistory />
//     </div>
//   )
// }

return (
  <div className='flexColumnCenter'>
    {user ? (
      <>
        <p>Adres e-mail: {user['email']}</p>
        <p>Imię i nazwisko: {user['first_name']} {user['last_name']}</p>

        {user['user_id'] === 1 && (
          <button
            className='Cursor fileUpload'
            onClick={() => navigate('/upload-files')}
          >
            Importuj oferty allegro
          </button>
        )}

        {vendors.length > 0 && (
          <div className='flexColumnCenter'>
            <p>Twoje sklepy:</p>
            {vendors.map((vendor, index) => (
              <div
                key={index}
                className='flexRowCenter gap10px border1px p5px m5px Cursor'
              >
                <StorefrontRoundedIcon onClick={() => loginAllegro(vendor['client_id'], vendor['name'])} />
                <p>{vendor['marketplace']} - {vendor['name']}</p>
              </div>
            ))}
          </div>
        )}

        <button className='Cursor' onClick={() => navigate('/returns')}>
          Zwroty
        </button>
        <p>Historia zamówień:</p>
        <OrderHistory />
      </>
    ) : (
      <p>Ładowanie danych użytkownika...</p>
    )}
  </div>
);
}

export default Profile