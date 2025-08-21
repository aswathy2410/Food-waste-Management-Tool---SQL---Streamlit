# app.py
import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px

# Establish Connections
def get_connection(host, port, user, password, database):
    return mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="Lathagopal@22",
        database="foodDB",
        autocommit=True,
    )

def run_query(conn, sql, params=None):
    cur = conn.cursor()
    cur.execute(sql, params or [])
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description] if cur.description else []
    cur.close()
    return pd.DataFrame(rows, columns=cols)

def exec_write(conn, sql, params=None):
    cur = conn.cursor()
    cur.execute(sql, params or [])
    affected = cur.rowcount
    cur.close()
    return affected

def get_distinct(conn, table, col, where_clause=None, params=None):
    sql = f"SELECT DISTINCT {col} FROM {table}"
    if where_clause:
        sql += f" WHERE {where_clause}"
    sql += f" ORDER BY {col}"
    df = run_query(conn, sql, params)
    return ["(All)"] + df[col].dropna().astype(str).tolist()

def convert_params(params):
    return [p.item() if hasattr(p, "item") else p for p in params]


# -----------------------------------------------------------
# UI SETUP

st.set_page_config(page_title="Too Good To Waste - Food Management Website", layout="wide")
st.title("Too Good To Waste - Food Management Website")

with st.sidebar:
    st.subheader("Connect to the Database")
    host = st.text_input("Host", value="localhost")
    port = st.number_input("Port", value=3306, step=1)
    user = st.text_input("User", value="root")
    password = st.text_input("Password", type="password", value="Lathagopal@22")
    database = st.text_input("Database", value="foodDB")
    connected = st.button("Connect")

# Keep connection in session
if "conn" not in st.session_state:
    st.session_state.conn = None

if connected:
    try:
        st.session_state.conn = get_connection(host, port, user, password, database)
        st.success("Connected to Food Database.")
    except Exception as e:
        st.session_state.conn = None
        st.error(f"[Unverified] Connection failed: {e}")

if st.session_state.conn is None:
    st.info("Connect to the Food Database to Begin.")
    st.stop()

conn = st.session_state.conn

# -------------------------------------------------------------------------------------------
# TABS
tab1, tab2, tab3= st.tabs([
    "Overview",
    "🔎 Find Your Food",
    "SQL Insights"
])

# --------------------------------------------------------------------------------------------
# TAB 1: Overview
with tab1:
    st.subheader("Overview")
    
    # Show full dataset initially
    df_full = run_query(conn, """
        SELECT
            f.Food_ID,
            f.Food_Name,
            f.Quantity,
            f.Expiry_Date,
            f.Provider_ID,
            f.Provider_Type,
            f.Location,
            f.Food_Type,
            f.Meal_Type,
            p.Name AS Provider_Name,
            p.Address,
            p.Contact
        FROM food_listings_data f
        LEFT JOIN providers_data p ON f.Provider_ID = p.Provider_ID
    """)
    st.write("### All Food Listings")
    st.dataframe(df_full, use_container_width=True)
    

    # categories Available 
    if not df_full.empty:
        chart_by = st.selectbox("Categories by", ["Food_Type", "Location", "Meal_Type","Food_Name"])
        if chart_by in df_full.columns and "Quantity" in df_full.columns:
            chart_data = df_full.groupby(chart_by, dropna=False)["Quantity"].sum().reset_index()
            fig = px.bar(chart_data, x=chart_by, y="Quantity", title=f"Total Quantity by {chart_by}")
            st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------------------------------------------------------------------------
# TAB 2: CHOOSE FOOD & CONTACT PROVIDER
with tab2:
    st.header("Find Food Near You")
    
    # 1. Filter by Location first
    locations = get_distinct(conn, "food_listings_data", "Location")
    locations = ["(All)"] + sorted([loc for loc in locations if loc != "(All)"])
    f_location = st.selectbox("Location", locations)

    # 2. Fetch Food Names available in selected Location
    if f_location != "(All)":
        food_names_q = get_distinct(
            conn,
            "food_listings_data",
            "Food_Name",
            where_clause="Location = %s",
            params=[f_location]
        )
    else:
        # If all locations, fetch all food names
        food_names_q = get_distinct(conn, "food_listings_data", "Food_Name")
    
    food_names_q = [name for name in food_names_q if name != "(All)"]
    food_names_q = sorted(set(food_names_q))
    food_names = ["(All)"] + food_names_q
    f_food_name = st.selectbox("Food Name", food_names)

    # 3. Build filters for the main query
    filters = []
    params = []

    if f_location != "(All)":
        filters.append("f.Location = %s")
        params.append(f_location)

    if f_food_name != "(All)":
        filters.append("f.Food_Name = %s")
        params.append(f_food_name)

    # 4. Prepare WHERE clause
    if filters:
        where_sql = "WHERE " + " AND ".join(filters)
    else:
        where_sql = ""

    # 5. Fetch matching listings
    sql = f"""
        SELECT
            f.Food_ID,
            f.Food_Name,
            f.Quantity,
            f.Expiry_Date,
            f.Provider_ID,
            f.Provider_Type,
            f.Location,
            f.Food_Type,
            f.Meal_Type,
            p.Name AS Provider_Name,
            p.Address,
            p.Contact
        FROM food_listings_data f
        LEFT JOIN providers_data p ON f.Provider_ID = p.Provider_ID
        {where_sql}
        ORDER BY f.Expiry_Date
    """

    # Convert params
    final_params = convert_params(params)
    listings = run_query(conn, sql, final_params)

    # 6. Display table with "Select" buttons
    st.subheader("Matching Food Listings")
    selected_provider_info = None

    for idx, row in listings.iterrows():
        cols = st.columns([8, 2])
        with cols[0]:
            expiry_str = row['Expiry_Date']
            st.write(f"{row['Food_Name']} (Expires: {expiry_str})|  from {row['Provider_Name']} | at {row['Location']}")
        with cols[1]:
            btn_label = f"Select_{row['Food_ID']}"
            if st.button("Select", key=btn_label):
                selected_provider_info = {
                    'Address': row['Address'],
                    'Contact': row['Contact']
                }

    # 7. Show contact info when selected
    if selected_provider_info:
        st.markdown("### Provider Contact Info")
        st.write(f"**Address:** {selected_provider_info['Address']}")
        st.write(f"**Contact Number:** {selected_provider_info['Contact']}")
        st.markdown(f'<a href="tel:{row["Contact"]}" style="background-color: red; color: white; padding: 4px 8px; border-radius: 4px; text-decoration: none;">Call</a>', unsafe_allow_html=True)
        st.info("Contact the provider for assistance.")


