from openai import OpenAI
import json
import requests

payload = {}
headers = {
  'Accept': 'application/json'
}


### UPDATED CHARACTER_SHEET WITH STARTING EQUIPMENT, MORE SKILL PROFICIENCIES, AND OTHER BASIC PROFICIENCIES. ALL DERIVED FROM THE CHARACTERS CLASS
def get_equipment(client: OpenAI, character_sheet: object, prompt: str): 
    skill_proficiencies = character_sheet["Skills"]
    normal_proficiencies = character_sheet["Proficiencies"]
    choices = get_choices(character_sheet["class"].lower())
    starting_equipment = choices["Starting Equipment"]
    proficiencies_choices = choices["Skill Proficiency Choices"]
    equipment_choices = choices["Starting Equipment Choices"]
    subclass_choices = character_sheet["Available Subclasses"]
    subclass_names = [subclass["name"] for subclass in subclass_choices]


    system_prompt = """You are an expert Dungeon Master for the game Dungeons and Dragons.
    You exclusively use the 2014 ruleset when making decisions.
    Given a DnD character and its character sheet, choose the equipment and proficiencies that best fit the character."""

    character_prompt = f"""This is a desription of the DnD character you are selecting skill proficiencies and equipment for: <Character Description> {prompt} </Character Description>
    This is the partially filled out character sheet for the same character: {character_sheet}
    """
    
    index = 0
    dynamic_schema = dict() ####DYNAMIC SCHEMA OOOOOOOOO AAAAAAAAAA
    # THESE LOOPS CREATE THE PROPERTIES OBJECT FOR THE EQUIPMENT SCHEMA, THIS ALLOWS FOR US TO ONLY CALL THE AI A SINGLE TIME FOR ALL OF THESE CHOICES
    for choice in equipment_choices:
        number_of_choices = choice["number_of_choices"]
        choice_name = "equipment_choice" + str(index)
        dynamic_schema[choice_name] = {
            "type": "array",
            "items":{"type":"string","enum":choice["choices"]},
            "description": "This is the list of equipment items that the given DnD character will start the game with. Choose the items that best fit the character.",
            "maxItems": number_of_choices,
            "minItems": number_of_choices,
        }
        index+=1
    index = 0
    for choice in proficiencies_choices:
        number_of_choices = choice["number_of_choices"]
        choice_name = "proficiency_choice" + str(index)
        dynamic_schema[choice_name] = {
            "type": "array",
            "items":{"type":"string","enum":choice["choices"]},
            "description": "This is the list of proficiencies that the given DnD character will start the game with. Choose the proficiencies that best fit the character.",
            "maxItems": number_of_choices,
            "minItems": number_of_choices,
        }
        index+=1

    #ADD IN SUBCLASS CHOICE
    dynamic_schema["subclass"]={
        "type": "string",
        "enum": subclass_names,
        "description": "This is the subclass for the provided DnD character. Pick the subclass that best fits the character.",
        "maxItems": 1,
        "minItems": 1,
    }

    equipment_schema = {
            "name": "dnd_setup",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": dynamic_schema,
                "required": list(dynamic_schema),
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
            response_format={"type": "json_schema", "json_schema":equipment_schema},
            temperature=1.0
        )
    content = json.loads(response.choices[0].message.content)
    all_chosen = list(dynamic_schema) #Full list of choices indexed
    for choice in all_chosen: #Loop through all choices sent to AI
        if choice in content: #Verify that the choice was returned by AI
            if choice.find("equipment") != -1: #If the choice was deciding starting equipment
                split_equipment(starting_equipment, content[choice]) #Add equipment to starting equipment using the split_equipment method that ensures each equipment item is separeted if it was combined for a choice
            elif choice == "proficiency_choice0": #If the choice decides skill proficiencies
                skill_proficiencies.extend(content[choice]) #Add skill proficiencies to the list, duplicates should be allowed for extra bonuses
            elif choice == "subclass": #If the choice was deciding subclass
                subclass = content[choice]
                subclass = next((item for item in character_sheet["Available Subclasses"] if item["name"] == subclass), None)
            else: #Rare edge case where other proficiency is decided
                normal_proficiencies.extend(content[choice]) #Add other proficiencies to general list
    
    character_sheet["Skills"] = skill_proficiencies
    character_sheet["Proficiencies"] = normal_proficiencies
    character_sheet["Starting Equipment"] = starting_equipment
    character_sheet["Subclass"] = subclass

# Split equipment string provided by LLM so that in case the string includes multiple equipment items they are each added to the dictionary separately as their own equipment items
# equipment_dict is the dictionary of equipment items for the character
# equipment_list is the list of equipment returned by a specific choice that the LLM made, it is often only 1-3 elements 
def split_equipment(equipment_dict: dict, equipment_list: list):
    #Split at the AND keyword that combines equipment string before prompting to the LLM
    print(equipment_list)
    for equipment_string in equipment_list:
        equipment_string_split = equipment_string.split(" and ")
        for equipment in equipment_string_split:
            equipment_words = equipment.split()
            word = equipment
            quantity = 1
            if len(equipment_words)>1:
                try:
                    quantity_str = equipment_words[0]
                    quantity = int(quantity_str)
                    word = " ".join(equipment_words[1:])
                    #Check to see if the remainding words are plural from previous transformation, if so, remove the added s
                    if word[-1] == 's':
                        word = word[:-1]
                except (ValueError, TypeError):
                    quantity = 1 #Do nothing if there is no quantity given
            if word in equipment_dict:
                equipment_dict[word] += quantity
            else:
                equipment_dict[word] = quantity


