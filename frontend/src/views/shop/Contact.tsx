import React, { useState } from "react";

// /home/alex/django/shop/e-commerce/frontend/src/views/shop/Contact.tsx

type ContactForm = {
    name: string;
    email: string;
    subject: string;
    message: string;
};

type Errors = Partial<Record<keyof ContactForm, string>> & { nonField?: string };

const initialForm: ContactForm = {
    name: "",
    email: "",
    subject: "",
    message: "",
};

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const Contact: React.FC = () => {
    const [form, setForm] = useState<ContactForm>(initialForm);
    const [errors, setErrors] = useState<Errors>({});
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState<string | null>(null);

    const handleChange =
        (key: keyof ContactForm) =>
        (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
            setForm((f) => ({ ...f, [key]: e.target.value }));
            setErrors((prev) => ({ ...prev, [key]: undefined, nonField: undefined }));
            setSuccess(null);
        };

    const validate = (): boolean => {
        const next: Errors = {};
        if (!form.name.trim()) next.name = "Name is required";
        if (!form.email.trim()) next.email = "Email is required";
        else if (!emailRegex.test(form.email)) next.email = "Enter a valid email";
        if (!form.subject.trim()) next.subject = "Subject is required";
        if (!form.message.trim()) next.message = "Message is required";
        setErrors(next);
        return Object.keys(next).length === 0;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!validate()) return;
        setLoading(true);
        setErrors({});
        setSuccess(null);

        try {
            const res = await fetch("/api/store/contact/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(form),
            });

            if (res.ok) {
                setSuccess("Twoja wiadomość została wysłana. Skontaktujemy się jak najszybciej.");
                setForm(initialForm);
            } else {
                // try to read JSON error payload if present
                let payload: any = null;
                try {
                    payload = await res.json();
                } catch {
                    /* ignore */
                }
                if (payload && typeof payload === "object") {
                    const fieldErrors: Errors = {};
                    // expecting { field: ["error1", ...], non_field_errors: ["..."] } style
                    for (const k of Object.keys(payload)) {
                        if (k === "non_field_errors" || k === "detail") {
                            fieldErrors.nonField = Array.isArray(payload[k]) ? payload[k].join(" ") : String(payload[k]);
                        } else if (k in form) {
                            const val = payload[k];
                            fieldErrors[k as keyof ContactForm] = Array.isArray(val) ? val.join(" ") : String(val);
                        } else {
                            fieldErrors.nonField = (fieldErrors.nonField ? fieldErrors.nonField + " " : "") + String(payload[k]);
                        }
                    }
                    setErrors(fieldErrors);
                } else {
                    setErrors({ nonField: `Failed to send message (${res.status})` });
                }
            }
        } catch (err) {
            setErrors({ nonField: "Network error. Please try again later." });
        } finally {
            setLoading(false);
        }
    };

    return (
        <main style={{ maxWidth: 720, margin: "2rem auto", padding: "0 1rem" }}>
            <h1>Napisz do nas</h1>
            <p>Jeśli masz pytania, skorzystaj z formulażu kontaktu</p>

            <form onSubmit={handleSubmit} noValidate aria-live="polite">
                <div style={{ marginBottom: 12 }}>
                    <label htmlFor="contact-name">Name</label>
                    <input
                        id="contact-name"
                        type="text"
                        value={form.name}
                        onChange={handleChange("name")}
                        disabled={loading}
                        style={{ display: "block", width: "100%", padding: 8 }}
                        aria-invalid={!!errors.name}
                    />
                    {errors.name && <div style={{ color: "red", marginTop: 4 }}>{errors.name}</div>}
                </div>

                <div style={{ marginBottom: 12 }}>
                    <label htmlFor="contact-email">Email</label>
                    <input
                        id="contact-email"
                        type="email"
                        value={form.email}
                        onChange={handleChange("email")}
                        disabled={loading}
                        style={{ display: "block", width: "100%", padding: 8 }}
                        aria-invalid={!!errors.email}
                    />
                    {errors.email && <div style={{ color: "red", marginTop: 4 }}>{errors.email}</div>}
                </div>

                <div style={{ marginBottom: 12 }}>
                    <label htmlFor="contact-subject">Temat</label>
                    <input
                        id="contact-subject"
                        type="text"
                        value={form.subject}
                        onChange={handleChange("subject")}
                        disabled={loading}
                        style={{ display: "block", width: "100%", padding: 8 }}
                        aria-invalid={!!errors.subject}
                    />
                    {errors.subject && <div style={{ color: "red", marginTop: 4 }}>{errors.subject}</div>}
                </div>

                <div style={{ marginBottom: 12 }}>
                    <label htmlFor="contact-message">Wiadomość</label>
                    <textarea
                        id="contact-message"
                        value={form.message}
                        onChange={handleChange("message")}
                        disabled={loading}
                        rows={6}
                        style={{ display: "block", width: "100%", padding: 8 }}
                        aria-invalid={!!errors.message}
                    />
                    {errors.message && <div style={{ color: "red", marginTop: 4 }}>{errors.message}</div>}
                </div>

                {errors.nonField && <div style={{ color: "red", marginBottom: 12 }}>{errors.nonField}</div>}
                {success && <div style={{ color: "green", marginBottom: 12 }}>{success}</div>}

                <button type="submit" disabled={loading} style={{ padding: "8px 16px" }}>
                    {loading ? "Wysyłam…" : "Wyślij"}
                </button>
            </form>
        </main>
    );
};

export default Contact;