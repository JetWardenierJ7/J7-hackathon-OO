import os
from mistralai import Mistral, SDKError
from dotenv import load_dotenv
import time
load_dotenv()

MISTRAL_API_KEY = os.environ["MISTRAL_API_KEY"]

class CL_Mistral_Connection:
    """This class is responsible for generating embeddings using the Mistral API"""

    def __init__(self, model="mistral-embed"):
        """This is constructor that initializes a CL_Openai_Embeddings object"""

        api_key = MISTRAL_API_KEY
        self.client = Mistral(api_key=api_key)
        self.model = model
        

    def generate_embedding(self, input_text):
        """Generates a 1024 dimension embedding over input text

        :param input_text: The text used to generate an embedding over
        :returns: Returns a 1024 dimensions embedding
        :rtype: List
        :raises TypeError: Expected input_text to be a string, but got something else
        """


        if not isinstance(input_text, str):
            raise TypeError(
                f"Expected the input_text variable to be a string, but got:  {type(input_text)}"
            )

        try:
            response = self.client.embeddings.create(
                    model=self.model,
                    inputs=[input_text],
            )
        except SDKError as e:
            print("Rate limit exceeded.")
            time.sleep(3)
            print("Retrying...")
            response = self.client.embeddings.create(
                    model=self.model,
                    inputs=[input_text],
            )
        
        return response.data[0].embedding
    
    def generate_completion(self, prompt, temperature=0.7, max_tokens=256, model="ministral-3b-latest"):
        """Generates a text completion for a given prompt using the Mistral completions endpoint.

        :param prompt: The user prompt to send to the model
        :param temperature: Sampling temperature
        :param max_tokens: Maximum number of tokens to generate
        :returns: Generated completion text
        :rtype: str
        """

        if not isinstance(prompt, str):
            raise TypeError(f"Expected prompt to be a string, but got: {type(prompt)}")

        try:
            response = self.client.chat.complete(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except SDKError as e:
            print("Error from SDK:", str(e))
            time.sleep(3)
            print("Retrying completion...")
            response = self.client.chat.complete(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )

        return response.choices[0].message.content
    