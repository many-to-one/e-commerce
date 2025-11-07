import React, { useEffect, useState } from 'react';
import '../../styles/category.css';
import '../../types/CategoryType';
import { useNavigate } from 'react-router-dom';

interface CategoryProps {
    category: CategoryType;
    // showCategories: boolean;
  }


const Category: React.FC<CategoryProps> = ({category}) => {

  const [showCategories, setShowCategories] = useState(false);
  const [showSubCategories, setShowSubCategories] = useState<CategoryType | null>();


  useEffect(() => {
    parseCateg()
  }, [])


    const parseCateg = () => {
      // console.log('category +++', category)
      if (!Array.isArray(category.category_hierarchy)) {
        console.error('category_hierarchy is not an array or is undefined');
        return;
      }
      category.category_hierarchy.forEach((title) => {

      });
    };

    
    

    const navigate = useNavigate();

    const goToProducts = () => {
      navigate(`category-products/${category.slug}`, {state: {catId: category.id}});
      window.location.reload(); // Ważne do odświeżenia widoku po nawigacji !!
    }

    const goToSubProducts = (subCat) => {
      console.log('subCat', subCat)
      navigate(`sub-category-products/${category.slug}`, {state: {subCat: subCat}});
      window.location.reload(); // Ważne do odświeżenia widoku po nawigacji !!
    }

  return (
    <div className='CatTitIn'>
        <div
          className='Cursor catTitle'
          onClick={goToProducts}
          onMouseEnter={() => {
            setShowCategories(true);
          }}
          onMouseLeave={() => {
            setShowCategories(false);
          }}
        >
          <p>{category.title}</p>
        </div>
        
        <div className='subCat'
          onMouseEnter={() => {
            setShowCategories(true);
          }}
          onMouseLeave={() => {
            // setShowCategories(false);
          }}
        >
          {showCategories && (
            <div>
              {category.category_hierarchy
                ?.flat() // Flatten the nested array
                .map((subcat, index) => (
                  <p className="Cursor" key={index} onClick={() => goToSubProducts(subcat)}>
                    {subcat}
                  </p>
                ))}
            </div>
          )}

        </div>
      </div>
  )
}

export default Category
