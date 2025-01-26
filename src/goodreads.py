import os

import requests
from bs4 import BeautifulSoup


def extract_books_progress(goodreads_id: str) -> list[dict]:
    """
    Extract book titles and reading progress from Goodreads reading HTML.
    Returns a list of dictionaries containing book info.
    {
        "Book Title" (str): <title>,
        "Current Page" (int): <X>,
        "Total Page" (int): <Y>,
    }
    """    
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }
    
    url = f"https://www.goodreads.com/user/show/{goodreads_id}"
    print(url)

    response = requests.get(url, headers=headers)
    print(response)
    
    if response.status_code != 200:
        raise RuntimeError(f"Goodreads API request failed with status code {response.status_code}.")

    soup = BeautifulSoup(response.text, "html.parser")

    h2_element = soup.find("h2", string=lambda t: t and "is Currently Reading" in t)

    if not h2_element:
        raise RuntimeError("Could not find 'is Currently Reading' section in the HTML")
    
    soup = h2_element.find_parent("div").find_parent("div")
        
    updates = soup.find_all('div', class_='Updates')
    books = []
    
    for update in updates:
        book_info = {}
        
        # Extract book title
        title_element = update.find('a', class_='bookTitle')
        if title_element:
            book_info['Book Title'] = title_element.text.strip()
        
        # Extract reading progress
        progress_link = update.find('a', onclick=lambda x: x and 'clickPageOfBook' in x)
        if progress_link:
            progress_text = progress_link.text.strip()
            if '(page' in progress_text:
                progress = progress_text.replace('(page ', '').replace(')', '')
                current_page, total_pages = progress.split(' of ')
                book_info['Current Page'] = int(current_page)
                book_info['Total Pages'] = int(total_pages)
                    
        if book_info:
            books.append(book_info)
    
    return books
