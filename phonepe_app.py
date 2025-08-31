import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text

st.set_page_config(layout="wide", page_title="PhonePe Case Studies Dashboard")

st.title("📊 PhonePe Case Studies Dashboard")
st.caption("Filter by Year, Quarter, and State → pick a case study → explore insights per study (maps, trend, distribution, category performance, and Top 10 states)")

# Database connection
@st.cache_resource
def get_connection():
    try:
        engine = create_engine(
            "mysql+pymysql://13DQLuf64nn2jC2.root:Yl91nAYMjEKQwgQK@"
            "gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/phonepe",
            connect_args={"ssl": {"ca": r"C:\\Users\\rosha\\Downloads\\phonepe project\\ca.pem"}},
            pool_pre_ping=True,
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as e:
        st.error(f"Database connection failed ❌: {e}")
        return None

engine = get_connection()
if engine is None:
    st.stop()

# India states and GeoJSON
INDIA_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman & Nicobar Islands", "Chandigarh", "Dadra & Nagar Haveli & Daman & Diu",
    "Delhi", "Jammu & Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
]

INDIA_GEOJSON_URL = "https://raw.githubusercontent.com/plotly/datasets/master/india_states.geojson"

STATE_FIXES = {
    "Nct Of Delhi": "Delhi",
    "Odissa": "Odisha",
    "Orissa": "Odisha",
    "Pondicherry": "Puducherry",
    "Jammu And Kashmir": "Jammu & Kashmir",
    "Dadra And Nagar Haveli And Daman And Diu": "Dadra & Nagar Haveli & Daman & Diu",
    "Andaman & Nicobar Islands": "Andaman & Nicobar Islands",
    "Andaman And Nicobar Islands": "Andaman & Nicobar Islands",
    "Uttaranchal": "Uttarakhand",
}

def normalize_state_for_geojson(name: str) -> str:
    if not isinstance(name, str):
        return name
    s = name.strip()
    s = " ".join([w.capitalize() if w.lower() not in {"&", "and"} else w for w in s.split()])
    return STATE_FIXES.get(s, s)

# Sidebar navigation
st.sidebar.title("Navigation")
CASE_STUDIES = [
    "Decoding Transaction Dynamics on PhonePe",
    "Device Dominance and User Engagement Analysis",
    "Insurance Penetration and Growth Potential",
    "Transaction Analysis for Market Expansion",
    "User Engagement and Growth Strategy",
    "Insurance Engagement Analysis",
]
selected_case = st.sidebar.selectbox("Choose Case Study", CASE_STUDIES)

# Load years and quarters
@st.cache_data(ttl=600)
def load_years_quarters():
    q = text("SELECT DISTINCT Year, Quater FROM Aggre_transaction ORDER BY Year, Quater;")
    with engine.connect() as conn:
        df = pd.read_sql_query(q, conn)
    return df

yq_df = load_years_quarters()
ALL_YEARS = sorted(yq_df["Year"].unique().tolist())
ALL_QUARTERS = sorted(yq_df["Quater"].unique().tolist())

# Sidebar filters
with st.sidebar.expander("Filters", expanded=True):
    sel_years = st.multiselect("Year(s)", ALL_YEARS, default=ALL_YEARS)
    sel_quarters = st.multiselect("Quarter(s)", ALL_QUARTERS, default=ALL_QUARTERS)
    sel_states = st.multiselect("State(s)", INDIA_STATES, default=INDIA_STATES)

# Reset filters button
with st.sidebar:
    if st.button("Reset Filters"):
        sel_years = ALL_YEARS
        sel_quarters = ALL_QUARTERS
        sel_states = INDIA_STATES

# Validate filters
if not sel_years or not sel_quarters or not sel_states:
    st.warning("Please select at least one Year, Quarter, and State from the sidebar.")
    st.stop()

# Utility function to find column names
def find_column(table: str, candidates: list) -> str | None:
    sql = text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = :schema AND table_name = :table"
    )
    with engine.connect() as conn:
        res = conn.execute(sql, {"schema": engine.url.database, "table": table}).fetchall()
    cols = [r[0] for r in res]
    cols_lower = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in cols_lower:
            return cols_lower[cand.lower()]
    st.warning(f"No matching column found for {table} in candidates: {candidates}")
    return None

