"""
Content Creation Agent

API Endpoint:
- `POST /content-creation-agent`: Processes new lead data and triggers research workflows.

"""
from fastapi import APIRouter, Response, Request
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
import asyncio
import logging
import json
import re
from ..utils.agent_tools import get_available_offers
from ..utils.publish_to_topic import produce
from ..utils.constants import AGENT_OUTPUT_TOPIC

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
model = ChatAnthropic(model='claude-3-5-haiku-20241022')

# Define tools to be used by the agent
tools = [get_available_offers]

SYSTEM_PROMPT = """
    You're a Content Creation Specialist at River Hotels, a global hospitality brand
    operating in over 40 countries. River Hotels is dedicated to crafting exceptional
    guest experiences through smart marketing and real-time personalization.

    Your role is to take the combined Customer and Hotel Research Report and generate a
    compelling, personalized email designed to encourage the guest to book their next stay.
    This email should be engaging, tailored, and action-driven, highlighting why the guest
    should choose this specific River Hotels location based on their preferences and past stays.
    """

graph = create_react_agent(model, tools=tools, state_modifier=SYSTEM_PROMPT)

def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()

async def start_agent_flow(context):
    example_output = {
        "to": "Lead's Email Address",
        "subject": "Example Subject Line",
        "body": "Example Email Body"
    }

    inputs = {"messages": [("user", f"""
      Using the combined Customer and Hotel Research Report, craft a personalized, engaging email
      that encourages the guest to book their next stay at River Hotels. This email should highlight
      how the hotel aligns with their preferences and showcase special offers or incentives to
      drive conversion.

      Key Responsibilities:
        - Personalize the email using insights from the guest's past stays, preferred room types, and amenities usage.
        - Highlight relevant hotel features that match the guest's preferences, such as room upgrades, exclusive services, or special experiences.
        - Leverage available offers to create urgency and excitement around the booking opportunity.
        - Ensure a warm and inviting tone that makes the guest feel valued and recognized.
        - Include a strong call-to-action (CTA) that encourages immediate booking, making the process seamless.
                            
      Use dedicated tools to enhance personalization and optimize engagement:
      - Get Available Offers - Retrieves current promotions, room upgrades, and special perks at the selected hotel.
      
      Ensure a clear and actionable CTA, encouraging the lead to engage without high friction.

      Input Data:               
        {context} 
        
      Expected Output - Personalized Booking Email:
      The email should be concise, compelling, and conversion-focused, containing:

      - Personalized Greeting - Address the guest warmly by name.
      - Tailored Introduction - Reference their past stays and highlight why this hotel is a great fit.
      - Highlighted Perks - Showcase relevant room types, amenities, and special services based on the guest's preferences.
      - Exclusive Offer or Incentive - Mention an available promotion or loyalty benefit.
      - Strong Call-to-Action (CTA) - Encourage immediate booking with a clear next step (e.g., “Reserve Now” button).

      This email will help River Hotels increase direct bookings, enhance guest engagement, and foster long-term loyalty.

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

@router.api_route("/content-creation-agent", methods=["GET", "POST"])
async def content_creation_agent(request: Request):
    print("content-creation-agent")
    if request.method == "POST":
        data = await request.json()

        logger.info(data)

        for item in data:
            logger.info(item)

            context = item.get('context', "")

            logger.info(f"Here is the context: {context}")

            asyncio.create_task(start_agent_flow(context))

        return Response(content="Content Creation Agent Started", media_type="text/plain", status_code=200)