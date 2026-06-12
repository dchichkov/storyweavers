#!/usr/bin/env python3
"""
Cautionary Tales Generator using TextWorld-inspired World Model

This uses TextWorld's logic system to model a storyworld where:
- Activities have preconditions (where you are, what you're holding)
- Activities have effects (including possible injuries)
- The world state constrains what can happen

This prevents nonsensical combinations like "playing with scissors → twisted ankle"
"""

import random
from dataclasses import dataclass, field
from typing import List, Set, Dict, Optional, Callable
from textworld import GameMaker
from textworld.logic import Proposition, Variable, State


# =============================================================================
# WORLD MODEL - Using TextWorld's fact-based representation
# =============================================================================

@dataclass
class Character:
    """A character in our storyworld."""
    name: str
    gender: str  # 'boy' or 'girl'
    
    @property
    def pronoun(self) -> str:
        return "he" if self.gender == "boy" else "she"
    
    @property
    def pronoun_obj(self) -> str:
        return "him" if self.gender == "boy" else "her"
    
    @property
    def pronoun_poss(self) -> str:
        return "his" if self.gender == "boy" else "her"
    
    @property
    def title(self) -> str:
        return "little boy" if self.gender == "boy" else "little girl"


@dataclass
class WorldObject:
    """An object in the world with properties that affect what can happen."""
    name: str
    properties: Set[str] = field(default_factory=set)
    # Properties like: "sharp", "hot", "heavy", "high", "fragile", "edible"


@dataclass 
class Location:
    """A location with properties."""
    name: str
    properties: Set[str] = field(default_factory=set)
    objects: List[WorldObject] = field(default_factory=list)
    # Properties like: "indoor", "outdoor", "has_stairs", "slippery", "high"


@dataclass
class Activity:
    """An activity a child might do, with preconditions and possible effects."""
    name: str
    description: str  # "running in the house"
    
    # Preconditions - what must be true for this activity
    required_location_props: Set[str] = field(default_factory=set)
    required_object_props: Set[str] = field(default_factory=set)
    requires_object: Optional[str] = None  # specific object needed
    
    # Effects - what can happen
    risk_factors: Set[str] = field(default_factory=set)  # "falling", "cutting", "burning"
    
    def can_occur_at(self, location: Location, held_object: Optional[WorldObject] = None) -> bool:
        """Check if this activity can happen given the world state."""
        # Check location requirements
        if self.required_location_props and not self.required_location_props.issubset(location.properties):
            return False
        
        # Check object requirements
        if self.requires_object and (held_object is None or held_object.name != self.requires_object):
            return False
            
        if self.required_object_props and held_object:
            if not self.required_object_props.issubset(held_object.properties):
                return False
                
        return True


@dataclass
class Injury:
    """A possible injury with its causes."""
    name: str
    description_template: str  # "{poss} finger" -> "his finger" / "her finger"
    caused_by: Set[str]  # risk factors that can cause this: "falling", "cutting", etc.
    body_part: str  # "finger", "head", "ankle", etc.


# =============================================================================
# WORLD KNOWLEDGE - Define what exists and how things relate
# =============================================================================

# Objects that can be in the world
WORLD_OBJECTS = [
    WorldObject("scissors", {"sharp", "small", "tool"}),
    WorldObject("knife", {"sharp", "dangerous", "tool"}),
    WorldObject("ball", {"throwable", "toy", "round"}),
    WorldObject("chair", {"climbable", "furniture"}),
    WorldObject("stove", {"hot", "dangerous", "appliance"}),
    WorldObject("toy car", {"toy", "small", "rollable"}),
    WorldObject("blocks", {"toy", "stackable", "throwable"}),
]

# Locations
LOCATIONS = [
    Location("the kitchen", {"indoor", "has_appliances"}, 
             [WorldObject("stove", {"hot", "dangerous"}), WorldObject("knife", {"sharp"})]),
    Location("the living room", {"indoor", "has_furniture"},
             [WorldObject("chair", {"climbable"}), WorldObject("toy car", {"toy"})]),
    Location("the backyard", {"outdoor", "has_ground"},
             [WorldObject("ball", {"throwable"})]),
    Location("the stairs", {"indoor", "has_stairs", "high"},
             []),
    Location("the playroom", {"indoor", "has_toys"},
             [WorldObject("scissors", {"sharp"}), WorldObject("blocks", {"throwable"})]),
]

