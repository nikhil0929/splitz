import json
import requests
from io import BytesIO


class NanonetsReceiptParser:
    def __init__(self, url, api_key):
        self.url = url
        self.api_key = api_key

    def parse_receipt(self, file_content):

            
        # Send POST request to OCR model
        response = requests.post(
            self.url,
            auth=requests.auth.HTTPBasicAuth(self.api_key, ''),
            files={"file": BytesIO(file_content)}
        )

        # print(response.text)

        # Assuming response.text contains the JSON string from the OCR model
        json_data = json.loads(response.text)
        print("JSON: ", json_data)

        # Extract predictions
        predictions = json_data.get("result", [])[0].get("prediction", [])

        # Variables to store extracted data
        merchant_name = ""
        total_amount = 0.0  
        tax_amount = 0.0    
        date = ""
        items = []

        # Helper dictionary to organize items
        item_details = {}

        # Iterate through each prediction
        for prediction in predictions:
            if prediction['label'] == 'Merchant_Name':
                merchant_name = prediction['ocr_text']
            elif prediction['label'] == 'Total_Amount':
                # Clean total
                clean_total_amount = prediction['ocr_text'].replace('$', '').replace(',', '') if prediction['ocr_text'] else '0.0'
                try:
                    # print(clean_total_amount, type(clean_total_amount))  # comment out
                    total_amount = float(clean_total_amount)  # truthy value else 0.0
                    # print(total_amount, type(total_amount))  # comment out
                except ValueError:
                    total_amount = 0.0  # float conversion error
            elif prediction['label'] == 'Tax_Amount':
                # Clean tax
                clean_tax_amount = prediction['ocr_text'].replace('$', '').replace(',', '') if prediction['ocr_text'] else '0.0'
                try:
                    # print(clean_tax_amount, type(clean_tax_amount))  # comment out
                    tax_amount = float(clean_tax_amount)  # truthy value else 0.0
                    # print(tax_amount, type(tax_amount))  # comment out
                except ValueError: 
                    tax_amount = 0.0  # float conversion error
            elif prediction['label'] == 'Date':
                date = prediction['ocr_text']
            elif prediction['label'] == 'table':
                for cell in prediction['cells']:
                    row = cell['row']
                    label = cell['label']
                    text = cell['text']
                    if row not in item_details:
                        item_details[row] = {'Quantity': '1', 'Description': '', 'Line_Amount': ''}  # Default quantity to '1'
                    if label in ['Quantity', 'Description', 'Line_Amount']:
                        item_details[row][label] = text

        # Convert item details to a list of structured dictionaries
        item_list = []
        for item in item_details.values():
            # Cleaning line amount
            clean_line_amount = item['Line_Amount'].replace('$', '').replace(',', '') if item['Line_Amount'] else '0.0'
            try:
                price = float(clean_line_amount)
            except ValueError:
                price = 0.0

            # Converting quantity to an integer
            try:
                quantity = int(item['Quantity']) if item['Quantity'] else 1
            except ValueError:
                quantity = 1  # Default to 1 if conversion fails

            item_list.append({
                'item_name': item['Description'], 
                'item_price': price,
                'item_quantity': quantity
            })

        # Final Output Dictionary
        parsed_receipt = {
            'merchant_name': merchant_name,
            'total_amount': total_amount,
            'tax_amount': tax_amount,
            "tip_amount": 0.00,
            'date': date,
            'items': item_list
        }

        return parsed_receipt