# Data loading functions
@st.cache_data(ttl=600)
def load_user_statewise(years: list, quarters: list, states: list):
    state_col = find_column('Map_user', ['state', 'State']) or 'State'
    year_col = find_column('Map_user', ['year', 'Year']) or 'Year'
    quarter_col = find_column('Map_user', ['quarter', 'Quarter']) or 'Quarter'
    users_col = find_column('Map_user', ['registeredUsers', 'registered_users', 'Registered_users', 'RegisteredUsers'])
    opens_col = find_column('Map_user', ['number_appOpens', 'appOpens', 'app_opens', 'App_opens', 'AppOpens'])
    if not users_col or not opens_col:
        st.warning(f"Columns not found in Map_user: users_col={users_col}, opens_col={opens_col}")
        return pd.DataFrame(columns=[state_col, 'Users', 'AppOpens'])
    q = text(
        f"SELECT {state_col} AS State, SUM({users_col}) AS Users, SUM({opens_col}) AS AppOpens "
        f"FROM Map_user WHERE {year_col} IN :years AND {quarter_col} IN :quarters AND {state_col} IN :states "
        f"GROUP BY {state_col};"
    )
    with engine.connect() as conn:
        return pd.read_sql_query(q, conn, params={"years": tuple(years), "quarters": tuple(quarters), "states": tuple(states)})

@st.cache_data(ttl=600)
def load_user_yearly(quarters: list):
    year_col = find_column('Map_user', ['year', 'Year']) or 'Year'
    quarter_col = find_column('Map_user', ['quarter', 'Quarter']) or 'Quarter'
    users_col = find_column('Map_user', ['registeredUsers', 'registered_users', 'Registered_users', 'RegisteredUsers'])
    opens_col = find_column('Map_user', ['number_appOpens', 'appOpens', 'app_opens', 'App_opens', 'AppOpens'])
    if not users_col or not opens_col:
        st.warning(f"Columns not found in Map_user: users_col={users_col}, opens_col={opens_col}")
        return pd.DataFrame(columns=[year_col, 'Users', 'AppOpens'])
    q = text(
        f"SELECT {year_col} AS Year, SUM({users_col}) AS Users, SUM({opens_col}) AS AppOpens "
        f"FROM Map_user WHERE {quarter_col} IN :quarters "
        f"GROUP BY {year_col} ORDER BY {year_col};"
    )
    with engine.connect() as conn:
        return pd.read_sql_query(q, conn, params={"quarters": tuple(quarters)})

@st.cache_data(ttl=600)
def load_user_brand(state: str | None, years: list, quarters: list):
    brand_col = find_column('Aggre_user', ['brand', 'Brand']) or 'Brand'
    count_col = find_column('Aggre_user', ['count', 'Count'])
    state_col = find_column('Aggre_user', ['state', 'State']) or 'State'
    year_col = find_column('Aggre_user', ['year', 'Year']) or 'Year'
    quater_col = find_column('Aggre_user', ['quater', 'Quater']) or 'Quater'
    if not count_col:
        st.warning(f"Column not found in Aggre_user: count_col={count_col}")
        return pd.DataFrame(columns=[brand_col, 'Users'])
    where_clause = f"WHERE {year_col} IN :years AND {quater_col} IN :quarters"
    params = {"years": tuple(years), "quarters": tuple(quarters)}
    if state:
        where_clause += f" AND {state_col} = :state"
        params['state'] = state
    q = text(
        f"SELECT {brand_col} AS Brand, SUM({count_col}) AS Users "
        f"FROM Aggre_user {where_clause} GROUP BY {brand_col};"
    )
    with engine.connect() as conn:
        return pd.read_sql_query(q, conn, params=params)

@st.cache_data(ttl=600)
def load_insurance_statewise(years: list, quarters: list, states: list):
    state_col = find_column('Map_insurance', ['state', 'State']) or 'State'
    year_col = find_column('Map_insurance', ['year', 'Year']) or 'Year'
    quarter_col = find_column('Map_insurance', ['quarter', 'Quarter']) or 'Quarter'
    cnt_col = find_column('Map_insurance', ['insurance_count', 'Insurance_count', 'transaction_count', 'transactionCount'])
    amt_col = find_column('Map_insurance', ['insurance_amount', 'Insurance_amount', 'transaction_amount', 'transactionAmount'])
    if not cnt_col or not amt_col:
        st.warning(f"Columns not found in Map_insurance: cnt_col={cnt_col}, amt_col={amt_col}")
        return pd.DataFrame(columns=[state_col, 'Insurance_count', 'Insurance_amount'])
    q = text(
        f"SELECT {state_col} AS State, SUM({cnt_col}) AS Insurance_count, SUM({amt_col}) AS Insurance_amount "
        f"FROM Map_insurance WHERE {year_col} IN :years AND {quarter_col} IN :quarters AND {state_col} IN :states "
        f"GROUP BY {state_col};"
    )
    with engine.connect() as conn:
        return pd.read_sql_query(q, conn, params={"years": tuple(years), "quarters": tuple(quarters), "states": tuple(states)})

