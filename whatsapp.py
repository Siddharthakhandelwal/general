import subprocess
from fpdf import FPDF # type: ignore
import os
import logging

def send_message(number, path):
    command = f"npx mudslide@latest send-file {number} {path}"
    result = subprocess.run(command, shell=True, text=True, capture_output=True, encoding="utf-8")    
    if result.returncode == 0:
        print(f"Message sent successfully: {result.stdout}")
    else:
        print(f"Error: {result.stderr}")

def create_pdf(number, text, filename="output.pdf"):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Handle encoding issues by replacing problematic characters
        safe_text = text.encode("latin-1", "ignore").decode("latin-1")
        pdf.multi_cell(0, 10, safe_text)
        pdf.output(filename)
        
        if not number:
            print("No phone number provided, cannot send PDF")
            return
            
        send_message(number[1:], filename)
    except Exception as e:
        print(f"Error creating or sending PDF: {e}")

def send_image(number):
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logger = logging.getLogger(__name__)
    image_array = []

    try: 
        # Make sure Downloads directory exists
        download_dir = "downloads"
        os.makedirs(download_dir, exist_ok=True)
        
        abs_path = os.path.abspath(download_dir)
        
        if not os.path.exists(abs_path):
            logger.error(f"Directory not found: {abs_path}")
            return []
            
        if not os.path.isdir(abs_path):
            logger.error(f"Path is not a directory: {abs_path}")
            return []
            
        logger.info(f"\nListing all files in: {abs_path}\n")
        
        for root, dirs, files in os.walk(abs_path):
            for file in files:
                file_path = os.path.join(root, file)
                size = os.path.getsize(file_path)
                _, extension = os.path.splitext(file)
                extension = extension[1:] if extension else "no extension"
                
                if not number:
                    logger.warning("No phone number provided, cannot send image")
                else:
                    send_message(number[1:], file_path)
                    
                logger.info(f"File: {file}")
                logger.info(f"Complete Path: {file_path}")
                logger.info(f"Type: {extension}")
                logger.info(f"Size: {size:,} bytes")
                logger.info("-" * 80 + "\n")
                image_array.append(file_path)
        return image_array

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return []   