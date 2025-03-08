# A  Multi-Agent System for Hotel Customer Engagement
This application uses LangChain, Anthropic's Claude, and Confluent to create a hotel booking engagement agent.

The multi-agent system automates and personalizes an email campaign to someone who is on a hotel website, looked at bookings, but hasn't booked. Apache Flink and external model inference is used to orchestrate communication with a series of AI agents, each responsible for a specific task in the lead management and outreach process.

The system is event-driven, leveraging [Confluent Cloud's](https://www.confluent.io/) as the backbone for real-time communication, orchestration, and data flow between agents. 

At a high level, the initial system consists of the following key agents:

* Customer Insights Agent: Based on click data for a hotel booking page, researches the customer and generates a report that can be used to personalize engagement
* Hotel Insights Agent: Uses the enriched customer data to look up hotel specific information and generate a combined report.
* Content Creation Agent: Uses the combined report to generate an email to send to the customer.

Each agent is designed to run as a microservice with a brain that communicates via event streams in Confluent Cloud, allowing for real-time processing and asynchronous handoffs between agents.

The diagram below illustrates how these agents interact through event-driven messaging.

<p align="center">
  <img src="/images/architecture-diagram.png" />
</p>

## How it works
All messages to and from agents are stored in the topic `agent_messages`. Adding a new message here with click and hotel data will start the agent flow.

# Project overview
Kafka and Flink, running on Confluent Cloud, are used to move data around between services.

The `agents` application is a Python app that includes routes to the different agents and API endpoints called by Confluent to consume messages from Kafka topics. These API endpoints take care of all the AI magic to generate a meal plan and grocery list.

# What you'll need
In order to set up and run the application, you need the following:

* [Node v22.5.1](https://nodejs.org/en) or above
* [Python 3.10](https://www.python.org/downloads/) or above
* A [Confluent Cloud](https://www.confluent.io/) account
* A [Claude](https://www.anthropic.com/claude) API key
* A [LangChain](https://www.langchain.com/) API key

## Getting set up

### Get the starter code
In a terminal, clone the sample code to your project's working directory with the following command:

```shell
git clone https://github.com/thefalc/hotel-booking-engagement-agent.git
```

### Setting up Confluent Cloud

The hotel customer engagement agent uses Confluent Cloud to move and operate on data in real-time and handle the heavy lifting for communication between the agents.

### Create the topics for agent communication and routing

In your Confluent Cloud account.

* Go to your Kafka cluster and click on **Topics** in the sidebar.
* Name the topic as `agent_messages`.
* Set other configurations as needed, such as the number of partitions and replication factor, based on your requirements.
* Go to **Schema Registry**
* Click **Add Schema** and select **agent_messages** as the subject
* Choose JSON Schema as the schema type
* Paste the schema from below into the editor

```json
{
  "properties": {
    "context": {
      "connect.index": 0,
      "oneOf": [
        {
          "type": "null"
        },
        {
          "type": "string"
        }
      ]
    }
  },
  "title": "Record",
  "type": "object"
}
```

* Save the schema

Next, we are going to create a topic that will contain the agent messages along with the agent name. This will be used for routing the message to the indicated agent.

* Go to your Kafka cluster and click on **Topics** in the sidebar.
* Name the topic as `agent_predictions`.
* Set other configurations as needed, such as the number of partitions and replication factor, based on your requirements.
* Go to **Schema Registry**
* Click **Add Schema** and select **agent_predictions** as the subject
* Choose JSON Schema as the schema type
* Paste the schema from below into the editor

```json
{
  "properties": {
    "agent_name": {
      "connect.index": 0,
      "oneOf": [
        {
          "type": "null"
        },
        {
          "type": "string"
        }
      ]
    },
    "context": {
      "connect.index": 1,
      "oneOf": [
        {
          "type": "null"
        },
        {
          "type": "string"
        }
      ]
    }
  },
  "title": "Record",
  "type": "object"
}
```

* Save the schema

### Create the HTTP sink connectors for all agents

Next, we have to setup the routing from the `agent_predictions` topic to the agent endpoints. We will do this by creating a new HTTP sink connector for each agent and filter messages using a Single Message Transform to only send messages matching the agent's name to the agent endpoint.

* Under **Connectors**, click **+ Add Connector**
* Search for "http" and select the **HTTP Sink** connector
* Select the **agent_predictions** topic
* In **Kafka credentials**, select **Service account** and use you existing service account and click **Continue**
* Enter the URL for where the `customer-insights-agent` endpoint is running under the `agents` folder. This will be
similar to `https://YOUR-PUBLIC-DOMAIN/api/customer-insights-agent`. If running locally, you can use [ngrok](https://ngrok.com/)
to create a publicly accessible URL. Click **Continue**
* Under **Configuration**, select **JSON_SR** and click **Continue**
* For **Sizing**, leave the defaults and click **Continue**
* Name the connector `customer-insights-agent-sink` and click **Continue**

Once the connector is created, under the **Settings** > **Advanced configuration** make sure the **Request Body Format** is set to **json**.

Additionally, in **Settings**, under **Transforms**, click **Edit**.

* Select **Filter$Value** for **Transform type**
* In **Filter Condition**, enter `$[?(@.agent_name == 'Customer Insights Agent')]`
* Select **include** in **Filter Type**
* Click **Save Changes**

Repeat these steps for agents for the Hotel Insights Agent, and Content Creation Agent.

### Flink SQL and LLM setup

Flink SQL is used to copy leads into `agent_messages` and map all `agent_messages` into `agent_predictions` using a LLM to determine where to map messages.

#### Connecting Flink to OpenAI

To extract dynamically map new messages to the agents available, we are going to use external model inference in Flink to call a model to dynamically determine the mapping. The first step is to create a connection between Flink and OpenAI (or whatever model you're using).

In your terminal, execute the following.

```bash
confluent flink connection create openai-connection \
--cloud aws \
--region us-east-1 \
--type openai \
--endpoint https://api.openai.com/v1/chat/completions \
--api-key REPLACE_WITH_YOUR_KEY
```

Make sure the region value matches the region for where you're running Confluent Cloud.

#### Flink SQL setup for copying leads

Flink SQL is used to copy leads into `agent_messages` and map all `agent_messages` into `agent_predictions` using a LLM to determine where to map messages.

First, let's write the Flink job to create the model.

* In your Kafka cluster, go to the **Stream processing** tab
* Click **Create workspace**
* Enter the following SQL

```sql
CREATE MODEL `agent_orchestrator`
INPUT (text STRING)
OUTPUT (response STRING)
WITH (
  'openai.connection'='openai-connection',
  'provider'='openai',
  'task'='text_generation',
  'openai.model_version' = 'gpt-4',
  'openai.system_prompt' = 'Your job is to map the prompt to an agent based on the highest
   probability match between the prompt and agent. Strictly adhere to the defined Input and
   Example Input for the agents below and ensure that only structured inputs matching the
   format are considered.

   Agent Name: Customer Insights Agent
   Description: Uses customer interest in a hotel based on click data for bookings to create a research report about the customer.
   Input: Customer email, hotel ID, and the activity time.

   Agent Name: Hotel Insights Agent
   Description: Uses a customer research report and information about the hotel to create an engagement plan.
   Input: A structured customer research report.

   Agent Name: Content Creation Agent
   Description: Uses a customer and hotel research report to create personalized content to engage the customer.
   Input: A combined hotel and customer research report.

   Rules for Classification:
   Reject emails and marketing messages:

   If the input contains "to", "subject", and "body", respond with DONE.
   If the input resembles a marketing message (e.g., promotional offers, greetings, call-to-action links), respond with DONE.
   Strict input validation for agents:

   The Customer Insights Agent requires:
   Customer email, hotel ID, and activity time in the structured format.
  
   The Hotel Insights Agent requires:
   A structured customer research report, not free-text content.

   The Content Creation Agent requires:
   A combined structured hotel and customer research report.
  
   If the input does not contain structured research fields (e.g., guest_id, hotel_research_report, travel_patterns, trip_frequency_per_year, etc.), respond with DONE.
   Any output other than a valid agent name or DONE is incorrect.'
);
```

* Click **Run**

#### Create the Flink job to act as the orchestrator

* In the same workspace, insert the following SQL

```sql
INSERT INTO agent_predictions
SELECT 
    CAST(NULL AS BYTES) AS key,
    context,
    prediction.response as agent_name
FROM (
    SELECT 
        context
    FROM agent_messages
) AS subquery
CROSS JOIN 
    LATERAL TABLE (
        ml_predict('agent_orchestrator', context)
    ) AS prediction;
```

* Click **Run**

### Run the application

1. In a terminal, navigate to your project directory. Run the app with the following command:

```shell
python -m venv env
source env/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
2. In Confluent Cloud, go to the `agent_messages` topic and click **Action** > **Product new message**.
3. In the **Value** field, paste the sample data below and click **Produce**.
```json
{
  "context": "Customer Email: | hoyt.huel@gmail.com | Hotel ID: | H10000382 | Activity Time: | 2025-03-01 11:26:44.230 | Hotel Name: | River Nice Luxury Lodge | City: | Nice | Similar Hotels: | River Nice Spa | Reviews: | The hotel’s dedication to sustainability, evident in its operations and decor, added a meaningful layer to our stay.||| The custom-designed furniture and artwork throughout the hotel celebrated local craftsmanship, adding to the unique ambience.||| Walking through the hotel grounds felt like strolling through a meticulously designed botanical garden, enhancing our sense of tranquility.||| The hotel's music selection in the common areas created an uplifting and welcoming atmosphere. It was the perfect backdrop to our luxurious stay.||| Having access to a well-equipped exercise room made my stay even more enjoyable. It was great to have the option to unwind with some physical activity.||| The hotel's spa was a haven of relaxation, offering a serene escape with top-notch services. Coupled with the elegant ambiance, it was the highlight of our stay.||| The hotel's spa was a haven of relaxation, offering a serene escape with top-notch services. Coupled with the elegant ambiance, it was the highlight of our stay.||| The hotel's proximity to major tourist attractions was incredibly convenient. Being able to walk to iconic landmarks and museums enriched our travel experience, saving us time and allowing for spontaneous explorations. This location is ideal for travelers eager to immerse themselves in the city's culture. | LLM Response: | Here's a Python function that summarizes the reviews into a single sentence:\n\n```python\ndef summarize_reviews(reviews):\n    \"\"\"\n    Summarizes hotel reviews into a concise summary sentence.\n\n    Args:\n    reviews (str): A string containing one or more hotel reviews, delimited by '|||'.\n\n    Returns:\n    str: A summary sentence highlighting what customers liked most about the hotel.\n    \"\"\"\n\n    # Handle the case where reviews is an empty string\n    if not reviews.strip():\n        return \"NO REVIEWS FOUND.\"\n\n    # Split the reviews into a list\n    reviews = reviews.split('|||')\n\n    # Initialize an empty set to store keywords\n    keywords = set()\n\n    # Initialize an empty dictionary to store the frequency of keywords\n    keyword_frequency = {}\n\n    # Process each review\n    for review in reviews:\n        # Remove leading and trailing whitespace\n        review = review.strip()\n\n        # Split the review into sentences\n        sentences = review.split('. ')\n\n        # Process each sentence\n        for sentence in sentences:\n            # Remove punctuation and convert to lowercase\n            sentence = sentence.lower().replace('.', '').replace(',', '').replace('!', '')\n\n            # Tokenize the sentence into words\n            words = sentence.split()\n\n            # Iterate over the words"
}
```
4. Wait for the agent flow to complete. If everything goes well, after a few minutes you'll have a personalized email in the `agent_message` topic.