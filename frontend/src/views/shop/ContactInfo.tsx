import React, { useEffect, useState } from "react";
import useAxios from "../../utils/useAxios";
import { showToast } from "../../utils/toast";


const ContactInfo: React.FC = () => {

    const axios = useAxios();

    const [fullName, setFullName] = useState<string>('');
    const [email, setEmail] = useState<string>('');
    const [mobile, setMobile] = useState<string>('');
    const [address, setAddress] = useState<string>('');
    const [nip, setNip] = useState<string>('');
    const [descr, setDescr] = useState<string>('');

    useEffect(() => {
        fetchData('api/store/vendor-contact')
    }, [])

    const fetchData = async (endpoint) => {
        try {
            const resp = await axios.get(endpoint)
            setFullName(resp.data.results[0].name)
            setEmail(resp.data.results[0].email)
            setMobile(resp.data.results[0].mobile)
            setAddress(resp.data.results[0].address)
            setNip(resp.data.results[0].nip)
            setDescr(resp.data.results[0].description)
            console.log('vendor-contact', resp)
        } catch (error) {
            showToast("error", error)
        }
    }

    return (
        <section style={{ maxWidth: 720, margin: "2rem auto", padding: "0 1rem" }}>
            <h2>Informacje kontaktowe</h2>
            <h4>{fullName}</h4>
            <h4>{address}</h4>
            <h4>{email}</h4>
            <h4>{mobile}</h4>
            <h4>NIP: {nip}</h4>
            <p>{descr}</p>
        </section>
    );
}

export default ContactInfo;