"""
Customer Insights Agent

API Endpoint:
- `/customer-insights-agent`: 
"""

from fastapi import APIRouter, Response, Request
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
import logging
import json
import asyncio
import re
from ..utils.agent_tools import get_travel_history, get_hotel_room_preferences, get_amenities_and_requests
from ..utils.publish_to_topic import produce
from ..utils.constants import AGENT_OUTPUT_TOPIC, PRODUCT_DESCRIPTION

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
model = ChatAnthropic(model='claude-3-5-haiku-20241022')

# Define tools to be used by the agent
tools = [get_travel_history, get_hotel_room_preferences, get_amenities_and_requests]

# This describes the role of the agent
SYSTEM_PROMPT = """
    You're a Customer Insights Specialist at River Hotels, a global hospitality brand operating
    in over 40 countries. River Hotels is dedicated to crafting exceptional guest experiences
    through smart marketing and real-time personalization.

    Your role is to analyze guest data and create Customer Research Reports that summarize
    individual hotel preferences based on past stays, booking behaviors, and engagement with
    River Hotels. Your insights will help marketing teams deliver tailored offers, personalized
    promotions, and relevant recommendations to guests in real time, enhancing loyalty and
    driving direct bookings.

    Focus on identifying patterns in travel history, preferred locations, amenities used, and
    special requests to build a comprehensive customer profile. Your analysis will empower River Hotels
    to engage each guest with the right message, at the right time, in the right place.
    """

# Configure a ReAct-based singular agent with the model, tools, and role
graph = create_react_agent(model, tools=tools, state_modifier=SYSTEM_PROMPT)

async def start_agent_flow(context):
    example_output = {
      "guest_id": "123456",
      "customer_research_report": {
        "travel_patterns": {
          "frequent_destinations": ["Tokyo, Japan", "Miami, USA", "Zermatt, Switzerland"],
          "trip_frequency_per_year": 3,
          "average_length_of_stay": "5 nights"
        },
        "room_preferences": {
          "preferred_bedding": "One King Bed",
          "preferred_number_of_guests": 2,
          "preferred_view": "Sea View"
        },
        "amenities_and_special_requests": {
          "frequently_used_amenities": ["Spa", "Gym", "Executive Lounge"],
          "common_special_requests": ["Late check-out", "Extra pillows"],
          "unique_guest_needs": ["Allergy-friendly bedding"]
        },
        "engagement_insights": {
          "loyalty_program_participation": "true",
          "tier_level": "Gold",
          "past_offer_redemptions": [
            {
              "offer_title": "Complimentary Room Upgrade",
              "redemption_date": "2023-08-05"
            },
            {
              "offer_title": "20% Off Spa Services",
              "redemption_date": "2022-12-22"
            }
          ],
          "responsiveness_to_promotions": {
            "opened_emails_percentage": "75",
            "clicked_booking_links_percentage": "50"
          }
        },
        "personalized_offer_recommendations": [
          {
            "offer_title": "Luxury Suite Upgrade for Your Next Stay",
            "offer_description": "Enjoy a complimentary upgrade to a luxury suite when booking 3+ nights.",
            "reason_for_recommendation": "Guest frequently redeems room upgrade offers and prefers premium accommodations."
          },
          {
            "offer_title": "Exclusive Spa Package",
            "offer_description": "Receive a free 30-minute massage with any spa booking.",
            "reason_for_recommendation": "Guest frequently uses spa services and previously redeemed a spa discount."
          }
        ]
      }
    }

    inputs = {"messages": [("user", f"""
      Using the guest's historical data, generate a Customer Research Report that summarizes their hotel preferences
      and booking behavior. This report will help River Hotels craft personalized marketing campaigns and real-time
      offers that align with the guest's preferences.

      Key Responsibilities:
      - Analyze past stays to identify patterns in the guest's travel habits, preferred locations, and frequency of visits.
      - Determine room preferences, including bed configuration, number of guests, and preferred room view (e.g., seaside vs. garden side).
      - Identify amenities usage, such as spa visits, gym access, dining choices, and any special requests made during past stays.
      - Assess engagement history, noting whether the guest has participated in loyalty programs, redeemed offers, or interacted with River Hotels' promotions.
      - Provide actionable insights to inform tailored marketing messages, ensuring offers are relevant and timely.
      
      Use dedicated tools to enhance personalization and optimize engagement:
      - Hotel History - Extracts relevant customer hotel history based on prior stays.
      - Room Preferences - Retrieves the guest's preferred bed setup, number of guests, and preferred view.
      - Amenities and Asks - Checks which amenities the guest has used previously and whether they've had special requests.
      
      Ensure a clear and actionable CTA, encouraging the lead to engage without high friction.
     
      Guest Profile Data:
        {context}

      Expected Output - Customer Research Report:
      The report should be concise and actionable, containing:

      - Travel Patterns - Frequent destinations, trip frequency, and length of stays.
      - Room Preferences - Bedding configuration, number of guests, view preferences.
      - Amenities & Special Requests - Services used, common requests, and any unique guest needs.
      - Engagement Insights - Loyalty program participation, past offer redemptions, and responsiveness to promotions.
      - Personalized Offer Recommendations - Suggestions for future promotions, upgrades, or exclusive perks based on past behavior.

      This report will enable River Hotels to deliver personalized, data-driven guest experiences that foster loyalty and maximize direct bookings.

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

@router.api_route("/customer-insights-agent", methods=["GET", "POST"])
async def customer_insights_agent(request: Request):
    logger.info("customer-insights-agent")
    if request.method == "POST":
        data = await request.json()

        for item in data:
            context = item.get('context', {})

            logger.info(f"Here is the context: {context}")

            asyncio.create_task(start_agent_flow(context))

        return Response(content="Customer Insights Agent Started", media_type="text/plain", status_code=200)