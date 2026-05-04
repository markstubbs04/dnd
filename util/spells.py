from openai import OpenAI
import json
import requests

############################################################################
####    THIS METHOD CALLS build_out_spell_list TO GET INFO ON ALL AVAILABLE
####    SPELLS, AND SPLITS THEM INTO SPELLS + CANTRIPS. THESE ARE SENT OFF
####    TO THE AI MODEL WHICH SELECTS THE SPELLS THAT WILL BEST FIT THE
####    CHARACTER. THE NUMBER OF SPELLS RETURNED IS ALSO THE MAXIMUM 
####    AMOUNT THAT THE CHARACTER CAN KNOW/PREPARE
def get_known_spells(client: OpenAI, character_sheet: object, prompt: str): 
    all_spells= character_sheet["Available Spells"]
    if len(all_spells)<1:
        return
    all_spells_spellbook = build_out_spell_list(all_spells)
    available_cantrips = list()
    available_spells = list()
    for spell in all_spells_spellbook:
        if spell["Level"] == 0: # Level 0 spells are cantrips
            available_cantrips.append(spell)
        else:
            available_spells.append(spell)

    character_sheet["Available Cantrips"] = available_cantrips
    character_sheet["Available Spells"]= available_spells

    available_cantrips_names = [cantrip["Name"] for cantrip in available_cantrips]
    available_spells_names = [spell["Name"] for spell in available_spells]

    spells_known = character_sheet["Spells Known"]
    cantrips_known = character_sheet["Cantrips Known"]
    
    system_prompt = """You are an expert Dungeon Master for the game Dungeons and Dragons.
    You exclusively use the 2014 ruleset when making decisions.
    You will be given a partially filled out character sheet for a Dungeons and Dragons character.
    Your job is to select which spells and cantrips best suit this character.
    ."""

    # CHARACTER_SHEET INCLUDES THE LIST OF KNOWN SPELLS AND CANTRIPS AFTER THEY HAVE BEEN BUILT UT, SO THE MODEL HAS CONTEXT FOR WHAT EACH SPELL DOES
    character_prompt = f"""This is a desription of the DnD character you are selecting spells for: <Character Description> {prompt} </Character Description>
    This is the partially filled out character sheet for the same character: {character_sheet}
    """

    spell_schema = {
            "name": "dnd_setup",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "spells":{
                        "type":"array",
                        "items":{"type":"string", "enum":available_spells_names},
                        "description":"This is the list of spells that best fit the given DnD character",
                        "maxItems":spells_known,
                        "minItems":spells_known,
                    },
                    "cantrips":{
                        "type":"array",
                        "items":{"type":"string", "enum":available_cantrips_names},
                        "description":"This is the list of cantrips that best fit the given DnD character",
                        "maxItems":cantrips_known,
                        "minItems":cantrips_known,
                    }
                },
                "required": ["spells","cantrips"],
                "additionalProperties": False
            }
        }

    model = "gpt-5-mini"
    spells_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": character_prompt},
        ]

    response = client.chat.completions.create(
            model=model,
            messages=spells_messages,
            response_format={"type": "json_schema", "json_schema":spell_schema},
            temperature=1.0
        )
    content = json.loads(response.choices[0].message.content)

    known_spells = content["spells"]
    known_cantrips = content["cantrips"]

    final_spells = list()
    for spell in available_spells:
        if spell["Name"] in known_spells:
            final_spells.append(spell)

    final_cantrips = list()
    for cantrip in available_cantrips:
        if cantrip["Name"] in known_cantrips:
            final_cantrips.append(cantrip)

    character_sheet["Prepared Spells"] = final_spells
    character_sheet["Prepared Cantrips"]= final_cantrips

#Get all potential spells that the character could have, including a description, range, and level
def build_out_spell_list(spells: list):
    spell_list = list()
    payload = {}
    headers = {
    'Accept': 'application/json'
    }

    for spell in spells:
        indexed_name = spell.lower().replace(" ","-").replace("/","-")
        
        url = f"https://www.dnd5eapi.co/api/2014/spells/{indexed_name}"
        flag = True
        while flag:
            response = requests.request("GET", url, headers=headers, data=payload)
            try:
                response_json = response.json()
                flag = False
            except requests.exceptions.JSONDecodeError:
                flag = True
        spell_info = {
            "Name": response_json["name"],
            "Description": response_json["desc"],
            "Range": response_json["range"],
            "Level": response_json["level"]
        }
        if "damage" in response_json:
            spell_info["Damage"] = response_json["damage"]
        spell_list.append(spell_info)
    return spell_list