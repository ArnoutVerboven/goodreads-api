# TODO: Logs on errors

import os

from src.goodreads import extract_books_progress
from src.notion import NotionAPI, NotionDB


class ReadingTracker:
    def __init__(self, db: NotionDB, db_event: NotionDB):
        self.db = db
        self.db_event = db_event
    
    def get_books(self):
        """
        Parse the Notion database results and extract book titles and reading progress.
        Returns a list of dictionaries containing book info.
        {
            "Book Title" (str): <title>,
            "Current Page" (int): <X>,
            "Total Pages" (int): <Y>,
            "page_id" (str): <id>,
        }
        """
        all_results = self.db.query()

        books = []
        for result in all_results:
            properties = result.get("properties", {})

            books.append({
                "Book Title": properties.get("Book Title", {}).get("title", [{}])[0].get("plain_text", ""),
                "Current Page": properties.get("Current Page", {}).get("number", 0),
                "Total Pages": properties.get("Total Pages", {}).get("number", 0),
                "page_id": result["id"]
            })

        return books

    def create_event_db(self, book_title: str, pages_read: int, book_finished: bool = False):
        """
        Add the reading progress event to the Notion database.
        `event` should be a dictionary with:
        - "Book Title" (str): The title of the book.
        - "Pages Read" (int): The number of pages read.
        - "Book Finished" (bool): Whether the book is finished.
        """
        print(book_title, pages_read, book_finished)
        self.db_event.create_page({
            "Book Title": {"title": [{"text": {"content": book_title}}]},
            "Pages Read": {"number": pages_read},
            "Book Finished": {"checkbox": book_finished}
        })
            
    def create_book_db(self, book: dict):
        """
        Add the book to the Notion database.
        `book` should be a dictionary with:
        - "Book Title" (str): The title of the book.
        - "Current Page" (int): The current page number.
        - "Total Pages" (int): The total number of pages.
        """
        self.db.create_page({
            "Book Title": {"title": [{"text": {"content": book["Book Title"]}}]},
            "Current Page": {"number": book["Current Page"]},
            "Total Pages": {"number": book["Total Pages"]}
        })
        
    def update_book_db(self, book: dict):
        """
        Update the book in the Notion database.
        `book` should be a dictionary with:
        - "Book Title" (str): The title of the book.
        - "Current Page" (int): The current page number.
        - "Total Pages" (int): The total number of pages.
        """
        self.db.update_page(book["page_id"], {
            "Current Page": {"number": book["Current Page"]},
            "Total Pages": {"number": book["Total Pages"]}
        })
        
    def delete_book_db(self, book: dict):
        """
        Delete the book from the Notion database.
        `book` should be a dictionary with:
        - "page_id" (str): The ID of the book page.
        """
        self.db.delete_page(book["page_id"])
        
    def update(self, updated_books: list[dict]):
        """
        Update the Notion database with the latest reading progress.
        Each item in `updated_books` should be a dictionary with:
        - "Book Title" (str): The title of the book.
        - "Current Page" (int): The current page number.
        - "Total Pages" (int): The total number of pages.
        """
        current_books = self.get_books()  # Lookup current books in the database

        for book in updated_books:
            if "Current Page" not in book or "Total Pages" not in book:
                continue

            # Check if the book already exists in the database
            existing_book = next((b for b in current_books if b["Book Title"] == book["Book Title"]), None)

            if not existing_book:
                # Create a new book in the database
                self.create_book_db(book)
                self.create_event_db(book["Book Title"], book["Current Page"])  # Pages read is the current page
            else:
                pages_read = book["Current Page"] - existing_book["Current Page"]
                if pages_read > 0:
                    # Update the existing book in the database
                    self.update_book_db({
                        "page_id": existing_book["page_id"],
                        "Current Page": book["Current Page"],
                        "Total Pages": book["Total Pages"]
                    })
                    self.create_event_db(book["Book Title"], pages_read)

        # Handle books in the database that are not in the updated_books list
        for book in current_books:
            if book["Book Title"] not in {b["Book Title"] for b in updated_books}:
                # Book is finished
                pages_read = book["Total Pages"] - book["Current Page"]
                self.delete_book_db(book)
                self.create_event_db(book["Book Title"], pages_read, book_finished=True)




if __name__ == "__main__":
    NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
    NOTION_DB_ID = os.environ.get("NOTION_DB_ID")
    NOTION_DB_EVENT_ID = os.environ.get("NOTION_DB_EVENT_ID")
    
    GOODREADS_ID = os.environ.get("GOODREADS_ID")

    notion_api = NotionAPI(NOTION_API_KEY)
    db = NotionDB(notion_api, NOTION_DB_ID)
    db_event = NotionDB(notion_api, NOTION_DB_EVENT_ID)

    reading_tracker = ReadingTracker(db, db_event)
    print(reading_tracker)
    
    goodreads_books = extract_books_progress()
    print(goodreads_books)
    
    reading_tracker.update(goodreads_books)
    print("Reading tracker updated successfully.")
    