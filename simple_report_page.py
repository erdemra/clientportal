"""
Simplified report page that processes complete CSV files with client and allergen data
"""
import streamlit as st
import pandas as pd
import os
from datetime import datetime
import zipfile
import io
import separate_pages_report
import improved_report
import improved_report_new
import fixed_report_layout

def render_reports_page():
    """
    Render the reports page with data upload and report generation
    """
    st.subheader("Generate Reports")
    
    # Initialize session state for multiple uploads
    if 'processed_reports' not in st.session_state:
        st.session_state.processed_reports = {}
    if 'generated_pdfs' not in st.session_state:
        st.session_state.generated_pdfs = {}
    
    # Setup client_info in session state if not present
    if 'client_info' not in st.session_state:
        st.session_state.client_info = {
            'name': 'Joseph Rahwanci',
            'dob': '12/06/1972',
            'gender': 'Male',
            'specimen': 'Dry Blood',
            'patient_id': '9178281823',
            'email': 'joe@incousa.com',
            'draw_date': '15/05/2025',
            'collection_date': '16/05/2025',
            'report_date': '17/05/2025',
            'practitioner': 'Dr. Sarah Johnson'
        }
    
    # Multiple upload and report generation section
    st.subheader("Upload Complete Report Data")
    st.markdown("Upload one or more CSV files containing client information and allergen data to generate reports.")
    
    # File uploader for multiple CSV files
    uploaded_data_files = st.file_uploader(
        "Choose CSV files with client and allergen data", 
        type=['csv'], 
        accept_multiple_files=True,
        help="Upload CSV files with both client information and allergen data. Each file should have client details in the first row."
    )
    
    if uploaded_data_files:
        # Process multiple files
        for file_idx, uploaded_file in enumerate(uploaded_data_files):
            try:
                # Read the uploaded CSV file
                uploaded_df = pd.read_csv(uploaded_file)
                
                # Check if required columns are present
                required_columns = ['Category', 'Allergen', 'IgG', 'Sample ID', 'Name', 'Gender', 'Date of Birth', 'Practitioner', 'Date of Receipt', 'Report Date']
                missing_columns = [col for col in required_columns if col not in uploaded_df.columns]
                
                if missing_columns:
                    st.error(f"File '{uploaded_file.name}' is missing required columns: {', '.join(missing_columns)}")
                    continue
                
                # Extract client information from the first row
                first_row = uploaded_df.iloc[0]
                patient_name = str(first_row['Name']) if pd.notna(first_row['Name']) else f"Patient_{file_idx+1}"
                patient_id = str(first_row['Sample ID']) if pd.notna(first_row['Sample ID']) else f"ID_{file_idx+1}"
                
                # Extract the actual date of birth from the CSV data
                actual_dob = str(first_row['Date of Birth']) if pd.notna(first_row['Date of Birth']) else ''
                
                extracted_client_info = {
                    'patient_id': patient_id,
                    'name': patient_name,
                    'gender': str(first_row['Gender']) if pd.notna(first_row['Gender']) else '',
                    'dob': actual_dob,  # Use the actual DOB from CSV
                    'practitioner': str(first_row['Practitioner']) if pd.notna(first_row['Practitioner']) else '',
                    'collection_date': str(first_row['Date of Receipt']) if pd.notna(first_row['Date of Receipt']) else '',
                    'report_date': str(first_row['Report Date']) if pd.notna(first_row['Report Date']) else '',
                    'specimen': 'Dry Blood',
                    'email': ''
                }
                
                # Convert the uploaded data to the format expected by the report generator
                processed_data = []
                for idx, row in uploaded_df.iterrows():
                    # Convert IgG values - handle "Unelevated" and numeric values
                    igg_value = row['IgG']
                    if pd.isna(igg_value) or str(igg_value).lower() == 'unelevated':
                        igg_numeric = 0.0
                    else:
                        try:
                            igg_numeric = float(igg_value)
                        except:
                            igg_numeric = 0.0
                    
                    processed_data.append({
                        'Row': idx + 1,
                        'Column': 1,
                        'Allergen': str(row['Allergen']) if pd.notna(row['Allergen']) else '',
                        'Latin Name': '',
                        'Category': str(row['Category']) if pd.notna(row['Category']) else '',
                        'IgG (µg/ml)': igg_numeric
                    })
                
                # Create processed dataframe
                processed_df = pd.DataFrame(processed_data)
                
                # Store processed data with unique identifier
                file_key = f"{patient_name}_{patient_id}_{file_idx}"
                st.session_state.processed_reports[file_key] = {
                    'client_info': extracted_client_info,
                    'data': processed_df,
                    'filename': uploaded_file.name
                }
                
            except Exception as e:
                st.error(f"Error processing file '{uploaded_file.name}': {str(e)}")
                continue
        
        # Display summary of processed files
        if st.session_state.processed_reports:
            st.success(f"✅ Successfully processed {len(st.session_state.processed_reports)} file(s)")
            
            # Show summary of all processed files
            st.subheader("Processed Files Summary")
            for file_key, report_data in st.session_state.processed_reports.items():
                client_info = report_data['client_info']
                data_df = report_data['data']
                elevated_count = len(data_df[data_df['IgG (µg/ml)'] > 0])
                
                with st.expander(f"📄 {client_info['name']} (ID: {client_info['patient_id']})"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Allergens", len(data_df))
                    with col2:
                        st.metric("Elevated Allergens", elevated_count)
                    with col3:
                        st.metric("Categories", len(data_df['Category'].unique()))
            
            st.markdown("---")
            
            # Batch operations
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Generate All PDF Reports", use_container_width=True):
                    with st.spinner("Generating all PDF reports..."):
                        success_count = 0
                        for file_key, report_data in st.session_state.processed_reports.items():
                            try:
                                pdf_data, _, _ = fixed_report_layout.create_report(
                                    report_data['data'],
                                    report_data['client_info'],
                                    output_format='both'
                                )
                                if pdf_data:
                                    # Save to database with client credentials
                                    from db import db_manager
                                    credentials = db_manager.save_client_report(
                                        report_data['client_info'],
                                        pdf_data,
                                        report_data['data']
                                    )
                                    
                                    if credentials:
                                        st.session_state.generated_pdfs[file_key] = {
                                            'pdf_data': pdf_data,
                                            'filename': f"{report_data['client_info']['patient_id']}_{report_data['client_info']['name']}.pdf",
                                            'credentials': credentials
                                        }
                                        success_count += 1
                            except Exception as e:
                                st.error(f"Failed to generate report for {report_data['client_info']['name']}: {str(e)}")
                        
                        if success_count > 0:
                            st.success(f"✅ Generated {success_count} PDF reports successfully!")
                            
                            # Display client credentials
                            st.subheader("🔑 Client Access Credentials")
                            st.markdown("Share these credentials with your clients to access their reports:")
                            
                            for file_key, pdf_data in st.session_state.generated_pdfs.items():
                                if 'credentials' in pdf_data:
                                    cred = pdf_data['credentials']
                                    with st.expander(f"📄 {cred['patient_name']} (ID: {cred['patient_id']})"):
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            st.code(f"Username: {cred['username']}\nPassword: {cred['password']}", language=None)
                                        with col2:
                                            st.markdown("**Portal URL:**")
                                            st.code("https://portal.pinnertest.com/client-login", language=None)
                            
                            st.rerun()
            
            with col2:
                # Download all processed data as CSV files in a zip
                if st.button("📥 Download All Data (ZIP)", use_container_width=True):
                    # Create zip file with all CSV data
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        for file_key, report_data in st.session_state.processed_reports.items():
                            csv_data = report_data['data'].to_csv(index=False)
                            filename = f"{report_data['client_info']['patient_id']}_{report_data['client_info']['name']}_data.csv"
                            zip_file.writestr(filename, csv_data)
                    
                    zip_buffer.seek(0)
                    st.download_button(
                        label="⬇️ Download CSV ZIP",
                        data=zip_buffer.getvalue(),
                        file_name=f"allergen_data_batch_{datetime.now().strftime('%Y%m%d')}.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
            
            with col3:
                # Download all PDF reports in a zip (only if PDFs are generated)
                if st.session_state.generated_pdfs:
                    if st.button("📄 Download All PDFs (ZIP)", use_container_width=True):
                        # Create zip file with all PDF reports
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            for file_key, pdf_data in st.session_state.generated_pdfs.items():
                                zip_file.writestr(pdf_data['filename'], pdf_data['pdf_data'])
                        
                        zip_buffer.seek(0)
                        st.download_button(
                            label="⬇️ Download PDF ZIP",
                            data=zip_buffer.getvalue(),
                            file_name=f"reports_batch_{datetime.now().strftime('%Y%m%d')}.zip",
                            mime="application/zip",
                            use_container_width=True
                        )
                else:
                    st.markdown('<div style="color: #666666; font-size: 0.85em; padding: 8px; text-align: center; font-style: italic;">Generate PDFs first</div>', unsafe_allow_html=True)
            
            # Clear all processed data button
            st.markdown("---")
            if st.button("🗑️ Clear All Data", type="secondary"):
                st.session_state.processed_reports = {}
                st.session_state.generated_pdfs = {}
                st.success("All data cleared!")
                st.rerun()
