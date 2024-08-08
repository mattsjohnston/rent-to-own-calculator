import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from streamlit_extras.add_vertical_space import add_vertical_space
from streamlit_extras.row import row
import numpy_financial as npf
import requests

# Define constants at the top of the file
DOWN_PAYMENT_RATIO = 0.0
INSURANCE_FIXED = 150
MANAGEMENT_FEE_RATE = 0.08
LOAN_TERM_YEARS = 30
DEFAULT_YEARS = 4  # New constant for default years

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_current_mortgage_rate():
    url = "https://api.stlouisfed.org/fred/series/observations?series_id=MORTGAGE30US&api_key=2ff2780e16de4ae8c876b130dc9981fe&file_type=json&limit=1&sort_order=desc"
    response = requests.get(url)
    data = response.json()
    return float(data['observations'][0]['value']) / 100

@st.cache_data(ttl=604800)  # Cache for 1 week
def calculate_rent_to_own(house_price, closing_costs_rate, property_tax_rate, appreciation_rate, insurance_cost):
    interest_rate = 0.035
    
    closing_costs = house_price * closing_costs_rate
    total_purchase_price = house_price + closing_costs
    
    # Calculate mortgage payment
    monthly_rate = interest_rate / 12
    num_payments = LOAN_TERM_YEARS * 12
    mortgage_payment = total_purchase_price * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
    
    monthly_interest = (total_purchase_price * interest_rate) / 12
    monthly_principal = mortgage_payment - monthly_interest
    monthly_insurance = insurance_cost
    monthly_property_tax = (house_price * property_tax_rate) / 12
    monthly_management_fee = MANAGEMENT_FEE_RATE * (mortgage_payment + monthly_property_tax + monthly_insurance)
    
    monthly_rent = mortgage_payment + monthly_insurance + monthly_property_tax + monthly_management_fee

    breakdown = {
        "Principal": monthly_principal,
        "Interest": monthly_interest,
        "Insurance": monthly_insurance,
        "Property Tax": monthly_property_tax,
        "Management Fee": monthly_management_fee
    }
    
    return house_price, monthly_rent, breakdown, interest_rate, LOAN_TERM_YEARS

def calculate_monthly_breakdown(loan_amount, interest_rate, loan_term_years, month):
    monthly_rate = interest_rate / 12
    num_payments = loan_term_years * 12
    
    # Calculate the monthly payment using numpy financial
    monthly_payment = -npf.pmt(monthly_rate, num_payments, loan_amount)
    
    # Calculate the remaining balance
    remaining_balance = npf.fv(monthly_rate, month - 1, monthly_payment, -loan_amount)
    
    # Calculate interest and principal for the specific month
    interest = remaining_balance * monthly_rate
    principal = monthly_payment - interest
    
    return principal, interest

def update_calculator(house_price, closing_costs_rate, property_tax_rate, appreciation_rate, years, insurance_cost):
    house_price, monthly_rent, breakdown, interest_rate, loan_term_years = calculate_rent_to_own(house_price, closing_costs_rate, property_tax_rate, appreciation_rate, insurance_cost)
    
    # Calculate loan amount
    loan_amount = house_price * (1 + closing_costs_rate)
    
    # Calculate average principal and interest over the specified years
    total_principal = 0
    total_interest = 0
    for month in range(1, years * 12 + 1):
        principal, interest = calculate_monthly_breakdown(loan_amount, interest_rate, loan_term_years, month)
        total_principal += principal
        total_interest += interest
    
    avg_principal = total_principal / (years * 12)
    avg_interest = total_interest / (years * 12)
    
    # Update breakdown with new average principal and interest values
    breakdown['Principal'] = avg_principal
    breakdown['Interest'] = avg_interest
    
    # Create pie chart
    labels = list(breakdown.keys())
    values = list(breakdown.values())
    
    # Define custom colors
    custom_colors = ['#0068C9', '#83C5BE', '#EDF6F9', '#FFDDD2', '#E29578']

    hover_text = [
        "Monthly amount going towards paying off the loan principal.<br>If you decide to buy the house, this amount will be credited towards your purchase.",
        "Monthly financing cost, calculated based on a 3.5% annual rate.<br>This represents the cost of the rent-to-own arrangement.",
        "Monthly homeowner's insurance cost",
        "Monthly property tax based on the home's value",
        "Monthly fee for property management services"
    ]

    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values, 
        hole=.5, 
        textinfo='label+value',
        texttemplate='%{label}<br>$%{value:,.2f}',
        hovertext=hover_text,
        hoverinfo='text',
        hoverlabel_align='left',
        textfont=dict(size=14),
        marker=dict(colors=custom_colors)  # Add this line to use custom colors
    )])
    fig.update_layout(
        showlegend=False,
        autosize=True,
        margin=dict(l=0, r=0, t=0, b=0),
        title_text=''
    )

    # Add total monthly rent to the center of the pie chart
    fig.add_annotation(
        text=f"<b>${monthly_rent:,.2f}</b>/mo",  # Updated format
        x=0.5,
        y=0.5,
        font_size=24,
        showarrow=False,
        font=dict(color="black")
    )
            
    return fig, house_price, loan_amount, monthly_rent

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

