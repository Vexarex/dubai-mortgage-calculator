import pandas as pd

def monthly_payment(principal, annual_rate, years):
    """Calculate monthly mortgage payment"""
    monthly_rate = annual_rate / 100 / 12
    months = years * 12
    if monthly_rate == 0:
        return principal / months
    return (principal * monthly_rate) / (1 - (1 + monthly_rate) ** -months)

def generate_amortization(loan, fixed_years, mortgage_years, fixed_rate, floating_rate):
    """Generate amortization schedule with fixed and floating periods"""
    total_months = mortgage_years * 12
    fixed_months = fixed_years * 12
    floating_months = total_months - fixed_months
    monthly_fixed = monthly_payment(loan, fixed_rate, mortgage_years)
    balance = loan
    data = []

    # Fixed period
    for month in range(1, fixed_months + 1):
        year = (month - 1) // 12 + 1
        monthly_rate = fixed_rate / 100 / 12
        interest = balance * monthly_rate
        principal = monthly_fixed - interest
        balance -= principal
        data.append([year, month, monthly_fixed, principal, interest, balance])

    # Floating period
    monthly_floating = monthly_payment(balance, floating_rate, floating_months / 12)
    for month in range(fixed_months + 1, total_months + 1):
        year = (month - 1) // 12 + 1
        monthly_rate = floating_rate / 100 / 12
        interest = balance * monthly_rate
        principal = monthly_floating - interest
        if balance - principal < 0:
            principal = balance
            monthly_floating = principal + interest
        balance -= principal
        data.append([year, month, monthly_floating, principal, interest, balance])
        if balance <= 0:
            break

    df = pd.DataFrame(data, columns=["Year", "Month", "Payment", "Principal", "Interest", "Remaining Balance"])
    yearly = df.groupby("Year")[["Principal", "Interest"]].sum().reset_index()
    return yearly, df

def calculate_mortgage_costs(property_price, down_payment_pct, loan_amount, 
                           mortgage_years, fixed_years, fixed_rate, floating_rate,
                           built_up_area, service_charge_rate):
    """Calculate all mortgage related costs"""
    monthly_fixed = monthly_payment(loan_amount, fixed_rate, mortgage_years)
    monthly_floating = monthly_payment(loan_amount, floating_rate, mortgage_years - fixed_years)
    
    annual_service_charge = built_up_area * service_charge_rate
    total_service_charge = annual_service_charge * mortgage_years
    
    total_fixed = monthly_fixed * fixed_years * 12
    total_floating = monthly_floating * (mortgage_years - fixed_years) * 12
    total_payment = total_fixed + total_floating
    total_interest = total_payment - loan_amount
    
    return {
        "monthly_fixed": monthly_fixed,
        "monthly_floating": monthly_floating,
        "annual_service_charge": annual_service_charge,
        "total_service_charge": total_service_charge,
        "total_payment": total_payment,
        "total_interest": total_interest
    }

def calculate_upfront_costs(property_price, loan_amount, down_payment, 
                          trustee_fee, valuation_fee, dewa_fee, snagging_fee,
                          arrangement_fee_pct, home_insurance_pct, life_insurance_pct):
    """Calculate all upfront costs for buying property"""
    dld_fee = 0.04 * property_price
    agent_fee = 0.02 * property_price
    mortgage_registration_fee = 0.0025 * loan_amount
    arrangement_fee = (arrangement_fee_pct / 100) * loan_amount * 1.05
    home_insurance = (home_insurance_pct / 100) * property_price
    life_insurance = (life_insurance_pct / 100) * loan_amount
    
    upfront_cost = sum([
        down_payment, dld_fee, trustee_fee, agent_fee,
        valuation_fee, dewa_fee, snagging_fee,
        mortgage_registration_fee, arrangement_fee,
        home_insurance, life_insurance
    ])
    
    return upfront_cost