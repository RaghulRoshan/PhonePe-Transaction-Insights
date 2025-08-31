  #📊 PhonePe Case Studies Dashboard 🚀
🌟 Overview
An interactive Streamlit dashboard to analyze PhonePe's transaction, user, and insurance data across Indian states. Features a 3D India map 🗺️ on the home page showing transaction amounts and six case studies with dynamic visualizations 📈.
📸 Screenshot of the dashboard home page showing the 3D India map with transaction amounts by state.
🔑 Key Features

🗺️ 3D India Map: Displays total transaction amounts by state (Aggre_transaction) in a 3D-like scattergeo plot (orthographic projection, Viridis scale) 🌍.
📊 Six Case Studies:
Transaction Dynamics (Aggre_transaction): Maps, trends, category shares 🧩.
Device Dominance (Map_user): User and app opens maps (2D map for app opens with Plasma scale, logarithmic) 📱.
Insurance Penetration (Map_insurance): Insurance amount/count analysis 🛡️.
Market Expansion (Map_transaction): Transaction amount/count insights 💸.
User Engagement (Top_user): Top user metrics 👥.
Insurance Engagement (Top_insurance): Insurance engagement analysis 🏦.


🎚️ Filters: Year, quarter, and state multiselect with reset button 🔄.
💾 Downloads: Export state-wise data as CSV 📄.
🛠️ State Normalization: Handles state name variations (e.g., "Odissa" → "Odisha") 🔍.

📸 Screenshot of a case study (e.g., Device Dominance) showing maps and charts.
🛠️ Prerequisites

🐍 Python: 3.8+
📦 Dependencies: streamlit, pandas, plotly, sqlalchemy, pymysql, requests
🗄️ Database: TiDB Cloud MySQL with tables: Aggre_transaction, Map_user, Map_insurance, Map_transaction, Top_user, Top_insurance, Aggre_user
🔒 SSL Certificate: ca.pem for TiDB Cloud connection

🚀 Installation

📥 Clone the Repository:
git clone https://github.com/your-username/phonepe-case-studies-dashboard.git
cd phonepe-case-studies-dashboard


📦 Install Dependencies:
pip install streamlit pandas plotly sqlalchemy pymysql requests


🔑 Update SSL Certificate Path in dashboard.py:
connect_args={"ssl": {"ca": "path/to/ca.pem"}}


🔐 (Optional) Use Streamlit Secrets for credentials:
echo '[database]' > .streamlit/secrets.toml
echo 'user = "your-user"' >> .streamlit/secrets.toml
echo 'password = "your-password"' >> .streamlit/secrets.toml
echo 'host = "your-host"' >> .streamlit/secrets.toml
echo 'port = 4000' >> .streamlit/secrets.toml
echo 'database = "phonepe"' >> .streamlit/secrets.toml
echo 'ssl_ca = "path/to/ca.pem"' >> .streamlit/secrets.toml



🖥️ Usage

▶️ Run the Dashboard:
streamlit run dashboard.py


🔎 Explore:

View the 3D map 🗺️ on the home page.
Select a case study from the sidebar 📋.
Filter by years, quarters, and states 🎚️.
Download data as CSV 💾.



📸 Screenshot of the sidebar with case study selection and filters.
🐞 Troubleshooting

🔗 Database Issues: Verify credentials and ca.pem path. Test:SELECT 1;


🗺️ 3D Map Issues: Check GeoJSON or data:SELECT State, SUM(Transaction_amount) FROM Aggre_transaction GROUP BY State;


🛠️ Column Mismatches: Verify schema:SHOW COLUMNS FROM Aggre_transaction;
SHOW COLUMNS FROM Map_user;



📜 License
MIT License. See LICENSE 📄.
