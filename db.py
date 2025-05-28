import os
import json
from datetime import datetime
import sqlite3
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, MetaData, Table, select, insert, Boolean, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import secrets
import string

# Create a directory for databases if it doesn't exist
DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

# Local SQLite database file
DB_PATH = os.path.join(DB_DIR, 'microarray_analysis.db')
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Define base class for SQLAlchemy models
Base = declarative_base()

# Define the Analysis model to store analysis results
class Analysis(Base):
    __tablename__ = 'analyses'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    date_created = Column(DateTime, default=datetime.utcnow)
    rows = Column(Integer, nullable=False)
    columns = Column(Integer, nullable=False)
    image_filename = Column(String(255), nullable=True)
    grid_params = Column(Text, nullable=False)  # Stored as JSON
    results = Column(Text, nullable=False)  # Stored as JSON

# New models for client portal system
class ClientReport(Base):
    __tablename__ = 'client_reports'
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(String(255), nullable=False)
    patient_name = Column(String(255), nullable=False)
    report_date = Column(DateTime, default=datetime.utcnow)
    practitioner = Column(String(255), nullable=True)
    collection_date = Column(String(255), nullable=True)
    gender = Column(String(10), nullable=True)
    dob = Column(String(255), nullable=True)
    specimen_type = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    pdf_data = Column(LargeBinary, nullable=False)  # Store PDF binary data
    allergen_data = Column(Text, nullable=False)  # JSON string of allergen results
    username = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    access_granted = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, nullable=True)

class PortalSettings(Base):
    __tablename__ = 'portal_settings'
    
    id = Column(Integer, primary_key=True)
    setting_name = Column(String(255), nullable=False, unique=True)
    setting_value = Column(Text, nullable=False)
    updated_date = Column(DateTime, default=datetime.utcnow)

