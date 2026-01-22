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

def generate_invoice_pdf(client_name, service_desc, services_amount, invoice_id, line_items=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Invoice #{invoice_id}", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Date: {datetime.date.today()}", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Billed To: {client_name}", ln=True)
    pdf.ln(10)
    
    # Add items table if provided
    items_total = 0.0
    if line_items and len(line_items) > 0:
        pdf.set_font("Arial", style='B', size=11)
        pdf.cell(0, 10, txt="Items", ln=True)
        pdf.set_font("Arial", size=9)
        
        # Table header
        pdf.set_fill_color(200, 200, 200)
        pdf.cell(40, 8, txt="Company", border=1, fill=True)
        pdf.cell(30, 8, txt="Category", border=1, fill=True)
        pdf.cell(50, 8, txt="Description", border=1, fill=True)
        pdf.cell(20, 8, txt="Qty", border=1, align='C', fill=True)
        pdf.cell(30, 8, txt="Unit Price", border=1, align='C', fill=True)
        pdf.cell(30, 8, txt="Total", border=1, align='C', fill=True, ln=True)
        
        # Table rows
        pdf.set_fill_color(255, 255, 255)
        for item in line_items:
            company = item.get("company", "")[:15]
            category = item.get("product_category", "")[:12]
            description = item.get("description", "")[:20]  # Limit to 20 chars
            qty = item.get("quantity", 0)
            unit_price = item.get("unit_price", 0.0)
            total = qty * unit_price
            items_total += total
            
            pdf.cell(40, 8, txt=company, border=1)
            pdf.cell(30, 8, txt=category, border=1)
            pdf.cell(50, 8, txt=description, border=1)
            pdf.cell(20, 8, txt=str(qty), border=1, align='C')
            pdf.cell(30, 8, txt=f"{unit_price:.2f}", border=1, align='C')
            pdf.cell(30, 8, txt=f"{total:.2f}", border=1, align='C', ln=True)
        
        # Items subtotal
        pdf.set_font("Arial", style='B', size=10)
        pdf.cell(150, 8, txt="Items Subtotal:", align='R')
        pdf.cell(40, 8, txt=f"{items_total:.2f}", border=0, align='C', ln=True)
        pdf.ln(5)
    
    # Add service description and amount if provided
    if service_desc or services_amount > 0:
        pdf.set_font("Arial", style='B', size=11)
        pdf.cell(0, 10, txt="Services", ln=True)
        pdf.set_font("Arial", size=10)
        
        if service_desc:
            pdf.multi_cell(0, 5, txt=service_desc)
        
        # Services amount
        pdf.set_font("Arial", style='B', size=10)
        pdf.cell(150, 8, txt="Services Amount:", align='R')
        pdf.cell(40, 8, txt=f"{services_amount:.2f}", border=0, align='C', ln=True)
        pdf.ln(5)
    
    # Total amount due
    total_amount = items_total + services_amount
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(150, 10, txt="Total Amount Due:", align='R')
    pdf.cell(40, 10, txt=f"{total_amount:.2f}", border=0, align='C', ln=True)
    pdf.ln(20)
    
    # Footer
    pdf.set_font("Arial", style='I', size=10)
    pdf.cell(0, 10, "Thank you for your business!", ln=True, align='C')
    filename = f"Invoice_{invoice_id}.pdf"
    pdf.output(filename)
    return filename

st.title("🧾 AutoBill Invoice Generator")
client_name = st.text_input("Client Name")
invoice_id = st.text_input("Invoice ID")

# Load items lookup file
items_lookup_file = "items_lookup.csv"
try:
    if os.path.exists(items_lookup_file):
        items_df = pd.read_csv(items_lookup_file, encoding='utf-8')
        items_list = items_df['item_name'].dropna().tolist()
        companies_list = sorted([x for x in items_df['company'].unique().tolist() if pd.notna(x)])
        product_categories_list = sorted([x for x in items_df['product_category'].unique().tolist() if pd.notna(x)])
        # Create dicts for quick lookup
        price_lookup = dict(zip(items_df['item_name'].dropna(), items_df['unit_price']))
        company_product_lookup = items_df.groupby('company')['product_category'].apply(lambda x: sorted([y for y in x.unique().tolist() if pd.notna(y)])).to_dict()
        company_category_items_lookup = items_df.groupby(['company', 'product_category'])['item_name'].apply(list).to_dict()
    else:
        items_list = []
        companies_list = []
        product_categories_list = []
        price_lookup = {}
        company_product_lookup = {}
        company_category_items_lookup = {}
except UnicodeDecodeError:
    items_list = []
    companies_list = []
    product_categories_list = []
    price_lookup = {}
    company_product_lookup = {}
    company_category_items_lookup = {}
    st.warning("Could not read items_lookup.csv. Please check file encoding.")

# Expandable section for items and quantities
with st.expander("📋 Add Items & Quantities", expanded=False):
    st.write("Select company first, then product category, then choose items")
    
    if "line_items" not in st.session_state:
        st.session_state.line_items = []
    
    col1, col2, col3, col4, col5, col6 = st.columns([1.2, 1.2, 1.5, 1, 1, 1])
    with col1:
        st.write("**Company**")
    with col2:
        st.write("**Product Category**")
    with col3:
        st.write("**Item Description**")
    with col4:
        st.write("**Quantity**")
    with col5:
        st.write("**Unit Price**")
    with col6:
        st.write("**Total**")
    
    # Display existing items
    for idx, item in enumerate(st.session_state.line_items):
        col1, col2, col3, col4, col5, col6 = st.columns([1.2, 1.2, 1.5, 1, 1, 1])
        
        with col1:
            # Company selector
            current_company = item.get("company", "")
            companies_with_blank = [""] + companies_list
            company_index = companies_with_blank.index(current_company) if current_company in companies_with_blank else 0
            selected_company = st.selectbox(
                f"Company {idx+1}",
                companies_with_blank,
                index=company_index,
                key=f"company_select_{idx}",
                label_visibility="collapsed"
            )
            st.session_state.line_items[idx]["company"] = selected_company
        
        with col2:
            # Product Category selector filtered by company
            company_categories = company_product_lookup.get(selected_company, []) if selected_company else []
            current_category = item.get("product_category", "")
            categories_with_blank = [""] + company_categories
            category_index = categories_with_blank.index(current_category) if current_category in categories_with_blank else 0
            
            selected_category = st.selectbox(
                f"Category {idx+1}",
                categories_with_blank,
                index=category_index,
                key=f"category_select_{idx}",
                label_visibility="collapsed"
            )
            st.session_state.line_items[idx]["product_category"] = selected_category
        
        with col3:
            # Item selector filtered by company and category
            items_by_company_category = company_category_items_lookup.get((selected_company, selected_category), []) if selected_company and selected_category else []
            current_item = item.get("description", "")
            items_with_blank = [""] + items_by_company_category
            item_index = items_with_blank.index(current_item) if current_item in items_with_blank else 0
            
            selected_item = st.selectbox(
                f"Item {idx+1}",
                items_with_blank,
                index=item_index,
                key=f"item_select_{idx}",
                label_visibility="collapsed"
            )
            st.session_state.line_items[idx]["description"] = selected_item
            
            # Auto-fill unit price if item is in lookup
            if selected_item in price_lookup:
                st.session_state.line_items[idx]["unit_price"] = float(price_lookup[selected_item])
        
        with col4:
            st.session_state.line_items[idx]["quantity"] = st.number_input(f"Qty {idx+1}", value=item["quantity"], min_value=1, key=f"qty_{idx}", label_visibility="collapsed")
        with col5:
            st.session_state.line_items[idx]["unit_price"] = st.number_input(f"Price {idx+1}", value=item["unit_price"], min_value=0.0, key=f"price_{idx}", label_visibility="collapsed")
        with col6:
            total = item["quantity"] * item["unit_price"]
            st.write(f"{total:.2f}")
    
    # Add new item button
    if st.button("➕ Add Item"):
        st.session_state.line_items.append({
            "company": "", 
            "product_category": "",
            "description": "", 
            "quantity": 1, 
            "unit_price": 0.0
        })
        st.rerun()
    
    # Remove item button
    if st.session_state.line_items and st.button("➖ Remove Last Item"):
        st.session_state.line_items.pop()
        st.rerun()
    
    # Display total
    if st.session_state.line_items:
        items_total = sum(item["quantity"] * item["unit_price"] for item in st.session_state.line_items)
        st.markdown(f"### **Items Subtotal: {items_total:.2f}**")
    else:
        st.info("No items added yet")

service_desc = st.text_area("Service Description")
services_amount = st.number_input("Services Amount", min_value=0.0)

# Display summary
st.markdown("---")
st.subheader("Invoice Summary")

col1, col2 = st.columns(2)

with col1:
    items_subtotal = sum(item["quantity"] * item["unit_price"] for item in st.session_state.get("line_items", [])) if st.session_state.get("line_items") else 0.0
    st.metric("Items Subtotal", f"{items_subtotal:.2f}")

with col2:
    st.metric("Services Amount", f"{services_amount:.2f}")

total_due = items_subtotal + services_amount
st.metric("Total Amount Due", f"{total_due:.2f}", delta=None)

if st.button("Generate Invoice"):
    if client_name and invoice_id:
        items_subtotal = sum(item["quantity"] * item["unit_price"] for item in st.session_state.get("line_items", [])) if st.session_state.get("line_items") else 0.0
        pdf_file = generate_invoice_pdf(client_name, service_desc, services_amount, invoice_id, st.session_state.line_items)
        with open(pdf_file, "rb") as f:
            st.download_button("📥 Download Invoice PDF", f, file_name=pdf_file, mime="application/pdf")
        total_due = items_subtotal + services_amount
        save_invoice(client_name, service_desc, total_due, invoice_id)
        st.success(f"Invoice {invoice_id} generated successfully!")
    else:
        st.error("Please fill in Client Name and Invoice ID.")

if st.button("Show Invoice History"):
    if os.path.exists(history_file):
        data = pd.read_csv(history_file)
        st.dataframe(data)
    else:
        st.warning("No invoice history found.")


