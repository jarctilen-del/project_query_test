import streamlit as st
import pandas as pd
import os
import json
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime

# Try to import the API fetcher, but handle if not available
try:
    from sedia_api_fetchers.EUFT_retrieve_projects import SEDIA_GET_PROJECTS
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False
    st.warning("SEDIA API fetcher not available. Using sample data or cached files.")

# ---------------------------------------------------------------
# DATA CLASSES
# ---------------------------------------------------------------
@dataclass
class ProjectInfo:
    """Data class to store project information."""
    project_id: str
    title: str
    acronym: str
    website: str
    start_date: str
    end_date: str
    total_budget: float
    has_slovenian_partners: bool
    slovenian_partners: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for display."""
        return {
            "Project ID": self.project_id,
            "Title": self.title,
            "Acronym": self.acronym,
            "Website": self.website,
            "Start Date": self.start_date,
            "End Date": self.end_date,
            "Total Budget": f"€{self.total_budget:,.0f}",
            "Has Slovenian Partners": self.has_slovenian_partners,
            "Slovenian Partners": ", ".join(self.slovenian_partners) if self.slovenian_partners else "None"
        }

@dataclass
class PartnerInfo:
    """Data class to store partner/organization information."""
    legal_name: str
    country: str
    total_eu_funding: float
    total_projects: int
    slovenian_projects: int
    collaboration_ratio: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for display."""
        return {
            "Legal Name": self.legal_name,
            "Country": self.country,
            "Total EU Funding": f"€{self.total_eu_funding:,.0f}",
            "Total Projects": self.total_projects,
            "Slovenian Projects": self.slovenian_projects,
            "Collaboration Ratio": f"{self.collaboration_ratio:.1%}"
        }

