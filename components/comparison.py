import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.mortgage_math import (
    calculate_mortgage_costs,
    calculate_upfront_costs,
    monthly_payment
)
from config import DEFAULTS

def show_buy_vs_rent():
    """Display the buy vs rent comparison tab"""
    # Retrieve property and mortgage values from session state if available
    property_price = st.session_state.get('property_price', DEFAULTS["property_price"])
    down_payment_pct = st.session_state.get('down_payment_pct', DEFAULTS["down_payment_pct"])
    mortgage_years = st.session_state.get('mortgage_years', DEFAULTS["mortgage_years"])
    fixed_years = st.session_state.get('fixed_years', DEFAULTS["fixed_years"])
    fixed_rate = st.session_state.get('fixed_rate', DEFAULTS["fixed_rate"])
    eibor_rate = st.session_state.get('eibor_rate', DEFAULTS["eibor_rate"])
    built_up_area = st.session_state.get('built_up_area', DEFAULTS["built_up_area"])
    service_charge_rate = st.session_state.get('service_charge_rate', DEFAULTS["service_charge_rate"])
    bank_margin = st.session_state.get('bank_margin', DEFAULTS["bank_margin"])
    life_insurance_pct = st.session_state.get('life_insurance_pct', DEFAULTS["life_insurance_pct"])
    home_insurance_pct = st.session_state.get('home_insurance_pct', DEFAULTS["home_insurance_pct"])
    
    # Check for DLD and agent fee parameters from session state
    dld_fee_pct = st.session_state.get('dld_fee_pct', DEFAULTS.get("dld_fee_pct", 4.0))
    agent_fee_pct = st.session_state.get('agent_fee_pct', DEFAULTS.get("agent_fee_pct", 2.0))
    processing_fee_pct = st.session_state.get('processing_fee_pct', DEFAULTS["processing_fee_pct"])
    trustee_fee = st.session_state.get('trustee_fee', DEFAULTS["trustee_fee"])
    valuation_fee = st.session_state.get('valuation_fee', DEFAULTS["valuation_fee"])
    dewa_fee = st.session_state.get('dewa_fee', DEFAULTS["dewa_fee"])
    snagging_fee = st.session_state.get('snagging_fee', DEFAULTS["snagging_fee"])

    # Additional inputs for this tab
    st.subheader("📥 Rent vs Buy Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        monthly_rent = st.number_input(
            "Current Monthly Rent (AED)", 
            value=DEFAULTS["monthly_rent"],
            min_value=0
        )
        rent_growth = st.number_input(
            "Expected Annual Rent Increase (%)", 
            0.0, 15.0, 
            DEFAULTS["rent_growth"]
        )
    
    with col2:
        compare_years = st.number_input(
            "Years to Compare", 
            5, 25, 
            DEFAULTS["compare_years"]
        )
        appreciation_rate = st.number_input(
            "Expected Property Appreciation Rate (%)", 
            0.0, 15.0, 
            DEFAULTS["appreciation_rate"]
        )
    
    # Set default value for tax advantage (keep this if it's used elsewhere)
    tax_advantage = 0.0

    # Calculations for buy scenario
    down_payment = (down_payment_pct / 100) * property_price
    loan_amount = property_price - down_payment
    floating_rate = eibor_rate + bank_margin
    
    # Calculate mortgage details and costs using the mortgage_math utilities
    mortgage_costs = calculate_mortgage_costs(
        property_price, down_payment_pct, loan_amount,
        mortgage_years, fixed_years, fixed_rate, floating_rate,
        built_up_area, service_charge_rate,
        home_insurance_pct, life_insurance_pct  
    )
    
    upfront_cost = calculate_upfront_costs(
        property_price, loan_amount, down_payment,
        trustee_fee, valuation_fee, 
        dewa_fee, snagging_fee,
        processing_fee_pct, dld_fee_pct, agent_fee_pct
    )
    
    # Get monthly payment information
    monthly_fixed_payment = monthly_payment(loan_amount, fixed_rate, mortgage_years)
    monthly_floating_payment = monthly_payment(loan_amount, floating_rate, mortgage_years - fixed_years)
    
    # Calculate total amount actually spent on the property 
    # (upfront costs + mortgage payments + insurance + service charges)
    total_buying_cost = mortgage_costs["total_payment"] + upfront_cost

    # Calculate rent costs over time
    rent_total = 0
    current_rent = monthly_rent
    rent_over_time = []
    buy_costs_over_time = []
    buy_equity_over_time = []
    net_position_over_time = []
    
    # Initial values
    property_value = property_price
    remaining_loan = loan_amount
    equity = property_value - remaining_loan  # Initial equity is the down payment
    
    # Calculate annual home insurance based on property value (fixed for simplicity)
    annual_home_insurance = (home_insurance_pct / 100) * property_price
    
    # Tracking variables for cumulative costs
    cumulative_mortgage_payment = 0
    cumulative_service_charge = 0
    cumulative_insurance = 0
    
    for year in range(1, compare_years + 1):
        # Calculate property value with appreciation (compound annually)
        property_value = property_price * ((1 + appreciation_rate / 100) ** year)
        
        # Rent scenario
        annual_rent = current_rent * 12
        rent_total += annual_rent
        rent_over_time.append((year, rent_total))
        current_rent *= (1 + rent_growth / 100)  # Increase rent for next year
        
        # Buy scenario - calculate annual costs
        annual_buy_cost = 0
        
        # Mortgage payments
        if year <= mortgage_years:
            # Calculate mortgage payments and principal reduction
            if year <= fixed_years:
                annual_mortgage = monthly_fixed_payment * 12
            else:
                annual_mortgage = monthly_floating_payment * 12
            
            # Estimate principal reduction for this year
            if year <= fixed_years:
                monthly_rate = fixed_rate / 100 / 12
            else:
                monthly_rate = floating_rate / 100 / 12
                
            annual_interest = remaining_loan * monthly_rate * 12
            annual_principal = annual_mortgage - annual_interest
            
            # Apply tax advantage if any
            tax_savings = annual_interest * (tax_advantage / 100)
            annual_mortgage -= tax_savings
            
            remaining_loan = max(0, remaining_loan - annual_principal)
            
            # Add mortgage payment to annual cost
            annual_buy_cost += annual_mortgage
            cumulative_mortgage_payment += annual_mortgage
        else:
            # Mortgage is paid off
            remaining_loan = 0
        
        # Add service charge
        annual_buy_cost += mortgage_costs["annual_service_charge"]
        cumulative_service_charge += mortgage_costs["annual_service_charge"]
        
        # Add insurance costs
        annual_buy_cost += annual_home_insurance  # Home insurance
        cumulative_insurance += annual_home_insurance
        
        # Add life insurance (based on remaining loan)
        if remaining_loan > 0:
            annual_life_insurance = (life_insurance_pct / 100) * remaining_loan
            annual_buy_cost += annual_life_insurance
            cumulative_insurance += annual_life_insurance
            
        # Update cumulative buy cost (including upfront costs for total costs over time)
        total_annual_cost = annual_buy_cost
        if year == 1:
            total_annual_cost += upfront_cost
            
        buy_costs_over_time.append((year, total_annual_cost if year == 1 else 
                                   buy_costs_over_time[-1][1] + annual_buy_cost))
        
        # Calculate equity (property value minus remaining loan)
        equity = property_value - remaining_loan
        buy_equity_over_time.append((year, equity))
        
        # Calculate net position (equity minus costs)
        # We're including ALL costs here, including down payment
        net_position = equity - buy_costs_over_time[-1][1]
        net_position_over_time.append((year, net_position))

    # Create dataframes for plotting
    rent_df = pd.DataFrame(rent_over_time, columns=["Year", "Cumulative Rent"])
    buy_cost_df = pd.DataFrame(buy_costs_over_time, columns=["Year", "Cumulative Buy Cost"])
    buy_equity_df = pd.DataFrame(buy_equity_over_time, columns=["Year", "Property Equity"])
    net_position_df = pd.DataFrame(net_position_over_time, columns=["Year", "Net Position"])
    
    # Merge dataframes for comparison chart
    comparison_df = pd.merge(rent_df, buy_cost_df, on="Year")
    comparison_df = pd.merge(comparison_df, buy_equity_df, on="Year")
    comparison_df = pd.merge(comparison_df, net_position_df, on="Year")
    
    # Calculate buy vs rent advantage
    comparison_df["Buy vs Rent Advantage"] = comparison_df["Net Position"] - (-comparison_df["Cumulative Rent"])
    
    # Find break-even point (when buying becomes better than renting)
    break_even_year = None
    for index, row in comparison_df.iterrows():
        if row["Buy vs Rent Advantage"] > 0:
            break_even_year = row["Year"]
            break
    
    # If we never break even in our time frame
    if break_even_year is None:
        # Estimate break-even by extending analysis
        extended_year = compare_years
        extended_property_value = property_value
        extended_rent_total = rent_total
        current_rent = monthly_rent * ((1 + rent_growth / 100) ** compare_years)
        
        while extended_year < 100:  # Cap at 100 years
            extended_year += 1
            # Update property value
            extended_property_value *= (1 + appreciation_rate / 100)
            
            # Update rent
            annual_rent = current_rent * 12
            extended_rent_total += annual_rent
            current_rent *= (1 + rent_growth / 100)
            
            # Simple check (not accounting for ongoing costs which are small after mortgage payoff)
            if extended_property_value - buy_cost_df.iloc[-1]["Cumulative Buy Cost"] > extended_rent_total:
                break_even_year = extended_year
                break

    # Final position values
    final_rent_cost = rent_df.iloc[-1]["Cumulative Rent"]
    final_buy_cost = buy_cost_df.iloc[-1]["Cumulative Buy Cost"]
    final_property_value = buy_equity_df.iloc[-1]["Property Equity"]
    final_net_position = net_position_df.iloc[-1]["Net Position"]
    true_financial_outcome = final_property_value - total_buying_cost 

    # ----------------------------------------
    # 📊 High-Level Summary: Rent vs Buy
    # ----------------------------------------
    st.subheader("📊 : Renting vs Buying")

    col1, col2 = st.columns(2)

    # Determine if buying is financially better
    buy_better = final_net_position > -final_rent_cost

    # 🏠 Buying Summary
    with col1:
        st.markdown("### 🏠 Buying a Home")
        st.markdown(f"**Total Spent (including fees):** AED {total_buying_cost:,.2f}")
        st.markdown(f"**Estimated Property Value:** AED {final_property_value:,.2f}")
        
        # Calculate the actual financial gain/loss
        financial_outcome = final_net_position
        
        if financial_outcome > 0:
            st.markdown(f"**Final Financial Outcome:** 🟢 **AED {true_financial_outcome:,.2f} gain**")
        else:
            st.markdown(f"**Final Financial Outcome:** 🔴 AED {abs(true_financial_outcome):,.2f} loss")

    # 🏢 Renting Summary
    with col2:
        st.markdown("### 🏢 Renting a Home")
        st.markdown(f"**Total Rent Paid:** AED {final_rent_cost:,.2f}")
        st.markdown(f"**Assets Owned:** AED 0.00")
        
        if not buy_better:
    # If renting is financially better overall
            rent_advantage = abs(final_net_position) - final_rent_cost
            st.markdown(f"**Final Financial Outcome:** 🟢 **AED {rent_advantage:,.2f} saved compared to buying**")
        else:
            # Renting always results in money spent with no asset
            st.markdown(f"**Final Financial Outcome:** 🔴 AED {final_rent_cost:,.2f} spent with no asset acquired")

    # Show the financial advantage with highlighting
    st.markdown("---")
    if buy_better:
        advantage_amount = final_rent_cost - abs(true_financial_outcome)
        st.success(f"### 💰 You'll be **AED {advantage_amount:,.2f}** better off by BUYING after {compare_years} years")
        
        if break_even_year and break_even_year <= compare_years:
            st.info(f"💡 You'll break even at year {break_even_year} (when buying becomes better than renting)")
        else:
            st.warning(f"💡 You'll break even after the comparison period (not within {compare_years} years)")
    else:
        advantage_amount = final_rent_cost - abs(true_financial_outcome)
        st.error(f"### 💰 You'll be **AED {advantage_amount:,.2f}** better off by RENTING after {compare_years} years")
        
        if break_even_year:
            st.info(f"💡 Buying becomes financially better after year {break_even_year}")
        else:
            st.warning(f"💡 With current assumptions, buying may not become better within a reasonable timeframe")
            
    # Key insight box
    st.markdown("""
    > 💡 **Key insight:** While renting may seem cheaper in the short term, buying builds equity—an asset that grows over time—while rent payments provide temporary housing but no lasting value.
    """)

    # Display charts and results
    st.subheader("📈 Financial Comparison Over Time")
    
    chart_tabs = st.tabs(["Total Position", "Buy vs Rent Advantage", "Detailed Breakdown"])
    
    with chart_tabs[1]:
        # Create a more beautiful chart with Plotly
        fig = go.Figure()
        
        # Add rent line
        fig.add_trace(go.Scatter(
            x=comparison_df["Year"],
            y=-comparison_df["Cumulative Rent"],
            name="Renting Position",
            line=dict(color="red", width=3),
            hovertemplate="Year %{x}: AED %{y:,.2f}<extra>Renting Position</extra>"
        ))
        
        # Add buying position line
        fig.add_trace(go.Scatter(
            x=comparison_df["Year"],
            y=comparison_df["Net Position"],
            name="Buying Position",
            line=dict(color="green", width=3),
            hovertemplate="Year %{x}: AED %{y:,.2f}<extra>Buying Position</extra>"
        ))
        
        # Add a horizontal line at zero
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        
        # Add break-even point marker if it exists within our time frame
        if break_even_year and break_even_year <= compare_years:
            break_even_point = comparison_df[comparison_df["Year"] == break_even_year]
            fig.add_trace(
                go.Scatter(
                    x=[break_even_year],
                    y=[break_even_point["Net Position"].values[0]],
                    mode="markers",
                    marker=dict(size=12, color="gold", symbol="star"),
                    name="Break-even Point",
                    hovertemplate="Break-even at Year %{x}<extra></extra>"
                )
            )
            
            # Add annotation for break-even point
            fig.add_annotation(
                x=break_even_year,
                y=break_even_point["Net Position"].values[0],
                text=f"Break-even at Year {break_even_year}",
                showarrow=True,
                arrowhead=1
            )
        
        # Style the chart
        fig.update_layout(
            title="Total Financial Position: Buying vs Renting",
            xaxis_title="Year",
            yaxis_title="Financial Position (AED)",
            legend_title="Scenario",
            hovermode="x unified",
            plot_bgcolor="rgba(240, 240, 240, 0.8)",  # Light gray background
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with chart_tabs[2]:
        # Buy vs Rent Advantage chart
        advantage_fig = go.Figure()
        
        # Add advantage area
        advantage_fig.add_trace(go.Scatter(
            x=comparison_df["Year"],
            y=comparison_df["Buy vs Rent Advantage"],
            name="Buying Advantage",
            fill='tozeroy',
            line=dict(color="green" if buy_better else "red"),
            fillcolor="rgba(0, 255, 0, 0.2)" if buy_better else "rgba(255, 0, 0, 0.1)",
            hovertemplate="Year %{x}: AED %{y:,.2f}<extra>Buying Advantage</extra>"
        ))
        
        # Add a horizontal line at zero
        advantage_fig.add_hline(y=0, line_dash="dash", line_color="gray")
        
        # Style the chart
        advantage_fig.update_layout(
            title="Financial Advantage of Buying vs Renting",
            xaxis_title="Year",
            yaxis_title="Advantage Amount (AED)",
            hovermode="x unified",
            plot_bgcolor="rgba(240, 240, 240, 0.8)",  # Light gray background
            height=500
        )
        
        st.plotly_chart(advantage_fig, use_container_width=True)
    
    with chart_tabs[0]:
        # Detailed breakdown of all components
        detail_fig = go.Figure()
        
        # Property Equity
        detail_fig.add_trace(go.Scatter(
            x=comparison_df["Year"],
            y=comparison_df["Property Equity"],
            name="Property Equity",
            line=dict(color="green", width=3),
            hovertemplate="Year %{x}: AED %{y:,.2f}<extra>Property Equity</extra>"
        ))
        
        # Buying Costs
        detail_fig.add_trace(go.Scatter(
            x=comparison_df["Year"],
            y=-comparison_df["Cumulative Buy Cost"],
            name="Buying Costs",
            line=dict(color="red", width=2),
            hovertemplate="Year %{x}: AED %{y:,.2f}<extra>Buying Costs</extra>"
        ))
        
        # Rent
        detail_fig.add_trace(go.Scatter(
            x=comparison_df["Year"],
            y=-comparison_df["Cumulative Rent"],
            name="Rent Paid",
            line=dict(color="orange", width=2),
            hovertemplate="Year %{x}: AED %{y:,.2f}<extra>Rent Paid</extra>"
        ))

        # Add a horizontal line at zero
        detail_fig.add_hline(y=0, line_dash="dash", line_color="gray")
        
        # Style the chart
        detail_fig.update_layout(
            title="Detailed Financial Components",
            xaxis_title="Year",
            yaxis_title="Amount (AED)",
            legend_title="Component",
            hovermode="x unified",
            plot_bgcolor="rgba(240, 240, 240, 0.8)",  # Light gray background
            height=600
        )
        
        st.plotly_chart(detail_fig, use_container_width=True)

    
    st.subheader("📏 Key Factors")
    st.markdown("""
    ### 
    1. **Higher property appreciation** makes buying more attractive
    2. **Higher rent increases** favor buying more strongly
    3. **Longer time horizon** generally benefits buying (as mortgage gets paid off)
    4. **Lower interest rates** improve the buying scenario
    5. **Higher down payment** reduces mortgage costs but increases opportunity cost
    
    > **Remember:** While finances are important, there are non-financial benefits to both options. Owning provides stability and freedom to customize, while renting offers flexibility to relocate.
    """)
