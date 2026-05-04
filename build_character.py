import json
import requests

payload = {}
headers = {
  'Accept': 'application/json'
}

# Primary function that builds out character_sheet with new information about the class/race, and also consolidates information that is useful for later
# calls to the LLM and for later decision making (Spells Known, ASI List, Available Skills)
def build_character(character_sheet: dict) -> dict:
    char_class = character_sheet["class"]
    level = character_sheet["level"]
    race = character_sheet["race"]
    origin = character_sheet["origin"]

    classes = ["Barbarian","Bard","Cleric","Druid","Fighter","Monk","Paladin","Ranger","Rogue","Sorcerer","Warlock","Wizard"]
    if char_class not in classes:
        print("Invalid class: ", char_class)
        raise KeyError
    races = ["Dragonborn","Dwarf","Elf","Gnome","Half-Elf","Half-Orc","Halfling","Human","Tiefling"]
    if race not  in races:
        print("Invalid race: ", race)
        raise KeyError
    origins = ["Acolyte","Artisan","Charlatan","Con Artist","Criminal","Entertainer","Exile", "Farmer","Folk Hero","Gambler","Guildmember","Hermit","Marauder","Noble","Outlander","Sage","Sailor","Scoundrel","Trader","Urchin"]
    if origin not in origins:
        print("Invalid origin: ", origin)
        raise KeyError
    if not (level<=20 and level>=1):
        print("Invalid level: ", level)
        raise KeyError

    available_spells = spells(char_class,level)
    active_proficiencies, saving_throws = proficiencies(char_class,race)
    general_info_dict = general_class_info(char_class,level)
    active_traits = traits(race)
    available_skills, equipment = skills_and_equipment(origin)
    speed, asi_list = get_race_stats(race)

    ability_scores = assign_ability_scores(character_sheet["abilityScores"], general_info_dict["Ability Scores Bonus"], asi_list) #New abilityScores dictionary replaces the list so that way each ability has a score
    character_sheet_updates = {
        "Available Spells": available_spells,
        "Spells Known":general_info_dict["Spells Known"],
        "Cantrips Known":general_info_dict["Cantrips Known"],
        "Proficiencies": active_proficiencies,
        "Traits":active_traits,
        "Features":general_info_dict["Features"],
        "Available Skills":available_skills,
        "Proficiency Bonus":general_info_dict["Proficiency Bonus"],
        "Saving Throws":saving_throws_dict(saving_throws,level),
        "abilityScores":ability_scores,
        "Ability Score Modifiers": get_ability_score_modifiers(ability_scores),
        "Passive Wisdom (Perception)": get_passive_wisdom(ability_scores),
        "Speed": speed,
        "ASI List": asi_list,
        "Ability Scores Bonus": general_info_dict["Ability Scores Bonus"],
        "Spellcasting": general_info_dict["Spellcasting"],
        "Equipment (Race)": equipment,
        "Available Subclasses": general_info_dict["Subclasses"],
        "Subclass Name":general_info_dict["Subclass Name"],
        "Spellcasting Ability": general_info_dict["Spellcasting Ability"],
        "Hit Dice": general_info_dict["Hit Dice"],
    }

    final = character_sheet | character_sheet_updates
    return final

#Get all spells for character's current level
def spells(char_class: str, level: int) -> list:
    #####################  SPELLS AVAILABLE AT CURRENT LEVEL  ###################################
    spells_url = f"https://www.dnd5eapi.co/api/2014/classes/{char_class.lower()}/levels/{level}/spells"

    response = requests.request("GET", spells_url, headers=headers, data=payload)
    spells = response.json()["results"]
    learnable_spells = list()
    for spell in spells:
        learnable_spells.append(spell['name'])

    # print("Learnable Spells: ", learnable_spells)
    return learnable_spells