@st.cache_data(ttl=600)
def load_insurance_yearly(quarters: list):
    year_col = find_column('Map_insurance', ['year', 'Year']) or 'Year'
    quarter_col = find_column('Map_insurance', ['quarter', 'Quarter']) or 'Quarter'
    cnt_col = find_column('Map_insurance', ['insurance_count', 'Insurance_count', 'transaction_count', 'transactionCount'])
    amt_col = find_column('Map_insurance', ['insurance_amount', 'Insurance_amount', 'transaction_amount', 'transactionAmount'])
    if not cnt_col or not amt_col:
        st.warning(f"Columns not found in Map_insurance: cnt_col={cnt_col}, amt_col={amt_col}")
        return pd.DataFrame(columns=[year_col, 'Insurance_count', 'Insurance_amount'])
    q = text(
        f"SELECT {year_col} AS Year, SUM({cnt_col}) AS Insurance_count, SUM({amt_col}) AS Insurance_amount "
        f"FROM Map_insurance WHERE {quarter_col} IN :quarters "
        f"GROUP BY {year_col} ORDER BY {year_col};"
    )
    with engine.connect() as conn:
        return pd.read_sql_query(q, conn, params={"quarters": tuple(quarters)})

@st.cache_data(ttl=600)
def load_insurance_engagement_statewise(years: list, quarters: list, states: list):
    state_col = find_column('Top_insurance', ['state', 'State']) or 'State'
    year_col = find_column('Top_insurance', ['year', 'Year']) or 'Year'
    quarter_col = find_column('Top_insurance', ['quarter', 'Quarter']) or 'Quarter'
    cnt_col = find_column('Top_insurance', ['district_count', 'insurance_count', 'transaction_count', 'transactionCount'])
    amt_col = find_column('Top_insurance', ['district_amount', 'insurance_amount', 'transaction_amount', 'transactionAmount'])
    if not cnt_col or not amt_col:
        st.warning(f"Columns not found in Top_insurance: cnt_col={cnt_col}, amt_col={amt_col}")
        return pd.DataFrame(columns=[state_col, 'Insurance_count', 'Insurance_amount'])
    q = text(
        f"SELECT {state_col} AS State, SUM({cnt_col}) AS Insurance_count, SUM({amt_col}) AS Insurance_amount "
        f"FROM Top_insurance WHERE {year_col} IN :years AND {quarter_col} IN :quarters AND {state_col} IN :states "
        f"GROUP BY {state_col};"
    )
    with engine.connect() as conn:
        return pd.read_sql_query(q, conn, params={"years": tuple(years), "quarters": tuple(quarters), "states": tuple(states)})

@st.cache_data(ttl=600)
def load_insurance_engagement_yearly(quarters: list):
    year_col = find_column('Top_insurance', ['year', 'Year']) or 'Year'
    quarter_col = find_column('Top_insurance', ['quarter', 'Quarter']) or 'Quarter'
    cnt_col = find_column('Top_insurance', ['district_count', 'insurance_count', 'transaction_count', 'transactionCount'])
    amt_col = find_column('Top_insurance', ['district_amount', 'insurance_amount', 'transaction_amount', 'transactionAmount'])
    if not cnt_col or not amt_col:
        st.warning(f"Columns not found in Top_insurance: cnt_col={cnt_col}, amt_col={amt_col}")
        return pd.DataFrame(columns=[year_col, 'Insurance_count', 'Insurance_amount'])
    q = text(
        f"SELECT {year_col} AS Year, SUM({cnt_col}) AS Insurance_count, SUM({amt_col}) AS Insurance_amount "
        f"FROM Top_insurance WHERE {quarter_col} IN :quarters "
        f"GROUP BY {year_col} ORDER BY {year_col};"
    )
    with engine.connect() as conn:
        return pd.read_sql_query(q, conn, params={"quarters": tuple(quarters)})

