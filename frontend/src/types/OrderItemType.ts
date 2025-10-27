type InvoiceType = {
  invoice_number?: string; // optional, if you expose it in serializer
};

type InvoiceFileType = {
  id: number;
  file: string;        // URL to the PDF
  created_at: string;  // ISO date string
  invoice: InvoiceType | null; // optional, if you expose it in serializer
  invoice_correction: InvoiceType | null;
};

type OrderItemType = {
    city: string;
    date: string;
    delivery_status: string;
    oid: string;
    total: string;
    sub_total: string;
    shipping_amount: string;
    order_status: string;
    payment_status: string;
    delivery_courier: string;
    tracking_id: string;
    delivery: string;
    invoices: InvoiceFileType[];
    invoice_correction: InvoiceFileType[];
    orderitem: {
        product: {
            image: string;
            title: string;
        };
        price: string;
        qty: string;
        total: string;
        initial_return: boolean;
        return_reason: string;
        return_decision: string;
        return_costs: string;
        return_delivery_courier: string;
        return_tracking_id: string;
    }[];
};
