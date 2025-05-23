from bs4 import BeautifulSoup
import re

def format_currency(value):
    """Format currency string to proper format with commas"""
    try:
        # Remove any existing commas and convert to float
        num = float(value.replace(',', ''))
        # Format with 2 decimal places and add commas
        return f"{num:,.2f}"
    except:
        return value

def print_header(soup):
    """Print the header section with project details"""
    print("ข้อมูลสาระสำคัญในสัญญา")
    print(f"{'หน่วยงาน':<15} {soup.find('input', {'name': 'deptSubName2'})['value']}")
    print(f"{'จังหวัด':<15} {soup.find('input', {'name': 'moiName'})['value']}")
    print(f"{'วิธีการจัดหา':<15} {soup.find('input', {'name': 'methodName2'})['value']}")
    print(f"{'ประเภทการจัดหา':<15} {soup.find('input', {'name': 'typeName2'})['value']}")
    print(f"{'ประเภทโครงการ':<15} {soup.find('input', {'name': 'govStatus2'})['value']}")
    print(f"{'เลขที่โครงการ':<15} {soup.find('input', {'name': 'projectId'})['value']}")
    print(f"{'ชื่อโครงการ':<15} {soup.find('input', {'name': 'projectName2'})['value']}")
    
    budget = format_currency(soup.find('input', {'name': 'projectMoney2'})['value'])
    price = format_currency(soup.find('input', {'name': 'priceBuild2'})['value'])
    
    print(f"{'งบประมาณ':<15} {budget} บาท")
    print(f"{'ราคากลาง':<15} {price} บาท")
    print(f"{'สถานะโครงการ':<15} {soup.find('input', {'name': 'projectStatus2'})['value']}")
    print("\nรายชื่อผู้เสนอราคา")

def print_bidders_table(soup):
    """Print the bidders table"""
    # Find the table with bidder information
    bidders_table = soup.find_all('table')[6]  # Adjust index based on your HTML structure
    
    # Print table headers
    headers = ["เลขประจำตัวผู้เสียภาษีอากร", "รายชื่อผู้เสนอราคา", "ราคาที่เสนอ"]
    print(f"{headers[0]:<25} {headers[1]:<40} {headers[2]}")
    print("-" * 80)

    # Find and process the data row
    data_row = bidders_table.find('tr', {'class': 'tr0'})
    if data_row:
        cells = data_row.find_all('td')
        
        # Get lists by splitting on <br> tags
        tax_ids = [x.strip() for x in cells[2].get_text('<br>').split('<br>') if x.strip()]
        bidder_names = [x.strip() for x in cells[3].get_text('<br>').split('<br>') if x.strip()]
        prices = [x.strip() for x in cells[4].get_text('<br>').split('<br>') if x.strip()]
        
        # Print all rows
        for i in range(len(tax_ids)):
            print(f"{tax_ids[i]:<25} {bidder_names[i]:<40} {format_currency(prices[i])}")

def main():
    # Read the HTML file
    with open('html_response.txt', 'r', encoding='utf-8') as file:
        html_content = file.read()

    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Print formatted output
    print_header(soup)
    print_bidders_table(soup)

if __name__ == "__main__":
    main()