def calculate_equity_over_time(house_price, loan_amount, interest_rate, loan_term_years, appreciation_rate, years):
    principal_over_time = []
    appreciation_over_time = []
    total_principal = 0
    for month in range(1, years * 12 + 1):
        principal, _ = calculate_monthly_breakdown(loan_amount, interest_rate, loan_term_years, month)
        total_principal += principal
        principal_over_time.append(total_principal)
        
        current_year = month / 12
        appreciation = calculate_estimated_equity(house_price, appreciation_rate, current_year)
        appreciation_over_time.append(appreciation * 0.5)  # 50% of appreciation
    
    return principal_over_time, appreciation_over_time

def create_equity_area_chart(principal_over_time, appreciation_over_time, years):
    x = list(range(1, years * 12 + 1))
    total_equity = [p + a for p, a in zip(principal_over_time, appreciation_over_time)]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=principal_over_time,
        mode='lines',
        # line=dict(width=0.5, color='#0068C9'),
        stackgroup='one',
        name='Principal',
        hovertemplate='$%{y:,.2f}'
    ))
    fig.add_trace(go.Scatter(
        x=x, y=appreciation_over_time,
        mode='lines',
        # line=dict(width=0.5, color='#003B72'),
        stackgroup='one',
        name='Appreciation',
        hovertemplate='$%{y:,.2f}'
    ))
    # Add new trace for total equity
    fig.add_trace(go.Scatter(
        x=x, y=total_equity,
        mode='lines',
        line=dict(width=2, color='#E29578'),
        name='Total Equity',
        hovertemplate='$%{y:,.2f}'
    ))
    
    # Add vertical lines for each year
    for year in range(1, years + 1):
        fig.add_vline(x=year * 12, line_dash="dash", line_color="gray", opacity=0.7)
        fig.add_annotation(
            x=year * 12,
            y=1,
            yref="paper",
            text=f"{year} Year{'s' if year > 1 else ''}",
            showarrow=False,
            textangle=-90,
            yshift=28,
            font=dict(size=10)
        )
    
    fig.update_layout(
        title='Equity Build-up Over Time',
        xaxis_title='Months',
        yaxis_title='Equity ($)',
        legend=dict(x=0.01, y=0.99, bgcolor='rgba(255, 255, 255, 0.8)'),
        hovermode='x unified'
    )
    
    return fig

