// import React from 'react';

// const HotSail: React.FC = () => {
//   return (
//     <div className="hot-sail">
//       {/* <img src="/hot-deal.png" alt="Hot Sale" width={50} height={50} /> */}
//       <span className="hot-label">🔥 Hot Deal</span>
//     </div>
//   );
// };

// export default HotSail;


import React from 'react';
import '../../styles/product.css';

const HotSail: React.FC = () => {
  return (
    <div className="hot-sail">
      <div className="hot-badge">
       <p>Okazja!</p>
      </div>
    </div>
  );
};

export default HotSail;
