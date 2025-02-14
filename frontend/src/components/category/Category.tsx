import React from 'react';
import '../../styles/category.css';
import '../../types/CategoryType';
import { useNavigate } from 'react-router-dom';

interface CategoryProps {
    category: CategoryType;
  }


const Category: React.FC<CategoryProps> = ({category}) => {

    const navigate = useNavigate();

    const goToProducts = () => {
      console.log('goToProducts', category)
      console.log('goToProducts', category)
      navigate(`category-products/${category.slug}`)
    }

  return (
    <div className='flexColumnCenter' onClick={goToProducts}>
        <img src={category.image} alt="" className='categoryCard categoryImage'/>
        <p>{category.title}</p>
    </div>
  )
}

export default Category