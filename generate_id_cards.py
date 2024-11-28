import os
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, request, send_from_directory, render_template, jsonify
import zipfile
from io import BytesIO

# Initialize Flask app
app = Flask(__name__)

# Set directories
project_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(project_dir, "cards")
photos_dir = os.path.join(project_dir, "photos")

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

# Load font (ensure 'OpenSans-Semibold.ttf' is in the same directory)
font_path = os.path.join(project_dir, "OpenSans-Semibold.ttf")
font = ImageFont.truetype(font_path, size=25)

# Function to generate ID cards
def generate_card(data):
    try:
        # Load the template image (ensure 'template.png' is in the same directory)
        template_path = os.path.join(project_dir, "template.png")
        template = Image.open(template_path)
        
        # Load and resize the photo, handle missing photos (ensure photos are in 'photos/' directory)
        photo_path = os.path.join(photos_dir, f"{data['id']}.jpg")
        if os.path.exists(photo_path):
            pic = Image.open(photo_path).resize((165, 190), Image.Resampling.LANCZOS)
            template.paste(pic, (25, 75))
        else:
            print(f"Photo missing for ID: {data['id']}")
        
        # Draw text on the template
        draw = ImageDraw.Draw(template)
        draw.text((315, 80), str(data['id']), font=font, fill='black')
        draw.text((315, 125), data['name'], font=font, fill='black')
        draw.text((315, 170), data['class'], font=font, fill='black')
        draw.text((315, 215), data['dob'], font=font, fill='black')
        
        return template
    
    except Exception as e:
        print(f"Error generating card for {data['name']}: {e}")
        return None

# Route to upload CSV file and generate ID cards
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']
        
        # If user did not select a file
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        if file and file.filename.endswith('.csv'):
            # Save uploaded CSV file
            csv_path = os.path.join(project_dir, file.filename)
            file.save(csv_path)

            # Read the CSV file
            df = pd.read_csv(csv_path)
            records = df.to_dict(orient='records')

            # Generate and save ID cards
            for record in records:
                card = generate_card(record)
                if card:
                    card.save(os.path.join(output_dir, f"{record['id']}.jpg"))

            # Create a zip of all generated cards
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for filename in os.listdir(output_dir):
                    zip_file.write(os.path.join(output_dir, filename), filename)

            # Save the zip buffer to a file
            zip_path = os.path.join(output_dir, 'cards.zip')
            with open(zip_path, 'wb') as f:
                f.write(zip_buffer.getvalue())
            
            # Return the link to download the ID cards as a zip file
            return jsonify({"message": "ID cards generated successfully", "download_link": "/download"})

    return render_template('index.html')  # Render the HTML form for file upload

# Route to download generated ID cards as a zip file
@app.route('/download', methods=['GET'])
def download_cards():
    zip_path = os.path.join(output_dir, 'cards.zip')
    if os.path.exists(zip_path):
        return send_from_directory(output_dir, 'cards.zip', as_attachment=True)
    else:
        return jsonify({"error": "No ID cards generated yet"}), 404

if __name__ == '__main__':
    app.run(debug=True)
