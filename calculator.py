import streamlit as st
# import plotly.graph_objects as go
# import pandas as pd
# from streamlit_extras.add_vertical_space import add_vertical_space
# import numpy_financial as npf
# import requests

# Define constants at the top of the file
DOWN_PAYMENT_RATIO = 0.2
INSURANCE_FIXED = 120
MANAGEMENT_FEE_RATE = 0.08
LOAN_TERM_YEARS = 30

# @st.cache_data(ttl=3600)  # Cache for 1 hour
# def get_current_mortgage_rate():
#     url = "https://api.stlouisfed.org/fred/series/observations?series_id=MORTGAGE30US&api_key=2ff2780e16de4ae8c876b130dc9981fe&file_type=json&limit=1&sort_order=desc"
#     response = requests.get(url)
#     data = response.json()
#     return float(data['observations'][0]['value']) / 100

@st.cache_data(ttl=604800)  # Cache for 1 week
def calculate_rent_to_own(house_price, closing_costs_rate, property_tax_rate, appreciation_rate):
    interest_rate = 0.035
    
    closing_costs = house_price * closing_costs_rate
    total_purchase_price = house_price + closing_costs
    
    # Calculate mortgage payment
    monthly_rate = interest_rate / 12
    num_payments = LOAN_TERM_YEARS * 12
    mortgage_payment = total_purchase_price * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
    
    monthly_interest = (total_purchase_price * interest_rate) / 12
    monthly_principal = mortgage_payment - monthly_interest
    monthly_insurance = INSURANCE_FIXED
    monthly_property_tax = (house_price * property_tax_rate) / 12
    monthly_management_fee = mortgage_payment * MANAGEMENT_FEE_RATE
    
    monthly_rent = mortgage_payment + monthly_insurance + monthly_property_tax + monthly_management_fee

    breakdown = {
        "Principal": monthly_principal,
        "Interest": monthly_interest,
        "Insurance": monthly_insurance,
        "Property Tax": monthly_property_tax,
        "Management Fee": monthly_management_fee
    }
    
    return house_price, monthly_rent, breakdown, interest_rate, LOAN_TERM_YEARS

def calculate_monthly_breakdown(house_price, interest_rate, loan_term_years, month):
    monthly_rate = interest_rate / 12
    num_payments = loan_term_years * 12
    monthly_payment = house_price * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
    
    remaining_balance = house_price * ((1 + monthly_rate)**num_payments - (1 + monthly_rate)**month) / ((1 + monthly_rate)**num_payments - 1)
    interest = remaining_balance * monthly_rate
    principal = monthly_payment - interest
    
    return principal, interest

def update_calculator(house_price, closing_costs_rate, property_tax_rate, appreciation_rate):
    house_price, monthly_rent, breakdown, interest_rate, loan_term_years = calculate_rent_to_own(house_price, closing_costs_rate, property_tax_rate, appreciation_rate)
    
    # Calculate loan amount
    loan_amount = house_price * (1 + closing_costs_rate)
    
    # Calculate principal and interest for the first month
    principal, interest = calculate_monthly_breakdown(loan_amount, interest_rate, loan_term_years, 1)
    
    # Update breakdown with new principal and interest values
    breakdown['Principal'] = principal
    breakdown['Interest'] = interest
    
    # Create pie chart
    # Commented out due to plotly dependency
    # labels = list(breakdown.keys())
    # values = list(breakdown.values())
    # fig = go.Figure(data=[go.Pie(
    #     labels=labels, 
    #     values=values, 
    #     hole=.5, 
    #     textinfo='label+value',
    #     texttemplate='%{label}<br>$%{value:,.2f}',
    #     name='',
    #     hoverinfo='none',
    #     textfont=dict(size=14)
    # )])
    # fig.update_layout(
    #     showlegend=False,
    #     autosize=True,
    #     margin=dict(l=0, r=0, t=0, b=0),
    #     title_text=''
    # )
    # fig.add_annotation(
    #     text=f"<b>${monthly_rent:,.2f}</b>/mo",
    #     x=0.5,
    #     y=0.5,
    #     font_size=24,
    #     showarrow=False,
    #     font=dict(color="black")
    # )
            
    return None, house_price, loan_amount, monthly_rent

def calculate_estimated_equity(house_price, appreciation_rate, years):
    future_value = house_price * (1 + appreciation_rate) ** years
    return future_value - house_price

@st.cache_data(ttl=604800)  # Cache for 1 week
def calculate_equity_breakdown(house_price, loan_amount, interest_rate, loan_term_years, appreciation_rate, years):
    # Calculate total principal paid
    total_principal = 0
    for month in range(1, years * 12 + 1):
        principal, _ = calculate_monthly_breakdown(loan_amount, interest_rate, loan_term_years, month)
        total_principal += principal
    
    # Calculate appreciation
    total_appreciation = calculate_estimated_equity(house_price, appreciation_rate, years)
    renter_share_appreciation = total_appreciation * 0.5
    
    return total_principal, renter_share_appreciation

