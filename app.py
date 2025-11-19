import streamlit as st
from fpdf import FPDF
import datetime

# Save invoice details to a CSV file
import pandas as pd
import os

history_file = "invoice_history.csv"

def save_invoice(client, service, amount, invoice_id):
    entry = pd.DataFrame([{
        "Invoice ID": invoice_id,
        "Client": client,
        "Service": service,
        "Amount": amount
    }])

    if os.path.exists(history_file):
        old_data = pd.read_csv(history_file)
        updated_data = pd.concat([old_data, entry], ignore_index=True)
    else:
        updated_data = entry

    updated_data.to_csv(history_file, index=False)

def generate_invoice_pdf(client_name, service_desc, amount, invoice_id):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Invoice #{invoice_id}", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Date: {datetime.date.today()}", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Billed To: {client_name}", ln=True)
    pdf.ln(10)
    pdf.multi_cell(0, 10, txt=f"Service Description:\n{service_desc}")
    pdf.cell(200, 10, txt=f"Total Amount Due: ${amount:.2f}", ln=True)
    pdf.ln(20)
    pdf.set_font("Arial", style='I', size=10)
    pdf.cell(0, 10, "Thank you for your business!", ln=True, align='C')
    filename = f"Invoice_{invoice_id}.pdf"
    pdf.output(filename)
    return filename

st.title("🧾 AutoBill Invoice Generator")
client_name = st.text_input("Client Name")
service_desc = st.text_area("Service Description")
amount = st.number_input("Amount ($)", min_value=0.0)
invoice_id = st.text_input("Invoice ID")

if st.button("Generate Invoice"):
    if client_name and service_desc and invoice_id:
        pdf_file = generate_invoice_pdf(client_name, service_desc, amount, invoice_id)
        with open(pdf_file, "rb") as f:
            st.download_button("📥 Download Invoice PDF", f, file_name=pdf_file, mime="application/pdf")
        save_invoice(client_name, service_desc, amount, invoice_id)
        st.success(f"Invoice {invoice_id} generated successfully!")
    else:
        st.error("Please fill in all fields before generating.")

if st.button("Show Invoice History"):
    if os.path.exists(history_file):
        data = pd.read_csv(history_file)
        st.dataframe(data)
    else:
        st.warning("No invoice history found.")


