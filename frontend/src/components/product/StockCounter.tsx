import React, { useState } from 'react';

interface StockCounterProps {
    initialQty: number;
    onQuantityChange: (newQuantity: number) => void;
  }

const StockCounter: React.FC<StockCounterProps> = ({ initialQty, onQuantityChange }) => {
  const [orderqty, setOrderqty] = useState<number>(1);

  const handleInputChange = (e) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value) && value > 0) {
      setOrderqty(value);
      onQuantityChange(value)
    }
  };

  const decrementQuantity = () => {
    setOrderqty((prevQty) => Math.max(prevQty - 1, 1));
    const decrement = orderqty - 1
    if ( decrement === 0 ) {
        onQuantityChange(1)
    } else {
        onQuantityChange(orderqty - 1)
    }
  };

  const incrementQuantity = () => {
    setOrderqty((prevQty) => prevQty + 1);
    onQuantityChange(orderqty + 1)
  };


  return (
    <div className='stockCont'>
      <button className='leftStockBtn' onClick={decrementQuantity}>-</button>
      <input
        type="number"
        value={orderqty}
        className='stockInput'
        onChange={handleInputChange}
      />
      <button className='rightStockBtn' onClick={incrementQuantity}>+</button>
    </div>
  );
};

export default StockCounter;
