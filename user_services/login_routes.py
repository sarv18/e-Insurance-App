from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from .models import Admin, get_db, Employee, Customer, InsuranceAgent
from .schemas import UserRegistrationSchema, CustomerRegistrationSchema, UserLoginSchema
from .utils import hash_password, verify_password, create_token, create_tokens
from settings import logger
from sqlalchemy.exc import SQLAlchemyError

app = APIRouter(tags=["Register and Login"])

# Register a user
@app.post("/register-user", status_code= 201)
def register_user(user_data: UserRegistrationSchema, user_type: str = Query(..., description="Type of user (e.g., admin, employee, insurance_agent)"), db: Session = Depends(get_db)):
    '''
    Discription: Registers a new user based on the user type provided as a query parameter.
    Parameters: 
    user_data: UserRegistrationSchema: The request body is validated using the UserRegistrationSchema, 
    which ensures that all required fields are correctly formatted.
    user_type: Type of user, want to register
    db: Session = Depends(get_db): Uses dependency injection to pass the current database session to the function.
    Return: 
    Returns a JSON response with a success message and the registered user's data (using the to_dict property of the admin model).
    '''
    try:
        # Map user_type to the corresponding ORM model
        user_model_mapping = {
            "admin": Admin,
            "employee": Employee,
            "insurance_agent": InsuranceAgent
        }

        # Validate user_type and select the appropriate model
        model = user_model_mapping.get(user_type.lower())
        if not model:
            logger.error(f"Invalid user type provided: {user_type}")
            raise HTTPException(status_code=400, detail="Invalid user type")
        
        # Check if the user already exists by email
        existing_user = db.query(model).filter(model.email == user_data.email).first()
        if existing_user:
            logger.error(f"Attempt to register an existing email: {user_data.email} for {user_type}")
            raise HTTPException(status_code=400, detail="Email already registered")

        # Hash the user's password
        hashed_password = hash_password(user_data.password)

        # Create a new user object
        db_user = model(
            email=user_data.email,
            password=hashed_password,
            username=user_data.username,
            full_name=user_data.full_name
        )

        # Add the user to the database and commit the transaction
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        # Generate the access token
        access_token = create_token({"sub": db_user.email}, "access")

        logger.info(f"{user_type.capitalize()} registered: {user_data.email}")
        return {
            "message": f"{user_type.capitalize()} registered successfully",
            "status": "success",
            "data": db_user.to_dict,
            "access_token": access_token,
        }

    except SQLAlchemyError as e:
        logger.error(f"Database error during {user_type.capitalize()} registration: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

    except Exception as e:
        logger.error(f"Unexpected error during {user_type.capitalize()} registration: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Register a customer
@app.post("/register-customer", status_code= 201)
def register_customer(user: CustomerRegistrationSchema,  db: Session = Depends(get_db)):
    '''
    Discription: Registers a new customer after validating the input, checking if the user exists, 
    hashing the password, and storing the user in the database.
    Parameters: 
    user: CustomerRegistrationSchema: The request body is validated using the CustomerRegistrationSchema, 
    which ensures that all required fields are correctly formatted.
    db: Session = Depends(get_db): Uses dependency injection to pass the current database session to the function.
    Return: Returns a JSON response with a success message and the registered user's data 
    (using the to_dict property of the User model).
    '''
    try:
        # Check if the user already exists by email
        existing_user = db.query(Customer).filter(Customer.email == user.email).first()
        if existing_user:
            logger.error(f"Attempt to register an existing email: {user.email}")
            raise HTTPException(status_code=400, detail="Email already registered")

        # Hash the user's password
        hashed_password = hash_password(user.password)

        # Create a new User object
        db_user = Customer(
            email=user.email, 
            password=hashed_password,
            username=user.username,
            full_name=user.full_name,
            agent_id=user.agent_id,
            date_of_birth=user.date_of_birth
        )

        # Add the user to the database and commit the transaction
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        # Generate the access token
        access_token = create_token({"sub": db_user.email}, "access")

        logger.info(f"Customer registered: {user.email}")
        return {
            "message": "Customer registered successfully",
            "status": "success",
            "data": db_user.to_dict,
            "access_token": access_token
        }

    except SQLAlchemyError as e:
        logger.error(f"Database error during customer registration: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

    except Exception as e:
        logger.error(f"Unexpected error during customer registration: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# User login
@app.post("/login", status_code= 200)
def login_user(user_data: UserLoginSchema, user_type: str = Query(..., description="Type of user (e.g., admin, employee, customer, insurance_agent)"), db: Session = Depends(get_db)):
    '''
    Discription: Logs in a user based on the user type provided as a query parameter.
    Parameters: 
    user_data: UserLoginSchema: The request body is validated using the UserLoginSchema (email and password).
    user_type: Type of user, want to register
    db: Session = Depends(get_db): Dependency injection is used to get a database session via the get_db function.
    Return:
    If the email and password match, a success message is returned, along with the logged-in user's data.
    '''
    try:
        # Map user_type to the corresponding ORM model
        user_model_mapping = {
            "admin": (Admin, Admin.admin_id),
            "employee": (Employee, Employee.employee_id),
            "customer": (Customer, Customer.customer_id),
            "insurance_agent": (InsuranceAgent, InsuranceAgent.agent_id),
        }

         # Validate user_type and select the appropriate model
        model_info = user_model_mapping.get(user_type.lower())
        if not model_info:
            logger.error(f"Invalid user type provided: {user_type}")
            raise HTTPException(status_code=400, detail="Invalid user type")

        model, id_column = model_info

        # Check if the user exists in the database by email
        db_user = db.query(model).filter(model.email == user_data.email).first()

        # Handle invalid email or password
        if not db_user or not verify_password(user_data.password, db_user.password):
            logger.warning(f"Invalid login attempt for email: {user_data.email} as {user_type}")
            raise HTTPException(status_code=400, detail="Invalid email or password")

        # Generate both JWT tokens
        access_token, refresh_token = create_tokens({"sub": db_user.email, "user_id": getattr(db_user, id_column.name)})

        logger.info(f"{user_type.capitalize()} logged in: {user_data.email}")
        return {
            "message": f"{user_type.capitalize()} login successful",
            "status": "success",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "data": db_user.to_dict,
        }

    except SQLAlchemyError as e:
        logger.error(f"Database error during {user_type.capitalize()} login: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

    except Exception as e:
        logger.error(f"Unexpected error during {user_type.capitalize()} login: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
