import os
import streamlit as st
from scraper import collect_ads
from utils import display_images, zip_images

st.set_page_config(page_title="Adspy Collector", layout="wide")

# Add more space before the title
st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

st.title("📸 Adspy Collector")
st.subheader("Capture ads from Google Transparency Center & Meta Ads Library")

# Add some custom CSS to make the layout more compact
st.markdown("""
    <style>
    .stImage > img {
        max-height: 200px;
        max-width: 100%;
        margin: 0;
        padding: 0;
    }
    .stCheckbox > label {
        font-size: 0.8rem;
        margin-bottom: 0;
        padding-bottom: 0;
    }
    /* Reduce padding within column containers */
    .row-widget.stHorizontal > div {
        padding-left: 5px !important;
        padding-right: 5px !important;
    }
    /* Reduce vertical spacing between elements */
    .element-container {
        margin-top: 0.2rem !important;
        margin-bottom: 0.2rem !important;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Step 1: Select platform
platform = st.radio("Select Platform", ["Google Ads Transparency", "Meta Ads Library"], horizontal=True)

# Step 2: Input search terms
if platform == "Google Ads Transparency":
    st.write("### Google Ads Transparency Center")
    domain = st.text_input("Enter the domain (e.g., nike.com)", "")
    
    # Set Region and Screenshot Count
    col1, col2 = st.columns(2)
    with col1:
        region = st.selectbox("Region", ["AR", "US", "UK", "CA", "AU", "DE", "FR", "ES", "IT", "JP"], index=0)
    with col2:
        screenshot_count = st.slider("Number of ads to collect", min_value=1, max_value=20, value=5)
    
    # Construct the Google Transparency Center URL
    if domain:
        url = f"https://adstransparency.google.com/?region={region}&domain={domain}"
        st.write(f"Scraping ads from: {url}")
    else:
        url = ""
        
else:  # Meta Ads Library
    st.write("### Meta Ads Library")
    keyword = st.text_input("Enter search keyword (e.g., nike)", "")
    
    # Set Country and Screenshot Count
    col1, col2 = st.columns(2)
    with col1:
        country = st.selectbox("Country", ["AR", "US", "GB", "CA", "AU", "DE", "FR", "ES", "IT", "JP"], index=0)
        # Map for country codes used by Facebook
        country_map = {
            "GB": "UK",  # Facebook uses UK instead of GB
        }
        fb_country = country_map.get(country, country)
    with col2:
        screenshot_count = st.slider("Number of ads to collect", min_value=1, max_value=20, value=5)
    
    # Construct the Meta Ads Library URL
    if keyword:
        url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country={fb_country}&is_targeted_country=false&media_type=all&q={keyword}&search_type=keyword_unordered"
        st.write(f"Scraping ads from: {url}")
    else:
        url = ""

# Step 3: Collect Ads
if st.button("🚀 Collect Ads"):
    if not url:
        if platform == "Google Ads Transparency":
            st.warning("Please enter a valid domain.")
        else:
            st.warning("Please enter a valid keyword.")
    else:
        with st.spinner(f"Collecting ads from {platform}..."):
            try:
                platform_param = "Meta Ads" if platform == "Meta Ads Library" else "Google Ads"
                images = collect_ads(url, platform=platform_param, screenshot_count=screenshot_count)
                if not images:
                    st.error("No ads found or something went wrong.")
                else:
                    st.session_state["ad_images"] = images
                    st.success(f"Captured {len(images)} ads!")
            except Exception as e:
                st.error(f"An error occurred: {e}")

# Step 4: Preview + Select
if "ad_images" in st.session_state:
    selected_images = display_images(st.session_state["ad_images"])

    # Step 5: Download ZIP
    if selected_images:
        zip_path = zip_images(selected_images)
        with open(zip_path, "rb") as f:
            st.download_button("📦 Download Selected Ads as ZIP", f, file_name="ads_selected.zip")
    else:
        st.warning("No images selected to download.")