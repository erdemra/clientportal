"""
Client Portal Website Design page for configuring the client-facing portal
"""
import streamlit as st
import json
from datetime import datetime

def render_client_portal_design_page():
    """
    Render the client portal design and configuration page
    """
    st.subheader("Client Portal Website Design")
    st.markdown("Design and configure the client-facing portal where patients access their reports and additional resources.")
    
    # Portal overview
    st.markdown("---")
    st.subheader("🌐 Portal Overview")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Current Features:**
        - Secure client login with unique credentials
        - PDF report download access
        - Individual patient data viewing
        - Report access tracking and timestamps
        """)
    
    with col2:
        st.markdown("""
        **Planned Features:**
        - Nutritional guidance and recommendations
        - Educational content about food intolerances
        - Progress tracking over multiple tests
        - Direct messaging with practitioners
        """)
    
    # Website branding and theme
    st.markdown("---")
    st.subheader("🎨 Branding & Theme Configuration")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Color Scheme**")
        primary_color = st.color_picker("Primary Color", "#4F79DF")
        secondary_color = st.color_picker("Secondary Color", "#6C757D")
        accent_color = st.color_picker("Accent Color", "#28A745")
        
        st.markdown("**Typography**")
        font_family = st.selectbox("Font Family", ["Inter", "Roboto", "Open Sans", "Lato", "Poppins"])
        font_size = st.slider("Base Font Size (px)", 14, 20, 16)
    
    with col2:
        st.markdown("**Logo & Images**")
        logo_url = st.text_input("Logo URL", "https://your-domain.com/logo.png")
        favicon_url = st.text_input("Favicon URL", "https://your-domain.com/favicon.ico")
        background_image = st.text_input("Background Image URL (optional)", "")
        
        st.markdown("**Portal Settings**")
        portal_title = st.text_input("Portal Title", "Pinnertest Client Portal")
        welcome_message = st.text_area("Welcome Message", 
            "Welcome to your personalized food intolerance report portal. Access your test results and nutritional guidance securely.")
    
    # Content management
    st.markdown("---")
    st.subheader("📝 Content Management")
    
    # Tabs for different content sections
    content_tab1, content_tab2, content_tab3, content_tab4 = st.tabs([
        "Homepage Content", 
        "Nutritional Info", 
        "Educational Resources", 
        "Contact & Support"
    ])
    
    with content_tab1:
        st.markdown("**Homepage Content Configuration**")
        
        hero_title = st.text_input("Hero Section Title", "Your Personal Food Intolerance Report")
        hero_subtitle = st.text_area("Hero Section Subtitle", 
            "Understand your body's unique responses to different foods and take control of your health journey.")
        
        # Feature highlights
        st.markdown("**Feature Highlights (3 sections)**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            feature1_icon = st.selectbox("Feature 1 Icon", ["📊", "🧬", "⚡", "🎯", "💡"], key="f1")
            feature1_title = st.text_input("Feature 1 Title", "Detailed Analysis", key="f1t")
            feature1_desc = st.text_area("Feature 1 Description", 
                "Comprehensive breakdown of your food intolerance levels", key="f1d")
        
        with col2:
            feature2_icon = st.selectbox("Feature 2 Icon", ["🥗", "📚", "🎯", "💪", "🌱"], key="f2")
            feature2_title = st.text_input("Feature 2 Title", "Nutritional Guidance", key="f2t")
            feature2_desc = st.text_area("Feature 2 Description", 
                "Personalized recommendations for your dietary needs", key="f2d")
        
        with col3:
            feature3_icon = st.selectbox("Feature 3 Icon", ["👥", "📞", "💬", "🔒", "⭐"], key="f3")
            feature3_title = st.text_input("Feature 3 Title", "Expert Support", key="f3t")
            feature3_desc = st.text_area("Feature 3 Description", 
                "Direct access to healthcare professionals and guidance", key="f3d")
    
    with content_tab2:
        st.markdown("**Nutritional Information Content**")
        
        nutrition_intro = st.text_area("Nutrition Section Introduction", 
            "Based on your test results, here are personalized nutritional recommendations to help you optimize your diet.")
        
        # Food category recommendations
        st.markdown("**Food Category Recommendations**")
        
        recommended_foods = st.text_area("Recommended Foods Content", 
            "Foods that showed low reactivity in your test and are generally well-tolerated by your system.")
        
        foods_to_limit = st.text_area("Foods to Limit Content", 
            "Foods that showed moderate reactivity. Consider reducing frequency or portion sizes.")
        
        foods_to_avoid = st.text_area("Foods to Avoid Content", 
            "Foods that showed high reactivity. We recommend avoiding these temporarily while your system recovers.")
        
        meal_planning_tips = st.text_area("Meal Planning Tips", 
            "Practical advice for meal planning, cooking methods, and ingredient substitutions based on your results.")
    
    with content_tab3:
        st.markdown("**Educational Resources**")
        
        # Resource links and articles
        st.markdown("**Article Library**")
        article1_title = st.text_input("Article 1 Title", "Understanding Food Intolerances")
        article1_url = st.text_input("Article 1 URL", "")
        
        article2_title = st.text_input("Article 2 Title", "The Science Behind IgG Testing")
        article2_url = st.text_input("Article 2 URL", "")
        
        article3_title = st.text_input("Article 3 Title", "Elimination Diet Guidelines")
        article3_url = st.text_input("Article 3 URL", "")
        
        # Video resources
        st.markdown("**Video Resources**")
        video1_title = st.text_input("Video 1 Title", "How to Read Your Report")
        video1_url = st.text_input("Video 1 URL (YouTube/Vimeo)", "")
        
        video2_title = st.text_input("Video 2 Title", "Meal Planning Made Easy")
        video2_url = st.text_input("Video 2 URL (YouTube/Vimeo)", "")
        
        # Downloadable resources
        st.markdown("**Downloadable Resources**")
        resource1_name = st.text_input("Resource 1 Name", "Food Diary Template")
        resource1_url = st.text_input("Resource 1 Download URL", "")
        
        resource2_name = st.text_input("Resource 2 Name", "Recipe Substitution Guide")
        resource2_url = st.text_input("Resource 2 Download URL", "")
    
    with content_tab4:
        st.markdown("**Contact & Support Information**")
        
        support_email = st.text_input("Support Email", "support@pinnertest.com")
        support_phone = st.text_input("Support Phone", "+1 (555) 123-4567")
        
        office_hours = st.text_area("Office Hours", 
            "Monday - Friday: 9:00 AM - 6:00 PM EST\nSaturday: 10:00 AM - 4:00 PM EST\nSunday: Closed")
        
        faq_content = st.text_area("Frequently Asked Questions", 
            "Q: How long do I need to avoid reactive foods?\nA: We typically recommend 3-6 months of avoidance...\n\nQ: Can I retest foods later?\nA: Yes, retesting after 6-12 months is recommended...")
        
        # Contact form settings
        st.markdown("**Contact Form Configuration**")
        enable_contact_form = st.checkbox("Enable Contact Form", True)
        contact_form_recipients = st.text_input("Form Recipients (comma-separated emails)", 
            "support@pinnertest.com, info@pinnertest.com")
    
    # Technical settings
    st.markdown("---")
    st.subheader("⚙️ Technical Configuration")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Security Settings**")
        session_timeout = st.slider("Session Timeout (minutes)", 15, 120, 60)
        password_expiry = st.slider("Password Expiry (days)", 30, 365, 90)
        max_login_attempts = st.slider("Max Login Attempts", 3, 10, 5)
        
        st.markdown("**Performance Settings**")
        enable_caching = st.checkbox("Enable Caching", True)
        cache_duration = st.slider("Cache Duration (hours)", 1, 24, 6)
    
    with col2:
        st.markdown("**Analytics & Tracking**")
        enable_analytics = st.checkbox("Enable Analytics", True)
        google_analytics_id = st.text_input("Google Analytics ID", "")
        
        st.markdown("**Notifications**")
        enable_email_notifications = st.checkbox("Email Notifications", True)
        admin_email = st.text_input("Admin Email for Notifications", "admin@pinnertest.com")
    
    # Save configuration
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save Configuration", type="primary", use_container_width=True):
            # Here you would save all the configuration to the database
            st.success("Portal configuration saved successfully!")
    
    with col2:
        if st.button("👀 Preview Portal", use_container_width=True):
            st.info("Portal preview functionality would open the client portal in a new tab")
    
    with col3:
        if st.button("🚀 Deploy Changes", use_container_width=True):
            st.info("Changes would be deployed to the live client portal")
    
    # Portal URL and access info
    st.markdown("---")
    st.subheader("🔗 Portal Access Information")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Portal URLs**")
        st.code("Production: https://portal.pinnertest.com", language=None)
        st.code("Staging: https://staging-portal.pinnertest.com", language=None)
        
    with col2:
        st.markdown("**Quick Actions**")
        if st.button("📋 Copy Client Login Instructions"):
            instructions = """
Client Portal Access Instructions:

1. Visit: https://portal.pinnertest.com
2. Use your unique credentials:
   - Username: [PROVIDED_USERNAME]
   - Password: [PROVIDED_PASSWORD]
3. Download your PDF report
4. View nutritional recommendations
5. Access educational resources

For support: support@pinnertest.com
            """
            st.code(instructions, language=None)
            st.success("Instructions ready to copy!")