import logging
from typing import Dict, Any, List, Optional
from config.config import Config
import json
import re
import random
import string

logger = logging.getLogger(__name__)

# Check if OpenAI is available
OPENAI_AVAILABLE = False
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI package not found. AI data generation will use fallback methods.")

class AIDataGenerator:
    """Helper class for generating realistic test data using AI."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with optional API key, otherwise use from config."""
        self.api_key = api_key or Config.OPENAI_API_KEY
        self.openai_available = OPENAI_AVAILABLE
        
        if self.openai_available:
            try:
                openai.api_key = self.api_key
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.openai_available = False
    
    def generate_user_profile(self, constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a realistic user profile with optional constraints.
        
        Args:
            constraints: Optional dictionary of constraints (e.g., {"country": "US", "age_min": 21})
            
        Returns:
            Dictionary with user profile data
        """
        if self.openai_available and self.api_key:
            try:
                constraints_text = ""
                if constraints:
                    constraints_text = "with these constraints: " + ", ".join([f"{k}: {v}" for k, v in constraints.items()])
                
                prompt = f"Generate a JSON object for a user profile {constraints_text}. Include name, email, age, address, and phone number fields."
                
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a test data generator that outputs only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                
                # Extract and parse the JSON response
                content = response.choices[0].message.content
                # Extract the JSON part from the response if needed
                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = content
                    
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    # Fall through to the fallback method
            except Exception as e:
                logger.error(f"Error generating user profile with AI: {e}")
                # Fall through to the fallback method
        
        # Fallback method: generate synthetic user profile
        return self._generate_fallback_user_profile(constraints)
    
    def _generate_fallback_user_profile(self, constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a synthetic user profile when AI is not available."""
        first_names = ["John", "Jane", "Michael", "Sarah", "David", "Lisa", "Robert", "Emily", "William", "Olivia"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Garcia", "Wilson", "Martinez"]
        domains = ["example.com", "test.com", "email.com", "domain.com", "mail.org"]
        street_types = ["St", "Ave", "Blvd", "Ln", "Dr", "Rd", "Ct", "Way", "Pl", "Pkwy"]
        cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"]
        states = ["NY", "CA", "IL", "TX", "AZ", "PA", "FL", "OH", "MI", "GA"]
        
        # Get constraints
        constraints = constraints or {}
        country = constraints.get("country", "US")
        age_min = constraints.get("age_min", 18)
        age_max = constraints.get("age_max", 80)
        
        # Generate basic profile
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        age = random.randint(age_min, age_max)
        email = f"{first_name.lower()}.{last_name.lower()}@{random.choice(domains)}"
        
        # Generate address
        street_num = random.randint(1, 9999)
        street_name = random.choice(last_names)
        street_type = random.choice(street_types)
        city = random.choice(cities)
        state = random.choice(states)
        zip_code = f"{random.randint(10000, 99999)}"
        
        address = f"{street_num} {street_name} {street_type}, {city}, {state} {zip_code}"
        
        # Generate phone number
        phone = f"{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        
        return {
            "name": f"{first_name} {last_name}",
            "email": email,
            "age": age,
            "address": address,
            "phone": phone,
            "country": country
        }
    
    def generate_api_payload(self, endpoint: str, method: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate an API payload based on endpoint, method, and optional schema.
        
        Args:
            endpoint: The API endpoint
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            schema: Optional schema definition for the payload
            
        Returns:
            Dictionary with API payload data
        """
        if self.openai_available and self.api_key:
            try:
                schema_text = ""
                if schema:
                    schema_text = "following this schema: " + json.dumps(schema)
                
                prompt = f"Generate a valid JSON payload for a {method} request to {endpoint} endpoint {schema_text}."
                
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a test data generator that outputs only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                
                # Extract and parse the JSON response
                content = response.choices[0].message.content
                # Extract the JSON part from the response
                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = content
                    
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    # Fall through to the fallback method
            except Exception as e:
                logger.error(f"Error generating API payload with AI: {e}")
                # Fall through to the fallback method
        
        # Fallback method: generate synthetic API payload
        return self._generate_fallback_api_payload(endpoint, method, schema)
    
    def _generate_fallback_api_payload(self, endpoint: str, method: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a synthetic API payload when AI is not available."""
        # Basic fields based on common API practices
        if "/users" in endpoint:
            payload = {
                "name": f"Test User {random.randint(1, 1000)}",
                "email": f"user{random.randint(1, 1000)}@example.com",
                "role": random.choice(["admin", "user", "guest"])
            }
        elif "/products" in endpoint:
            payload = {
                "name": f"Test Product {random.randint(1, 1000)}",
                "price": round(random.uniform(10, 1000), 2),
                "category": random.choice(["electronics", "clothing", "food", "books"])
            }
        elif "/orders" in endpoint:
            payload = {
                "orderId": f"ORD-{random.randint(1000, 9999)}",
                "userId": random.randint(1, 100),
                "items": [
                    {"productId": random.randint(1, 100), "quantity": random.randint(1, 5)}
                    for _ in range(random.randint(1, 3))
                ]
            }
        else:
            # Generic payload
            payload = {
                "id": random.randint(1, 1000),
                "name": f"Test Item {random.randint(1, 1000)}",
                "active": random.choice([True, False])
            }
        
        # Apply schema if provided
        if schema:
            for key, type_str in schema.items():
                if type_str == "string":
                    payload[key] = f"test_{key}_{random.randint(1, 1000)}"
                elif type_str == "integer":
                    payload[key] = random.randint(1, 1000)
                elif type_str == "boolean":
                    payload[key] = random.choice([True, False])
                elif type_str == "array":
                    payload[key] = [f"item_{i}" for i in range(random.randint(1, 3))]
                elif type_str == "object":
                    payload[key] = {"subkey": f"value_{random.randint(1, 100)}"}
        
        return payload
    
    def generate_test_data_set(self, data_type: str, count: int = 5, constraints: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Generate a set of test data items.
        
        Args:
            data_type: Type of data to generate (e.g., "user", "product", "address")
            count: Number of items to generate
            constraints: Optional constraints to apply
            
        Returns:
            List of generated data items
        """
        if self.openai_available and self.api_key:
            try:
                constraints_text = ""
                if constraints:
                    constraints_text = "with these constraints: " + ", ".join([f"{k}: {v}" for k, v in constraints.items()])
                
                prompt = f"Generate a JSON array containing {count} {data_type} objects {constraints_text}. Each object should have appropriate fields for a {data_type}."
                
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a test data generator that outputs only valid JSON arrays."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                
                # Extract and parse the JSON response
                content = response.choices[0].message.content
                # Extract the JSON part from the response
                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = content
                    
                try:
                    result = json.loads(json_str)
                    if isinstance(result, list):
                        return result
                    elif isinstance(result, dict):
                        return [result]  # Convert single object to list
                    else:
                        logger.error(f"Unexpected response format: {type(result)}")
                        # Fall through to the fallback method
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    # Fall through to the fallback method
            except Exception as e:
                logger.error(f"Error generating test data set with AI: {e}")
                # Fall through to the fallback method
        
        # Fallback method: generate synthetic data set
        if data_type.lower() == "user":
            return [self._generate_fallback_user_profile(constraints) for _ in range(count)]
        elif data_type.lower() in ["product", "products"]:
            return self._generate_fallback_products(count, constraints)
        elif data_type.lower() in ["order", "orders"]:
            return self._generate_fallback_orders(count, constraints)
        else:
            # Generic data items
            return [self._generate_fallback_generic_item(data_type, constraints) for _ in range(count)]
    
    def _generate_fallback_products(self, count: int, constraints: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Generate synthetic product data."""
        constraints = constraints or {}
        category = constraints.get("category")
        
        products = []
        product_names = ["Widget", "Gadget", "Tool", "Device", "Accessory", "Item", "Product"]
        categories = ["electronics", "clothing", "food", "books", "home", "toys", "sports"]
        
        for i in range(count):
            name = f"{random.choice(product_names)} {random.randint(1, 1000)}"
            price = round(random.uniform(10, 1000), 2)
            stock = random.randint(0, 100)
            product_category = category or random.choice(categories)
            
            product = {
                "id": i + 1,
                "name": name,
                "price": price,
                "stock": stock,
                "category": product_category,
                "active": random.choice([True, False])
            }
            
            products.append(product)
        
        return products
    
    def _generate_fallback_orders(self, count: int, constraints: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Generate synthetic order data."""
        constraints = constraints or {}
        
        orders = []
        statuses = ["pending", "processing", "shipped", "delivered", "cancelled"]
        
        for i in range(count):
            order_id = f"ORD-{random.randint(1000, 9999)}"
            user_id = random.randint(1, 100)
            status = constraints.get("status") or random.choice(statuses)
            item_count = random.randint(1, 5)
            
            items = []
            total = 0
            
            for j in range(item_count):
                price = round(random.uniform(10, 100), 2)
                quantity = random.randint(1, 3)
                item_total = price * quantity
                total += item_total
                
                items.append({
                    "productId": random.randint(1, 100),
                    "name": f"Product {random.randint(1, 100)}",
                    "price": price,
                    "quantity": quantity,
                    "total": item_total
                })
            
            order = {
                "id": i + 1,
                "orderId": order_id,
                "userId": user_id,
                "status": status,
                "items": items,
                "total": round(total, 2),
                "date": f"2023-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
            }
            
            orders.append(order)
        
        return orders
    
    def _generate_fallback_generic_item(self, item_type: str, constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a generic data item."""
        constraints = constraints or {}
        
        # Basic fields
        item = {
            "id": random.randint(1, 1000),
            "name": f"{item_type.title()} {random.randint(1, 1000)}",
            "description": f"This is a test {item_type}",
            "createdAt": f"2023-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        }
        
        # Add some random fields
        item["active"] = random.choice([True, False])
        item["score"] = round(random.uniform(0, 100), 2)
        item["tags"] = [f"tag{i}" for i in range(random.randint(1, 3))]
        
        # Apply any constraints
        for key, value in constraints.items():
            item[key] = value
        
        return item
    
    def generate_form_data(self, form_name: str, fields: List[str]) -> Dict[str, Any]:
        """
        Generate form data based on form name and field list.
        
        Args:
            form_name: Name of the form (e.g., "registration", "payment")
            fields: List of field names
            
        Returns:
            Dictionary with form field values
        """
        if self.openai_available and self.api_key:
            try:
                fields_text = ", ".join(fields)
                
                prompt = f"Generate valid form data for a {form_name} form with these fields: {fields_text}. Return as JSON with the field names as keys."
                
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a test data generator that outputs only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                
                # Extract and parse the JSON response
                content = response.choices[0].message.content
                # Extract the JSON part from the response
                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = content
                    
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    # Fall through to the fallback method
            except Exception as e:
                logger.error(f"Error generating form data with AI: {e}")
                # Fall through to the fallback method
        
        # Fallback method: generate synthetic form data
        return self._generate_fallback_form_data(form_name, fields)
    
    def _generate_fallback_form_data(self, form_name: str, fields: List[str]) -> Dict[str, Any]:
        """Generate synthetic form data when AI is not available."""
        form_data = {}
        
        # Common field patterns
        for field in fields:
            field_lower = field.lower()
            
            # Name fields
            if "name" in field_lower:
                if "first" in field_lower:
                    form_data[field] = random.choice(["John", "Jane", "Michael", "Sarah", "David"])
                elif "last" in field_lower:
                    form_data[field] = random.choice(["Smith", "Johnson", "Williams", "Brown", "Jones"])
                elif "full" in field_lower:
                    form_data[field] = f"{random.choice(['John', 'Jane'])} {random.choice(['Smith', 'Johnson'])}"
                else:
                    form_data[field] = f"Test User {random.randint(1, 100)}"
            
            # Email fields
            elif "email" in field_lower:
                form_data[field] = f"user{random.randint(1, 1000)}@example.com"
            
            # Password fields
            elif "password" in field_lower or "pwd" in field_lower:
                # Generate a random password
                chars = string.ascii_letters + string.digits + string.punctuation
                form_data[field] = ''.join(random.choice(chars) for _ in range(12))
            
            # Phone fields
            elif "phone" in field_lower:
                form_data[field] = f"{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
            
            # Address fields
            elif "address" in field_lower:
                form_data[field] = f"{random.randint(1, 9999)} Example St, Test City, TS 12345"
            elif "city" in field_lower:
                form_data[field] = random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"])
            elif "state" in field_lower:
                form_data[field] = random.choice(["NY", "CA", "IL", "TX", "AZ"])
            elif "zip" in field_lower or "postal" in field_lower:
                form_data[field] = f"{random.randint(10000, 99999)}"
            elif "country" in field_lower:
                form_data[field] = random.choice(["US", "CA", "UK", "AU", "DE"])
            
            # Date fields
            elif "date" in field_lower or "dob" in field_lower or "birth" in field_lower:
                form_data[field] = f"{random.randint(1970, 2000)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
            
            # Number fields
            elif "age" in field_lower:
                form_data[field] = random.randint(18, 80)
            elif "amount" in field_lower or "price" in field_lower or "cost" in field_lower:
                form_data[field] = round(random.uniform(10, 1000), 2)
            
            # Boolean fields
            elif "subscribe" in field_lower or "agree" in field_lower or "accept" in field_lower:
                form_data[field] = random.choice([True, False])
            
            # Generic fields
            else:
                form_data[field] = f"test_{field}_{random.randint(1, 100)}"
        
        return form_data
