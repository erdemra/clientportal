import streamlit as st
import pandas as pd
import os
import json
import base64
from datetime import datetime

# Database functionality
import db
from db import DatabaseManager

# Initialize session state for navigation
if 'current_page' not in st.session_state:
    st.session_state.current_page = "reports"

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

def check_credentials(username, password):
    """
    Check if the provided username and password are valid
    """
    # Admin access only for super secure analysis features
    if username == "admin" and password == "admin":
        return "admin"
    
    # Demo client for testing (replace with real database later)
    if username == "johndoe_1990" and password == "demo123":
        return "client"
    
    # Check against client database for real client credentials
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
    <div style='text-align: center; padding: 2rem;'>
        <h1>🔬 Pinnertest Portal</h1>
        <p style='color: #666; font-size: 1.2rem;'>Secure access to your personalized allergen reports</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### Login to Access Your Reports")
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        if st.button("Login", use_container_width=True):
            auth_result = check_credentials(username, password)
            if auth_result:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.user_role = auth_result  # Store role (admin/client)
                st.rerun()
            else:
                st.error("Invalid username or password. Please try again.")
        
        st.markdown("---")
        st.markdown("**Need help?** Contact your healthcare provider for login credentials.")

def render_navigation():
    """
    Render the navigation bar
    """
    st.markdown("""
    <div style='background: white; padding: 1rem; margin-bottom: 2rem; border-radius: 0.5rem; border: 1px solid #e0e0e0; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'>
        <h2 style='color: #333; margin: 0; text-align: center;'>🔬 Pinnertest Client Portal</h2>
        <p style='color: #666; margin: 0; text-align: center;'>Welcome back! Access your personalized allergen reports below.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show different navigation based on user role
    user_role = st.session_state.get('user_role', 'client')
    
    if user_role == "admin":
        # Admin gets access to all features
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📊 Reports", use_container_width=True):
                st.session_state.current_page = "reports"
                st.rerun()
        
        with col2:
            if st.button("📁 Archive", use_container_width=True):
                st.session_state.current_page = "archive"
                st.rerun()
                
        with col3:
            if st.button("🎨 Portal Design", use_container_width=True):
                st.session_state.current_page = "portal"
                st.rerun()
        
        with col4:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.current_page = "reports"
                st.rerun()
    else:
        # Regular clients only see their reports (NO analysis access)
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

def main():
    """
    Main application entry point
    """
    st.set_page_config(
        page_title="Pinnertest Client Portal",
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
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
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
        try:
            # Import and render the simplified report page
            from simple_report_page import render_reports_page
            render_reports_page()
        except ImportError:
            st.error("Report functionality not available in this deployment.")

    elif st.session_state.current_page == "archive":
        try:
            # Import and render the report archive page
            from report_archive_page import render_report_archive_page
            render_report_archive_page()
        except ImportError:
            st.error("Archive functionality not available in this deployment.")

    elif st.session_state.current_page == "portal":
        try:
            # Import and render the client portal design page
            from client_portal_design_page import render_client_portal_design_page
            render_client_portal_design_page()
        except ImportError:
            st.error("Portal design functionality not available in this deployment.")

if __name__ == "__main__":
    main()