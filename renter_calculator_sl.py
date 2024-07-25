import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd
import datetime

def calculate_rent_to_own(house_price):
    closing_costs_rate = 0.03
    interest_rate = 0.035
    insurance_fixed = 120
    property_tax_rate = 0.01122
    management_fee_rate = 0.08
    loan_term_years = 30
    
    closing_costs = house_price * closing_costs_rate
    total_purchase_price = house_price + closing_costs
    
    # Calculate mortgage payment
    monthly_rate = interest_rate / 12
    num_payments = loan_term_years * 12
    mortgage_payment = total_purchase_price * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
    
    monthly_interest = (total_purchase_price * interest_rate) / 12
    monthly_principal = mortgage_payment - monthly_interest
    monthly_insurance = insurance_fixed
    monthly_property_tax = (house_price * property_tax_rate) / 12
    monthly_management_fee = mortgage_payment * management_fee_rate
    
    monthly_rent = mortgage_payment + monthly_insurance + monthly_property_tax + monthly_management_fee

    breakdown = {
        "Principal": monthly_principal,
        "Interest": monthly_interest,
        "Insurance": monthly_insurance,
        "Property Tax": monthly_property_tax,
        "Management Fee": monthly_management_fee
    }
    
    return house_price, monthly_rent, breakdown, interest_rate, loan_term_years

def calculate_monthly_breakdown(house_price, interest_rate, loan_term_years, month):
    monthly_rate = interest_rate / 12
    num_payments = loan_term_years * 12
    monthly_payment = house_price * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
    
    remaining_balance = house_price * ((1 + monthly_rate)**num_payments - (1 + monthly_rate)**month) / ((1 + monthly_rate)**num_payments - 1)
    interest = remaining_balance * monthly_rate
    principal = monthly_payment - interest
    
    return principal, interest

def calculate_amortization(house_price, interest_rate, loan_term_years):
    monthly_rate = interest_rate / 12
    num_payments = loan_term_years * 12
    monthly_payment = house_price * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
    
    schedule = []
    balance = house_price
    total_interest = 0
    current_year = datetime.datetime.now().year
    annual_appreciation_rate = 0.035
    
    for month in range(1, num_payments + 1):
        interest = balance * monthly_rate
        principal = monthly_payment - interest
        total_interest += interest
        balance -= principal
        
        if month % 12 == 0 or month == 1 or month == num_payments:
            years_passed = (month - 1) // 12
            appreciated_value = house_price * (1 + annual_appreciation_rate) ** years_passed
            appreciation = appreciated_value - house_price
            equity_with_appreciation = (house_price - balance) + (0.5 * appreciation)
            
            schedule.append({
                'Year': current_year + years_passed,
                'Principal Paid': house_price - balance,
                'Interest Paid': total_interest,
                'Loan Balance': max(0, balance),
                'Equity with Appreciation': equity_with_appreciation
            })
    
    return pd.DataFrame(schedule)

def generate_date_labels(num_months):
    start_date = datetime.datetime.now().replace(day=1)
    date_labels = [(start_date + datetime.timedelta(days=30*i)).strftime('%m/%Y') for i in range(num_months)]
    return date_labels

