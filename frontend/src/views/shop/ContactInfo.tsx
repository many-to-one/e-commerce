import React from "react";


const ContactInfo: React.FC = () => {
    return (
        <section style={{ maxWidth: 720, margin: "2rem auto", padding: "0 1rem" }}>
            <h2>Informacje kontaktowe</h2>
            <p>Możesz się z nami skontaktować pod następującymi danymi:</p>
            <ul>
                <li>Email: </li>
                <li>Telefon: </li>
            </ul>
            <p>Jesteśmy dostępni od poniedziałku do piątku w godzinach 9:00 - 17:00.</p>
        </section>
    );
}

export default ContactInfo;