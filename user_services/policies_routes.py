from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from .models import get_db, Customer, Policy, CustomerPolicy
from .schemas import PurchasePolicySchema
from .utils import verify_user
from settings import logger

app = APIRouter(tags=["Policy Operations"], prefix= "/policies")

# View policy
@app.get("/", status_code= 200)
def get_policies( user_type: str = Query(..., description="Type of user (admin or customer)"), page: int = Query(1, ge=1, description="Page number (starting from 1)"),
    size: int = Query(10, ge=1, le=100, description="Number of records per page (max: 100)"), db: Session = Depends(get_db)):
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
        # Validate user type
        user_type = user_type.lower()
        if user_type not in {"admin", "customer"}:
            logger.error(f"Invalid user type provided: {user_type}")
            raise HTTPException(status_code=400, detail="Invalid user type. Allowed values: 'admin', 'customer'.")

        # Calculate offset
        offset = (page - 1) * size

        if user_type == "customer":
            # Customers retrieve all available policies
            total_records = db.query(Policy).count()
            policies = db.query(Policy).offset(offset).limit(size).all()
            policies_data = [policy.to_dict for policy in policies]

        else:  # Admins
            # Admin retrieves both total policies and purchased policies with customer IDs
            total_policies = db.query(Policy).count()
            
            # Purchased policies with customer IDs
            purchased_policies_query = (
                db.query(Policy, CustomerPolicy.customer_id)
                .join(CustomerPolicy, Policy.policy_id == CustomerPolicy.policy_id, isouter=True)
                .offset(offset)
                .limit(size)
            )
            purchased_policies = purchased_policies_query.all()

            # Prepare response for admins
            policies_data = []
            for policy, customer_id in purchased_policies:
                policy_data = policy.to_dict
                
                # Include customer ID if policy is purchased
                policy_data["customer_id"] = customer_id if customer_id else "Not Assigned"
                policies_data.append(policy_data)

            total_purchased_policies = db.query(CustomerPolicy).count()
            total_pages = (total_policies + size - 1) // size

            logger.info(f"Admin retrieved {len(policies_data)} policies on page {page}")

            return {
                "message": "Policies retrieved successfully",
                "status": "success",
                "current_page": page,
                "page_size": size,
                "total_pages": total_pages,
                "total_policies": total_policies,
                "total_purchased_policies": total_purchased_policies,
                "data": policies_data,
            }

        # For customers, return paginated policies
        if not policies_data:
            raise HTTPException(status_code=404, detail="No policies found on this page")
        
        total_pages = (total_records + size - 1) // size
        logger.info(f"Customer retrieved {len(policies_data)} policies on page {page}")

        return {
            "message": "Policies retrieved successfully",
            "status": "success",
            "current_page": page,
            "page_size": size,
            "total_pages": total_pages,
            "total_records": total_records,
            "data": policies_data,
        }

    except HTTPException as http_exc:
        logger.error(f"HTTP error during policy retrieval: {http_exc.detail}")
        raise http_exc
    except Exception as exc:
        logger.error(f"Unexpected error during policy retrieval: {str(exc)}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred")
    
    
# Policy purchase by customer
@app.post("/purchase", status_code=201)
def purchase_policy( policy_data: PurchasePolicySchema, token: str = Query(...), db: Session = Depends(get_db)):
    """
    Customer Only, API for customers to purchase a policy.
    Parameters:
    policy_data: PurchasePolicySchema
    token: Customer authentication token
    db: Database session
    Returns:
    A success message with policy details or an error if the purchase fails.
    """
    try:
        # Verify customer access
        _, customer_id = verify_user(token, db, "customer")
        
        # Validate selected policy
        policy = db.query(Policy).filter(Policy.policy_id == policy_data.policy_id).first()
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")

         # Check if the customer already purchased this policy
        customer = db.query(Customer).filter(customer_id == customer_id).first()
        
        if not customer:
            logger.error(f"Customer with ID {customer_id} not found.")
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Check if the policy is already assigned to the customer
        existing_assignment = db.query(CustomerPolicy).filter(CustomerPolicy.customer_id == customer_id, CustomerPolicy.policy_id == policy_data.policy_id).first()
        if existing_assignment:
            logger.error(f"Customer {customer_id} already has policy {policy_data.policy_id}")
            raise HTTPException(status_code=400, detail="Policy already purchased by the customer")

        # Create a new customer-policy assignment
        new_customer_policy = CustomerPolicy(
            customer_id=customer_id, 
            policy_id=policy_data.policy_id, 
            date_assigned=func.now()
        )
        db.add(new_customer_policy)
        db.commit()

        # Log and return success
        logger.info(f"Customer {customer_id} purchased policy {policy.policy_id}")
        return {
            "message": "Policy purchased successfully",
            "status": "success",
            "data": policy.to_dict
        }

    except HTTPException as e:
        logger.error(f"Error during policy purchase: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during policy purchase: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred")
    