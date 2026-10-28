import streamlit as st
import mysql.connector
from mysql.connector import Error
from pymongo import MongoClient
from datetime import datetime, date
import pandas as pd

# ------------- DB CONNECTION HELPERS ----------------

@st.cache_resource
def get_mysql_conn():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="manager",   # <-- your MySQL password
            database="ewaste_db"
        )
        return conn
    except Error as e:
        st.error(f"MySQL connection error: {e}")
        return None


@st.cache_resource
def get_mongo_db():
    client = MongoClient("mongodb://localhost:27017/")
    return client["ewaste_mongo"]


mysql_conn = get_mysql_conn()
mongo_db = get_mongo_db()

# ------------- CITIZEN PAGES ----------------

def page_citizen_create_pickup():
    st.header("Request E-Waste Pickup")

    user_id = st.number_input("User ID", min_value=1, step=1)
    pickup_address = st.text_area("Pickup Address")
    city = st.text_input("City", value="Bengaluru")
    slot = st.selectbox("Preferred Slot", ["Morning", "Afternoon", "Evening"])

    if st.button("Submit Pickup Request"):
        if mysql_conn is None:
            st.error("No MySQL connection.")
            return

        if not pickup_address.strip():
            st.error("Pickup address is required.")
            return

        cursor = mysql_conn.cursor()
        try:
            cursor.callproc(
                "sp_create_pickup_request",
                (int(user_id), pickup_address, city, slot)
            )
            mysql_conn.commit()

            # Log to MongoDB
            mongo_db["user_activity_logs"].insert_one({
                "user_id": int(user_id),
                "action": "Created Pickup Request",
                "pickup_address": pickup_address,
                "city": city,
                "preferred_slot": slot,
                "timestamp": datetime.utcnow()
            })

            st.success("Pickup request created successfully.")
        except Error as e:
            mysql_conn.rollback()
            st.error(f"MySQL error: {e}")
        finally:
            cursor.close()


def page_citizen_view_requests():
    st.header("My Pickup Requests")

    email = st.text_input("Registered Email")

    if st.button("Fetch Requests"):
        if mysql_conn is None:
            st.error("No MySQL connection.")
            return

        if not email.strip():
            st.error("Email is required.")
            return

        cursor = mysql_conn.cursor(dictionary=True)
        sql = """
            SELECT p.request_id, p.pickup_address, p.city, p.request_date,
                   p.preferred_slot, p.status
            FROM pickup_request p
            JOIN users u ON p.user_id = u.user_id
            WHERE u.email = %s
            ORDER BY p.request_date DESC;
        """
        cursor.execute(sql, (email,))
        rows = cursor.fetchall()
        cursor.close()

        if not rows:
            st.info("No pickup requests found for this email.")
        else:
            st.dataframe(rows)


# ------------- ADMIN PAGES ----------------

def page_admin_dashboard():
    st.header("Center Admin Dashboard")

    center_id = st.number_input("Center ID", min_value=1, step=1)

    if st.button("Load Center Summary"):
        if mysql_conn is None:
            st.error("No MySQL connection.")
            return

        cursor = mysql_conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT center_name, capacity_kg, current_load_kg,
                   ROUND((current_load_kg / capacity_kg) * 100, 2) AS utilization_pct
            FROM collection_center
            WHERE center_id = %s
        """, (center_id,))
        center_info = cursor.fetchone()

        cursor.execute("""
            SELECT COUNT(*) AS total_items,
                   SUM(weight_kg) AS total_weight
            FROM ewaste_item
            WHERE center_id = %s
        """, (center_id,))
        item_stats = cursor.fetchone()

        cursor.close()

        if not center_info:
            st.error("Center not found.")
            return

        # Convert Decimal -> float/str for Streamlit metric
        capacity = float(center_info["capacity_kg"]) if center_info["capacity_kg"] is not None else 0.0
        current_load = float(center_info["current_load_kg"]) if center_info["current_load_kg"] is not None else 0.0
        utilization = float(center_info["utilization_pct"]) if center_info["utilization_pct"] is not None else 0.0

        total_items = int(item_stats["total_items"] or 0)
        total_weight = float(item_stats["total_weight"]) if item_stats["total_weight"] is not None else 0.0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Center", center_info["center_name"])
        col2.metric("Capacity (kg)", f"{capacity:.2f}")
        col3.metric("Current Load (kg)", f"{current_load:.2f}")
        col4.metric("Utilization (%)", f"{utilization:.2f}")

        st.write("**Total Items:**", total_items)
        st.write("**Total Item Weight (kg):**", f"{total_weight:.2f}")


def page_admin_add_item():
    st.header("Add E-Waste Item (Demo Trigger)")

    if mysql_conn is None:
        st.error("No MySQL connection.")
        return

    st.caption("Inserting an item here will fire the trigger that updates center load.")

    request_id_input = st.text_input("Request ID (optional, leave blank for drop-off)")
    center_id = st.number_input("Center ID", min_value=1, step=1)
    category_id = st.number_input("Category ID", min_value=1, step=1)
    brand = st.text_input("Brand")
    model = st.text_input("Model")
    weight = st.number_input("Weight (kg)", min_value=0.1, step=0.1)
    item_condition = st.selectbox("Condition", ["Working", "Damaged", "Scrap"])
    intake_type = st.selectbox("Intake Type", ["Pickup", "Dropoff"])
    intake_date_val = st.date_input("Intake Date", value=date.today())

    if st.button("Insert Item"):
        if mysql_conn is None:
            st.error("No MySQL connection.")
            return

        cursor = mysql_conn.cursor()
        try:
            request_id = None
            if request_id_input.strip():
                request_id = int(request_id_input)

            sql = """
                INSERT INTO ewaste_item
                    (request_id, center_id, category_id, brand, model,
                     weight_kg, item_condition, intake_type, intake_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                request_id,
                int(center_id),
                int(category_id),
                brand if brand.strip() else None,
                model if model.strip() else None,
                float(weight),
                item_condition,
                intake_type,
                intake_date_val.isoformat()
            )
            cursor.execute(sql, params)
            mysql_conn.commit()

            st.success("Item inserted successfully. Center load updated by trigger.")

        except Error as e:
            mysql_conn.rollback()
            st.error(f"MySQL error: {e}")
        finally:
            cursor.close()


