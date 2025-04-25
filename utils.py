import streamlit as st
import os
import zipfile
import tempfile
from PIL import Image

def display_images(image_paths):
    st.markdown("### 🖼️ Preview Collected Ads")
    
    # Ensure unique paths (in case the scraper captured duplicates)
    unique_paths = []
    seen_paths = set()
    for path in image_paths:
        if path not in seen_paths:
            unique_paths.append(path)
            seen_paths.add(path)
    
    # If there were duplicates, let the user know
    if len(unique_paths) < len(image_paths):
        st.info(f"Removed {len(image_paths) - len(unique_paths)} duplicate images.")
    
    # Determine the number of columns in the grid
    num_columns = 5  # Increased to 5 columns for an even more compact grid
    
    # Calculate how many rows we need
    num_images = len(unique_paths)
    
    # Process images in groups of size num_columns
    for i in range(0, num_images, num_columns):
        # Create columns for this row with minimal spacing
        columns = st.columns(num_columns)
        
        # Add images to this row
        for col_idx in range(num_columns):
            img_idx = i + col_idx
            
            # Check if we still have images to display
            if img_idx < num_images:
                img_path = unique_paths[img_idx]
                with columns[col_idx]:
                    # Make UI more compact by using smaller components
                    # Generate a unique key for each checkbox based on index and path
                    checkbox_key = f"checkbox_{img_idx}_{os.path.basename(img_path)}"
                    
                    # Add checkbox with better label for accessibility
                    selected = st.checkbox("Keep", value=True, key=checkbox_key, 
                                         help="Select to keep this ad", 
                                         label_visibility="collapsed")
                    
                    # Display the image with compact sizing
                    st.image(img_path, width=120)  # Smaller width for tighter grid
                    
                    # Store the selection state
                    if "selected_images" not in st.session_state:
                        st.session_state.selected_images = {}
                    st.session_state.selected_images[img_path] = selected
    
    # Collect the selected images
    if "selected_images" in st.session_state:
        selected_images = [path for path, keep in st.session_state.selected_images.items() if keep]
        return selected_images
    return []
    
    # Collect the selected images
    if "selected_images" in st.session_state:
        selected_images = [path for path, keep in st.session_state.selected_images.items() if keep]
        return selected_images
    return []


def zip_images(image_paths):
    temp_zip = os.path.join(tempfile.gettempdir(), "ads_selected.zip")
    with zipfile.ZipFile(temp_zip, 'w') as zipf:
        for path in image_paths:
            arcname = os.path.basename(path)
            zipf.write(path, arcname=arcname)
    return temp_zip