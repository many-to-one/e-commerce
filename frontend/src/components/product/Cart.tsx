import React, { useEffect } from 'react'
import MaterialIcon from '@material/react-material-icon';
import useAxios from '../../utils/useAxios';
import { useAuthStore } from '../../store/auth';

function Cart () {

  return (
    <div>
        <MaterialIcon icon="shopping_cart" />
    </div>
  )
}

export default Cart