# ------------------------------------------------------------------------------------------------------------
# TAB 3: INSIGHTS FROM ANALYSIS
with tab3:
    st.subheader("SQL Analysis Insights")

    QUERIES = {
        "1) Number of Providers in Each City": """
            Select City, count(Provider_ID) from providers_data group by City;
        """,
        "2) Number of Receivers in Each City": """
            Select City, count(Receiver_ID) from receivers_data group by City;
        """,
        "3) Type of Food Provider Contributing the Most": """
            Select Provider_Type, sum(Quantity) as total_contributed from food_listings_data 
            group by provider_type order by total_contributed desc limit 1;
        """,
        "4) Receivers who Claimed the Most Food": """
            Select r.Receiver_ID, r.Name, count(c.claim_id) AS total_claimed
            from claims_data c join receivers_data r on c.Receiver_ID = r.Receiver_ID 
            where c.status ='Completed' group by r.Receiver_ID, r.Name order by total_claimed DESC;
        """,
        "5) The Total Quantity of Food Available from All Providers": """
            Select sum(quantity) as total_quantity from food_listings_data;
        """,
        "6) City with the Highest Number of Food Listings": """
            Select Location, count(*) as num_of_listings from food_listings_data group by Location order by num_of_listings desc;
        """,
        "7) The Most Commonly Available Food Types": """
            Select Food_Type, count((Food_Type)) as type_count from food_listings_data group by Food_Type order by type_count desc;
        """,
        "8) Claims Made for Each Food Item": """
            Select f.Food_Name, c.Food_ID, COUNT(c.Food_ID) as num_claims 
            from claims_data c join food_listings_data f 
            on f.Food_ID = c.Food_ID group by Food_ID;
        """,
        "9) Providers with the Highest Number of Successful Food Claims": """
            Select p.Provider_ID, p.Name, count(*) as successful_claims from claims_data c
            join food_listings_data f on c.Food_ID = f.Food_ID
            join providers_data p on f.Provider_ID = p.Provider_ID
            where c.Status = 'Completed' group by p.Provider_ID, p.Name
            order by successful_claims desc;
        """,
        "10) Percentage of Food Claims (Completed vs. Pending vs. Canceled)": """
            Select Status, count(*) * 100.0 / (select count(*) from claims_data) as percentage from claims_data
            group by Status;
        """,
        "11) Average Quantity of Food Claimed per Receiver": """
            Select avg(total_claimed) as average_claimed_per_receiver from (
            select Receiver_ID, sum(case when Status = 'Completed' then 1 else 0 end) as total_claimed
            from claims_data group by Receiver_ID
            ) as receiver_totals;
        """,
        "12) Meal Type Claimed the Most": """
            Select Meal_Type, count((Meal_Type)) as type_count from food_listings_data group by Meal_Type order by type_count desc;
        """,
        "13) Total Quantity of Food Donated by Each Provider": """
            Select sum(quantity) as total_quantity from food_listings_data;
        """,
        "14) Food Listings that were Never Claimed": """
            Select * from food_listings_data where food_ID not in (Select food_ID from claims_data);
        """,
        "15) Providers with No Claims": """
            Select providers_data.* from providers_data
            join food_listings_data on providers_data.Provider_ID = food_listings_data.Provider_ID
            left join claims_data on food_listings_data.Food_ID = claims_data.Food_ID
            where claims_data.Claim_ID is null;
        """
    }

    qname = st.selectbox("Select a query", list(QUERIES.keys()))
    if st.button("Run"):
        try:
            out = run_query(conn, QUERIES[qname])
            st.write(f"**Rows: {len(out)}**")
            st.dataframe(out, use_container_width=True)
            # Quick chart if possible
            if not out.empty:
                # pick a numeric column if exists
                num_cols = out.select_dtypes(include=["number"]).columns.tolist()
                if len(out.columns) >= 2 and num_cols:
                    xcol = out.columns[0]
                    ycol = num_cols[0]
                    fig = px.bar(out, x=xcol, y=ycol, title=qname)
                    st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"[Unverified] Query failed: {e}")
