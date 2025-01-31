import React, { useEffect } from 'react'
import { logout } from '../../utils/auth'

const Logout =() => {

    useEffect(() => {
        logout();
    }, [])

  return (
    <div>Logout</div>
  )
}

export default Logout