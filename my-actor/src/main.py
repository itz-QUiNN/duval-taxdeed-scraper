import json
import time
from apify import Actor
from playwright.async_api import async_playwright

async def scrape_duval_taxdeed():
    data_list = []
    base_url = "https://taxdeed.duvalclerk.com/"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(base_url)
        
        # --- Step 1: Select Date Options and Search ---
        await page.select_option("#SearchSaleDateFrom", index=3)
        await page.select_option("#SearchSaleDateTo", index=1)
        await page.click("#tabs-9 button")
        
        # Enter "SALE" into the Status Search Box like Selenium
        status_input = page.locator("#gs_Status")
        await status_input.click()
        await status_input.fill("")  # Clear the field first
        await status_input.type("SALE")  # Simulate typing like Selenium
        await page.wait_for_timeout(2000)  # Wait for results to refresh

        # Get total number of pages
        try:
            total_pages = int(await page.text_content("#sp_1_pager").strip())
        except:
            total_pages = 1

        # Loop through all pages
        for current_page in range(1, total_pages + 1):
            print(f"Processing page {current_page} of {total_pages}")
            
            rows = await page.locator("tr[role='row'][id]").all()
            filtered_row_ids = []

            for row in rows:
                row_id = await row.get_attribute("id")
                if row_id and row_id.isdigit():
                    status = await row.locator("td[aria-describedby='TaxDeed_Status']").text_content()
                    if status.strip() == "SALE":
                        filtered_row_ids.append(row_id)
            
            print("Filtered Row IDs with 'SALE' status:", filtered_row_ids)

            # --- Step 2: Visit Each Details Page, Extract Data ---
            for row_id in filtered_row_ids:
                details_url = f"https://taxdeed.duvalclerk.com/Home/Details?id={row_id}"
                print("Visiting details URL:", details_url)
                await page.goto(details_url)
                await page.wait_for_timeout(2000)

                detail_data = {}
                rows = await page.locator("tr:has(td b)").all()
                
                for row in rows:
                    try:
                        key = await row.locator("td:nth-child(1) b").text_content()
                        value = await row.locator("td:nth-child(2)").text_content()
                        if key.strip() in ["Property Address", "Parcel ID", "Opening Bid"]:
                            detail_data[key.strip()] = value.strip()
                    except:
                        pass
                
                # Fill missing values with 'N/A'
                for field in ["Property Address", "Parcel ID", "Opening Bid"]:
                    if field not in detail_data:
                        detail_data[field] = "N/A"

                data_list.append(detail_data)

                # page.goto(base_url)  # Optionally return to base URL
                # page.wait_for_selector("#gs_Status", timeout=60000)  # Wait for search box to appear
                # page.fill("#gs_Status", "SALE")
                # await page.wait_for_timeout(2000)  # Wait for results to refresh

            # --- Step 3: Click "Next Page" if available ---
            if current_page < total_pages:
                await page.click("#next_pager")
                await page.wait_for_timeout(3000)

        # --- Step 4: Save Data to JSON ---
        output_filename = "taxdeed_details.json"
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(data_list, f, indent=4)

        print(f"Data saved to {output_filename}")
        await browser.close()

# This function will be called by the Apify actor runner.
Actor.main(scrape_duval_taxdeed)