@st.cache_data(ttl=600)
def load_tran_statewise_from_map(years: list, quarters: list, states: list):
    state_col = find_column('Map_transaction', ['state', 'State']) or 'State'
    year_col = find_column('Map_transaction', ['year', 'Year']) or 'Year'
    quarter_col = find_column('Map_transaction', ['quarter', 'Quarter']) or 'Quarter'
    cnt_col = find_column('Map_transaction', ['Transaction_count', 'transaction_count', 'transactionCount'])
    amt_col = find_column('Map_transaction', ['Transaction_amount', 'transaction_amount', 'transactionAmount'])
    if not cnt_col or not amt_col:
        st.warning(f"Columns not found in Map_transaction: cnt_col={cnt_col}, amt_col={amt_col}")
        return pd.DataFrame(columns=[state_col, 'Transactions', 'Amount'])
    q = text(
        f"SELECT {state_col} AS State, SUM({cnt_col}) AS Transactions, SUM({amt_col}) AS Amount "
        f"FROM Map_transaction WHERE {year_col} IN :years AND {quarter_col} IN :quarters AND {state_col} IN :states "
        f"GROUP BY {state_col};"
    )
    with engine.connect() as conn:
        return pd.read_sql_query(q, conn, params={"years": tuple(years), "quarters": tuple(quarters), "states": tuple(states)})

@st.cache_data(ttl=600)
def load_tran_yearly_from_map(quarters: list):
    year_col = find_column('Map_transaction', ['year', 'Year']) or 'Year'
    quarter_col = find_column('Map_transaction', ['quarter', 'Quarter']) or 'Quarter'
    cnt_col = find_column('Map_transaction', ['Transaction_count', 'transaction_count', 'transactionCount'])
    amt_col = find_column('Map_transaction', ['Transaction_amount', 'transaction_amount', 'transactionAmount'])
    if not cnt_col or not amt_col:
        st.warning(f"Columns not found in Map_transaction: cnt_col={cnt_col}, amt_col={amt_col}")
        return pd.DataFrame(columns=[year_col, 'Transactions', 'Amount'])
    q = text(
        f"SELECT {year_col} AS Year, SUM({cnt_col}) AS Transactions, SUM({amt_col}) AS Amount "
        f"FROM Map_transaction WHERE {quarter_col} IN :quarters "
        f"GROUP BY {year_col} ORDER BY {year_col};"
    )
    with engine.connect() as conn:
        return pd.read_sql_query(q, conn, params={"quarters": tuple(quarters)})

@st.cache_data(ttl=600)
def load_top_user_statewise(years: list, quarters: list, states: list):
    state_col = find_column('Top_user', ['state', 'State']) or 'State'
    year_col = find_column('Top_user', ['year', 'Year']) or 'Year'
    quarter_col = find_column('Top_user', ['quater', 'Quater', 'quarter', 'Quarter']) or 'Quarter'
    users_col = find_column('Top_user', ['district_registeredUsers', 'registeredUsers', 'registered_users', 'Registered_users', 'RegisteredUsers'])
    if not users_col:
        st.warning(f"Column not found in Top_user: users_col={users_col}")
        return pd.DataFrame(columns=[state_col, 'TopUsers'])
    q = text(
        f"SELECT {state_col} AS State, SUM({users_col}) AS TopUsers "
        f"FROM Top_user WHERE {year_col} IN :years AND {quarter_col} IN :quarters AND {state_col} IN :states "
        f"GROUP BY {state_col};"
    )
    with engine.connect() as conn:
        return pd.read_sql_query(q, conn, params={"years": tuple(years), "quarters": tuple(quarters), "states": tuple(states)})

@st.cache_data(ttl=600)
def load_top_user_yearly(quarters: list):
    year_col = find_column('Top_user', ['year', 'Year']) or 'Year'
    quarter_col = find_column('Top_user', ['quater', 'Quater', 'quarter', 'Quarter']) or 'Quarter'
    users_col = find_column('Top_user', ['district_registeredUsers', 'registeredUsers', 'registered_users', 'Registered_users', 'RegisteredUsers'])
    if not users_col:
        st.warning(f"Column not found in Top_user: users_col={users_col}")
        return pd.DataFrame(columns=[year_col, 'TopUsers'])
    q = text(
        f"SELECT {year_col} AS Year, SUM({users_col}) AS TopUsers "
        f"FROM Top_user WHERE {quarter_col} IN :quarters "
        f"GROUP BY {year_col} ORDER BY {year_col};"
    )
    with engine.connect() as conn:
        return pd.read_sql_query(q, conn, params={"quarters": tuple(quarters)})

