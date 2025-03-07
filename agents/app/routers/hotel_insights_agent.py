"""
Hotel Insights Agent

API Endpoint:
- `/hotel-insights-agent`: 
"""
from fastapi import APIRouter, Response, Request
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
import logging
import asyncio
import json
import re
from ..utils.agent_tools import get_hotel_reviews, get_hotel_amenities
from ..utils.publish_to_topic import produce
from ..utils.constants import AGENT_OUTPUT_TOPIC

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
model = ChatAnthropic(model='claude-3-5-haiku-20241022')

# Define tools to be used by the agent
tools = [get_hotel_reviews, get_hotel_amenities]

# This describes the role of the agent
SYSTEM_PROMPT = """
    You're a Hotel Insights Specialist at River Hotels, a global hospitality brand operating
    in over 40 countries. River Hotels is dedicated to delivering exceptional guest experiences
    through smart marketing and real-time personalization.

    Your role is to analyze the current hotel's offerings in relation to a guest's Customer
    Research Report and generate a Hotel Research Report. This report will highlight how the
    hotel's amenities, services, and experiences align with the guest's preferences, ensuring
    tailored recommendations and a personalized stay.
    """

# Configure a ReAct-based singular agent with the model, tools, and role
graph = create_react_agent(model, tools=tools, state_modifier=SYSTEM_PROMPT)

async def start_agent_flow(context):
    example_output = {
        "guest_id": "123456",
        "hotel_id": "RH-TOKYO-001",
        "hotel_name": "River Grand Tokyo",
        "location": "Tokyo, Japan",
        "hotel_and_guest_research_report": {
            "guest_preference_alignment": {
            "room_match_score": "90",
            "amenities_match_score": "85",
            "overall_alignment": "Strong match with the guest's past stay preferences."
            },
            "room_and_view_recommendation": {
            "recommended_room_type": "Executive Suite",
            "reason_for_recommendation": "Guest prefers King Bed and City View, and frequently stays in premium rooms.",
            "available_views": ["City View"],
            "bed_configuration": "One King Bed"
            },
            "amenities_and_services_match": {
            "matching_amenities": ["Spa", "Executive Lounge", "Gym"],
            "unavailable_amenities": ["Private Beach Access"],
            "recommended_alternatives": ["Rooftop Infinity Pool instead of Private Beach Access"]
            },
            "guest_experience_insights": {
            "potential_gaps": [
                {
                "issue": "Preferred amenity (Private Beach Access) is not available.",
                "suggestion": "Offer complimentary spa treatment or priority poolside cabana reservation."
                }
            ],
            "guest_sentiment_analysis": {
                "recent_reviews_match_guest_preferences": "true",
                "notable_review_highlights": [
                "Guests love the service in the Executive Lounge.",
                "High ratings for cleanliness and staff hospitality."
                ],
                "areas_for_improvement": [
                "Some guests found room service to be slow during peak hours."
                ]
            }
            },
            "personalized_stay_enhancements": [
            {
                "enhancement": "Complimentary Room Upgrade",
                "details": "Upgrade to a Suite with Lounge Access as a loyalty perk.",
                "justification": "Guest has redeemed room upgrades in the past and prefers premium accommodations."
            },
            {
                "enhancement": "Exclusive Spa Package",
                "details": "Offer 20% off on spa services during the stay.",
                "justification": "Guest frequently uses spa services and enjoys wellness amenities."
            }
            ]
        }
    }

    inputs = {"messages": [("user", f"""
      Using the guest's Customer Research Report, generate a Hotel Research Report that evaluates how the current
      hotel's offerings align with the guest's preferences and booking behavior. This report will help River Hotels
      deliver personalized recommendations, room assignments, and service enhancements tailored to the guest's expectations.

      Key Responsibilities:
      - Analyze the guest's preferences based on their Customer Research Report, including travel patterns, room choices, and amenity usage.
      - Evaluate the current hotel's offerings, identifying relevant room types, available services, and exclusive experiences.
      - Compare hotel reviews to past guest preferences, ensuring the stay aligns with expectations.
      - Highlight personalized recommendations, such as room upgrades, service add-ons, or special offers that enhance the guest experience.
      - Identify potential gaps, such as unavailable preferred amenities, and suggest alternatives to maintain high satisfaction.
      
      Use dedicated tools to enhance personalization and optimize engagement:
      - Hotel Reviews - Analyzes feedback from past guests to assess strengths, weaknesses, and areas for improvement.
      - Hotel Amenities - Retrieves information on available room types, dining options, spa services, fitness facilities, and other key offerings.
      
      Ensure a clear and actionable CTA, encouraging the lead to engage without high friction.
     
      Customer Research Report:
        {context}

      Expected Output - Hotel Research Report:
      The report should be concise, actionable, and aligned with the guest's needs, containing:

      - Guest Preference Alignment - How well the current hotel matches the guest's past stay preferences.
      - Room & View Recommendation - Best available options based on past room type, view, and bed configuration choices.
      - Amenities & Services Match - Available hotel amenities that align with the guest's usage history.
      - Guest Experience Insights - Any potential experience gaps and recommendations to improve satisfaction.
      - Personalized Stay Enhancements - Suggested perks, promotions, or personalized touches to maximize guest comfort and loyalty.

      This report will enable River Hotels to deliver a seamless, customized guest experience, increasing satisfaction and
      direct bookings while reinforcing brand loyalty.

      Output Format
      - The output must be strictly formatted as JSON, with no additional text, commentary, or explanation.
      - The JSON should exactly match the following structure:
         {json.dumps(example_output)}

      Failure to strictly follow this format will result in incorrect output.
      """)]}
    
    response = await graph.ainvoke(inputs)
    last_message_content = response["messages"][-1]
    content = last_message_content.pretty_repr()

    json_match = re.search(r"\{.*\}", content, re.DOTALL)

    if json_match:
        context = json_match.group()

        logger.info(f"Response from agent: {context}")

        # Write a message to the agent messages topic with the output from this agent
        produce(AGENT_OUTPUT_TOPIC, { "context": context })

@router.api_route("/hotel-insights-agent", methods=["GET", "POST"])
async def customer_insights_agent(request: Request):
    logger.info("customer-insights-agent")
    if request.method == "POST":
        data = await request.json()

        logger.info(data)

        for item in data:
            logger.info(item)

            context = item.get('context', "")

            logger.info(f"Here is the context: {context}")

            asyncio.create_task(start_agent_flow(context))

        return Response(content="Hotel Insights Agent Started", media_type="text/plain", status_code=200)
    

    # TODO: try GPT-4