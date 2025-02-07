import React from 'react';
import '../../styles/category.css';

interface CategoryProps {
    category: CategoryType;
  }


const Category: React.FC<CategoryProps> = ({category}) => {

    // console.log('Product props', category)
  return (
    <div className='flexColumnCenter'>
        <img src={category.image} alt="" className='categoryCard categoryImage'/>
        <p>{category.title}</p>
    </div>
  )
}

export default Category