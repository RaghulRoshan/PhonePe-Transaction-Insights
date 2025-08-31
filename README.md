# PhonePe-Transaction-Insights


PhonePe Case Studies Dashboard
Overview
The PhonePe Case Studies Dashboard is an interactive web application built with Streamlit to analyze and visualize PhonePe's transaction, user engagement, and insurance data across Indian states. It provides six case studies with dynamic visualizations (maps, charts, and graphs) and supports filtering by year, quarter, and state. The dashboard now features a 3D map of India on the home page, showcasing total transaction amounts by state using a Plotly scattergeo plot with an orthographic projection.
This project connects to a MySQL database hosted on TiDB Cloud, leveraging data from tables such as Aggre_transaction, Map_user, Map_insurance, Map_transaction, Top_user, Top_insurance, and Aggre_user.
Features

3D India Map on Home Page: Displays total transaction amounts by state using Aggre_transaction data in a 3D-like scattergeo plot with orthographic projection (Viridis color scale, marker size proportional to amount).
Six Case Studies:
Decoding Transaction Dynamics (Aggre_transaction): Choropleth map, yearly trends, category share (pie/bar), and top 10 states by transaction amount.
Device Dominance and User Engagement (Map_user): Two maps (registered users and app opens, with app opens using Plasma scale and logarithmic scaling), yearly growth, device brand distribution, and top 10 states.
Insurance Penetration (Map_insurance): Choropleth map, yearly growth, and top 10 states by insurance amount/count.
Transaction Analysis for Market Expansion (Map_transaction): Choropleth map, yearly growth, and top 10 states by transaction amount/count.
User Engagement and Growth Strategy (Top_user): Choropleth map, yearly growth, and top 10 states by top users.
Insurance Engagement Analysis (Top_insurance): Choropleth map, yearly growth, and top 10 states by insurance amount/count.


Interactive Filters: Select multiple years, quarters, and states from the sidebar.
Reset Filters: Button to restore default filter selections.
Data Downloads: Export state-wise data as CSV for each case study.
State Normalization: Handles variations in state names (e.g., "Odissa" → "Odisha") using STATE_FIXES.
Dynamic Column Handling: Uses find_column to adapt to varying column names in the database.

Prerequisites

Python: 3.8 or higher
Dependencies:
streamlit
pandas
plotly
sqlalchemy
pymysql
requests (for GeoJSON fetching)


MySQL Database: Access to a TiDB Cloud MySQL database with the following tables:
Aggre_transaction: State, Year, Quater, Transaction_type, Transaction_count, Transaction_amount
Map_user: State, Year, Quarter, registeredUsers, number_appOpens
Aggre_user: State, Year, Quater, Brand, Count
Map_insurance: State, Year, Quarter, insurance_count, insurance_amount
Map_transaction: State, Year, Quarter, Transaction_count, Transaction_amount
Top_user: State, Year, Quarter, district_registeredUsers
Top_insurance: State, Year, Quarter, district_count, district_amount


SSL Certificate: Required for TiDB Cloud connection (ca.pem).

Installation

Clone the Repository:
git clone https://github.com/your-username/phonepe-case-studies-dashboard.git
cd phonepe-case-studies-dashboard


Create a Virtual Environment (optional but recommended):
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate


Install Dependencies:
pip install streamlit pandas plotly sqlalchemy pymysql requests


Download SSL Certificate:

Obtain the ca.pem file for TiDB Cloud and place it at the specified path (e.g., C:\Users\rosha\Downloads\phonepe project\ca.pem).
Update the path in dashboard.py if different:connect_args={"ssl": {"ca": "path/to/your/ca.pem"}}




Set Up Database Credentials:

The code uses hardcoded credentials for simplicity. For security, consider using Streamlit secrets:echo '[database]' > .streamlit/secrets.toml
echo 'user = "13DQLuf64nn2jC2.root"' >> .streamlit/secrets.toml
echo 'password = "Yl91nAYMjEKQwgQK"' >> .streamlit/secrets.toml
echo 'host = "gateway01.ap-southeast-1.prod.aws.tidbcloud.com"' >> .streamlit/secrets.toml
echo 'port = 4000' >> .streamlit/secrets.toml
echo 'database = "phonepe"' >> .streamlit/secrets.toml
echo 'ssl_ca = "path/to/ca.pem"' >> .streamlit/secrets.toml

Update dashboard.py to use secrets:engine = create_engine(
    f"mysql+pymysql://{st.secrets['database']['user']}:{st.secrets['database']['password']}@"
    f"{st.secrets['database']['host']}:{st.secrets['database']['port']}/{st.secrets['database']['database']}",
    connect_args={"ssl": {"ca": st.secrets['database']['ssl_ca']}},
    pool_pre_ping=True,
)





Usage

Run the Application:
streamlit run dashboard.py


Explore the Dashboard:

Home Page: View the 3D India map showing total transaction amounts by state.
Sidebar:
Select a case study from the dropdown.
Filter by years, quarters, and states using multiselect widgets.
Use the "Reset Filters" button to restore defaults.


