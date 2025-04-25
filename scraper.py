import os
import time
import tempfile
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def collect_ads(url, platform="Google Ads", screenshot_count=5):
    """
    Collect ad screenshots from different ad transparency platforms
    
    Args:
        url: URL of the ad transparency platform with search query
        platform: "Google Ads" or "Meta Ads"
        screenshot_count: Maximum number of ads to capture
        
    Returns:
        List of paths to the captured screenshots
    """
    if platform == "Google Ads":
        return collect_google_ads(url, screenshot_count)
    elif platform == "Meta Ads":
        return collect_meta_ads(url, screenshot_count)
    else:
        raise ValueError(f"Unsupported platform: {platform}")


def collect_google_ads(url, screenshot_count=5):
    """Collect ad screenshots from Google Ads Transparency Center"""
    
    # Setup driver
    options = uc.ChromeOptions()
    options.headless = True
    options.add_argument("--window-size=1920,1080")  # Set a consistent window size
    driver = uc.Chrome(options=options)
    
    try:
        driver.get(url)
        
        # Wait for the ads to load with explicit wait instead of sleep
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'priority-creative-grid creative-preview')))
        
        # Scroll to load more ads
        last_height = driver.execute_script("return document.body.scrollHeight")
        for _ in range(3):  # Limit scrolling to prevent infinite loops
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        # Find all creative-preview elements inside priority-creative-grid
        ad_elements = driver.find_elements(By.CSS_SELECTOR, 'priority-creative-grid creative-preview')
        print(f"Found {len(ad_elements)} Google ad elements")

        # Limit the number of screenshots to `screenshot_count`
        ad_elements = ad_elements[:screenshot_count]
        
        image_paths = []
        for i, ad in enumerate(ad_elements):
            try:
                # Scroll element into view before taking screenshot
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", ad)
                time.sleep(1)  # Wait for scrolling to complete
                
                # Define the screenshot file path
                screenshot_path = os.path.join(tempfile.gettempdir(), f"google_ad_{i}.png")
                
                # Take screenshot of only this specific element
                ad.screenshot(screenshot_path)
                image_paths.append(screenshot_path)
                print(f"Successfully captured Google ad {i}")
                
            except Exception as e:
                print(f"Failed to capture Google ad {i}: {e}")
        
        return image_paths
    except Exception as e:
        print(f"Error during Google scraping: {e}")
        return []
    finally:
        # Always quit the driver, even in case of error
        driver.quit()


