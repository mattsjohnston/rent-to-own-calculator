import gradio as gr
import numpy as np
import plotly.graph_objects as go
import pandas as pd
import datetime

def calculate_rent_to_own(house_price=None, monthly_rent=None):
    if house_price is None and monthly_rent is None:
        return None, None, None
    
    closing_costs_rate = 0.03
    interest_rate = 0.035
    insurance_fixed = 120
    property_tax_rate = 0.01122
    management_fee_rate = 0.08
    loan_term_years = 30
    
    if house_price is not None:
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
    else:
        # Calculate house price based on monthly rent (reverse calculation)
        # This is an approximation and may not be exact
        monthly_payment = monthly_rent / (1 + management_fee_rate + (insurance_fixed / monthly_rent) + (property_tax_rate / 12))
        monthly_rate = interest_rate / 12
        num_payments = loan_term_years * 12
        total_purchase_price = monthly_payment / ((monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1))
        
        house_price = total_purchase_price / (1 + closing_costs_rate)
        closing_costs = house_price * closing_costs_rate
        
        mortgage_payment = monthly_payment
        monthly_interest = (total_purchase_price * interest_rate) / 12
        monthly_principal = mortgage_payment - monthly_interest
        monthly_insurance = insurance_fixed
        monthly_property_tax = (house_price * property_tax_rate) / 12
        monthly_management_fee = mortgage_payment * management_fee_rate

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

def update_calculator(house_price, monthly_rent, month_slider):
    if house_price:
        house_price, monthly_rent, breakdown, interest_rate, loan_term_years = calculate_rent_to_own(house_price=house_price)
        
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
        
        selected_date = (datetime.datetime.now().replace(day=1) + datetime.timedelta(days=30*(month_slider-1))).strftime('%m/%Y')
        
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
        
        amortization_summary = f"""
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 20px 60px;">
            <div>
                <span style="font-size: 14px; color: #666;">Loan amount</span>
                <h2 style="margin: 0; font-size: 24px;">${house_price:,.0f}</h2>
            </div>
            <div>
                <span style="font-size: 14px; color: #666;">Total interest paid</span>
                <h2 style="margin: 0; font-size: 24px;">${total_interest_paid:,.0f}</h2>
            </div>
            <div>
                <span style="font-size: 14px; color: #666;">Total cost of loan</span>
                <h2 style="margin: 0; font-size: 24px;">${total_cost:,.0f}</h2>
            </div>
            <div>
                <span style="font-size: 14px; color: #666;">Payoff date</span>
                <h2 style="margin: 0; font-size: 24px;">{payoff_date.strftime('%b %Y')}</h2>
            </div>
        </div>
        """
        
        return fig, breakdown_html, fig_amortization, amortization_summary
    else:
        return None, "Please enter a House Price to calculate the amortization schedule.", None, ""

with gr.Blocks() as demo:
    gr.Markdown("# Rent-to-Own Calculator")
    
    with gr.Row():
        with gr.Column(scale=1):
            with gr.Tabs():
                with gr.TabItem("House Price"):
                    house_price = gr.Number(label="House Price ($)")
                with gr.TabItem("Rental Budget"):
                    monthly_rent = gr.Number(label="Monthly Rent ($)")
            calculate_btn = gr.Button("Calculate")
        
        with gr.Column(scale=4):
            with gr.Tabs():
                with gr.TabItem("Payment Breakdown"):
                    with gr.Row():
                        gr.Markdown("## Monthly Payment Breakdown")
                    with gr.Row():
                        date_labels = generate_date_labels(360)
                        month_slider = gr.Slider(minimum=1, maximum=360, step=1, value=1, label="Payment Date")
                    with gr.Row():
                        with gr.Column(scale=2):
                            plot_output = gr.Plot(label="Payment Breakdown", container=True)
                        with gr.Column(scale=1):
                            breakdown_output = gr.HTML()
                    summary_output = gr.HTML()
                with gr.TabItem("Amortization"):
                    gr.Markdown(f"""## Amortization for rent-to-own program
                                In a rent-to-own program, your monthly payments contribute to both rent and future ownership. As time progresses, a larger portion of your payment goes towards building equity in the property. This schedule shows how your payments reduce the remaining balance over time, eventually leading to full ownership at the end of the term.
                                """)
                    amortization_summary = gr.HTML()
                    amortization_plot = gr.Plot(label="Amortization Schedule")

    calculate_btn.click(
        fn=update_calculator,
        inputs=[house_price, monthly_rent, month_slider],
        outputs=[plot_output, breakdown_output, amortization_plot, amortization_summary]
    )
    
    month_slider.change(
        fn=update_calculator,
        inputs=[house_price, monthly_rent, month_slider],
        outputs=[plot_output, breakdown_output, amortization_plot, amortization_summary]
    )

if __name__ == "__main__":
    demo.launch(server_port=7861)