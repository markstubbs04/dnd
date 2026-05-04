from openai import OpenAI
import json
import requests


initial_schema = {
        "name": "dnd_setup",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "name": {"type":"string"},
                "class": {"type": "string", "enum": ["Barbarian","Bard","Cleric","Druid","Fighter","Monk","Paladin","Ranger","Rogue","Sorcerer","Warlock","Wizard"]},
                "race": {"type": "string", "enum": ["Dragonborn","Dwarf","Elf","Gnome","Half-Elf","Half-Orc","Halfling","Human","Tiefling"]},
                "origin": {"type": "string", "enum":["Acolyte","Artisan","Charlatan","Con Artist","Criminal","Entertainer","Exile", "Farmer","Folk Hero","Gambler","Guildmember","Hermit","Marauder","Noble","Outlander","Sage","Sailor","Scoundrel","Trader","Urchin"]},
                "alignment_order_versus_chaos": {"type": "string", "enum":["Lawful","Neutral","Chaotic"]},
                "alignment_good_versus_evil":{"type": "string", "enum":["Good","Neutral","Evil"]},
                "level":{"type":"integer","min":1,"max":20,"description":"Level should be assigned based on the character's overall power and overall experience."},
                "weapons":{
                    "type":"array",
                    "items":{
                        "type":"object", 
                        "properties": {
                            "name": {"type":"string"},
                            "range":{"type":"array","items":{"type":"string","enum":["Martial Melee", "Martial Ranged", "Martial", "Melee", "Ranged", "Simple Melee", "Simple Ranged", "Simple"]}},
                            "weaponProperty": {"type":"array","items":{"type":"string","enum":["One-Handed","Two-Handed","Ammunition","Finesse","Heavy","Light","Loading","Monk","Reach","Special","Thrown","Versatile","Range","Improvised Weapon"]}},
                            "weaponDamageType": {"type":"string","enum":["Bludgeoning","Piercing","Slashing","Acid","Cold","Fire","Force","Lightning","Necrotic","Poison","Psychic","Radiant","Slashing","Thunder"]},
                            "damageDie":{"type":"string","enum":["1d4","1d6","1d8","1d10","1d12"],"description":"This is the amount of damage the weapon does. If the weapon is more important or rare, it should do more damage. If a weapon is particularly large it should also do more damage."}
                        },
                        "required":["name","range","weaponProperty","weaponDamageType","damageDie"],
                        "additionalProperties": False
                    },
                    "description":"A list of weapons that this character currently wields. If the user does not specify a weapon, return 1 or 2 objects the character could use as an improvised weapon. Return only the object name. EX: 'Briefcase', 'Bottle', 'Belt'"
                },
                "shield":{"type":"string","description":"Leave blank if the character does not have a shield."},
                "abilityScores":{
                    "type": "array",
                    "description": "This is an ordered list of ability scores for the character. The abilities more pertinent to the character should be ordered first",
                    "items": {
                        "type": "string",
                        "enum": ["STR", "DEX", "CON", "INT", "WIS", "CHA"],
                    },
                    "maxItems":6,
                    "minItems":6
                },
                "personality_traits":{
                    "type": "array",
                    "description": "Personality traits are short, specific characteristics that define how a character acts, speaks, and interacts with the world. They represent a character’s demeanor and help distinguish them from others. Only return personality traits that are relevant to the given character description. Examples: 'Curious', 'Polite', 'Sarcastic/Vain', 'Dedicated', 'Stoic', 'Abrasive'",
                    "items": {"type": "string"},
                    "maxItems":5,
                    "minItems":2
                },
                "ideals":{
                    "type": "array",
                    "description": "Ideals are a character's core beliefs, ethical principles, and driving motivations that guide their actions and decisions, typically chosen from their background. They define what the character cares about most, bridging the gap between personality traits and alignment. Only return ideals that match the given character alignment and personality traits. Examples: 'Charity', 'Retribution', 'Order', 'Freedom', 'Knowledge', 'Respect', 'Greed'",
                    "items": {"type": "string"},
                    "maxItems":5,
                    "minItems":1
                },
                "bonds":{
                    "type": "array",
                    "description": "Bonds are character traits defining what (or whom) a character cares about most, acting as a primary motivation for adventuring, such as a person, place, or object. ONLY return bonds if they are relevant to the provided character and related to the prompt. Examples: 'I would die to protect my mentor, who is also a terrible person I'm trying to reform', 'I will do anything to protect the temple where I served', 'I am trying to pay off an old debt I owe to the Gnome gang', 'My mother's necklace was taken from me, and I aim to steal it back'",
                    "items": {"type": "string"},
                    "maxItems":0,
                    "minItems":5
                },
                "flaws":{
                    "type": "array",
                    "description": "Flaws are personality shortcomings, fears, or biases that create drama, drive roleplay, and hinder the character, preventing them from being perfect heroes. ONLY return flaws if they are relevant to the provided character description. Examples: 'Dishonesty', 'Arrogance', 'Selfishness', 'Addictions or Secrets', 'Cowardice', 'Recklessness'",
                    "items": {"type": "string"},
                    "maxItems":6,
                    "minItems":6
                }
            },
            "required": ["name", "class", "race", "origin", "alignment_order_versus_chaos","alignment_good_versus_evil", "level", "weapons", "shield", "abilityScores", "personality_traits", "ideals", "bonds", "flaws"],
            "additionalProperties": False
        }
    }

system_prompt = """You are an expert Dungeon Master for the game Dungeons and Dragons.
You exclusively use the 2014 ruleset when making decisions.
Users will provide a short description of a character, translate this character into the world of Dungeons and Dragons by assigning it a class, a race, an origin, an alignment, and a level.
For each required attribute, think through your decision and carefully consider why the provided character would 
."""

model = "gpt-5-mini"


def create_character(client: OpenAI, prompt: str) -> object:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_schema", "json_schema":initial_schema},
            temperature=1.0
        )
    character_sheet = json.loads(response.choices[0].message.content)
    return character_sheet