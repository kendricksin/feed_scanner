import streamlit as st
from bs4 import BeautifulSoup
import pandas as pd

def parse_procurement_document(file_content):
    """
    Parse the HTML procurement document and extract key information
    """
    soup = BeautifulSoup(file_content, 'html.parser')
    
    # Extract project details
    project_details = {
        'หน่วยงาน': soup.find('input', {'name': 'deptSubName2'})['value'],
        'จังหวัด': soup.find('input', {'name': 'moiName'})['value'],
        'วิธีการจัดหา': soup.find('input', {'name': 'methodName2'})['value'],
        'ประเภทการจัดหา': soup.find('input', {'name': 'typeName2'})['value'],
        'ประเภทโครงการ': soup.find('input', {'name': 'govStatus2'})['value'],
        'เลขที่โครงการ': soup.find('input', {'name': 'projectId'})['value'],
        'ชื่อโครงการ': soup.find('input', {'name': 'projectName2'})['value'],
        'ราคากลาง': soup.find('input', {'name': 'priceBuild2'})['value']
    }
    
    # Extract contract details
    contract_rows = soup.find_all('tr', class_='tr0')
    contract_data = []
    for row in contract_rows:
        cols = row.find_all('td')
        if len(cols) >= 9:
            contract_data.append({
                'ลำดับ': cols[0].get_text(strip=True),
                'เลขประจำตัวผู้เสียภาษีอากร': cols[1].get_text(strip=True),
                'ชื่อผู้ขาย': cols[2].get_text(strip=True),
                'เลขคุมสัญญา': cols[3].get_text(strip=True),
                'เลขที่สัญญา': cols[4].get_text(strip=True),
                'วันที่ทำสัญญา': cols[5].get_text(strip=True),
                'จำนวนเงิน': cols[6].get_text(strip=True),
                'สถานะสัญญา': cols[7].get_text(strip=True),
                'เหตุผลที่คัดเลือก': cols[8].get_text(strip=True)
            })
    
    # Extract bidders details - look for the specific table with class 'thGreen'
    bidder_tables = soup.find_all('table', width='100%')
    bidder_data = []
    
    for table in bidder_tables:
        header_row = table.find('tr', class_='thGreen')
        if not header_row:
            continue
        
        # Find the data row
        data_row = table.find('tr', class_='tr0')
        if not data_row:
            continue
        
        # Extract data from the row
        cols = data_row.find_all('td')
        if len(cols) >= 5:
            # Split the multi-line content
            project_detail = cols[1].get_text(strip=True)
            tax_ids = cols[2].get_text(strip=True).split('\n')
            bidder_names = cols[3].get_text(strip=True).split('\n')
            prices = cols[4].get_text(strip=True).split('\n')
            
            # Create a row for each bidder
            for tax_id, name, price in zip(tax_ids, bidder_names, prices):
                bidder_data.append({
                    'รายการพิจารณา': project_detail,
                    'เลขประจำตัวผู้เสียภาษีอากร': tax_id.strip(),
                    'รายชื่อผู้เสนอราคา': name.strip(),
                    'ราคาที่เสนอ': price.strip()
                })
    
    return project_details, contract_data, bidder_data

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

def main():
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
            details_col1, details_col2 = st.columns(2)
            
            with details_col1:
                for key in list(project_details.keys())[:len(project_details)//2]:
                    st.text(f'{key}: {project_details[key]}')
            
            with details_col2:
                for key in list(project_details.keys())[len(project_details)//2:]:
                    st.text(f'{key}: {project_details[key]}')
            
            # Display Contract Details
            st.header('รายละเอียดสัญญา')
            contract_df = pd.DataFrame(contract_details)
            st.dataframe(contract_df, use_container_width=True)
            
            # Display Bidders Details
            st.header('รายชื่อผู้เสนอราคา')
            bidder_df = pd.DataFrame(bidder_details)
            st.dataframe(bidder_df, use_container_width=True)
        
        except Exception as e:
            st.error(f"An error occurred while parsing the document: {str(e)}")
            st.error("Please ensure the uploaded file is a valid Thai Government Procurement HTML document.")

if __name__ == '__main__':
    main()