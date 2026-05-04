from openai import OpenAI
import json

all_skills =["Acrobatics","Animal Handling","Arcana","Athletics","Deception","History","Insight","Intimidation","Investigation","Medicine","Nature","Perception","Performance","Persuasion","Religion","Sleight of Hand","Stealth","Survival"]
dex_skills = ["Acrobatics", "Sleight of Hand", "Stealth"]
str_skills = ["Athletics"]
int_skills = ["Arcana","History","Investigation","Nature","Religion"]
cha_skills = ["Deception","Intimidation","Performance","Persuasion"]
wis_skills = ["Animal Handling", "Insight", "Medicine", "Perception", "Survival"]



def get_skills(client: OpenAI, character_sheet: object, prompt: str): 
    system_prompt = """You are an expert Dungeon Master for the game Dungeons and Dragons.
    You exclusively use the 2014 ruleset when making decisions.
    Given the options for skill proficiencies for a character, choose two skill proficiencies that best suit that character."""

    character_prompt = f"""This is a desription of the DnD character you are selecting skill proficiencies for: <Character Description> {prompt} </Character Description>
    This is the partially filled out character sheet for the same character: {character_sheet}
    """
    skill_schema = {
            "name": "dnd_setup",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "skills":{
                        "type":"array",
                        "items":{"type":"string", "enum":list_skills(character_sheet["Available Skills"])},
                        "description":"This is the list of skills that are available to the given DnD character. Choose the values that best reflect the character.",
                        "maxItems":2,
                        "minItems":2,
                    },
                },
                "required": ["skills"],
                "additionalProperties": False
            }
        }

    # print("Potential Skills: ", list_skills(character_sheet["Available Skills"]))

    model = "gpt-5-mini"
    spells_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": character_prompt},
        ]

    response = client.chat.completions.create(
            model=model,
            messages=spells_messages,
            response_format={"type": "json_schema", "json_schema":skill_schema},
            temperature=1.0
        )
    content = json.loads(response.choices[0].message.content)
    known_skills = content["skills"]
    # print("Known Skills: ",known_skills)
    character_sheet["Skills"] = known_skills

def list_skills(availableSkills: str):
    skill_list = list()
    for skill in all_skills:
        if availableSkills.find(skill)!=-1:
            skill_list.append(skill)
    return skill_list


def build_skills(character_sheet: dict):
    char_skills = {skill: 0 for skill in all_skills}
    for skill in character_sheet["Skills"]:
        if skill in character_sheet["Skills"]:
            char_skills[skill]+=character_sheet["Proficiency Bonus"]
    for skill in dex_skills:
        char_skills[skill]+=character_sheet["Ability Score Modifiers"]["DEX"]
    for skill in str_skills:
        char_skills[skill]+=character_sheet["Ability Score Modifiers"]["STR"]
    for skill in int_skills:
        char_skills[skill]+=character_sheet["Ability Score Modifiers"]["INT"]
    for skill in cha_skills:
        char_skills[skill]+=character_sheet["Ability Score Modifiers"]["CHA"]
    for skill in wis_skills:
        char_skills[skill]+=character_sheet["Ability Score Modifiers"]["WIS"]
    character_sheet["Skills"] = char_skills
    