################################################################################################################
### THIS FUNCTION ITERATES THROUGH THE DIFFERENT CHOICES PROVIDED TO PLAYERS WHEN THEY SELECT THEIR CLASS
### IT RETURNS A DICTIONARY WITH A LIST OF CHOICES FOR PROFICIENCIES AND A LIST OF CHOICES FOR EQUIPMENT
### IT ALSO EXTRACTS STARTING EQUIPMENT FOR THE CHARACTER
def get_choices(char_class: str):
    choices_final = dict()
    class_url = f"https://www.dnd5eapi.co/api/2014/classes/{char_class}"

    response = requests.request("GET", class_url, headers=headers, data=payload)
    class_data = response.json()

    #First extract the given starting equipment from the response, this part does not deal with the choices logic
    equipment = dict()
    if "starting_equipment" in class_data:
        for equipment_item in class_data["starting_equipment"]:
            name = equipment_item["equipment"]["name"]
            quantity = equipment_item["quantity"]
            if name in equipment:
                equipment[name] += quantity
            else:  
                equipment[name] = quantity
                
    choices_final["Starting Equipment"] = equipment

    if "starting_equipment_options" in class_data:
        choices_final["Starting Equipment Choices"] = list()
        for choice in class_data["starting_equipment_options"]:
            number_of_choices = choice["choose"] #Number of items to select
            choices = list()
            options_set_type = choice["from"]["option_set_type"]
            if options_set_type == "options_array": #Check to see if the options are in array form
                options = choice["from"]["options"]
                for option in options:
                    option_type = option['option_type']
                    if option_type == "counted_reference": #Put name directly into options list if it is just a regular option
                        name = option["of"]["name"]
                        count = option["count"]
                        if count>1: #Check to see if there are multiple of this equipment item included in the choice, and modify the string to convey this information to LLM
                            name = str(count) + " " + name + "s"
                        choices.append(name)
                    elif option_type == "multiple": #When multiple items must be considered one option
                        items = option["items"]
                        grouped_items = list()
                        for item in items:
                            if item["option_type"] == "choice": #When a nested choice is given by the API
                                choice_url = item["choice"]["from"]["equipment_category"]["url"]
                                equpment_options = (get_equipment_list(choice_url))
                                grouped_items.extend(equpment_options)
                            elif item["option_type"] == "counted_reference": 
                                name = item["of"]["name"]
                                if item["count"]>1:
                                    grouped_items.append(str(item["count"]) + " " + name + "s")
                                else:
                                    grouped_items.append(name)
                            else:
                                print("Unknown Option Type ", item["option_type"])
                        final_grouped_name = " and ".join(grouped_items)
                        choices.append(final_grouped_name)
                    elif option_type == "choice": #When a further choice is given by the API (ex: select any martial melee weapon)
                        choice_url = option["choice"]["from"]["equipment_category"]["url"]
                        choices.extend(get_equipment_list(choice_url))
                    else:
                        print("Unknown Option Type ", option_type)
            elif options_set_type == "equipment_category": #Check to see if the option is an equipment catagory --> retrieve with function
                choice_url = choice["from"]["equipment_category"]["url"]
                choices.extend(get_equipment_list(choice_url))
            equipment_choice = {
                "number_of_choices": number_of_choices,
                "choices": choices
            }
            choices_final["Starting Equipment Choices"].append(equipment_choice)

    if "proficiency_choices" in class_data:
        choices_final["Skill Proficiency Choices"] = list()
        for choice in class_data["proficiency_choices"]:
            number_of_choices = choice["choose"] #Number of items to select
            options = choice["from"]["options"]
            choices = list()
            for option in options:
                if option["option_type"] == "choice":
                    items = option['choice']['from']['options']
                    items = [item['item']['name'] for item in items]
                    choices.extend(items)
                elif option["option_type"] == "reference":
                    skill = option["item"]["name"]
                    if option["item"]["name"].find("Skill: ") != -1:
                        skill = skill[7:] #String slicing to remove "Skill: " from the beginning of each skill proficiency option
                    choices.append(skill)
            skill_proficiency_choice = {
                "number_of_choices": number_of_choices,
                "choices": choices,
            }
            choices_final["Skill Proficiency Choices"].append(skill_proficiency_choice)
    return choices_final


### THIS METHOD TAKES IN A URL GIVEN BACK BY THE API AND RETURNS THE EQUIPMENT LISTS THAT IT GIVES
def get_equipment_list(url: str):
    equipment_url = "https://www.dnd5eapi.co" + url
    response = requests.request("GET", equipment_url, headers=headers, data=payload)
    equipment_data = response.json()
    equipment_choices = equipment_data['equipment']
    equipment_choices = [equipment['name'] for equipment in equipment_choices]
    return equipment_choices