import streamlit as st
import asyncio
import pandas as pd
from playwright.async_api import async_playwright

st.set_page_config(page_title="D&B Global Scraper", page_icon="📊", layout="centered")

st.title("🌐 D&B Directory Cloud Scraper")
st.markdown("Enter any Dun & Bradstreet directory link below to extract company names, key principals, and websites automatically.")

# User input for any D&B URL
target_url = st.text_input(
    "D&B Directory URL:", 
    value="https://www.dnb.com/business-directory/company-information.paper_and_paper_product_merchant_wholesalers.eg.html"
)

# Async scraping function adapted for the web app
async def run_scraper(url, status_text, progress_bar):
    async with async_playwright() as p:
        # Must be headless=True for cloud servers that don't have a physical display
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        main_page = await context.new_page()
        
        status_text.text("Navigating to target directory...")
        try:
            await main_page.goto(url, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            st.error(f"Failed to load URL: {e}")
            await browser.close()
            return []
        
        extracted_data = []
        has_next = True
        page_num = 1
        
        while has_next:
            status_text.text(f"Scanning Directory Page {page_num}...")
            try:
                await main_page.wait_for_selector("a[href*='company-profile']", timeout=15000)
            except:
                status_text.text("No more company links found or page timed out.")
                break
                
            hrefs = await main_page.eval_on_selector_all(
                "a[href*='company-profile']", 
                "elements => elements.map(e => e.href)"
            )
            company_urls = list(set(hrefs))
            
            if not company_urls:
                break
            
            total_companies = len(company_urls)
            for idx, c_url in enumerate(company_urls):
                detail_page = await context.new_page()
                try:
                    await detail_page.goto(c_url, wait_until="domcontentloaded", timeout=30000)
                    
                    # Extract Company Name
                    company_name = "N/A"
                    try:
                        h1_element = await detail_page.wait_for_selector("h1", timeout=3000)
                        company_name = await h1_element.inner_text()
                    except:
                        page_title = await detail_page.title()
                        if page_title:
                            company_name = page_title.split('- Company Profile')[0].strip()

                    # Extract Key Principal
                    key_principal = "N/A"
                    kp_locator = detail_page.locator("text='Key Principal:'")
                    if await kp_locator.count() > 0:
                        raw_kp_text = await kp_locator.locator("..").inner_text()
                        key_principal = raw_kp_text.replace("Key Principal:", "").split("See more")[0].strip()

                    # Extract Website
                    website = "N/A"
                    website_locator = detail_page.locator("a:has-text('Website'), a:has-text('www.')").first
                    if await website_locator.count() > 0:
                        website = await website_locator.get_attribute("href") or await website_locator.inner_text()

                    extracted_data.append({
                        "Company Name": company_name.strip() if company_name else "N/A",
                        "Key Principal": key_principal,
                        "Website": website,
                        "Profile URL": c_url
                    })
                    
                    # Update progress bar dynamically
                    progress_bar.progress(min((idx + 1) / total_companies, 1.0), text=f"Scraping Page {page_num}: {company_name}")
                except Exception:
                    pass
                finally:
                    await detail_page.close()
                    await asyncio.sleep(1)

            # Pagination handling
            try:
                next_btn = main_page.locator("a[aria-label='Next'], a.pagination-next, button:has-text('Next')").first
                if await next_btn.count() > 0:
                    class_name = await next_btn.get_attribute("class") or ""
                    aria_disabled = await next_btn.get_attribute("aria-disabled") == "true"
                    if "disabled" in class_name.lower() or aria_disabled:
                        has_next = False
                    else:
                        next_url = await next_btn.get_attribute("href")
                        if next_url and next_url not in ["#", "javascript:void(0)"]:
                            if not next_url.startswith("http"):
                                next_url = "https://www.dnb.com" + next_url if next_url.startswith("/") else "https://www.dnb.com/" + next_url
                            await main_page.goto(next_url, wait_until="domcontentloaded", timeout=60000)
                        else:
                            await next_btn.click(force=True)
                            await main_page.wait_for_timeout(3000)
                        page_num += 1
                else:
                    has_next = False
            except:
                has_next = False

        await browser.close()
        return extracted_data

# Trigger Button in UI
if st.button("🚀 Start Scraping Directory", type="primary"):
    if not target_url:
        st.warning("Please enter a valid URL first.")
    else:
        status_container = st.empty()
        progress_bar = st.progress(0, text="Initializing browser...")
        
        # Run async loop inside Streamlit
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            data = loop.run_until_complete(run_scraper(target_url, status_container, progress_bar))
            
            if data:
                df = pd.DataFrame(data)
                status_container.success(f"Successfully extracted {len(df)} companies!")
                progress_bar.empty()
                
                # Display table preview
                st.dataframe(df)
                
                # Download CSV button
                csv_data = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Results as CSV",
                    data=csv_data,
                    file_name="dnb_extracted_directory.csv",
                    mime="text/csv",
                )
            else:
                status_container.error("No data was extracted. Check the URL or try again.")
        except Exception as ex:
            st.error(f"An error occurred: {ex}")