@st.cache_data(ttl=604800)  # Cache for 1 week
def calculate_comparison_values(house_price, property_tax_rate, appreciation_rate, years, monthly_rent, total_equity, down_payment_ratio, price_to_rent_ratio, investment_return_rate, marginal_tax_rate, mortgage_rate, pmi_rate, insurance_cost):
    traditional_loan = house_price * (1 - down_payment_ratio)
    mortgage_payment = npf.pmt(mortgage_rate/12, LOAN_TERM_YEARS*12, -traditional_loan)
    monthly_insurance = insurance_cost
    monthly_property_tax = (house_price * property_tax_rate) / 12
    monthly_pmi = (traditional_loan * pmi_rate) / 12 if down_payment_ratio < 0.2 else 0
    traditional_payment = mortgage_payment + monthly_insurance + monthly_property_tax + monthly_pmi
    traditional_principal = sum(calculate_monthly_breakdown(traditional_loan, mortgage_rate, LOAN_TERM_YEARS, month)[0] for month in range(1, years*12+1))
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

    # Calculate total interest paid for traditional mortgage
    total_interest_paid = sum(calculate_monthly_breakdown(traditional_loan, mortgage_rate, LOAN_TERM_YEARS, month)[1] for month in range(1, years*12+1))
    
    # Calculate tax savings from mortgage interest deduction
    tax_savings = total_interest_paid * marginal_tax_rate
    
    # Adjust the traditional cost to include tax savings
    traditional_cost -= tax_savings

    return {
        'mortgage_rate': mortgage_rate,
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
        'price_to_rent_ratio': price_to_rent_ratio,
        'tax_savings': tax_savings,
        'monthly_pmi': monthly_pmi
    }

# Sidebar inputs
with st.sidebar:
    st.markdown("#### Advanced Settings")
    st.write("These settings are optional and can be adjusted to see how they impact the results.")
    # Advanced settings in an expandable section
    with st.expander("Advanced Settings"):
        current_mortgage_rate = get_current_mortgage_rate()
        mortgage_rate = st.number_input("Mortgage Rate (%)", min_value=0.0, max_value=15.0, value=current_mortgage_rate*100, step=0.1, help="The annual mortgage interest rate. Defaults to the current 30-year fixed rate from FRED.") / 100
        appreciation_rate = st.number_input("Annual Appreciation Rate (%)", min_value=0.0, max_value=10.0, value=3.5, step=0.1) / 100
        closing_costs_rate = st.number_input("Closing Costs (%)", min_value=0.0, max_value=10.0, value=0.75, step=0.1) / 100
        property_tax_rate = st.number_input("Property Tax Rate (%)", min_value=0.0, max_value=5.0, value=1.122, step=0.001) / 100
        investment_return_rate = st.number_input("Investment Return Rate (%)", min_value=0.0, max_value=20.0, value=5.0, step=0.1, help="The rate of return you expect to earn in an investment account. This is used to calculate the opportunity cost of the down payment if you were to invest it instead of using it for a traditional mortgage.") / 100
        price_to_rent_ratio = st.number_input("Price-to-Rent Ratio", min_value=1, max_value=50, value=19, step=1, help="The ratio of the price of the home to the rent of a similar home. This is used to calculate the monthly rent of an equivalent home for comparison purposes.")
        marginal_tax_rate = st.number_input("Marginal Tax Rate (%)", min_value=0.0, max_value=50.0, value=16.0, step=0.1, help="Your marginal tax rate. This is used to calculate the tax savings from the mortgage interest deduction.") / 100
        pmi_rate = st.number_input("PMI Rate (%)", min_value=0.0, max_value=5.0, value=1.5, step=0.1, help="Private Mortgage Insurance rate. This is typically required when the down payment is less than 20% of the home value.") / 100
        insurance_cost = st.number_input("Monthly Home Insurance ($)", min_value=0, max_value=1000, value=INSURANCE_FIXED, step=10, help="Monthly cost of home insurance.")

# Set up the main title and description
st.title("Rent-to-Own Calculator")
st.write("This tool enables you to determine the equity you will own in your home over time, calculate monthly mortgage payments, and gives a great comparison between buying and renting a place.")

# Basic price input
col1, col2 = st.columns(2)
house_price = col1.number_input("Enter the price of the home you are considering ($)", min_value=0.0, step=5000.0, value=400000.0, format="%.0f")

add_vertical_space(1)

st.subheader("Monthly Rent Breakdown")
st.write("Unlike typical rent, rent to own applies a portion of your rent towards the purchase of the home. The rest is used to pay for the loan, property taxes, insurance, and maintenance.")

add_vertical_space(1)

subheader_slot = st.empty()
add_vertical_space(1)
plot_slot = st.empty()
plot_slot.container(height=300)

