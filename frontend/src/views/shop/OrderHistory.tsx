import React, { useEffect, useState } from 'react'
import { useAuthStore } from '../../store/auth';
import useAxios from '../../utils/useAxios';
import '../../types/OrderItemType';
import { showToast } from '../../utils/toast';
import { useNavigate } from 'react-router-dom';
import '../../types/OrderItemType';
import InfoOutlineRoundedIcon from '@mui/icons-material/InfoOutlineRounded';

function OrderHistory() {

    const user = useAuthStore((state) => state.allUserData);
    const axios_ = useAxios();
    const navigate = useNavigate();

    const [products, setProducts] = useState<OrderItemType[]>([]);
    const [returnReasons, setReturnReasons] = useState<[]>([]);
    const [isHovered, setIsHovered] = useState(false);

    useEffect(() => {
        fetchHistory()
        }, [])


    const fetchHistory = async () => {
        try {
            const resp = await axios_.get('api/store/order-history')
            setProducts(resp.data.results)
            setReturnReasons(resp.data.return_reasons)
            console.log('OrderHistory', resp)
        } catch (error) {
            showToast("error", error)
        }
    }

    const formatDate = (isoString) => {
        const date = new Date(isoString);
        return date.toISOString().slice(0, 16).replace('T', ' '); // "2025-03-18 12:15"
    };
        

        const API_BASE_URL = "https://api-preprod.dpsin.dpdgroup.com:8443/shipping/v1";

        const getDPDToken = async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/login`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-DPD-LOGIN": "test",
                        "X-DPD-PASSWORD": "thetu4Ee",
                        "X-DPD-BUCODE": "021"
                    }
                });
        
                if (!response.ok) {
                    throw new Error("Failed to authenticate");
                }
        
                const data = await response.json();
                console.log('getDPDToken', data)
                // return data.token; // Assuming the API response contains a "token" field
            } catch (error) {
                console.error("Error getting DPD token:", error);
                return null;
            }
        };


    return (
      <div className='orders-history'>
        {products?.map((item, index) => (
            <div key={index}>
                <div className='cartItem'>
                    <div>
                        <div className='flexColumnStart'>
                            <p className='flexRowBetween'><b>ID zamówienie:</b> {item.oid}</p>
                            <p className='flexRowBetween'><b>Data złożenia:</b> {formatDate(item.date)}</p>
                            <p className='flexRowBetween'><b>Status opłaty:</b> {item.payment_status}</p>
                            <p className='flexRowBetween'><b>Status dostawy:</b> {item.delivery_status}</p> 
                            <p className='flexRowBetween'><b>Dostawa:</b> {item.delivery}</p>
                            <p className='flexRowBetween'><b>Numer śledzenia:</b> {item.tracking_id}</p> 
                        </div>
                        {item.orderitem.map((order, index) => (
                           <div>
                                <div className='flexRowBetween'>
                                    <div className='flexRowBetween gap-15'>
                                        <img src={order.product.image} alt="" width={100}/>
                                        <p className='history-title'>{order.product.title}</p>
                                    </div>

                                    { order.initial_return === true ?
                                        (
                                            <div>
                                                <div 
                                                    className="flexRowBetween gap-15 return-info" 
                                                    onMouseEnter={() => setIsHovered(true)}
                                                    onMouseLeave={() => setIsHovered(false)}
                                                >
                                                    <p>Otworzyłeś zwrot:</p>
                                                    {/* <MaterialIcon icon="info"  className="Cursor"/> */}
                                                    <InfoOutlineRoundedIcon className="Cursor"/>
                                                </div>
                                                
                                                {isHovered && (
                                                    <div 
                                                        className="return-data" 
                                                        // onMouseEnter={() => setIsHovered(true)} 
                                                        onMouseLeave={() => setIsHovered(false)}
                                                    >
                                                        {order.return_reason !== null &&
                                                            <p className="flexRowBetween"><b>Powód:</b> {order.return_reason}</p>
                                                        }
                                                        {order.return_decision !== null &&
                                                            <p className="flexRowBetween"><b>Decyzja:</b> {order.return_decision}</p>
                                                        }
                                                        {order.return_costs !== null &&
                                                            <p className="flexRowBetween"><b>Koszty:</b> {order.return_costs}</p>
                                                        }
                                                        {order.return_delivery_courier !== null &&
                                                            <p className="flexRowBetween"><b>Zwrot przez:</b> {order.return_delivery_courier}</p>
                                                        }
                                                        {order.return_tracking_id !== null &&
                                                            <p className="flexRowBetween"><b>Numer śledzenia zwrotu:</b> {order.return_tracking_id}</p>
                                                        }
                                                    </div>
                                                )}
                                            </div>
                                        ) :
                                        (
                                            <button 
                                                onClick={() => navigate(
                                                    '/initial-return', 
                                                    {state: {
                                                        oid: item.oid, 
                                                        date: item.date,
                                                        payment_status: item.payment_status,
                                                        order_status: item.order_status,
                                                        tracking_id: item.tracking_id,
                                                        total_price: item.sub_total,
                                                        orderitem: order,
                                                        return_reasons: returnReasons,
                                                    }}
                                                )} className='mainBtn'
                                                // onClick={getDPDToken}
                                            >
                                                Otwórz zwrot
                                            </button>
                                        )
                                    }
                                </div>
                                <p className='flexRowBetween'><b>Cena:</b> {order.price}PLN</p>
                                <p className='flexRowBetween'><b>Ilość:</b> {order.qty} szt.</p>
                                <p className='flexRowBetween'><b>Razem:</b> {item.sub_total}PLN</p>
                                <p className='flexRowBetween'><b>Koszt dostawy:</b> {item.shipping_amount}PLN</p>
                                <hr />

                                {item.invoices.length > 0 ? (
                                    <div className="flexColumnStart">
                                        <b>Faktury:</b>
                                        {item.invoices.map(inv => (
                                        <p key={inv.id}>
                                            <a href={inv.file} target="_blank" rel="noopener noreferrer">
                                            Pobierz fakturę:  {inv.invoice?.invoice_number || `Korekta: ${inv.invoice_correction?.invoice_number}`}
                                            </a>
                                        </p>
                                        ))}
                                    </div>
                                    ) : (
                                    <p><b>Faktury:</b> Brak</p>
                                    )}



                            </div>
                        ))}
                        <div className='flexRowBetween'>
                            <p><b>KOSZT CAŁKOWITY:</b></p>
                            <p><b>{item.total} PLN</b></p>
                        </div>
                        <hr /> 

                       
                    </div>
                </div>
            </div>
        ))}
        <br />
        <br />
        <br />
        <br />
      </div>
    )
}

export default OrderHistory