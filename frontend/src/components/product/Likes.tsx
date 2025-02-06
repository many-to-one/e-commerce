import axios from '../../utils/axios';
import React, { useEffect } from 'react';


const Likes: React.FC<RatingType> = ({rating }) => {

  // console.log('Likes', rating)

  return (
    <div>
      {rating === "5" && <p>★★★★★</p>}
    </div>
  )
}

export default Likes