import React from 'react'
import { useNavigate } from 'react-router-dom'

function SuccessPayment() {
    
  const navigate = useNavigate();  

  return (
    <div className='flexColumnCenter gap-15'>
        <img src="/success_payment.jpg" alt="" className='alertImg'/>
        <button onClick={() => (navigate('/'))}>Continue shopping</button>
    </div>
  )
}

export default SuccessPayment