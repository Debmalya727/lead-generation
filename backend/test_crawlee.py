import asyncio
from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext

async def test_scraper():
    crawler = PlaywrightCrawler(
        max_requests_per_crawl=3,
        headless=True,
        browser_launch_options={"args": ["--no-sandbox", "--disable-setuid-sandbox"]}
    )
    
    scraped_data = []

    @crawler.router.default_handler
    async def default_handler(context: PlaywrightCrawlingContext) -> None:
        print("Handling default search page...")
        try:
            await context.page.wait_for_selector('div[role="feed"]', timeout=20000)
            print("Found feed")
        except:
            print("No feed found")
            return
            
        # Wait a bit
        await context.page.wait_for_timeout(2000)
        
        # Scroll down to load results
        for _ in range(3):
            await context.page.mouse.wheel(0, 1000)
            await context.page.wait_for_timeout(1000)
        
        # Google Maps search results
        places = await context.page.locator('a[href*="/maps/place/"]').all()
        urls_to_enqueue = []
        for place in places:
            url = await place.get_attribute("href")
            if url:
                urls_to_enqueue.append(url)
                
        print(f"Found {len(urls_to_enqueue)} places")
        await context.enqueue_links(urls=urls_to_enqueue, label="detail")

    @crawler.router.handler("detail")
    async def detail_handler(context: PlaywrightCrawlingContext) -> None:
        try:
            await context.page.wait_for_selector('h1', timeout=10000)
            name = await context.page.locator('h1').inner_text()
            
            website = ""
            web_loc = context.page.locator('a[data-tooltip="Open website"]')
            if await web_loc.count() > 0:
                website = await web_loc.first.get_attribute('href')
                
            phone = ""
            phone_loc = context.page.locator('button[data-tooltip="Copy phone number"]')
            if await phone_loc.count() > 0:
                phone = await phone_loc.first.inner_text()
                
            scraped_data.append({
                "name": name,
                "website": website,
                "phone": phone
            })
            print(f"Scraped: {name} - {website} - {phone}")
        except Exception as e:
            print(f"Failed detail: {e}")

    await crawler.run(['https://www.google.com/maps/search/plumbers+in+new+york'])
    print(scraped_data)

if __name__ == '__main__':
    asyncio.run(test_scraper())
