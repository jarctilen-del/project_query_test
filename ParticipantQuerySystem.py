import os
import pandas as pd
import json
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime
from sedia_api_fetchers.EUFT_retrieve_projects import SEDIA_GET_PROJECTS

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
    """Utility class for saving terminal output to files."""
    
    def __init__(self, output_folder: str = None):
        """Initialize the report saver with an output folder."""
        self.output_folder = output_folder
        self.current_session_folder = None
    
    def set_output_folder(self, folder_path: str):
        """Set the output folder for saving reports."""
        self.output_folder = folder_path
        os.makedirs(self.output_folder, exist_ok=True)
        print(f"Output folder set to: {self.output_folder}")
    
    def create_session_folder(self) -> str:
        """Create a timestamped folder for the current session."""
        if not self.output_folder:
            self.output_folder = os.getcwd()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_folder = os.path.join(self.output_folder, f"session_{timestamp}")
        os.makedirs(session_folder, exist_ok=True)
        self.current_session_folder = session_folder
        print(f"\n✓ Session folder created: {session_folder}")
        return session_folder
    
    def save_report(self, content: str, filename: str, subfolder: str = None) -> str:
        """
        Save report content to a file.
        
        Args:
            content: Report content to save
            filename: Name of the file
            subfolder: Optional subfolder within the session folder
        
        Returns:
            Path to the saved file
        """
        # Determine save location
        if self.current_session_folder:
            save_dir = self.current_session_folder
            if subfolder:
                save_dir = os.path.join(save_dir, subfolder)
        elif self.output_folder:
            save_dir = self.output_folder
        else:
            save_dir = os.getcwd()
        
        # Create directory if it doesn't exist
        os.makedirs(save_dir, exist_ok=True)
        
        # Ensure filename has .txt extension
        if not filename.endswith('.txt'):
            filename += '.txt'
        
        filepath = os.path.join(save_dir, filename)
        
        # Save the file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath
    
    def save_search_results(self, partners: List[PartnerInfo], search_term: str, search_type: str = 'name') -> str:
        """
        Save search results to a file.
        
        Args:
            partners: List of PartnerInfo objects
            search_term: The search term used
            search_type: Either 'name' or 'country'
        
        Returns:
            Path to the saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        search_type_label = "country" if search_type == 'country' else "name"
        filename = f"search_{search_type_label}_{search_term}_{timestamp}.txt"
        
        # Build report content
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
        """
        Save collaboration details to a file.
        
        Args:
            details: Dictionary with partner details and projects
            legal_name: Name of the partner
        
        Returns:
            Path to the saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in legal_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_name}_collaboration_details_{timestamp}.txt"
        
        partner_info = details["partner_info"]
        collaborations = details["slovenian_projects"]
        
        # Build report content
        lines = []
        lines.append("=" * 80)
        lines.append(f"COLLABORATION DETAILS: {partner_info['Legal Name']}")
        lines.append("=" * 80)
        lines.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Partner information
        lines.append("PARTNER INFORMATION:")
        lines.append("-" * 40)
        for key, value in partner_info.items():
            lines.append(f"  {key}: {value}")
        lines.append("")
        
        # Collaboration summary
        lines.append("COLLABORATION SUMMARY:")
        lines.append("-" * 40)
        lines.append(f"  Total Projects: {details['total_projects']}")
        lines.append(f"  Slovenian Collaborations: {details['slovenian_collaborations']}")
        lines.append(f"  Collaboration Ratio: {partner_info['Collaboration Ratio']}")
        lines.append("")
        
        # List of collaborations
        if collaborations:
            lines.append(f"PROJECTS WITH SLOVENIAN PARTNERS ({len(collaborations)}):")
            lines.append("-" * 80)
            
            for i, project in enumerate(collaborations, 1):
                lines.append(f"\n{i}. {project['Title']}")
                lines.append(f"   Acronym: {project['Acronym']}")
                lines.append(f"   Project ID: {project['Project ID']}")
                lines.append(f"   Website: {project['Website']}")
                lines.append(f"   Duration: {project['Start Date']} to {project['End Date']}")
                lines.append(f"   Budget: {project['Total Budget']}")
                lines.append(f"   Slovenian Partners: {project['Slovenian Partners']}")
        else:
            lines.append("NO PROJECTS WITH SLOVENIAN PARTNERS FOUND")
        
        lines.append("")
        lines.append("=" * 80)
        
        content = "\n".join(lines)
        return self.save_report(content, filename, "collaboration_details")
    
    def save_terminal_output(self, output_lines: List[str], description: str) -> str:
        """
        Save terminal output to a file.
        
        Args:
            output_lines: List of strings that were printed to terminal
            description: Description of what was saved
        
        Returns:
            Path to the saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_desc = "".join(c for c in description if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"terminal_output_{safe_desc}_{timestamp}.txt"
        
        # Build content
        lines = []
        lines.append("=" * 80)
        lines.append(f"TERMINAL OUTPUT SAVE: {description}")
        lines.append("=" * 80)
        lines.append(f"Saved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.extend(output_lines)
        lines.append("")
        lines.append("=" * 80)
        
        content = "\n".join(lines)
        return self.save_report(content, filename, "terminal_outputs")


# ---------------------------------------------------------------
# PARTICIPANT QUERY SYSTEM
# ---------------------------------------------------------------
class ParticipantQuerySystem:
    """
    System for querying project participants and their collaborations with Slovenian partners.
    """
    
    def __init__(self, results_folder: str = r"C:\Users\User\Documents\python\rs\results"):
        """Initialize the query system."""
        self.results_folder = results_folder
        self.main_file = os.path.join(results_folder, "edf_comprehensive_analysis.xlsx")
        
        # Initialize report saver
        self.report_saver = ReportSaver(results_folder)
        
        # Initialize data structures
        self.all_projects_df = None
        self.filtered_projects_df = None
        self.foreign_partners_df = None
        self.partner_projects_cache = {}
        self.project_has_slo_cache = {}
        
        # Track terminal output for saving
        self.terminal_output_buffer = []
        
        # Load data if file exists
        self._load_data()
    
    def _print_and_buffer(self, *args, **kwargs):
        """Print to terminal and buffer the output for potential saving."""
        # Convert arguments to string
        output = " ".join(str(arg) for arg in args)
        
        # Print to terminal
        print(output, **kwargs)
        
        # Add to buffer
        self.terminal_output_buffer.append(output)
    
    def clear_buffer(self):
        """Clear the terminal output buffer."""
        self.terminal_output_buffer = []
    
    def save_current_session_output(self, description: str = "session_output") -> str:
        """
        Save all terminal output from the current session.
        
        Args:
            description: Description for the saved file
        
        Returns:
            Path to the saved file
        """
        if not self.terminal_output_buffer:
            self._print_and_buffer("No terminal output to save.")
            return ""
        
        return self.report_saver.save_terminal_output(self.terminal_output_buffer, description)
    
    def _load_data(self) -> None:
        """Load data from Excel file or fetch from API if not available."""
        if os.path.exists(self.main_file):
            self._print_and_buffer(f"Loading data from: {self.main_file}")
            try:
                # Load all projects data
                self.all_projects_df = pd.read_excel(self.main_file, sheet_name='All_Projects')
                
                # Try to load Slovenian projects data
                try:
                    self.filtered_projects_df = pd.read_excel(
                        self.main_file, 
                        sheet_name='Projects_from_SI'
                    )
                except Exception as e:
                    self._print_and_buffer(f"No Slovenian projects data found in Excel: {e}")
                
                # Try to load foreign partners data
                try:
                    self.foreign_partners_df = pd.read_excel(
                        self.main_file,
                        sheet_name='Foreign_Partners_SI'
                    )
                except:
                    self._print_and_buffer("No foreign partners analysis found - will calculate if needed")
                
                self._print_and_buffer("Data loaded successfully!")
                
            except Exception as e:
                self._print_and_buffer(f"Error loading data: {e}")
                self._print_and_buffer("Will fetch fresh data from API...")
                self._fetch_fresh_data()
        else:
            self._print_and_buffer(f"Data file not found: {self.main_file}")
            self._print_and_buffer("Fetching fresh data from API...")
            self._fetch_fresh_data()
    
    def _fetch_fresh_data(self) -> None:
        """Fetch fresh data from the API."""
        self._print_and_buffer("Fetching project data from API...")
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
        
        # Filter by date (projects ending after 2025-12-01)
        self.filtered_projects_df = self.filtered_projects_df[
            self.filtered_projects_df["end_date"] > "2025-12-01T00:00:00.000+0100"
        ]
        
        self._print_and_buffer(f"Total projects loaded: {len(self.all_projects_df)}")
        self._print_and_buffer(f"Projects with Slovenian partners: {len(self.filtered_projects_df)}")
    
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
        
        # Try to find website in project data
        project_row = self.all_projects_df[self.all_projects_df['project_ID'] == project_id]
        if not project_row.empty:
            participants = project_row.iloc[0]['participants']
            if isinstance(participants, list):
                websites = self._extract_project_links(participants)
                if websites:
                    return websites[0]
        
        # Default website template
        return f"https://cordis.europa.eu/project/id/{project_id}"
    
    def _project_has_slovenian_partners(self, project_id: str) -> Tuple[bool, List[str]]:
        """
        Check if a project has Slovenian partners and return list of Slovenian partner names.
        
        Returns:
            Tuple of (has_slovenian_partners: bool, slovenian_partners: List[str])
        """
        # Check cache first
        if project_id in self.project_has_slo_cache:
            return self.project_has_slo_cache[project_id]
        
        # Find the project
        project_row = self.all_projects_df[self.all_projects_df['project_ID'] == project_id]
        if project_row.empty:
            self.project_has_slo_cache[project_id] = (False, [])
            return (False, [])
        
        participants = project_row.iloc[0]['participants']
        if not isinstance(participants, list):
            self.project_has_slo_cache[project_id] = (False, [])
            return (False, [])
        
        # Check for Slovenian partners
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
        # Check cache first
        if project_id in self.partner_projects_cache:
            return self.partner_projects_cache[project_id]
        
        # Find the project
        project_row = self.all_projects_df[self.all_projects_df['project_ID'] == project_id]
        if project_row.empty:
            return None
        
        row = project_row.iloc[0]
        
        # Check if project has Slovenian partners
        has_slovenian, slovenian_partners = self._project_has_slovenian_partners(project_id)
        
        # Create project info
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
        
        # Cache the result
        self.partner_projects_cache[project_id] = project_info
        
        return project_info
    
    def search_partners(self, search_term: str, search_by_country: bool = False) -> List[PartnerInfo]:
        """
        Search for partners by name or country.
        
        Args:
            search_term: Text to search for in partner names or countries
            search_by_country: If True, search by country code instead of name
        
        Returns:
            List of matching PartnerInfo objects
        """
        if self.all_projects_df is None:
            self._print_and_buffer("No data available. Please load data first.")
            return []
        
        search_term = search_term.upper() if search_by_country else search_term.lower()
        matched_partners = []
        
        # Collect all unique partners
        all_partners = {}
        
        for idx, row in self.all_projects_df.iterrows():
            if not isinstance(row['participants'], list):
                continue
            
            for participant in row['participants']:
                legal_name = participant.get('legalName')
                country = participant.get('address_country_abbreviation')
                
                if not legal_name or not country:
                    continue
                
                # Check if partner matches search criteria
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
                
                # Add project information for matched partners
                if legal_name in all_partners:
                    project_id = row['project_ID']
                    eu_contribution = participant.get('eucontribution', 0)
                    
                    # Convert to numeric if possible
                    try:
                        if isinstance(eu_contribution, str):
                            eu_contribution = float(eu_contribution.replace(',', ''))
                        elif not isinstance(eu_contribution, (int, float)):
                            eu_contribution = 0
                    except:
                        eu_contribution = 0
                    
                    all_partners[legal_name]['project_ids'].add(project_id)
                    all_partners[legal_name]['total_funding'] += eu_contribution
                    
                    # Check if this project has Slovenian partners
                    has_slovenian, _ = self._project_has_slovenian_partners(project_id)
                    if has_slovenian:
                        all_partners[legal_name]['slo_project_ids'].add(project_id)
        
        # Convert to PartnerInfo objects
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
        
        # Sort by total funding (descending)
        matched_partners.sort(key=lambda x: x.total_eu_funding, reverse=True)
        
        return matched_partners
    
    def get_partner_details(self, legal_name: str) -> Optional[Dict]:
        """
        Get detailed information about a specific partner.
        
        Args:
            legal_name: Exact legal name of the partner/organization
        
        Returns:
            Dictionary with partner details and project information
        """
        if self.all_projects_df is None:
            self._print_and_buffer("No data available. Please load data first.")
            return None
        
        # Get partner information
        partners = self.search_partners(legal_name)
        if not partners:
            self._print_and_buffer(f"No partner found with name: {legal_name}")
            return None
        
        # Find exact match
        partner_info = None
        for partner in partners:
            if partner.legal_name.lower() == legal_name.lower():
                partner_info = partner
                break
        
        if not partner_info:
            self._print_and_buffer(f"No exact match found for: {legal_name}")
            return None
        
        # Get all projects for this partner
        partner_projects = []
        slovenian_projects = []
        
        for idx, row in self.all_projects_df.iterrows():
            if not isinstance(row['participants'], list):
                continue
            
            # Check if this partner is in the project
            partner_in_project = False
            for participant in row['participants']:
                if participant.get('legalName') == partner_info.legal_name:
                    partner_in_project = True
                    break
            
            if not partner_in_project:
                continue
            
            project_id = row['project_ID']
            
            # Get project info
            project_info = self._get_project_info(project_id, partner_info.legal_name)
            if not project_info:
                continue
            
            # Add to appropriate list
            partner_projects.append(project_info)
            
            # Check if this is a Slovenian project
            if project_info.has_slovenian_partners:
                slovenian_projects.append(project_info)
        
        # Prepare detailed information
        details = {
            "partner_info": partner_info.to_dict(),
            "total_projects": len(partner_projects),
            "slovenian_collaborations": len(slovenian_projects),
            "all_projects": [p.to_dict() for p in partner_projects],
            "slovenian_projects": [p.to_dict() for p in slovenian_projects]
        }
        
        return details
    
    def get_slovenian_collaborations(self, legal_name: str) -> List[Dict]:
        """
        Get list of projects where the partner collaborates with Slovenian partners.
        
        Args:
            legal_name: Exact legal name of the partner/organization
        
        Returns:
            List of project dictionaries with name, acronym, and website
        """
        details = self.get_partner_details(legal_name)
        if not details:
            return []
        
        return details["slovenian_projects"]
    
    def export_collaborations_to_csv(self, legal_name: str, output_folder: str = None) -> str:
        """
        Export Slovenian collaborations to a CSV file.
        
        Args:
            legal_name: Exact legal name of the partner/organization
            output_folder: Folder to save the CSV (default: results folder)
        
        Returns:
            Path to the created CSV file
        """
        if output_folder is None:
            output_folder = self.results_folder
        
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Get collaborations
        collaborations = self.get_slovenian_collaborations(legal_name)
        if not collaborations:
            self._print_and_buffer(f"No Slovenian collaborations found for: {legal_name}")
            return ""
        
        # Create filename (sanitize legal name)
        safe_name = "".join(c for c in legal_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_name}_slovenian_collaborations.csv"
        filepath = os.path.join(output_folder, filename)
        
        # Create DataFrame and save to CSV
        df = pd.DataFrame(collaborations)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        self._print_and_buffer(f"Exported {len(collaborations)} collaborations to: {filepath}")
        return filepath
    
    def generate_collaboration_report(self, legal_name: str) -> str:
        """
        Generate a formatted text report of Slovenian collaborations.
        
        Args:
            legal_name: Exact legal name of the partner/organization
        
        Returns:
            Formatted report string
        """
        details = self.get_partner_details(legal_name)
        if not details:
            return f"No data found for partner: {legal_name}"
        
        partner_info = details["partner_info"]
        collaborations = details["slovenian_projects"]
        
        # Build report
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append(f"COLLABORATION REPORT: {partner_info['Legal Name']}")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # Partner information
        report_lines.append("PARTNER INFORMATION:")
        report_lines.append("-" * 40)
        for key, value in partner_info.items():
            report_lines.append(f"  {key}: {value}")
        report_lines.append("")
        
        # Collaboration summary
        report_lines.append(f"COLLABORATION WITH SLOVENIAN PARTNERS:")
        report_lines.append("-" * 40)
        report_lines.append(f"  Total Projects: {details['total_projects']}")
        report_lines.append(f"  Slovenian Collaborations: {details['slovenian_collaborations']}")
        report_lines.append(f"  Collaboration Ratio: {partner_info['Collaboration Ratio']}")
        report_lines.append("")
        
        # List of collaborations
        if collaborations:
            report_lines.append(f"PROJECTS WITH SLOVENIAN PARTNERS ({len(collaborations)}):")
            report_lines.append("-" * 40)
            
            for i, project in enumerate(collaborations, 1):
                report_lines.append(f"\n{i}. {project['Title']}")
                report_lines.append(f"   Acronym: {project['Acronym']}")
                report_lines.append(f"   Project ID: {project['Project ID']}")
                report_lines.append(f"   Website: {project['Website']}")
                report_lines.append(f"   Duration: {project['Start Date']} to {project['End Date']}")
                report_lines.append(f"   Budget: {project['Total Budget']}")
                report_lines.append(f"   Slovenian Partners in Project: {project['Slovenian Partners']}")
        else:
            report_lines.append("NO PROJECTS WITH SLOVENIAN PARTNERS FOUND")
        
        report_lines.append("")
        report_lines.append("=" * 80)
        report_lines.append(f"Report generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return "\n".join(report_lines)
    
    def export_collaboration_report_to_txt(self, legal_name: str, output_file: str = None) -> str:
        """
        Export the collaboration report to a .txt file.
        
        Args:
            legal_name: Exact legal name of the partner/organization
            output_file: Full path to output file (if None, auto-generates filename)
        
        Returns:
            Path to the created .txt file
        """
        # Generate the report
        report = self.generate_collaboration_report(legal_name)
        
        if "No data found" in report:
            self._print_and_buffer(report)
            return ""
        
        # Determine output file path
        if output_file is None:
            # Create output folder if it doesn't exist
            os.makedirs(self.results_folder, exist_ok=True)
            
            # Sanitize legal name for filename
            safe_name = "".join(c for c in legal_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_name}_collaboration_report_{timestamp}.txt"
            output_file = os.path.join(self.results_folder, filename)
        else:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Write report to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self._print_and_buffer(f"\n✓ Report successfully exported to: {output_file}")
        return output_file
    
    def debug_partner_projects(self, legal_name: str):
        """
        Debug function to see all projects for a partner and why they are/aren't counted as Slovenian.
        """
        if self.all_projects_df is None:
            self._print_and_buffer("No data available.")
            return
        
        self._print_and_buffer(f"\nDEBUG INFO FOR: {legal_name}")
        self._print_and_buffer("=" * 80)
        
        all_projects = []
        slo_projects = []
        
        for idx, row in self.all_projects_df.iterrows():
            if not isinstance(row['participants'], list):
                continue
            
            # Check if this partner is in the project
            partner_found = False
            partner_country = None
            for participant in row['participants']:
                if participant.get('legalName') == legal_name:
                    partner_found = True
                    partner_country = participant.get('address_country_abbreviation')
                    break
            
            if not partner_found:
                continue
            
            project_id = row['project_ID']
            project_title = row['title']
            
            # Check if project has Slovenian partners
            has_slovenian, slovenian_partners = self._project_has_slovenian_partners(project_id)
            
            project_info = {
                'project_id': project_id,
                'title': project_title,
                'has_slovenian': has_slovenian,
                'slovenian_partners': slovenian_partners,
                'partner_country': partner_country
            }
            
            all_projects.append(project_info)
            if has_slovenian:
                slo_projects.append(project_info)
        
        self._print_and_buffer(f"\nTotal projects found for {legal_name}: {len(all_projects)}")
        self._print_and_buffer(f"Projects with Slovenian partners: {len(slo_projects)}")
        
        self._print_and_buffer("\nDETAILED PROJECT LIST:")
        self._print_and_buffer("-" * 80)
        
        for i, project in enumerate(all_projects, 1):
            status = "✓ SI" if project['has_slovenian'] else "✗ No SI"
            self._print_and_buffer(f"\n{i}. {project['title']} [{project['project_id']}]")
            self._print_and_buffer(f"   Status: {status}")
            self._print_and_buffer(f"   Partner Country: {project['partner_country']}")
            if project['has_slovenian']:
                self._print_and_buffer(f"   Slovenian Partners: {', '.join(project['slovenian_partners'])}")
    
    def interactive_query(self):
        """Run an interactive query session."""
        self._print_and_buffer("\n" + "="*80)
        self._print_and_buffer("PARTICIPANT QUERY SYSTEM")
        self._print_and_buffer("="*80)
        self._print_and_buffer("Query project participants and their collaborations with Slovenian partners")
        self._print_and_buffer("")
        
        while True:
            self._print_and_buffer("\n" + "-"*40)
            self._print_and_buffer("MAIN MENU")
            self._print_and_buffer("-"*40)
            self._print_and_buffer("1. Search partners by name")
            self._print_and_buffer("2. Search partners by country")
            self._print_and_buffer("3. Get partner details and Slovenian collaborations")
            self._print_and_buffer("4. Export collaborations to CSV")
            self._print_and_buffer("5. Generate collaboration report")
            self._print_and_buffer("6. Export collaboration report to TXT")
            self._print_and_buffer("7. View partner statistics")
            self._print_and_buffer("8. Debug partner projects")
            self._print_and_buffer("9. Save all terminal output to file")
            self._print_and_buffer("10. Change output folder")
            self._print_and_buffer("11. Exit")
            self._print_and_buffer("")
            
            choice = input("Enter your choice (1-11): ").strip()
            
            if choice == "1":
                self._search_by_name()
            elif choice == "2":
                self._search_by_country()
            elif choice == "3":
                self._get_collaborations()
            elif choice == "4":
                self._export_to_csv()
            elif choice == "5":
                self._generate_report()
            elif choice == "6":
                self._export_report_to_txt()
            elif choice == "7":
                self._view_statistics()
            elif choice == "8":
                self._debug_partner()
            elif choice == "9":
                self._save_terminal_output()
            elif choice == "10":
                self._change_output_folder()
            elif choice == "11":
                self._print_and_buffer("\nThank you for using the Participant Query System!")
                break
            else:
                self._print_and_buffer("Invalid choice. Please try again.")
    
    def _save_terminal_output(self):
        """Save all terminal output from the current session."""
        description = input("\nEnter a description for this saved output (optional): ").strip()
        if not description:
            description = "session_output"
        
        filepath = self.save_current_session_output(description)
        if filepath:
            self._print_and_buffer(f"\n✓ Terminal output saved to: {filepath}")
    
    def _change_output_folder(self):
        """Change the output folder for saving reports."""
        new_folder = input("\nEnter new output folder path: ").strip()
        if new_folder:
            self.report_saver.set_output_folder(new_folder)
            self.results_folder = new_folder
            self._print_and_buffer(f"Output folder changed to: {new_folder}")
        else:
            self._print_and_buffer("No folder specified. Keeping current folder.")
    
    def _search_by_name(self):
        """Search partners by name."""
        search_term = input("\nEnter partner name to search for: ").strip()
        if not search_term:
            self._print_and_buffer("No search term entered.")
            return
        
        self._print_and_buffer(f"\nSearching for partners with '{search_term}' in name...")
        partners = self.search_partners(search_term)
        
        if not partners:
            self._print_and_buffer("No partners found.")
            return
        
        self._print_and_buffer(f"\nFound {len(partners)} partners:")
        self._print_and_buffer("-" * 120)
        self._print_and_buffer(f"{'No.':<4} {'Legal Name':<40} {'Country':<8} {'Total Funding':<15} {'Projects':<10} {'SI Collab.':<10} {'Ratio':<10}")
        self._print_and_buffer("-" * 120)
        
        for i, partner in enumerate(partners[:20], 1):
            self._print_and_buffer(f"{i:<4} {partner.legal_name[:38]:<40} {partner.country:<8} "
                      f"€{partner.total_eu_funding:,.0f} {'':<3} {partner.total_projects:<10} "
                      f"{partner.slovenian_projects:<10} {partner.collaboration_ratio:.1%}")
        
        if len(partners) > 20:
            self._print_and_buffer(f"... and {len(partners) - 20} more partners")
        
        # Ask to save search results
        save_choice = input("\nSave these search results to file? (y/n): ").strip().lower()
        if save_choice == 'y':
            filepath = self.report_saver.save_search_results(partners, search_term, 'name')
            self._print_and_buffer(f"\n✓ Search results saved to: {filepath}")
        
        # Ask to export report for any partner
        export_choice = input("\nWould you like to export a collaboration report for any of these partners? (y/n): ").strip().lower()
        if export_choice == 'y':
            partner_num = input("Enter the partner number (or exact name): ").strip()
            try:
                # Try to interpret as number
                idx = int(partner_num) - 1
                if 0 <= idx < len(partners):
                    selected_partner = partners[idx]
                    self._print_and_buffer(f"\nExporting report for: {selected_partner.legal_name}")
                    self.export_collaboration_report_to_txt(selected_partner.legal_name)
                    
                    # Also save details
                    details = self.get_partner_details(selected_partner.legal_name)
                    if details:
                        self.report_saver.save_collaboration_details(details, selected_partner.legal_name)
                else:
                    self._print_and_buffer("Invalid partner number.")
            except ValueError:
                # Treat as name
                self.export_collaboration_report_to_txt(partner_num)
                details = self.get_partner_details(partner_num)
                if details:
                    self.report_saver.save_collaboration_details(details, partner_num)
    
    def _search_by_country(self):
        """Search partners by country."""
        country_code = input("\nEnter 2-letter country code (e.g., DE, FR, IT): ").strip().upper()
        if len(country_code) != 2:
            self._print_and_buffer("Please enter a valid 2-letter country code.")
            return
        
        self._print_and_buffer(f"\nSearching for partners from country: {country_code}...")
        partners = self.search_partners(country_code, search_by_country=True)
        
        if not partners:
            self._print_and_buffer(f"No partners found from {country_code}.")
            return
        
        self._print_and_buffer(f"\nFound {len(partners)} partners from {country_code}:")
        self._print_and_buffer("-" * 120)
        self._print_and_buffer(f"{'No.':<4} {'Legal Name':<40} {'Total Funding':<15} {'Projects':<10} {'SI Collab.':<10} {'Ratio':<10}")
        self._print_and_buffer("-" * 120)
        
        for i, partner in enumerate(partners[:20], 1):
            self._print_and_buffer(f"{i:<4} {partner.legal_name[:38]:<40} €{partner.total_eu_funding:,.0f} {'':<3} "
                      f"{partner.total_projects:<10} {partner.slovenian_projects:<10} "
                      f"{partner.collaboration_ratio:.1%}")
        
        if len(partners) > 20:
            self._print_and_buffer(f"... and {len(partners) - 20} more partners")
        
        # Ask to save search results
        save_choice = input("\nSave these search results to file? (y/n): ").strip().lower()
        if save_choice == 'y':
            filepath = self.report_saver.save_search_results(partners, country_code, 'country')
            self._print_and_buffer(f"\n✓ Search results saved to: {filepath}")
        
        # Ask to export report for any partner
        export_choice = input("\nWould you like to export a collaboration report for any of these partners? (y/n): ").strip().lower()
        if export_choice == 'y':
            partner_num = input("Enter the partner number (or exact name): ").strip()
            try:
                idx = int(partner_num) - 1
                if 0 <= idx < len(partners):
                    selected_partner = partners[idx]
                    self._print_and_buffer(f"\nExporting report for: {selected_partner.legal_name}")
                    self.export_collaboration_report_to_txt(selected_partner.legal_name)
                    
                    details = self.get_partner_details(selected_partner.legal_name)
                    if details:
                        self.report_saver.save_collaboration_details(details, selected_partner.legal_name)
                else:
                    self._print_and_buffer("Invalid partner number.")
            except ValueError:
                self.export_collaboration_report_to_txt(partner_num)
                details = self.get_partner_details(partner_num)
                if details:
                    self.report_saver.save_collaboration_details(details, partner_num)
    
    def _get_collaborations(self):
        """Get partner details and Slovenian collaborations."""
        legal_name = input("\nEnter exact legal name of the partner: ").strip()
        if not legal_name:
            self._print_and_buffer("No partner name entered.")
            return
        
        self._print_and_buffer(f"\nGetting details for: {legal_name}")
        details = self.get_partner_details(legal_name)
        
        if not details:
            self._print_and_buffer(f"Partner not found: {legal_name}")
            return
        
        partner_info = details["partner_info"]
        collaborations = details["slovenian_projects"]
        
        self._print_and_buffer("\n" + "="*80)
        self._print_and_buffer(f"PARTNER: {partner_info['Legal Name']}")
        self._print_and_buffer("="*80)
        self._print_and_buffer(f"Country: {partner_info['Country']}")
        self._print_and_buffer(f"Total EU Funding: {partner_info['Total EU Funding']}")
        self._print_and_buffer(f"Total Projects: {partner_info['Total Projects']}")
        self._print_and_buffer(f"Slovenian Projects: {partner_info['Slovenian Projects']}")
        self._print_and_buffer(f"Collaboration Ratio: {partner_info['Collaboration Ratio']}")
        
        if collaborations:
            self._print_and_buffer(f"\nPROJECTS WITH SLOVENIAN PARTNERS ({len(collaborations)}):")
            self._print_and_buffer("-" * 80)
            for i, project in enumerate(collaborations, 1):
                self._print_and_buffer(f"\n{i}. {project['Title']}")
                self._print_and_buffer(f"   Acronym: {project['Acronym']}")
                self._print_and_buffer(f"   Website: {project['Website']}")
                self._print_and_buffer(f"   Duration: {project['Start Date']} to {project['End Date']}")
                self._print_and_buffer(f"   Budget: {project['Total Budget']}")
                self._print_and_buffer(f"   Slovenian Partners: {project['Slovenian Partners']}")
        else:
            self._print_and_buffer("\nNO PROJECTS WITH SLOVENIAN PARTNERS FOUND")
        
        # Ask to save details
        save_choice = input("\nSave these collaboration details to file? (y/n): ").strip().lower()
        if save_choice == 'y':
            filepath = self.report_saver.save_collaboration_details(details, legal_name)
            self._print_and_buffer(f"\n✓ Collaboration details saved to: {filepath}")
    
    def _export_to_csv(self):
        """Export collaborations to CSV."""
        legal_name = input("\nEnter exact legal name of the partner: ").strip()
        if not legal_name:
            self._print_and_buffer("No partner name entered.")
            return
        
        output_folder = input(f"Enter output folder (press Enter for default: {self.results_folder}): ").strip()
        if not output_folder:
            output_folder = self.results_folder
        
        filepath = self.export_collaborations_to_csv(legal_name, output_folder)
        if filepath:
            self._print_and_buffer(f"\nSuccessfully exported to: {filepath}")
    
    def _generate_report(self):
        """Generate collaboration report."""
        legal_name = input("\nEnter exact legal name of the partner: ").strip()
        if not legal_name:
            self._print_and_buffer("No partner name entered.")
            return
        
        report = self.generate_collaboration_report(legal_name)
        
        # Print report
        self._print_and_buffer("\n" + "="*80)
        self._print_and_buffer("COLLABORATION REPORT")
        self._print_and_buffer("="*80)
        self._print_and_buffer(report)
        
        # Ask to save to file
        save = input("\nSave report to file? (y/n): ").strip().lower()
        if save == 'y':
            safe_name = "".join(c for c in legal_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_name}_collaboration_report.txt"
            filepath = os.path.join(self.results_folder, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)
            
            self._print_and_buffer(f"Report saved to: {filepath}")
    
    def _export_report_to_txt(self):
        """Export collaboration report to TXT file."""
        legal_name = input("\nEnter exact legal name of the partner: ").strip()
        if not legal_name:
            self._print_and_buffer("No partner name entered.")
            return
        
        # Optional custom output path
        custom_path = input("Enter custom output path (press Enter for auto-generated): ").strip()
        if not custom_path:
            custom_path = None
        
        filepath = self.export_collaboration_report_to_txt(legal_name, custom_path)
        if filepath:
            self._print_and_buffer(f"\n✓ Report successfully exported to: {filepath}")
            
            # Also save detailed collaboration info
            details = self.get_partner_details(legal_name)
            if details:
                details_filepath = self.report_saver.save_collaboration_details(details, legal_name)
                self._print_and_buffer(f"✓ Detailed collaboration info saved to: {details_filepath}")
    
    def _view_statistics(self):
        """View partner statistics."""
        self._print_and_buffer("\n" + "="*80)
        self._print_and_buffer("PARTNER STATISTICS")
        self._print_and_buffer("="*80)
        
        if self.foreign_partners_df is not None and not self.foreign_partners_df.empty:
            # Calculate statistics from foreign partners data
            total_partners = len(self.foreign_partners_df)
            exclusive_partners = len(self.foreign_partners_df[
                self.foreign_partners_df['collaboration_level'] == 'Exclusive to SI'
            ])
            strong_partners = len(self.foreign_partners_df[
                self.foreign_partners_df['collaboration_level'] == 'Strong (>50%)'
            ])
            
            self._print_and_buffer(f"Total foreign partners with SI collaborations: {total_partners:,}")
            self._print_and_buffer(f"Partners exclusive to SI projects: {exclusive_partners:,}")
            self._print_and_buffer(f"Partners with strong SI collaboration (>50%): {strong_partners:,}")
            
            # Top countries
            if 'country' in self.foreign_partners_df.columns:
                country_counts = self.foreign_partners_df['country'].value_counts().head(10)
                self._print_and_buffer("\nTop 10 countries by number of partners collaborating with SI:")
                for country, count in country_counts.items():
                    self._print_and_buffer(f"  {country}: {count:,} partners")
        
        # Overall statistics
        if self.all_projects_df is not None:
            total_projects = len(self.all_projects_df)
            self._print_and_buffer(f"\nTotal projects in database: {total_projects:,}")
            
            # Count projects with Slovenian partners
            si_project_count = 0
            for idx, row in self.all_projects_df.iterrows():
                has_slovenian, _ = self._project_has_slovenian_partners(row['project_ID'])
                if has_slovenian:
                    si_project_count += 1
            
            self._print_and_buffer(f"Projects with Slovenian partners: {si_project_count:,}")
            self._print_and_buffer(f"Percentage of projects with SI: {si_project_count/total_projects:.1%}")
        
        # Ask to save statistics
        save_choice = input("\nSave these statistics to file? (y/n): ").strip().lower()
        if save_choice == 'y':
            # Capture the statistics output
            stats_lines = []
            stats_lines.append("=" * 80)
            stats_lines.append("PARTNER STATISTICS")
            stats_lines.append("=" * 80)
            stats_lines.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            stats_lines.append("")
            
            if self.foreign_partners_df is not None and not self.foreign_partners_df.empty:
                stats_lines.append(f"Total foreign partners with SI collaborations: {total_partners:,}")
                stats_lines.append(f"Partners exclusive to SI projects: {exclusive_partners:,}")
                stats_lines.append(f"Partners with strong SI collaboration (>50%): {strong_partners:,}")
            
            if self.all_projects_df is not None:
                stats_lines.append(f"\nTotal projects in database: {total_projects:,}")
                stats_lines.append(f"Projects with Slovenian partners: {si_project_count:,}")
                stats_lines.append(f"Percentage of projects with SI: {si_project_count/total_projects:.1%}")
            
            stats_lines.append("")
            stats_lines.append("=" * 80)
            
            filepath = self.report_saver.save_report("\n".join(stats_lines), "statistics_report")
            self._print_and_buffer(f"\n✓ Statistics saved to: {filepath}")
    
    def _debug_partner(self):
        """Debug partner projects."""
        legal_name = input("\nEnter exact legal name of the partner to debug: ").strip()
        if not legal_name:
            self._print_and_buffer("No partner name entered.")
            return
        
        self.debug_partner_projects(legal_name)
        
        # Ask to save debug output
        save_choice = input("\nSave debug output to file? (y/n): ").strip().lower()
        if save_choice == 'y':
            # Capture the debug output from buffer
            debug_lines = self.terminal_output_buffer[-50:]  # Get recent output
            filepath = self.report_saver.save_report("\n".join(debug_lines), f"debug_{legal_name}")
            self._print_and_buffer(f"\n✓ Debug output saved to: {filepath}")


# ---------------------------------------------------------------
# MAIN EXECUTION
# ---------------------------------------------------------------
def main():
    """
    Main function to search for partners and export collaboration reports.
    This function provides a streamlined workflow for searching partners
    and exporting their collaboration reports to .txt files.
    """
    print("Initializing Participant Query System...")
    query_system = ParticipantQuerySystem()
    
    # Check if data is loaded
    if query_system.all_projects_df is None:
        print("Failed to load data. Exiting.")
        return
    
    # Ask for output folder at the beginning
    print("\n" + "="*80)
    print("SETUP: OUTPUT FOLDER CONFIGURATION")
    print("="*80)
    custom_folder = input(f"Enter output folder path (press Enter for default: {query_system.results_folder}): ").strip()
    if custom_folder:
        query_system.report_saver.set_output_folder(custom_folder)
        query_system.results_folder = custom_folder
    
    # Create session folder
    create_session = input("\nCreate a new session folder for today's outputs? (y/n): ").strip().lower()
    if create_session == 'y':
        query_system.report_saver.create_session_folder()
    
    print("\n" + "="*80)
    print("PARTNER SEARCH AND REPORT EXPORT SYSTEM")
    print("="*80)
    print("This tool helps you search for partners and export collaboration reports.")
    print("All terminal output can be saved at any time using option 9.")
    print()
    
    while True:
        print("\n" + "-"*40)
        print("MAIN MENU")
        print("-"*40)
        print("1. Search partners by name")
        print("2. Search partners by country")
        print("3. Export collaboration report for a partner (TXT)")
        print("4. View partner details and collaborations")
        print("5. Full interactive session")
        print("6. Save all terminal output from this session")
        print("7. Change output folder")
        print("8. Exit")
        print()
        
        choice = input("Enter your choice (1-8): ").strip()
        
        if choice == "1":
            # Search by name
            search_term = input("\nEnter partner name to search for: ").strip()
            if not search_term:
                print("No search term entered.")
                continue
            
            print(f"\nSearching for partners with '{search_term}' in name...")
            partners = query_system.search_partners(search_term)
            
            if not partners:
                print("No partners found.")
                continue
            
            # Display results
            print(f"\nFound {len(partners)} partners:")
            print("-" * 120)
            print(f"{'No.':<4} {'Legal Name':<40} {'Country':<8} {'Total Funding':<15} {'Projects':<10} {'SI Collab.':<10} {'Ratio':<10}")
            print("-" * 120)
            
            for i, partner in enumerate(partners[:20], 1):
                print(f"{i:<4} {partner.legal_name[:38]:<40} {partner.country:<8} "
                      f"€{partner.total_eu_funding:,.0f} {'':<3} {partner.total_projects:<10} "
                      f"{partner.slovenian_projects:<10} {partner.collaboration_ratio:.1%}")
            
            if len(partners) > 20:
                print(f"... and {len(partners) - 20} more partners")
            
            # Save search results
            save_choice = input("\nSave these search results to file? (y/n): ").strip().lower()
            if save_choice == 'y':
                filepath = query_system.report_saver.save_search_results(partners, search_term, 'name')
                print(f"\n✓ Search results saved to: {filepath}")
            
            # Export report for selected partner
            export_choice = input("\nWould you like to export a collaboration report for any of these partners? (y/n): ").strip().lower()
            if export_choice == 'y':
                partner_num = input("Enter the partner number (or exact name): ").strip()
                try:
                    idx = int(partner_num) - 1
                    if 0 <= idx < len(partners):
                        selected_partner = partners[idx]
                        print(f"\nExporting report for: {selected_partner.legal_name}")
                        query_system.export_collaboration_report_to_txt(selected_partner.legal_name)
                        
                        # Also save detailed collaboration info
                        details = query_system.get_partner_details(selected_partner.legal_name)
                        if details:
                            query_system.report_saver.save_collaboration_details(details, selected_partner.legal_name)
                    else:
                        print("Invalid partner number.")
                except ValueError:
                    query_system.export_collaboration_report_to_txt(partner_num)
                    details = query_system.get_partner_details(partner_num)
                    if details:
                        query_system.report_saver.save_collaboration_details(details, partner_num)
        
        elif choice == "2":
            # Search by country
            country_code = input("\nEnter 2-letter country code (e.g., DE, FR, IT): ").strip().upper()
            if len(country_code) != 2:
                print("Please enter a valid 2-letter country code.")
                continue
            
            print(f"\nSearching for partners from country: {country_code}...")
            partners = query_system.search_partners(country_code, search_by_country=True)
            
            if not partners:
                print(f"No partners found from {country_code}.")
                continue
            
            print(f"\nFound {len(partners)} partners from {country_code}:")
            print("-" * 120)
            print(f"{'No.':<4} {'Legal Name':<40} {'Total Funding':<15} {'Projects':<10} {'SI Collab.':<10} {'Ratio':<10}")
            print("-" * 120)
            
            for i, partner in enumerate(partners[:20], 1):
                print(f"{i:<4} {partner.legal_name[:38]:<40} €{partner.total_eu_funding:,.0f} {'':<3} "
                      f"{partner.total_projects:<10} {partner.slovenian_projects:<10} "
                      f"{partner.collaboration_ratio:.1%}")
            
            if len(partners) > 20:
                print(f"... and {len(partners) - 20} more partners")
            
            # Save search results
            save_choice = input("\nSave these search results to file? (y/n): ").strip().lower()
            if save_choice == 'y':
                filepath = query_system.report_saver.save_search_results(partners, country_code, 'country')
                print(f"\n✓ Search results saved to: {filepath}")
            
            # Export report for selected partner
            export_choice = input("\nWould you like to export a collaboration report for any of these partners? (y/n): ").strip().lower()
            if export_choice == 'y':
                partner_num = input("Enter the partner number (or exact name): ").strip()
                try:
                    idx = int(partner_num) - 1
                    if 0 <= idx < len(partners):
                        selected_partner = partners[idx]
                        print(f"\nExporting report for: {selected_partner.legal_name}")
                        query_system.export_collaboration_report_to_txt(selected_partner.legal_name)
                        
                        details = query_system.get_partner_details(selected_partner.legal_name)
                        if details:
                            query_system.report_saver.save_collaboration_details(details, selected_partner.legal_name)
                    else:
                        print("Invalid partner number.")
                except ValueError:
                    query_system.export_collaboration_report_to_txt(partner_num)
                    details = query_system.get_partner_details(partner_num)
                    if details:
                        query_system.report_saver.save_collaboration_details(details, partner_num)
        
        elif choice == "3":
            # Direct export of collaboration report
            legal_name = input("\nEnter exact legal name of the partner: ").strip()
            if not legal_name:
                print("No partner name entered.")
                continue
            
            # Optional custom output path
            custom_path = input("Enter custom output path (press Enter for auto-generated): ").strip()
            if not custom_path:
                custom_path = None
            
            filepath = query_system.export_collaboration_report_to_txt(legal_name, custom_path)
            if filepath:
                print(f"\n✓ Report successfully exported to: {filepath}")
                
                # Also save detailed collaboration info
                details = query_system.get_partner_details(legal_name)
                if details:
                    details_filepath = query_system.report_saver.save_collaboration_details(details, legal_name)
                    print(f"✓ Detailed collaboration info saved to: {details_filepath}")
        
        elif choice == "4":
            # View partner details and collaborations
            legal_name = input("\nEnter exact legal name of the partner: ").strip()
            if not legal_name:
                print("No partner name entered.")
                continue
            
            details = query_system.get_partner_details(legal_name)
            if not details:
                print(f"Partner not found: {legal_name}")
                continue
            
            partner_info = details["partner_info"]
            collaborations = details["slovenian_projects"]
            
            print("\n" + "="*80)
            print(f"PARTNER: {partner_info['Legal Name']}")
            print("="*80)
            print(f"Country: {partner_info['Country']}")
            print(f"Total EU Funding: {partner_info['Total EU Funding']}")
            print(f"Total Projects: {partner_info['Total Projects']}")
            print(f"Slovenian Projects: {partner_info['Slovenian Projects']}")
            print(f"Collaboration Ratio: {partner_info['Collaboration Ratio']}")
            
            if collaborations:
                print(f"\nPROJECTS WITH SLOVENIAN PARTNERS ({len(collaborations)}):")
                print("-" * 80)
                for i, project in enumerate(collaborations, 1):
                    print(f"\n{i}. {project['Title']}")
                    print(f"   Acronym: {project['Acronym']}")
                    print(f"   Website: {project['Website']}")
                    print(f"   Duration: {project['Start Date']} to {project['End Date']}")
                    print(f"   Budget: {project['Total Budget']}")
                    print(f"   Slovenian Partners: {project['Slovenian Partners']}")
            else:
                print("\nNO PROJECTS WITH SLOVENIAN PARTNERS FOUND")
            
            # Save details
            save_choice = input("\nSave these collaboration details to file? (y/n): ").strip().lower()
            if save_choice == 'y':
                filepath = query_system.report_saver.save_collaboration_details(details, legal_name)
                print(f"\n✓ Collaboration details saved to: {filepath}")
        
        elif choice == "5":
            # Launch full interactive session
            query_system.interactive_query()
            break
        
        elif choice == "6":
            # Save all terminal output
            description = input("\nEnter a description for this saved output (optional): ").strip()
            if not description:
                description = "main_session_output"
            
            filepath = query_system.save_current_session_output(description)
            if filepath:
                print(f"\n✓ Terminal output saved to: {filepath}")
        
        elif choice == "7":
            # Change output folder
            new_folder = input("\nEnter new output folder path: ").strip()
            if new_folder:
                query_system.report_saver.set_output_folder(new_folder)
                query_system.results_folder = new_folder
                print(f"Output folder changed to: {new_folder}")
            else:
                print("No folder specified. Keeping current folder.")
        
        elif choice == "8":
            print("\nThank you for using the Partner Search and Report Export System!")
            break
        
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    # Run the streamlined main function for search and export
    main()
