from fastapi import FastAPI
from user_services import admin_routes, customer_routes, login_routes, policies_routes

# Initialize FastAPI app
app = FastAPI()

# Include router for Register and Login
app.include_router(login_routes.app)

# Include router for admin
app.include_router(admin_routes.app)

# Include router for Customer
app.include_router(customer_routes.app)

# Include router for Policy Operations
app.include_router(policies_routes.app)





