"""
Complete Pinnertest Portal - Admin report generation + Client access
"""
import streamlit as st
from db import DatabaseManager
import json
import pandas as pd

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

def check_credentials(username, password):
    """
    Check if the provided username and password are valid
    """
    # Admin access for full system management
    if username == "admin" and password == "admin":
        return "admin"
    
    # Demo client for testing
    if username == "johndoe_1990" and password == "demo123":
        st.session_state.demo_client_data = {
            'patient_name': 'John Doe',
            'patient_id': 'P12345',
            'dob': '1990-01-15',
            'gender': 'Male',
            'collection_date': '2025-05-28',
            'practitioner': 'Dr. Smith',
            'specimen_type': 'Serum',
            'email': 'john.doe@example.com',
            'allergen_data': '[{"Allergen": "Wheat", "IgG_Level": 2.1, "Classification": "Moderate"}, {"Allergen": "Milk", "IgG_Level": 0.8, "Classification": "Low"}, {"Allergen": "Eggs", "IgG_Level": 3.5, "Classification": "High"}, {"Allergen": "Peanuts", "IgG_Level": 1.2, "Classification": "Low"}, {"Allergen": "Tree Nuts", "IgG_Level": 0.4, "Classification": "Low"}, {"Allergen": "Soy", "IgG_Level": 2.8, "Classification": "Moderate"}, {"Allergen": "Fish", "IgG_Level": 0.9, "Classification": "Low"}, {"Allergen": "Shellfish", "IgG_Level": 1.6, "Classification": "Low"}]'
        }
        return "client"
    
    # Check real client database
    try:
        db_manager = DatabaseManager()
        db_manager.connect()
        
        if db_manager.connected:
            client_report = db_manager.get_client_report(username, password)
            if client_report:
                return "client"
    except Exception as e:
        print(f"Database authentication error: {e}")
    
    return False

