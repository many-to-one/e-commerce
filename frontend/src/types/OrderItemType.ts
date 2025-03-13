type OrderItemType = {
    city: string;
    date: string;
    delivery_status: string;
    oid: string;
    total: string;
    sub_total: string;
    order_status: string;
    payment_status: string;
    initial_return: string;
    delivery_courier: string;
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
    return_delivery_courier: string;
    return_tracking_id: string;
};