@st.cache_data(ttl=600)
def load_payment_categories_statewise(years: list, quarters: list, states: list):
    state_col = find_column('Aggre_transaction', ['state', 'State']) or 'State'
    type_col = find_column('Aggre_transaction', ['Transaction_type', 'transaction_type', 'transactionType']) or 'Transaction_type'
    cnt_col = find_column('Aggre_transaction', ['Transaction_count', 'transaction_count', 'transactionCount'])
    amt_col = find_column('Aggre_transaction', ['Transaction_amount', 'transaction_amount', 'transactionAmount'])
    year_col = find_column('Aggre_transaction', ['year', 'Year']) or 'Year'
    quater_col = find_column('Aggre_transaction', ['quater', 'Quater']) or 'Quater'
    if not cnt_col or not amt_col:
        st.warning(f"Columns not found in Aggre_transaction: cnt_col={cnt_col}, amt_col={amt_col}")
        return pd.DataFrame(columns=[state_col, 'Category', 'Txn_count', 'Txn_amount'])
    q = text(
        f"SELECT {state_col} AS State, {type_col} AS Category, SUM({cnt_col}) AS Txn_count, SUM({amt_col}) AS Txn_amount "
        f"FROM Aggre_transaction WHERE {year_col} IN :years AND {quater_col} IN :quarters AND {state_col} IN :states "
        f"GROUP BY {state_col}, {type_col};"
    )
    with engine.connect() as conn:
        return pd.read_sql_query(q, conn, params={"years": tuple(years), "quarters": tuple(quarters), "states": tuple(states)})

@st.cache_data(ttl=600)
def load_payment_categories_overall(years: list, quarters: list):
    type_col = find_column('Aggre_transaction', ['Transaction_type', 'transaction_type', 'transactionType']) or 'Transaction_type'
    cnt_col = find_column('Aggre_transaction', ['Transaction_count', 'transaction_count', 'transactionCount'])
    amt_col = find_column('Aggre_transaction', ['Transaction_amount', 'transaction_amount', 'transactionAmount'])
    year_col = find_column('Aggre_transaction', ['year', 'Year']) or 'Year'
    quater_col = find_column('Aggre_transaction', ['quater', 'Quater']) or 'Quater'
    if not cnt_col or not amt_col:
        st.warning(f"Columns not found in Aggre_transaction: cnt_col={cnt_col}, amt_col={amt_col}")
        return pd.DataFrame(columns=['Category', 'Txn_count', 'Txn_amount'])
    q = text(
        f"SELECT {type_col} AS Category, SUM({cnt_col}) AS Txn_count, SUM({amt_col}) AS Txn_amount "
        f"FROM Aggre_transaction WHERE {year_col} IN :years AND {quater_col} IN :quarters "
        f"GROUP BY {type_col};"
    )
    with engine.connect() as conn:
        return pd.read_sql_query(q, conn, params={"years": tuple(years), "quarters": tuple(quarters)})

# Visualization functions
def draw_india_map(df: pd.DataFrame, value_col: str, title: str, log_scale: bool = False, color_scale: str = "Viridis"):
    if df.empty:
        st.info("No data to display for map.")
        return
    df = df.copy()
    if "State_geo" not in df.columns and "State" in df.columns:
        df["State_geo"] = df["State"].apply(normalize_state_for_geojson)
    fig = px.choropleth(
        df,
        geojson=INDIA_GEOJSON_URL,
        featureidkey="properties.ST_NM",
        locations="State_geo",
        color=value_col,
        title=title,
        color_continuous_scale=color_scale,
        range_color=[df[value_col].min(), df[value_col].max()] if not log_scale else None,
    )
    if log_scale:
        fig.update_traces(z=df[value_col].apply(lambda x: max(x, 1)))  # Avoid log(0)
        fig.update_layout(coloraxis_colorbar=dict(tickvals=[1, 10, 100, 1000, 10000], ticktext=["1", "10", "100", "1K", "10K"]))
    fig.update_geos(fitbounds="locations", visible=False)
    st.plotly_chart(fig, use_container_width=True)

