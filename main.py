from mistralai import Mistral
from pydantic import BaseModel, Field, ValidationError
from typing import List, Dict
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
import os
load_dotenv()
api_key = os.getenv("API_KEY")
app = FastAPI()

# Jargon database as a dictionary
JARGON_DATABASE = {
    "10-K Report": "A comprehensive annual report filed by public companies to the SEC, detailing their financial performance.",
    "SEC (Securities and Exchange Commission)": "A U.S. federal agency responsible for enforcing securities laws and regulating the securities industry.",
    "Registrant": "The company that is registering securities or filing reports with the SEC.",
    "Fiscal Year": "A one-year period that companies use for accounting and financial reporting, differing from the calendar year.",
    "Nasdaq Global Select Market": "A tier of the Nasdaq stock market for companies meeting the highest standards for financial metrics and liquidity.",
    "Class A and Class C Stock": "Different classes of company stock, often with variations in voting rights or other privileges.",
    "I.R.S. Employer Identification Number (EIN)": "A unique number assigned by the Internal Revenue Service to identify a business entity for tax purposes.",
    "Well-Known Seasoned Issuer (WKSI)": "A category of company that meets specific SEC criteria, including market value and reporting history, allowing for streamlined filing processes.",
    "Interactive Data File": "A digital file containing financial data in a format (like XBRL) for easy processing and analysis by software.",
    "Traffic Acquisition Costs (TAC)": "Costs incurred by companies like Google to attract traffic to their websites, often through partnerships or paid referrals.",
    "Foreign Exchange Risk Management": "Strategies used to mitigate potential losses due to fluctuations in currency exchange rates.",
    "Other Income (Expense), Net (OI&E)": "Financial accounting term for non-operating income or expenses, such as interest income, investment gains, or losses.",
    "Hedging Activities": "Financial strategies used to offset potential losses in investments or currency fluctuations.",
    "Carbon Neutral": "Achieving a balance between emitting and offsetting carbon dioxide, often through renewable energy or carbon credits.",
    "Sustainability Bond": "Bonds issued to finance projects with environmental and social benefits, such as clean energy or affordable housing."
}
class JargonQuery(BaseModel):
    text: str

class JargonResponse(BaseModel):
    """
    Pydantic model for the output response from the Jargon Identifier tool.
    """
    identified_jargons: List[Dict[str, str]] = Field(..., description="A list of identified jargons and their descriptions.")


class JargonIdentifierTool:
    def __init__(self, api_key: str):
        """
        Initialize the Mistral client with the given API key.
        """
        self.client = Mistral(api_key=api_key)

    def identify_jargons(self, text: str, model="mistral-small-latest", max_tokens=500, temperature=0.7) -> JargonResponse:
        """
        Identify and return the jargons and their descriptions from the provided text.

        Args:
            text (str): Input query text from which to identify jargons.
            model (str): The model to use for chat completion.
            max_tokens (int): The maximum number of tokens in the response.
            temperature (float): The sampling temperature.

        Returns:
            JargonResponse: Identified jargons and their descriptions.
        """
        # Craft the input prompt for the chat model
        prompt = (
            "Identify and return only the following jargons and their descriptions [without any extra responses] in the provided text:\n\n"
            f"{text}\n\n"
            "Jargons are from the following Jargon Database[contains both jargons and their descriptions]:\n"
            + "\n".join([f"{term}: {desc}" for term, desc in JARGON_DATABASE.items()])
        )

        # Call the chat model
        response = self.client.chat.complete(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        # Parsing response into structured format
        
        identified_jargons = response.choices[0].message.content
        jargons_list = []

        for line in identified_jargons.split('\n'):
            i,j = line.split(':')
            jargons_list.append({
                        "term": i.strip(),
                        "description": j.strip()
                    })

        return JargonResponse(identified_jargons=jargons_list)

tool = JargonIdentifierTool(api_key='Sr72xWgjOEhEfTaUM4FcEebXmKVBP8tk')

@app.post("/identify-jargons", response_model=JargonResponse)
def identify_jargons(query: JargonQuery):
    try:
        result = tool.identify_jargons(query.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error identifying jargons: {str(e)}")

# Endpoint to process the main pipeline input
@app.get("/pipeline", response_model=JargonResponse)
def run_pipeline():
    # Example pipeline input
    main_pipeline_input = """The SEC has requested further clarification on the 10-K Report filed by the Registrant for the Fiscal Year. 
        This report, submitted to meet Nasdaq Global Select Market requirements, includes an update on Traffic Acquisition Costs (TAC) 
        and Foreign Exchange Risk Management strategies."""

    try:
        # Identify jargons from the predefined text
        result = tool.identify_jargons(main_pipeline_input)
        return result
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"Validation Error: {e.json()}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in pipeline: {str(e)}")