## DnD Character Creator

This application turns simple plaintext english into a fully fleshed out Dungeons and Dragons character sheet. The character sheet is downloadable to the user once the app has finished constriucting it. This app is my final project for CSC 7644: Applied LLM Development

## Key Features

- Returns a markdown document to the user containing all of the information in a typical DnD character sheet.

## Tech Stack and Architecture:

- Model: OpenAI gpt-5-mini
- APIs:
  1. https://5e-bits.github.io/docs/
  2. https://open5e.com/
- Primary Components:
  - Front end: Simple Streamlit app
  - Back end: DnD APIs (there is no storage of local data other than the character sheets)
  - Controller: Centrally consolidates information into the character sheet by calling the various RAG methods and LLM invocations.

## Setup Instructions

- Prerequisites:
  - Python 3.12
  - pip
  - OpenAI, requests, dotenv, streamlit
- How to install dependencies: pip install openai, requests, streamlit
- .env Setup:
  1. Create a new file named .env
  2. Insert: OPENAI_API_KEY={Your OpenAI API Key Value Here}

## Running the Application

1. Open the terminal with your virtual environment
2. In the root of the project directory, run streamlit run app.py
3. A window should open in your browser with the streamlit web app.
4. All you need to do now is input a character prompt and press the ENTER key for the application to begin constructing you a character sheet!!!

## Repository Organization

- ~/ : Contains the code to run the streamlit app, as well as the controller that organizes the LLM and RAG processes.
- ~/llm_primary : Contains the first and final calls to the LLM. These are the two LLM calls that are building out new information the most, with the rest of the application logic mainly dealing with choices and rule logic.
- ~/util : Contains all of the middle functions within the controller. These functions are used primarily to build out the character_sheet dictionary that contains all information about the created character. The functions within the util folder primarily make calls to the DnD APIs to gather information relevant to the created character's class, race, origin, and level. It then takes this info, parses through it, and potentially sends it through the LLM to make decisions about the character (which skill should I select from the list?, what weapon should I start with? etc.).

## Attributions and Citations:

- "API." D&D 5e SRD API, 5e-bits, https://5e-bits.github.io/docs/introduction. Accessed 3 May 2026.
- "API Docs." Open5e, https://open5e.com/api-docs. Accessed 3 May 2026.
