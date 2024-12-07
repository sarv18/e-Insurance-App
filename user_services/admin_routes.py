from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from .models import get_db, Employee, Customer, InsuranceAgent, InsurancePlan, Scheme, Policy, Commission
from .schemas import UserRegistrationSchema, CustomerRegistrationSchema, InsurancePlanSchema, SchemeSchema, PolicySchema, CalculateCommissionSchema
from .utils import hash_password, verify_user
from settings import logger
from sqlalchemy.exc import SQLAlchemyError

# Initialize FastAPI app
app = APIRouter(tags=["Admin"], prefix="/admin")

# Create insurance plan 
@app.post("/insurance-plans", status_code=201)
def create_insurance_plan( plan_data: InsurancePlanSchema, token: str,  db: Session = Depends(get_db)):
    """
    Creates a new insurance plan. Only admins are authorized to perform this action.
    """
    try:
        # Verify admin authentication
        verify_user(token, db, "admin")
        
        # Check for duplicate plan names
        existing_plan = db.query(InsurancePlan).filter(InsurancePlan.plan_name == plan_data.plan_name).first()
        if existing_plan:
            logger.error(f"Duplicate insurance plan name: {plan_data.plan_name}")
            raise HTTPException(status_code=400, detail="Insurance plan with this name already exists")

        # Create and save the new insurance plan
        new_plan = InsurancePlan(
            plan_name=plan_data.plan_name,
            plan_details=plan_data.plan_details,
        )
        
        db.add(new_plan)
        db.commit()
        db.refresh(new_plan)

        logger.info(f"Insurance plan created by admin")
        return {
            "message": "Insurance plan created successfully",
            "status": "success",
            "data": new_plan.to_dict,
        }

    except SQLAlchemyError as e:
        logger.error(f"Database error during insurance plan creation: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

    except Exception as e:
        logger.error(f"Unexpected error during insurance plan creation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Create scheme
@app.post("/scheme", status_code=201)
def create_scheme( scheme_data: SchemeSchema, token: str,  db: Session = Depends(get_db)):
    """
    Creates a new scheme. Only admins are authorized to perform this action.
    """
    try:
        # Verify admin authentication
        verify_user(token, db, "admin")
        
        # Check for duplicate scheme names
        existing_scheme = db.query(Scheme).filter(Scheme.scheme_name == scheme_data.scheme_name).first()
        if existing_scheme:
            logger.error(f"Duplicate scheme name: {scheme_data.scheme_name}")
            raise HTTPException(status_code=400, detail="Scheme with this name already exists")

        # Create and save the new scheme
        new_scheme = Scheme(
            scheme_name=scheme_data.scheme_name,
            scheme_details=scheme_data.scheme_details,
            plan_id=scheme_data.plan_id
        )
        
        db.add(new_scheme)
        db.commit()
        db.refresh(new_scheme)

        logger.info(f"Scheme created by admin")
        return {
            "message": "Scheme created successfully",
            "status": "success",
            "data": new_scheme.to_dict,
        }

    except SQLAlchemyError as e:
        logger.error(f"Database error during scheme creation: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

    except Exception as e:
        logger.error(f"Unexpected error during scheme creation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Create policy
@app.post("/policy", status_code=201)
def create_policy( policy_data: PolicySchema, token: str,  db: Session = Depends(get_db)):
    """
    Creates a new policy. Only admins are authorized to perform this action.
    """
    try:
        # Verify admin authentication
        verify_user(token, db, "admin")
        
        # Check for duplicate policy names
        existing_policy = db.query(Policy).filter(Policy.policy_details == policy_data.policy_details).first()
        if existing_policy:
            logger.error(f"Duplicate policy name: {policy_data.policy_details}")
            raise HTTPException(status_code=400, detail="policy with this name already exists")

        # Create and save the new policy
        new_policy = Policy(
            policy_details= policy_data.policy_details,
            scheme_id= policy_data.scheme_id,
            premium= policy_data.premium,
            date_issued= policy_data.date_issued,
            maturity_period= policy_data.maturity_period,
            policy_lapse_date= policy_data.policy_lapse_date
        )
        
        db.add(new_policy)
        db.commit()
        db.refresh(new_policy)

        logger.info(f"policy created by admin")
        return {
            "message": "policy created successfully",
            "status": "success",
            "data": new_policy.to_dict,
        }

    except SQLAlchemyError as e:
        logger.error(f"Database error during policy creation: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

    except Exception as e:
        logger.error(f"Unexpected error during policy creation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Employee creation by Admin
@app.post("/employee", status_code=201)
def create_employee( employee_data: UserRegistrationSchema, token: str = Query(...), db: Session = Depends(get_db)):
    """
    Create a new employee. Admin only.
    """
    try:
        # Verify admin access
        verify_user(token, db, "admin")

        # Check if the user already exists by email
        existing_employee = db.query(Employee).filter(Employee.email == employee_data.email).first()
        if existing_employee:
            logger.error(f"Attempt to register an existing email: {employee_data.email}")
            raise HTTPException(status_code=400, detail="Email already registered")

        # Hash the user's password
        hashed_password = hash_password(employee_data.password)
        
        # Create a new employee
        new_employee = Employee(
            email=employee_data.email, 
            password=hashed_password,
            username=employee_data.username,
            full_name=employee_data.full_name                        
        )
        db.add(new_employee)
        db.commit()
        db.refresh(new_employee)

        logger.info(f"Employee created by Admin successfully : {employee_data.email}")
        return {
            "message": "Employee created by Admin successfully", 
            "status": "success",
            "data": new_employee.to_dict}

    except HTTPException as e:
        logger.error(f"Error creating employee: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create employee")

# Employee update by Admin
@app.put("/employee/{employee_id}", status_code=200)
def update_employee( employee_id: int, employee_data: UserRegistrationSchema, token: str = Query(...), db: Session = Depends(get_db)):
    """
    Update an employee's details. Admin only.
    """
    try:
        # Verify admin access
        verify_user(token, db, "admin")

        # Fetch and update employee
        employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
        if not employee:
            logger.error(f"Employee not found: {employee_data.email}")
            raise HTTPException(status_code=404, detail="Employee not found.")

        for key, value in employee_data.dict().items():
            if key == "password" and value:  
                hashed_password = hash_password(value)
                setattr(employee, key, hashed_password)
            else:
                setattr(employee, key, value)

        db.commit()
        db.refresh(employee)

        logger.info("Employee updated by admin successfully .")
        return {
            "message": "Employee updated by admin successfully", 
            "status": "success",
            "data": employee.to_dict
        }

    except HTTPException as e:
        logger.error(f"Error updating employee: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update employee")

# Delete employee by admin
@app.delete("/employee/{employee_id}", status_code=200)
def delete_employee( employee_id: int, token: str = Query(...), db: Session = Depends(get_db)):
    """
    Delete an employee. Admin only.
    """
    try:
        # Verify admin access
        verify_user(token, db, "admin")

        # Fetch and delete employee
        employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
        if not employee:
            logger.error(f"Employee not found with ID {employee_id}")
            raise HTTPException(status_code=404, detail="Employee not found.")

        db.delete(employee)
        db.commit()

        logger.info("Employee deleted successfully.")
        return {
            "message": "Employee deleted successfully",
            "status": "success"
        }

    except HTTPException as e:
        logger.error(f"Error deleting employee: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete employee")


# Insurance agent creation by Admin
@app.post("/insurance_agent", status_code=201)
def create_insurance_agent( insurance_agent_data: UserRegistrationSchema, token: str = Query(...), db: Session = Depends(get_db)):
    """
    Create a new Insurance agent. Admin only.
    """
    try:
        # Verify admin access
        verify_user(token, db, "admin")

        # Check if the user already exists by email
        existing_insurance_agent = db.query(InsuranceAgent).filter(InsuranceAgent.email == insurance_agent_data.email).first()
        if existing_insurance_agent:
            logger.error(f"Attempt to register an existing email: {insurance_agent_data.email}")
            raise HTTPException(status_code=400, detail="Email already registered")

        # Hash the user's password
        hashed_password = hash_password(insurance_agent_data.password)
        
        # Create a new insurance_agent
        new_insurance_agent = InsuranceAgent(
            email=insurance_agent_data.email, 
            password=hashed_password,
            username=insurance_agent_data.username,
            full_name=insurance_agent_data.full_name                        
        )
        db.add(new_insurance_agent)
        db.commit()
        db.refresh(new_insurance_agent)

        logger.info(f"Insurance agent created by Admin successfully : {insurance_agent_data.email}")
        return {
            "message": "Insurance agent created by Admin successfully", 
            "status": "success",
            "data": new_insurance_agent.to_dict}

    except HTTPException as e:
        logger.error(f"Error creating insurance_agent: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create insurance_agent")


# Insurance agent update by Admin
@app.put("/insurance_agent/{insurance_agent_id}", status_code=200)
def update_insurance_agent( insurance_agent_id: int, insurance_agent_data: UserRegistrationSchema, token: str = Query(...), db: Session = Depends(get_db)):
    """
    Update an Insurance agent's details. Admin only.
    """
    try:
        # Verify admin access
        verify_user(token, db, "admin")
        
        # Fetch and update insurance_agent
        insurance_agent = db.query(InsuranceAgent).filter(InsuranceAgent.agent_id == insurance_agent_id).first()
        if not insurance_agent:
            logger.error(f"Insurance agent not found: {insurance_agent_data.email}")
            raise HTTPException(status_code=404, detail="Insurance agent not found.")

        for key, value in insurance_agent_data.dict().items():
            if key == "password" and value:  
                hashed_password = hash_password(value)
                setattr(insurance_agent, key, hashed_password)
            else:
                setattr(insurance_agent, key, value)

        db.commit()
        db.refresh(insurance_agent)

        logger.info("Insurancc Agent updated by admin successfully .")
        return {
            "message": "Insurance Agent updated by Admin successfully", 
            "status": "success",
            "data": insurance_agent.to_dict
        }

    except HTTPException as e:
        logger.error(f"Error updating Insurance Agent: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update Insurance Agent")

# Delete Insurance Agent by admin
@app.delete("/insurance_agent/{insurance_agent_id}", status_code=200)
def delete_insurance_agent( insurance_agent_id: int, token: str = Query(...), db: Session = Depends(get_db)):
    """
    Delete an Insurance Agent. Admin only.
    """
    try:
        # Verify admin access
        verify_user(token, db, "admin")

        # Fetch and delete insurance_agent
        insurance_agent = db.query(InsuranceAgent).filter(InsuranceAgent.agent_id == insurance_agent_id).first()
        if not insurance_agent:
            logger.error(f"Insurance Agent not found with ID {insurance_agent_id}")
            raise HTTPException(status_code=404, detail="Insurance Agent not found.")

        db.delete(insurance_agent)
        db.commit()

        logger.info("Insurance Agent deleted successfully.")
        return {
            "message": "Insurance Agent deleted successfully",
            "status": "success"
        }

    except HTTPException as e:
        logger.error(f"Error deleting Insurance agent: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete Insurance agent.")


# Customer creation by Admin
@app.post("/customer", status_code=201)
def create_customer( customer_data: CustomerRegistrationSchema, token: str = Query(...), db: Session = Depends(get_db)):
    """
    Create a new customer. Admin only.
    """
    try:
        # Verify admin access
        verify_user(token, db, "admin")

        # Check if the user already exists by email
        existing_customer = db.query(Customer).filter(Customer.email == customer_data.email).first()
        if existing_customer:
            logger.error(f"Attempt to register an existing email: {customer_data.email}")
            raise HTTPException(status_code=400, detail="Email already registered")

        # Hash the user's password
        hashed_password = hash_password(customer_data.password)
        
        # Create a new customer
        new_customer = Customer(
            email=customer_data.email, 
            password=hashed_password,
            username=customer_data.username,
            full_name=customer_data.full_name,
            agent_id=customer_data.agent_id,
            date_of_birth=customer_data.date_of_birth                        
        )
        db.add(new_customer)
        db.commit()
        db.refresh(new_customer)

        logger.info(f"Customer created by Admin successfully : {customer_data.email}")
        return {
            "message": "Customer created by Admin successfully", 
            "status": "success",
            "data": new_customer.to_dict}

    except HTTPException as e:
        logger.error(f"Error creating customer: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create customer")


# Customer update by Admin
@app.put("/customer/{customer_id}", status_code=200)
def update_customer( customer_id: int, customer_data: CustomerRegistrationSchema, token: str = Query(...), db: Session = Depends(get_db)):
    """
    Update an customer's details. Admin only.
    """
    try:
        # Verify admin access
        verify_user(token, db, "admin")

        # Fetch and update customer
        customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
        if not customer:
            logger.error(f"customer not found: {customer_data.email}")
            raise HTTPException(status_code=404, detail="Customer not found.")

        for key, value in customer_data.dict().items():
            if key == "password" and value:  
                hashed_password = hash_password(value)
                setattr(customer, key, hashed_password)
            else:
                setattr(customer, key, value)

        db.commit()
        db.refresh(customer)

        logger.info("Customer updated by admin successfully .")
        return {
            "message": "Customer updated by admin successfully", 
            "status": "success",
            "data": customer.to_dict
        }

    except HTTPException as e:
        logger.error(f"Error updating customer: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update customer")

# Delete customer by admin
@app.delete("/customer/{customer_id}", status_code=200)
def delete_customer( customer_id: int, token: str = Query(...), db: Session = Depends(get_db)):
    """
    Delete an customer. Admin only.
    """
    try:
        # Verify admin access
        verify_user(token, db, "admin")

        # Fetch and delete customer
        customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
        if not customer:
            logger.error(f"Customer not found with ID {customer_id}")
            raise HTTPException(status_code=404, detail="Customer not found.")

        # Handle policies associated with the customer
        policies = db.query(Policy).filter(Policy.customer_id == customer_id).all()
        for policy in policies:
            policy.customer_id = None 
            db.add(policy)

        db.delete(customer)
        db.commit()

        logger.info("Customer deleted successfully.")
        return {
            "message": "Customer deleted successfully",
            "status": "success"
        }

    except HTTPException as e:
        logger.error(f"Error deleting customer: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete customer")


@app.post("/calculate-commission", status_code=200)
def calculate_commission( commission_details: CalculateCommissionSchema, token: str = Query(), db: Session = Depends(get_db)):
    """
    Commition Calculation for agents. Admin only.
    """
    try:
        # Verify the admin
        admin_payload = verify_user(token, db, "admin")

        # Retrieve the insurance agent by agent_id
        agent = db.query(InsuranceAgent).filter(InsuranceAgent.agent_id == commission_details.agent_id).first()

        if not agent:
            raise HTTPException(status_code=404, detail="Insurance agent not found")

        # Retrieve all customers managed by the agent
        customers = db.query(Customer).filter(Customer.agent_id == agent.agent_id).all()

        if not customers:
            raise HTTPException(status_code=404, detail="No customers found for this agent")

        # Collect all policies associated with these customers
        customer_ids = [customer.customer_id for customer in customers]
        policies = db.query(Policy).filter(Policy.customer_id.in_(customer_ids)).all()

        if not policies:
            raise HTTPException(status_code=404, detail="No policies found for this agent's customers")
        
        # Calculate total commission
        commission_rate = commission_details.commission_rate / 100 
        total_commission = 0

        commission_details_list = []
        for policy in policies:
            # Ensure `policy` attributes are accessed correctly
            commission = policy.premium * commission_rate
            total_commission += commission

            commission_details_list.append({
                "policy_id": policy.policy_id,
                "policy_details": policy.policy_details,
                "premium": policy.premium,
                "commission": commission,
            })
            
            # Log the calculated commission for each policy
            logger.info(f"Policy ID: {policy.policy_id}, Premium: {policy.premium}, Commission: {commission}")

            # Store the commission in the Commission table
            commission_record = Commission(
                agent_id=agent.agent_id,
                policy_id=policy.policy_id,
                commission_amount=commission
            )
            db.add(commission_record)

        # Commit the transaction
        db.commit()

        # Calculate total commission using a generator expression
        total_commission = sum(detail["commission"] for detail in commission_details_list)

        # Log and return the result
        logger.info(f"Admin: {admin_payload[0]} calculated commission for Agent ID: {agent.agent_id}")

        return {
            "agent_id": agent.agent_id,
            "total_commission": total_commission,
            "commission_rate": commission_details.commission_rate,
            "commission_details": commission_details_list,
        }

    except HTTPException as e:
        logger.error(f"HTTP error during commission calculation: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during commission calculation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")