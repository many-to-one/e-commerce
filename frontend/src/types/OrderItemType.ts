type OrderItemType = {
    city: string;
    date: string;
    delivery_status: string;
    oid: string;
    total: string;
    order_status: string;
    payment_status: string;
    tracking_id: string;
    orderitem: {
        product: {
            image: string;
            title: string;
        };
        price: string;
        qty: string;
        total: string;
    }[];
};
