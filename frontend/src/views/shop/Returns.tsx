import React, { useEffect, useState } from 'react'
import useAxios from '../../utils/useAxios'
import { showToast } from '../../utils/toast';
import '../../types/OrderItemType';
import { useAuthStore } from '../../store/auth';

function Returns() {

  const axios_ = useAxios();
  const user = useAuthStore((state) => state.allUserData);
  const [products, setProducts] = useState<OrderItemType[]>([]);

  const usersReturns = async () => {
    try {
          const resp = await axios_.post('api/store/returns', 
            {
              userId: user.user_id
            }
          )
          setProducts(resp.data.returns)

          console.log('usersReturns', resp)
        } catch (error) {
            showToast("error", error)
        }
  }

  useEffect(() => {
    usersReturns();
  }, [])
  return (
    <div>Returns</div>
  )
}

export default Returns