def draw_top10_states(df: pd.DataFrame, metric_col: str, title: str):
    if df.empty:
        st.info("No data to display for Top 10 chart.")
        return
    top10 = df.sort_values(metric_col, ascending=False).head(10)
    fig = px.bar(top10, x="State", y=metric_col, text=metric_col, title=title)
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

# Case studies
if selected_case == "Decoding Transaction Dynamics on PhonePe":
    st.subheader("Decoding Transaction Dynamics on PhonePe (Aggre_transaction)")
    with st.spinner("Loading data..."):
        df_cat_state = load_payment_categories_statewise(sel_years, sel_quarters, sel_states)
    if not df_cat_state.empty:
        totals = df_cat_state.groupby("State", as_index=False)["Txn_amount"].sum()
        draw_india_map(totals, "Txn_amount", "Total Transaction Amount by State")
        st.download_button(
            label="Download Data as CSV",
            data=totals.to_csv(index=False),
            file_name="transaction_dynamics_state_data.csv",
            mime="text/csv",
        )
    st.markdown("### 📈 Yearly Trend by Category")
    q = text(
        """
        SELECT Year, Transaction_type AS Category,
               SUM(Transaction_amount) AS Txn_amount
        FROM Aggre_transaction
        WHERE Quater IN :quarters AND State IN :states
        GROUP BY Year, Transaction_type
        ORDER BY Year;
        """
    )
    with engine.connect() as conn:
        df_trend = pd.read_sql_query(q, conn, params={"quarters": tuple(sel_quarters), "states": tuple(sel_states)})
    if not df_trend.empty:
        fig = px.line(df_trend, x="Year", y="Txn_amount", color="Category", markers=True)
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("### 🧩 Category Share (Overall)")
    df_cat_overall = load_payment_categories_overall(sel_years, sel_quarters)
    if not df_cat_overall.empty:
        col1, col2 = st.columns(2)
        with col1:
            fig = px.pie(df_cat_overall, names="Category", values="Txn_amount", hole=0.4, title="Amount Share by Category")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.bar(df_cat_overall.sort_values("Txn_count", ascending=False), x="Category", y="Txn_count", text="Txn_count", title="Transaction Count by Category")
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)
    st.markdown("### 🧭 State-wise Performance of Payment Categories (Stacked)")
    if not df_cat_state.empty:
        totals = df_cat_state.groupby("State", as_index=False)["Txn_amount"].sum().sort_values("Txn_amount", ascending=False).head(10)
        top_states = totals["State"].tolist()
        df_top_cat = df_cat_state[df_cat_state["State"].isin(top_states)]
        fig = px.bar(df_top_cat, x="State", y="Txn_amount", color="Category", barmode="stack", title="Top 10 States — Payment Category Amount Split")
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("### 🏆 Top 10 States (Total Txn Amount)")
    if not df_cat_state.empty:
        totals = df_cat_state.groupby("State", as_index=False)["Txn_amount"].sum()
        draw_top10_states(totals, "Txn_amount", "Top 10 States by Total Transaction Amount")

elif selected_case == "Device Dominance and User Engagement Analysis":
    st.subheader("Device Dominance and User Engagement Analysis (Map_user)")
    with st.spinner("Loading data..."):
        df_user_state = load_user_statewise(sel_years, sel_quarters, sel_states)
    st.markdown("### 🗺️ Registered Users by State")
    draw_india_map(df_user_state, "Users", "Registered Users by State", color_scale="Viridis")
    st.markdown("### 🗺️ App Opens by State (Indian 2D Map)")
    draw_india_map(df_user_state, "AppOpens", "App Opens by State", log_scale=True, color_scale="Plasma")
    if not df_user_state.empty:
        st.download_button(
            label="Download Data as CSV",
            data=df_user_state.to_csv(index=False),
            file_name="user_state_data.csv",
            mime="text/csv",
        )
    st.markdown("### 📈 Yearly Growth (Users & App Opens)")
    df_user_yearly = load_user_yearly(sel_quarters)
    if not df_user_yearly.empty:
        fig = px.line(df_user_yearly, x="Year", y=["Users", "AppOpens"], markers=True)
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("### 🧩 Device Brand Distribution")
    state_opt = st.selectbox("(Optional) Filter brand distribution by a specific state:", ["-- All States --"] + sorted(df_user_state["State"].unique().tolist()) if not df_user_state.empty else ["-- All States --"])
    brand_state = None if state_opt.startswith("--") else state_opt
    df_brand = load_user_brand(brand_state, sel_years, sel_quarters)
    if not df_brand.empty:
        col1, col2 = st.columns(2)
        with col1:
            fig = px.pie(df_brand, names="Brand", values="Users", hole=0.4, title="Registered Users by Brand")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.bar(df_brand.sort_values("Users", ascending=False), x="Brand", y="Users", text="Users", title="Users by Brand")
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)
    st.markdown("### 🧭 State-wise Performance of Payment Categories (from Aggre_transaction)")
    df_cat_state = load_payment_categories_statewise(sel_years, sel_quarters, sel_states)
    if not df_cat_state.empty:
        totals = df_cat_state.groupby("State", as_index=False)["Txn_amount"].sum().sort_values("Txn_amount", ascending=False).head(10)
        top_states = totals["State"].tolist()
        df_top_cat = df_cat_state[df_cat_state["State"].isin(top_states)]
        fig = px.bar(df_top_cat, x="State", y="Txn_amount", color="Category", barmode="stack", title="Top 10 States — Payment Category Amount Split")
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("### 🏆 Top 10 States (Registered Users)")
    draw_top10_states(df_user_state, "Users", "Top 10 States by Registered Users")

