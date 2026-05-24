import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import re

# Page setup
st.set_page_config(page_title="Data Cleaning & Automation", layout="wide")

st.title("🧹 Data Cleaning & Reporting Automation Dashboard")
st.markdown("*Automated Data Preprocessing, Cleaning, and Report Generation*")
st.markdown("---")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("raw_customer_data.csv")
    return df

raw_df = load_data()

# Display raw data
st.subheader("📊 Step 1: Raw Data (Before Cleaning)")
st.markdown("⚠️ **Notice the issues:** Missing values, duplicates, invalid emails, missing phone numbers")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Rows", len(raw_df))
col2.metric("Total Columns", len(raw_df.columns))
col3.metric("Missing Values", raw_df.isnull().sum().sum())
col4.metric("Duplicates", raw_df.duplicated().sum())

st.dataframe(raw_df, width='stretch')

st.markdown("---")

# ========== DATA CLEANING FUNCTION ==========
st.subheader("🧹 Step 2: Data Cleaning Process")

def clean_data(df):
    cleaning_log = []
    
    # Make a copy
    df_clean = df.copy()
    
    # 1. Remove duplicates
    duplicates_before = df_clean.duplicated().sum()
    df_clean = df_clean.drop_duplicates()
    cleaning_log.append(f"✅ Removed {duplicates_before} duplicate rows")
    
    # 2. Fix data types first - Convert problematic columns
    df_clean['Orders'] = pd.to_numeric(df_clean['Orders'], errors='coerce')
    df_clean['Total_Spent'] = pd.to_numeric(df_clean['Total_Spent'], errors='coerce')
    
    # 3. Handle missing values
    missing_before = df_clean.isnull().sum().sum()
    
    df_clean['Name'] = df_clean['Name'].fillna("Unknown")
    df_clean['Email'] = df_clean['Email'].fillna("unknown@email.com")
    df_clean['Phone'] = df_clean['Phone'].fillna("Not Provided")
    df_clean['City'] = df_clean['City'].fillna("Unknown")
    df_clean['Total_Spent'] = df_clean['Total_Spent'].fillna(df_clean['Total_Spent'].median())
    df_clean['Orders'] = df_clean['Orders'].fillna(df_clean['Orders'].median())
    
    missing_after = df_clean.isnull().sum().sum()
    cleaning_log.append(f"✅ Filled {missing_before - missing_after} missing values")
    
    # 4. Fix invalid emails
    def fix_email(email):
        if pd.isna(email):
            return "unknown@email.com"
        email = str(email).lower().strip()
        if '@' not in email or '.' not in email:
            return f"{email}@fixed.com"
        return email
    
    df_clean['Email'] = df_clean['Email'].apply(fix_email)
    cleaning_log.append("✅ Fixed invalid email formats")
    
    # 5. Fix phone numbers
    df_clean['Phone'] = df_clean['Phone'].astype(str)
    df_clean['Phone'] = df_clean['Phone'].apply(lambda x: "Not Provided" if x in ["nan", "None", "-"] else x)
    cleaning_log.append("✅ Standardized phone number format")
    
    # 6. Fix date columns
    df_clean['Join_Date'] = pd.to_datetime(df_clean['Join_Date'], errors='coerce')
    df_clean['Last_Order'] = pd.to_datetime(df_clean['Last_Order'], errors='coerce')
    
    today = datetime.now()
    df_clean['Join_Date'] = df_clean['Join_Date'].fillna(today)
    df_clean['Last_Order'] = df_clean['Last_Order'].fillna(today)
    cleaning_log.append("✅ Fixed date formats and missing dates")
    
    # 7. Fix Status column
    df_clean['Status'] = df_clean['Status'].astype(str)
    df_clean['Status'] = df_clean['Status'].str.capitalize()
    df_clean.loc[df_clean['Status'].str.isnumeric(), 'Status'] = 'Active'
    df_clean['Status'] = df_clean['Status'].fillna("Active")
    cleaning_log.append("✅ Standardized Status values")
    
    # 8. Remove leading/trailing spaces
    string_columns = df_clean.select_dtypes(include=['object']).columns
    for col in string_columns:
        df_clean[col] = df_clean[col].astype(str).str.strip()
    cleaning_log.append("✅ Removed extra spaces from all text fields")
    
    # 9. Add data quality score
    df_clean['Data_Quality_Score'] = 100
    df_clean.loc[df_clean['Name'] == "Unknown", 'Data_Quality_Score'] -= 20
    df_clean.loc[df_clean['Email'].str.contains('fixed', na=False), 'Data_Quality_Score'] -= 15
    df_clean.loc[df_clean['Phone'] == "Not Provided", 'Data_Quality_Score'] -= 15
    df_clean.loc[df_clean['City'] == "Unknown", 'Data_Quality_Score'] -= 10
    df_clean['Data_Quality_Score'] = df_clean['Data_Quality_Score'].clip(0, 100)
    cleaning_log.append("✅ Added Data Quality Score metric")
    
    # 10. Clean up numeric columns
    df_clean['Orders'] = pd.to_numeric(df_clean['Orders'], errors='coerce').fillna(0).astype(int)
    df_clean['Total_Spent'] = pd.to_numeric(df_clean['Total_Spent'], errors='coerce').fillna(0).astype(float)
    
    return df_clean, cleaning_log

# Perform cleaning
cleaned_df, cleaning_log = clean_data(raw_df)

# Display cleaning log
with st.expander("📋 View Cleaning Log"):
    for log in cleaning_log:
        st.success(log)

st.markdown("---")

