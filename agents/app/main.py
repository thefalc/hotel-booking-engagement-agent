from fastapi import FastAPI
from app.routers import customer_insights_agent, hotel_insights_agent, content_creation_agent

app = FastAPI()

# Include the routers
app.include_router(customer_insights_agent.router, prefix="/api", tags=["Customer Insights Agent"])
app.include_router(hotel_insights_agent.router, prefix="/api", tags=["Hotel Insights Agent"])
app.include_router(content_creation_agent.router, prefix="/api", tags=["Content Creation Agent"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the API!"}