# @st.cache_data(ttl=604800)  # Cache for 1 week
# def create_equity_pie_chart(total_principal, renter_share_appreciation):
#     # Commented out due to plotly dependency

@st.cache_data(ttl=604800)  # Cache for 1 week
def calculate_comparison_values(house_price, property_tax_rate, appreciation_rate, years, monthly_rent, total_equity, down_payment_ratio, price_to_rent_ratio, investment_return_rate):
    # current_mortgage_rate = get_current_mortgage_rate()
    current_mortgage_rate = 0.05  # Placeholder value
    traditional_loan = house_price * (1 - down_payment_ratio)
    # mortgage_payment = npf.pmt(current_mortgage_rate/12, LOAN_TERM_YEARS*12, -traditional_loan)
    mortgage_payment = 0  # Placeholder value
    monthly_insurance = INSURANCE_FIXED
    monthly_property_tax = (house_price * property_tax_rate) / 12
    traditional_payment = mortgage_payment + monthly_insurance + monthly_property_tax
    traditional_principal = sum(calculate_monthly_breakdown(traditional_loan, current_mortgage_rate, LOAN_TERM_YEARS, month)[0] for month in range(1, years*12+1))
    traditional_appreciation = calculate_estimated_equity(house_price, appreciation_rate, years)
    traditional_equity = traditional_principal + traditional_appreciation + house_price * down_payment_ratio

    rental_payment = house_price / (price_to_rent_ratio * 12)
    rental_equity = 0

    down_payment = house_price * down_payment_ratio

    rent_to_own_spent = monthly_rent * years * 12
    traditional_spent = traditional_payment * years * 12 + down_payment
    renting_spent = rental_payment * years * 12

    traditional_opportunity_cost = down_payment * ((1 + investment_return_rate) ** years - 1)
    rent_to_own_opportunity_cost = 0
    renting_opportunity_cost = 0

    rent_to_own_cost = rent_to_own_spent - total_equity + rent_to_own_opportunity_cost
    traditional_cost = traditional_spent - traditional_equity + traditional_opportunity_cost
    renting_cost = renting_spent - rental_equity + renting_opportunity_cost

    return {
        'current_mortgage_rate': current_mortgage_rate,
        'traditional_payment': traditional_payment,
        'traditional_equity': traditional_equity,
        'rental_payment': rental_payment,
        'down_payment': down_payment,
        'rent_to_own_spent': rent_to_own_spent,
        'traditional_spent': traditional_spent,
        'renting_spent': renting_spent,
        'rent_to_own_cost': rent_to_own_cost,
        'traditional_cost': traditional_cost,
        'renting_cost': renting_cost,
        'price_to_rent_ratio': price_to_rent_ratio
    }

# Sidebar inputs
with st.sidebar:
    st.markdown("#### Advanced Settings")
    st.write("These settings are optional and can be adjusted to see how they impact the results.")
    # Advanced settings in an expandable section
    with st.expander("Advanced Settings"):
        appreciation_rate = st.number_input("Annual Appreciation Rate (%)", min_value=0.0, max_value=10.0, value=3.5, step=0.1) / 100
        closing_costs_rate = st.number_input("Closing Costs (%)", min_value=0.0, max_value=10.0, value=3.0, step=0.1) / 100
        property_tax_rate = st.number_input("Property Tax Rate (%)", min_value=0.0, max_value=5.0, value=1.122, step=0.001) / 100
        investment_return_rate = st.number_input("Investment Return Rate (%)", min_value=0.0, max_value=20.0, value=5.0, step=0.1, help="The rate of return you expect to earn in an investment account. This is used to calculate the opportunity cost of the down payment if you were to invest it instead of using it for a traditional mortgage.") / 100
        price_to_rent_ratio = st.number_input("Price-to-Rent Ratio", min_value=1.0, max_value=50.0, value=19.0, step=0.1, help="The ratio of the price of the home to the rent of a similar home. This is used to calculate the monthly rent of an equivalent home for comparison purposes.")

# Set up the main title and description
st.title("Rent-to-Own Calculator")
st.write("This tool enables you to determine the equity you will own in your home over time, calculate monthly mortgage payments, and gives a great comparison between buying and renting a place.")

# Basic price input
house_price = st.number_input("Enter the price of the home you are considering:", min_value=0.0, step=5000.0, value=400000.0, format="%.0f")

# add_vertical_space(1)

