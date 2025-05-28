import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
import io
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.colors import Normalize
from matplotlib.patches import Circle, Rectangle
import os
import json
import base64
from datetime import datetime
import cv2

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
    # For development, accept admin/admin
    if username == "admin" and password == "admin":
        return True
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
            if check_credentials(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
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
    <div style='background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); padding: 1rem; margin-bottom: 2rem; border-radius: 0.5rem;'>
        <h2 style='color: white; margin: 0; text-align: center;'>🔬 Pinnertest Client Portal</h2>
        <p style='color: rgba(255,255,255,0.9); margin: 0; text-align: center;'>Welcome back! Access your personalized allergen reports below.</p>
    </div>
    """, unsafe_allow_html=True)
    
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
    
    # Custom CSS for professional styling
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        margin: -1rem -1rem 2rem -1rem;
        color: white;
        text-align: center;
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        font-weight: 600;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
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
        # Import and render the simplified report page
        from simple_report_page import render_reports_page
        
        # Display the reports page
        render_reports_page()

    elif st.session_state.current_page == "archive":
        # Import and render the report archive page
        from report_archive_page import render_report_archive_page
        
        # Display the report archive page
        render_report_archive_page()

    elif st.session_state.current_page == "portal":
        # Import and render the client portal design page
        from client_portal_design_page import render_client_portal_design_page
        
        # Display the client portal design page
        render_client_portal_design_page()

if __name__ == "__main__":
    main()