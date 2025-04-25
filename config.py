# Default values for mortgage calculator

DEFAULTS = {
    # Property details
    "property_price": 2000000,
    "built_up_area": 1500,
    "service_charge_rate": 15.0,
    
    # Mortgage details
    "down_payment_pct": 20,
    "mortgage_years": 25,
    "fixed_years": 3,
    "fixed_rate": 3.99,
    "eibor_rate": 3.5,
    
    # Fees
    "trustee_fee": 4200,
    "valuation_fee": 3000,
    "dewa_fee": 2000,
    "snagging_fee": 1000,
    "home_insurance_pct": 0.2,
    "life_insurance_pct": 0.5,
    "arrangement_fee_pct": 1.0,
    
    # Rent comparison
    "monthly_rent": 8000,
    "rent_growth": 5.0,
    "compare_years": 20,
    "appreciation_rate": 3.0
}