# Get all proficiencies related to the characters class and race
def proficiencies(char_class: str, race: str):
    #####################  PROFICIENCIES  ###################################
    # PROFICIENCIES FROM CLASS
    proficiencies_url = f"https://www.dnd5eapi.co/api/2014/classes/{char_class.lower()}/proficiencies"
    response = requests.request("GET", proficiencies_url, headers=headers, data=payload)
    proficiencies_raw = response.json()["results"]
    # PROFICIENCIES FROM RACE
    proficiencies_url = f"https://www.dnd5eapi.co/api/2014/races/{race.lower()}/proficiencies"
    response = requests.request("GET", proficiencies_url, headers=headers, data=payload)
    proficiencies_raw += response.json()["results"]

    saving_throws = list()

    proficiencies = list()
    for proficiency in proficiencies_raw:
        if proficiency['name'].find("Saving Throw: ") != -1:
            saving_throws.append(proficiency['name'][-3:])
        else:
            proficiencies.append(proficiency['name'])

    # print("Proficiencies: ", proficiencies)
    # print("Saving throws: ", saving_throws)
    return proficiencies, saving_throws

############### SKILL PROFICIENCY CAN BE PULLED FROM THE CLASS PATH FROM THE ORIGINAL API
############### THE SAME API PATH GIVES STARTING EQUIPMENT AS WELL AS CHOICES FOR STARTING EQUIPMMENT, SKILL PROFICIENCY SELECTION, AND TOOL PROFICIENCY SELECTION
############### TODO: CREATE A WAY TO EXTRACT ALL OF THESE CHOICES AND SEND THEM OFF TO API
def general_class_info(char_class: str, level: int) -> dict:
    ######################  GENERAL INFO FOR LEVEL + CLASS  ######################
    level_url = f"https://www.dnd5eapi.co/api/2014/classes/{char_class.lower()}/levels"
    response = requests.request("GET", level_url, headers=headers, data=payload)
    level_resources = response.json()
    # print(level_resources)

    index = 0
    features = list()

    #LOOP THROUGH ALL LEVELS UP TO CURRENT LEVEL TO GET ALL POSSIBLE FEATURES
    while index<level and index<len(level_resources):
        for feat in level_resources[index]["features"]:
            # IF THE CHARACTER HAS A FEAT TO IMPROVE THEIR ABILITY SCORES, KEEP TRACK OF IT BUT DONT ADD IT TO THE FEATS LIST BECAUSE IT WILL NOT MAKE SENSE
            if feat['name'] != "Ability Score Improvement":
                features.append(feat['name'])
        index+=1
    # print("Features: ", features)

    # PROFICIENCY BONUS
    proficiency_bonus = level_resources[level]["prof_bonus"]
    # print("Proficiency Bonus: ", proficiency_bonus)
    # KEEPS TRACK OF HOW MANY ABILITY SCORES YOU CAN INCREASE
    ability_scores_bonus = level_resources[level]["ability_score_bonuses"]
    # print("Ability Scores Bonus: ", ability_scores_bonus)

    # CHECK FOR SPELLCASTING INFO, SOME CLASSES OMIT THIS
    spells_known = 0
    spellcasting_info = {}
    cantrips_known = 0
    if "spellcasting" in level_resources[level]:
        spellcasting_info = level_resources[level]["spellcasting"]
        # print("Spellcastin Info: ", spellcasting_info)
        if "spells_known" in spellcasting_info:
            spells_known = spellcasting_info['spells_known'] #THIS IS THE NUMBER OF KNOWN SPELLS
        if "cantrips_known" in spellcasting_info:
            cantrips_known = spellcasting_info['cantrips_known'] #THIS IS THE NUMBER OF KNOWN CANTRIPS


    class_info_url = f"https://api.open5e.com/v1/classes/?name={char_class}"
    response = requests.request("GET", class_info_url, headers=headers, data=payload)
    response = json.loads(response.text)

    class_info=response["results"][0]
    hit_dice = class_info["hit_dice"]
    spellcasting_ability = class_info["spellcasting_ability"]
    subclass_name = class_info["subtypes_name"]
    if subclass_name[-1:] == 's':
        subclass_name = subclass_name[:-1]
    subclasses = class_info["archetypes"]
    

    return {
        "Features": features,
        "Proficiency Bonus": proficiency_bonus,
        "Ability Scores Bonus": ability_scores_bonus,
        "Spellcasting": spellcasting_info,
        "Spells Known": spells_known,
        "Cantrips Known": cantrips_known,
        "Hit Dice": hit_dice,
        "Spellcasting Ability": spellcasting_ability,
        "Subclass Name": subclass_name,
        "Subclasses": subclasses,
    }