add_vertical_space(2)
st.divider()
add_vertical_space(1)

# Equity calculation section
st.header("How much equity can you build in your home over time?")
st.write("In addition to a portion of your rent going towards the purchase of the home, you will also share in 50% of the appreciation of the home as it goes up in value.")

add_vertical_space(1)

# User input for years of renting
years = st.slider("Select the number of years you plan to rent the home.", min_value=1, max_value=7, value=DEFAULT_YEARS, step=1)

# Calculate initial values with default years
fig, house_price, loan_amount, monthly_rent = update_calculator(house_price, closing_costs_rate, property_tax_rate, appreciation_rate, years, insurance_cost)

subheader_slot.subheader(f"Your monthly rent would be :blue[${monthly_rent:,.2f}].")
plot_slot.plotly_chart(fig, use_container_width=True)

# Calculate and display equity breakdown
principal_over_time, appreciation_over_time = calculate_equity_over_time(house_price, loan_amount, 0.035, LOAN_TERM_YEARS, appreciation_rate, years)
equity_fig = create_equity_area_chart(principal_over_time, appreciation_over_time, years)

total_equity = principal_over_time[-1] + appreciation_over_time[-1]
st.subheader(f"You would build an estimated :blue[${total_equity:,.2f}] in equity.")
st.write("This is assuming a 3.5% annual appreciation, which will depend on the local market.")

add_vertical_space(1)
st.plotly_chart(equity_fig, use_container_width=True)
add_vertical_space(3)


row1 = row([10, 1], vertical_align="center")

# Comparison of different scenarios
row1.markdown(f"#### In :blue[{years}] years, how does the cost compare to renting?")

# Add toggles for including down payment opportunity cost and tax deductions
with row1.popover(":gear:"):
    include_opportunity_cost = st.toggle(
        "Include down payment opportunity cost",
        value=True,
        help="If enabled, calculates the potential earnings lost by using money for a down payment instead of investing it."
    )
    include_tax_deductions = st.toggle(
        "Include tax deductions",
        value=True,
        help="If enabled, includes the tax savings from mortgage interest deductions in the calculations."
    )
    down_payment = st.number_input("Your down payment for a traditional mortgage ($)", min_value=0.0, max_value=house_price, value=0.0, step=1000.0, format="%.0f")

# Calculate down payment ratio
down_payment_ratio = down_payment / house_price

# Calculate comparison values
comparison_values = calculate_comparison_values(
    house_price, 
    property_tax_rate, 
    appreciation_rate, 
    years, 
    monthly_rent, 
    total_equity, 
    down_payment_ratio, 
    price_to_rent_ratio, 
    investment_return_rate, 
    marginal_tax_rate,
    mortgage_rate,
    pmi_rate,
    insurance_cost
)

# Recalculate costs based on toggle settings
if not include_opportunity_cost:
    comparison_values['traditional_cost'] -= (comparison_values['traditional_cost'] - comparison_values['traditional_spent'] + comparison_values['traditional_equity'])

if not include_tax_deductions:
    comparison_values['traditional_cost'] += comparison_values['tax_savings']

# Create full comparison data
comparison_data = {
    "": ["Initial purchase price", "Down payment", "Interest rate", "Appreciation share", "Monthly payment", 
         "Monthly PMI", f"Total equity ({years} years)", f"Total spent ({years} years)",
         "Down payment opportunity cost", "Tax savings (mortgage interest)", "Total true cost"],
    "Rent to Own": [f"${house_price:,.0f}", "$0", f"{0.035:.1%}", "50%", f"${monthly_rent:,.0f}", 
                    "$0", f"${total_equity:,.0f}", f"${comparison_values['rent_to_own_spent']:,.0f}",
                    "$0", "$0", f"${comparison_values['rent_to_own_cost']:,.0f}"],
    "Traditional Mortgage": [f"${house_price:,.0f}", f"${comparison_values['down_payment']:,.0f}", f"{comparison_values['mortgage_rate']:.2%}", "100%", 
                             f"${comparison_values['traditional_payment']:,.0f}", 
                             f"${comparison_values['monthly_pmi']:,.0f}",
                             f"${comparison_values['traditional_equity']:,.0f}", f"${comparison_values['traditional_spent']:,.0f}",
                             f"${comparison_values['traditional_cost'] - comparison_values['traditional_spent'] + comparison_values['traditional_equity']:,.0f}",
                             f"${comparison_values['tax_savings']:,.0f}", f"${comparison_values['traditional_cost']:,.0f}"],
    "Renting": ["$0", "$0", "", "0%", f"${comparison_values['rental_payment']:,.0f}", 
                "$0", "$0", f"${comparison_values['renting_spent']:,.0f}",
                "$0", "$0", f"${comparison_values['renting_cost']:,.0f}"]
}

