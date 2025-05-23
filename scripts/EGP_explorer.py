import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from typing import Dict, List
import logging
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EGPClient:
    BASE_URL = "https://process3.gprocurement.go.th/egp2procmainWeb/procsearch.sch"
    
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,th;q=0.8',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://process3.gprocurement.go.th',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'
        }

    def get_project_details(self, project_id: str) -> Dict:
        form_data = {
            'announceType': 'I',
            'servlet': 'FPRO9965Servlet',
            'proc_id': 'FPRO9965_2',
            'proc_name': 'Procure',
            'processFlows': 'Procure',
            'mode': 'LINK',
            'homeflag': 'A',
            'temp_projectId': project_id,
            'projectId': project_id
        }
        
        try:
            response = self.session.post(
                self.BASE_URL,
                data=form_data,
                headers=self.headers,
                verify=False,
                timeout=30
            )
            
            soup = BeautifulSoup(response.text, 'html.parser')
            project_info = self._extract_project_info(soup)
            bid_info = self._extract_bid_info(soup)
            
            return {
                'project': project_info,
                'bids': bid_info
            }
            
        except Exception as e:
            logger.error(f"Error getting project details: {e}")
            return {'project': {}, 'bids': []}

    def _extract_project_info(self, soup: BeautifulSoup) -> Dict:
        """Extract project information from HTML using improved parser"""
        def get_input_value(name):
            try:
                elem = soup.find('input', {'name': name})
                if elem and 'value' in elem.attrs:
                    return elem['value'].strip()
                logger.error(f"Could not find input element: {name}")
                return 'N/A'
            except Exception as e:
                logger.error(f"Error extracting {name}: {e}")
                return 'N/A'

        def parse_amount(value: str) -> float:
            try:
                if value == 'N/A':
                    return 0.0
                # Remove currency symbol, commas, and convert to float
                cleaned = value.replace('฿', '').replace(',', '').strip()
                return float(cleaned)
            except (ValueError, TypeError, AttributeError) as e:
                logger.error(f"Error parsing amount {value}: {e}")
                return 0.0

        try:
            # Define field mappings
            field_mappings = {
                'methodName2': 'procurement_method',
                'typeName2': 'procurement_type',
                'govStatus2': 'project_type',
                'projectId': 'project_id',
                'projectName2': 'project_name',
                'projectMoney2': 'budget',
                'priceBuild2': 'reference_price',
                'projectStatus2': 'project_status',
                'deptSubName2': 'agency',
                'moiName': 'province'
            }

            # Extract all values first
            raw_values = {
                field: get_input_value(html_field)
                for html_field, field in field_mappings.items()
            }

            # Log raw values for debugging
            logger.info("Raw input values:")
            for field, value in raw_values.items():
                logger.info(f"{field}: {value}")

            info = {
                'title': 'ข้อมูลสาระสำคัญในสัญญา',
                **raw_values,
                'budget': parse_amount(raw_values['budget']),
                'reference_price': parse_amount(raw_values['reference_price'])
            }
            
            # Log processed values
            logger.info("Processed project info:")
            for key, value in info.items():
                logger.info(f"{key}: {value}")
                
            return info
            
        except Exception as e:
            logger.error(f"Error in _extract_project_info: {e}")
            return {}
        
        return info

    def _extract_bid_info(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract bid information using improved parser"""
        try:
            # Find the table that contains bidder information
            bidders_table = None
            for table in soup.find_all('table'):
                if table.find('td', string=lambda t: t and 'รายชื่อผู้เสนอราคา' in t):
                    bidders_table = table
                    break

            if not bidders_table:
                logger.warning("Bidders table not found")
                return []

            # Find the data row
            data_row = bidders_table.find('tr', {'class': 'tr0'})
            if not data_row:
                logger.warning("No bid data row found")
                return []

            cells = data_row.find_all('td')
            if len(cells) < 5:
                logger.warning(f"Insufficient cells in bid row: {len(cells)}")
                return []

            # Get lists by splitting on <br> tags
            tax_ids = [x.strip() for x in cells[2].get_text('<br>').split('<br>') if x.strip()]
            bidder_names = [x.strip() for x in cells[3].get_text('<br>').split('<br>') if x.strip()]
            prices = [x.strip() for x in cells[4].get_text('<br>').split('<br>') if x.strip()]

            bids = []
            reference_price = self._extract_project_info(soup)['reference_price']
            
            # Add debug logging
            logger.info(f"Found {len(tax_ids)} bids")
            logger.info(f"Reference price: {reference_price}")
            
        except Exception as e:
            logger.error(f"Error extracting bid info: {e}")
            return []
        
        for tax_id, company, amount in zip(tax_ids, bidder_names, prices):
            bid_amount = float(amount.replace(',', ''))
            price_cut = ((bid_amount / reference_price) - 1) * 100 if reference_price else 0
            
            bids.append({
                'tax_id': tax_id,
                'company': company,
                'bid_amount': bid_amount,
                'price_cut': price_cut
            })

        return sorted(bids, key=lambda x: x['bid_amount'])

def format_currency(value: float) -> str:
    return f"฿{value:,.2f}"

def format_percentage(value: float) -> str:
    return f"{value:.1f}%"

def main():
    st.set_page_config(page_title="EGP Project Explorer", layout="wide")
    st.title("🏛️ EGP Project Explorer")
    
    client = EGPClient()
    
    project_id = st.text_input(
        "Enter Project ID",
        help="Enter the 11-digit project ID from EGP system",
        value="67109000344"
    )
    
    if st.button("🔍 Get Project Details", type="primary", use_container_width=True):
        with st.spinner("Fetching project details..."):
            result = client.get_project_details(project_id)
            
            if result['project']:
                # Project Info Section
                project = result['project']
                
                # Main header with emoji
                st.header("📄 " + project['title'])
                
                # Create two columns for the main layout
                left_col, right_col = st.columns([2, 1])
                
                with left_col:
                    st.markdown("### ข้อมูลโครงการ")
                    
                    # Core project information
                    info_md = f"""
                    **หน่วยงาน:** {project.get('agency')}  
                    **จังหวัด:** {project.get('province')}  
                    **วิธีการจัดหา:** {project.get('procurement_method')}  
                    **ประเภทการจัดหา:** {project.get('procurement_type')}  
                    **ประเภทโครงการ:** {project.get('project_type')}  
                    **เลขที่โครงการ:** {project.get('project_id')}  
                    """
                    st.markdown(info_md)
                    
                    # Project name
                    st.markdown("**ชื่อโครงการ:**")
                    if project.get('project_name') != 'N/A':
                        st.info(project.get('project_name'))
                    else:
                        st.error("ไม่พบข้อมูลชื่อโครงการ")
                
                with right_col:
                    # Financial and status metrics
                    if project.get('budget', 0) > 0:
                        st.metric(
                            "งบประมาณ",
                            format_currency(project['budget']) + " บาท"
                        )
                    
                    if project.get('reference_price', 0) > 0:
                        st.metric(
                            "ราคากลาง",
                            format_currency(project['reference_price']) + " บาท"
                        )
                    
                    if project.get('project_status') != 'N/A':
                        st.metric(
                            "สถานะโครงการ",
                            project['project_status']
                        )
                
                # Bid Information Section
                if result['bids']:
                    st.header("💰 Bid Summary") 
                    
                    # Get winning (lowest) bid
                    winning_bid = result['bids'][0]
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric(
                        "Winning Bid",
                        winning_bid['company'],
                        format_currency(winning_bid['bid_amount'])
                    )
                    
                    col2.metric(
                        "Price Cut",
                        format_percentage(winning_bid['price_cut']),
                        delta=format_percentage(winning_bid['price_cut']),
                        delta_color="inverse"
                    )
                    
                    avg_bid = sum(b['bid_amount'] for b in result['bids']) / len(result['bids'])
                    col3.metric(
                        "Average Bid",
                        format_currency(avg_bid)
                    )
                    
                    # Bid Table
                    st.header("📊 All Bids")
                    df = pd.DataFrame(result['bids'])
                    df['bid_amount'] = df['bid_amount'].map(format_currency) 
                    df['price_cut'] = df['price_cut'].map(format_percentage)
                    
                    st.dataframe(
                        df,
                        column_config={
                            "tax_id": "Tax ID",
                            "company": "Company",
                            "bid_amount": "Bid Amount",
                            "price_cut": "Price Cut"
                        },
                        use_container_width=True
                    )
            else:
                st.error("Failed to fetch project details")

if __name__ == "__main__":
    main()