Case Studies: Each study includes:
Choropleth maps (e.g., transaction amount, registered users, app opens).
Line charts for yearly trends.
Pie/bar charts for category or brand distributions.
Stacked bar charts for payment category splits.
Top 10 state rankings.
CSV download buttons for state-wise data.




Example Workflow:

Select "Device Dominance and User Engagement Analysis".
Choose specific years (e.g., 2023, 2024) and quarters (e.g., Q1, Q2).
Filter states (e.g., Maharashtra, Karnataka).
View the 2D map for app opens (logarithmic, Plasma scale), brand distribution, and top states.
Download the data as CSV for further analysis.



Database Schema
The dashboard queries the following tables:

Aggre_transaction: Transaction data by state, year, quarter, and type.
Columns: State, Year, Quater, Transaction_type, Transaction_count, Transaction_amount


Map_user: User engagement data.
Columns: State, Year, Quarter, registeredUsers, number_appOpens


Aggre_user: Device brand data.
Columns: State, Year, Quater, Brand, Count


Map_insurance: Insurance transaction data.
Columns: State, Year, Quarter, insurance_count, insurance_amount


Map_transaction: Transaction data by state.
Columns: State, Year, Quarter, Transaction_count, Transaction_amount


Top_user: Top user data.
Columns: State, Year, Quarter, district_registeredUsers


Top_insurance: Top insurance data.
Columns: State, Year, Quarter, district_count, district_amount



Run the following SQL to verify:
SHOW TABLES;
SHOW COLUMNS FROM Aggre_transaction;
SHOW COLUMNS FROM Map_user;
SHOW COLUMNS FROM Map_insurance;
SHOW COLUMNS FROM Map_transaction;
SHOW COLUMNS FROM Top_user;
SHOW COLUMNS FROM Top_insurance;
SHOW COLUMNS FROM Aggre_user;

Performance Optimization

Caching: Uses @st.cache_data and @st.cache_resource to cache queries and database connections (TTL: 600 seconds).
Indexes: Add indexes to improve query performance:CREATE INDEX idx_aggre_transaction_state_year_quater ON Aggre_transaction (State, Year, Quater);
CREATE INDEX idx_map_user_state_year_quarter ON Map_user (State, Year, Quarter);
CREATE INDEX idx_map_insurance_state_year_quarter ON Map_insurance (State, Year, Quarter);
CREATE INDEX idx_map_transaction_state_year_quarter ON Map_transaction (State, Year, Quarter);
CREATE INDEX idx_top_user_state_year_quarter ON Top_user (State, Year, Quarter);
CREATE INDEX idx_top_insurance_state_year_quarter ON Top_insurance (State, Year, Quarter);


GeoJSON Caching: Cache the GeoJSON file for the 3D map:@st.cache_data
def load_geojson():
    return requests.get(INDIA_GEOJSON_URL).json()
geojson = load_geojson()



Troubleshooting

Database Connection Issues:

Verify TiDB Cloud credentials and SSL certificate path.
Test connection:SELECT 1;


Ensure ca.pem is accessible and correctly referenced.


3D Map Issues:

GeoJSON Failure: If INDIA_GEOJSON_URL fails, use a local GeoJSON file:with open("india_states.geojson") as f:
    geojson = json.load(f)


Empty Map: Check data:SELECT State, SUM(Transaction_amount) FROM Aggre_transaction GROUP BY State;




Column Mismatches:

If columns like number_appOpens or Transaction_amount are missing, verify schema:SHOW COLUMNS FROM Map_user;
SHOW COLUMNS FROM Aggre_transaction;


Update find_column candidates if needed.


Slow Performance:

Reduce selected years/quarters/states for faster queries.
Increase cache TTL or use a local database replica.



Future Enhancements

Interactive 3D Map Controls:

Add a dropdown to toggle metrics (e.g., Transaction_count):metric = st.selectbox("3D Map Metric:", ["Transaction Amount", "Transaction Count"])
metric_col = "Transaction_amount" if metric == "Transaction Amount" else "Transaction_count"




Map Export:

Add PNG download for the 3D map:fig_3d.write_image("3d_map.png")
st.download_button(
    label="Download 3D Map as PNG",
    data=open("3d_map.png", "rb").read(),
    file_name="3d_map.png",
    mime="image/png",
)




District-Level Analysis:

Extend the 3D map to districts using Map_transaction and a district GeoJSON:q = text(
    "SELECT Transaction_district_name AS District, SUM(Transaction_amount) AS Transaction_amount "
    "FROM Map_transaction GROUP BY Transaction_district_name;"
)





Contributing
Contributions are welcome! Please:

Fork the repository.
Create a feature branch (git checkout -b feature/your-feature).
Commit changes (git commit -m "Add your feature").
Push to the branch (git push origin feature/your-feature).
Open a pull request.

License
This project is licensed under the MIT License. See the LICENSE file for details.
Contact
For questions or support, contact your-email@example.com or open an issue on GitHub.
