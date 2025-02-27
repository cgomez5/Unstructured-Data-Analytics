# app.py

import asyncio
import nest_asyncio
import smtplib
import pandas as pd
import streamlit as st
from email.message import EmailMessage
from playwright.async_api import async_playwright
from datetime import datetime
import pytz

# Email Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "gomezchristian925@gmail.com"
SENDER_PASSWORD = "slihulrequvfqbel"  # Replace with your actual App Password
RECIPIENT_EMAIL = "cgomez5@nd.edu"

# Function to Send Email
def send_email_with_html(html_content):
    st.write("📧 Email function was triggered!")  # Show in Streamlit UI
    print("📧 Email function was triggered!")  # Debugging in terminal

    eastern = pytz.timezone("US/Eastern")
    display_timestamp = datetime.now(eastern).strftime("%Y-%m-%d %H:%M:%S")

    msg = EmailMessage()
    msg["Subject"] = f"World Indices Report - {display_timestamp} (Eastern)"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECIPIENT_EMAIL
    msg.set_content(f"World Indices report generated at {display_timestamp}. Check the Streamlit app for details.")
    msg.add_alternative(html_content, subtype="html")

    try:
        st.write("🔄 Connecting to SMTP server...")
        print("🔄 Connecting to SMTP server...")  # Debugging in terminal

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            st.write("🔐 Securing connection with TLS...")
            print("🔐 Securing connection with TLS...")  # Debugging in terminal
            server.starttls()

            st.write("🔑 Logging into email...")
            print("🔑 Logging into email...")  # Debugging in terminal
            server.login(SENDER_EMAIL, SENDER_PASSWORD)

            st.write("📩 Sending email now...")
            print("📩 Sending email now...")  # Debugging in terminal
            server.send_message(msg)

        st.success("✅ Email sent successfully!")
        print("✅ Email sent successfully!")  # Debugging in terminal

    except Exception as e:
        st.error(f"❌ Failed to send email: {e}")  # Show error in UI
        print(f"❌ Email Error: {e}")  # Log error in terminal

nest_asyncio.apply()

# Scrape the Yahoo website
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
            row_data = [ (await cells.nth(j).inner_text()).strip() for j in range(cell_count) ]
            data.append(row_data)
        
        await browser.close()
    return data

# Generate Yahoo Finance links
def generate_yahoo_link(symbol: str) -> str:
    encoded_symbol = symbol.replace('^', '%5E')
    return f"https://finance.yahoo.com/quote/{encoded_symbol}/"

# Streamlit UI
st.title("World Indices Report")
st.write("This app scrapes Yahoo Finance to get world indices and displays key data.")

if st.button("Scrape Data", key="scrape_data"):
    st.write("Fetching data... please wait.")
    
    # Run the scraper
    raw_data = asyncio.run(scrape_yahoo_world_indices())

    # Convert to DataFrame
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

    # Display data in Streamlit
    st.subheader("USA Major Indices")
    st.dataframe(df_tickers)

    st.subheader("Indices on the Move")
    st.dataframe(df_change)

# Send email button - Fixed duplicate issue
if st.button("Send Email Report", key="send_email_btn"):
    st.write("🟢 Button Clicked - Calling Email Function")
    print("🟢 Button Clicked - Calling Email Function")
    send_email_with_html("<h1>Test Email from Streamlit</h1>")