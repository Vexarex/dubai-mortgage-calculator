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
    
    # Create a sidebar for inputs
    with st.sidebar:
        st.header("📌 Input Details")
        
        # Property details
        st.subheader("Property Details")
        property_price = st.number_input(
            "Property Price (AED)", 
            value=DEFAULTS["property_price"], 
            step=10000,
            min_value=100000,
            key="property_price"  # Adding keys to enable session_state
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
        st.subheader("Mortgage Details")
        down_payment_pct = st.slider(
            "Down Payment (%)", 
            0, 100, 
            DEFAULTS["down_payment_pct"],
            key="down_payment_pct"
        )
        mortgage_years = st.slider(
            "Mortgage Term (years)", 
            5, 30, 
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
        eibor_rate = st.number_input(
            "Current EIBOR (%)", 
            value=DEFAULTS["eibor_rate"], 
            step=0.01,
            min_value=0.0,
            key="eibor_rate"
        )
        
        # Fees
        st.subheader("Fees & Insurance")
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
        arrangement_fee_pct = st.slider(
            "Mortgage Arrangement Fee (%)", 
            0.0, 2.0, 
            DEFAULTS["arrangement_fee_pct"],
            key="arrangement_fee_pct"
        )

    # Calculate mortgage details
    down_payment = (down_payment_pct / 100) * property_price
    loan_amount = property_price - down_payment
    floating_rate = eibor_rate + 1.5
    
    # Calculate costs
    mortgage_costs = calculate_mortgage_costs(
        property_price, down_payment_pct, loan_amount,
        mortgage_years, fixed_years, fixed_rate, floating_rate,
        built_up_area, service_charge_rate
    )
    
    upfront_cost = calculate_upfront_costs(
        property_price, loan_amount, down_payment,
        trustee_fee, valuation_fee, dewa_fee, snagging_fee,
        arrangement_fee_pct, home_insurance_pct, life_insurance_pct
    )

    # Display mortgage summary
    st.subheader("📋 Mortgage Summary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Loan Amount:** AED {loan_amount:,.2f}")
        st.write(f"**Down Payment:** AED {down_payment:,.2f}")
        st.write(f"**Upfront Cost (Fees & Insurance):** AED {upfront_cost:,.2f}")
        st.write(f"**Monthly Payment (Fixed):** AED {mortgage_costs['monthly_fixed']:,.2f}")
        st.write(f"**Monthly Payment (Floating):** AED {mortgage_costs['monthly_floating']:,.2f}")

    with col2:
        st.write(f"**Annual Service Charge:** AED {mortgage_costs['annual_service_charge']:,.2f}")
        st.write(f"**Total Service Charge:** AED {mortgage_costs['total_service_charge']:,.2f}")
        st.write(f"**Total Interest:** AED {mortgage_costs['total_interest']:,.2f}")
        st.write(f"**Total Paid:** AED {mortgage_costs['total_payment']:,.2f}")

    # Generate amortization schedule
    yearly_amort, monthly_amort = generate_amortization(
        loan_amount, fixed_years, mortgage_years, fixed_rate, floating_rate
    )
    yearly_amort["Cumulative Principal"] = yearly_amort["Principal"].cumsum()
    yearly_amort["Cumulative Interest"] = yearly_amort["Interest"].cumsum()

    # Display charts
    st.subheader("📊 Annual Breakdown")
    col1, col2 = st.columns(2)
    
    with col1:
        # Bar chart showing principal vs interest paid each year
        principal_interest_fig = px.bar(
            yearly_amort,
            x="Year",
            y=["Principal", "Interest"],
            title="Principal vs Interest Paid Each Year",
            labels={"value": "Amount (AED)", "variable": "Payment Type"}
        )
        st.plotly_chart(principal_interest_fig, use_container_width=True)
    
    with col2:
        # Line chart showing cumulative payments over time
        cumulative_fig = px.line(
            yearly_amort,
            x="Year",
            y=["Cumulative Principal", "Cumulative Interest"],
            title="Cumulative Payments Over Time",
            labels={"value": "Amount (AED)", "variable": "Payment Type"}
        )
        st.plotly_chart(cumulative_fig, use_container_width=True)

    # Show amortization table
    show_amortization = st.checkbox("Show full amortization schedule")
    if show_amortization:
        st.subheader("📑 Amortization Schedule")
        # Add year-month column for better readability
        monthly_amort["Period"] = monthly_amort["Year"].astype(str) + "-" + monthly_amort["Month"].astype(str).str.zfill(2)
        
        # Format the monetary columns
        for col in ["Payment", "Principal", "Interest", "Remaining Balance"]:
            monthly_amort[col] = monthly_amort[col].map("AED {:,.2f}".format)
            
        st.dataframe(
            monthly_amort[["Period", "Payment", "Principal", "Interest", "Remaining Balance"]],
            use_container_width=True
        )

    # Pie chart
    st.subheader("🥧 Mortgage Composition")
    pie_data = pd.DataFrame({
        "Component": ["Principal", "Interest", "Service Charges"],
        "Amount": [loan_amount, mortgage_costs["total_interest"], mortgage_costs["total_service_charge"]]
    })
    fig = px.pie(
        pie_data, 
        names="Component", 
        values="Amount", 
        title="Total Mortgage Repayment Composition",
        color_discrete_sequence=px.colors.sequential.Bluyl
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)