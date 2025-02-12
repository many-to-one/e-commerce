import React from 'react'

interface AddToCardProps {
    id: number,
    quantity: number,
}

const AddToCard: React.FC<AddToCardProps> = ({id, quantity}) => {


    const sendToCard = () => {
        console.log('AddToCard', id, quantity)
    }

  return (
    <div>
        <button className='mainBtn' onClick={sendToCard}>Add to Card</button>
    </div>
  )
}

export default AddToCard