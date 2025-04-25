import streamlit as st
import os
import zipfile
import tempfile
from PIL import Image
import io

def display_images(image_paths):
    st.markdown("### 🖼️ Preview Collected Ads")
    
    # Check if image_paths is None or empty
    if not image_paths:
        st.warning("No images were collected. Please try again.")
        return []
    
    # Ensure unique paths (in case the scraper captured duplicates)
    unique_paths = []
    seen_paths = set()
    
    # Filter valid image files from the results
    valid_images = []
    for path in image_paths:
        # Skip duplicates
        if path in seen_paths:
            continue
        
        seen_paths.add(path)
        
        # Check if this is a valid image file
        try:
            # Try to open the file as an image
            with Image.open(path) as img:
                # If it opens successfully, it's a valid image
                valid_images.append(path)
        except Exception as e:
            # If it's not an image, check if it's a text file with error info
            try:
                if path.endswith(".txt"):
                    with open(path, 'r') as f:
                        error_text = f.read()
                    st.error(f"Scraping encountered an error: {error_text}")
                else:
                    st.warning(f"Found invalid file that's not an image or readable text: {os.path.basename(path)}")
            except:
                st.warning(f"Found invalid file: {os.path.basename(path)}")
    
    # If we found no valid images
    if not valid_images:
        st.error("No valid images were found. The scraper encountered errors.")
        return []
        
    # If there were duplicates, let the user know
    if len(valid_images) < len(image_paths):
        st.info(f"Filtered out {len(image_paths) - len(valid_images)} invalid or duplicate images.")
    
    # Determine the number of columns in the grid
    num_columns = 5  # Increased to 5 columns for an even more compact grid
    
    # Calculate how many rows we need
    num_images = len(valid_images)
    
    # Process images in groups of size num_columns
    for i in range(0, num_images, num_columns):
        # Create columns for this row with minimal spacing
        columns = st.columns(num_columns)
        
        # Add images to this row
        for col_idx in range(num_columns):
            img_idx = i + col_idx
            
            # Check if we still have images to display
            if img_idx < num_images:
                img_path = valid_images[img_idx]
                with columns[col_idx]:
                    # Make UI more compact by using smaller components
                    # Generate a unique key for each checkbox based on index and path
                    checkbox_key = f"checkbox_{img_idx}_{os.path.basename(img_path)}"
                    
                    # Add checkbox with better label for accessibility
                    selected = st.checkbox("Keep", value=True, key=checkbox_key, 
                                         help="Select to keep this ad", 
                                         label_visibility="collapsed")
                    
                    # Display the image with compact sizing
                    try:
                        st.image(img_path, width=120)  # Smaller width for tighter grid
                    except Exception as e:
                        st.error(f"Error displaying image: {os.path.basename(img_path)}")
                    
                    # Store the selection state
                    if "selected_images" not in st.session_state:
                        st.session_state.selected_images = {}
                    st.session_state.selected_images[img_path] = selected
    
    # Collect the selected images
    if "selected_images" in st.session_state:
        selected_images = [path for path, keep in st.session_state.selected_images.items() if keep]
        return selected_images
    return []


def zip_images(image_paths):
    # Make sure we have valid image paths
    valid_paths = []
    for path in image_paths:
        try:
            # Check if the file exists and is an image
            if os.path.exists(path):
                # Try to open as image to verify
                Image.open(path).verify()
                valid_paths.append(path)
        except:
            # Skip invalid files
            continue
    
    if not valid_paths:
        st.error("No valid images to zip")
        return None
    
    temp_zip = os.path.join(tempfile.gettempdir(), "ads_selected.zip")
    with zipfile.ZipFile(temp_zip, 'w') as zipf:
        for path in valid_paths:
            arcname = os.path.basename(path)
            zipf.write(path, arcname=arcname)
    return temp_zip