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
    st.header("🏡 Buy vs Rent Comparison")
    
    # Retrieve property and mortgage values from session state if available
    property_price = st.session_state.get('property_price', DEFAULTS["property_price"])
    down_payment_pct = st.session_state.get('down_payment_pct', DEFAULTS["down_payment_pct"])
    mortgage_years = st.session_state.get('mortgage_years', DEFAULTS["mortgage_years"])
    fixed_years = st.session_state.get('fixed_years', DEFAULTS["fixed_years"])
    fixed_rate = st.session_state.get('fixed_rate', DEFAULTS["fixed_rate"])
    eibor_rate = st.session_state.get('eibor_rate', DEFAULTS["eibor_rate"])
    built_up_area = st.session_state.get('built_up_area', DEFAULTS["built_up_area"])
    service_charge_rate = st.session_state.get('service_charge_rate', DEFAULTS["service_charge_rate"])
    
    # Toggle advanced mode
    show_advanced = st.sidebar.checkbox("Show Advanced Options", value=False)
    
    # Additional inputs for this tab
    st.subheader("📥 Rent vs Buy Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        monthly_rent = st.number_input(
            "Current Monthly Rent (AED)", 
            value=DEFAULTS["monthly_rent"],
            min_value=0
        )
        rent_growth = st.slider(
            "Expected Annual Rent Increase (%)", 
            0.0, 15.0, 
            DEFAULTS["rent_growth"]
        )
    
    with col2:
        compare_years = st.slider(
            "Years to Compare", 
            10, 50, 
            DEFAULTS["compare_years"]
        )
        appreciation_rate = st.slider(
            "Expected Property Appreciation Rate (%)", 
            0.0, 15.0, 
            DEFAULTS["appreciation_rate"]
        )
    
    # Advanced options
    if show_advanced:
        st.subheader("🔍 Advanced Assumptions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Investment return rate (for opportunity cost of down payment)
            investment_return = st.slider(
                "Alternative Investment Return (%)", 
                0.0, 20.0, 
                5.0
            )
            
        with col2:
            # Property tax/maintenance not covered by service charge
            additional_ownership_costs = st.slider(
                "Additional Annual Ownership Costs (% of property value)", 
                0.0, 2.0, 
                0.5
            )
            
        with col3:
            # Tax advantages (in some countries mortgage interest is tax deductible)
            tax_advantage = st.slider(
                "Tax Advantage (% of mortgage interest)", 
                0.0, 100.0, 
                0.0
            )
            
        # Option to include opportunity cost of down payment
        include_opportunity_cost = st.checkbox("Include Opportunity Cost of Down Payment", value=False)
    else:
        # Set default values
        investment_return = 5.0
        additional_ownership_costs = 0.5
        tax_advantage = 0.0
        include_opportunity_cost = False

    # Calculations for buy scenario
    down_payment = (down_payment_pct / 100) * property_price
    loan_amount = property_price - down_payment
    floating_rate = eibor_rate + 1.5
    
    # Calculate ongoing insurance costs
    annual_home_insurance = (DEFAULTS["home_insurance_pct"] / 100) * property_price
    annual_life_insurance = (DEFAULTS["life_insurance_pct"] / 100) * loan_amount
    
    # Calculate mortgage details
    monthly_fixed_payment = monthly_payment(loan_amount, fixed_rate, mortgage_years)
    monthly_floating_payment = monthly_payment(loan_amount, floating_rate, mortgage_years - fixed_years)
    
    mortgage_costs = calculate_mortgage_costs(
        property_price, down_payment_pct, loan_amount,
        mortgage_years, fixed_years, fixed_rate, floating_rate,
        built_up_area, service_charge_rate
    )
    
    upfront_cost = calculate_upfront_costs(
        property_price, loan_amount, down_payment,
        DEFAULTS["trustee_fee"], DEFAULTS["valuation_fee"], 
        DEFAULTS["dewa_fee"], DEFAULTS["snagging_fee"],
        DEFAULTS["arrangement_fee_pct"], 
        DEFAULTS["home_insurance_pct"], 
        DEFAULTS["life_insurance_pct"]
    )

    # Calculate rent costs over time
    rent_total = 0
    current_rent = monthly_rent
    rent_over_time = []
    buy_costs_over_time = []
    buy_equity_over_time = []
    opportunity_cost_over_time = []
    net_position_over_time = []
    
    # Initial buy cost (down payment + fees, excluding the down payment itself 
    # which is part of equity calculation)
    buy_total = upfront_cost - down_payment  # Remove down payment from costs since it's an asset
    opportunity_cost = 0  # Track opportunity cost of down payment
    property_value = property_price
    remaining_loan = loan_amount
    equity = property_value - remaining_loan  # Initial equity is just the down payment
    
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
        else:
            # Mortgage is paid off
            remaining_loan = 0
        
        # Add service charge
        annual_buy_cost += mortgage_costs["annual_service_charge"]
        
        # Add insurance costs
        annual_buy_cost += annual_home_insurance
        if remaining_loan > 0:
            annual_buy_cost += annual_life_insurance
            
        # Add additional ownership costs
        annual_buy_cost += property_value * (additional_ownership_costs / 100)
        
        # Calculate opportunity cost of down payment
        if include_opportunity_cost:
            # Simple compound interest on down payment
            opportunity_cost = down_payment * ((1 + investment_return / 100) ** year - 1)
        else:
            opportunity_cost = 0
            
        # Update cumulative buy cost (excluding down payment)
        buy_total += annual_buy_cost
        buy_costs_over_time.append((year, buy_total))
        opportunity_cost_over_time.append((year, opportunity_cost))
        
        # Calculate equity (property value minus remaining loan)
        equity = property_value - remaining_loan
        buy_equity_over_time.append((year, equity))
        
        # Calculate net position (equity minus costs minus opportunity cost)
        net_position = equity - buy_total - opportunity_cost + down_payment  # Add back down payment
        net_position_over_time.append((year, net_position))

    # Create dataframes for plotting
    rent_df = pd.DataFrame(rent_over_time, columns=["Year", "Cumulative Rent"])
    buy_cost_df = pd.DataFrame(buy_costs_over_time, columns=["Year", "Cumulative Buy Cost"])
    buy_equity_df = pd.DataFrame(buy_equity_over_time, columns=["Year", "Property Equity"])
    opportunity_cost_df = pd.DataFrame(opportunity_cost_over_time, columns=["Year", "Opportunity Cost"])
    net_position_df = pd.DataFrame(net_position_over_time, columns=["Year", "Net Position"])
    
    # Merge dataframes for comparison chart
    comparison_df = pd.merge(rent_df, buy_cost_df, on="Year")
    comparison_df = pd.merge(comparison_df, buy_equity_df, on="Year")
    comparison_df = pd.merge(comparison_df, opportunity_cost_df, on="Year")
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
            if extended_property_value - buy_total > extended_rent_total:
                break_even_year = extended_year
                break

    # Final position
    final_rent_cost = rent_df.iloc[-1]["Cumulative Rent"]
    final_buy_cost = buy_cost_df.iloc[-1]["Cumulative Buy Cost"]
    final_property_value = buy_equity_df.iloc[-1]["Property Equity"]
    final_opportunity_cost = opportunity_cost_df.iloc[-1]["Opportunity Cost"]
    net_worth_buying = final_property_value - final_buy_cost - final_opportunity_cost

    # -------------------------------------------------------------
    # Side-by-side summary of rent vs buy at the top
    # -------------------------------------------------------------
    st.subheader("💹 Quick Comparison Summary")
    
    col1, col2 = st.columns(2)
    
    # Style based on which option is better
    # buy_better = net_worth_buying > final_rent_cost
    buy_better = net_worth_buying + final_rent_cost > 0
    
    with col1:
        st.markdown("### 🏠 Buying")
        st.markdown(f"**Total Outlay:** AED {(upfront_cost + final_buy_cost):,.2f}")
        st.markdown(f"**Property Value:** AED {final_property_value:,.2f}")
        
        if buy_better:
            st.markdown(f"**Net Position:** 🟢 **AED {net_worth_buying:,.2f}**")
        else:
            st.markdown(f"**Net Position:** AED {net_worth_buying:,.2f}")
    
    with col2:
        st.markdown("### 🏢 Renting")
        st.markdown(f"**Total Rent Paid:** AED {final_rent_cost:,.2f}")
        st.markdown("**Property Value:** AED 0")
        
        if not buy_better:
            st.markdown(f"**Net Position:** 🟢 **AED -{final_rent_cost:,.2f}**")
        else:
            st.markdown(f"**Net Position:** AED -{final_rent_cost:,.2f}")
    
    # Show the financial advantage with highlighting
    st.markdown("---")
    if buy_better:
        advantage_amount = net_worth_buying + final_rent_cost
        st.success(f"### 💰 You'll be **AED {advantage_amount:,.2f}** better off by BUYING after {compare_years} years")
        
        if break_even_year:
            st.info(f"💡 You'll break even at year {break_even_year} (when buying becomes better than renting)")
        else:
            st.warning(f"💡 You'll break even after the comparison period (estimated around year {break_even_year})")
    else:
        advantage_amount = final_rent_cost - net_worth_buying
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
    
    with chart_tabs[0]:
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
    
    with chart_tabs[1]:
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
    
    with chart_tabs[2]:
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
        
        # Opportunity Cost (if included)
        if include_opportunity_cost:
            detail_fig.add_trace(go.Scatter(
                x=comparison_df["Year"],
                y=-comparison_df["Opportunity Cost"],
                name="Opportunity Cost",
                line=dict(color="purple", width=2, dash="dash"),
                hovertemplate="Year %{x}: AED %{y:,.2f}<extra>Opportunity Cost</extra>"
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

    # Financial breakdown
    st.subheader("💸 Detailed Financial Breakdown")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🏠 Buying Details")
        st.write(f"**Upfront Costs:** AED {upfront_cost:,.2f}")
        st.write(f"**Total Mortgage & Expenses:** AED {final_buy_cost:,.2f}")
        if include_opportunity_cost:
            st.write(f"**Opportunity Cost of Down Payment:** AED {final_opportunity_cost:,.2f}")
        st.write(f"**Final Property Value:** AED {final_property_value:,.2f}")
        st.write(f"**Net Financial Position:** AED {net_worth_buying:,.2f}")
        
    with col2:
        st.markdown("### 🏢 Renting Details")
        st.write(f"**Starting Monthly Rent:** AED {monthly_rent:,.2f}")
        st.write(f"**Final Monthly Rent:** AED {monthly_rent * ((1 + rent_growth / 100) ** (compare_years - 1)):,.2f}")
        st.write(f"**Total Rent Paid:** AED {final_rent_cost:,.2f}")
        st.write(f"**Assets Acquired:** AED 0")
        st.write(f"**Net Financial Position:** AED -{final_rent_cost:,.2f}")
    
    # Sensitivity analysis
    st.subheader("📏 What Could Change This Outcome?")
    
    # Create sensitivity analysis for key parameters
    col1, col2 = st.columns(2)
    
    with col1:
        # Sensitivity to appreciation rate
        appreciation_sensitivity = []
        test_rates = [max(1.0, appreciation_rate - 3), appreciation_rate, appreciation_rate + 3]
        
        for test_rate in test_rates:
            test_property_value = property_price * ((1 + test_rate / 100) ** compare_years)
            test_net_worth = test_property_value - final_buy_cost - final_opportunity_cost
            test_advantage = test_net_worth + final_rent_cost
            
            appreciation_sensitivity.append({
                "Rate": f"{test_rate:.1f}%",
                "Advantage": test_advantage,
                "Better": "Buying" if test_advantage > 0 else "Renting"
            })
        
        sensitivity_df = pd.DataFrame(appreciation_sensitivity)
        
        # Plot sensitivity to appreciation
        fig = px.bar(
            sensitivity_df,
            x="Rate",
            y="Advantage",
            color="Better",
            title=f"Effect of Property Appreciation Rate",
            color_discrete_map={"Buying": "green", "Renting": "red"},
            labels={"Advantage": f"Buying Advantage (AED) after {compare_years} years", "Rate": "Property Appreciation Rate"}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Sensitivity to rent growth
        rent_sensitivity = []
        test_rates = [max(1.0, rent_growth - 3), rent_growth, rent_growth + 3]
        
        for test_rate in test_rates:
            # Recalculate rent total
            test_rent_total = 0
            test_current_rent = monthly_rent
            
            for year in range(1, compare_years + 1):
                test_rent_total += test_current_rent * 12
                test_current_rent *= (1 + test_rate / 100)
                
            test_advantage = net_worth_buying + test_rent_total
            
            rent_sensitivity.append({
                "Rate": f"{test_rate:.1f}%",
                "Advantage": test_advantage,
                "Better": "Buying" if test_advantage > 0 else "Renting"
            })
        
        rent_sensitivity_df = pd.DataFrame(rent_sensitivity)
        
        # Plot sensitivity to rent growth
        fig = px.bar(
            rent_sensitivity_df,
            x="Rate",
            y="Advantage",
            color="Better",
            title=f"Effect of Annual Rent Increase Rate",
            color_discrete_map={"Buying": "green", "Renting": "red"},
            labels={"Advantage": f"Buying Advantage (AED) after {compare_years} years", "Rate": "Rent Growth Rate"}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Key factors
    st.markdown("""
    ### 🔑 Key Factors That Could Change This Analysis
    
    1. **Higher property appreciation** makes buying more attractive
    2. **Higher rent increases** favor buying more strongly
    3. **Longer time horizon** generally benefits buying (as mortgage gets paid off)
    4. **Lower interest rates** improve the buying scenario
    5. **Higher down payment** reduces mortgage costs but increases opportunity cost
    
    > **Remember:** While finances are important, there are non-financial benefits to both options. Owning provides stability and freedom to customize, while renting offers flexibility to relocate.
    """)