# Create DataFrame for detailed comparison
df = pd.DataFrame(comparison_data)

# Remove rows based on toggle states
if not include_opportunity_cost:
    df = df.drop(df.index[df.iloc[:, 0] == "Down payment opportunity cost"])

if not include_tax_deductions:
    df = df.drop(df.index[df.iloc[:, 0] == "Tax savings (mortgage interest)"])

# Reset index after dropping rows
df = df.reset_index(drop=True)

# Display total cost metrics for each scenario
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Rent to Own Cost", 
              f"${comparison_values['rent_to_own_cost']:,.0f}")
with col2:
    delta_traditional = comparison_values['rent_to_own_cost'] - comparison_values['traditional_cost']
    st.metric("Traditional Mortgage Cost", 
              f"${comparison_values['traditional_cost']:,.0f}", 
              delta=f"{'-' if delta_traditional > 0 else ''}${abs(delta_traditional):,.0f}",
              delta_color="inverse")
with col3:
    delta_renting = comparison_values['rent_to_own_cost'] - comparison_values['renting_cost']
    st.metric("Traditional Renting Cost", 
              f"${comparison_values['renting_cost']:,.0f}", 
              delta=f"{'-' if delta_renting > 0 else ''}${abs(delta_renting):,.0f}",
              delta_color="inverse")

# Define column configuration for better display
column_config = {
    "Metric": st.column_config.TextColumn("Metric", width="medium"),
    "Rent to Own": st.column_config.NumberColumn("Rent to Own", width="small"),
    "Traditional Mortgage": st.column_config.NumberColumn("Mortgage", width="small"),
    "Renting": st.column_config.NumberColumn("Renting", width="small")
}

# Display detailed comparison table in an expandable section
with st.expander("🔍 See the full comparison table"):
    st.dataframe(
        df.style.set_properties(**{'text-align': 'right'}, subset=df.columns[1:]),
        column_config=column_config,
        hide_index=True,
        use_container_width=True
    )

    # Add glossary of terms
    st.markdown("""
    ##### Glossary of Terms
    - **Initial purchase price**: The original cost of the home.
    - **Down payment**: The initial upfront payment made when purchasing a home.
    - **Interest rate**: The annual cost of borrowing the money, expressed as a percentage.
    - **Appreciation share**: The percentage of the home's increase in value that you benefit from.
    - **Monthly payment**: The amount paid each month for housing costs.
    - **Total equity**: The total value of your ownership stake in the property.
    - **Total spent**: The total amount of money paid over the selected time period.
    - **Down payment opportunity cost**: The potential earnings lost by using money for a down payment instead of investing it.
    - **Tax savings (mortgage interest)**: The amount saved on taxes due to the mortgage interest deduction.
    - **Total true cost**: The net cost after considering all expenses, equity gained, and opportunity costs.
    """)

# Add caption explaining assumptions
st.caption(f"This looks at all the money you'll be spending on a house minus your gained equity and appreciation. We're assuming a mortgage rate of {comparison_values['mortgage_rate']:.2%}, an average appreciation rate of {appreciation_rate:.1%}, a {property_tax_rate:.2%} annual property tax rate, a {down_payment_ratio:.1%} down payment with {pmi_rate:.1%} PMI (if applicable), a price-to-rent ratio of {price_to_rent_ratio}, and a marginal tax rate of {marginal_tax_rate:.1%}.")