import streamlit as st
import pandas as pd
import plotly.express as px
from utils.mortgage_math import (
    monthly_payment, 
    generate_amortization,
    calculate_mortgage_costs,
    calculate_upfront_costs
)
from config import DEFAULTS

def show_mortgage_calculator():
    """Display the mortgage calculator tab"""
    st.header("📊 Mortgage Calculator")

    # --- Sidebar for inputs ---
    with st.sidebar:
        st.header("📌 Input Details")

        # Property details
        st.subheader("🏠 Property Details")
        property_price = st.number_input(
            "Property Price (AED)", 
            value=DEFAULTS["property_price"], 
            step=10000,
            min_value=100000,
            key="property_price"
        )
        built_up_area = st.number_input(
            "Built-up Area (sq ft)", 
            value=DEFAULTS["built_up_area"], 
            step=50,
            min_value=100,
            key="built_up_area"
        )
        service_charge_rate = st.number_input(
            "Service Charge Rate (AED/sq ft/year)", 
            value=DEFAULTS["service_charge_rate"], 
            step=0.1,
            min_value=0.0,
            key="service_charge_rate"
        )

        # Mortgage details
        st.subheader("💰 Mortgage Details")
        down_payment_pct = st.slider(
            "Down Payment (%)", 
            0, 100, 
            DEFAULTS["down_payment_pct"],
            key="down_payment_pct"
        )
        mortgage_years = st.slider(
            "Mortgage Term (years)", 
            5, 25, 
            DEFAULTS["mortgage_years"],
            key="mortgage_years"
        )
        fixed_years = st.slider(
            "Fixed Rate Duration (years)", 
            1, min(10, mortgage_years), 
            DEFAULTS["fixed_years"],
            key="fixed_years"
        )
        fixed_rate = st.number_input(
            "Fixed Interest Rate (%)", 
            value=DEFAULTS["fixed_rate"], 
            step=0.01,
            min_value=0.0,
            key="fixed_rate"
        )
        bank_margin = st.number_input(
            "Bank Margin over EIBOR (%)",
            value=DEFAULTS.get("bank_margin", 1.5),
            step=0.1,
            min_value=0.0,
            key="bank_margin"
        )
        eibor_rate = st.number_input(
            "Current EIBOR (%)", 
            value=DEFAULTS["eibor_rate"], 
            step=0.01,
            min_value=0.0,
            key="eibor_rate"
        )

        # Fees
        st.subheader("🧾 Fees & Insurance")
        dld_fee_pct = st.number_input(
            "Dubai Land Department Fee (%)",
            value=DEFAULTS.get("dld_fee_pct", 4.0),
            step=0.1,
            min_value=0.0,
            key="dld_fee_pct"
        )
        agent_fee_pct = st.number_input(
            "Agent Fee (%)",
            value=DEFAULTS.get("agent_fee_pct", 2.0),
            step=0.1,
            min_value=0.0,
            key="agent_fee_pct"
        )
        trustee_fee = st.number_input(
            "Trustee Fee (AED)", 
            value=DEFAULTS["trustee_fee"],
            key="trustee_fee"
        )
        valuation_fee = st.number_input(
            "Bank Valuation Fee (AED)", 
            value=DEFAULTS["valuation_fee"],
            key="valuation_fee"
        )
        dewa_fee = st.number_input(
            "DEWA Connection Fee (AED)", 
            value=DEFAULTS["dewa_fee"],
            key="dewa_fee"
        )
        snagging_fee = st.number_input(
            "Snagging Inspection Fee (AED)", 
            value=DEFAULTS["snagging_fee"],
            key="snagging_fee"
        )
        home_insurance_pct = st.slider(
            "Home Insurance (% annually)", 
            0.0, 1.0, 
            DEFAULTS["home_insurance_pct"],
            key="home_insurance_pct"
        )
        life_insurance_pct = st.slider(
            "Life Insurance (% annually)", 
            0.0, 1.0, 
            DEFAULTS["life_insurance_pct"],
            key="life_insurance_pct"
        )
        processing_fee_pct = st.slider(
            "Mortgage Processing Fee (%)", 
            0.0, 2.0, 
            DEFAULTS["processing_fee_pct"],
            key="processing_fee_pct"
        )

    # --- Calculations ---
    down_payment = (down_payment_pct / 100) * property_price
    loan_amount = property_price - down_payment
    loan_pct = 100 - down_payment_pct
    floating_rate = eibor_rate + bank_margin

    mortgage_costs = calculate_mortgage_costs(
        property_price, down_payment_pct, loan_amount,
        mortgage_years, fixed_years, fixed_rate, floating_rate,
        built_up_area, service_charge_rate,
        home_insurance_pct, life_insurance_pct
    )

    upfront_cost = calculate_upfront_costs(
        property_price, loan_amount, down_payment,
        trustee_fee, valuation_fee, dewa_fee, snagging_fee,
        processing_fee_pct, dld_fee_pct, agent_fee_pct
    )

    # --- Compute grand total ---
    grand_total = mortgage_costs['total_payment'] + upfront_cost

    # --- Summary ---
    summary_rows = [
        ("Property Price", f"AED {property_price:,.2f}", "Total property value"),
        ("Loan Amount (Principal)", f"AED {loan_amount:,.2f}", f"Loan principal after {loan_pct}% financing"),
        ("Down Payment", f"AED {down_payment:,.2f}", f"Initial {down_payment_pct}% payment"),
        ("Upfront Costs", f"AED {upfront_cost:,.2f}", "Down Payment + Fees + Registration costs"),
        ("Monthly Payment (Fixed)", f"AED {mortgage_costs['monthly_fixed']:,.2f}", f"Monthly during fixed rate period ({fixed_years} years)"),
        ("Monthly Payment (Floating)", f"AED {mortgage_costs['monthly_floating']:,.2f}", f"Estimated floating payment (EIBOR {eibor_rate}% + {bank_margin}%)"),
        ("Monthly Service Charge", f"AED {mortgage_costs['annual_service_charge'] / 12:,.2f}", "Service charge paid monthly"),
        # ("Total Principal", f"AED {loan_amount:,.2f}", "Loan amount to be repaid"),
        ("Total Interest", f"AED {mortgage_costs['total_interest']:,.2f}", "Full interest paid over life of loan"),
        ("Total Service Charge", f"AED {mortgage_costs['total_service_charge']:,.2f}", "Full period service charges"),
        ("Total Home Insurance", f"AED {mortgage_costs['total_home_insurance']:,.2f}", "Home insurance over mortgage period"),
        ("Total Life Insurance", f"AED {mortgage_costs['total_life_insurance']:,.2f}", "Decreasing life insurance over mortgage period"),
        ("Total Mortgage Cost", f"AED {mortgage_costs['total_payment']:,.2f}", "Principal + Interest + Charges + Insurance"),
        ("Grand Total (All Costs)", f"AED {grand_total:,.2f}", "Total cost including upfront costs")
    ]

    # --- HTML Table ---
    info_icon = "<span style='cursor:help; color:#888;' title='{tooltip}'> ℹ️</span>"
    table_html = "<table style='width:100%; border-collapse:collapse;'>"
    table_html += "<thead><tr><th style='text-align:left;'>Description</th><th style='text-align:right;'>Amount (AED)</th></tr></thead><tbody>"

    for desc, amount, tooltip in summary_rows:
        icon = info_icon.format(tooltip=tooltip)
        table_html += f"<tr><td style='padding:8px;'>{desc} {icon}</td><td style='padding:8px; text-align:right;'>{amount}</td></tr>"

    table_html += "</tbody></table>"

    # --- Layout ---
    st.subheader("📋 Mortgage Summary")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(table_html, unsafe_allow_html=True)

    with col2:
        # Improved pie chart with all costs
        pie_data = pd.DataFrame({
            "Component": ["Principal", "Interest", "Service Charges", "Home Insurance", "Life Insurance", "Upfront Costs"],
            "Amount": [
                loan_amount, 
                mortgage_costs["total_interest"], 
                mortgage_costs["total_service_charge"],
                mortgage_costs["total_home_insurance"],
                mortgage_costs["total_life_insurance"],
                upfront_cost
            ]
        })
        fig = px.pie(
            pie_data, 
            names="Component", 
            values="Amount",
            title="Total Cost Breakdown",
            hole=0.4
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

    # --- Annual Breakdown ---
    st.subheader("📊 Annual Breakdown")
    yearly_amort, monthly_amort = generate_amortization(
        loan_amount, fixed_years, mortgage_years, fixed_rate, floating_rate
    )

    yearly_amort["Cumulative Principal"] = yearly_amort["Principal"].cumsum()
    yearly_amort["Cumulative Interest"] = yearly_amort["Interest"].cumsum()

    col3, col4 = st.columns(2)

    with col3:
        principal_interest_fig = px.bar(
            yearly_amort,
            x="Year",
            y=["Principal", "Interest"],
            title="Principal vs Interest Paid Each Year",
            labels={"value": "Amount (AED)", "variable": "Type"}
        )
        st.plotly_chart(principal_interest_fig, use_container_width=True)

    with col4:
        cumulative_fig = px.line(
            yearly_amort,
            x="Year",
            y=["Cumulative Principal", "Cumulative Interest"],
            title="Cumulative Payments Over Time",
            labels={"value": "Cumulative Amount (AED)", "variable": "Type"}
        )
        st.plotly_chart(cumulative_fig, use_container_width=True)

    # --- Amortization Table ---
    st.subheader("📑 Full Amortization Schedule")
    monthly_amort["Period"] = monthly_amort["Year"].astype(str) + "-" + monthly_amort["Month"].astype(str).str.zfill(2)
    
    # Add insurance columns to the display
    monthly_amort["Home Insurance"] = monthly_amort.apply(
        lambda row: property_price * (home_insurance_pct / 100) / 12, axis=1
    )
    monthly_amort["Life Insurance"] = monthly_amort.apply(
        lambda row: row["Remaining Balance"] * (life_insurance_pct / 100) / 12, axis=1
    )
    monthly_amort["Service Charge"] = mortgage_costs["annual_service_charge"] / 12
    
    # Format for display
    for col in ["Payment", "Principal", "Interest", "Remaining Balance", "Home Insurance", "Life Insurance", "Service Charge"]:
        monthly_amort[col] = monthly_amort[col].map(lambda x: f"AED {x:,.2f}")

    st.dataframe(
        monthly_amort[["Period", "Payment", "Principal", "Interest", "Remaining Balance", "Home Insurance", "Life Insurance", "Service Charge"]],
        use_container_width=True
    )
