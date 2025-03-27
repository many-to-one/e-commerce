import axios from '../../utils/axios';
import React, { useEffect } from 'react';
import '../../types/RatingType'


const Likes: React.FC<RatingType> = ({rating }) => {

  // console.log('Likes', rating)

  return (
    <div>
      {rating === "5" && <p>★★★★★</p>}
      {rating === "4" && <p>★★★★☆</p>}
      {rating === "3" && <p>★★★☆☆</p>}
      {rating === "2" && <p>★★☆☆☆</p>}
      {rating === "1" && <p>★☆☆☆☆</p>}
      {rating === "0" && <p>☆☆☆☆☆</p>}
    </div>
  )
}

export default Likes