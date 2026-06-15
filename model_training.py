import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report

# ONNX Conversion Libraries
from skl2onnx import __max_supported_opset__
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import StringTensorType

def train_and_export():
    # 1. Load the custom dataset
    print("Loading honeypot_dataset.csv...")
    try:
        df = pd.read_csv("honeypot_dataset.csv")
    except FileNotFoundError:
        print("Error: honeypot_dataset.csv not found! Make sure it is in this directory.")
        return

    X = df['log_text'].values
    y = df['label'].values

    # 2. Split data for a quick validation check
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 3. Create a processing and classification pipeline
    # We use lowercase=False to preserve case-sensitive attack flags like GET/POST/CRIT
    print("Training the TF-IDF and Logistic Regression pipeline...")
    
    clean_regex = r'\b\w+\b|/[a-zA-Z0-9_.-]+|\.\./'
    
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(lowercase=False, token_pattern=clean_regex, ngram_range=(1, 3))),
        ('classifier', LogisticRegression(max_iter=1000, C=1.0))
    ])

    # Train the model
    pipeline.fit(X_train, y_train)

    # 4. Evaluate performance
    print("\n--- Model Evaluation Results ---")
    predictions = pipeline.predict(X_test)
    print(classification_report(y_test, predictions, zero_division=0))

    # 5. Convert the Scikit-Learn pipeline to ONNX format
    print("Converting model to ONNX format...")
    
    # Define the input type. The model expects a batch of 1D strings (the log text)
    initial_type = [('str_input', StringTensorType([None, 1]))]
    
    # Get the maximum supported operational set version for compatibility
    target_opset = __max_supported_opset__

    # Convert the pipeline
    onnx_model = convert_sklearn(
        pipeline, 
        name="HoneypotLogClassifier",
        initial_types=initial_type,
        target_opset=target_opset
    )

    # 6. Save the compiled model file
    output_filename = "custom_model.onnx"
    with open(output_filename, "wb") as f:
        f.write(onnx_model.SerializeToString())
    
    print(f"\nSuccess! Exported deployment-ready model to: {output_filename}")

if __name__ == "__main__":
    train_and_export()