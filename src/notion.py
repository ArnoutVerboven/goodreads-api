import requests


class NotionAPI:
    def __init__(self, api_token: str):
        self.API_TOKEN = api_token
        self.url = "https://api.notion.com/v1"   
    def get_headers(self):
        return {
            "Authorization": f"Bearer {self.API_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
    def request(self, method : str, url : str, data : dict = None) -> dict:  # method: "GET" | "POST" | "PATCH" | "DELETE"
        headers = self.get_headers()
        if data:
            response = requests.request(method, url, headers=headers, json=data)
        else:
            response = requests.request(method, url, headers=headers)
            
        if response.status_code != 200:
            raise RuntimeError(f"Notion API request failed with status code {response.status_code}.")
        
        return response.json()    
    
    
class NotionDB:
    def __init__(self, api : NotionAPI, id : str):
        self.api = api
        self.id = id
        self.url = f"{api.url}/databases/{self.id}"
        
    def query(self):
        """
        Query the Notion database and return the data as a dictionary.
        Handles pagination to fetch all results.
        """
        has_more = True
        next_cursor = None
        all_results = []

        while has_more:
            payload = {}
            if next_cursor:
                payload["start_cursor"] = next_cursor

            data = self.api.request("POST", f"{self.url}/query", data=payload)

            all_results.extend(data.get("results", []))

            has_more = data.get("has_more", False)
            next_cursor = data.get("next_cursor")
        return all_results
    
    def create_page(self, properties : dict):
        """
        Create a new page in the Notion database.
        properties: A dictionary containing the properties of the new page.
        """
        data = {
            "parent": {"database_id": self.id},
            "properties": properties
        }
        return self.api.request("POST", f"{self.api.url}/pages", data=data)
    
    def update_page(self, page_id : str, properties : dict):
        """
        Update an existing page in the Notion database.
        page_id: The ID of the page to update.
        properties: A dictionary containing the properties to update.
        """
        data = {
            "properties": properties
        }
        return self.api.request("PATCH", f"{self.api.url}/pages/{page_id}", data=data)
    
    def delete_page(self, page_id : str):
        """
        Delete a page from the Notion database.
        page_id: The ID of the page to delete.
        """
        return self.api.request("DELETE", f"{self.api.url}/pages/{page_id}")