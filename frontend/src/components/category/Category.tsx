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

    // const parseCateg = () => {
    //   category.category_hierarchy.forEach((title) => {
    //     console.log('CAT TITLE', title)
    //   })
    // }

    const parseCateg = () => {
      // console.log('category +++', category)
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

    const goToSubProducts = (subCat) => {
      navigate(`sub-category-products/${category.slug}`, {state: {subCat: subCat}});
      window.location.reload();
    }

    // const upOn = () => {
    //   setShowCategories(false);
    //   // setInterval(() => {
    //   //   setShowCategories(true);
    //   // }, 2000)
    // }

    // const upDown = () => {
    //   setShowSubCategories(null);
    // }

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
