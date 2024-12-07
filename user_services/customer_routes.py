from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from .models import get_db, Customer, Policy, Payment
from .schemas import CalculatePremiumSchema, PaymentSchema
from .utils import verify_user, generate_receipt_pdf
from settings import logger
from datetime import datetime
from fastapi.responses import FileResponse


app = APIRouter(tags=["Customer"], prefix="/customer")

# Calculate premium
@app.post("/calculate-premium", status_code=200)
def calculate_premium( premium_details: CalculatePremiumSchema, token: str = Query(...), db: Session = Depends(get_db)):
    """
    Calculate the premium for a policy based on the customer's age, premium and rate of interest.
    """
    try:
        # Verify the user and extract the payload
        user_payload, customer_id = verify_user(token, db, user_type="customer")

        # Retrieve customer details from the database
        customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()

        # Check if the customer exists
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Ensure the customer has a valid date of birth
        if not customer.date_of_birth:
            raise HTTPException(
                status_code=400,
                detail="Date of birth is missing for the customer",
            )

        # Calculate the age based on the date of birth
        today = datetime.today()
        dob = customer.date_of_birth
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        # Log the input details
        logger.info(f"Customer ID: {customer_id}, Age: {age}, Rate of Interest: {premium_details.rate_of_interest}")
        
        # Retrieve policies associated with the customer
        policies = db.query(Policy).filter(Policy.customer_id == customer_id).all()

        if not policies:
            raise HTTPException(
                status_code=404, detail="No policies found for the customer"
            )

        # Calculate total premium for all policies
        policy_ids = []
        total_premium = 0
        for policy in policies:
            # Example calculation: Base premium + interest + age factor
            base_premium = policy.premium  
            age_factor = 1 + (age / 100) 
            interest_factor = 1 + (premium_details.rate_of_interest / 100)

            # Calculate the premium for the policy
            policy_premium = base_premium * age_factor * interest_factor
            total_premium += policy_premium
            
            policy_ids.append(policy.policy_id)

        # Log the total premium
        logger.info(f"Customer ID: {customer_id}, Total Premium: {total_premium:.2f}")

        return {
            "message": "Premium calculated successfully",
            "status": "success",
            "data": {
                "customer_id": customer_id,
                "age": age,
                "policies": policy_ids,
                "rate_of_interest": premium_details.rate_of_interest,
                "total_premium": round(total_premium, 2),
            },
        }

    except HTTPException as e:
        logger.error(f"HTTP Error during premium calculation: {e.detail}")
        raise e

    except Exception as e:
        logger.error(f"Unexpected error during premium calculation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Make payment
@app.post("/make_payment")
def make_payment(payment: PaymentSchema, token: str = Query(...), db: Session = Depends(get_db)):
    """
    API to make a payment for a policy.
    """
    try:
        # Verify the user and extract the payload
        user_payload, customer_id = verify_user(token, db, user_type="customer")

        # Retrieve the policy associated with the payment
        policy = db.query(Policy).filter(Policy.policy_id == payment.policy_id).first()

        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        # Ensure the customer is the one making the payment (check customer ID)
        if policy.customer_id != customer_id:
            raise HTTPException(status_code=403, detail="Payment does not belong to the customer")

        # Create the payment record
        new_payment = Payment(
            customer_id=customer_id,
            policy_id=payment.policy_id,
            amount=payment.amount,
            payment_date=datetime.utcnow()  
        )

        db.add(new_payment)
        db.commit()
        db.refresh(new_payment)

        #Return the payment details as a response
        return {
            "message": "Payment processed successfully", 
            "status": "success",
            "payment_id": new_payment.payment_id
        }
    
    except HTTPException as e:
        logger.error(f"HTTP Error during Payment: {e.detail}")
        raise e

    except Exception as e:
        logger.error(f"Unexpected error during Payment: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

    
# Download Reciept
@app.get("/download_receipt/{payment_id}")
def download_receipt(payment_id: int, token: str, db: Session = Depends(get_db)):
    """
    API to generate and download a receipt/invoice for a payment.
    """
    try:
        # Verify the user and extract the payload
        user_payload, customer_id = verify_user(token, db, user_type="customer")

        # Retrieve customer details from the database
        customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()

        # Check if the customer exists
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Fetch payment details
        payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")

        # Fetch policy details
        policy = db.query(Policy).filter(Policy.policy_id == payment.policy_id).first()
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")

        # Ensure the payment belongs to the customer
        if policy.customer_id != payment.customer_id:
            raise HTTPException(status_code=403, detail="Access denied: Payment does not belong to the customer")

        # Generate the receipt PDF
        receipt_file = generate_receipt_pdf(payment, policy, customer.email)

        # Step 5: Return the file as a response
        return FileResponse(
            path=receipt_file,
            media_type="application/pdf",
            filename=f"Receipt_{customer.email}_{payment_id}.pdf"
        )
    
    except HTTPException as e:
        logger.error(f"HTTP Error during Reciept Generation: {e.detail}")
        raise e

    except Exception as e:
        logger.error(f"Unexpected error during Reciept Generation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
