from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from datetime import datetime, timedelta
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import json
import os
import requests
import logging
from ..utils.constants import PRODUCT_DESCRIPTION

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

model = ChatAnthropic(model='claude-3-5-haiku-20241022', temperature=0.7, anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"))

def remove_empty_lines(text):
    return "\n".join([line for line in text.split("\n") if line.strip()])

@tool
def get_travel_history(customer_email):
    """
    Gets the customer travel history with the hotel chain.
    """

    logger.info(f"Finds relevant hotel history {customer_email}")

    example_output = {
        "guest_email": "email@email.com",
        "travel_history": [
            {
            "hotel_name": "River Grand Tokyo",
            "location": "Tokyo, Japan",
            "check_in": "2024-02-10",
            "check_out": "2024-02-15",
            "number_of_guests": 1,
            "stay_purpose": "Business"
            },
            {
            "hotel_name": "River Beach Resort",
            "location": "Miami, USA",
            "check_in": "2023-08-05",
            "check_out": "2023-08-12",
            "number_of_guests": 2,
            "stay_purpose": "Vacation"
            },
            {
            "hotel_name": "River Alpine Lodge",
            "location": "Zermatt, Switzerland",
            "check_in": "2022-12-20",
            "check_out": "2022-12-27",
            "number_of_guests": 4,
            "stay_purpose": "Holiday"
            }
        ]
        }

    prompt = f"""
      Take the customer email and generate believable but fake hotel history with 
      River Hotels, a global hospitality brand operating in over 40 countries.

      Customer
      {customer_email}

      The fake output should look like this:
      {json.dumps(example_output)}

      Only include the fake output. No additional description is needed.
    """

    data = model.invoke([{ "role": "user", "content": prompt }])
    return data

def get_hotel_room_preferences(customer_email):
    """
    Gets the customer hotel room preferences.
    """

    logger.info(f"Finds relevant hotel room preferences {customer_email}")

    example_output = {
        "guest_email": "email@email.com",
        "room_preferences": [
            {
            "room_type": "Deluxe King",
            "view_preference": "City View",
            "bed_configuration": "One King Bed"
            },
            {
            "room_type": "Oceanfront Suite",
            "view_preference": "Sea View",
            "bed_configuration": "Two Queen Beds"
            },
            {
            "room_type": "Luxury Chalet",
            "view_preference": "Mountain View",
            "bed_configuration": "One King Bed with Sofa Bed"
            }
        ]
        }

    prompt = f"""
      Take the customer email and generate believable but fake hotel room preferenes for
      the guest's three most popular choices for River Hotels, a global hospitality brand
      operating in over 40 countries.

      Customer
      {customer_email}

      The fake output should look like this:
      {json.dumps(example_output)}

      Only include the fake output. No additional description is needed.
    """

    data = model.invoke([{ "role": "user", "content": prompt }])
    
    return data

def get_amenities_and_requests(customer_email):
    """
    Gets the amenities and guest requests.
    """

    logger.info(f"Finds amenities and requests for the guest {customer_email}")

    example_output = {
        "guest_email": "email@email.com",
        "amenities_and_requests": [
            {
            "amenity": "Spa",
            "frequency": "Frequent"
            },
            {
            "amenity": "Executive Lounge Access",
            "frequency": "Occasional"
            },
            {
            "amenity": "Gym",
            "frequency": "Frequent"
            }
        ],
        "special_requests": [
            {
            "request": "Late check-out",
            "frequency": "Frequent"
            },
            {
            "request": "Extra pillows",
            "frequency": "Occasional"
            },
            {
            "request": "Room near elevator",
            "frequency": "Rare"
            }
        ]
        }

    prompt = f"""
      Take the customer email and generate believable but fake amenities and requests for
      for River Hotels, a global hospitality brand operating in over 40 countries.

      Customer
      {customer_email}

      The fake output should look like this:
      {json.dumps(example_output)}

      Only include the fake output. No additional description is needed.
    """

    data = model.invoke([{ "role": "user", "content": prompt }])
    
    return data

@tool
def get_hotel_reviews(hotel_id):
    """
    Gets a summary of the hotel's reviews.
    """

    logger.info(f"Finds the hotel reviews {hotel_id}")

    example_output = {
        "hotel_id": "RH-TOKYO-001",
        "hotel_name": "River Grand Tokyo",
        "location": "Tokyo, Japan",
        "average_rating": 4.3,
        "total_reviews": 256,
        "reviews": [
            {
            "review_id": "REV12345",
            "reviewer_type": "Business",
            "rating": 5,
            "review_text": "Fantastic stay! The executive lounge was excellent, and the staff was very accommodating.",
            "review_date": "2024-02-15",
            "common_themes": ["Service", "Lounge", "Business-friendly"],
            "sentiment": "Positive"
            },
            {
            "review_id": "REV67890",
            "reviewer_type": "Leisure",
            "rating": 3,
            "review_text": "Great location, but the room was smaller than expected. Breakfast options were limited.",
            "review_date": "2024-01-10",
            "common_themes": ["Location", "Room Size", "Dining"],
            "sentiment": "Neutral"
            },
            {
            "review_id": "REV54321",
            "reviewer_type": "Leisure",
            "rating": 2,
            "review_text": "The check-in process was slow, and my request for an early check-in was not honored.",
            "review_date": "2023-12-20",
            "common_themes": ["Check-in", "Service"],
            "sentiment": "Negative"
            }
        ]
        }

    prompt = f"""
      Take the hotel and generate believable but a fake summary of hotel reviews
      for River Hotels, a global hospitality brand operating in over 40 countries.

      Hotel:
      {hotel_id}

      The fake output should look like this:
      {json.dumps(example_output)}

      Only include the fake output. No additional description is needed.
    """

    data = model.invoke([{ "role": "user", "content": prompt }])
    
    return data

@tool
def get_hotel_amenities(hotel_id):
    """
    Gets a list of the hotel amenities.
    """

    logger.info(f"Finds hotel amenities {hotel_id}")

    example_output = {
        "hotel_id": "RH-TOKYO-001",
        "hotel_name": "River Grand Tokyo",
        "location": "Tokyo, Japan",
        "room_types": [
            {
            "room_type": "Deluxe King",
            "bed_configuration": "One King Bed",
            "view_options": ["City View", "Garden View"],
            "features": ["Smart TV", "Work Desk", "Mini Bar", "Rain Shower"]
            },
            {
            "room_type": "Executive Suite",
            "bed_configuration": "One King Bed",
            "view_options": ["City View"],
            "features": ["Private Lounge Access", "Large Work Desk", "In-Room Dining", "Spacious Living Area"]
            },
            {
            "room_type": "Oceanfront Suite",
            "bed_configuration": "Two Queen Beds",
            "view_options": ["Sea View"],
            "features": ["Private Balcony", "Luxury Bedding", "Whirlpool Tub", "Complimentary Breakfast"]
            }
        ],
        "amenities": {
            "general": ["Free Wi-Fi", "24/7 Concierge", "Airport Shuttle", "Pet-Friendly"],
            "wellness": ["Spa", "Gym", "Indoor Pool", "Yoga Classes"],
            "dining": ["Fine Dining Restaurant", "Buffet Breakfast", "Lobby Bar", "Room Service"],
            "business": ["Meeting Rooms", "Conference Center", "Co-Working Space"],
            "leisure": ["Rooftop Lounge", "Private Beach Access", "City Tour Packages"]
        },
        "special_services": [
            "Early Check-in & Late Check-out",
            "Personalized Concierge Services",
            "Complimentary Welcome Drinks",
            "Private Airport Transfers"
        ]
        }

    prompt = f"""
      Take the hotel and generate believable but a fake list of hotel amenities
      for River Hotels, a global hospitality brand operating in over 40 countries.

      Hotel:
      {hotel_id}

      The fake output should look like this:
      {json.dumps(example_output)}

      Only include the fake output. No additional description is needed.
    """

    data = model.invoke([{ "role": "user", "content": prompt }])
    
    return data


@tool
def get_available_offers(hotel_id):
    """
    Gets a list of the hotel offers.
    """

    logger.info(f"Finds hotel offers {hotel_id}")

    example_output = {
        "hotel_id": "RH-TOKYO-001",
        "hotel_name": "River Grand Tokyo",
        "location": "Tokyo, Japan",
        "available_offers": [
            {
            "offer_id": "OFFER123",
            "title": "Complimentary Room Upgrade",
            "description": "Enjoy a free upgrade to the next room category when you book a minimum 3-night stay.",
            "offer_type": "Room Upgrade",
            "eligibility": ["Loyalty Members", "Bookings of 3+ nights"],
            "validity_period": {
                "start_date": "2024-03-01",
                "end_date": "2024-06-30"
            },
            "discount_percentage": 0,
            "benefits": ["Free upgrade", "Priority check-in"],
            "terms_conditions": "Subject to availability. Cannot be combined with other promotions."
            },
            {
            "offer_id": "OFFER456",
            "title": "20% Off Spa Services",
            "description": "Relax and rejuvenate with 20% off all spa treatments during your stay.",
            "offer_type": "Wellness",
            "eligibility": ["All Guests"],
            "validity_period": {
                "start_date": "2024-02-15",
                "end_date": "2024-05-15"
            },
            "discount_percentage": 20,
            "benefits": ["Discounted spa treatments", "Complimentary herbal tea"],
            "terms_conditions": "Advance booking required. Not applicable to in-room massages."
            },
            {
            "offer_id": "OFFER789",
            "title": "Business Traveler Package",
            "description": "Exclusive business traveler perks, including free high-speed Wi-Fi and meeting room access.",
            "offer_type": "Business",
            "eligibility": ["Business Travelers", "Corporate Bookings"],
            "validity_period": {
                "start_date": "2024-04-01",
                "end_date": "2024-07-31"
            },
            "discount_percentage": 0,
            "benefits": ["Complimentary meeting room access", "Free high-speed Wi-Fi", "Late check-out"],
            "terms_conditions": "Valid for business travelers only. ID may be required at check-in."
            }
        ]
        }

    prompt = f"""
      Take the hotel and generate believable but a fake list of hotel on-going offers
      for River Hotels, a global hospitality brand operating in over 40 countries.

      Hotel:
      {hotel_id}

      The fake output should look like this:
      {json.dumps(example_output)}

      Only include the fake output. No additional description is needed.
    """

    data = model.invoke([{ "role": "user", "content": prompt }])
    
    return data