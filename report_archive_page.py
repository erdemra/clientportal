"""
Report Archive page for viewing and managing all generated client reports
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from db import db_manager

def render_report_archive_page():
    """
    Render the report archive page with all client reports
    """
    st.subheader("Report Archive")
    st.markdown("View and manage all generated client reports with their access credentials.")
    
    # Get all client reports from database
    reports = db_manager.get_all_client_reports()
    
    if not reports:
        st.info("No reports found. Generate reports in the Reporting tab to see them here.")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Reports", len(reports))
    with col2:
        active_reports = len([r for r in reports if r['is_active']])
        st.metric("Active Reports", active_reports)
    with col3:
        accessed_reports = len([r for r in reports if r['last_accessed']])
        st.metric("Accessed Reports", accessed_reports)
    with col4:
        recent_reports = len([r for r in reports if (datetime.now() - r['report_date']).days <= 7])
        st.metric("This Week", recent_reports)
    
    st.markdown("---")
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        search_term = st.text_input("🔍 Search by patient name or ID", placeholder="Enter patient name or ID")
    with col2:
        status_filter = st.selectbox("Filter by status", ["All", "Active", "Inactive", "Accessed", "Not Accessed"])
    
    # Filter reports based on search and status
    filtered_reports = reports
    if search_term:
        filtered_reports = [r for r in filtered_reports if 
                          search_term.lower() in r['patient_name'].lower() or 
                          search_term.lower() in r['patient_id'].lower()]
    
    if status_filter == "Active":
        filtered_reports = [r for r in filtered_reports if r['is_active']]
    elif status_filter == "Inactive":
        filtered_reports = [r for r in filtered_reports if not r['is_active']]
    elif status_filter == "Accessed":
        filtered_reports = [r for r in filtered_reports if r['last_accessed']]
    elif status_filter == "Not Accessed":
        filtered_reports = [r for r in filtered_reports if not r['last_accessed']]
    
    st.markdown(f"**Showing {len(filtered_reports)} of {len(reports)} reports**")
    
    # Display reports in a table format
    if filtered_reports:
        for report in filtered_reports:
            with st.expander(f"📄 {report['patient_name']} (ID: {report['patient_id']}) - {report['report_date'].strftime('%Y-%m-%d %H:%M')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Patient:** {report['patient_name']}")
                    st.write(f"**Patient ID:** {report['patient_id']}")
                    st.write(f"**Practitioner:** {report['practitioner'] or 'Not specified'}")
                    st.write(f"**Report Date:** {report['report_date'].strftime('%Y-%m-%d %H:%M')}")
                    
                    # Status indicators
                    status_color = "green" if report['is_active'] else "red"
                    status_text = "Active" if report['is_active'] else "Inactive"
                    st.markdown(f"**Status:** <span style='color: {status_color}'>{status_text}</span>", unsafe_allow_html=True)
                    
                    if report['last_accessed']:
                        st.write(f"**Last Accessed:** {report['last_accessed'].strftime('%Y-%m-%d %H:%M')}")
                    else:
                        st.write("**Last Accessed:** Never")
                
                with col2:
                    st.markdown("**🔑 Client Access Credentials:**")
                    
                    # Display credentials in a copy-friendly format
                    st.code(f"Username: {report['username']}\nPassword: {report['password']}", language=None)
                    
                    # Generate client portal URL (this would be your actual domain)
                    portal_url = f"https://your-portal-domain.com/client-login"
                    st.markdown(f"**Portal URL:** `{portal_url}`")
                    
                    # Action buttons
                    button_col1, button_col2 = st.columns(2)
                    with button_col1:
                        if st.button(f"📧 Email Credentials", key=f"email_{report['id']}"):
                            st.info("Email functionality would be implemented here")
                    
                    with button_col2:
                        toggle_text = "Deactivate" if report['is_active'] else "Activate"
                        if st.button(f"🔒 {toggle_text}", key=f"toggle_{report['id']}"):
                            st.info(f"Report status toggle functionality would be implemented here")
    
    # Bulk operations
    st.markdown("---")
    st.subheader("Bulk Operations")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📧 Email All Active Credentials"):
            active_count = len([r for r in reports if r['is_active']])
            st.success(f"Would email credentials to {active_count} active clients")
    
    with col2:
        if st.button("📊 Export Report Data"):
            # Create a summary dataframe for export
            export_data = []
            for report in reports:
                export_data.append({
                    'Patient Name': report['patient_name'],
                    'Patient ID': report['patient_id'],
                    'Practitioner': report['practitioner'],
                    'Report Date': report['report_date'].strftime('%Y-%m-%d %H:%M'),
                    'Username': report['username'],
                    'Password': report['password'],
                    'Status': 'Active' if report['is_active'] else 'Inactive',
                    'Last Accessed': report['last_accessed'].strftime('%Y-%m-%d %H:%M') if report['last_accessed'] else 'Never'
                })
            
            df = pd.DataFrame(export_data)
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_data,
                file_name=f"report_archive_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    with col3:
        if st.button("🗑️ Cleanup Old Reports"):
            st.info("Cleanup functionality would be implemented here")