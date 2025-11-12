import React, { useEffect, useState } from 'react';
import '../../styles/category.css';
import '../../types/CategoryType';
import { useNavigate } from 'react-router-dom';
import ArrowBackIosNewRoundedIcon from '@mui/icons-material/ArrowBackIosNewRounded';

interface CategoryProps {
    category: CategoryType;
  }


const Category: React.FC<CategoryProps> = ({category}) => {

  const [showCategories, setShowCategories] = useState(false);
  const [showSubCategories, setShowSubCategories] = useState<CategoryType | null>();
  const [isMobile, setIsMobile] = useState(false);




  useEffect(() => {
    parseCateg()
  }, [])


    const parseCateg = () => {
      setShowSubCategories(category)
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

    useEffect(() => {
      const checkMobile = () => setIsMobile(window.innerWidth <= 768);
      checkMobile();
      window.addEventListener("resize", checkMobile);
      return () => window.removeEventListener("resize", checkMobile);
    }, []);


    const toggleCategories = () => {
      setShowCategories((prev) => !prev);
    };


  return (
  <div className="CatTitIn">
    <div
      className="Cursor catTitle"
      onClick={isMobile ? toggleCategories : goToProducts}
      onMouseEnter={!isMobile ? () => setShowCategories(true) : undefined}
      onMouseLeave={!isMobile ? () => setShowCategories(false) : undefined}
    >
      <p>{category.title}</p>
    </div>

    {showCategories && showSubCategories && (
      <div
        className="subCat"
        onMouseEnter={!isMobile ? () => setShowCategories(true) : undefined}
        onMouseLeave={!isMobile ? () => setShowCategories(false) : undefined}
      >
        {/* Close button */}
          <ArrowBackIosNewRoundedIcon  onClick={() => setShowCategories(false)} />

        {category.category_hierarchy?.flat().map((subcat, index) => (
          <p
            className="Cursor"
            key={index}
            onClick={() => goToSubProducts(subcat)}
          >
            {subcat}
          </p>
        ))}
      </div>
    )}
  </div>
);


}

export default Category


