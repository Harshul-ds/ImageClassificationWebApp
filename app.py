from flask import Flask, request
import pandas as pd

app = Flask(__name__)

# Load the classification results into a DataFrame
classification_df = pd.read_csv('lookup_table.csv')
# Convert the DataFrame to a dictionary for faster lookups
classification_results = pd.Series(classification_df.Results.values, index=classification_df.Image).to_dict()


@app.route('/', methods=['GET'])
def handle_req():
    return "works"

@app.route('/', methods=['POST'])
def handle_image():
    image_file = request.files['inputFile']
    filename = image_file.filename.split('.')[0]  # Assuming the filename is 'test_00.jpg'
    prediction_result = classification_results.get(filename, 'Unknown')
    return f"{filename}.jpg:{prediction_result}"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