# Display cleaned data
st.subheader("📊 Step 3: Cleaned Data (After Cleaning)")
st.markdown("✅ **All issues resolved:** No missing values, no duplicates, clean formats")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Rows", len(cleaned_df))
col2.metric("Total Columns", len(cleaned_df.columns))
col3.metric("Missing Values", cleaned_df.isnull().sum().sum())
col4.metric("Duplicates", cleaned_df.duplicated().sum())

st.dataframe(cleaned_df, width='stretch')

st.markdown("---")

# ========== DATA QUALITY METRICS ==========
st.subheader("📈 Step 4: Data Quality Dashboard")

col1, col2 = st.columns(2)

with col1:
    quality_dist = cleaned_df['Data_Quality_Score'].value_counts().sort_index().reset_index()
    quality_dist.columns = ['Score', 'Count']
    fig_quality = px.bar(
        quality_dist,
        x='Score',
        y='Count',
        title='Data Quality Score Distribution',
        color='Score',
        color_continuous_scale='Viridis',
        text='Count'
    )
    fig_quality.update_traces(textposition='outside')
    st.plotly_chart(fig_quality, width='stretch')

with col2:
    status_counts = cleaned_df['Status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    fig_status = px.pie(
        status_counts,
        values='Count',
        names='Status',
        title='Customer Status Distribution',
        hole=0.3,
        color_discrete_sequence=['green', 'red', 'orange']
    )
    st.plotly_chart(fig_status, width='stretch')

# City Distribution
st.subheader("📍 Customer Distribution by City")
city_counts = cleaned_df['City'].value_counts().reset_index()
city_counts.columns = ['City', 'Count']
fig_city = px.bar(
    city_counts,
    x='City',
    y='Count',
    title='Number of Customers per City',
    color='Count',
    color_continuous_scale='Blues',
    text='Count'
)
fig_city.update_traces(textposition='outside')
st.plotly_chart(fig_city, width='stretch')

st.markdown("---")

# ========== AUTOMATED REPORT ==========
st.subheader("📄 Step 5: Automated Summary Report")

total_customers = len(cleaned_df)
active_customers = len(cleaned_df[cleaned_df['Status'] == 'Active'])
inactive_customers = len(cleaned_df[cleaned_df['Status'] == 'Inactive'])
total_revenue = cleaned_df['Total_Spent'].sum()
avg_spend = cleaned_df['Total_Spent'].mean()
total_orders = cleaned_df['Orders'].sum()
avg_orders = cleaned_df['Orders'].mean()
avg_quality_score = cleaned_df['Data_Quality_Score'].mean()

col1, col2, col3, col4 = st.columns(4)
col1.metric("👥 Total Customers", total_customers)
col2.metric("💰 Total Revenue", f"₹{total_revenue:,.0f}")
col3.metric("📦 Total Orders", f"{total_orders:,}")
col4.metric("⭐ Avg Quality Score", f"{avg_quality_score:.1f}%")

st.markdown("---")

# Detailed Report
st.subheader("📊 Automated Business Report")

report = f"""
### 📋 Executive Summary

**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Data Source:** raw_customer_data.csv
**Total Records Processed:** {total_customers}

---

### 📈 Key Metrics

| Metric | Value |
|--------|-------|
| Total Customers | {total_customers} |
| Active Customers | {active_customers} ({active_customers/total_customers*100:.1f}%) |
| Inactive Customers | {inactive_customers} ({inactive_customers/total_customers*100:.1f}%) |
| Total Revenue | ₹{total_revenue:,.0f} |
| Average Spend per Customer | ₹{avg_spend:,.0f} |
| Total Orders | {total_orders:,} |
| Average Orders per Customer | {avg_orders:.1f} |

---

### 🧹 Data Quality Summary

- **Missing Values Fixed:** {raw_df.isnull().sum().sum() - cleaned_df.isnull().sum().sum()}
- **Duplicates Removed:** {raw_df.duplicated().sum()}
- **Average Data Quality Score:** {avg_quality_score:.1f}%

---

### 🏆 Top 5 Cities by Customers

{cleaned_df['City'].value_counts().head(5).to_string()}

---

### 📊 Recommendations

1. **Data Quality:** Focus on improving data collection for {cleaned_df[cleaned_df['Data_Quality_Score'] < 80].shape[0]} customers with low quality scores
2. **Customer Engagement:** Re-engage {inactive_customers} inactive customers with special offers
3. **City Focus:** {cleaned_df['City'].value_counts().index[0]} has highest customer concentration
"""

st.markdown(report)

st.markdown("---")

# ========== DOWNLOAD OPTIONS ==========
st.subheader("📥 Step 6: Export Cleaned Data & Reports")

col1, col2 = st.columns(2)

with col1:
    csv_cleaned = cleaned_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Cleaned Data (CSV)",
        data=csv_cleaned,
        file_name="cleaned_customer_data.csv",
        mime="text/csv",
    )

with col2:
    report_txt = report.encode('utf-8')
    st.download_button(
        label="📄 Download Report (TXT)",
        data=report_txt,
        file_name=f"data_quality_report_{datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain",
    )

# Show before/after comparison
with st.expander("🔍 Before vs After Comparison"):
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Before Cleaning")
        st.dataframe(raw_df.head(10), width='stretch')
    with col2:
        st.subheader("After Cleaning")
        st.dataframe(cleaned_df.head(10), width='stretch')

st.markdown("---")
st.caption("✅ Data Cleaning & Automation Dashboard | Automated Reports | Built with Python, Streamlit & Plotly")