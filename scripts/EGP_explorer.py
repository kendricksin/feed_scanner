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
            bid_info = self._extract_bid_info(soup, project_info['reference_price'])
            
            return {
                'project': project_info,
                'bids': bid_info
            }
            
        except Exception as e:
            logger.error(f"Error getting project details: {e}")
            return {'project': {}, 'bids': []}

    def _extract_project_info(self, soup: BeautifulSoup) -> Dict:
        """Extract project information from HTML"""
        info = {}
        
        # Try to get project name and reference price first
        for elem in soup.find_all('input', {'class': 'txtDisabled'}):
            name = elem.get('name', '')
            value = elem.get('value', '').strip()
            
            if name == 'projectId':
                info['project_id'] = value
            elif name == 'deptSubName2':
                info['agency'] = value
            elif name == 'moiName':
                info['province'] = value
            elif name == 'methodName2':
                info['procurement_method'] = value
            elif name == 'typeName2':
                info['procurement_type'] = value
            elif name == 'projectName2':
                info['project_name'] = value
            elif name == 'priceBuild2' and value:
                try:
                    info['reference_price'] = float(value.replace(',', ''))
                except ValueError:
                    pass
                    
        return info

    def _extract_bid_info(self, soup: BeautifulSoup, reference_price: float) -> List[Dict]:
        """Extract bid information from HTML"""
        bids_table = None
        for table in soup.find_all('table'):
            if table.find('td', string=lambda t: t and 'รายชื่อผู้เสนอราคา' in t):
                bids_table = table
                break

        if not bids_table:
            return []

        bids = []
        for row in bids_table.find_all('tr', class_='tr0'):
            cells = row.find_all('td')
            if len(cells) >= 5:
                tax_ids = cells[2].get_text('\n').strip().split('\n')
                companies = cells[3].get_text('\n').strip().split('\n')
                amounts = cells[4].get_text('\n').strip().split('\n')
                
                for tax_id, company, amount in zip(tax_ids, companies, amounts):
                    bid_amount = float(amount.replace(',', ''))
                    price_cut = ((bid_amount / reference_price) - 1) * 100
                    
                    bids.append({
                        'tax_id': tax_id.strip(),
                        'company': company.strip(),
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
                st.header("📋 Project Information")
                col1, col2 = st.columns(2)
                
                project = result['project']
                with col1:
                    st.metric("Project ID", project.get('project_id', 'N/A'))
                    st.metric("Agency", project.get('agency', 'N/A'))
                    st.metric("Province", project.get('province', 'N/A'))
                
                with col2:
                    method = project.get('procurement_method', project.get('methodName2', 'N/A'))
                    st.metric("Method", method)
                    st.metric("Type", project.get('procurement_type', project.get('typeName2', 'N/A')))
                    if 'reference_price' in project:
                        st.metric("Reference Price", format_currency(project['reference_price']))
                
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