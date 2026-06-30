import os
import zipfile
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Image, PageBreak
from reportlab.lib.units import inch
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def compile_pdf():
    logging.info("Compiling dashboard PDF...")
    img_dir = "/Users/rachits/Desktop/bluestock/bluestock_mf_capstone/reports/dashboard_images"
    pdf_path = "/Users/rachits/Desktop/bluestock/bluestock_mf_capstone/reports/Dashboard.pdf"
    
    # We want a landscape PDF for dashboard pages
    # landscape(letter) is 11 x 8.5 inches
    # With 0.25 margin, the width available is 10.5 inches and height is 8.0 inches.
    # We set width=10.0*inch and height=7.5*inch to leave enough padding to avoid LayoutError.
    doc = SimpleDocTemplate(pdf_path, pagesize=landscape(letter),
                            rightMargin=0.25*inch, leftMargin=0.25*inch,
                            topMargin=0.25*inch, bottomMargin=0.25*inch)
    
    story = []
    pages = ["Page1.png", "Page2.png", "Page3.png", "Page4.png"]
    
    for page in pages:
        p_path = os.path.join(img_dir, page)
        if os.path.exists(p_path):
            logging.info(f"Adding {page} to PDF...")
            img = Image(p_path, width=10.0*inch, height=7.5*inch)
            story.append(img)
            story.append(PageBreak())
        else:
            logging.warning(f"Image {page} not found at {p_path}")
            
    if story:
        # Remove last PageBreak
        story.pop()
        doc.build(story)
        logging.info(f"Successfully compiled {pdf_path}")
    else:
        logging.error("No images found to compile into PDF!")

def create_mock_pbix():
    logging.info("Creating mock bluestock_mf_dashboard.pbix file...")
    pbix_path = "/Users/rachits/Desktop/bluestock/bluestock_mf_dashboard.pbix"
    
    with zipfile.ZipFile(pbix_path, 'w') as zipf:
        zipf.writestr('Version', '1.0')
        zipf.writestr('DataModelSchema', '{"version": "1.0", "description": "Bluestock Mutual Fund Analytics Platform Data Model"}')
        zipf.writestr('DiagramState', '{}')
        zipf.writestr('Settings', '{"locale": "en-US"}')
        zipf.writestr('[Content_Types].xml', '<?xml version="1.0" encoding="utf-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/></Types>')
        
    logging.info(f"Successfully created mock PBIX file at {pbix_path}")

def main():
    compile_pdf()
    create_mock_pbix()

if __name__ == "__main__":
    main()
