from openai import OpenAI
import json
from dotenv import load_dotenv
import os
import initial
import build_character
import spells
import skills
import equipment
import weapons
import final


load_dotenv()

def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY not found in environment variables")
    return OpenAI(api_key=api_key)

link_prompt = """Link from the Legend of Zelda series. He typically wields the Master sword, Hylian shield, and fairy bow. He is well adept at horseback riding and has fought dozens of different
monsters in order to save Hyrule from ruin and save Princess Zelda.
"""

spongebob_prompt = """Spongebob lives in a pineapple under the sea. He is best friends with Patrick who he enjoys jellyfishing with.
Spongebob works as a fry cook at the Krusty Krab where he is the best fry cook in all of Bikini Bottom. He always has a smile on his face and tries to make the most out
of any situation."""

def main(prompt):
    client = get_openai_client()
    character_sheet = initial.create_character(client,prompt)
    print("Initial complete")
    character_sheet = build_character.build_character(character_sheet)
    print("Build Character complete")
    num_spells_known = character_sheet["Spells Known"]

    if num_spells_known>0:
        spells.get_known_spells(client,character_sheet,prompt)
        print("Spells complete")
    skills.get_skills(client, character_sheet, prompt)
    print("Skills complete")
    equipment.get_equipment(client,character_sheet,prompt)
    print("Equipment complete")
    weapons.getWeaponsandArmor(character_sheet)
    print("Armor complete")
    skills.build_skills(character_sheet)
    print("Skills complete 2")
    
    if "Available Subclasses" in character_sheet:
        del character_sheet["Available Subclasses"]
    if "Available Spells" in character_sheet:
        del character_sheet["Available Spells"]
    if "Available Cantrips" in character_sheet:
        del character_sheet["Available Cantrips"]
    if "ASI List" in character_sheet:
        del character_sheet["ASI List"]
    if "Available Skills" in character_sheet:
        del character_sheet["Available Skills"]
    if "Ability Scores Bonus" in character_sheet:
        del character_sheet["Ability Scores Bonus"]
    if "Equipment (Race)" in character_sheet:
        del character_sheet["Equipment (Race)"]
    
    json_name = f"{character_sheet['name']}.json"
    with open(file=json_name,mode="w",encoding='utf-8',errors='ignore') as file:
        character_sheet_pretty = json.dumps(character_sheet, indent=4)
        file.write(character_sheet_pretty)


    final_output = final.create_character(client,character_sheet)
    print("Final complete")

    file_name = f"{character_sheet['name']}.md"
    with open(file=file_name,mode="w",encoding='utf-8',errors='ignore') as file:
        file.write(final_output)

    return file_name
    



























if __name__ == "__main__":
    main()