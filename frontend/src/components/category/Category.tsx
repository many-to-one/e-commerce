import React, { useEffect } from 'react';
import '../../styles/category.css';
import '../../types/CategoryType';
import { useNavigate } from 'react-router-dom';

interface CategoryProps {
    category: CategoryType;
  }


const Category: React.FC<CategoryProps> = ({category}) => {


  useEffect(() => {
    parseCateg()
  }, [])

    // const parseCateg = () => {
    //   category.category_hierarchy.forEach((title) => {
    //     console.log('CAT TITLE', title)
    //   })
    // }

    const parseCateg = () => {
      // console.log('category_hierarchy:', category.category_hierarchy);
      if (!Array.isArray(category.category_hierarchy)) {
        console.error('category_hierarchy is not an array or is undefined');
        return;
      }
      category.category_hierarchy.forEach((title) => {

        // console.log('TITLE', title)
        // const structuredCategories = {};
        // let currentLevel = structuredCategories;

        // category.category_hierarchy.forEach((item) => {
        //     const cleanItem = item.split('(')[0].trim(); // Clean up the category name
        //     if (!currentLevel[cleanItem]) {
        //         currentLevel[cleanItem] = {}; // Create nested structure
        //     }
        //     currentLevel = currentLevel[cleanItem];
        // });

        // console.log('Structured Categories:', structuredCategories);

      });
    };

    
    

    const navigate = useNavigate();

    const goToProducts = () => {
      navigate(`category-products/${category.slug}`, {state: {catId: category.id}});
      window.location.reload();
    }

  return (
    <div className='categoryCard' onClick={goToProducts}>
        <p className='Cursor'>{category.title}</p>
    </div>
  )
}

export default Category
