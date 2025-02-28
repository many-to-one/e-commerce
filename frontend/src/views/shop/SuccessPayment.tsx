import React, { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { showToast } from '../../utils/toast';

function SuccessPayment() {
    
  const navigate = useNavigate();  

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