def collect_meta_ads(url, screenshot_count=5):
    """Collect ad screenshots from Meta Ads Library"""
    
    # Setup driver with more robust configuration
    options = uc.ChromeOptions()
    options.headless = True  # Use headless for Streamlit compatibility
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    
    # Add arguments specifically to help with headless mode on Facebook
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-dev-shm-usage')
    
    # Add user agent to appear more like a regular browser
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = uc.Chrome(options=options)
    
    try:
        # Execute JavaScript to avoid detection
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Navigate to the URL
        print(f"Opening Meta Ads URL: {url}")
        driver.get(url)
        
        # Give Facebook time to load initial content
        time.sleep(7)  # Increased wait time for headless mode
        
        # Check if we need to handle a cookie consent dialog
        try:
            cookie_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Allow') or contains(text(), 'Cookies')]")
            if cookie_buttons:
                print("Attempting to click cookie consent button...")
                for button in cookie_buttons:
                    try:
                        button.click()
                        time.sleep(1)
                        print("Clicked cookie consent button")
                        break
                    except:
                        pass
        except Exception as e:
            print(f"No cookie dialog found or error handling it: {e}")
        
        # Wait for the page to load and stabilize
        print("Waiting for page to load...")
        time.sleep(5)  # Increased wait time
        
        # First try with the most specific selector
        ad_selector = 'div[role="article"]'
        backup_selector = 'div._7jyg'  # Backup selector based on your example HTML
        third_selector = 'div._8nsi'   # Another potential selector from your HTML
        
        # Try to find ads with the primary selector
        ads_found = False
        try:
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ad_selector)))
            ads_found = True
            print(f"Found ads with primary selector: {ad_selector}")
        except:
            print(f"Could not find ads with primary selector, trying backup selector: {backup_selector}")
            try:
                wait = WebDriverWait(driver, 10)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, backup_selector)))
                ad_selector = backup_selector
                ads_found = True
                print(f"Found ads with backup selector: {backup_selector}")
            except:
                print(f"Could not find ads with backup selector, trying third selector: {third_selector}")
                try:
                    wait = WebDriverWait(driver, 10)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, third_selector)))
                    ad_selector = third_selector
                    ads_found = True
                    print(f"Found ads with third selector: {third_selector}")
                except:
                    print("Could not find ads with any selector")
        
        # If we can't find ads, look for specific elements in the HTML source
        if not ads_found:
            page_source = driver.page_source
            
            # Look for ad container patterns in the HTML
            if '"role":"article"' in page_source or '_7jyg' in page_source or '_8nsi' in page_source:
                print("Found ad patterns in HTML source but couldn't locate elements. Taking sequential screenshots...")
                
                # Take sequence of screenshots as we scroll down
                image_paths = []
                for i in range(min(screenshot_count, 5)):  # Limit to 5 full-page screenshots
                    # Scroll down progressively
                    driver.execute_script(f"window.scrollBy(0, {800 * (i+1)});")
                    time.sleep(3)  # Wait for content to load
                    
                    # Take screenshot
                    screenshot_path = os.path.join(tempfile.gettempdir(), f"meta_page_{i}.png")
                    driver.save_screenshot(screenshot_path)
                    image_paths.append(screenshot_path)
                    print(f"Captured full-page screenshot {i}")
                
                return image_paths
            
            # As last resort, take a single full page screenshot
            print("Taking full page screenshot as fallback...")
            full_screen_path = os.path.join(tempfile.gettempdir(), "meta_full_page.png")
            driver.save_screenshot(full_screen_path)
            return [full_screen_path]
        
        # Now proceed with capturing ads
        image_paths = []
        ads_captured = 0
        scroll_attempts = 0
        max_scroll_attempts = 20  # Increased for headless mode
        
        # Track which ads we've already processed to avoid duplicates
        processed_ads = set()
        
        # Keep scrolling and capturing until we reach the limit or run out of ads
        while ads_captured < screenshot_count and scroll_attempts < max_scroll_attempts:
            print(f"Scroll attempt {scroll_attempts + 1}/{max_scroll_attempts}")
            
            # Find all ad elements
            ad_elements = driver.find_elements(By.CSS_SELECTOR, ad_selector)
            print(f"Found {len(ad_elements)} Meta ad elements")
            
            if not ad_elements and scroll_attempts > 5:
                print("No ad elements found after multiple scrolls, taking full page screenshot")
                full_screen_path = os.path.join(tempfile.gettempdir(), "meta_full_page.png")
                driver.save_screenshot(full_screen_path)
                return [full_screen_path]
            
            # Process elements we haven't captured yet
            new_ads_in_this_scroll = 0
            for i, ad in enumerate(ad_elements):
                try:
                    # Skip already processed ads
                    # Generate a unique identifier for this ad
                    # Using a combination of text content, class names, and position
                    ad_text = ad.text[:100] if ad.text else ""
                    ad_class = ad.get_attribute("class") or ""
                    ad_position = f"{ad.location['x']}-{ad.location['y']}"
                    ad_size = f"{ad.size['width']}-{ad.size['height']}"
                    ad_id = f"{ad_text}_{ad_class}_{ad_position}_{ad_size}"
                    ad_hash = hash(ad_id)
                    
                    if ad_hash in processed_ads:
                        continue
                    
                    # Mark this ad as processed
                    processed_ads.add(ad_hash)
                    
                    # Scroll to the element
                    print(f"Scrolling to new ad {ads_captured}")
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", ad)
                    time.sleep(2)  # Give more time for scrolling and rendering
                    
                    # Define the screenshot file path
                    screenshot_path = os.path.join(tempfile.gettempdir(), f"meta_ad_{ads_captured}.png")
                    
                    # Take screenshot of this specific ad element
                    try:
                        ad.screenshot(screenshot_path)
                        image_paths.append(screenshot_path)
                        print(f"Successfully captured Meta ad {ads_captured}")
                        ads_captured += 1
                        new_ads_in_this_scroll += 1
                        
                        if ads_captured >= screenshot_count:
                            break
                            
                    except Exception as e:
                        print(f"Failed to screenshot ad: {e}")
                        # Try an alternative approach
                        try:
                            print("Trying alternative screenshot method...")
                            # Get location and size
                            location = ad.location
                            size = ad.size
                            
                            # Take full screenshot
                            temp_path = os.path.join(tempfile.gettempdir(), f"meta_temp.png")
                            driver.save_screenshot(temp_path)
                            
                            # Crop to ad dimensions
                            from PIL import Image
                            img = Image.open(temp_path)
                            left = location['x']
                            top = location['y']
                            right = left + size['width']
                            bottom = top + size['height']
                            
                            # Ensure dimensions are within the image
                            img_width, img_height = img.size
                            left = max(0, left)
                            top = max(0, top)
                            right = min(img_width, right)
                            bottom = min(img_height, bottom)
                            
                            # Crop and save
                            if left < right and top < bottom:
                                cropped = img.crop((left, top, right, bottom))
                                cropped.save(screenshot_path)
                                image_paths.append(screenshot_path)
                                print(f"Successfully captured Meta ad {ads_captured} with alternative method")
                                ads_captured += 1
                                new_ads_in_this_scroll += 1
                                
                                if ads_captured >= screenshot_count:
                                    break
                            else:
                                print(f"Invalid crop dimensions: {left}, {top}, {right}, {bottom}")
                        except Exception as e2:
                            print(f"Alternative screenshot method also failed: {e2}")
                            
                except Exception as e:
                    print(f"Error processing Meta ad: {e}")
            
            # If we found new ads in this scroll, continue; otherwise, scroll more
            if new_ads_in_this_scroll == 0:
                print("No new ads found in this scroll, scrolling down more...")
                # Scroll a bit further each time
                scroll_distance = 800 + (scroll_attempts * 200)
                driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
                time.sleep(3)  # Wait longer for content to load
            else:
                print(f"Found {new_ads_in_this_scroll} new ads in this scroll")
                
            scroll_attempts += 1
            
            # Every 5 attempts, take a full page screenshot as backup
            if scroll_attempts % 5 == 0 and ads_captured < screenshot_count:
                backup_path = os.path.join(tempfile.gettempdir(), f"meta_backup_{scroll_attempts}.png")
                driver.save_screenshot(backup_path)
                image_paths.append(backup_path)
                print(f"Added backup screenshot at scroll attempt {scroll_attempts}")
        
        if not image_paths:
            print("No ads captured, taking full page screenshot as fallback")
            full_screen_path = os.path.join(tempfile.gettempdir(), "meta_full_page.png")
            driver.save_screenshot(full_screen_path)
            return [full_screen_path]
            
        return image_paths
    except Exception as e:
        print(f"Error during Meta scraping: {e}")
        try:
            # Take a full page screenshot as fallback
            full_screen_path = os.path.join(tempfile.gettempdir(), "meta_error_page.png")
            driver.save_screenshot(full_screen_path)
            return [full_screen_path]
        except:
            return []
    finally:
        # Always quit the driver, even in case of error
        try:
            driver.quit()
        except:
            pass