# Activities with their risk profiles
ACTIVITIES = [
    Activity(
        name="running_indoors",
        description="running in the house",
        required_location_props={"indoor"},
        risk_factors={"falling", "collision"}
    ),
    Activity(
        name="playing_scissors", 
        description="playing with scissors",
        required_object_props={"sharp"},
        risk_factors={"cutting"}
    ),
    Activity(
        name="jumping_furniture",
        description="jumping on the furniture",
        required_location_props={"indoor"},
        required_object_props={"climbable"},
        risk_factors={"falling", "collision"}
    ),
    Activity(
        name="throwing_inside",
        description="throwing things inside",
        required_location_props={"indoor"},
        required_object_props={"throwable"},
        risk_factors={"collision", "breaking"}
    ),
    Activity(
        name="climbing_chair",
        description="standing on a wobbly chair",
        required_object_props={"climbable"},
        risk_factors={"falling"}
    ),
    Activity(
        name="running_stairs",
        description="running on the stairs",
        required_location_props={"has_stairs"},
        risk_factors={"falling", "tumbling"}
    ),
    Activity(
        name="touching_stove",
        description="touching the hot stove",
        required_object_props={"hot"},
        risk_factors={"burning"}
    ),
]

# Injuries linked to risk factors
INJURIES = [
    Injury("fell_down", "fell down and scraped {poss} knee", {"falling", "tumbling"}, "knee"),
    Injury("bumped_head", "bumped {poss} head hard", {"falling", "collision"}, "head"),
    Injury("twisted_ankle", "twisted {poss} ankle", {"falling", "tumbling"}, "ankle"),
    Injury("cut_finger", "cut {poss} finger", {"cutting"}, "finger"),
    Injury("cut_hand", "got a cut on {poss} hand", {"cutting"}, "hand"),
    Injury("got_bruise", "got a big bruise", {"falling", "collision"}, "body"),
    Injury("burned_hand", "burned {poss} hand", {"burning"}, "hand"),
    Injury("broke_something", "broke something and got hurt by the pieces", {"breaking"}, "hand"),
]


# =============================================================================
# STORY WORLD - Simulation engine
# =============================================================================

class StoryWorld:
    """
    A world simulation that tracks state and generates causally-consistent events.
    Inspired by TextWorld's fact-based world model.
    """
    
    def __init__(self):
        self.facts: Set[str] = set()  # Current world state as facts
        self.character: Optional[Character] = None
        self.location: Optional[Location] = None
        self.held_object: Optional[WorldObject] = None
        self.parent: str = "mom"
        
    def setup(self, character: Character, location: Location, held_object: Optional[WorldObject] = None):
        """Initialize the world state."""
        self.character = character
        self.location = location
        self.held_object = held_object
        self.parent = random.choice(["mom", "dad", "mommy", "daddy"])
        
        # Set facts
        self.facts = {
            f"at({character.name}, {location.name})",
            f"warned_by({character.name}, {self.parent})",
        }
        if held_object:
            self.facts.add(f"holding({character.name}, {held_object.name})")
            
        for prop in location.properties:
            self.facts.add(f"location_is({prop})")
            
    def get_valid_activities(self) -> List[Activity]:
        """Return activities that can occur in current world state."""
        valid = []
        for activity in ACTIVITIES:
            # Check if activity can occur here
            if activity.can_occur_at(self.location, self.held_object):
                valid.append(activity)
            # Also check objects in the location
            elif activity.required_object_props:
                for obj in self.location.objects:
                    if activity.required_object_props.issubset(obj.properties):
                        valid.append(activity)
                        break
        return valid
    
    def get_valid_injuries(self, activity: Activity) -> List[Injury]:
        """Return injuries that can result from this activity."""
        return [inj for inj in INJURIES if inj.caused_by & activity.risk_factors]
    
    def simulate_accident(self) -> Optional[Dict]:
        """
        Simulate an accident scenario.
        Returns the activity, injury, and relevant objects if valid scenario exists.
        """
        valid_activities = self.get_valid_activities()
        if not valid_activities:
            return None
            
        activity = random.choice(valid_activities)
        valid_injuries = self.get_valid_injuries(activity)
        
        if not valid_injuries:
            return None
            
        injury = random.choice(valid_injuries)
        
        # Find the relevant object (if any)
        relevant_object = self.held_object
        if not relevant_object and activity.required_object_props:
            for obj in self.location.objects:
                if activity.required_object_props.issubset(obj.properties):
                    relevant_object = obj
                    break
        
        return {
            "activity": activity,
            "injury": injury,
            "object": relevant_object,
            "location": self.location,
        }