elif selected_case == "Insurance Penetration and Growth Potential":
    st.subheader("Insurance Penetration and Growth Potential (Map_insurance)")
    with st.spinner("Loading data..."):
        df_ins_state = load_insurance_statewise(sel_years, sel_quarters, sel_states)
    draw_india_map(df_ins_state, "Insurance_amount", "Insurance Amount by State")
    if not df_ins_state.empty:
        st.download_button(
            label="Download Data as CSV",
            data=df_ins_state.to_csv(index=False),
            file_name="insurance_state_data.csv",
            mime="text/csv",
        )
    st.markdown("### 📈 Yearly Growth (Insurance Amount & Count)")
    df_ins_yearly = load_insurance_yearly(sel_quarters)
    if not df_ins_yearly.empty:
        fig = px.line(df_ins_yearly, x="Year", y=["Insurance_amount", "Insurance_count"], markers=True)
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("### 🧮 Top States by Insurance Amount")
    draw_top10_states(df_ins_state, "Insurance_amount", "Top 10 States by Insurance Amount")
    st.markdown("### 🧭 State-wise Performance of Payment Categories (from Aggre_transaction)")
    df_cat_state = load_payment_categories_statewise(sel_years, sel_quarters, sel_states)
    if not df_cat_state.empty:
        totals = df_cat_state.groupby("State", as_index=False)["Txn_amount"].sum().sort_values("Txn_amount", ascending=False).head(10)
        top_states = totals["State"].tolist()
        df_top_cat = df_cat_state[df_cat_state["State"].isin(top_states)]
        fig = px.bar(df_top_cat, x="State", y="Txn_amount", color="Category", barmode="stack", title="Top 10 States — Payment Category Amount Split")
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("### 🏆 Top 10 States (Insurance Count)")
    draw_top10_states(df_ins_state, "Insurance_count", "Top 10 States by Insurance Count")

elif selected_case == "Transaction Analysis for Market Expansion":
    st.subheader("Transaction Analysis for Market Expansion (Map_transaction)")
    with st.spinner("Loading data..."):
        df_map_tran = load_tran_statewise_from_map(sel_years, sel_quarters, sel_states)
    draw_india_map(df_map_tran, "Amount", "Transaction Amount by State")
    if not df_map_tran.empty:
        st.download_button(
            label="Download Data as CSV",
            data=df_map_tran.to_csv(index=False),
            file_name="transaction_state_data.csv",
            mime="text/csv",
        )
    st.markdown("### 📈 Yearly Growth (Transaction Amount & Count)")
    df_tran_yearly = load_tran_yearly_from_map(sel_quarters)
    if not df_tran_yearly.empty:
        fig = px.line(df_tran_yearly, x="Year", y=["Amount", "Transactions"], markers=True)
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("### 🧮 Top States by Transaction Amount")
    draw_top10_states(df_map_tran, "Amount", "Top 10 States by Transaction Amount")
    st.markdown("### 🧭 State-wise Performance of Payment Categories (from Aggre_transaction)")
    df_cat_state = load_payment_categories_statewise(sel_years, sel_quarters, sel_states)
    if not df_cat_state.empty:
        totals = df_cat_state.groupby("State", as_index=False)["Txn_amount"].sum().sort_values("Txn_amount", ascending=False).head(10)
        top_states = totals["State"].tolist()
        df_top_cat = df_cat_state[df_cat_state["State"].isin(top_states)]
        fig = px.bar(df_top_cat, x="State", y="Txn_amount", color="Category", barmode="stack", title="Top 10 States — Payment Category Amount Split")
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("### 🏆 Top 10 States (Transactions Count)")
    draw_top10_states(df_map_tran, "Transactions", "Top 10 States by Transaction Count")