def login_page():
    """
    Render the login page
    """
    st.markdown("""
    <div class="main-header">
        <h1>🔬 Pinnertest Management Portal</h1>
        <p>Complete system for report generation and client access</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        st.markdown("### Please log in to access the system")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login", use_container_width=True)
        
        if submit:
            if username and password:
                auth_result = check_credentials(username, password)
                if auth_result:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.password = password
                    st.session_state.user_role = auth_result
                    if 'current_page' not in st.session_state:
                        st.session_state.current_page = "reports"
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.warning("Please enter both username and password")

def render_navigation():
    """
    Render the navigation bar
    """
    if st.session_state.user_role == "admin":
        # Admin has access to all features
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📊 Generate Reports", use_container_width=True):
                st.session_state.current_page = "reports"
                st.rerun()
        
        with col2:
            if st.button("📁 Report Archive", use_container_width=True):
                st.session_state.current_page = "archive"
                st.rerun()
                
        with col3:
            if st.button("👥 Client Management", use_container_width=True):
                st.session_state.current_page = "clients"
                st.rerun()
        
        with col4:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.current_page = "reports"
                st.rerun()
    else:
        # Regular clients only see their reports
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            st.markdown("**Your Personalized Allergen Report**")
        
        with col2:
            st.markdown("*Secure client access only*")
            
        with col3:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.current_page = "reports"
                st.rerun()

def render_admin_reports_page():
    """
    Render the admin report generation page
    """
    st.subheader("📊 Generate Client Reports")
    
    # File upload section
    uploaded_file = st.file_uploader(
        "Upload CSV file with client and allergen data", 
        type=['csv'],
        help="Upload a CSV file containing client information and allergen test results"
    )
    
    if uploaded_file is not None:
        try:
            # Read the uploaded CSV
            df = pd.read_csv(uploaded_file)
            
            st.success(f"✅ File uploaded successfully! Found {len(df)} records.")
            
            # Display preview
            with st.expander("📋 Data Preview", expanded=True):
                st.dataframe(df.head())
            
            # Process and generate reports
            if st.button("🔄 Process Data & Generate Reports", type="primary", use_container_width=True):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                generated_reports = []
                
                for idx, row in df.iterrows():
                    progress = (idx + 1) / len(df)
                    progress_bar.progress(progress)
                    status_text.text(f"Processing client {idx + 1} of {len(df)}...")
                    
                    # Extract client info
                    client_info = {
                        'patient_name': row.get('Name', ''),
                        'patient_id': f"P{idx + 1:04d}",
                        'dob': row.get('Date of Birth', ''),
                        'gender': row.get('Gender', ''),
                        'collection_date': row.get('Collection Date', '2025-05-28'),
                        'practitioner': row.get('Practitioner', 'Dr. Smith'),
                        'specimen_type': 'Serum',
                        'email': row.get('Email', '')
                    }
                    
                    # Create allergen data from CSV columns
                    allergen_data = []
                    for col in df.columns:
                        if col not in ['Name', 'Date of Birth', 'Gender', 'Email', 'Collection Date', 'Practitioner']:
                            try:
                                value = float(row[col]) if pd.notna(row[col]) else 0.0
                                if value >= 2.5:
                                    classification = "High"
                                elif value >= 1.5:
                                    classification = "Moderate"
                                else:
                                    classification = "Low"
                                
                                allergen_data.append({
                                    'Allergen': col,
                                    'IgG_Level': value,
                                    'Classification': classification
                                })
                            except:
                                continue
                    
                    # Generate PDF placeholder
                    pdf_content = f"Report for {client_info['patient_name']} - {len(allergen_data)} allergens tested".encode()
                    
                    # Save to database
                    try:
                        db_manager = DatabaseManager()
                        if db_manager.is_connected():
                            result = db_manager.save_client_report(
                                client_info, 
                                pdf_content, 
                                pd.DataFrame(allergen_data)
                            )
                            generated_reports.append({
                                'name': client_info['patient_name'],
                                'username': result['username'],
                                'password': result['password'],
                                'allergens': len(allergen_data)
                            })
                    except Exception as e:
                        st.error(f"Error saving report for {client_info['patient_name']}: {e}")
                
                progress_bar.progress(1.0)
                status_text.text("✅ Processing complete!")
                
                # Display generated reports
                if generated_reports:
                    st.success(f"🎉 Successfully generated {len(generated_reports)} client reports!")
                    
                    st.subheader("📋 Generated Client Credentials")
                    for report in generated_reports:
                        with st.expander(f"👤 {report['name']} - {report['allergens']} allergens"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Username:** `{report['username']}`")
                            with col2:
                                st.write(f"**Password:** `{report['password']}`")
                
        except Exception as e:
            st.error(f"Error processing file: {e}")

def render_client_report():
    """
    Render the client's personalized allergen report
    """
    try:
        client_report = None
        
        # Try to get data from database first
        db_manager = DatabaseManager()
        if db_manager.is_connected():
            client_report = db_manager.get_client_report(st.session_state.username, st.session_state.get('password', ''))
        
        # If no database data, use demo data for demo account
        if not client_report and hasattr(st.session_state, 'demo_client_data'):
            client_report = st.session_state.demo_client_data
        
        if client_report:
            # Display client information
            st.markdown("### 👤 Patient Information")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Name:** {client_report['patient_name']}")
                st.write(f"**Date of Birth:** {client_report['dob']}")
                st.write(f"**Gender:** {client_report['gender']}")
            with col2:
                st.write(f"**Patient ID:** {client_report['patient_id']}")
                st.write(f"**Collection Date:** {client_report['collection_date']}")
                st.write(f"**Practitioner:** {client_report['practitioner']}")
            
            st.markdown("---")
            
            # Display allergen results
            st.markdown("### 🧪 Your Allergen Test Results")
            
            # Parse allergen data from JSON
            allergen_data = json.loads(client_report['allergen_data'])
            df = pd.DataFrame(allergen_data)
            
            # Create colored display based on classification
            for idx, row in df.iterrows():
                col1, col2, col3 = st.columns([3, 2, 2])
                
                with col1:
                    st.write(f"**{row['Allergen']}**")
                
                with col2:
                    # Color-coded classification
                    if row['Classification'] == 'High':
                        st.markdown(f"<span style='color: #FF4B4B; font-weight: bold;'>{row['Classification']}</span>", unsafe_allow_html=True)
                    elif row['Classification'] == 'Moderate':
                        st.markdown(f"<span style='color: #FFA500; font-weight: bold;'>{row['Classification']}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<span style='color: #00C851; font-weight: bold;'>{row['Classification']}</span>", unsafe_allow_html=True)
                
                with col3:
                    st.write(f"IgG: {row['IgG_Level']}")
            
            st.markdown("---")
            st.markdown("*For questions about your results, please contact your healthcare practitioner.*")
        else:
            st.error("Unable to retrieve your report. Please contact support.")
    except Exception as e:
        st.error(f"Unable to load your report: {str(e)}")

def render_archive_page():
    """
    Render the report archive page
    """
    st.subheader("📁 Report Archive")
    
    try:
        db_manager = DatabaseManager()
        if db_manager.is_connected():
            reports = db_manager.get_all_client_reports()
            
            if reports:
                st.info(f"Found {len(reports)} client reports in the database")
                
                for report in reports:
                    with st.expander(f"👤 {report['patient_name']} - {report['report_date']}"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Patient ID:** {report['patient_id']}")
                            st.write(f"**Username:** {report['username']}")
                        with col2:
                            st.write(f"**DOB:** {report['dob']}")
                            st.write(f"**Gender:** {report['gender']}")
                        with col3:
                            st.write(f"**Practitioner:** {report['practitioner']}")
                            st.write(f"**Active:** {'Yes' if report['is_active'] else 'No'}")
            else:
                st.info("No reports found in the archive")
        else:
            st.error("Database connection unavailable")
    except Exception as e:
        st.error(f"Error loading archive: {e}")

def main():
    """
    Main application entry point
    """
    st.set_page_config(
        page_title="Pinnertest Management Portal",
        page_icon="🔬",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS for clean white theme
    st.markdown("""
    <style>
    .main-header {
        background: white;
        padding: 2rem;
        margin: -1rem -1rem 2rem -1rem;
        color: #333;
        text-align: center;
        border-bottom: 2px solid #f0f0f0;
    }
    .stButton > button {
        background: white;
        color: #333;
        border: 2px solid #e0e0e0;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        font-weight: 600;
    }
    .stButton > button:hover {
        background: #f8f9fa;
        border-color: #ccc;
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Check authentication
    if not st.session_state.authenticated:
        login_page()
        return
    
    # Render navigation
    render_navigation()
    
    # Route to appropriate page
    if st.session_state.current_page == "reports":
        if st.session_state.user_role == "admin":
            render_admin_reports_page()
        else:
            render_client_report()
    
    elif st.session_state.current_page == "archive":
        render_archive_page()
    
    elif st.session_state.current_page == "clients":
        st.subheader("👥 Client Management")
        st.info("Client management features coming soon...")

if __name__ == "__main__":
    main()