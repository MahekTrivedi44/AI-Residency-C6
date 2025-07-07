---
title: CtrlEMI
emoji: 📈
colorFrom: indigo
colorTo: gray
sdk: gradio
sdk_version: 5.35.0
app_file: app.py
pinned: false
license: other
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference

# Ctrl+Loan EMI Calculator! 💰✨

A charming and intuitive Equated Monthly Installment (EMI) calculator built with Gradio. This app helps you quickly calculate your monthly loan payments, total interest, and total payable amount, offering a detailed amortization schedule and a visual breakdown chart. It even supports currency conversion for global users!

## Table of Contents

* [Features](#features)
* [Live Demo](#live-demo)
* [How to Use](#how-to-use)
* [Currency Conversion](#currency-conversion)
* [Installation (Local)](#installation-local)
* [Running Locally](#running-locally)
* [Project Structure](#project-structure)
* [Technical Details](#technical-details)
* [Contact](#contact)

## Features


* **EMI Calculation:** Calculates accurate monthly EMIs based on Principal, Interest Rate, and Tenure.
* **Detailed Breakdown:** Provides Total Interest Payable and Total Amount Payable.
* **Amortization Schedule:** Generates a comprehensive table showing month-by-month principal and interest payments.
* **Visual Representation:** Includes a beautiful chart visualizing the principal vs. interest paid over time.
* **Multi-Currency Support:** Convert results to various major global currencies, offering flexibility for international users.
* **Interactive Explanations:** An "How was this calculated?" accordion provides detailed insights into the EMI, Total Interest, and Currency Conversion formulas.
* **Charming UI:** Custom CSS provides a unique, user-friendly interface with a delightful "Ctrl+Loan" theme.

## Live Demo

Experience the calculator live on Hugging Face Spaces:

**🔗 [https://huggingface.co/spaces/MahekTrivedi/CtrlEMI](https://huggingface.co/spaces/MahekTrivedi/CtrlEMI)**

## How to Use

1.  **Loan Amount (Principal):** Enter the total amount you wish to borrow.
2.  **Input Currency:** Select the currency in which your loan amount is denominated.
3.  **Annual Interest Rate (%):** Input the yearly interest rate for your loan.
4.  **Loan Tenure (Years):** Specify the repayment period in years.
5.  **Display Results In:** Choose the currency you want the EMI, total interest, and total payable amounts to be displayed in.
6.  **Click "Calculate My EMI!":** The app will instantly display your results, amortization table, and chart.
7.  **Explore Explanations:** Expand the "🤔 How was this calculated?" accordion to understand the underlying formulas and currency conversion logic.

## Currency Conversion

The calculator uses a set of static exchange rates relative to the US Dollar. Please note that these rates are **placeholders from July 5, 2025**, and are not real-time. For critical financial decisions, always consult official and up-to-date exchange rate sources.

## Installation (Local)

To run this application on your local machine, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
    cd your-repo-name
    ```
    *(Replace `your-username/your-repo-name` with your actual GitHub repository URL)*

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows:
    .\venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

    The `requirements.txt` file contains:
    ```
    gradio
    pandas
    matplotlib
    ```

## Running Locally

Once you have installed the dependencies, you can run the Gradio app:

```bash
python app.py
```

The app will typically launch on http://127.0.0.1:7860 (or another local port if 7860 is in use). You will see a message in your terminal indicating the local URL.

## Project Structure
```bash
.
├── app.py                  # Main Gradio application code
├── requirements.txt        # Python dependencies
├── README.md               # This README file
└── assets/                 # (Optional) Directory for screenshots etc.
    └── screenshot.png
```
## Technical Details
  1. Frontend/Backend Framework: Gradio
  
  2. Data Handling: Pandas for tabular data
  
  3. Plotting: Matplotlib for charts
  
  4. Styling: Custom CSS embedded within app.py for a personalized look.
  
  5. Font Integration: Google Fonts (Emilys Candy, Special Elite) are imported via CSS.

## Contact
If you have any questions or feedback, feel free to reach out:

GitHub: [MahekTrivedi44](https://github.com/MahekTrivedi44)

Hugging Face: [MahekTrivedi](https://huggingface.co/MahekTrivedi)

Email: mahektrivedi2006@gmail.com
