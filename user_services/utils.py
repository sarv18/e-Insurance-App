from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import jwt
from settings import settings, logger
from sqlalchemy.orm import Session
from fastapi import HTTPException
from .models import Admin, Customer
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter 
from pathlib import Path


# CryptContext for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Utility function to hash a password
def hash_password(password: str) -> str:
    '''
    Discription: Takes a plain text password and returns a hashed version of it using bcrypt.
    Parameters: 
    password: str: A string representing the plain text password that needs to be hashed.
    Return: 
    str: Returns the hashed version of the password as a string.
    '''
    try:
        hashed_password = pwd_context.hash(password)
        logger.info("Password hashed successfully.")
        return hashed_password
    except Exception as e:
        logger.error(f"Error while hashing password: {str(e)}")
        raise ValueError("Password hashing failed.")


# Utility function to verify hashed password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    '''
    Discription: Takes a plain text password and a hashed password and checks if 
    they are equivalent by hashing the plain text and comparing the result.
    Parameters: 
    plain_password: str: The plain text password input by the user.
    hashed_password: str: The hashed password that was stored (e.g., during user registration).
    Return: 
    bool: Returns True if the plain text password matches the hashed password, otherwise False.
    '''
    try:
        is_valid = pwd_context.verify(plain_password, hashed_password)
        logger.info("Password verification successful.")
        return is_valid
    except Exception as e:
        logger.error(f"Error while verifying password: {str(e)}")
        return False


# Unified Token Generation Function
def create_token(data: dict, token_type: str, exp= None):
    """
    Creates a token (either access or refresh) based on the token_type parameter.
    Parameters:
    data (dict): Data to encode into the token.
    token_type (str): The type of token to create, either 'access' or 'refresh'.
    exp (datetime, optional): Optional expiration time. If not provided, defaults are used.
    Returns:
    str: The encoded JWT token.
    """
    try:
        if token_type == "access":
            expiration = exp or (datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes))
        elif token_type == "refresh":
            expiration = exp or (datetime.now(timezone.utc) + timedelta(minutes=settings.refresh_token_expire_minutes))
        else:
            raise ValueError("Invalid token type. Must be 'access' or 'refresh'.")

        token = jwt.encode({**data, "exp": expiration}, settings.secret_key, algorithm=settings.algorithm)
        logger.info(f"{token_type.capitalize()} token created successfully.")
        return token

    except Exception as e:
        logger.error(f"Error while creating {token_type} token: {str(e)}")
        raise
  
# To generate both tokens
def create_tokens(data: dict):
    """
    Description:
    Generates both access and refresh tokens for a given user.
    Parameters:
    data : Data to encode into the tokens.
    Returns:
    tuple: A tuple containing the access token and refresh token.
    """
    try:
        access_token = create_token(data, "access")
        refresh_token = create_token(data, "refresh")
        logger.info("Access and refresh tokens created successfully.")
        return access_token, refresh_token
    except Exception as e:
        logger.error(f"Error while generating tokens: {str(e)}")
        raise
    
# verify user  
def verify_user(token: str, db: Session, user_type: str):
    """
    Verify a user (admin or customer) based on the provided token and user type.
    Parameters:
    token (str): JWT token for authentication.
    db (Session): Database session.
    user_type (str): Type of user to verify ('admin' or 'customer').
    Returns:
    payload (dict): Decoded JWT payload if the user is verified.
    """
    try:
        # Decode the token
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token: email missing")

        # Verify the user type and check the database
        if user_type.lower() == "admin":
            user = db.query(Admin).filter(Admin.email == email).first()
        elif user_type.lower() == "customer":
            user = db.query(Customer).filter(Customer.email == email).first()
        else:
            raise HTTPException(status_code=400, detail=f"Invalid {user_type} provided")

        # Raise an error if the user does not exist
        if not user:
            raise HTTPException(
                status_code=403, detail=f"Access denied: User is not a valid {user_type}"
            )
                    
        # Return the customer ID for 'customer', or None for 'admin'
        customer_id = user.customer_id if user_type.lower() == "customer" else None
        return email, customer_id

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def generate_receipt_pdf(payment, policy, customer_email: str):
    """
    Generates a receipt as a PDF file.
    """
    # Directory to store receipts
    receipt_dir = Path("receipts")
    receipt_dir.mkdir(exist_ok=True)  # Ensure the directory exists

    # Generate file path
    file_path = receipt_dir / f"Receipt_{customer_email}_{payment.payment_id}.pdf"

    # Create the PDF
    c = canvas.Canvas(str(file_path), pagesize=letter)
    c.setFont("Helvetica", 12)

    # Title
    c.drawString(100, 750, "Receipt/Invoice")
    c.line(100, 745, 500, 745)

    # Customer Details
    c.drawString(100, 720, f"Customer Email: {customer_email}")
    c.drawString(100, 700, f"Policy Name: {policy.policy_details}")
    c.drawString(100, 680, f"Policy ID: {policy.policy_id}")

    # Payment Details
    c.drawString(100, 660, f"Payment ID: {payment.payment_id}")
    c.drawString(100, 640, f"Payment Date: {payment.payment_date.strftime('%Y-%m-%d')}")
    c.drawString(100, 620, f"Amount Paid: $ {payment.amount:.2f}")

    # Footer
    c.drawString(100, 600, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Save the PDF
    c.save()

    return file_path