from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, Date, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine
from settings import settings, logger
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

Base = declarative_base()

# Create engine and session
engine = create_engine(settings.db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get the DB session
def get_db():
    """
    Dependency function to get a new database session.
    This function provides a database session (`db`) that can be used in request handlers.
    The session is opened at the beginning and properly closed after the request completes.
    Yields:
    db (SessionLocal): A new SQLAlchemy session connected to the database.
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database session error: {e}")
        raise HTTPException(status_code=500, detail="Internal database error")
    finally:
        try:
            db.close()
            logger.info("Database session closed.")
        except SQLAlchemyError as e:
            logger.error(f"Failed to close the database session: {e}")

class Admin(Base):
    """
    Represents a `Admin` table in the database.
    """
    __tablename__ = 'admin'
    
    admin_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    @property
    def to_dict(self):
        """
        Converts the `Admin` object to a dictionary format, excluding the password field.
        Returns:
        dict: A dictionary containing all the Admin attributes, except for the password.
        """
        try:
            return {col.name: getattr(self, col.name) for col in self.__table__.columns if col.name != "password"}
        except SQLAlchemyError as e:
            logger.error(f"Error in to_dict method: {e}")
            raise HTTPException(status_code=500, detail="Error processing user data")


class Employee(Base):
    __tablename__ = 'employee'

    employee_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    @property
    def to_dict(self):
        """
        Converts the `Employee` object to a dictionary format, excluding the password field.
        Returns:
        dict: A dictionary containing all the Admin attributes, except for the password.
        """
        try:
            return {col.name: getattr(self, col.name) for col in self.__table__.columns if col.name != "password"}
        except SQLAlchemyError as e:
            logger.error(f"Error in to_dict method: {e}")
            raise HTTPException(status_code=500, detail="Error processing user data")


class InsuranceAgent(Base):
    __tablename__ = 'insurance_agent'

    agent_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationship to Customer
    customers = relationship('Customer', back_populates='agent')

    @property
    def to_dict(self):
        """
        Converts the `InsuranceAgent` object to a dictionary format, excluding the password field.
        Returns:
        dict: A dictionary containing all the Admin attributes, except for the password.
        """
        try:
            return {col.name: getattr(self, col.name) for col in self.__table__.columns if col.name != "password"}
        except SQLAlchemyError as e:
            logger.error(f"Error in to_dict method: {e}")
            raise HTTPException(status_code=500, detail="Error processing user data")


class Customer(Base):
    __tablename__ = 'customer'

    customer_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    agent_id = Column(Integer, ForeignKey('insurance_agent.agent_id'), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationship to InsuranceAgent
    agent = relationship('InsuranceAgent', back_populates='customers')

    # Many-to-many relationship with Policy
    customer_policies = relationship("CustomerPolicy", back_populates="customer")

    @property
    def to_dict(self):
        """
        Converts the `Customer` object to a dictionary format, excluding the password field.
        Returns:
        dict: A dictionary containing all the Admin attributes, except for the password.
        """
        try:
            return {col.name: getattr(self, col.name) for col in self.__table__.columns if col.name != "password"}
        except SQLAlchemyError as e:
            logger.error(f"Error in to_dict method: {e}")
            raise HTTPException(status_code=500, detail="Error processing user data")


class InsurancePlan(Base):
    __tablename__ = 'insurance_plan'

    plan_id = Column(Integer, primary_key=True, autoincrement=True)
    plan_name = Column(String, nullable=False)
    plan_details = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationship to Scheme
    schemes = relationship('Scheme', back_populates='plan')
    
    @property
    def to_dict(self):
        """
        Converts the `InsurancePlan` object to a dictionary format, excluding the password field.
        Returns:
        dict: A dictionary containing all the Admin attributes, except for the password.
        """
        try:
            return {col.name: getattr(self, col.name) for col in self.__table__.columns if col.name != "password"}
        except SQLAlchemyError as e:
            logger.error(f"Error in to_dict method: {e}")
            raise HTTPException(status_code=500, detail="Error processing user data")


class Scheme(Base):
    __tablename__ = 'scheme'

    scheme_id = Column(Integer, primary_key=True, autoincrement=True)
    scheme_name = Column(String, nullable=False)
    scheme_details = Column(String, nullable=False)
    plan_id = Column(Integer, ForeignKey('insurance_plan.plan_id'), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationship to InsurancePlan
    plan = relationship('InsurancePlan', back_populates='schemes')

    # Relationship to Policy
    policies = relationship('Policy', back_populates='scheme')

    # Relationship to EmployeeScheme
    employee_schemes = relationship('EmployeeScheme', back_populates='scheme')

    @property
    def to_dict(self):
        """
        Converts the `Scheme` object to a dictionary format, excluding the password field.
        Returns:
        dict: A dictionary containing all the Admin attributes, except for the password.
        """
        try:
            return {col.name: getattr(self, col.name) for col in self.__table__.columns if col.name != "password"}
        except SQLAlchemyError as e:
            logger.error(f"Error in to_dict method: {e}")
            raise HTTPException(status_code=500, detail="Error processing user data")


class Policy(Base):
    __tablename__ = 'policy'

    policy_id = Column(Integer, primary_key=True, autoincrement=True)
    scheme_id = Column(Integer, ForeignKey('scheme.scheme_id'), nullable=False)
    policy_details = Column(String, nullable=False)
    premium = Column(Integer, nullable=False)
    date_issued = Column(Date, nullable=False)
    maturity_period = Column(Integer, nullable=False)
    policy_lapse_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Many-to-many relationship with Customer
    customer_policies = relationship("CustomerPolicy", back_populates="policy")
    
    # Relationships
    scheme = relationship('Scheme', back_populates='policies')
    payments = relationship('Payment', back_populates='policy')
    commissions = relationship('Commission', back_populates='policy')
    
    @property
    def to_dict(self):
        """
        Converts the `Policy` object to a dictionary format, excluding the password field.
        Returns:
        dict: A dictionary containing all the Admin attributes, except for the password.
        """
        try:
            return {col.name: getattr(self, col.name) for col in self.__table__.columns if col.name != "password"}
        except SQLAlchemyError as e:
            logger.error(f"Error in to_dict method: {e}")
            raise HTTPException(status_code=500, detail="Error processing user data")


class Payment(Base):
    __tablename__ = 'payment'

    payment_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customer.customer_id'), nullable=False)
    policy_id = Column(Integer, ForeignKey('policy.policy_id'), nullable=False)
    amount = Column(Integer, nullable=False)
    payment_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationship to Policy
    policy = relationship('Policy', back_populates='payments')


class Commission(Base):
    __tablename__ = 'commission'

    commission_id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey('insurance_agent.agent_id'), nullable=False)
    policy_id = Column(Integer, ForeignKey('policy.policy_id'), nullable=False)
    commission_amount = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    policy = relationship('Policy', back_populates='commissions')
    agent = relationship('InsuranceAgent')


class EmployeeScheme(Base):
    __tablename__ = 'employee_scheme'

    employee_scheme_id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey('employee.employee_id'), nullable=False)
    scheme_id = Column(Integer, ForeignKey('scheme.scheme_id'), nullable=False)

    # Relationships
    employee = relationship('Employee')
    scheme = relationship('Scheme', back_populates='employee_schemes')

class CustomerPolicy(Base):
    __tablename__ = "customer_policy"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customer.customer_id"), nullable=False)
    policy_id = Column(Integer, ForeignKey("policy.policy_id"), nullable=False)
    date_assigned = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="customer_policies")
    policy = relationship("Policy", back_populates="customer_policies")