def update_calculator(house_price, selected_date):
    # Convert selected_date back to month number
    start_date = datetime.datetime.now().replace(day=1)
    selected_date = datetime.datetime.strptime(selected_date, '%m/%Y')
    month_slider = (selected_date.year - start_date.year) * 12 + (selected_date.month - start_date.month) + 1

    house_price, monthly_rent, breakdown, interest_rate, loan_term_years = calculate_rent_to_own(house_price)
    
    # Calculate principal and interest for the selected month
    principal, interest = calculate_monthly_breakdown(house_price, interest_rate, loan_term_years, month_slider)
    
    # Update breakdown with new principal and interest values
    breakdown['Principal'] = principal
    breakdown['Interest'] = interest
    
    # Create pie chart
    labels = list(breakdown.keys())
    values = list(breakdown.values())
    colors = ['#4285F4', '#34A853', '#FBBC05', '#EA4335', '#5F6368']

    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values, 
        hole=.6, 
        marker_colors=colors,
        textinfo='label+value',
        hoverinfo='label+percent',
        texttemplate='%{label}<br>$%{value:.2f}',
        hovertemplate='%{label}<br>$%{value:.2f}<br>%{percent:.1%}',
        name=''  # Set name to empty string to remove "trace 0"
    )])
    fig.update_layout(
        annotations=[dict(text=f'<b>${monthly_rent:.2f}</b><br>/mo', x=0.5, y=0.5, font_size=20, showarrow=False)],
        showlegend=True,
        autosize=True,
        margin=dict(l=20, r=20, t=20, b=20),
        title_text=''  # Set title to empty string
    )
    
    selected_date = selected_date.strftime('%m/%Y')
    
    breakdown_html = f"""
    <table style="width:100%; border-collapse: collapse; font-size: 16px;">
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>House Price:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">${house_price:,.2f}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Monthly Rent:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">${monthly_rent:.2f}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Principal ({selected_date}):</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">${breakdown['Principal']:.2f}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Interest ({selected_date}):</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">${breakdown['Interest']:.2f}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Property tax:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">${breakdown['Property Tax']:.2f}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Insurance:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">${breakdown['Insurance']:.2f}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Management Fee:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">${breakdown['Management Fee']:.2f}</td>
        </tr>
    </table>
    """
    
    df = calculate_amortization(house_price, interest_rate, loan_term_years)
    
    fig_amortization = go.Figure()
    fig_amortization.add_trace(go.Scatter(
        x=df['Year'], 
        y=df['Principal Paid'], 
        name='Principal paid', 
        line=dict(color='#4285F4'),
        text=[f'${y:,.0f}' for y in df['Principal Paid']],
        hovertemplate='%{x}: %{text}<extra></extra>'
    ))
    fig_amortization.add_trace(go.Scatter(
        x=df['Year'], 
        y=df['Interest Paid'], 
        name='Interest paid', 
        line=dict(color='#34A853'),
        text=[f'${y:,.0f}' for y in df['Interest Paid']],
        hovertemplate='%{x}: %{text}<extra></extra>'
    ))
    fig_amortization.add_trace(go.Scatter(
        x=df['Year'], 
        y=df['Loan Balance'], 
        name='Loan balance', 
        line=dict(color='#EA4335'),
        text=[f'${y:,.0f}' for y in df['Loan Balance']],
        hovertemplate='%{x}: %{text}<extra></extra>'
    ))
    fig_amortization.add_trace(go.Scatter(
        x=df['Year'], 
        y=df['Equity with Appreciation'], 
        name='Equity with Appreciation', 
        line=dict(color='#FBBC05'),
        text=[f'${y:,.0f}' for y in df['Equity with Appreciation']],
        hovertemplate='%{x}: %{text}<extra></extra>'
    ))
    
    fig_amortization.update_layout(
        title='Amortization and Equity Schedule',
        xaxis_title='Year',
        yaxis_title='Amount ($)',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(l=40, r=40, t=60, b=40),
        height=500,
        yaxis=dict(tickformat='$,.0f')
    )
    
    total_interest_paid = df['Interest Paid'].iloc[-1]
    total_cost = house_price + total_interest_paid
    payoff_date = pd.Timestamp.now() + pd.DateOffset(years=loan_term_years)
    
    return fig, breakdown_html, fig_amortization, house_price, total_interest_paid, total_cost, payoff_date

def main():
    st.set_page_config(layout="wide")
    st.title("Rent-to-Own Calculator")
    st.text("")

    col1, col2 = st.columns([1, 4], gap="large")

    with col1:
        st.subheader("Enter your house price budget.")
        st.write("This can be the price of a house you're looking at, or just your maximum budget.")
        house_price = st.number_input("House Price", min_value=0.0, step=5000.0, value=400000.0, format="%.0f", help="This can be the price of a house you're looking at, or just your maximum budget.")

    with col2:
        tab1, tab2 = st.tabs(["Payment Breakdown", "Amortization"])
        
        with tab1:
            st.header("Monthly Payment Breakdown")
            st.write("This shows where your rent is going each month. Like a mortgage, the amount that goes towards the principal increases over time.")
            date_labels = generate_date_labels(7 * 12)

            if house_price:
                col1, col2 = st.columns([2, 1])
                with col1:
                    # Create placeholders for chart and slider
                    chart_placeholder = st.empty()
                    st.subheader("See how principal contributions increase over time")
                    st.write("Move the slider to see how your principal contributions increase over time.")
                    slider_placeholder = st.empty()
                    
                    # Use date_labels for the slider
                    selected_date = slider_placeholder.select_slider("Payment Date", options=date_labels, value=date_labels[0])
                    
                    # Calculate with the selected date
                    fig, breakdown_html, fig_amortization, loan_amount, total_interest_paid, total_cost, payoff_date = update_calculator(house_price, selected_date)
                    
                    # Display the pie chart above the slider
                    chart_placeholder.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.markdown(breakdown_html, unsafe_allow_html=True)

        with tab2:
            st.header("Amortization for rent-to-own program")
            st.write("In a rent-to-own program, your monthly payments contribute to both rent and future ownership. As time progresses, a larger portion of your payment goes towards building equity in the property. This schedule shows how your payments reduce the remaining balance over time, eventually leading to full ownership at the end of the term.")
            
            if house_price:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Loan amount", f"${loan_amount:,.0f}")
                with col2:
                    st.metric("Total interest paid", f"${total_interest_paid:,.0f}")
                with col3:
                    st.metric("Total cost of loan", f"${total_cost:,.0f}")
                with col4:
                    st.metric("Payoff date", payoff_date.strftime('%b %Y'))

                st.plotly_chart(fig_amortization, use_container_width=True)

if __name__ == "__main__":
    main()