# Get racial traits
def traits(race:str):
    #############################  TRAITS  #############################
    # TRAITS FROM RACE
    traits_url = f"https://www.dnd5eapi.co/api/2014/races/{race.lower()}/traits"
    response = requests.request("GET", traits_url, headers=headers, data=payload)
    traits = response.json()["results"]
    traits_parsed = list()
    for trait in traits:
        traits_parsed.append(trait['name'])
    # print("Traits: ", traits_parsed)
    return traits_parsed

# Some starting equipment and skills based on the characters selected origin
def skills_and_equipment(origin:str):
    #############################  SKILLS  #############################
    background_url = f"https://api.open5e.com/v1/backgrounds/?name={origin}"

    response = requests.request("GET", background_url, headers=headers, data=payload)
    background = response.json()["results"][0]
    skill_proficiencies = background["skill_proficiencies"]
    # print("Skill proficiencies: ",skill_proficiencies)
    equipment = background["equipment"]
    return skill_proficiencies, equipment


### This function applies the ability score bonuses greedily. The bonuses are applied to the top score until it reaches a max of 20 and then moves onto the next score
def ability_score_bonuses(ability_scores_dict: dict, bonus_number: int):
    def largest_ability_score_under_20(ability_scores_dict:dict):
        max = 0
        max_ability = ""
        for ability in ability_scores_dict.keys():
            if ability_scores_dict[ability] > max and ability_scores_dict[ability]<20:
                max = ability_scores_dict[ability]
                max_ability = ability
        return max_ability

    bonus_points= bonus_number*2
    while bonus_points>0:
        ability = largest_ability_score_under_20(ability_scores_dict)
        ability_scores_dict[ability] +=1
        bonus_points-=1
    
    return ability_scores_dict

# Applies the Ability Score Indexes to the ability scores of the character (applies changes to str, con, dex, etc based on the given modifier list)
def apply_asi(ability_scores_dict: dict, asi_list: list):
    ability_map = {
        "Strength": "STR",
        "Constitution": "CON",
        "Dexterity": "DEX",
        "Intelligence": "INT",
        "Wisdom": "WIS",
        "Charisma": "CHA"
    }
    for asi in asi_list:
        ability = asi["attributes"][0]
        mapped_ability = ability_map[ability]
        ability_scores_dict[mapped_ability] += asi["value"]
    return ability_scores_dict


def assign_ability_scores(abilityScores: list, abilityScoresBonus: int, asi_list: list):
    #abilityScores is a list of all 6 ability names (DEX, STR, INT, etc.) in order of practical importance to the character. This is returned in the first AI call
    #abilityScoresBonus is the number of ability score bonuses the character has at their current level (+2 to one score or +1 to two scores). 
    #                             These bonuses will be assigned to the spread rather than changing the values once assigned in the dictionary
    #asi_list is the list of Ability Score Increases based off of the characters race. These should be applied to the ability scores before any bonuses
    ability_scores_spread = [15, 14, 13, 12, 10, 8]
    ability_scores_dict = dict(zip(abilityScores,ability_scores_spread))
    ability_scores_dict = apply_asi(ability_scores_dict, asi_list)
    ability_scores_dict = ability_score_bonuses(ability_scores_dict, abilityScoresBonus)
    return ability_scores_dict

#Calculate the abiliy score modifiers by applying the formula
def get_ability_score_modifiers(ability_scores: dict) -> dict:
    ability_score_mod = dict.copy(ability_scores)
    for key in ability_scores.keys():
        score = ability_scores[key]
        modifier = (score - 10)//2
        ability_score_mod[key] = modifier
    return ability_score_mod

#Saving throws value changes based on character level
def saving_throws_value(level):
    if level<5: return 2
    elif level<9: return 3
    elif level<13: return 4
    elif level<17: return 5
    else: return 6

def saving_throws_dict(saving_throws: list, level: int):
    return dict.fromkeys(saving_throws,saving_throws_value(level))

# Calculates passive wisdom (used for idle perception)
def get_passive_wisdom(ability_scores: dict):
    wisdom_modifier = (int(ability_scores["WIS"]-10))//2
    return 10 + wisdom_modifier 

#Get information about the character based on race
def get_race_stats(race: str):
    url = f"https://api.open5e.com/v1/races/?name={race}"
    response = requests.request("GET", url, headers=headers, data=payload)


    response = json.loads(response.text)
    #ASI = Ability Score Increase
    race_info=response["results"][0]
    asi_list= race_info["asi"]
    speed = race_info["speed"]["walk"]

    return speed, asi_list