# ---------------------------------------------------------------
# REPORT SAVING UTILITIES
# ---------------------------------------------------------------
class ReportSaver:
    """Utility class for saving reports to files."""
    
    def __init__(self, output_folder: str = None):
        """Initialize the report saver with an output folder."""
        self.output_folder = output_folder or os.getcwd()
        self.current_session_folder = None
    
    def set_output_folder(self, folder_path: str):
        """Set the output folder for saving reports."""
        self.output_folder = folder_path
        os.makedirs(self.output_folder, exist_ok=True)
    
    def create_session_folder(self) -> str:
        """Create a timestamped folder for the current session."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_folder = os.path.join(self.output_folder, f"session_{timestamp}")
        os.makedirs(session_folder, exist_ok=True)
        self.current_session_folder = session_folder
        return session_folder
    
    def save_report(self, content: str, filename: str, subfolder: str = None) -> str:
        """Save report content to a file."""
        if self.current_session_folder:
            save_dir = self.current_session_folder
            if subfolder:
                save_dir = os.path.join(save_dir, subfolder)
        else:
            save_dir = self.output_folder
        
        os.makedirs(save_dir, exist_ok=True)
        
        if not filename.endswith('.txt'):
            filename += '.txt'
        
        filepath = os.path.join(save_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath
    
    def save_search_results(self, partners: List[PartnerInfo], search_term: str, search_type: str = 'name') -> str:
        """Save search results to a file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_term = "".join(c for c in search_term if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"search_{search_type}_{safe_term}_{timestamp}.txt"
        
        lines = []
        lines.append("=" * 80)
        lines.append(f"SEARCH RESULTS: {search_term.upper()} (by {search_type})")
        lines.append("=" * 80)
        lines.append(f"Search performed on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Total partners found: {len(partners)}")
        lines.append("")
        
        if partners:
            lines.append("-" * 120)
            lines.append(f"{'No.':<6} {'Legal Name':<45} {'Country':<10} {'Total Funding':<18} {'Projects':<12} {'SI Collab.':<12} {'Ratio':<10}")
            lines.append("-" * 120)
            
            for i, partner in enumerate(partners, 1):
                lines.append(f"{i:<6} {partner.legal_name[:43]:<45} {partner.country:<10} "
                           f"€{partner.total_eu_funding:,.0f} {'':<3} {partner.total_projects:<12} "
                           f"{partner.slovenian_projects:<12} {partner.collaboration_ratio:.1%}")
            
            lines.append("-" * 120)
        else:
            lines.append("No partners found matching the search criteria.")
        
        lines.append("")
        lines.append("=" * 80)
        
        content = "\n".join(lines)
        return self.save_report(content, filename, "search_results")
    
    def save_collaboration_details(self, details: Dict, legal_name: str) -> str:
        """Save collaboration details to a file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in legal_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_name}_collaboration_details_{timestamp}.txt"
        
        partner_info = details["partner_info"]
        all_projects = details["all_projects"]
        slovenian_projects = details["slovenian_projects"]
        non_slovenian_projects = details.get("non_slovenian_projects", [])
        
        lines = []
        lines.append("=" * 80)
        lines.append(f"PARTNER DETAILS: {partner_info['Legal Name']}")
        lines.append("=" * 80)
        lines.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        lines.append("PARTNER INFORMATION:")
        lines.append("-" * 40)
        for key, value in partner_info.items():
            lines.append(f"  {key}: {value}")
        lines.append("")
        
        lines.append("COLLABORATION SUMMARY:")
        lines.append("-" * 40)
        lines.append(f"  Total Projects: {details['total_projects']}")
        lines.append(f"  Slovenian Collaborations: {details['slovenian_collaborations']}")
        lines.append(f"  Non-Slovenian Projects: {len(non_slovenian_projects)}")
        lines.append(f"  Collaboration Ratio: {partner_info['Collaboration Ratio']}")
        lines.append("")
        
        # Show ALL projects (both Slovenian and non-Slovenian)
        if all_projects:
            lines.append(f"ALL PROJECTS ({len(all_projects)}):")
            lines.append("-" * 80)
            
            for i, project in enumerate(all_projects, 1):
                si_status = "✓ WITH SLOVENIAN PARTNERS" if project['Has Slovenian Partners'] else "✗ NO SLOVENIAN PARTNERS"
                lines.append(f"\n{i}. {project['Title']}")
                lines.append(f"   Acronym: {project['Acronym']}")
                lines.append(f"   Project ID: {project['Project ID']}")
                lines.append(f"   Status: {si_status}")
                lines.append(f"   Website: {project['Website']}")
                lines.append(f"   Duration: {project['Start Date']} to {project['End Date']}")
                lines.append(f"   Budget: {project['Total Budget']}")
                if project['Has Slovenian Partners']:
                    lines.append(f"   Slovenian Partners: {project['Slovenian Partners']}")
        else:
            lines.append("NO PROJECTS FOUND FOR THIS PARTNER")
        
        lines.append("")
        lines.append("=" * 80)
        
        content = "\n".join(lines)
        return self.save_report(content, filename, "collaboration_details")

# ---------------------------------------------------------------
# PARTICIPANT QUERY SYSTEM
# ---------------------------------------------------------------
class ParticipantQuerySystem:
    """System for querying project participants and their collaborations with Slovenian partners."""
    
    def __init__(self, results_folder: str = "results"):
        """Initialize the query system."""
        self.results_folder = results_folder
        self.main_file = os.path.join(results_folder, "edf_comprehensive_analysis.xlsx")
        
        # Initialize data structures
        self.all_projects_df = None
        self.filtered_projects_df = None
        self.foreign_partners_df = None
        self.partner_projects_cache = {}
        self.project_has_slo_cache = {}
        
        # Create results folder if it doesn't exist
        os.makedirs(results_folder, exist_ok=True)
        
        # Load data
        self._load_data()
    
    def _load_data(self) -> None:
        """Load data from Excel file or fetch from API if not available."""
        if os.path.exists(self.main_file):
            st.info(f"Loading data from: {self.main_file}")
            try:
                self.all_projects_df = pd.read_excel(self.main_file, sheet_name='All_Projects')
                st.success("Data loaded successfully!")
            except Exception as e:
                st.error(f"Error loading data: {e}")
                if API_AVAILABLE:
                    self._fetch_fresh_data()
                else:
                    st.error("API not available and no cached data found.")
        else:
            if API_AVAILABLE:
                st.info("Data file not found. Fetching fresh data from API...")
                self._fetch_fresh_data()
            else:
                st.error("No data file found and API is not available. Please ensure the data file exists or install the API package.")
    
    def _fetch_fresh_data(self) -> None:
        """Fetch fresh data from the API."""
        with st.spinner("Fetching project data from API... This may take a few moments."):
            try:
                project_fetcher = SEDIA_GET_PROJECTS(flatten_metadata=True)
                projects_df = project_fetcher.get('edf', save=False)
                
                # Clean and prepare data
                column_mapping = {
                    "metadata_title": "title",
                    "metadata_acronym": "acronym",
                    "metadata_callIdentifier": "call_ID",
                    "metadata_overallBudget": "budget",
                    "metadata_participants": "participants",
                    "metadata_programmes": "programmes",
                    "metadata_legalEntityNames": "legal_entity_names",
                    "metadata_countries": "countries",
                    "metadata_projectId": "project_ID",
                    "metadata_startDate": "start_date",
                    "metadata_endDate": "end_date",
                    "metadata_freeKeywords": "keywords",
                }
                
                required_columns = list(column_mapping.keys())
                self.all_projects_df = projects_df[required_columns].rename(columns=column_mapping)
                
                # Filter projects with Slovenian participants
                self.filtered_projects_df = self._filter_by_country(self.all_projects_df, {"SI"})
                
                # Filter by date
                self.filtered_projects_df = self.filtered_projects_df[
                    self.filtered_projects_df["end_date"] > "2025-12-01T00:00:00.000+0100"
                ]
                
                # Save to Excel for future use
                try:
                    with pd.ExcelWriter(self.main_file, engine='openpyxl') as writer:
                        self.all_projects_df.to_excel(writer, sheet_name='All_Projects', index=False)
                        if self.filtered_projects_df is not None:
                            self.filtered_projects_df.to_excel(writer, sheet_name='Projects_from_SI', index=False)
                except:
                    pass
                
                st.success(f"Total projects loaded: {len(self.all_projects_df)}")
                st.info(f"Projects with Slovenian partners: {len(self.filtered_projects_df)}")
                
            except Exception as e:
                st.error(f"Error fetching data: {e}")
                st.error("Please check your API connection and try again.")
    
    def _filter_by_country(self, df: pd.DataFrame, countries: set) -> pd.DataFrame:
        """Filter projects containing participants from specified countries."""
        def has_country_participant(participant_list):
            if not isinstance(participant_list, list):
                return False
            
            for participant in participant_list:
                country = participant.get('address_country_abbreviation')
                if country in countries:
                    return True
            return False
        
        return df[df['participants'].apply(has_country_participant)]
    
    def _extract_project_links(self, participants_list: List[Dict]) -> List[str]:
        """Extract project website links from participants data."""
        websites = set()
        for participant in participants_list:
            url = participant.get('url')
            if url and isinstance(url, str) and url.startswith(('http://', 'https://')):
                websites.add(url)
        return list(websites)
    
    def _get_project_website(self, project_id: str) -> str:
        """Get project website from project data."""
        if project_id in self.partner_projects_cache:
            project_info = self.partner_projects_cache[project_id]
            if hasattr(project_info, 'website') and project_info.website:
                return project_info.website
        
        project_row = self.all_projects_df[self.all_projects_df['project_ID'] == project_id]
        if not project_row.empty:
            participants = project_row.iloc[0]['participants']
            if isinstance(participants, list):
                websites = self._extract_project_links(participants)
                if websites:
                    return websites[0]
        
        return f"https://cordis.europa.eu/project/id/{project_id}"
    
    def _project_has_slovenian_partners(self, project_id: str) -> Tuple[bool, List[str]]:
        """Check if a project has Slovenian partners."""
        if project_id in self.project_has_slo_cache:
            return self.project_has_slo_cache[project_id]
        
        project_row = self.all_projects_df[self.all_projects_df['project_ID'] == project_id]
        if project_row.empty:
            self.project_has_slo_cache[project_id] = (False, [])
            return (False, [])
        
        participants = project_row.iloc[0]['participants']
        if not isinstance(participants, list):
            self.project_has_slo_cache[project_id] = (False, [])
            return (False, [])
        
        slovenian_partners = []
        for participant in participants:
            country = participant.get('address_country_abbreviation')
            legal_name = participant.get('legalName')
            if country == 'SI' and legal_name:
                slovenian_partners.append(legal_name)
        
        has_slovenian = len(slovenian_partners) > 0
        result = (has_slovenian, slovenian_partners)
        self.project_has_slo_cache[project_id] = result
        
        return result
    
    def _get_project_info(self, project_id: str, legal_name: str = None) -> Optional[ProjectInfo]:
        """Get complete project information."""
        if project_id in self.partner_projects_cache:
            return self.partner_projects_cache[project_id]
        
        project_row = self.all_projects_df[self.all_projects_df['project_ID'] == project_id]
        if project_row.empty:
            return None
        
        row = project_row.iloc[0]
        has_slovenian, slovenian_partners = self._project_has_slovenian_partners(project_id)
        
        project_info = ProjectInfo(
            project_id=project_id,
            title=row['title'],
            acronym=row['acronym'] if pd.notna(row['acronym']) else "N/A",
            website=self._get_project_website(project_id),
            start_date=row['start_date'],
            end_date=row['end_date'],
            total_budget=float(row['budget']) if pd.notna(row['budget']) else 0,
            has_slovenian_partners=has_slovenian,
            slovenian_partners=slovenian_partners
        )
        
        self.partner_projects_cache[project_id] = project_info
        return project_info
    
    def search_partners(self, search_term: str, search_by_country: bool = False) -> List[PartnerInfo]:
        """Search for partners by name or country."""
        if self.all_projects_df is None:
            st.error("No data available. Please load data first.")
            return []
        
        search_term = search_term.upper() if search_by_country else search_term.lower()
        all_partners = {}
        
        for idx, row in self.all_projects_df.iterrows():
            if not isinstance(row['participants'], list):
                continue
            
            for participant in row['participants']:
                legal_name = participant.get('legalName')
                country = participant.get('address_country_abbreviation')
                
                if not legal_name or not country:
                    continue
                
                if search_by_country:
                    if country.upper() == search_term:
                        if legal_name not in all_partners:
                            all_partners[legal_name] = {
                                'legal_name': legal_name,
                                'country': country,
                                'total_funding': 0.0,
                                'project_ids': set(),
                                'slo_project_ids': set()
                            }
                else:
                    if search_term in legal_name.lower():
                        if legal_name not in all_partners:
                            all_partners[legal_name] = {
                                'legal_name': legal_name,
                                'country': country,
                                'total_funding': 0.0,
                                'project_ids': set(),
                                'slo_project_ids': set()
                            }
                
                if legal_name in all_partners:
                    project_id = row['project_ID']
                    eu_contribution = participant.get('eucontribution', 0)
                    
                    try:
                        if isinstance(eu_contribution, str):
                            eu_contribution = float(eu_contribution.replace(',', ''))
                        elif not isinstance(eu_contribution, (int, float)):
                            eu_contribution = 0
                    except:
                        eu_contribution = 0
                    
                    all_partners[legal_name]['project_ids'].add(project_id)
                    all_partners[legal_name]['total_funding'] += eu_contribution
                    
                    has_slovenian, _ = self._project_has_slovenian_partners(project_id)
                    if has_slovenian:
                        all_partners[legal_name]['slo_project_ids'].add(project_id)
        
        matched_partners = []
        for partner_data in all_partners.values():
            total_projects = len(partner_data['project_ids'])
            slo_projects = len(partner_data['slo_project_ids'])
            collaboration_ratio = slo_projects / total_projects if total_projects > 0 else 0
            
            partner_info = PartnerInfo(
                legal_name=partner_data['legal_name'],
                country=partner_data['country'],
                total_eu_funding=partner_data['total_funding'],
                total_projects=total_projects,
                slovenian_projects=slo_projects,
                collaboration_ratio=collaboration_ratio
            )
            matched_partners.append(partner_info)
        
        matched_partners.sort(key=lambda x: x.total_eu_funding, reverse=True)
        return matched_partners
    
    def get_partner_details(self, legal_name: str) -> Optional[Dict]:
        """Get detailed information about a specific partner including ALL projects."""
        if self.all_projects_df is None:
            st.error("No data available.")
            return None
        
        partners = self.search_partners(legal_name)
        if not partners:
            return None
        
        partner_info = None
        for partner in partners:
            if partner.legal_name.lower() == legal_name.lower():
                partner_info = partner
                break
        
        if not partner_info:
            return None
        
        partner_projects = []
        slovenian_projects = []
        non_slovenian_projects = []
        
        for idx, row in self.all_projects_df.iterrows():
            if not isinstance(row['participants'], list):
                continue
            
            partner_in_project = False
            for participant in row['participants']:
                if participant.get('legalName') == partner_info.legal_name:
                    partner_in_project = True
                    break
            
            if not partner_in_project:
                continue
            
            project_id = row['project_ID']
            project_info = self._get_project_info(project_id, partner_info.legal_name)
            if not project_info:
                continue
            
            partner_projects.append(project_info)
            
            if project_info.has_slovenian_partners:
                slovenian_projects.append(project_info)
            else:
                non_slovenian_projects.append(project_info)
        
        details = {
            "partner_info": partner_info.to_dict(),
            "total_projects": len(partner_projects),
            "slovenian_collaborations": len(slovenian_projects),
            "non_slovenian_projects": len(non_slovenian_projects),
            "all_projects": [p.to_dict() for p in partner_projects],
            "slovenian_projects": [p.to_dict() for p in slovenian_projects],
            "non_slovenian_projects_list": [p.to_dict() for p in non_slovenian_projects]
        }
        
        return details
    
    def generate_collaboration_report(self, legal_name: str) -> str:
        """Generate a formatted text report showing ALL projects (both with and without Slovenian partners)."""
        details = self.get_partner_details(legal_name)
        if not details:
            return f"No data found for partner: {legal_name}"
        
        partner_info = details["partner_info"]
        all_projects = details["all_projects"]
        slovenian_projects = details["slovenian_projects"]
        non_slovenian_projects = details.get("non_slovenian_projects_list", [])
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append(f"COMPLETE PARTNER REPORT: {partner_info['Legal Name']}")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Partner information
        report_lines.append("PARTNER INFORMATION:")
        report_lines.append("-" * 40)
        for key, value in partner_info.items():
            report_lines.append(f"  {key}: {value}")
        report_lines.append("")
        
        # Collaboration summary
        report_lines.append("COLLABORATION SUMMARY:")
        report_lines.append("-" * 40)
        report_lines.append(f"  Total Projects: {details['total_projects']}")
        report_lines.append(f"  Projects with Slovenian Partners: {details['slovenian_collaborations']}")
        report_lines.append(f"  Projects without Slovenian Partners: {len(non_slovenian_projects)}")
        report_lines.append(f"  Collaboration Ratio: {partner_info['Collaboration Ratio']}")
        report_lines.append("")
        
        # ALL PROJECTS (complete list)
        if all_projects:
            report_lines.append(f"ALL PROJECTS ({len(all_projects)} TOTAL):")
            report_lines.append("=" * 80)
            
            # Separate into two sections for clarity
            if slovenian_projects:
                report_lines.append(f"\n✓ PROJECTS WITH SLOVENIAN PARTNERS ({len(slovenian_projects)}):")
                report_lines.append("-" * 60)
                
                for i, project in enumerate(slovenian_projects, 1):
                    report_lines.append(f"\n  {i}. {project['Title']}")
                    report_lines.append(f"     Acronym: {project['Acronym']}")
                    report_lines.append(f"     Project ID: {project['Project ID']}")
                    report_lines.append(f"     Website: {project['Website']}")
                    report_lines.append(f"     Duration: {project['Start Date']} to {project['End Date']}")
                    report_lines.append(f"     Budget: {project['Total Budget']}")
                    report_lines.append(f"     Slovenian Partners: {project['Slovenian Partners']}")
            
            if non_slovenian_projects:
                report_lines.append(f"\n✗ PROJECTS WITHOUT SLOVENIAN PARTNERS ({len(non_slovenian_projects)}):")
                report_lines.append("-" * 60)
                
                for i, project in enumerate(non_slovenian_projects, 1):
                    report_lines.append(f"\n  {i}. {project['Title']}")
                    report_lines.append(f"     Acronym: {project['Acronym']}")
                    report_lines.append(f"     Project ID: {project['Project ID']}")
                    report_lines.append(f"     Website: {project['Website']}")
                    report_lines.append(f"     Duration: {project['Start Date']} to {project['End Date']}")
                    report_lines.append(f"     Budget: {project['Total Budget']}")
        else:
            report_lines.append("NO PROJECTS FOUND FOR THIS PARTNER")
        
        report_lines.append("")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def export_collaboration_report_to_txt(self, legal_name: str, output_file: str = None) -> str:
        """Export the collaboration report to a .txt file."""
        report = self.generate_collaboration_report(legal_name)
        
        if "No data found" in report:
            return ""
        
        if output_file is None:
            os.makedirs(self.results_folder, exist_ok=True)
            safe_name = "".join(c for c in legal_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_name}_complete_report_{timestamp}.txt"
            output_file = os.path.join(self.results_folder, filename)
        else:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return output_file

# ---------------------------------------------------------------
# STREAMLIT APP
# ---------------------------------------------------------------
def main():
    """Main function to run the Streamlit app."""
    # Configure page
    st.set_page_config(
        page_title="EU Project Partner Search System",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
        .stButton > button {
            width: 100%;
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
        }
        .stButton > button:hover {
            background-color: #45a049;
        }
        .success-box {
            background-color: #d4edda;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            border-left: 4px solid #28a745;
        }
        .info-box {
            background-color: #d1ecf1;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            border-left: 4px solid #17a2b8;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'query_system' not in st.session_state:
        with st.spinner("Initializing system and loading data..."):
            st.session_state.query_system = ParticipantQuerySystem("results")
            st.session_state.report_saver = ReportSaver("results")
            st.session_state.search_results = None
            st.session_state.selected_partner = None
            st.session_state.generated_report = None
            st.session_state.current_search_term = ""
            st.session_state.current_search_type = ""
    
    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        
        # Output folder
        output_folder = st.text_input(
            "Output Folder",
            value="results",
            key="output_folder_input",
            help="Folder where reports will be saved"
        )
        
        if st.button("📁 Update Output Folder", key="update_output_folder"):
            st.session_state.query_system.results_folder = output_folder
            st.session_state.report_saver.set_output_folder(output_folder)
            st.success(f"Output folder updated to: {output_folder}")
        
        st.divider()
        
        # Session folder
        if st.button("📂 Create New Session Folder", key="create_session"):
            folder = st.session_state.report_saver.create_session_folder()
            st.success(f"Session folder created: {folder}")
        
        st.divider()
        
        # Statistics
        st.markdown("## 📊 Database Statistics")
        if st.session_state.query_system.all_projects_df is not None:
            total_projects = len(st.session_state.query_system.all_projects_df)
            st.metric("Total Projects", total_projects)
            
            # Count SI projects
            si_count = 0
            for _, row in st.session_state.query_system.all_projects_df.iterrows():
                has_si, _ = st.session_state.query_system._project_has_slovenian_partners(row['project_ID'])
                if has_si:
                    si_count += 1
            st.metric("Projects with Slovenian Partners", si_count)
            st.metric("Percentage with SI", f"{(si_count/total_projects)*100:.1f}%" if total_projects > 0 else "0%")
        else:
            st.warning("No data loaded yet")
    
    # Main content
    st.title("🔍 EU Project Partner Search System")
    st.markdown("Search for research partners and view ALL their projects (both with and without Slovenian collaborations)")
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔎 Search Partners", "📄 Complete Reports", "📊 Statistics", "💾 Saved Outputs"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Search by Partner Name")
            partner_name = st.text_input("Enter partner name:", key="name_search_input")
            
            if st.button("🔍 Search by Name", key="search_by_name_btn"):
                if partner_name:
                    with st.spinner("Searching..."):
                        results = st.session_state.query_system.search_partners(partner_name)
                        st.session_state.search_results = results
                        st.session_state.current_search_term = partner_name
                        st.session_state.current_search_type = "name"
                        
                        if results:
                            st.success(f"Found {len(results)} partners")
                        else:
                            st.warning("No partners found")
        
        with col2:
            st.subheader("Search by Country")
            country_code = st.text_input("Enter country code (e.g., DE, FR, IT):", key="country_search_input", max_chars=2)
            
            if st.button("🔍 Search by Country", key="search_by_country_btn"):
                if country_code and len(country_code) == 2:
                    with st.spinner("Searching..."):
                        results = st.session_state.query_system.search_partners(country_code.upper(), search_by_country=True)
                        st.session_state.search_results = results
                        st.session_state.current_search_term = country_code.upper()
                        st.session_state.current_search_type = "country"
                        
                        if results:
                            st.success(f"Found {len(results)} partners from {country_code.upper()}")
                        else:
                            st.warning(f"No partners found from {country_code.upper()}")
                else:
                    st.error("Please enter a valid 2-letter country code")
        
        # Display search results
        if st.session_state.search_results:
            st.subheader(f"📋 Search Results ({len(st.session_state.search_results)} partners)")
            
            # Convert to DataFrame
            results_data = []
            for i, partner in enumerate(st.session_state.search_results[:100], 1):
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
            
            # Save search results
            if st.button("💾 Save Search Results", key="save_search_results_btn"):
                filepath = st.session_state.report_saver.save_search_results(
                    st.session_state.search_results, 
                    st.session_state.current_search_term,
                    st.session_state.current_search_type
                )
                st.success(f"Search results saved to: {filepath}")
            
            # Select partner for detailed view
            st.subheader("Select Partner for Complete Analysis")
            st.info("View ALL projects for this partner (both with and without Slovenian partners)")
            partner_names = [p.legal_name for p in st.session_state.search_results[:100]]
            selected_name = st.selectbox("Choose a partner:", partner_names, key="partner_select")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📄 View Complete Details", key="view_details_btn"):
                    with st.spinner("Loading all projects for this partner..."):
                        details = st.session_state.query_system.get_partner_details(selected_name)
                        if details:
                            st.session_state.selected_partner = details
                            st.success(f"Loaded {details['total_projects']} projects for {selected_name}")
                        else:
                            st.error("Could not load partner details")
            
            with col2:
                if st.button("📝 Generate Complete Report", key="generate_report_btn_tab1"):
                    with st.spinner("Generating complete report..."):
                        report = st.session_state.query_system.generate_collaboration_report(selected_name)
                        st.session_state.generated_report = report
                        st.success("Complete report generated!")
            
            with col3:
                if st.button("💾 Save Report to File", key="save_report_btn_tab1"):
                    with st.spinner("Saving..."):
                        filepath = st.session_state.query_system.export_collaboration_report_to_txt(selected_name)
                        if filepath:
                            st.success(f"Report saved to: {filepath}")
                            
                            # Also save detailed info
                            details = st.session_state.query_system.get_partner_details(selected_name)
                            if details:
                                st.session_state.report_saver.save_collaboration_details(details, selected_name)
            
            # Display generated report
            if st.session_state.generated_report:
                with st.expander("📄 Complete Report", expanded=True):
                    st.text_area("Report Content", st.session_state.generated_report, height=500, key="report_content_tab1")
                    
                    # Download button
                    st.download_button(
                        label="📥 Download Complete Report as TXT",
                        data=st.session_state.generated_report,
                        file_name=f"{selected_name}_complete_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        key="download_report_btn_tab1"
                    )
            
            # Display partner details with ALL projects
            if st.session_state.selected_partner:
                with st.expander("📊 Complete Partner Details", expanded=True):
                    details = st.session_state.selected_partner
                    partner_info = details["partner_info"]
                    
                    # Summary metrics
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        st.metric("Country", partner_info["Country"])
                    with col2:
                        st.metric("Total Projects", partner_info["Total Projects"])
                    with col3:
                        st.metric("With Slovenian Partners", partner_info["Slovenian Projects"])
                    with col4:
                        st.metric("Without Slovenian Partners", details["non_slovenian_projects"])
                    with col5:
                        st.metric("Collaboration Ratio", partner_info["Collaboration Ratio"])
                    
                    # ALL PROJECTS section
                    st.subheader(f"📋 ALL PROJECTS ({details['total_projects']} Total)")
                    
                    # Projects with Slovenian partners
                    if details["slovenian_projects"]:
                        st.markdown("### ✅ Projects WITH Slovenian Partners")
                        projects_data_si = []
                        for project in details["slovenian_projects"]:
                            projects_data_si.append({
                                "Title": project["Title"],
                                "Acronym": project["Acronym"],
                                "Project ID": project["Project ID"],
                                "Budget": project["Total Budget"],
                                "Slovenian Partners": project["Slovenian Partners"][:50] + "..." if len(project["Slovenian Partners"]) > 50 else project["Slovenian Partners"]
                            })
                        st.dataframe(pd.DataFrame(projects_data_si), use_container_width=True)
                    
                    # Projects without Slovenian partners
                    if details.get("non_slovenian_projects_list"):
                        st.markdown("### ❌ Projects WITHOUT Slovenian Partners")
                        projects_data_non_si = []
                        for project in details["non_slovenian_projects_list"]:
                            projects_data_non_si.append({
                                "Title": project["Title"],
                                "Acronym": project["Acronym"],
                                "Project ID": project["Project ID"],
                                "Budget": project["Total Budget"],
                                "Has Slovenian Partners": "No"
                            })
                        st.dataframe(pd.DataFrame(projects_data_non_si), use_container_width=True)
                    
                    if not details["slovenian_projects"] and not details.get("non_slovenian_projects_list"):
                        st.info("No projects found for this partner")
    
    with tab2:
        st.subheader("📄 Generate Complete Partner Report")
        st.markdown("Generate a report showing ALL projects for a partner (both with and without Slovenian collaborations)")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            partner_name = st.text_input("Enter exact legal name:", key="report_name_input")
        
        with col2:
            st.write("")
            st.write("")
            generate_btn = st.button("🚀 Generate Complete Report", key="generate_report_btn_tab2")
        
        if generate_btn and partner_name:
            with st.spinner("Generating complete report..."):
                report = st.session_state.query_system.generate_collaboration_report(partner_name)
                
                if "No data found" in report:
                    st.error(report)
                else:
                    st.success("Complete report generated successfully!")
                    
                    # Display report
                    st.text_area("Complete Report", report, height=600, key="report_content_tab2")
                    
                    # Save options
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("💾 Save to File", key="save_report_btn_tab2"):
                            filepath = st.session_state.query_system.export_collaboration_report_to_txt(partner_name)
                            if filepath:
                                st.success(f"Saved to: {filepath}")
                    
                    with col2:
                        st.download_button(
                            label="📥 Download Complete Report",
                            data=report,
                            file_name=f"{partner_name}_complete_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain",
                            key="download_report_btn_tab2"
                        )
                    
                    with col3:
                        if st.button("💾 Save Details", key="save_details_btn_tab2"):
                            details = st.session_state.query_system.get_partner_details(partner_name)
                            if details:
                                filepath = st.session_state.report_saver.save_collaboration_details(details, partner_name)
                                st.success(f"Details saved to: {filepath}")
    
    with tab3:
        st.subheader("📊 System Statistics")
        
        if st.button("🔄 Refresh Statistics", key="refresh_stats_btn"):
            st.rerun()
        
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
        else:
            st.info("No data loaded. Please wait for data to load or check your connection.")
        
        # Export statistics
        if st.button("📊 Export Statistics Report", key="export_stats_btn"):
            stats_report = []
            stats_report.append("=" * 80)
            stats_report.append("SYSTEM STATISTICS REPORT")
            stats_report.append("=" * 80)
            stats_report.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            stats_report.append("")
            
            if st.session_state.query_system.all_projects_df is not None:
                total_projects_local = len(st.session_state.query_system.all_projects_df)
                stats_report.append(f"Total Projects: {total_projects_local}")
                stats_report.append(f"Projects with Slovenian Partners: {si_count}")
                stats_report.append(f"Percentage: {(si_count/total_projects_local)*100:.1f}%")
            
            stats_text = "\n".join(stats_report)
            
            st.download_button(
                label="📥 Download Statistics Report",
                data=stats_text,
                file_name=f"statistics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                key="download_stats_btn"
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
                        filepath = os.path.join(root, filename)
                        rel_path = os.path.relpath(root, output_folder)
                        if rel_path == '.':
                            rel_path = 'root'
                        
                        files.append({
                            "File": filename,
                            "Folder": rel_path,
                            "Size": f"{os.path.getsize(filepath) / 1024:.1f} KB",
                            "Modified": datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
                        })
            
            if files:
                df_files = pd.DataFrame(files)
                st.dataframe(df_files, use_container_width=True)
                
                # Open folder button
                if st.button("📂 Open Output Folder", key="open_folder_btn"):
                    import subprocess
                    import platform
                    
                    try:
                        if platform.system() == "Windows":
                            os.startfile(output_folder)
                        elif platform.system() == "Darwin":
                            subprocess.run(["open", output_folder])
                        else:
                            subprocess.run(["xdg-open", output_folder])
                        st.success("Output folder opened in file explorer")
                    except Exception as e:
                        st.error(f"Could not open folder: {e}")
            else:
                st.info("No files saved yet. Generate some reports to see them here.")
        else:
            st.info("Output folder doesn't exist yet. It will be created when you save your first report.")
    
    # Footer
    st.divider()
    st.markdown(f"""
    <div style="text-align: center; color: gray;">
        <p>EU Project Partner Search System | Shows ALL projects (both with and without Slovenian collaborations)</p>
        <p>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    """, unsafe_allow_html=True)


# Run the app
if __name__ == "__main__":
    main()
