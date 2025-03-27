import React, { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { showToast } from '../../utils/toast';
import useAxios from '../../utils/useAxios';
import { useAuthStore } from '../../store/auth';
import Cookies from 'js-cookie';
import { __userId } from '../../utils/auth';

function SuccessPayment() {
    
  const navigate = useNavigate();  
  const axios = useAxios();
  const user = __userId()

  const [searchParams] = useSearchParams();
  const orderId = searchParams.get("order_id");
  const userId = searchParams.get("buyer");
  const sessionId = searchParams.get("session_id");

  const finishOrder = async () => {
    console.log("SuccessPayment finishOrder", orderId)
    const res = await axios.post('api/store/finish-order', {
        oid: orderId,
        user_id: user?.['user_id'],
    })

    console.log("SuccessPayment res", res)
  }

  useEffect(() => {
    finishOrder();
  }, [])

  useEffect(() => {
    showToast("success", "Gratulacje!")
  }, [])

  return (
    <div className='flexColumnCenter gap-15'>
        <img src="/success_payment.jpg" alt="" className='alertImg'/>
        <button onClick={() => (navigate('/'))}>Kontynuuj Zajupy</button>
    </div>
  )
}

export default SuccessPayment