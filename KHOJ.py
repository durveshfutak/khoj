import streamlit as st
import mysql.connector
import bcrypt

# Database Connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="khoj_db1"
)
cursor = conn.cursor()

# Drop existing tables
cursor.execute("DROP TABLE IF EXISTS lost_found")
cursor.execute("DROP TABLE IF EXISTS medical_assistance")
cursor.execute("DROP TABLE IF EXISTS womens_safety")

# Create Users Table
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    password VARCHAR(255),
    role ENUM('USER', 'VOLUNTEER')
)''')

# Create Lost & Found Table with updated status options
cursor.execute('''CREATE TABLE IF NOT EXISTS lost_found (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(100),
    train_number VARCHAR(50),
    compartment_number VARCHAR(50),
    seat_number VARCHAR(50),
    item_description TEXT,
    phone_number VARCHAR(15),
    status ENUM('Pending', 'Received', 'Assigned to Volunteer', 'Searching', 'Found', 'Out for Delivery', 'Resolved') DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

# Create Medical Assistance Table
cursor.execute('''CREATE TABLE IF NOT EXISTS medical_assistance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(100),
    symptoms TEXT,
    station_left VARCHAR(100),
    arriving_station VARCHAR(100),
    assistance_type VARCHAR(50),
    status ENUM('Pending', 'Received', 'Assigned to Volunteer', 'In Progress', 'Out for Assistance', 'Resolved') DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

# Create Women's Safety Table
cursor.execute('''CREATE TABLE IF NOT EXISTS womens_safety (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(100),
    boarding_station VARCHAR(100),
    destination_station VARCHAR(100),
    time_of_boarding VARCHAR(50),
    phone_number VARCHAR(15),
    status ENUM('Pending', 'Received', 'Assigned to Volunteer', 'In Progress', 'Assistance Dispatched', 'Resolved') DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

conn.commit()

# Function to register user
def register_user(name, email, password, role):
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    try:
        cursor.execute("INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)", 
                       (name, email, hashed_pw, role))
        conn.commit()
        return True
    except mysql.connector.IntegrityError:
        return False

# Function to authenticate user
def authenticate_user(email, password):
    cursor.execute("SELECT name, password, role FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    if user and bcrypt.checkpw(password.encode(), user[1].encode()):
        return user[0], user[2]
    return None, None

# Functions to add complaints
def add_lost_found(user_name, train_number, compartment_number, seat_number, item_description, phone_number):
    cursor.execute("""
        INSERT INTO lost_found 
        (user_name, train_number, compartment_number, seat_number, item_description, phone_number) 
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (user_name, train_number, compartment_number, seat_number, item_description, phone_number))
    conn.commit()

def add_medical_assistance(user_name, symptoms, station_left, arriving_station, assistance_type):
    cursor.execute("""
        INSERT INTO medical_assistance 
        (user_name, symptoms, station_left, arriving_station, assistance_type) 
        VALUES (%s, %s, %s, %s, %s)
    """, (user_name, symptoms, station_left, arriving_station, assistance_type))
    conn.commit()

def add_womens_safety(user_name, boarding_station, destination_station, time_of_boarding, phone_number):
    cursor.execute("""
        INSERT INTO womens_safety 
        (user_name, boarding_station, destination_station, time_of_boarding, phone_number) 
        VALUES (%s, %s, %s, %s, %s)
    """, (user_name, boarding_station, destination_station, time_of_boarding, phone_number))
    conn.commit()

# Function to get user's complaints
def get_user_complaints(user_name):
    complaints = {
        'lost_found': [],
        'medical_assistance': [],
        'womens_safety': []
    }
    
    cursor.execute("""
        SELECT id, train_number, compartment_number, seat_number, 
               item_description, phone_number, status, created_at 
        FROM lost_found 
        WHERE user_name = %s
        ORDER BY created_at DESC
    """, (user_name,))
    complaints['lost_found'] = cursor.fetchall()
    
    cursor.execute("""
        SELECT id, symptoms, station_left, arriving_station, 
               assistance_type, status, created_at 
        FROM medical_assistance 
        WHERE user_name = %s
        ORDER BY created_at DESC
    """, (user_name,))
    complaints['medical_assistance'] = cursor.fetchall()
    
    cursor.execute("""
        SELECT id, boarding_station, destination_station, 
               time_of_boarding, phone_number, status, created_at 
        FROM womens_safety 
        WHERE user_name = %s
        ORDER BY created_at DESC
    """, (user_name,))
    complaints['womens_safety'] = cursor.fetchall()
    
    return complaints

# Functions to get all complaints
def get_lost_found_complaints():
    cursor.execute("""
        SELECT id, user_name, train_number, compartment_number, seat_number, 
               item_description, phone_number, status, created_at 
        FROM lost_found 
        ORDER BY status, created_at DESC
    """)
    return cursor.fetchall()

def get_medical_assistance_complaints():
    cursor.execute("""
        SELECT id, user_name, symptoms, station_left, arriving_station, 
               assistance_type, status, created_at 
        FROM medical_assistance 
        ORDER BY status, created_at DESC
    """)
    return cursor.fetchall()

def get_womens_safety_complaints():
    cursor.execute("""
        SELECT id, user_name, boarding_station, destination_station, 
               time_of_boarding, phone_number, status, created_at 
        FROM womens_safety 
        ORDER BY status, created_at DESC
    """)
    return cursor.fetchall()

# Function to update complaint status
def update_complaint_status(table_name, complaint_id, new_status):
    # Define valid statuses for each table
    valid_statuses = {
        'lost_found': ['Pending', 'Received', 'Assigned to Volunteer', 'Searching', 'Found', 'Out for Delivery', 'Resolved'],
        'medical_assistance': ['Pending', 'Received', 'Assigned to Volunteer', 'In Progress', 'Out for Assistance', 'Resolved'],
        'womens_safety': ['Pending', 'Received', 'Assigned to Volunteer', 'In Progress', 'Assistance Dispatched', 'Resolved']
    }
    
    # Validate the status
    if new_status not in valid_statuses[table_name]:
        raise ValueError(f"Invalid status for {table_name}")
        
    cursor.execute(f"UPDATE {table_name} SET status=%s WHERE id=%s", (new_status, complaint_id))
    conn.commit()

# Streamlit UI
st.title("KHOJ - Find & Help")

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_name = ""
    st.session_state.role = ""

# Menu options based on user role
menu = st.sidebar.selectbox(
    "Menu", 
    ["Login", "Register"] if not st.session_state.logged_in 
    else (["Home", "Track Applications", "Logout"] if st.session_state.role == "USER" 
          else ["Home", "Logout"])
)

# Register Page
if menu == "Register":
    st.subheader("Register")
    name = st.text_input("Full Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Register as", ["USER", "VOLUNTEER"])
    if st.button("Register"):
        if register_user(name, email, password, role):
            st.success("Registered successfully! You can now login.")
        else:
            st.error("Email already exists. Try logging in.")

# Login Page
elif menu == "Login":
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user_name, role = authenticate_user(email, password)
        if role:
            st.session_state.logged_in = True
            st.session_state.user_name = user_name
            st.session_state.role = role
            st.success(f"Welcome, {user_name} ({role})!")
            st.experimental_rerun()
        else:
            st.error("Invalid email or password")

# Track Applications Page
elif menu == "Track Applications":
    st.subheader("Track Your Applications")
    
    complaints = get_user_complaints(st.session_state.user_name)
    
    tab1, tab2, tab3 = st.tabs(["Lost & Found", "Medical Assistance", "Women's Safety"])
    
    with tab1:
        st.write("### Lost & Found Complaints")
        if complaints['lost_found']:
            for complaint in complaints['lost_found']:
                id, train_number, compartment_number, seat_number, \
                item_description, phone_number, status, created_at = complaint
                with st.expander(f"Complaint Status: {status} - {created_at}"):
                    st.write(f"**Train Number:** {train_number}")
                    st.write(f"**Compartment:** {compartment_number}")
                    st.write(f"**Seat:** {seat_number}")
                    st.write(f"**Item:** {item_description}")
                    st.write(f"**Current Status:** {status}")
        else:
            st.info("No Lost & Found complaints found.")
    
    with tab2:
        st.write("### Medical Assistance Requests")
        if complaints['medical_assistance']:
            for complaint in complaints['medical_assistance']:
                id, symptoms, station_left, arriving_station, \
                assistance_type, status, created_at = complaint
                with st.expander(f"Request Status: {status} - {created_at}"):
                    st.write(f"**Symptoms:** {symptoms}")
                    st.write(f"**Last Station:** {station_left}")
                    st.write(f"**Arriving Station:** {arriving_station}")
                    st.write(f"**Assistance Type:** {assistance_type}")
                    st.write(f"**Current Status:** {status}")
        else:
            st.info("No Medical Assistance requests found.")
    
    with tab3:
        st.write("### Women's Safety Requests")
        if complaints['womens_safety']:
            for complaint in complaints['womens_safety']:
                id, boarding_station, destination_station, \
                time_of_boarding, phone_number, status, created_at = complaint
                with st.expander(f"Request Status: {status} - {created_at}"):
                    st.write(f"**Boarding:** {boarding_station}")
                    st.write(f"**Destination:** {destination_station}")
                    st.write(f"**Time:** {time_of_boarding}")
                    st.write(f"**Current Status:** {status}")
        else:
            st.info("No Women's Safety requests found.")

# Home Page
elif st.session_state.logged_in and menu == "Home":
    if st.session_state.role == "USER":
        st.subheader(f"Welcome {st.session_state.user_name} ({st.session_state.role})")
        
        tab1, tab2, tab3 = st.tabs(["Lost & Found", "Medical Assistance", "Women's Safety Travel"])
        
        with tab1:
            st.write("### Lost & Found")
            with st.form("lost_found_form"):
                train_number = st.text_input("Train Number or Name")
                compartment_number = st.text_input("Compartment Number")
                seat_number = st.text_input("Seat Number")
                item_description = st.text_area("Item Description")
                phone_number = st.text_input("Your Phone Number")
                submitted = st.form_submit_button("Submit")
                if submitted and all([train_number, compartment_number, seat_number, item_description, phone_number]):
                    add_lost_found(st.session_state.user_name, train_number, compartment_number, 
                                 seat_number, item_description, phone_number)
                    st.success("Lost & Found request submitted successfully!")

        with tab2:
            st.write("### Medical Assistance")
            with st.form("medical_assistance_form"):
                symptoms = st.text_area("Symptoms")
                station_left = st.text_input("Last Station Left")
                arriving_station = st.text_input("Arriving Station")
                assistance_type = st.radio("Do you need assistance?", ["Ambulance Assistance", "Volunteer Assistance"])
                submitted = st.form_submit_button("Submit")
                if submitted and all([symptoms, station_left, arriving_station, assistance_type]):
                    add_medical_assistance(st.session_state.user_name, symptoms, station_left, 
                                        arriving_station, assistance_type)
                    st.success("Medical assistance request submitted successfully!")

        with tab3:
            st.write("### Women's Safety Travel")
            with st.form("womens_safety_form"):
                boarding_station = st.text_input("Boarding Station")
                destination_station = st.text_input("Destination Station")
                time_of_boarding = st.text_input("Time of Boarding")
                phone_number = st.text_input("Your Phone Number")
                submitted = st.form_submit_button("Submit")
                if submitted and all([boarding_station, destination_station, time_of_boarding, phone_number]):
                    add_womens_safety(st.session_state.user_name, boarding_station, destination_station, 
                                    time_of_boarding, phone_number)
                    st.success("Women's Safety Travel details submitted successfully!")

    # Volunteer Dashboard
    elif st.session_state.role == "VOLUNTEER":
        st.subheader("Volunteer Dashboard")
        
        tab1, tab2, tab3 = st.tabs(["Lost & Found", "Medical Assistance", "Women's Safety"])
        
        with tab1:
            st.write("### Lost & Found Complaints")
            complaints = get_lost_found_complaints()
            for complaint in complaints:
                id, user_name, train_number, compartment_number,seat_number, item_description, phone_number, status, created_at = complaint
                
                with st.expander(f"Lost & Found - {status} (by {user_name}) - {created_at}"):
                    st.write(f"**Train Number:** {train_number}")
                    st.write(f"**Compartment:** {compartment_number}")
                    st.write(f"**Seat:** {seat_number}")
                    st.write(f"**Item:** {item_description}")
                    st.write(f"**Phone:** {phone_number}")
                    st.write(f"**Current Status:** {status}")
                    
                    if status != "Resolved":
                        status_options = [
                            'Pending',
                            'Received',
                            'Assigned to Volunteer',
                            'Searching',
                            'Found',
                            'Out for Delivery',
                            'Resolved'
                        ]
                        new_status = st.selectbox(
                            "Update Status",
                            status_options,
                            key=f"lf_status_{id}"
                        )
                        if st.button(f"Update Status", key=f"lf_{id}"):
                            update_complaint_status("lost_found", id, new_status)
                            st.success("Status updated successfully!")
                            st.experimental_rerun()
        
        with tab2:
            st.write("### Medical Assistance Requests")
            complaints = get_medical_assistance_complaints()
            for complaint in complaints:
                id, user_name, symptoms, station_left, arriving_station, \
                assistance_type, status, created_at = complaint
                
                with st.expander(f"Medical Assistance - {status} (by {user_name}) - {created_at}"):
                    st.write(f"**Symptoms:** {symptoms}")
                    st.write(f"**Last Station:** {station_left}")
                    st.write(f"**Arriving Station:** {arriving_station}")
                    st.write(f"**Assistance Type:** {assistance_type}")
                    st.write(f"**Current Status:** {status}")
                    
                    if status != "Resolved":
                        status_options = [
                            'Pending',
                            'Received',
                            'Assigned to Volunteer',
                            'In Progress',
                            'Out for Assistance',
                            'Resolved'
                        ]
                        new_status = st.selectbox(
                            "Update Status",
                            status_options,
                            key=f"ma_status_{id}"
                        )
                        if st.button(f"Update Status", key=f"ma_{id}"):
                            update_complaint_status("medical_assistance", id, new_status)
                            st.success("Status updated successfully!")
                            st.experimental_rerun()
        
        with tab3:
            st.write("### Women's Safety Travel Requests")
            complaints = get_womens_safety_complaints()
            for complaint in complaints:
                id, user_name, boarding_station, destination_station, \
                time_of_boarding, phone_number, status, created_at = complaint
                
                with st.expander(f"Women's Safety - {status} (by {user_name}) - {created_at}"):
                    st.write(f"**Boarding Station:** {boarding_station}")
                    st.write(f"**Destination Station:** {destination_station}")
                    st.write(f"**Time of Boarding:** {time_of_boarding}")
                    st.write(f"**Phone Number:** {phone_number}")
                    st.write(f"**Current Status:** {status}")
                    
                    if status != "Resolved":
                        status_options = [
                            'Pending',
                            'Received',
                            'Assigned to Volunteer',
                            'In Progress',
                            'Assistance Dispatched',
                            'Resolved'
                        ]
                        new_status = st.selectbox(
                            "Update Status",
                            status_options,
                            key=f"ws_status_{id}"
                        )
                        if st.button(f"Update Status", key=f"ws_{id}"):
                            update_complaint_status("womens_safety", id, new_status)
                            st.success("Status updated successfully!")
                            st.experimental_rerun()

# Logout
elif menu == "Logout":
    st.session_state.logged_in = False
    st.session_state.user_name = ""
    st.session_state.role = ""
    st.success("Logged out successfully.")
    st.experimental_rerun()