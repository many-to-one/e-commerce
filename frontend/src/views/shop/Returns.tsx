// import React, { useEffect, useState } from 'react'
// import useAxios from '../../utils/useAxios'
// import { showToast } from '../../utils/toast';
// import '../../types/OrderItemType';
// import { useAuthStore } from '../../store/auth';

// type ReturnItemType = {
//   id: number;
//   order: { oid: string };
//   product: { name: string; image: string; sku: string };
//   qty: number;
//   price: string;
//   total: string;
//   date: string;
//   return_status: string;
//   return_reason: string;
//   return_decision: string;
//   return_costs: string;
//   return_delivery_courier: string;
//   return_tracking_id: string;
// };

// function Returns() {

//   const axios_ = useAxios();
//   const user = useAuthStore((state) => state.allUserData);
//   const [products, setProducts] = useState<OrderItemType[]>([]);

//   const usersReturns = async () => {
//     try {
//           const resp = await axios_.post('api/store/returns', 
//             {
//               userId: user.user_id
//             }
//           )
//           setProducts(resp.data.returns)

//           console.log('usersReturns', resp)
//         } catch (error) {
//             showToast("error", error)
//             console.log('usersReturns error ----', error)
//         }
//   }

//   useEffect(() => {
//     usersReturns();
//   }, [])
//   return (
//     <div>Returns</div>
//   )
// }

// export default Returns



import React, { useEffect, useState } from "react";
import useAxios from "../../utils/useAxios";
import { showToast } from "../../utils/toast";
import { useAuthStore } from "../../store/auth";
import '../../styles/returns.css';

type ReturnItemType = {
  id: number;
  order: { oid: string ; sub_total: string;};
  product: { title: string; image: string; sku: string; shipping_amount: string };
  qty: number;
  price: string;
  date: string;
  return_status: string;
  return_reason: string;
  return_decision: string;
  return_costs: string;
  return_delivery_courier: string;
  return_tracking_id: string;
};

function Returns() {
  const axios_ = useAxios();
  const user = useAuthStore((state) => state.allUserData);
  const [returns, setReturns] = useState<ReturnItemType[]>([]);
  const [loading, setLoading] = useState(true);

  const usersReturns = async () => {
    try {
      const resp = await axios_.post("api/store/returns", {
        userId: user.user_id,
      });
      setReturns(resp.data.returns);
    } catch (error: any) {
      showToast("error", error.message || "Błąd pobierania zwrotów");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    usersReturns();
  }, []);

  if (loading) return <p className="p-4">Ładowanie zwrotów...</p>;

  return (
    <div className="returns-container">
      {returns.map(ret => (
        <div className="return-card" key={ret.id}>
          <img src={`http://localhost:8100/${ret.product.image}`} alt={ret.product.title} />
          <div>
            <h3>{ret.product.title}</h3>
            <p className='flexRowBetween'key={ret.id}><b>ID zamówienie:</b> {ret.order.oid}</p>
            <p className='flexRowBetween'key={ret.id}><b>Ilość:</b> {ret.qty} × {ret.price} PLN = {ret.order.sub_total} PLN</p>
            <p className='flexRowBetween'key={ret.id}><b>Powód:</b> {ret.return_reason}</p>
            <p className='flexRowBetween'key={ret.id}><b>Decyzja:</b> {ret.return_decision}</p>
            <p className='flexRowBetween'key={ret.id}><b></b> {ret.return_costs}</p>
            <p className='flexRowBetween'key={ret.id}><b>Koszty zwrotu:</b> {ret.product.shipping_amount}</p>
            {/* renderuj tylko jeśli nie null/undefined/puste */}
            {ret.return_delivery_courier && (
              <p className="flexRowBetween"><b>Kurier:</b> {ret.return_delivery_courier}</p>
              )}
              {ret.return_tracking_id && (
                <p className="flexRowBetween"><b>Numer śledzenia:</b> {ret.return_tracking_id}</p>
              )}
            <p className='flexRowBetween'key={ret.id}><b>Status:</b> {ret.return_status}</p>
          </div>
        </div>
      ))}
    </div>

  );
}

export default Returns;
