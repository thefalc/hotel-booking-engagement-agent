# Multi-Agent for Hotel Engagement and HTTP Sink APIs

This folder contains a Python app that supports given API endpoints. 

* `/api/customer-research-agent`: A ReAct agent that researches the customer to figure out the best way to engage.
* `/api/content-creation-agent`: A ReAct agent that creates engaging content for the customer.

Refer to the main README.md for detailed instructions in how to setup and configure this application.

## Configuring the application

You need to create a `.env` file with the following values:
* ANTHROPIC_API_KEY
* LANGCHAIN_TRACING_V2
* LANGCHAIN_API_KEY

As well as a `client.properties` file that contains properties to connect to Confluent.

## Running the application

From the your terminal, navigate to the `/agents` directory and enter the following command:

```shell
python -m venv env
source env/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```