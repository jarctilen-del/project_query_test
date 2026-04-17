import streamlit as st
import pandas as pd
import os
from datetime import datetime
from typing import List, Dict
import json

# Import your existing classes
from participant_query_system import ParticipantQuerySystem, PartnerInfo, ReportSaver

# Configure page
st.set_page_config(
    page_title="EU Project Partner Search",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .report-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .success-box {
        background-color: #d4edda;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'query_system' not in st.session_state:
    with st.spinner("Loading data... Please wait."):
        st.session_state.query_system = ParticipantQuerySystem()
        st.session_state.report_saver = ReportSaver()
        st.session_state.search_results = None
        st.session_state.selected_partner = None

# Sidebar for configuration
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/european-union.png", width=80)
    st.title("⚙️ Configuration")
    
    # Output folder configuration
    output_folder = st.text_input(
        "Output Folder",
        value=st.session_state.query_system.results_folder,
        help="Folder where reports will be saved"
    )
    
    if st.button("📁 Update Output Folder"):
        st.session_state.query_system.results_folder = output_folder
        st.session_state.report_saver.set_output_folder(output_folder)
        st.success(f"Output folder updated to: {output_folder}")
    
    st.divider()
    
    # Create session folder
    if st.button("📂 Create New Session Folder"):
        folder = st.session_state.report_saver.create_session_folder()
        st.success(f"Session folder created: {folder}")
    
    st.divider()
    
    # Statistics
    st.subheader("📊 Database Statistics")
    if st.session_state.query_system.all_projects_df is not None:
        st.metric("Total Projects", len(st.session_state.query_system.all_projects_df))
        
        # Count SI projects
        si_count = sum(1 for _, row in st.session_state.query_system.all_projects_df.iterrows()
                      if st.session_state.query_system._project_has_slovenian_partners(row['project_ID'])[0])
        st.metric("Projects with Slovenian Partners", si_count)
        st.metric("Partners in Database", "Loading...")

# Main content area
st.title("🔍 EU Project Partner Search System")
st.markdown("Search for partners and their collaborations with Slovenian organizations")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["🔎 Search Partners", "📄 Collaboration Reports", "📊 Statistics", "💾 Saved Outputs"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Search by Partner Name")
        partner_name = st.text_input("Enter partner name:", key="name_search")
        
        if st.button("🔍 Search by Name", key="btn_name"):
            if partner_name:
                with st.spinner("Searching..."):
                    results = st.session_state.query_system.search_partners(partner_name)
                    st.session_state.search_results = results
                    
                    if results:
                        st.success(f"Found {len(results)} partners")
                    else:
                        st.warning("No partners found")
        
    with col2:
        st.subheader("Search by Country")
        country_code = st.text_input("Enter country code (e.g., DE, FR, IT):", key="country_search")
        
        if st.button("🔍 Search by Country", key="btn_country"):
            if country_code and len(country_code) == 2:
                with st.spinner("Searching..."):
                    results = st.session_state.query_system.search_partners(country_code, search_by_country=True)
                    st.session_state.search_results = results
                    
                    if results:
                        st.success(f"Found {len(results)} partners from {country_code.upper()}")
                    else:
                        st.warning(f"No partners found from {country_code.upper()}")
            else:
                st.error("Please enter a valid 2-letter country code")
    
    # Display search results
    if st.session_state.search_results:
        st.subheader(f"📋 Search Results ({len(st.session_state.search_results)} partners)")
        
        # Convert to DataFrame for display
        results_data = []
        for i, partner in enumerate(st.session_state.search_results[:50], 1):
            results_data.append({
                "No.": i,
                "Legal Name": partner.legal_name,
                "Country": partner.country,
                "Total Funding": f"€{partner.total_eu_funding:,.0f}",
                "Total Projects": partner.total_projects,
                "SI Collaborations": partner.slovenian_projects,
                "Collaboration Ratio": f"{partner.collaboration_ratio:.1%}"
            })
        
        df_results = pd.DataFrame(results_data)
        st.dataframe(df_results, use_container_width=True, height=400)
        
        # Select partner for detailed view
        st.subheader("Select Partner for Detailed Report")
        partner_names = [p.legal_name for p in st.session_state.search_results[:50]]
        selected_name = st.selectbox("Choose a partner:", partner_names)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📄 View Details"):
                with st.spinner("Loading details..."):
                    details = st.session_state.query_system.get_partner_details(selected_name)
                    if details:
                        st.session_state.selected_partner = details
                        st.success(f"Loaded details for {selected_name}")
                    else:
                        st.error("Could not load partner details")
        
        with col2:
            if st.button("📝 Generate Report"):
                with st.spinner("Generating report..."):
                    report = st.session_state.query_system.generate_collaboration_report(selected_name)
                    st.session_state.generated_report = report
                    st.success("Report generated!")
        
        with col3:
            if st.button("💾 Save to TXT"):
                with st.spinner("Saving..."):
                    filepath = st.session_state.query_system.export_collaboration_report_to_txt(selected_name)
                    if filepath:
                        st.success(f"Report saved to: {filepath}")
                        
                        # Also save detailed info
                        details = st.session_state.query_system.get_partner_details(selected_name)
                        if details:
                            st.session_state.report_saver.save_collaboration_details(details, selected_name)
        
        # Display generated report
        if 'generated_report' in st.session_state and st.session_state.generated_report:
            with st.expander("📄 Generated Report", expanded=True):
                st.text_area("Report Content", st.session_state.generated_report, height=400)
                
                # Download button
                st.download_button(
                    label="📥 Download Report as TXT",
                    data=st.session_state.generated_report,
                    file_name=f"{selected_name}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
        
        # Display partner details
        if st.session_state.selected_partner:
            with st.expander("📊 Partner Details", expanded=True):
                details = st.session_state.selected_partner
                partner_info = details["partner_info"]
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Country", partner_info["Country"])
                with col2:
                    st.metric("Total Projects", partner_info["Total Projects"])
                with col3:
                    st.metric("SI Collaborations", partner_info["Slovenian Projects"])
                with col4:
                    st.metric("Collaboration Ratio", partner_info["Collaboration Ratio"])
                
                st.subheader("Projects with Slovenian Partners")
                if details["slovenian_projects"]:
                    projects_data = []
                    for project in details["slovenian_projects"]:
                        projects_data.append({
                            "Title": project["Title"],
                            "Acronym": project["Acronym"],
                            "Project ID": project["Project ID"],
                            "Budget": project["Total Budget"],
                            "Slovenian Partners": project["Slovenian Partners"][:50] + "..."
                        })
                    st.dataframe(pd.DataFrame(projects_data), use_container_width=True)
                else:
                    st.info("No Slovenian collaborations found")

with tab2:
    st.subheader("📄 Generate Collaboration Report")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        partner_name = st.text_input("Enter exact legal name:", key="report_name")
    
    with col2:
        st.write("")
        st.write("")
        generate_btn = st.button("🚀 Generate Report", key="generate_report_btn")
    
    if generate_btn and partner_name:
        with st.spinner("Generating report..."):
            report = st.session_state.query_system.generate_collaboration_report(partner_name)
            
            if "No data found" in report:
                st.error(report)
            else:
                st.success("Report generated successfully!")
                
                # Display report
                st.text_area("Collaboration Report", report, height=500)
                
                # Save options
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("💾 Save to File"):
                        filepath = st.session_state.query_system.export_collaboration_report_to_txt(partner_name)
                        if filepath:
                            st.success(f"Saved to: {filepath}")
                
                with col2:
                    st.download_button(
                        label="📥 Download",
                        data=report,
                        file_name=f"{partner_name}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
                
                with col3:
                    # Option to save detailed info
                    if st.button("💾 Save Details"):
                        details = st.session_state.query_system.get_partner_details(partner_name)
                        if details:
                            filepath = st.session_state.report_saver.save_collaboration_details(details, partner_name)
                            st.success(f"Details saved to: {filepath}")

with tab3:
    st.subheader("📊 System Statistics")
    
    if st.button("🔄 Refresh Statistics"):
        st.rerun()
    
    # Overall statistics
    if st.session_state.query_system.all_projects_df is not None:
        total_projects = len(st.session_state.query_system.all_projects_df)
        st.metric("Total Projects in Database", f"{total_projects:,}")
        
        # Count SI projects
        si_count = 0
        si_projects_list = []
        for idx, row in st.session_state.query_system.all_projects_df.iterrows():
            has_si, si_partners = st.session_state.query_system._project_has_slovenian_partners(row['project_ID'])
            if has_si:
                si_count += 1
                si_projects_list.append({
                    "Title": row['title'],
                    "Project ID": row['project_ID'],
                    "Slovenian Partners": ", ".join(si_partners)
                })
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Projects with Slovenian Partners", f"{si_count:,}")
            st.metric("Percentage", f"{(si_count/total_projects)*100:.1f}%")
        
        with col2:
            st.metric("Projects without Slovenian Partners", f"{total_projects - si_count:,}")
        
        # Display SI projects
        if si_projects_list:
            st.subheader(f"Projects with Slovenian Partners ({len(si_projects_list)})")
            df_si = pd.DataFrame(si_projects_list)
            st.dataframe(df_si, use_container_width=True, height=300)
    
    # Export statistics
    if st.button("📊 Export Statistics Report"):
        stats_report = []
        stats_report.append("=" * 80)
        stats_report.append("SYSTEM STATISTICS REPORT")
        stats_report.append("=" * 80)
        stats_report.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        stats_report.append("")
        
        if st.session_state.query_system.all_projects_df is not None:
            stats_report.append(f"Total Projects: {total_projects}")
            stats_report.append(f"Projects with Slovenian Partners: {si_count}")
            stats_report.append(f"Percentage: {(si_count/total_projects)*100:.1f}%")
        
        stats_text = "\n".join(stats_report)
        
        st.download_button(
            label="📥 Download Statistics Report",
            data=stats_text,
            file_name=f"statistics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

with tab4:
    st.subheader("💾 Saved Outputs")
    
    st.info("All reports and outputs are saved to your specified output folder.")
    
    output_folder = st.session_state.query_system.results_folder
    st.write(f"**Current output folder:** `{output_folder}`")
    
    if os.path.exists(output_folder):
        # List files in output folder
        files = []
        for root, dirs, filenames in os.walk(output_folder):
            for filename in filenames:
                if filename.endswith('.txt') or filename.endswith('.csv'):
                    files.append({
                        "File": filename,
                        "Folder": os.path.relpath(root, output_folder),
                        "Size": f"{os.path.getsize(os.path.join(root, filename)) / 1024:.1f} KB",
                        "Modified": datetime.fromtimestamp(os.path.getmtime(os.path.join(root, filename))).strftime('%Y-%m-%d %H:%M:%S')
                    })
        
        if files:
            df_files = pd.DataFrame(files)
            st.dataframe(df_files, use_container_width=True)
            
            # Open folder button
            if st.button("📂 Open Output Folder"):
                import subprocess
                import platform
                
                if platform.system() == "Windows":
                    os.startfile(output_folder)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", output_folder])
                else:  # Linux
                    subprocess.run(["xdg-open", output_folder])
        else:
            st.info("No files saved yet. Generate some reports to see them here.")

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: gray;">
    <p>EU Project Partner Search System | Data source: European Commission</p>
    <p>Last updated: {}</p>
</div>
""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')), unsafe_allow_html=True)