class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.Session = None
        self.connected = False
        self.db_url = DATABASE_URL
        
        # Try to connect to the database
        self.connect()
    
    def connect(self, db_url=None):
        """Connect to the database using PostgreSQL or SQLite fallback"""
        if db_url:
            self.db_url = db_url
        else:
            # Try PostgreSQL from environment first
            import os
            postgres_url = os.environ.get('DATABASE_URL')
            if postgres_url:
                self.db_url = postgres_url
        
        try:
            # Create SQLAlchemy engine
            self.engine = create_engine(self.db_url)
            
            # Create session factory
            self.Session = sessionmaker(bind=self.engine)
            
            # Create tables if they don't exist
            Base.metadata.create_all(self.engine)
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(select(1))
                self.connected = True
            
            if 'postgresql' in self.db_url:
                print("Connected to PostgreSQL cloud database")
            else:
                print(f"Connected to local SQLite database at: {DB_PATH}")
            return True
        except Exception as e:
            print(f"Database connection error: {e}")
            self.connected = False
            return False
    
    def is_connected(self):
        """Check if the database is connected"""
        return self.connected
    
    def save_analysis(self, name, description, rows, columns, image_filename, grid_params, results_df):
        """
        Save analysis results to the database
        
        Parameters:
        -----------
        name : str
            Name of the analysis
        description : str
            Description of the analysis
        rows : int
            Number of rows in the grid
        columns : int
            Number of columns in the grid
        image_filename : str
            Filename of the analyzed image
        grid_params : dict
            Grid parameters used for the analysis
        results_df : pandas.DataFrame
            Analysis results dataframe
        
        Returns:
        --------
        int
            ID of the saved analysis record, or None if save failed
        """
        if not self.connected or self.Session is None:
            print("Not connected to database.")
            return None
        
        try:
            # Convert dataframe to JSON
            results_json = results_df.to_json(orient='records')
            
            # Create a new Analysis object
            analysis = Analysis(
                name=name,
                description=description,
                rows=rows,
                columns=columns,
                image_filename=image_filename,
                grid_params=json.dumps(grid_params),
                results=results_json
            )
            
            # Save to database
            session = self.Session()
            session.add(analysis)
            session.commit()
            analysis_id = analysis.id
            session.close()
            
            return analysis_id
        except Exception as e:
            print(f"Error saving analysis: {e}")
            return None
    
    def get_analyses(self):
        """
        Get a list of all analyses
        
        Returns:
        --------
        list
            List of dictionaries containing analysis information
        """
        if not self.connected or self.Session is None:
            print("Not connected to database.")
            return []
        
        try:
            session = self.Session()
            analyses = session.query(Analysis).order_by(Analysis.date_created.desc()).all()
            
            result = []
            for analysis in analyses:
                result.append({
                    'id': analysis.id,
                    'name': analysis.name,
                    'description': analysis.description,
                    'date_created': analysis.date_created,
                    'rows': analysis.rows,
                    'columns': analysis.columns,
                    'image_filename': analysis.image_filename
                })
            
            session.close()
            return result
        except Exception as e:
            print(f"Error retrieving analyses: {e}")
            return []
    
    def get_analysis(self, analysis_id):
        """
        Get a specific analysis by ID
        
        Parameters:
        -----------
        analysis_id : int
            ID of the analysis to retrieve
        
        Returns:
        --------
        dict
            Dictionary containing analysis information and results
        """
        if not self.connected or self.Session is None:
            print("Not connected to database.")
            return None
        
        try:
            session = self.Session()
            analysis = session.query(Analysis).filter(Analysis.id == analysis_id).first()
            
            if not analysis:
                return None
            
            # Parse JSON data
            grid_params = json.loads(str(analysis.grid_params))
            results = json.loads(str(analysis.results))
            
            result = {
                'id': analysis.id,
                'name': analysis.name,
                'description': analysis.description,
                'date_created': analysis.date_created,
                'rows': analysis.rows,
                'columns': analysis.columns,
                'image_filename': analysis.image_filename,
                'grid_params': grid_params,
                'results': results
            }
            
            session.close()
            return result
        except Exception as e:
            print(f"Error retrieving analysis: {e}")
            return None
    
    def generate_client_credentials(self, client_info):
        """Generate unique username and password for client access"""
        # Extract name and birth year from client info
        name = client_info.get('name', 'client').replace(' ', '').lower()
        dob = client_info.get('dob', '')
        
        # Extract year from date of birth
        birth_year = ""
        if dob:
            # Try to extract year from various date formats
            try:
                # Handle formats like "12/06/1972", "1972-06-12", "1972", "1/1/90"
                if '/' in dob:
                    parts = dob.split('/')
                    # Check last part first (most common format)
                    year_part = parts[-1].strip()
                    if len(year_part) == 4 and year_part.isdigit():
                        birth_year = year_part
                    elif len(year_part) == 2 and year_part.isdigit():
                        # Convert 2-digit year to 4-digit (assume 90-99 = 1990-1999, 00-89 = 2000-2089)
                        year_int = int(year_part)
                        if year_int >= 90:
                            birth_year = str(1900 + year_int)
                        else:
                            birth_year = str(2000 + year_int)
                    elif len(parts[0]) == 4 and parts[0].isdigit():
                        birth_year = parts[0]
                elif '-' in dob:
                    parts = dob.split('-')
                    year_part = parts[0] if len(parts[0]) >= 2 else parts[-1]
                    if len(year_part) == 4 and year_part.isdigit():
                        birth_year = year_part
                    elif len(year_part) == 2 and year_part.isdigit():
                        year_int = int(year_part)
                        if year_int >= 90:
                            birth_year = str(1900 + year_int)
                        else:
                            birth_year = str(2000 + year_int)
                elif len(dob) == 4 and dob.isdigit():
                    birth_year = dob
                elif len(dob) == 2 and dob.isdigit():
                    year_int = int(dob)
                    if year_int >= 90:
                        birth_year = str(1900 + year_int)
                    else:
                        birth_year = str(2000 + year_int)
                else:
                    # Try to find any year pattern
                    import re
                    # Look for 4-digit years first
                    year_match = re.search(r'\b(19|20)\d{2}\b', dob)
                    if year_match:
                        birth_year = year_match.group()
                    else:
                        # Look for 2-digit years
                        two_digit_match = re.search(r'\b\d{2}\b', dob)
                        if two_digit_match:
                            year_int = int(two_digit_match.group())
                            if year_int >= 90:
                                birth_year = str(1900 + year_int)
                            else:
                                birth_year = str(2000 + year_int)
            except:
                birth_year = ""
        
        # Create base username
        base_username = f"{name}_{birth_year}" if birth_year else f"{name}_unknown"
        
        # Check for duplicates and add numerical suffix if needed
        username = base_username
        counter = 2
        
        if self.connected and self.Session:
            session = self.Session()
            while True:
                existing = session.query(ClientReport).filter_by(username=username).first()
                if not existing:
                    break
                username = f"{base_username}_{counter}"
                counter += 1
            session.close()
        
        # Generate a secure password
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for _ in range(8))
        
        return username, password
    
    def save_client_report(self, client_info, pdf_data, allergen_data):
        """
        Save a client report with authentication credentials
        
        Parameters:
        -----------
        client_info : dict
            Client information dictionary
        pdf_data : bytes
            PDF report binary data
        allergen_data : pandas.DataFrame
            Allergen results dataframe
        
        Returns:
        --------
        dict
            Dictionary containing username, password, and report ID
        """
        if not self.connected or self.Session is None:
            return None
        
        try:
            # Generate unique credentials
            username, password = self.generate_client_credentials(client_info)
            
            # Convert allergen data to JSON
            allergen_json = allergen_data.to_json(orient='records')
            
            # Create new client report record
            client_report = ClientReport(
                patient_id=client_info.get('patient_id', ''),
                patient_name=client_info.get('name', ''),
                practitioner=client_info.get('practitioner', ''),
                collection_date=client_info.get('collection_date', ''),
                gender=client_info.get('gender', ''),
                dob=client_info.get('dob', ''),
                specimen_type=client_info.get('specimen', ''),
                email=client_info.get('email', ''),
                pdf_data=pdf_data,
                allergen_data=allergen_json,
                username=username,
                password=password
            )
            
            # Save to database
            session = self.Session()
            session.add(client_report)
            session.commit()
            report_id = client_report.id
            session.close()
            
            return {
                'report_id': report_id,
                'username': username,
                'password': password,
                'patient_name': client_info.get('name', ''),
                'patient_id': client_info.get('patient_id', '')
            }
        except Exception as e:
            print(f"Error saving client report: {e}")
            return None
    
    def get_all_client_reports(self):
        """Get all client reports for archive view"""
        if not self.connected or self.Session is None:
            return []
        
        try:
            session = self.Session()
            reports = session.query(ClientReport).order_by(ClientReport.report_date.desc()).all()
            
            result = []
            for report in reports:
                result.append({
                    'id': report.id,
                    'patient_name': report.patient_name,
                    'patient_id': report.patient_id,
                    'report_date': report.report_date,
                    'practitioner': report.practitioner,
                    'username': report.username,
                    'password': report.password,
                    'is_active': report.is_active,
                    'last_accessed': report.last_accessed
                })
            
            session.close()
            return result
        except Exception as e:
            print(f"Error retrieving client reports: {e}")
            return []
    
    def get_client_report(self, username, password):
        """Authenticate and retrieve client report"""
        if not self.connected or self.Session is None:
            return None
        
        try:
            session = self.Session()
            report = session.query(ClientReport).filter_by(
                username=username, 
                password=password, 
                is_active=True
            ).first()
            
            if report:
                # Update last accessed time
                report.last_accessed = datetime.utcnow()
                session.commit()
                
                # Return report data
                result = {
                    'id': report.id,
                    'patient_name': report.patient_name,
                    'patient_id': report.patient_id,
                    'report_date': report.report_date,
                    'pdf_data': report.pdf_data,
                    'allergen_data': json.loads(report.allergen_data)
                }
                session.close()
                return result
            
            session.close()
            return None
        except Exception as e:
            print(f"Error retrieving client report: {e}")
            return None

# Create a global instance of the database manager
db_manager = DatabaseManager()

# Function to check database connection
def check_db_connection():
    """Check if the database is connected, try to connect if not"""
    if not db_manager.is_connected():
        return db_manager.connect()
    return db_manager.is_connected()