# =============================================================================
# NARRATIVE GENERATOR - Turns simulation into stories
# =============================================================================

class NarrativeGenerator:
    """Generates story text from world simulation results."""
    
    def __init__(self, world: StoryWorld):
        self.world = world
        
    def format_injury(self, injury: Injury) -> str:
        """Format injury description with correct pronouns."""
        return injury.description_template.format(poss=self.world.character.pronoun_poss)
    
    def generate_story(self, scenario: Dict) -> str:
        """Generate a full cautionary tale from a scenario."""
        char = self.world.character
        parent = self.world.parent
        activity = scenario["activity"]
        injury = scenario["injury"]
        location = scenario["location"]
        
        injury_text = self.format_injury(injury)
        
        story = f"""Once upon a time, there was a {char.title} named {char.name}. {char.name} loved to play in {location.name}.

One day, {char.pronoun_poss} {parent} said, "Please be careful! Don't be {activity.description}." But {char.name} didn't listen.

When {parent} wasn't looking, {char.name} started {activity.description}. {char.pronoun.capitalize()} thought it would be fun!

But then something bad happened. {char.name} {injury_text}! It hurt a lot, and {char.name} started to cry.

{parent.capitalize()} came running and helped {char.pronoun_obj}. "This is why I warned you," said {parent} gently, giving {char.name} a hug.

{char.name} felt sorry for not listening. {char.pronoun.capitalize()} learned that {parent} gives warnings because {parent} loves {char.pronoun_obj} and wants to keep {char.pronoun_obj} safe.

From that day on, {char.name} remembered to be more careful. Some rules are there to protect us!"""
        
        return story


# =============================================================================
# MAIN GENERATOR
# =============================================================================

BOY_NAMES = ["Tim", "Tommy", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli"]
GIRL_NAMES = ["Lily", "Emma", "Mia", "Zoe", "Ava", "Ella", "Ruby", "Lucy", "Ivy", "Chloe"]


def generate_cautionary_tale() -> Optional[str]:
    """Generate a single causally-consistent cautionary tale."""
    # Create a random character
    gender = random.choice(["boy", "girl"])
    name = random.choice(BOY_NAMES if gender == "boy" else GIRL_NAMES)
    character = Character(name, gender)
    
    # Pick a random location
    location = random.choice(LOCATIONS)
    
    # Sometimes the child is holding something
    held_object = None
    if random.random() < 0.3 and location.objects:
        held_object = random.choice(location.objects)
    
    # Create and setup world
    world = StoryWorld()
    world.setup(character, location, held_object)
    
    # Simulate an accident
    scenario = world.simulate_accident()
    if not scenario:
        return None
    
    # Generate narrative
    narrator = NarrativeGenerator(world)
    return narrator.generate_story(scenario)


def generate_unique_stories(count: int = 100) -> List[str]:
    """Generate multiple unique cautionary tales."""
    stories = []
    seen = set()
    attempts = 0
    max_attempts = count * 5
    
    while len(stories) < count and attempts < max_attempts:
        attempts += 1
        story = generate_cautionary_tale()
        if story:
            # Check uniqueness
            story_hash = hash(story[:200] + story[-200:] if len(story) > 400 else story)
            if story_hash not in seen:
                seen.add(story_hash)
                stories.append(story)
    
    return stories


def main():
    """Generate and print cautionary tales."""
    print("=" * 70)
    print("CAUTIONARY TALES - Generated with World Model Constraints")
    print("=" * 70)
    print()
    
    # Generate a few example stories
    stories = generate_unique_stories(5)
    
    for i, story in enumerate(stories, 1):
        print(f"--- Story {i} ---")
        print(story)
        print()
        print()


if __name__ == "__main__":
    main()
