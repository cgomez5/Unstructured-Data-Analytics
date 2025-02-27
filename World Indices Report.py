import asyncio
import nest_asyncio
import smtplib
import pandas as pd
import streamlit as st
from email.message import EmailMessage
from playwright.async_api import async_playwright
from datetime import datetime
import pytz

nest_asyncio.apply()

# SMTP Email Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def send_email_with_html(sender_email, sender_password, recipient_email, html_content):
    st.write("📧 Email function was triggered!")
    print("📧 Email function was triggered!")

    eastern = pytz.timezone("US/Eastern")
    display_timestamp = datetime.now(eastern).strftime("%Y-%m-%d %H:%M:%S")

    msg = EmailMessage()
    msg["Subject"] = f"World Indices Report - {display_timestamp} (Eastern)"
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg.set_content("This is an automated world indices report. See below for details.")
    msg.add_alternative(html_content, subtype="html")

    try:
        st.write("🔄 Connecting to SMTP server...")
        print("🔄 Connecting to SMTP server...")

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            st.write("🔐 Securing connection with TLS...")
            print("🔐 Securing connection with TLS...")
            server.starttls()

            st.write("🔑 Logging into email...")
            print("🔑 Logging into email...")
            server.login(sender_email, sender_password)

            st.write("📩 Sending email now...")
            print("📩 Sending email now...")
            server.send_message(msg)

        st.success("✅ Email sent successfully with embedded HTML!")
        print("✅ Email sent successfully with embedded HTML!")

    except Exception as e:
        st.error(f"❌ Failed to send email: {e}")
        print(f"❌ Email Error: {e}")

# Asynchronous function to scrape Yahoo Finance for world indices
async def scrape_yahoo_world_indices():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto("https://finance.yahoo.com/markets/world-indices/")
        await page.wait_for_load_state("domcontentloaded", timeout=60000)
        await asyncio.sleep(3)

        table = page.locator("div.tableContainer.yf-j24h8w table[data-testid='table-container']")
        await table.wait_for(state="visible", timeout=30000)
        rows = table.locator("tbody tr")
        row_count = await rows.count()

        data = []
        for i in range(row_count):
            row = rows.nth(i)
            cells = row.locator("td")
            cell_count = await cells.count()
            row_data = [(await cells.nth(j).inner_text()).strip() for j in range(cell_count)]
            data.append(row_data)

        await browser.close()
    return data

# Helper function to generate a Yahoo Finance link for a given symbol
def generate_yahoo_link(symbol: str) -> str:
    encoded_symbol = symbol.replace('^', '%5E')
    return f"https://finance.yahoo.com/quote/{encoded_symbol}/"

# ------------------ Streamlit App ------------------

st.title("World Indices Report")
st.write("This app scrapes Yahoo Finance to get world indices and displays key data.")

# --- Prompt the user for email credentials ---
st.subheader("Email Configuration")
sender_email = st.text_input("Enter the **sender** email address:", "")
sender_password = st.text_input("Enter the **sender** email password:", type="password")
recipient_email = st.text_input("Enter the **recipient** email address:", "")

# --- Button to scrape data ---
if st.button("Scrape Data", key="scrape_data"):
    st.write("Fetching data... please wait.")

    # Run the scraper
    raw_data = asyncio.run(scrape_yahoo_world_indices())

    # Convert the scraped data into a DataFrame
    columns = ["Symbol", "Name", "Unused", "Price", "Change", "Change %", "Volume", "Day Range", "52 Wk Range"]
    df_all = pd.DataFrame(raw_data, columns=columns)
    df_all = df_all.drop(columns=["Unused", "Day Range", "52 Wk Range", "Volume"], errors="ignore")

    # Table 1 - USA Major Indices
    df_tickers = df_all[df_all["Symbol"].isin(["^GSPC", "^DJI", "^IXIC"])].copy()
    df_tickers["YahooLink"] = df_tickers["Symbol"].apply(generate_yahoo_link)

    # Table 2 - Indices on the Move
    temp = df_all.copy()
    temp["Change % numeric"] = temp["Change %"].str.rstrip("%").astype(float)
    df_change = temp[(temp["Change % numeric"] > 0.75) | (temp["Change % numeric"] < -1.0)].copy()
    df_change = df_change.sort_values("Change % numeric", ascending=False)
    df_change = df_change.drop(columns=["Change % numeric"])
    df_change["YahooLink"] = df_change["Symbol"].apply(generate_yahoo_link)

    # Generate timestamp and HTML content
    eastern = pytz.timezone("US/Eastern")
    display_timestamp = datetime.now(eastern).strftime("%Y-%m-%d %H:%M:%S")

    html_output = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>World Indices Report - {display_timestamp}</title>
        <style>
        table {{
            border-collapse: collapse;
            width: 100%;
            margin-bottom: 20px;
        }}
        th, td {{
            border: 1px solid #dddddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        </style>
    </head>
    <body>
        <h1>World Indices Report</h1>
        <p>Date and Time (Eastern): {display_timestamp}</p>
        <h2>USA Major Indices (^GSPC, ^DJI, ^IXIC)</h2>
        {df_tickers.to_html(index=False)}
        <h2>Indices On The Move (> 0.75% or < -1.0%)</h2>
        {df_change.to_html(index=False)}
    </body>
    </html>
    """

    # Display the data in Streamlit
    st.subheader("USA Major Indices")
    st.dataframe(df_tickers)

    st.subheader("Indices on the Move")
    st.dataframe(df_change)

    # Store the HTML output in session state for later use (email)
    st.session_state["html_output"] = html_output
    st.success("Report generated successfully!")

# --- Button to send email ---
if st.button("Send Email Report", key="send_email_btn"):
    if "html_output" in st.session_state:
        if not sender_email or not sender_password or not recipient_email:
            st.error("Please fill in the sender email, password, and recipient email before sending.")
        else:
            st.write("🟢 Button Clicked - Calling Email Function")
            print("🟢 Button Clicked - Calling Email Function")
            send_email_with_html(
                sender_email,
                sender_password,
                recipient_email,
                st.session_state["html_output"]
            )
    else:
        st.error("No report generated yet. Please scrape data first.")