def page_admin_batches():
    st.header("Recycling Batches")

    if mysql_conn is None:
        st.error("No MySQL connection.")
        return

    cursor = mysql_conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT batch_id, center_id, batch_date, total_weight_kg,
               treatment_type, status
        FROM recycling_batch
        ORDER BY batch_date DESC;
    """)
    batches = cursor.fetchall()
    cursor.close()

    if not batches:
        st.info("No recycling batches found. Insert rows in MySQL to demo this.")
        return

    st.subheader("All Batches")
    st.dataframe(batches)

    batch_ids = [b["batch_id"] for b in batches]
    selected_batch = st.selectbox("Select a batch to view MongoDB logs:", batch_ids)

    if selected_batch:
        log = mongo_db["recycling_logs"].find_one({"batch_id": int(selected_batch)})
        st.subheader(f"Recycling Log for Batch {selected_batch}")
        if log and "events" in log:
            for ev in log["events"]:
                st.write(f"- {ev.get('time')}: {ev.get('action')}")
        else:
            st.info("No log found in MongoDB for this batch.")


def page_admin_iot():
    st.header("IoT Weight Scan Analytics")

    center_id = st.number_input("Center ID", min_value=1, step=1, key="iot_center")

    if st.button("Load IoT Analytics"):
        pipeline = [
            {"$match": {"center_id": int(center_id)}},
            {"$group": {
                "_id": {
                    "date": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$timestamp"
                        }
                    }
                },
                "total_scans": {"$sum": 1},
                "total_weight": {"$sum": "$weight_kg"}
            }},
            {"$sort": {"_id.date": 1}}
        ]

        results = list(mongo_db["iot_weight_scans"].aggregate(pipeline))

        if not results:
            st.info("No IoT data available for this center in MongoDB.")
            return

        dates = [r["_id"]["date"] for r in results]
        weights = [r["total_weight"] for r in results]
        scans = [r["total_scans"] for r in results]

        df = pd.DataFrame({
            "date": dates,
            "total_weight_kg": weights,
            "total_scans": scans
        }).set_index("date")

        st.subheader("Daily Total Weight (kg)")
        st.line_chart(df["total_weight_kg"])

        st.subheader("Daily Scan Count")
        st.bar_chart(df["total_scans"])


def page_admin_show_all():
    st.header(" Show All Database Tables")

    if mysql_conn is None:
        st.error("MySQL connection not available.")
        return

    tables = [
        "users",
        "collection_center",
        "ewaste_category",
        "pickup_request",
        "ewaste_item",
        "recycling_batch",
        "batch_item"
    ]

    cursor = mysql_conn.cursor(dictionary=True)

    for table in tables:
        st.subheader(f" {table}")
        cursor.execute(f"SELECT * FROM {table};")
        rows = cursor.fetchall()

        if rows:
            st.dataframe(rows, use_container_width=True)
        else:
            st.info(f"No data found in {table}")

        st.markdown("---")

    cursor.close()


# ------------- MAIN APP ----------------

def main():
    st.title("E-Waste Recycling Management System")

    role = st.sidebar.selectbox("Role", ["Citizen", "Center Admin"])

    if role == "Citizen":
        page = st.sidebar.radio("Citizen Pages", ["Request Pickup", "View My Requests"])
        if page == "Request Pickup":
            page_citizen_create_pickup()
        else:
            page_citizen_view_requests()

    else:  # Center Admin
        page = st.sidebar.radio(
            "Admin Pages",
            [
                "Dashboard",
                "Add E-Waste Item",
                "Recycling Batches",
                "IoT Weight Scans",
                "Show All Data"
            ]
        )
        if page == "Dashboard":
            page_admin_dashboard()
        elif page == "Add E-Waste Item":
            page_admin_add_item()
        elif page == "Recycling Batches":
            page_admin_batches()
        elif page == "IoT Weight Scans":
            page_admin_iot()
        elif page == "Show All Data":
            page_admin_show_all()


if __name__ == "__main__":
    main()
