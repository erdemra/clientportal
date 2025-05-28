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

import image_processing
import grid_utils
import analysis
import db
import persistent_storage
import cv2

# Set page config
st.set_page_config(
    page_title="Colorimetric Microarray Analysis",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS to make the UI more compact and hide Streamlit UI elements
st.markdown("""
<style>
    /* Make the page more compact by reducing margins */
    .block-container {
        padding-top: 0 !important;
        padding-bottom: 1rem;
        margin-top: 0 !important;
    }
    /* Smaller title to save space */
    h1 {
        font-size: 1.8rem !important;
        margin-bottom: 0.5rem !important;
    }
    h2 {
        font-size: 1.5rem !important;
        margin-bottom: 0.5rem !important;
    }
    h3 {
        font-size: 1.2rem !important;
        margin-bottom: 0.5rem !important;
    }
    /* Custom styling for navigation buttons */
    [data-testid="stHorizontalBlock"] .stButton button {
        background-color: white;
        color: rgb(49, 51, 63);
        border: 1px solid rgb(230, 234, 241);
        border-radius: 4px;
    }
    
    /* Only the active tab should be blue */
    [data-testid="stHorizontalBlock"] .stButton button[kind="primary"] {
        background-color: rgb(79, 121, 223) !important;
        color: white !important;
        border-color: rgb(79, 121, 223) !important;
    }
    /* Consistent button styling across app */
    .stButton button {
        padding: 0.2rem 0.5rem;
        font-size: 0.8rem;
        border-radius: 4px;
        height: 32px;
        font-weight: 500;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        transition: all 0.2s;
    }
    /* Primary button style */
    .stButton button[data-baseweb="button"].primary {
        background-color: #4e8aff;
        color: white;
        border-color: #4e8aff;
    }
    /* Secondary button style */
    .stButton button[data-baseweb="button"].secondary:hover {
        background-color: #e9ecef;
        border-color: #dee2e6;
    }
    /* Hover effect for all buttons */
    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
    }
    .stForm {
        padding: 1rem;
        margin-bottom: 0.5rem;
    }
    /* Hide the sidebar */
    [data-testid="stSidebar"] {
        display: none;
    }
    /* Hide all Streamlit UI elements */
    button[kind="header"] {
        display: none !important;
    }
    header {
        display: none !important;
    }
    #MainMenu {
        visibility: hidden !important;
    }
    footer {
        visibility: hidden !important;
    }
    [data-testid="stToolbar"] {
        display: none !important;
    }
    [data-testid="stDecoration"] {
        display: none !important;
    }
    [data-testid="stStatusWidget"] {
        display: none !important;
    }
    .stDeployButton {
        display: none !important;
    }
    [data-testid="stAppViewBlockContainer"] {
        margin-top: 0 !important;
    }
    [data-testid="stHeader"] {
        display: none !important;
    }
    /* Remove all top margins */
    .stApp {
        margin-top: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# Page title removed as requested
# st.markdown("<h1 style='text-align: center;'>Colorimetric Microarray Analysis Tool</h1>", unsafe_allow_html=True)

# Initialize session state for various app components
if 'uploaded_image' not in st.session_state:
    st.session_state.uploaded_image = None
if 'processed_image' not in st.session_state:
    st.session_state.processed_image = None
if 'grid_params' not in st.session_state:
    st.session_state.grid_params = {
        'rows': 15,
        'cols': 10,
        'h_spacing': 50,
        'v_spacing': 50,
        'x_offset': 50,
        'y_offset': 50,
        'rotation': 0,
        'scale': 1.0,
        'spot_size': 10
    }
if 'grid_coordinates' not in st.session_state:
    st.session_state.grid_coordinates = None
if 'adjusted_spots' not in st.session_state:
    st.session_state.adjusted_spots = {}
    
# Clear adjusted spots when the grid parameters are changed through code
# This helps avoid index errors when switching between different grid sizes
if 'grid_reset_done' not in st.session_state:
    st.session_state.adjusted_spots = {}
    st.session_state.grid_reset_done = True
if 'selected_spot' not in st.session_state:
    st.session_state.selected_spot = (0, 0)
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None

# Try to load saved grid settings
saved_grid = persistent_storage.load_grid_settings()
if saved_grid is not None:
    grid_params, adjusted_spots = saved_grid
    
    # We now allow negative offsets, no validation needed
    st.session_state.grid_params = grid_params
    st.session_state.adjusted_spots = adjusted_spots

# Define callbacks for updating grid parameters
def on_param_change():
    """Callback for when a grid parameter changes"""
    # Store previous grid dimensions to check if they've changed
    prev_rows = st.session_state.grid_params['rows'] if 'grid_params' in st.session_state else 0
    prev_cols = st.session_state.grid_params['cols'] if 'grid_params' in st.session_state else 0
    
    # First update all grid parameters from session state
    update_grid_params_from_session_state()
    
    # Check if rows or columns have changed - if so, we'll reset the adjusted spots
    current_rows = st.session_state.grid_params['rows']
    current_cols = st.session_state.grid_params['cols']
    grid_dimensions_changed = (prev_rows != current_rows or prev_cols != current_cols)
    
    if grid_dimensions_changed:
        # Clear adjusted spots when dimensions change
        st.session_state.adjusted_spots = {}
    
    if st.session_state.uploaded_image is not None:
        # Always regenerate grid coordinates when any parameter changes
        st.session_state.grid_coordinates = grid_utils.generate_grid_coordinates(
            st.session_state.processed_image,
            int(st.session_state.grid_params['rows']),
            int(st.session_state.grid_params['cols']),
            float(st.session_state.grid_params['h_spacing']),
            float(st.session_state.grid_params['v_spacing']),
            float(st.session_state.grid_params['x_offset']),
            float(st.session_state.grid_params['y_offset']),
            float(st.session_state.grid_params['rotation']),
            float(st.session_state.grid_params['scale'])
        )
        
        # Save the current settings to file
        persistent_storage.save_grid_settings(
            st.session_state.grid_params,
            st.session_state.adjusted_spots
        )

# Helper function to update grid params from session state
def update_grid_params_from_session_state():
    """Update grid_params from current session state values"""
    # Update grid parameters from their respective session state values
    if 'rows' in st.session_state:
        st.session_state.grid_params['rows'] = st.session_state.rows
    if 'cols' in st.session_state:
        st.session_state.grid_params['cols'] = st.session_state.cols
    if 'spot_size' in st.session_state:
        st.session_state.grid_params['spot_size'] = st.session_state.spot_size
    if 'h_spacing' in st.session_state:
        st.session_state.grid_params['h_spacing'] = st.session_state.h_spacing
    if 'v_spacing' in st.session_state:
        st.session_state.grid_params['v_spacing'] = st.session_state.v_spacing
    if 'x_offset' in st.session_state:
        st.session_state.grid_params['x_offset'] = st.session_state.x_offset
    if 'y_offset' in st.session_state:
        st.session_state.grid_params['y_offset'] = st.session_state.y_offset
    if 'rotation' in st.session_state:
        st.session_state.grid_params['rotation'] = st.session_state.rotation

def on_spot_change(row_idx, col_idx, x, y):
    """Callback for when an individual spot position is adjusted"""
    # Store the adjusted spot coordinates
    st.session_state.adjusted_spots[(row_idx, col_idx)] = (x, y)
    
    # Save the current settings to file
    persistent_storage.save_grid_settings(
        st.session_state.grid_params,
        st.session_state.adjusted_spots
    )

# Create a horizontal menu in the header and hide sidebar
st.markdown("""
<style>
    /* Hide the sidebar navigation */
    [data-testid="stSidebar"] {
        display: none;
    }
    
    /* Header menu styles */
    .header-menu {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin-bottom: 20px;
    }
    .header-menu a {
        color: #4e8aff;
        text-decoration: none;
        padding: 5px 15px;
        border-radius: 5px;
        transition: background-color 0.3s;
    }
    .header-menu a:hover {
        background-color: rgba(78, 138, 255, 0.1);
    }
    .header-menu a.active {
        background-color: rgba(78, 138, 255, 0.2);
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize page in session state if not exists
if 'current_page' not in st.session_state:
    st.session_state.current_page = "app"
    
# Initialize allergen data in session state
if 'allergen_data' not in st.session_state:
    st.session_state.allergen_data = None
    
if 'allergen_file_name' not in st.session_state:
    st.session_state.allergen_file_name = None

# Create navigation menu using buttons for a cleaner look
menu_options = ["app", "reports", "archive", "portal"]

# Add additional styling for the navigation menu
st.markdown("""
<style>
    /* Navigation container style */
    .nav-container {
        display: flex;
        justify-content: center;
        margin-bottom: 1rem;
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 0.5rem;
    }
    
    /* Navigation button style */
    .nav-button {
        padding: 0.5rem 1rem;
        margin: 0 0.5rem;
        background-color: #ffffff;
        color: #4e8aff;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        font-weight: bold;
        transition: all 0.3s;
    }
    
    /* Active button style */
    .nav-button.active {
        background-color: #4e8aff;
        color: white;
    }
    
    /* Hover effect */
    .nav-button:hover:not(.active) {
        background-color: #e1e5eb;
    }
</style>
""", unsafe_allow_html=True)

# Logo section removed as requested

# Custom CSS for better button styling
st.markdown("""
<style>
/* Style for active button */
.nav-active {
    background-color: #4F79DF !important;
    color: white !important;
    border-color: #4F79DF !important;
}
/* Style for inactive button */
.nav-inactive {
    background-color: white !important;
    color: #333 !important;
    border-color: #e6eaf1 !important;
}
</style>
""", unsafe_allow_html=True)

# Create a row of buttons for navigation
col1, col2, col3, col4 = st.columns(4)

# Add the "Reporting" button
with col1:
    report_button_type = "primary" if st.session_state.current_page == "reports" else "secondary"
    if st.button("Reporting", key="nav_reports", type=report_button_type, use_container_width=True):
        st.session_state.current_page = "reports"
        st.rerun()

# Add the "Report Archive" button
with col2:
    archive_button_type = "primary" if st.session_state.current_page == "archive" else "secondary"
    if st.button("Report Archive", key="nav_archive", type=archive_button_type, use_container_width=True):
        st.session_state.current_page = "archive"
        st.rerun()

# Add the "Client Portal Design" button
with col3:
    portal_button_type = "primary" if st.session_state.current_page == "portal" else "secondary"
    if st.button("Client Portal Design", key="nav_portal", type=portal_button_type, use_container_width=True):
        st.session_state.current_page = "portal"
        st.rerun()

# Add placeholder for future expansion
with col4:
    st.write("")  # Empty for now

# Set default page to reports if not set
if 'current_page' not in st.session_state:
    st.session_state.current_page = "reports"

# Translate tab removed as requested

# Add the Pinnertest logo UNDER the navigation tabs
logo_path = "attached_assets/Pinnertest Logo copy.png"
if os.path.exists(logo_path):
    with open(logo_path, "rb") as img_file:
        logo_base64 = base64.b64encode(img_file.read()).decode()
    st.markdown(
        f"""
        <style>
        .logo-under-tabs {{
            display: flex;
            justify-content: flex-start;
            margin-top: 15px;
            margin-bottom: 15px;
        }}
        .logo-larger {{
            max-height: 90px; /* 300% larger than the 30px size */
        }}
        </style>
        
        <div class="logo-under-tabs">
            <img src="data:image/png;base64,{logo_base64}" class="logo-larger">
        </div>
        """,
        unsafe_allow_html=True
    )

# Add a separator line
st.markdown("<hr style='margin-top: 0; margin-bottom: 1rem; border-width: 1px;'>", unsafe_allow_html=True)

# Define base64 image function
def get_base64_of_image(image_path):
    """Get the base64 encoding of an image"""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Will add the logo AFTER the tabs in the page content

# Remove duplicate function definition

# Main content based on selected page
if st.session_state.current_page == "app":
    # Single column for image uploader only
    upload_col = st.container()
    
    with upload_col:
        # File uploader section
        st.subheader("Upload Image")
        uploaded_file = st.file_uploader("Select image file", type=['png', 'jpg', 'jpeg', 'tif', 'tiff'], label_visibility="collapsed")

    # Check if we should use a persisted image from a previous session
    last_image = None
    if uploaded_file is None:
        last_image = persistent_storage.load_last_image()
        # No text notification about using the last image
    
    # If we have a new upload, use it
    if uploaded_file is not None:
        # Read and display the uploaded image
        image = Image.open(uploaded_file)
        st.session_state.uploaded_image = image
        st.session_state.uploaded_image_filename = uploaded_file.name
        
        # Save the image for persistence between sessions
        persistent_storage.save_last_image(image)
        
        # Store the raw image array and original color image for processing
        img_array = np.array(image)
        st.session_state.original_image = img_array.copy()
        
        # For new uploads, use saved user preferences if available
        # Load user's preferred image settings
        user_preferences = persistent_storage.load_image_preferences()
        st.session_state.contrast = user_preferences.get('contrast', 1.0)
        st.session_state.brightness = user_preferences.get('brightness', 0)
        
        # Convert to grayscale if color image
        if len(img_array.shape) > 2 and img_array.shape[2] > 1:
            # Convert to grayscale using numpy
            gray_img = np.dot(img_array[..., :3], [0.299, 0.587, 0.114]).astype(np.uint8)
        else:
            gray_img = img_array.copy()
        
        # Save the original grayscale image for later adjustments
        st.session_state.gray_image = gray_img
            
        # Apply contrast enhancement using numpy operations with current values
        alpha = st.session_state.contrast  # Contrast control
        beta = st.session_state.brightness  # Brightness control
        
        # Apply contrast and brightness adjustment manually
        enhanced_img = np.clip(alpha * gray_img + beta, 0, 255).astype(np.uint8)
        
        # Store the enhanced image for analysis
        st.session_state.processed_image = enhanced_img
    # If no new upload but we have a persisted image, use it
    elif last_image is not None:
        st.session_state.uploaded_image = last_image
        st.session_state.uploaded_image_filename = "persisted_image.png"
        
        # Store the raw image array and original color image for processing
        img_array = np.array(last_image)
        st.session_state.original_image = img_array.copy()
        
        # For persisted images, only initialize if not already set
        # This maintains previous adjustments when refreshing the page
        if 'contrast' not in st.session_state or 'brightness' not in st.session_state:
            # Load user's preferred image settings
            user_preferences = persistent_storage.load_image_preferences()
            if 'contrast' not in st.session_state:
                st.session_state.contrast = user_preferences.get('contrast', 1.0)
            if 'brightness' not in st.session_state:
                st.session_state.brightness = user_preferences.get('brightness', 0)
        
        # Convert to grayscale if color image
        if len(img_array.shape) > 2 and img_array.shape[2] > 1:
            # Convert to grayscale using numpy
            gray_img = np.dot(img_array[..., :3], [0.299, 0.587, 0.114]).astype(np.uint8)
        else:
            gray_img = img_array.copy()
        
        # Save the original grayscale image for later adjustments
        st.session_state.gray_image = gray_img
            
        # Apply contrast enhancement using numpy operations with current values
        alpha = st.session_state.contrast  # Contrast control
        beta = st.session_state.brightness  # Brightness control
        
        # Apply contrast and brightness adjustment manually
        enhanced_img = np.clip(alpha * gray_img + beta, 0, 255).astype(np.uint8)
        
        # Store the enhanced image for analysis
        st.session_state.processed_image = enhanced_img
    
    # If we have either an uploaded image or a persisted image
    if st.session_state.uploaded_image is not None:
        # Create two columns for the image and controls
        image_col, controls_col = st.columns([3, 2])
        
        with image_col:
            # Function to update processed image when sliders change (defined outside accordions)
            def update_processed_image():
                # Ensure we have the original grayscale image
                if 'gray_image' not in st.session_state:
                    return
                
                # Get current contrast and brightness settings
                contrast_factor = st.session_state.contrast
                brightness_offset = st.session_state.brightness
                
                # Simple direct adjustment using OpenCV for reliability
                adjusted = cv2.convertScaleAbs(
                    st.session_state.gray_image,
                    alpha=contrast_factor,
                    beta=brightness_offset
                )
                
                # Store the processed image
                st.session_state.processed_image = adjusted
                
                # Force grid coordinate regeneration to update display
                st.session_state.grid_coordinates = None
                
            # Add image adjustment controls in an accordion (closed by default)
            with st.expander("Image Controls", expanded=False):
                adjust_col1, adjust_col2 = st.columns(2)
                
                # Simple contrast controls
                with adjust_col1:
                    st.write("**Contrast Control**")
                    st.write(f"Current: {st.session_state.contrast:.1f}")
                    
                    # Button for increasing contrast
                    if st.button("More Contrast", key="more_contrast_button"):
                        # Decrease contrast value (which visually increases contrast)
                        st.session_state.contrast = max(0.1, st.session_state.contrast - 0.1)
                        update_processed_image()
                    
                    # Button for decreasing contrast
                    if st.button("Less Contrast", key="less_contrast_button"):
                        # Increase contrast value (which visually decreases contrast)
                        st.session_state.contrast = min(2.0, st.session_state.contrast + 0.1)
                        update_processed_image()
                
                # Simple brightness controls
                with adjust_col2:
                    st.write("**Brightness Control**")
                    st.write(f"Current: {st.session_state.brightness:.1f}")
                    
                    # Button for increasing brightness
                    if st.button("Brighter", key="brighter_button"):
                        # Increase brightness by 5
                        st.session_state.brightness = min(50, st.session_state.brightness + 5)
                        update_processed_image()
                    
                    # Button for decreasing brightness
                    if st.button("Darker", key="darker_button"):
                        # Decrease brightness by 5
                        st.session_state.brightness = max(-30, st.session_state.brightness - 5)
                        update_processed_image()
                
                # Add control buttons in a row
                reset_col, save_col = st.columns(2)
                with reset_col:
                    # Reset button to restore default values
                    if st.button("Reset Image", key="reset_image_button"):
                        # Reset to original values
                        st.session_state.contrast = 1.0
                        st.session_state.brightness = 0
                        update_processed_image()
                
                with save_col:
                    # Save as Default button
                    if st.button("Save as Default", key="save_default_button"):
                        # Save current contrast and brightness as default preferences
                        preferences = {
                            'contrast': st.session_state.contrast,
                            'brightness': st.session_state.brightness
                        }
                        saved = persistent_storage.save_image_preferences(preferences)
                        if saved:
                            st.success("Default image settings saved successfully!")
                        else:
                            st.error("Failed to save default image settings.")
            
            # Add a Run Analysis button at the top of the image section (3D and smaller)
            left_col, center_col, right_col = st.columns([1, 2, 1])
            with center_col:
                # Style for the button to match the page UI
                st.markdown("""
                <style>
                div[data-testid="stButton"] button {
                    background-color: #4285f4;
                    color: white;
                    font-weight: 500;
                    padding: 0.25rem 1rem;
                    border-radius: 4px;
                    border: none;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
                }
                div[data-testid="stButton"] button:hover {
                    background-color: #3b78e7;
                }
                </style>
                """, unsafe_allow_html=True)
                run_analysis_clicked = st.button("Run Analysis", key="run_analysis_top", type="primary")
            
            # Only proceed with analysis if the button was clicked and we have an image
            if run_analysis_clicked:
                if 'processed_image' not in st.session_state or st.session_state.processed_image is None:
                    st.error("Please upload an image first")
                else:
                    # Get the final adjusted coordinates
                    final_coordinates = grid_utils.get_adjusted_coordinates(
                        st.session_state.grid_coordinates if 'grid_coordinates' in st.session_state else None,
                        st.session_state.adjusted_spots if 'adjusted_spots' in st.session_state else {},
                        st.session_state.grid_params['rows'],
                        st.session_state.grid_params['cols']
                    )
                    
                    # Run the analysis
                    analysis_results = analysis.analyze_spots(
                        st.session_state.processed_image,
                        final_coordinates,
                        st.session_state.grid_params['rows'],
                        st.session_state.grid_params['cols'],
                        st.session_state.grid_params['spot_size']
                    )
                    
                    # Store the results in session state
                    st.session_state.analysis_results = analysis_results
                    
                    # Display a success message
                    st.success("Analysis completed successfully! Redirecting to Reporting tab...")
                    
                    # Navigate to the Reports page automatically after analysis is complete
                    st.session_state.current_page = "reports"
                    # Force page to reload
                    st.rerun()
                    
                    # Generate normalized IgG results based on analysis
                    try:
                        # Sort by optical density
                        sorted_results = analysis_results.sort_values('Avg_OD', ascending=False).reset_index(drop=True)
                        
                        # Get 3rd and 20th highest Avg_OD values for normalization
                        if len(sorted_results) >= 20:
                            od_top3 = sorted_results.iloc[2]['Avg_OD']  # 3rd highest (0-indexed)
                            od_top20 = sorted_results.iloc[19]['Avg_OD']  # 20th highest
                        elif len(sorted_results) >= 3:
                            od_top3 = sorted_results.iloc[2]['Avg_OD']
                            od_top20 = sorted_results.iloc[-1]['Avg_OD']  # Use the last value if less than 20 items
                        else:
                            # Not enough data for normalization
                            od_top3 = analysis_results['Avg_OD'].max() if not analysis_results.empty else 0
                            od_top20 = analysis_results['Avg_OD'].min() if not analysis_results.empty else 0
                            
                        # Calculate normalization parameters (linear equation: y = ax + b)
                        # Conditions: IgG_normalized = 20.0 at od_top3, IgG_normalized = 7.5 at od_top20
                        if od_top3 != od_top20:
                            a = (20.0 - 7.5) / (od_top3 - od_top20)
                            b = 20.0 - (a * od_top3)
                            
                            # Apply formula to all rows: IgG_normalized = a * Avg_OD + b
                            analysis_results['IgG_normalized'] = analysis_results['Avg_OD'].apply(lambda x: a * x + b)
                            
                            # Classify based on IgG_normalized values
                            def classify_igg(value):
                                if value >= 20.0:
                                    return "Highly elevated"
                                elif value >= 7.5:
                                    return "Elevated"
                                else:
                                    return "< 7.5 μg/ml"
                            
                            analysis_results['Rating'] = analysis_results['IgG_normalized'].apply(classify_igg)
                            
                            # Store numeric values before potential formatting
                            analysis_results['IgG_numeric'] = analysis_results['IgG_normalized']
                            
                            # Create a combined output with allergen data
                            if st.session_state.allergen_data is not None:
                                # Create a mapping function to look up allergen info for each spot
                                def lookup_allergen_info(row_idx, col_idx, allergen_df):
                                    match = allergen_df[(allergen_df['Row'] == row_idx) & (allergen_df['Column'] == col_idx)]
                                    if not match.empty:
                                        category = "Uncategorized"
                                        if 'Category' in allergen_df.columns:
                                            category = match['Category'].values[0]
                                        
                                        # Check which column name exists for allergen name
                                        name_column = None
                                        if 'Allergen' in allergen_df.columns:
                                            name_column = 'Allergen'
                                        elif 'Name' in allergen_df.columns:
                                            name_column = 'Name'
                                        
                                        # Get name based on available column
                                        if name_column is not None:
                                            name = match[name_column].values[0]
                                        else:
                                            name = f"Spot {row_idx}-{col_idx}"
                                        
                                        # Get Latin name if available
                                        latin_name = "N/A"
                                        if 'Latin Name' in allergen_df.columns:
                                            latin_name = match['Latin Name'].values[0]
                                        
                                        return name, latin_name, category
                                    else:
                                        return "N/A", "N/A", "N/A"
                                
                                # Create a new normalized output dataframe
                                normalized_output = []
                                
                                for _, row in analysis_results.iterrows():
                                    row_idx = int(row['Row'])
                                    col_idx = int(row['Column'])
                                    name, latin_name, category = lookup_allergen_info(row_idx, col_idx, st.session_state.allergen_data)
                                    
                                    # Format IgG values - use "Unelevated" for values below threshold
                                    igg_value = row['IgG_normalized']
                                    igg_display = "Unelevated" if igg_value < 7.5 else f"{igg_value:.1f}"
                                    
                                    normalized_output.append({
                                        'Row': row_idx,
                                        'Column': col_idx,
                                        'Allergen': name,
                                        'Latin Name': latin_name,
                                        'Category': category,
                                        'IgG (µg/ml)': igg_display
                                    })
                                
                                # Convert to dataframe and save to CSV
                                normalized_df = pd.DataFrame(normalized_output)
                                
                                # Save normalized results to CSV for report generation
                                normalized_df.to_csv('data/normalized_allergen_results.csv', index=False)
                                
                                # Store in session state for later use
                                st.session_state.normalized_df = normalized_df
                        
                    except Exception as e:
                        st.error(f"Error during normalization and data preparation: {str(e)}")
                    
                    # Store results and go to Results page
                    st.session_state.current_page = "report template"
                    
                    # Force a rerun to navigate to the Results page
                    st.rerun()
            
            # Always regenerate coordinates whenever we render the image
            # This ensures the grid always reflects the current parameters
            st.session_state.grid_coordinates = grid_utils.generate_grid_coordinates(
                st.session_state.processed_image,
                int(st.session_state.grid_params['rows']),
                int(st.session_state.grid_params['cols']),
                float(st.session_state.grid_params['h_spacing']),
                float(st.session_state.grid_params['v_spacing']),
                float(st.session_state.grid_params['x_offset']),
                float(st.session_state.grid_params['y_offset']),
                float(st.session_state.grid_params['rotation']),
                float(st.session_state.grid_params['scale'])
            )
            
            # Get the final adjusted coordinates - always do this to reflect current parameters
            final_coordinates = grid_utils.get_adjusted_coordinates(
                st.session_state.grid_coordinates if 'grid_coordinates' in st.session_state else None,
                st.session_state.adjusted_spots if 'adjusted_spots' in st.session_state else {},
                st.session_state.grid_params['rows'],
                st.session_state.grid_params['cols']
            )
            
            # Display processed image (title removed)
            
            # Always use the processed image with contrast/brightness adjustments for display
            display_image = st.session_state.processed_image
            cmap = 'gray'  # Always use grayscale for processed images
            
            # Get dimensions for aspect ratio calculation
            img_height, img_width = display_image.shape[:2]
            aspect_ratio = img_height / img_width
            
            # Create completely trimmed figure with no white space or padding
            fig, ax = plt.subplots(figsize=(0.70, 0.70 * aspect_ratio), dpi=300, frameon=False)
            fig.patch.set_alpha(0)      # Transparent figure background
            ax.patch.set_alpha(0)       # Transparent axis background
            
            # Completely remove all padding, margins, and frame
            ax.axis('off')
            fig.tight_layout(pad=0)
            plt.subplots_adjust(left=0, right=1, top=1, bottom=0, wspace=0, hspace=0)
            
            # Set fully transparent background colors 
            fig.set_facecolor('none')
            ax.set_facecolor('none')
            
            # Hide spines (borders) completely
            for spine in ax.spines.values():
                spine.set_visible(False)
            
            # Directly display the image with absolutely no padding
            # Use extent parameter to eliminate any automatic padding matplotlib adds
            img_height, img_width = display_image.shape[:2]
            ax.imshow(display_image, cmap=cmap, extent=[0, img_width, img_height, 0])
            
            # Eliminate all axes elements and set limits to match image exactly
            ax.set_xlim(0, img_width)
            ax.set_ylim(img_height, 0)  # Reversed y-axis
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_xticklabels([])
            ax.set_yticklabels([])
            
            # Add grid overlay with much more visible lines and make spots clickable
            # Create a dictionary to store circles for each spot (row, col)
            spot_circles = {}
            
            # Create a dictionary for annotations (tooltips)
            annotations = {}
            
            # Calculate background rectangle for the grid area
            grid_min_x = min([coord[0] for coord in final_coordinates]) - st.session_state.grid_params['spot_size'] * 1.5
            grid_max_x = max([coord[0] for coord in final_coordinates]) + st.session_state.grid_params['spot_size'] * 1.5
            grid_min_y = min([coord[1] for coord in final_coordinates]) - st.session_state.grid_params['spot_size'] * 1.5
            grid_max_y = max([coord[1] for coord in final_coordinates]) + st.session_state.grid_params['spot_size'] * 1.5
            
            # Remove the background padding completely by using a transparent background
            rect = Rectangle((grid_min_x, grid_min_y), 
                           grid_max_x - grid_min_x, 
                           grid_max_y - grid_min_y, 
                           fill=True, 
                           color='none',
                           linewidth=0,
                           alpha=0.0)
            ax.add_patch(rect)
            
            for i in range(len(final_coordinates)):
                x, y = final_coordinates[i]
                
                # Calculate row and column for this spot
                row = i // st.session_state.grid_params['cols']
                col = i % st.session_state.grid_params['cols']
                
                # Consistent green circles for all spots with thinner higher-definition borders
                circle = Circle((x, y), st.session_state.grid_params['spot_size'], 
                              fill=False, edgecolor='#00cc00', alpha=0.8, linewidth=0.2)
                ax.add_patch(circle)
                
                # Store circle with its coordinates for later reference
                spot_circles[(row, col)] = (x, y)
                
                # Store label information but don't show it by default
                annotations[(row, col)] = (row, col, x, y)
            
            # Create click functionality for the figure
            def on_image_click(event):
                if event.xdata is not None and event.ydata is not None:
                    # Find the closest spot to the click
                    min_dist = float('inf')
                    closest_spot = None
                    
                    for (row, col), (x, y) in spot_circles.items():
                        dist = ((event.xdata - x)**2 + (event.ydata - y)**2)**0.5
                        if dist < min_dist:
                            min_dist = dist
                            closest_spot = (row, col)
                    
                    # If we found a spot close to the click and it's within a reasonable distance
                    if closest_spot and min_dist < st.session_state.grid_params['spot_size'] * 2:
                        # Get coordinates of the selected spot
                        x, y = spot_circles[closest_spot]
                        row, col = closest_spot
                        
                        # Add a temporary text label near the selected spot
                        ax.text(x + st.session_state.grid_params['spot_size'] + 1, 
                               y - st.session_state.grid_params['spot_size'] - 1, 
                               f"{row+1},{col+1}", 
                               fontsize=3, 
                               color='blue',
                               bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="blue", alpha=0.8),
                               zorder=10)  # Ensure it's on top
                        
                        # Redraw the figure
                        fig.canvas.draw_idle()
                        
                        # Update the selected row and column in session state
                        st.session_state.selected_row = closest_spot[0] + 1  # +1 for 1-based indexing
                        st.session_state.selected_col = closest_spot[1] + 1  # +1 for 1-based indexing
                        st.session_state.selected_spot = (closest_spot[0], closest_spot[1])
                        # Force a rerun to update the UI
                        st.rerun()
            
            # Connect the click event to the figure
            fig.canvas.mpl_connect('button_press_event', on_image_click)
            
            # Set axes limits
            ax.set_xlim(0, st.session_state.processed_image.shape[1])
            ax.set_ylim(st.session_state.processed_image.shape[0], 0)
            
            # Row and column numbers have been removed as requested
            # Keeping the improved spot circles only
            
            # Remove axis ticks and labels
            ax.set_xticks([])
            ax.set_yticks([])
            
            # Make it compact with no padding
            fig.tight_layout(pad=0)
            
            # Convert to bytes buffer for full control over padding
            buf = io.BytesIO()
            fig.savefig(buf, format='png', transparent=True, 
                       bbox_inches='tight', pad_inches=0.0,
                       facecolor='none', edgecolor='none',
                       dpi=300)
            buf.seek(0)
            
            # Display the image with fixed width of 350px
            container = st.container()
            fixed_width = 350  # Exactly 350px
                
            # Custom CSS for fixed width image
            container.markdown(
                f"""
                <style>
                    .fixed-width-image {{
                        width: {fixed_width}px;
                        margin: 0 auto;
                    }}
                </style>
                """, 
                unsafe_allow_html=True
            )
            
            # Use a div with the fixed width class
            container.markdown(
                f"""
                <div class="fixed-width-image">
                    <img src="data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}" 
                         style="width: 100%; display: block;"/>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        # Controls column - place grid configuration and spot adjustment here
        with controls_col:
            # Generate grid coordinates if they don't exist
            if st.session_state.grid_coordinates is None:
                on_param_change()
            
            # Get the final adjusted coordinates for controls
            final_coordinates = grid_utils.get_adjusted_coordinates(
                st.session_state.grid_coordinates,
                st.session_state.adjusted_spots,
                st.session_state.grid_params['rows'],
                st.session_state.grid_params['cols']
            )
            
            # Grid Configuration in a compact layout
            # Define callback functions for immediate updates
            def on_rows_change():
                # Check if rows have changed
                old_rows = st.session_state.grid_params['rows']
                new_rows = st.session_state.rows_input
                if old_rows != new_rows:
                    # Clear adjusted spots when dimensions change
                    st.session_state.adjusted_spots = {}
                    st.session_state.grid_params['rows'] = new_rows
                    # Force grid coordinate regeneration
                    st.session_state.grid_coordinates = None
                update_grid()
            
            def on_cols_change():
                # Check if columns have changed
                old_cols = st.session_state.grid_params['cols']
                new_cols = st.session_state.cols_input
                if old_cols != new_cols:
                    # Clear adjusted spots when dimensions change
                    st.session_state.adjusted_spots = {}
                    st.session_state.grid_params['cols'] = new_cols
                    # Force grid coordinate regeneration
                    st.session_state.grid_coordinates = None
                update_grid()
            
            def on_spot_size_change():
                st.session_state.grid_params['spot_size'] = st.session_state.spot_size_input
                update_grid()
            
            def on_h_spacing_change():
                st.session_state.grid_params['h_spacing'] = st.session_state.h_spacing_input
                # Force grid coordinate regeneration
                st.session_state.grid_coordinates = None
                update_grid()
            
            def on_v_spacing_change():
                st.session_state.grid_params['v_spacing'] = st.session_state.v_spacing_input
                # Force grid coordinate regeneration  
                st.session_state.grid_coordinates = None
                update_grid()
            
            def on_x_offset_change():
                st.session_state.grid_params['x_offset'] = st.session_state.x_offset_input
                # Force grid coordinate regeneration when offset changes
                st.session_state.grid_coordinates = None
                # Clear any manual spot adjustments to allow all spots to move with the grid
                st.session_state.adjusted_spots = {}
                update_grid()
            
            def on_y_offset_change():
                st.session_state.grid_params['y_offset'] = st.session_state.y_offset_input
                # Force grid coordinate regeneration when offset changes
                st.session_state.grid_coordinates = None
                # Clear any manual spot adjustments to allow all spots to move with the grid
                st.session_state.adjusted_spots = {}
                update_grid()
            
            def on_rotation_change():
                st.session_state.grid_params['rotation'] = st.session_state.rotation_input
                # Force grid coordinate regeneration when rotation changes
                st.session_state.grid_coordinates = None
                update_grid()
                
            def update_grid():
                if st.session_state.uploaded_image is not None:
                    # Regenerate grid coordinates with the updated parameters
                    st.session_state.grid_coordinates = grid_utils.generate_grid_coordinates(
                        st.session_state.processed_image,
                        int(st.session_state.grid_params['rows']),
                        int(st.session_state.grid_params['cols']), 
                        float(st.session_state.grid_params['h_spacing']),
                        float(st.session_state.grid_params['v_spacing']), 
                        float(st.session_state.grid_params['x_offset']),
                        float(st.session_state.grid_params['y_offset']), 
                        float(st.session_state.grid_params['rotation']), 
                        float(st.session_state.grid_params['scale'])
                    )
                    
                    # Save current parameters to ensure they persist through rerun
                    persistent_storage.save_grid_settings(
                        st.session_state.grid_params,
                        st.session_state.adjusted_spots
                    )
                    
                    # Print debug info
                    print(f"Updating grid: rows={st.session_state.grid_params['rows']}, cols={st.session_state.grid_params['cols']}")
                    
                    # Refresh the UI to show the updated grid
                    st.rerun()
                    
            # Grid parameters in compact layout with multiple columns
            params_col1, params_col2, params_col3 = st.columns(3)
            
            with params_col1:
                rows = st.number_input("Rows", min_value=1, max_value=50, 
                                    value=int(st.session_state.grid_params['rows']), step=1, 
                                    key="rows_input", on_change=on_rows_change)
                
                h_spacing = st.number_input("H Spacing", min_value=10.0, max_value=500.0, 
                                        value=float(st.session_state.grid_params['h_spacing']), step=1.0, 
                                        key="h_spacing_input", on_change=on_h_spacing_change)
                
                x_offset = st.number_input("X Offset", min_value=-500.0, max_value=1000.0, 
                                        value=float(st.session_state.grid_params['x_offset']), step=1.0, 
                                        key="x_offset_input", on_change=on_x_offset_change)
            
            with params_col2:
                cols = st.number_input("Columns", min_value=1, max_value=50, 
                                    value=int(st.session_state.grid_params['cols']), step=1, 
                                    key="cols_input", on_change=on_cols_change)
                
                v_spacing = st.number_input("V Spacing", min_value=10.0, max_value=500.0, 
                                        value=float(st.session_state.grid_params['v_spacing']), step=1.0, 
                                        key="v_spacing_input", on_change=on_v_spacing_change)
                
                y_offset = st.number_input("Y Offset", min_value=-500.0, max_value=1000.0, 
                                        value=float(st.session_state.grid_params['y_offset']), step=1.0, 
                                        key="y_offset_input", on_change=on_y_offset_change)
            
            with params_col3:
                spot_size = st.number_input("Spot Size", min_value=1.0, max_value=100.0, 
                                        value=float(st.session_state.grid_params['spot_size']), step=1.0, 
                                        key="spot_size_input", on_change=on_spot_size_change)
                
                rotation = st.number_input("Rotation", min_value=-180.0, max_value=180.0, 
                                        value=float(st.session_state.grid_params['rotation']), step=1.0, 
                                        key="rotation_input", on_change=on_rotation_change)
            
            # Remove the Save Settings button under the image
            # Empty columns to maintain spacing
            save_col1, save_col2, save_col3 = st.columns([1, 1, 1])
            with save_col3:
                # Add empty space where the button used to be
                st.write("")
                
                # Hide Save Settings button
                if False:  # Effectively disables this section
                    # Save all current settings to disk
                    persistent_storage.save_grid_settings(
                        st.session_state.grid_params,
                        st.session_state.adjusted_spots
                    )
                    st.success("Settings saved successfully!")
            
            # Fine-tune spot position section in an expandable section
            with st.expander("Fine-tune Spot Position", expanded=False):
                st.markdown("#### Select Spot to Adjust")
                
                # Row and column selection for spot adjustment
                spot_row_idx = st.session_state.selected_spot[0]
                spot_col_idx = st.session_state.selected_spot[1]
                
                sel_col1, sel_col2 = st.columns(2)
                
                with sel_col1:
                    st.selectbox("Row", range(1, st.session_state.grid_params['rows'] + 1), index=spot_row_idx,
                                key="selected_row", on_change=lambda: setattr(st.session_state, 'selected_spot', 
                                                                            (st.session_state.selected_row - 1, 
                                                                            st.session_state.selected_spot[1])))
                    spot_row_idx = st.session_state.selected_row - 1
                
                with sel_col2:
                    st.selectbox("Column", range(1, st.session_state.grid_params['cols'] + 1), index=spot_col_idx,
                                key="selected_col", on_change=lambda: setattr(st.session_state, 'selected_spot', 
                                                                            (st.session_state.selected_spot[0], 
                                                                            st.session_state.selected_col - 1)))
                    spot_col_idx = st.session_state.selected_col - 1
                
                # Get the current position of the selected spot
                spot_idx = spot_row_idx * st.session_state.grid_params['cols'] + spot_col_idx
                if (spot_row_idx, spot_col_idx) in st.session_state.adjusted_spots:
                    current_x, current_y = st.session_state.adjusted_spots[(spot_row_idx, spot_col_idx)]
                else:
                    current_x, current_y = st.session_state.grid_coordinates[spot_idx]
                
                # Allow adjustment of individual spot coordinates - now with real-time updates
                st.markdown("#### Adjust Coordinates")
                
                adjust_col1, adjust_col2 = st.columns(2)
                
                # Create keys for these input widgets so we can detect changes
                spot_x_key = f"spot_x_{spot_row_idx}_{spot_col_idx}"
                spot_y_key = f"spot_y_{spot_row_idx}_{spot_col_idx}"
                
                # Define callback functions for real-time updates
                def on_spot_x_change():
                    on_spot_change(spot_row_idx, spot_col_idx, 
                                  st.session_state[spot_x_key], 
                                  current_y if spot_y_key not in st.session_state else st.session_state[spot_y_key])
                
                def on_spot_y_change():
                    on_spot_change(spot_row_idx, spot_col_idx, 
                                  current_x if spot_x_key not in st.session_state else st.session_state[spot_x_key], 
                                  st.session_state[spot_y_key])
                
                with adjust_col1:
                    st.number_input("X Position", value=float(current_x), step=1.0,
                                   key=spot_x_key, on_change=on_spot_x_change)
                
                with adjust_col2:
                    st.number_input("Y Position", value=float(current_y), step=1.0,
                                   key=spot_y_key, on_change=on_spot_y_change)
                
                # Hide original image reference
                if False:  # Effectively disables this section
                    st.markdown("#### Original Image Reference")
                    st.image(st.session_state.uploaded_image, channels="RGB", 
                            width=int(st.session_state.uploaded_image.width * 0.33))
                
                # Reset buttons removed
        
        # All reset buttons removed
    
    # Database Storage Section (if results exist)
    if st.session_state.analysis_results is not None:
        # Hide Save Settings Button
        if False:  # Effectively disables this section
            # Save the grid settings
            persistent_storage.save_grid_settings(
                st.session_state.grid_params,
                st.session_state.adjusted_spots
            )
            st.success("Settings saved successfully.")

# === Different page contents ==
# The report template page has been removed as requested
            
            # Add allergen info to the results dataframe
            allergen_categories = []
            allergen_names = []
            allergen_latin_names = []
            
            for _, row in results_df.iterrows():
                row_idx = int(row['Row'])
                col_idx = int(row['Column'])
                name, latin_name, category = lookup_allergen_info(row_idx, col_idx, allergen_data)
                allergen_names.append(name)
                allergen_latin_names.append(latin_name)
                allergen_categories.append(category)
            results_with_allergens["Category"] = allergen_categories
            
            # Add the new columns to the results dataframe
            results_with_allergens['Allergen'] = allergen_names
            results_with_allergens['Latin Name'] = allergen_latin_names
            
            # Use the combined dataframe for display
            display_df = results_with_allergens
        else:
            # No allergen data available, use original analysis results
            display_df = st.session_state.analysis_results if 'analysis_results' in st.session_state else pd.DataFrame()
        
        # Find max intensity if column exists
        try:
            if 'Total_Intensity' in display_df.columns:
                max_intensity_idx = display_df['Total_Intensity'].idxmax()
            elif 'IgG_numeric' in display_df.columns:
                max_intensity_idx = display_df['IgG_numeric'].idxmax()
            else:
                max_intensity_idx = None
        except:
            max_intensity_idx = None
        
        # Highlight the max intensity row
        def highlight_max(s):
            if max_intensity_idx is not None and s.name == max_intensity_idx:
                return ['background-color: #ffff99'] * len(s)
            else:
                return [''] * len(s)
        
        # Normalize values for IgG estimation
        try:
            # Sort by optical density
            sorted_df = display_df.sort_values('Avg_OD', ascending=False).reset_index(drop=True)
            
            # Get 3rd and 20th highest Avg_OD values
            if len(sorted_df) >= 20:
                od_top3 = sorted_df.iloc[2]['Avg_OD']  # 3rd highest (0-indexed)
                od_top20 = sorted_df.iloc[19]['Avg_OD']  # 20th highest
            elif len(sorted_df) >= 3:
                od_top3 = sorted_df.iloc[2]['Avg_OD']
                od_top20 = sorted_df.iloc[-1]['Avg_OD']  # Use the last value if less than 20 items
            else:
                # Not enough data for normalization
                od_top3 = display_df['Avg_OD'].max() if not display_df.empty else 0
                od_top20 = display_df['Avg_OD'].min() if not display_df.empty else 0
            
            # Solve for normalization constants (linear equation: y = ax + b)
            # Where y is IgG_normalized and x is Avg_OD
            # Conditions: IgG_normalized = 20.0 at od_top3, IgG_normalized = 7.5 at od_top20
            
            # Prevent division by zero
            if od_top3 != od_top20:
                a = (20.0 - 7.5) / (od_top3 - od_top20)
                b = 20.0 - (a * od_top3)
                
                # Apply formula to all rows: IgG_normalized = a * Avg_OD + b
                display_df['IgG_normalized'] = display_df['Avg_OD'].apply(lambda x: a * x + b)
                
                # Classify based on IgG_normalized values
                def classify_igg(value):
                    if value >= 20.0:
                        return "Highly elevated"
                    elif value >= 7.5:
                        return "Elevated"
                    else:
                        return "Not elevated"
                
                display_df['Rating'] = display_df['IgG_normalized'].apply(classify_igg)
                
                # Store original numeric values before formatting for sorting
                display_df['IgG_numeric'] = display_df['IgG_normalized']
                # Format the normalized values to 1 decimal place
                display_df['IgG_normalized'] = display_df['IgG_normalized'].apply(lambda x: f"{x:.1f}")
            else:
                # Can't normalize with identical values
                display_df['IgG_normalized'] = "N/A"
                display_df['Rating'] = "N/A"
                
        except Exception as e:
            st.error(f"Error during normalization: {str(e)}")
            display_df['IgG_normalized'] = "Error"
            display_df['Rating'] = "Error"
        
        # Hide results table completely from the Analysis tab
        # Results will only be visible in the Reports tab
        
        # Hide allergen analysis completely from the Analysis tab
        # This will only be visible in the Reports tab
        if False:  # Effectively disables this section
            # Sort by intensity to find strongest reactions - use either Avg_OD or IgG column
            if 'Avg_OD' in display_df.columns:
                sort_column = 'Avg_OD'
            elif 'IgG (µg/ml)' in display_df.columns:
                sort_column = 'IgG (µg/ml)'
            elif 'IgG_numeric' in display_df.columns:
                sort_column = 'IgG_numeric'
            elif 'IgG' in display_df.columns:
                sort_column = 'IgG'
            else:
                # If no sorting column is available, just show unsorted data
                st.write("### Top Allergen Reactions")
                st.write("Showing first 10 allergens:")
                st.dataframe(display_df[['Row', 'Column', 'Allergen', 'Latin Name']].head(10))
            
            sorted_df = display_df.sort_values(sort_column, ascending=False)
            
            st.write("### Top Allergen Reactions")
            st.write(f"Sorted by {sort_column} (highest first):")
            st.dataframe(sorted_df[['Row', 'Column', 'Allergen', 'Latin Name']].head(10))
        
        # Hide normalization report from Analysis tab
        if False:  # Effectively disables this section
            if 'IgG_normalized' in display_df.columns and 'Rating' in display_df.columns:
                with st.expander("Normalized Values Report", expanded=True):
                    st.write("### IgG Reactivity Classification")

                    
                    # Sort by numeric IgG values
                    norm_sorted_df = display_df.sort_values('IgG_numeric', ascending=False)
                    
                    # Count items in each category
                    highly_elevated = len(norm_sorted_df[norm_sorted_df['Rating'] == 'Highly elevated'])
                    elevated = len(norm_sorted_df[norm_sorted_df['Rating'] == 'Elevated'])
                    not_elevated = len(norm_sorted_df[norm_sorted_df['Rating'] == 'Not elevated'])
                    
                    # Create metric displays for category counts
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Highly Elevated", highly_elevated, 
                                  delta="IgG ≥ 20.0 µg/ml", delta_color="off")
                    with col2:
                        st.metric("Elevated", elevated, 
                                  delta="7.5 ≤ IgG < 20.0 µg/ml", delta_color="off")
                    
                    # Display the highly elevated and elevated allergens
                    if highly_elevated > 0:
                        st.write("#### Allergens that cause High Reaction")
                        he_df = norm_sorted_df[norm_sorted_df['Rating'] == 'Highly elevated'].copy()
                        # Rename columns for better display
                        he_df = he_df.rename(columns={
                            'IgG_normalized': 'IgG (µg/ml)',
                            'Avg_OD': 'Optical Density'
                        })
                        st.dataframe(he_df[['Allergen', 'IgG (µg/ml)']], use_container_width=True)
                    
                    if elevated > 0:
                        st.write("#### Allergens that cause Moderate Reaction")
                        e_df = norm_sorted_df[norm_sorted_df['Rating'] == 'Elevated'].copy()
                        # Rename columns for better display
                        e_df = e_df.rename(columns={
                            'IgG_normalized': 'IgG (µg/ml)',
                            'Avg_OD': 'Optical Density'
                        })
                        st.dataframe(e_df[['Allergen', 'IgG (µg/ml)']], use_container_width=True)
                    
                    if not_elevated > 0:
                        st.write("#### Unelevated Allergens")
                        ne_df = norm_sorted_df[norm_sorted_df['Rating'] == 'Not elevated'].copy()
                        # Create a new dataframe with "Unelevated" for IgG values
                        ne_display_df = ne_df[['Allergen']].copy()
                        ne_display_df['IgG (µg/ml)'] = "Unelevated"
                        st.dataframe(ne_display_df, use_container_width=True)
            
            # Top 20 allergens section removed as requested
        
        # Download results buttons
        st.markdown("### Download Options")
        
        # Download normalized results if available, otherwise download raw results
        if 'IgG_normalized' in display_df.columns and 'Rating' in display_df.columns:
            # Prepare normalized data for download
            download_df = display_df.copy()
            # Rename columns for better clarity in downloaded file
            download_df = download_df.rename(columns={
                'IgG_normalized': 'IgG (µg/ml)',
                'Avg_OD': 'Optical Density'
            })
            # Select only the relevant columns, excluding Optical Density and Rating
            # First ensure all required columns exist, adding empty ones if needed
            required_columns = ['Row', 'Column', 'Allergen', 'Latin Name', 'IgG (µg/ml)']
            for col in required_columns:
                if col not in download_df.columns:
                    download_df[col] = ''
            download_df = download_df[required_columns]
            # Replace IgG values with "< 7.5 μg/ml" for non-elevated allergens
            if 'Rating' in display_df.columns:
                rating_column = display_df['Rating'].copy()
                # Check if there are any non-elevated values
                if '< 7.5 μg/ml' in rating_column.values:
                    download_df.loc[rating_column == '< 7.5 μg/ml', 'IgG (µg/ml)'] = "< 7.5 μg/ml"
                
                # Sort by IgG values (highest first)
                has_elevated = (rating_column != '< 7.5 μg/ml').any()
                has_unelevated = (rating_column == '< 7.5 μg/ml').any()
                
                if has_elevated and has_unelevated:
                    elevated_rows = download_df.loc[rating_column != '< 7.5 μg/ml']
                    unelevated_rows = download_df.loc[rating_column == '< 7.5 μg/ml']
                    
                    # Only sort if the column exists
                    if 'Allergen' in download_df.columns:
                        unelevated_rows = unelevated_rows.sort_values('Allergen')
                        
                    download_df = pd.concat([
                        elevated_rows.sort_values('IgG (µg/ml)', ascending=False),
                        unelevated_rows
                    ])
            # If no Rating column, just keep the dataframe as is
            csv = download_df.to_csv(index=False)
            file_name = "normalized_allergen_results.csv"
        else:
            # Raw results download
            csv = display_df.to_csv(index=False)
            file_name = "microarray_analysis_results.csv"
            
        # Hide download options completely from the Analysis tab
        # Download option will only be available in the Reports tab
        
        # Show results overlaid on the processed image
        if st.session_state.processed_image is not None:
            # Grid Overlay visualization has been removed as requested
            pass
        else:
            # Show placeholder when no results are available
            st.info("No analysis results available. Go to Image Analysis and run analysis first.")

# Add Reports page
elif st.session_state.current_page == "reports":
    # Import the simplified report page module that only uses IgG (µg/ml) data
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