elif selected_case == "User Engagement and Growth Strategy":
    st.subheader("User Engagement and Growth Strategy (Top_user)")
    with st.spinner("Loading data..."):
        df_top_user = load_top_user_statewise(sel_years, sel_quarters, sel_states)
    draw_india_map(df_top_user, "TopUsers", "Top Users by State")
    if not df_top_user.empty:
        st.download_button(
            label="Download Data as CSV",
            data=df_top_user.to_csv(index=False),
            file_name="top_user_state_data.csv",
            mime="text/csv",
        )
    st.markdown("### 📈 Yearly Growth (Top Users)")
    df_top_user_yearly = load_top_user_yearly(sel_quarters)
    if not df_top_user_yearly.empty:
        fig = px.line(df_top_user_yearly, x="Year", y=["TopUsers"], markers=True)
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("### 🧮 Top States by Top Users")
    draw_top10_states(df_top_user, "TopUsers", "Top 10 States by Top Users")
    st.markdown("### 🧭 State-wise Performance of Payment Categories (from Aggre_transaction)")
    df_cat_state = load_payment_categories_statewise(sel_years, sel_quarters, sel_states)
    if not df_cat_state.empty:
        totals = df_cat_state.groupby("State", as_index=False)["Txn_amount"].sum().sort_values("Txn_amount", ascending=False).head(10)
        top_states = totals["State"].tolist()
        df_top_cat = df_cat_state[df_cat_state["State"].isin(top_states)]
        fig = px.bar(df_top_cat, x="State", y="Txn_amount", color="Category", barmode="stack", title="Top 10 States — Payment Category Amount Split")
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("### 🧩 Overall Payment Category Mix (from Aggre_transaction)")
    df_cat_overall = load_payment_categories_overall(sel_years, sel_quarters)
    if not df_cat_overall.empty:
        fig = px.pie(df_cat_overall, names="Category", values="Txn_amount", hole=0.4, title="Payment Category Amount Share (Overall)")
        st.plotly_chart(fig, use_container_width=True)

elif selected_case == "Insurance Engagement Analysis":
    st.subheader("Insurance Engagement Analysis (Top_insurance)")
    with st.spinner("Loading data..."):
        df_ins_state = load_insurance_engagement_statewise(sel_years, sel_quarters, sel_states)
    draw_india_map(df_ins_state, "Insurance_amount", "Insurance Amount by State")
    if not df_ins_state.empty:
        st.download_button(
            label="Download Data as CSV",
            data=df_ins_state.to_csv(index=False),
            file_name="insurance_engagement_state_data.csv",
            mime="text/csv",
        )
    st.markdown("### 📈 Yearly Growth (Insurance Amount & Count)")
    df_ins_yearly = load_insurance_engagement_yearly(sel_quarters)
    if not df_ins_yearly.empty:
        fig = px.line(df_ins_yearly, x="Year", y=["Insurance_amount", "Insurance_count"], markers=True)
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("### 🧮 Top States by Insurance Amount")
    draw_top10_states(df_ins_state, "Insurance_amount", "Top 10 States by Insurance Amount")
    st.markdown("### 🧭 State-wise Performance of Payment Categories (from Aggre_transaction)")
    df_cat_state = load_payment_categories_statewise(sel_years, sel_quarters, sel_states)
    if not df_cat_state.empty:
        totals = df_cat_state.groupby("State", as_index=False)["Txn_amount"].sum().sort_values("Txn_amount", ascending=False).head(10)
        top_states = totals["State"].tolist()
        df_top_cat = df_cat_state[df_cat_state["State"].isin(top_states)]
        fig = px.bar(df_top_cat, x="State", y="Txn_amount", color="Category", barmode="stack", title="Top 10 States — Payment Category Amount Split")
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("### 🏆 Top 10 States (Insurance Count)")
    draw_top10_states(df_ins_state, "Insurance_count", "Top 10 States by Insurance Count")