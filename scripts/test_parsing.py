import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup

def decode_file_content(uploaded_file):
    """
    Try multiple encodings to decode the file content
    """
    encodings_to_try = ['TIS-620', 'utf-8', 'cp874', 'latin-1']
    
    file_bytes = uploaded_file.read()
    
    for encoding in encodings_to_try:
        try:
            return file_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    
    # If all encoding attempts fail, try reading as bytes
    st.error("Could not decode the file with standard encodings. Please check the file.")
    return None

def parse_bidders_details(soup):
    """
    Parse bidders details from the table after the title
    """
    # Find the span with the exact title
    title_span = soup.find('span', class_='regTitle', text=lambda t: 'รายชื่อผู้เสนอราคา' in str(t) if t else False)
    
    if not title_span:
        st.warning("Could not find bidders title")
        return []
    
    # Find the next table after the title
    current = title_span
    while current and current.name != 'table':
        current = current.find_next_sibling()
    
    if not current or current.name != 'table':
        st.warning("Could not find bidders table")
        return []
    
    # Find the data row
    data_row = current.find('tr', class_='tr0')
    if not data_row:
        st.warning("Could not find data row for bidders")
        return []

    # Find the columns
    cols = data_row.find_all('td')
    if len(cols) < 5:
        st.warning("Insufficient columns in bidders table")
        return []

    # Extract tax IDs, company names, and prices
    tax_ids = [id.strip() for id in cols[2].get_text(strip=True, separator='\n').split('\n') if id.strip()]
    companies = [name.strip() for name in cols[3].get_text(strip=True, separator='\n').split('\n') if name.strip()]
    prices = [price.strip() for price in cols[4].get_text(strip=True, separator='\n').split('\n') if price.strip()]

    # Create bidders list
    bidders = []
    for i in range(min(len(tax_ids), len(companies), len(prices))):
        bidders.append({
            'ลำดับ': i + 1,
            'รายการพิจารณา': cols[1].get_text(strip=True),
            'เลขประจำตัวผู้เสียภาษีอากร': tax_ids[i],
            'รายชื่อผู้เสนอราคา': companies[i],
            'ราคาที่เสนอ': prices[i]
        })

    return bidders

def parse_project_details(soup):
    """
    Extract project details from input fields
    """
    project_details = {}
    detail_mappings = [
        ('หน่วยงาน', 'deptSubName2'),
        ('จังหวัด', 'moiName'),
        ('วิธีการจัดหา', 'methodName2'),
        ('ประเภทการจัดหา', 'typeName2'),
        ('ประเภทโครงการ', 'govStatus2'),
        ('เลขที่โครงการ', 'projectId'),
        ('ชื่อโครงการ', 'projectName2'),
        ('ราคากลาง', 'priceBuild2')
    ]

    for label, input_name in detail_mappings:
        input_elem = soup.find('input', {'name': input_name})
        if input_elem:
            project_details[label] = input_elem.get('value', '').strip()

    return project_details

def parse_contract_details(soup):
    """
    Extract contract details from table rows
    """
    contract_data = []
    contract_rows = soup.find_all('tr', class_='tr0')

    for row in contract_rows:
        cols = row.find_all('td')
        if len(cols) >= 9:
            contract_entry = {
                'ลำดับ': cols[0].get_text(strip=True),
                'เลขประจำตัวผู้เสียภาษีอากร': cols[1].get_text(strip=True),
                'ชื่อผู้ขาย': cols[2].get_text(strip=True),
                'เลขคุมสัญญา': cols[3].get_text(strip=True),
                'เลขที่สัญญา': cols[4].get_text(strip=True),
                'วันที่ทำสัญญา': cols[5].get_text(strip=True),
                'จำนวนเงิน': cols[6].get_text(strip=True),
                'สถานะสัญญา': cols[7].get_text(strip=True),
                'เหตุผลที่คัดเลือก': cols[8].get_text(strip=True)
            }
            contract_data.append(contract_entry)

    return contract_data

def parse_procurement_document(file_content):
    """
    Main parsing function for the procurement document
    """
    # Parse the HTML content
    soup = BeautifulSoup(file_content, 'html.parser')

    # Extract project details
    project_details = parse_project_details(soup)

    # Extract contract details
    contract_details = parse_contract_details(soup)

    # Extract bidders details
    bidder_details = parse_bidders_details(soup)

    return project_details, contract_details, bidder_details

def main():
    st.set_page_config(page_title="Thai Government Procurement Document Viewer", layout="wide")
    
    st.title('Thai Government Procurement Document Viewer')
    
    # File uploader
    uploaded_file = st.file_uploader("Upload HTML Procurement Document", type=['html'])
    
    if uploaded_file is not None:
        # Read and decode the file content
        file_content = decode_file_content(uploaded_file)
        
        if file_content is None:
            st.error("Failed to read the uploaded file. Please check the file encoding.")
            return
        
        try:
            # Parse the document
            project_details, contract_details, bidder_details = parse_procurement_document(file_content)
            
            # Display Project Details
            st.header('ข้อมูลสาระสำคัญในสัญญา')
            
            # Create two columns for project details
            details_col1, details_col2 = st.columns(2)
            
            # Split project details between two columns
            project_items = list(project_details.items())
            mid = len(project_items) // 2
            
            with details_col1:
                for key, value in project_items[:mid]:
                    st.text(f'{key}: {value}')
            
            with details_col2:
                for key, value in project_items[mid:]:
                    st.text(f'{key}: {value}')
            
            # Display Contract Details
            st.header('รายละเอียดสัญญา')
            if contract_details:
                contract_df = pd.DataFrame(contract_details)
                st.dataframe(contract_df, use_container_width=True)
            else:
                st.write("No contract details found.")
            
            # Display Bidders Details
            st.header('รายชื่อผู้เสนอราคา')
            if bidder_details:
                bidder_df = pd.DataFrame(bidder_details)
                st.dataframe(bidder_df, use_container_width=True)
            else:
                st.write("No bidders found.")
        
        except Exception as e:
            st.error(f"An error occurred while parsing the document: {str(e)}")
            st.error("Please ensure the uploaded file is a valid Thai Government Procurement HTML document.")
            # Optional: print the full traceback for debugging
            import traceback
            st.error(traceback.format_exc())

if __name__ == '__main__':
    main()