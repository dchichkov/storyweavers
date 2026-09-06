#!/usr/bin/env python3
"""
A small superhero storyworld about teamwork, foreshadowing, and a classic rescue
with a sledge and a pot of linguini.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = STORYWORLDS_ROOT.parent
sys.path.insert(0, str(REPOSITORY_ROOT))
sys.path.insert(0, str(STORYWORLDS_ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "heroine"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "hero"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    hero: str
    sidekick: str
    villain: str
    place: str
    team_tool: str
    prize: str
    seed: Optional[int] = None
    scenario: str = "clock_tower"
    telling_mode: int = 0
    variant: int = 0


HERO_NAMES = ["Nova", "Milo", "Ivy", "Tara", "Ezra", "Juno"]
SIDEKICK_NAMES = ["Pip", "Rue", "Bea", "Ollie", "Skye", "Luca"]
VILLAIN_NAMES = ["Captain Cloud", "Dr. Shade", "The Grumble Giant", "Mister Slip"]


SCENARIOS: dict[str, dict[str, str]] = {
    "clock_tower": {
        "premise": "the clock tower rang at noon, although both hands pointed to eleven",
        "trouble": "a delivery lift carrying the town's lunch had jammed halfway up the tower",
        "clue": "a silver scrape on the third gear matched the edge of the missing lunch lid",
        "risk": "striking the gear would drop the lift instead of freeing it",
        "mistake": "The villain had wedged the lid into the gears to make the bell announce a fake parade.",
        "hero_action": "braced the sledge beneath the lift as a steady support",
        "sidekick_action": "threaded the classic grappling line through the safe gear and pulled on three",
        "solution": "the bent lid slid free and the lift settled gently onto the landing",
        "repair": "straightened the lid and helped reset the clock to the proper hour",
        "lesson": "A strong rescue begins with noticing what does not fit.",
        "ending": "At sunset, the true twelve chimes floated over bowls of warm linguini.",
    },
    "canal_bridge": {
        "premise": "three ducks paddled backward beneath the canal bridge",
        "trouble": "the bridge was rising with a supper wagon stranded on its center span",
        "clue": "green ribbon from the villain's cape fluttered inside the control box",
        "risk": "forcing the lever would snap its cable and tip the wagon into the canal",
        "mistake": "The villain had tied the ribbon around the switch while trying to stage a grand entrance.",
        "hero_action": "laid the sledge across the rails to stop the wagon from rolling",
        "sidekick_action": "used the classic grappling line to lift the ribbon clear of the switch",
        "solution": "the bridge lowered one careful notch at a time and the wagon rolled ashore",
        "repair": "untangled the controls and carried every supper basket to the square",
        "lesson": "Teamwork is strongest when each teammate handles the task suited to them.",
        "ending": "Moonlight striped the quiet canal while forks twirled rescued linguini.",
    },
    "library_float": {
        "premise": "paper bookmarks began sailing from the library windows like tiny flags",
        "trouble": "a parade balloon had snagged the rooftop pantry and lifted its linguini crate",
        "clue": "floury footprints ended beside a spool with one freshly cut strand",
        "risk": "popping the balloon would send the crate through the glass reading-room roof",
        "mistake": "The villain had cut the guide rope to borrow the balloon, then lost control of it.",
        "hero_action": "anchored the sledge behind a stone chimney",
        "sidekick_action": "cast the classic grappling line around the drifting crate's padded handle",
        "solution": "they reeled the crate onto the flat roof while the balloon sighed into a tree",
        "repair": "knotted a new guide rope and returned the bookmarks in their proper books",
        "lesson": "A careful plan can be braver than a spectacular leap.",
        "ending": "That evening, one red bookmark rested beside the last shining bowl.",
    },
    "greenhouse": {
        "premise": "the greenhouse windows fogged in the shape of question marks",
        "trouble": "runaway watering pipes were flooding the community supper garden",
        "clue": "dry soil beneath one valve showed that its puddle came from somewhere else",
        "risk": "closing that valve would build pressure until every glass pane burst",
        "mistake": "The villain had reversed two hose labels while hiding a stolen recipe card.",
        "hero_action": "set the sledge against the bucking main pipe to hold it still",
        "sidekick_action": "followed the classic grappling line from the dry valve to the crossed hoses",
        "solution": "they uncrossed the hoses, released the pressure, and saved the young plants",
        "repair": "relabeled every pipe and returned the recipe card to the cooks",
        "lesson": "Good clues describe causes, not merely the loudest mess.",
        "ending": "By dusk, basil leaves stood bright beside a fragrant pot of linguini.",
    },
    "tram_tunnel": {
        "premise": "the old tram arrived empty with a dinner napkin caught in its bell",
        "trouble": "the next tram was stuck in the tunnel with cooks and their supper aboard",
        "clue": "fresh chalk arrows on the wall pointed away from the emergency siding",
        "risk": "following those arrows would send rescuers toward a loose ceiling panel",
        "mistake": "The villain had drawn false arrows to hide a shortcut into the station pantry.",
        "hero_action": "propped the loose panel with the broad wooden sledge",
        "sidekick_action": "ran the classic grappling line along the real raised track markers",
        "solution": "the passengers followed the safe line out while the hero guarded the ceiling",
        "repair": "erased the false arrows and painted clear emergency signs",
        "lesson": "A warning matters only when the team pauses long enough to understand it.",
        "ending": "The tram bell gave one honest ding as steaming linguini reached the platform.",
    },
    "ice_rink": {
        "premise": "a single warm puddle appeared at the center of the winter ice rink",
        "trouble": "the supper pavilion was sliding toward a widening crack",
        "clue": "a trail of black pepper led from the puddle to a humming heater cart",
        "risk": "pulling the pavilion directly would spread the crack beneath the crowd",
        "mistake": "The villain had switched on the heater cart to warm a private bowl and forgotten its brakes.",
        "hero_action": "turned the sledge sideways to make a broad bridge over the crack",
        "sidekick_action": "lassoed the heater cart with the classic grappling line and shut it down",
        "solution": "families crossed the sledge while the pavilion stopped on solid ice",
        "repair": "salted the unsafe edge and helped carry every table to shore",
        "lesson": "Small selfish choices can create large problems for everyone.",
        "ending": "Snow dusted the parked heater while the team shared peppery linguini indoors.",
    },
    "museum_dinosaur": {
        "premise": "the museum dinosaur's shadow nodded though its bones stood still",
        "trouble": "a motorized display was dragging the gala supper toward the fossil stairs",
        "clue": "the moving shadow came from a blinking projector hidden behind a column",
        "risk": "cutting power at the main box would lock visitors inside the exhibit halls",
        "mistake": "The villain had rerouted the projector cable to steer the display as a getaway cart.",
        "hero_action": "slid the sledge beneath the display's rubber wheels as a brake",
        "sidekick_action": "traced the classic grappling line beside the cable to its portable controller",
        "solution": "one teammate held the brake while the other switched off only the display motor",
        "repair": "returned the controller and rolled the supper safely into the gala room",
        "lesson": "Foreshadowing is useful when a later discovery explains an earlier odd detail.",
        "ending": "Under the quiet dinosaur, sauce made small red moons on plates of linguini.",
    },
    "windmill": {
        "premise": "the bakery windmill turned on a perfectly still morning",
        "trouble": "its flour hoist had trapped the festival's pasta basket above the yard",
        "clue": "soap bubbles drifted from a new copper tube aimed at the windmill blades",
        "risk": "grabbing the rope would spin the hoist faster and scatter the basket",
        "mistake": "The villain had built a hidden air pump to turn the blades and impress the town.",
        "hero_action": "wedged the sledge under the hoist drum without striking it",
        "sidekick_action": "looped the classic grappling line around the air pump's safe shutoff handle",
        "solution": "the pump stopped, the drum rested on the sledge, and the basket descended",
        "repair": "dismantled the secret tube and rebuilt it as a bubble machine for everyone",
        "lesson": "Real heroism protects people instead of chasing applause.",
        "ending": "Bubbles floated over the picnic as children passed bowls of buttery linguini.",
    },
    "aquarium": {
        "premise": "silver fish crowded one side of the aquarium as if listening",
        "trouble": "a rolling kitchen cart was blocking the pump-room door while an alarm flashed",
        "clue": "the fish were following a faint tapping from a spoon inside the wall vent",
        "risk": "ramming the cart would spill hot sauce and frighten the animals",
        "mistake": "The villain had hidden a stolen tasting spoon in the vent and nudged the cart across the door.",
        "hero_action": "used the sledge as a low ramp beneath one locked wheel",
        "sidekick_action": "pulled evenly on the classic grappling line from the opposite side",
        "solution": "the cart rolled clear, the keeper reached the pump, and the alarm went dark",
        "repair": "returned the spoon and scrubbed the sauce tray before supper",
        "lesson": "Gentle, coordinated force can solve what one hard shove cannot.",
        "ending": "Fish flashed like coins beyond the glass while the keepers ate cool linguini salad.",
    },
    "hill_fair": {
        "premise": "every pinwheel at the hill fair suddenly pointed downhill",
        "trouble": "the feast cart had slipped its chock and begun creeping toward the crowded games",
        "clue": "a triangular gap in the mud was exactly the shape of the missing wheel block",
        "risk": "standing in front of the cart would put a rescuer directly in its path",
        "mistake": "The villain had borrowed the wheel block to prop up a crooked prize booth.",
        "hero_action": "guided the sledge beside the wheel as a moving barrier",
        "sidekick_action": "snared the rear axle with the classic grappling line from uphill",
        "solution": "their two angles turned the cart into an empty hay bale and stopped it",
        "repair": "restored the wheel block and leveled the booth with proper boards",
        "lesson": "Teammates stay safer when they plan positions before they use their strength.",
        "ending": "The pinwheels spun every direction above a long table of festival linguini.",
    },
    "lighthouse": {
        "premise": "the lighthouse beam blinked twice whenever the kitchen door opened",
        "trouble": "a food basket hung outside the gallery rail while fog covered the harbor",
        "clue": "sauce-red fingerprints marked the emergency shutter crank",
        "risk": "opening the shutter fully would blind an approaching rescue boat",
        "mistake": "The villain had tied the basket to the crank while sneaking it onto the balcony.",
        "hero_action": "secured the sledge across the doorway as an anchor",
        "sidekick_action": "clipped the classic grappling line to the basket and matched each lighthouse blink",
        "solution": "they lifted the basket during the dark beats without interrupting the guiding beam",
        "repair": "cleaned the crank and carried a signal lamp down to the harbor keeper",
        "lesson": "The best solution protects both the thing nearby and the people still on their way.",
        "ending": "Through thinning fog, the steady beam swept over a table of rescued linguini.",
    },
    "orchard_stage": {
        "premise": "apples rolled onto the outdoor stage before the curtain rose",
        "trouble": "the scenery wagon and the cast's supper were sliding toward the orchestra pit",
        "clue": "each apple bore a crescent dent from the same loose brake handle",
        "risk": "catching the scenery by hand would topple its painted castle",
        "mistake": "The villain had removed the brake handle to use it as a pretend royal wand.",
        "hero_action": "placed the sledge flat across the pit edge to spread the wagon's weight",
        "sidekick_action": "used the classic grappling line to pull the brake cable from backstage",
        "solution": "the wagon stopped with its castle upright and its supper bowls unspilled",
        "repair": "reattached the handle and joined the crew in sweeping the stage",
        "lesson": "Admitting a foolish choice is the first step toward repairing it.",
        "ending": "When the curtain rose, one apple and one curl of linguini sat beneath the paper crown.",
    },
}

OPENINGS = [
    "In {place}, {hero} and {sidekick} wore the old star badge of a classic superhero team.",
    "The classic superhero partners {hero} and {sidekick} began patrol above {place}.",
    "Every child in {place} knew the classic superhero sign: {hero} and {sidekick} arriving together.",
    "At breakfast in {place}, {hero} and {sidekick} promised that a classic superhero listens before leaping.",
    "A brass bell welcomed the classic superhero team of {hero} and {sidekick} to {place}.",
    "For {hero} and {sidekick}, guarding {place} as a classic superhero team meant sharing both plans and credit.",
    "The morning paper called {hero} and {sidekick} the classic superhero guardians of {place}.",
    "Above {place}, two capes turned together: the classic superhero team of {hero} and {sidekick}.",
]

FORESHADOW_LINES = [
    "Neither hero understood it yet, but the detail would become important.",
    "It seemed small then; later, it would explain the whole danger.",
    "That was the story's foreshadowing, a quiet promise that the clue would matter.",
    "The clue did not solve the trouble yet, but it pointed toward the truth.",
    "They marked the odd detail instead of rushing past it.",
    "For a moment the clue looked harmless, though it would soon guide their rescue.",
    "The partners stored that early warning in their shared plan.",
    "A good superhero notices the whisper before the crash, and this was that whisper.",
]

TEAM_LINES = [
    '"One plan, two jobs," said {hero}. "I will steady it; you follow the clue."',
    '"Teamwork, not guesswork," {sidekick} said. They counted, "One, two, three!"',
    '"Your eyes found the cause; my hands can hold the weight," said {hero}.',
    '"Neither of us does both jobs alone," {sidekick} said, and {hero} nodded.',
    '"We move only when we both say ready," said {hero}. "Ready," answered {sidekick}.',
    '"The clue gives us the order," said {sidekick}. "Then let us share the work," said {hero}.',
    '"Strong and careful belong on the same team," {hero} said.',
    '"You protect the people; I will undo the cause," {sidekick} proposed, and the plan clicked into place.',
]

TURN_LINES = [
    "Now the strange beginning made sense.",
    "The early clue pointed straight to the hidden cause.",
    "What had looked accidental became a clear chain of cause and effect.",
    "The warning from the beginning finally paid off.",
    "At once, the partners understood why the first detail had felt wrong.",
    "The clue, the danger, and the villain's choice joined into one explanation.",
    "Their patient observation had found the one safe opening.",
    "Instead of fighting the symptom, they could finally repair the cause.",
]

SUCCESS_LINES = [
    "The two jobs met at exactly the right moment",
    "Because neither partner rushed, the rescue succeeded",
    "Strength and observation worked as one",
    "Their careful count brought both actions together",
    "The clue had given them the order, and the order worked",
    "Neither action was enough alone; together they changed the outcome",
    "The team moved as one",
    "Their separate tasks joined into one successful plan",
]


class World:
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with teamwork and foreshadowing.")
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
    ap.add_argument("--villain")
    ap.add_argument("--place")
    ap.add_argument("--team-tool")
    ap.add_argument("--prize")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def generate_world(p: StoryParams) -> World:
    w = World(p.place)
    hero = w.add(Entity(id="hero", kind="character", type="hero", label=p.hero))
    sidekick = w.add(Entity(id="sidekick", kind="character", type="hero", label=p.sidekick))
    villain = w.add(Entity(id="villain", kind="character", type="villain", label=p.villain))
    prize = w.add(Entity(id="prize", kind="thing", label=p.prize, owner="town", caretaker="sidekick"))
    tool = w.add(Entity(id="tool", kind="thing", label=p.team_tool, owner="hero"))
    return w


def tell(world: World, p: StoryParams) -> World:
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    villain = world.get("villain")
    prize = world.get("prize")
    tool = world.get("tool")

    case = SCENARIOS[p.scenario]
    rng = random.Random((p.seed or 0) ^ p.variant ^ 0x51ED6E)
    opening = OPENINGS[p.telling_mode % len(OPENINGS)].format(
        hero=p.hero, sidekick=p.sidekick, place=p.place
    )
    clue_bridge = FORESHADOW_LINES[rng.randrange(len(FORESHADOW_LINES))]
    team_line = TEAM_LINES[(p.telling_mode + rng.randrange(len(TEAM_LINES))) % len(TEAM_LINES)].format(
        hero=p.hero, sidekick=p.sidekick
    )
    turn_line = TURN_LINES[rng.randrange(len(TURN_LINES))]
    supper_detail = f"the patrol cart carried {p.prize}"
    if "linguini" not in p.prize.casefold():
        supper_detail += " beside a covered pot of linguini"
    tool_label = p.team_tool
    if not tool_label.casefold().startswith(("a ", "an ", "the ")):
        tool_label = f"a {tool_label}"
    tool_detail = f"their chosen rescue tool was {tool_label}"
    if "sledge" not in p.team_tool.casefold():
        tool_detail += ", with a broad sledge ready as backup"
    supper_line = rng.choice(
        [
            f"Before the alarm, {supper_detail}, and {tool_detail}.",
            f"Their morning checklist said that {supper_detail}; {tool_detail}.",
            f"Nearby, {supper_detail}. For this mission, {tool_detail}.",
            f"They checked their supplies together: {supper_detail}, while {tool_detail}.",
        ]
    )
    warning = rng.choice(
        [
            f'"Wait," {p.sidekick} said. "{case["risk"].capitalize()}."',
            f"{p.hero} started forward, but {p.sidekick} explained that {case['risk']}.",
            f"They tested the first idea with an empty tin and discovered that {case['risk']}.",
            f"A quick sketch showed them the danger: {case['risk']}.",
        ]
    )

    world.say(opening)
    world.say(supper_line)
    world.say(f"Then they noticed something peculiar: {case['premise']}.")
    world.say(f"Moments later, an alarm revealed the real emergency: {case['trouble']}.")

    world.para()
    world.say(f"While {p.villain} insisted it was merely bad luck, {p.sidekick} found a clue: {case['clue']}.")
    world.say(f"That was foreshadowing. {clue_bridge}")
    world.say(warning)
    world.say(f"They built a teamwork plan around the clue. {team_line}")

    world.para()
    world.say(f"{p.hero} {case['hero_action']}.")
    world.say(f"At the same time, {p.sidekick} {case['sidekick_action']}.")
    success_line = SUCCESS_LINES[rng.randrange(len(SUCCESS_LINES))]
    world.say(f"{success_line}: {case['solution']}.")
    world.say(turn_line)
    world.say(case["mistake"])

    world.para()
    apology = rng.choice(
        [
            f'"I wanted everyone to notice me," {p.villain} admitted. "Instead, I put them in danger. I am sorry."',
            f'{p.villain} lowered their head. "My shortcut caused this. May I help put it right?"',
            f'"The clue led to me," {p.villain} said. "I will stop hiding what I did and help repair it."',
            f'{p.villain} took a slow breath. "I made the trouble worse. Please let me make amends."',
        ]
    )
    world.say(apology)
    world.say(f"Together, the three of them {case['repair']}.")
    world.say(f"{case['lesson']} That was the team's classic rule, and they had proved it through action.")
    world.say(case["ending"])

    prize.owner = "town"
    prize.caretaker = "hero"
    tool.meters["used_safely"] = 1.0
    hero.memes["Teamwork"] = 1.0
    sidekick.memes["Teamwork"] = 1.0
    villain.memes["Accountability"] = 0.8
    world.fired.update({"foreshadowing_paid_off", "team_plan_succeeded", "villain_repaired_harm"})

    world.facts = {
        "hero": p.hero,
        "sidekick": p.sidekick,
        "villain": p.villain,
        "place": p.place,
        "team_tool": p.team_tool,
        "prize": p.prize,
        "scenario": p.scenario,
        "premise": case["premise"],
        "trouble": case["trouble"],
        "clue": case["clue"],
        "risk": case["risk"],
        "hero_action": case["hero_action"],
        "sidekick_action": case["sidekick_action"],
        "solution": case["solution"],
        "repair": case["repair"],
        "lesson": case["lesson"],
        "ending": case["ending"],
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a superhero story about {f['hero']} and {f['sidekick']} using teamwork during this emergency: {f['trouble']}.",
        f"Tell a classic adventure in {f['place']} where the clue '{f['clue']}' foreshadows the safe solution.",
        f"Write a child-friendly rescue involving {f['villain']}, a sledge, linguini, dialogue, and the lesson '{f['lesson']}'",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Who worked together in the story?",
            answer=f"{f['hero']} and {f['sidekick']} worked together as a team.",
        ),
        QAItem(
            question=f"What early clue foreshadowed the cause of the emergency?",
            answer=f"The early clue was that {f['clue']}. It helped the heroes understand what had caused the danger.",
        ),
        QAItem(
            question=f"How did {f['hero']} and {f['sidekick']} divide the rescue work?",
            answer=f"{f['hero']} {f['hero_action']}. Meanwhile, {f['sidekick']} {f['sidekick_action']}.",
        ),
        QAItem(
            question=f"What changed because the teammates followed their plan?",
            answer=f"Their plan meant that {f['solution']}. Then everyone could safely help with the repair.",
        ),
        QAItem(
            question=f"How did {f['villain']} make amends?",
            answer=f"{f['villain']} admitted the mistake and helped the team {f['repair']}.",
        ),
        QAItem(
            question="What lesson did the team prove through its actions?",
            answer=f"They proved this lesson: {f['lesson']}",
        ),
        QAItem(
            question="What food and selected rescue tool did the team bring on patrol?",
            answer=f"The patrol supplies included {f['prize']}, and the selected rescue tool was {f['team_tool']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and work together toward the same goal.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a small clue that hints something important may happen later.",
        ),
        QAItem(
            question="What is a sledge?",
            answer="A sledge is a strong tool or sled-like object that can help move or lift heavy things.",
        ),
        QAItem(
            question="What is linguini?",
            answer="Linguini is a type of long, flat pasta that people often eat with sauce.",
        ),
    ]


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("tool", "sledge"),
            asp.fact("tool", "classic_grappling_line"),
            asp.fact("prize", "linguini"),
            asp.fact("prize", "the_mayors_lunchbox"),
        ]
    )


ASP_RULES = r"""
compatible_story(nova, pip, old_harbor, sledge, linguini).
compatible_story(milo, rue, bright_city, classic_grappling_line, the_mayors_lunchbox).
compatible_story(ivy, bea, moonbridge, sledge, linguini).
compatible_story(tara, ollie, pine_plaza, classic_grappling_line, the_mayors_lunchbox).
compatible_story(ezra, skye, old_harbor, sledge, linguini).
compatible_story(juno, luca, bright_city, classic_grappling_line, the_mayors_lunchbox).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible_story/5."))
    clingo_set = set(asp.atoms(model, "compatible_story"))
    python_set = {
        ("nova", "pip", "old_harbor", "sledge", "linguini"),
        ("milo", "rue", "bright_city", "classic_grappling_line", "the_mayors_lunchbox"),
        ("ivy", "bea", "moonbridge", "sledge", "linguini"),
        ("tara", "ollie", "pine_plaza", "classic_grappling_line", "the_mayors_lunchbox"),
        ("ezra", "skye", "old_harbor", "sledge", "linguini"),
        ("juno", "luca", "bright_city", "classic_grappling_line", "the_mayors_lunchbox"),
    }
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: kind={e.kind} label={e.label} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for title, items in [
            ("== Generation prompts ==", sample.prompts),
            ("== Story questions ==", sample.story_qa),
            ("== World questions ==", sample.world_qa),
        ]:
            print(title)
            for item in items:
                if isinstance(item, str):
                    print(item)
                else:
                    print(f"Q: {item.question}")
                    print(f"A: {item.answer}")
            print()


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    world = tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(hero="Nova", sidekick="Pip", villain="Captain Cloud", place="Old Harbor", team_tool="sledge", prize="linguini", seed=11, scenario="clock_tower", telling_mode=0, variant=11),
    StoryParams(hero="Milo", sidekick="Rue", villain="Dr. Shade", place="Bright City", team_tool="classic grappling line", prize="the mayor's lunchbox", seed=29, scenario="museum_dinosaur", telling_mode=6, variant=29),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HERO_NAMES)
    sidekick_choices = [name for name in SIDEKICK_NAMES if name != hero]
    return StoryParams(
        hero=hero,
        sidekick=args.sidekick or rng.choice(sidekick_choices),
        villain=args.villain or rng.choice(VILLAIN_NAMES),
        place=args.place or rng.choice(["Old Harbor", "Bright City", "Moonbridge", "Pine Plaza"]),
        team_tool=args.team_tool or rng.choice(["sledge", "classic grappling line"]),
        prize=args.prize or rng.choice(["linguini", "the mayor's lunchbox"]),
        scenario=rng.choice(list(SCENARIOS)),
        telling_mode=rng.randrange(len(OPENINGS)),
        variant=rng.randrange(1_000_000_000),
    )


def format_json(samples: list[StorySample]) -> str:
    if len(samples) == 1:
        return samples[0].to_json()
    return json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible_story/5."))
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        print(format_json(samples))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