# Main area calculations and displays
if house_price:
    # Calculate and display monthly rent breakdown
    fig, house_price, loan_amount, monthly_rent = update_calculator(house_price, closing_costs_rate, property_tax_rate, appreciation_rate)

    st.subheader(f"Your monthly rent would be :blue[${monthly_rent:,.2f}].")
    st.write("Unlike typical rent, rent to own applies a portion of your rent towards the purchase of the home. The rest is used to pay for the loan, property taxes, insurance, and maintenance.")

    # add_vertical_space(2)
    # st.plotly_chart(fig, use_container_width=True)

    # add_vertical_space(3)
    st.divider()
    # add_vertical_space(1)

    # Equity calculation section
    st.header("How much equity can you build in your home over time?")
    st.write("In addition to a portion of your rent going towards the purchase of the home, you will also share in 50% of the appreciation of the home as it goes up in value.")

    # add_vertical_space(1)

    # User input for years of renting
    years = st.slider("Select the number of years you plan to rent the home.", min_value=1, max_value=7, value=4, step=1)

    # Calculate and display equity breakdown
    total_principal, renter_share_appreciation = calculate_equity_breakdown(house_price, loan_amount, 0.035, LOAN_TERM_YEARS, appreciation_rate, years)
    # equity_fig = create_equity_pie_chart(total_principal, renter_share_appreciation)

    total_equity = total_principal + renter_share_appreciation
    st.subheader(f"You would build an estimated :blue[${total_equity:,.2f}] in equity.")
    st.write("This is assuming a 3.5% annual appreciation, which will depend on the local market.")

    # add_vertical_space(1)
    # st.plotly_chart(equity_fig, use_container_width=True)
    # add_vertical_space(1)

    # Comparison of different scenarios
    st.markdown(f"#### What's the total cost of each scenario after :blue[{years}] years?")
    
    # Calculate comparison values
    comparison_values = calculate_comparison_values(
        house_price, 
        property_tax_rate, 
        appreciation_rate, 
        years, 
        monthly_rent, 
        total_equity, 
        DOWN_PAYMENT_RATIO, 
        price_to_rent_ratio, 
        investment_return_rate
    )

    # Prepare comparison data for display
    comparison_data = {
        "": ["Initial purchase price", "Down payment", "Interest rate", "Appreciation share", "Monthly payment", 
                f"Total equity ({years} years)", f"Total spent ({years} years)", 
                "Down payment opportunity cost", "Total true cost"],
        "Rent to Own": [f"${house_price:,.0f}", "$0", f"{0.035:.1%}", "50%", f"${monthly_rent:,.0f}", 
                        f"${total_equity:,.0f}", f"${comparison_values['rent_to_own_spent']:,.0f}", 
                        "$0", f"${comparison_values['rent_to_own_cost']:,.0f}"],
        "Traditional Mortgage": [f"${house_price:,.0f}", f"${comparison_values['down_payment']:,.0f}", f"{comparison_values['current_mortgage_rate']:.2%}", "100%", 
                                    f"${comparison_values['traditional_payment']:,.0f}", f"${comparison_values['traditional_equity']:,.0f}", f"${comparison_values['traditional_spent']:,.0f}", 
                                    f"${comparison_values['traditional_cost'] - comparison_values['traditional_spent'] + comparison_values['traditional_equity']:,.0f}", f"${comparison_values['traditional_cost']:,.0f}"],
        "Renting": ["$0", "$0", "", "0%", f"${comparison_values['rental_payment']:,.0f}", 
                    "$0", f"${comparison_values['renting_spent']:,.0f}", 
                    "$0", f"${comparison_values['renting_cost']:,.0f}"]
    }

    # Display total cost metrics for each scenario
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Rent to Own Cost", f"${comparison_values['rent_to_own_cost']:,.0f}")
    with col2:
        st.metric("Traditional Mortgage Cost", f"${comparison_values['traditional_cost']:,.0f}")
    with col3:
        st.metric("Renting Cost", f"${comparison_values['renting_cost']:,.0f}")

    # Create DataFrame for detailed comparison
    # df = pd.DataFrame(comparison_data)
    
    # Define column configuration for better display
    # column_config = {
    #     "Metric": st.column_config.TextColumn("Metric", width="medium"),
    #     "Rent to Own": st.column_config.NumberColumn("Rent to Own", width="small"),
    #     "Traditional Mortgage": st.column_config.NumberColumn("Traditional Mortgage", width="small"),
    #     "Renting": st.column_config.NumberColumn("Renting", width="small")
    # }

    # Display detailed comparison table in an expandable section
    with st.expander("🔍 See the full comparison table"):
        # st.dataframe(
        #     df.style.set_properties(**{'text-align': 'right'}, subset=df.columns[1:]),
        #     column_config=column_config,
        #     hide_index=True,
        #     use_container_width=True
        # )
        st.write("Detailed comparison table is currently unavailable.")
    
    # Add caption explaining assumptions
    st.caption(f"This looks at all the money you'll be spending on a house minus your gained equity and appreciation. We're assuming a mortgage rate of {comparison_values['current_mortgage_rate']:.2%}, an average appreciation rate of {appreciation_rate:.1%}, a {property_tax_rate:.2%} annual property tax rate, a {DOWN_PAYMENT_RATIO:.0%} down payment, and a price-to-rent ratio of {price_to_rent_ratio}.")
