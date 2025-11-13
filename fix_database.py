import os
from sqlalchemy import create_engine, text
from backend.database import Base
from backend import models

# Your Neon PostgreSQL connection
DATABASE_URL = "postgresql://neondb_owner:npg_QKXcYWpmGj90@ep-dawn-cherry-a4wr3mmr-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require"

def reset_database():
    """Drop and recreate all tables with correct schema"""
    engine = create_engine(DATABASE_URL)
    
    print("🔄 Dropping all existing tables...")
    Base.metadata.drop_all(bind=engine)
    
    print("✅ Creating fresh tables with correct schema...")
    Base.metadata.create_all(bind=engine)
    
    print("🎉 Database schema fixed successfully!")
    print("\nTables created:")
    print("  - users")
    print("  - vehicles")  
    print("  - service_centers (with available_slots JSONB column)")
    print("  - bookings")
    
    engine.dispose()

if __name__ == "__main__":
    reset_database()
