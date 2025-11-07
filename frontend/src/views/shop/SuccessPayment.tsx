import React, { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { showToast } from '../../utils/toast';
import useAxios from '../../utils/useAxios';
import { useAuthStore } from '../../store/auth';
import Cookies from 'js-cookie';
import { __userId } from '../../utils/auth';

function SuccessPayment() {
    
  const navigate = useNavigate();  

  useEffect(() => {
    showToast("success", "Gratulacje!")
  }, [])

  return (
    <div className='flexColumnCenter gap-15'>
        <img src="/success_payment.jpg" alt="" className='alertImg'/>
        <button onClick={() => (navigate('/'))}>Kontynuuj Zakupy</button>
    </div>
  )
}

export default SuccessPayment