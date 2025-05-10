from locust import HttpUser, task, between

class ExampleUser(HttpUser):
    # Wait between 1 and 5 seconds between tasks
    wait_time = between(1, 5)
    
    # Base URL - change this to your application's URL
    host = "https://example.com"
    
    @task
    def index_page(self):
        # This simulates a user accessing the index page
        self.client.get("/")
        
    @task(3)
    def view_item(self):
        # This task has a higher weight (3x more common than other tasks)
        # Simulates a user viewing an item page
        item_id = 1
        self.client.get(f"/item/{item_id}", name="/item/[id]")
        
    @task
    def search(self):
        # Simulates a search with a query parameter
        self.client.get("/search?query=example")
        
    def on_start(self):
        # This runs when a user starts - could be used for logging in
        # Uncomment and modify if your app requires authentication
        # self.client.post("/login", {"username": "test_user", "password": "secret"})
        pass
