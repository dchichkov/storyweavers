#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/luncheon_sober_teamwork_rhyme_superhero_story.py
============================================================================

A standalone story world for a tiny "superhero luncheon" domain.

The core tale:
- Children are at a special luncheon and pretending to be superheroes.
- A lunch centerpiece or serving thing starts to wobble.
- One child feels like making a flashy solo save.
- Another child suggests a sober plan and a small teamwork rhyme.
- The group either saves the luncheon together or makes a mess and then cleans it
  up together, learning that real heroes help side by side.

Run it
------
    python storyworlds/worlds/gpt-5.4/luncheon_sober_teamwork_rhyme_superhero_story.py
    python storyworlds/worlds/gpt-5.4/luncheon_sober_teamwork_rhyme_superhero_story.py --hazard soup_tureen --tool tray
    python storyworlds/worlds/gpt-5.4/luncheon_sober_teamwork_rhyme_superhero_story.py --tool superhero_leap
    python storyworlds/worlds/gpt-5.4/luncheon_sober_teamwork_rhyme_superhero_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/luncheon_sober_teamwork_rhyme_superhero_story.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so three dirname() calls
# reach the package dir storyworlds/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher_woman"}
        male = {"boy", "father", "man", "teacher_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "teacher_woman": "teacher",
            "teacher_man": "teacher",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Venue:
    id: str
    label: str
    opening: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    phrase: str
    location: str
    motion: str
    risk: int
    min_helpers: int
    needs: str
    spill_text: str
    safe_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)
    power: int = 0
    sense: int = 0
    use_text: str = ""
    fail_text: str = ""
    qa_text: str = ""


@dataclass
class StoryParams:
    venue: str
    hazard: str
    tool: str
    leader: str
    leader_gender: str
    partner: str
    partner_gender: str
    adult: str
    helpers: int = 2
    delay: int = 0
    rhyme: str = "steady"
    seed: Optional[int] = None


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


class World:
    def __init__(self, venue: Venue) -> None:
        self.venue = venue
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"leader", "partner", "helper"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.venue)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["wobble"] < THRESHOLD:
            continue
        sig = ("wobble", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "room" in world.entities:
            world.get("room").meters["danger"] += 1
        for kid in world.kids():
            kid.memes["worry"] += 1
        out.append("__wobble__")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["spilled"] < THRESHOLD:
            continue
        sig = ("spill", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "floor" in world.entities:
            world.get("floor").meters["messy"] += 1
        if "luncheon" in world.entities:
            world.get("luncheon").meters["lost_food"] += 1
        for kid in world.kids():
            kid.memes["sad"] += 1
        out.append("__spill__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="spill", tag="physical", apply=_r_spill),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


VENUES = {
    "cafeteria": Venue(
        id="cafeteria",
        label="the school cafeteria",
        opening="Long paper stars hung over the tables, and the whole school cafeteria felt like a hero headquarters.",
        affords={"juice_jug", "soup_tureen", "sandwich_tower"},
        tags={"cafeteria", "luncheon"},
    ),
    "courtyard": Venue(
        id="courtyard",
        label="the sunny courtyard",
        opening="The sunny courtyard was dressed for a hero luncheon, with bright cloths snapping softly in the breeze.",
        affords={"juice_jug", "sandwich_tower"},
        tags={"courtyard", "luncheon"},
    ),
    "community_hall": Venue(
        id="community_hall",
        label="the community hall",
        opening="The community hall glowed with streamers and lunch tables, ready for a neighborhood superhero luncheon.",
        affords={"juice_jug", "soup_tureen", "sandwich_tower"},
        tags={"hall", "luncheon"},
    ),
}

HAZARDS = {
    "juice_jug": Hazard(
        id="juice_jug",
        label="juice jug",
        phrase="a tall glass juice jug",
        location="on the drink table",
        motion="trembling near the edge",
        risk=2,
        min_helpers=2,
        needs="steady",
        spill_text="orange juice sloshed over the cloth and ran in shiny streams across the floor",
        safe_text="the juice settled with a soft glug, and not one drop escaped",
        tags={"juice", "spill"},
    ),
    "soup_tureen": Hazard(
        id="soup_tureen",
        label="soup tureen",
        phrase="a warm soup tureen",
        location="on a rolling cart",
        motion="shivering as one wheel kept turning",
        risk=3,
        min_helpers=3,
        needs="brace",
        spill_text="golden soup splashed from the tureen, and the cart left a warm trail behind it",
        safe_text="the cart stopped, the lid rattled once, and the soup stayed snug inside",
        tags={"soup", "spill"},
    ),
    "sandwich_tower": Hazard(
        id="sandwich_tower",
        label="sandwich tower",
        phrase="a tall sandwich tower",
        location="by the fan table",
        motion="leaning like a wobbly block castle",
        risk=2,
        min_helpers=2,
        needs="catch",
        spill_text="sandwiches slid in soft little landslides, and lettuce fluttered onto the floor",
        safe_text="the tower stood straight again, neat as a little delicious castle",
        tags={"sandwich", "spill"},
    ),
}

TOOLS = {
    "tray": Tool(
        id="tray",
        label="serving tray",
        phrase="a wide serving tray",
        tags={"steady", "catch"},
        power=2,
        sense=3,
        use_text="slid the wide serving tray under the danger and held it level while the others guided the food back to safety",
        fail_text="got the serving tray there, but not quickly enough to catch everything",
        qa_text="used a wide serving tray to support the wobbling food",
    ),
    "cart_brake": Tool(
        id="cart_brake",
        label="cart brake",
        phrase="the little cart brake",
        tags={"brace"},
        power=3,
        sense=3,
        use_text="clicked the little cart brake into place while the others steadied the tureen with careful hands",
        fail_text="reached for the cart brake, but the cart rolled one shake too far before it clicked",
        qa_text="clicked the cart brake on while the team steadied the cart",
    ),
    "folded_towels": Tool(
        id="folded_towels",
        label="folded towels",
        phrase="a stack of folded towels",
        tags={"steady", "brace"},
        power=2,
        sense=2,
        use_text="tucked folded towels under the shaky side and pressed gently until the wobble stopped",
        fail_text="stuffed towels under the edge, but the lunch thing was already tipping too hard",
        qa_text="used folded towels to prop the shaky side",
    ),
    "superhero_leap": Tool(
        id="superhero_leap",
        label="superhero leap",
        phrase="a flying superhero leap",
        tags={"flash"},
        power=1,
        sense=1,
        use_text="made a flying superhero leap toward the problem",
        fail_text="made a flying superhero leap that looked brave but did not make the food any safer",
        qa_text="tried to save it with a flashy leap",
    ),
}

RHYMES = {
    "steady": '“Steady and ready, side by side!\nLunch stays safe when heroes guide!”',
    "carry": '“Careful and merry, one-two-three!\nHelping hands are super, see?”',
    "brace": '“Brace with grace, do not race!\nTeamwork keeps lunch in its place!”',
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]


def hazard_supported(hazard: Hazard, tool: Tool) -> bool:
    return hazard.needs in tool.tags


def sensible_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for vid, venue in VENUES.items():
        for hid in sorted(venue.affords):
            hazard = HAZARDS[hid]
            for tid, tool in TOOLS.items():
                if hazard_supported(hazard, tool) and tool.sense >= SENSE_MIN:
                    combos.append((vid, hid, tid))
    return sorted(combos)


def support_score(hazard: Hazard, tool: Tool, helpers: int, delay: int) -> int:
    return tool.power + helpers - delay


def is_saved(hazard: Hazard, tool: Tool, helpers: int, delay: int) -> bool:
    if helpers < hazard.min_helpers:
        return False
    return support_score(hazard, tool, helpers, delay) >= hazard.risk + hazard.min_helpers


def predict_attempt(world: World, hazard_id: str, tool_id: str, helpers: int, delay: int) -> dict:
    sim = world.copy()
    hazard_ent = sim.get("hazard")
    tool = TOOLS[tool_id]
    hazard = HAZARDS[hazard_id]
    if is_saved(hazard, tool, helpers, delay):
        hazard_ent.meters["wobble"] = 0.0
    else:
        hazard_ent.meters["spilled"] += 1
        propagate(sim, narrate=False)
    return {
        "saved": hazard_ent.meters["spilled"] < THRESHOLD,
        "mess": sim.get("floor").meters["messy"] if "floor" in sim.entities else 0.0,
    }


def introduce(world: World, leader: Entity, partner: Entity, venue: Venue, adult: Entity) -> None:
    leader.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f"{leader.id} and {partner.id} came to {venue.label} wearing paper capes for a special luncheon. "
        f"{venue.opening}"
    )
    world.say(
        f"{adult.label_word.capitalize()} had called it the Helping Hands Luncheon, because everyone would eat and share together."
    )


def hero_play(world: World, leader: Entity, partner: Entity) -> None:
    world.say(
        f'“Captain Comet and Mighty Maple!” {leader.id} whispered, pointing first at {partner.id} and then at {leader.pronoun("object")}. '
        f'The two friends were sure every table needed a superhero team.'
    )


def spot_hazard(world: World, hazard: Hazard) -> None:
    h = world.get("hazard")
    h.meters["wobble"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then they saw {hazard.phrase} {hazard.location}, {hazard.motion}. "
        f"The whole luncheon suddenly felt a little less like a game."
    )


def tempt(world: World, leader: Entity) -> None:
    leader.memes["flash"] += 1
    world.say(
        f'{leader.id} took one quick step forward. “I can dash in alone!” {leader.pronoun()} said.'
    )


def warn(world: World, partner: Entity, leader: Entity, hazard: Hazard, tool: Tool, helpers: int, delay: int) -> None:
    pred = predict_attempt(world, hazard.id, tool.id, helpers, delay)
    partner.memes["calm"] += 1
    world.facts["predicted_saved"] = pred["saved"]
    world.facts["predicted_mess"] = pred["mess"]
    world.say(
        f'{partner.id} reached for {leader.pronoun("possessive")} cape. “Use a sober plan,” {partner.pronoun()} said in a small, steady voice. '
        f'“Real heroes do not just jump. They look, think, and help.”'
    )


def gather_team(world: World, leader: Entity, partner: Entity, adult: Entity, helpers: int, rhyme: str) -> None:
    leader.memes["calm"] += 1
    partner.memes["brave"] += 1
    world.say(
        f"{leader.id} stopped, took a breath, and nodded. Soon {helpers} children stood in a line with {partner.id}, "
        f"while {adult.label_word} cleared a little space and watched with careful eyes."
    )
    world.say(RHYMES[rhyme])


def rescue(world: World, hazard: Hazard, tool: Tool, helpers: int) -> None:
    h = world.get("hazard")
    h.meters["wobble"] = 0.0
    world.get("room").meters["danger"] = 0.0
    world.get("luncheon").meters["saved_food"] += 1
    for kid in world.kids():
        kid.memes["pride"] += 1
        kid.memes["worry"] = 0.0
    world.say(
        f"Together they moved as if the rhyme had tied their steps together. One child brought {tool.phrase}; "
        f"the team {tool.use_text}. {hazard.safe_text}"
    )
    world.say(
        f"A little cheer skipped across the tables. The luncheon was safe, and the capes suddenly felt earned."
    )


def spill(world: World, hazard: Hazard, tool: Tool, helpers: int) -> None:
    h = world.get("hazard")
    h.meters["spilled"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They tried hard, but the moment was too quick. One child grabbed {tool.phrase}, and the team {tool.fail_text}. "
        f"Instead, {hazard.spill_text}"
    )
    world.say(
        "For one quiet second, nobody felt super at all."
    )


def cleanup(world: World, adult: Entity, leader: Entity, partner: Entity) -> None:
    floor = world.get("floor")
    floor.meters["messy"] = 0.0
    for kid in world.kids():
        kid.memes["lesson"] += 1
        kid.memes["sad"] = 0.0
        kid.memes["pride"] += 1
    world.say(
        f"Then {adult.label_word} knelt beside them. “A mess is not the end of helping,” {adult.pronoun()} said. "
        f"“Heroes can fetch towels too.”"
    )
    world.say(
        f"So {leader.id}, {partner.id}, and the others wiped, lifted, and set the room right again. "
        f"By the time the floor was clean, their teamwork felt stronger than any flashy move."
    )


def ending_saved(world: World, leader: Entity, partner: Entity, hazard: Hazard) -> None:
    world.say(
        f"At last everyone sat down again. {leader.id} passed plates, {partner.id} poured carefully, "
        f"and the saved {hazard.label} stood calm in the middle like a trophy for teamwork."
    )
    world.say(
        "The heroes ate their luncheon with bright smiles, and every crumb seemed to say that helping side by side was the truest superpower."
    )


def ending_after_cleanup(world: World, leader: Entity, partner: Entity) -> None:
    world.say(
        f"When the room was neat again, there was still enough luncheon left for everyone to share. "
        f"{leader.id} and {partner.id} sat shoulder to shoulder, their paper capes a little crooked and their hearts much steadier."
    )
    world.say(
        "They were not proud of the spill, but they were proud that they stayed, cleaned, and helped. That was a sober kind of heroism."
    )


def tell(
    venue: Venue,
    hazard: Hazard,
    tool: Tool,
    leader_name: str,
    leader_gender: str,
    partner_name: str,
    partner_gender: str,
    adult_type: str,
    helpers: int,
    delay: int,
    rhyme: str,
) -> World:
    world = World(venue)
    leader = world.add(Entity(id=leader_name, kind="character", type=leader_gender, role="leader"))
    partner = world.add(Entity(id=partner_name, kind="character", type=partner_gender, role="partner"))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type, role="adult", label="the adult"))
    for i in range(max(0, helpers - 2)):
        world.add(Entity(id=f"Helper{i+1}", kind="character", type="child", role="helper", label="helper child"))
    world.add(Entity(id="room", type="room", label=venue.label))
    world.add(Entity(id="floor", type="floor", label="the floor"))
    world.add(Entity(id="luncheon", type="meal", label="luncheon"))
    hazard_ent = world.add(Entity(id="hazard", type="hazard", label=hazard.label, phrase=hazard.phrase))
    tool_ent = world.add(Entity(id="tool", type="tool", label=tool.label, phrase=tool.phrase))
    tool_ent.attrs["sense"] = tool.sense
    hazard_ent.attrs["risk"] = hazard.risk

    introduce(world, leader, partner, venue, adult)
    hero_play(world, leader, partner)

    world.para()
    spot_hazard(world, hazard)
    tempt(world, leader)
    warn(world, partner, leader, hazard, tool, helpers, delay)

    world.para()
    gather_team(world, leader, partner, adult, helpers, rhyme)

    saved = is_saved(hazard, tool, helpers, delay)
    if saved:
        rescue(world, hazard, tool, helpers)
        world.para()
        ending_saved(world, leader, partner, hazard)
    else:
        spill(world, hazard, tool, helpers)
        world.para()
        cleanup(world, adult, leader, partner)
        world.para()
        ending_after_cleanup(world, leader, partner)

    world.facts.update(
        venue=venue,
        hazard_cfg=hazard,
        tool_cfg=tool,
        leader=leader,
        partner=partner,
        adult=adult,
        helpers=helpers,
        delay=delay,
        rhyme=rhyme,
        outcome="saved" if saved else "spilled",
        used_teamwork=helpers >= 2,
        luncheon_saved=saved,
        mess_happened=not saved,
        tool_entity=tool_ent,
    )
    return world


KNOWLEDGE = {
    "luncheon": [
        (
            "What is a luncheon?",
            "A luncheon is a meal eaten in the middle of the day. It is another word for lunch, often used when the meal feels a little special."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people helping one another toward the same goal. Each person does a part, and together they can do more than one person alone."
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme uses words that sound alike, like side and guide. Rhymes can help people remember a plan."
        )
    ],
    "sober": [
        (
            "What does sober mean in a story like this?",
            "Here, sober means calm, serious, and thoughtful. A sober plan is one made carefully instead of in a wild rush."
        )
    ],
    "juice": [
        (
            "Why can a big juice jug spill easily?",
            "A tall jug can tip if it is close to an edge or if the table shakes. Once the liquid starts moving, it can slosh out quickly."
        )
    ],
    "soup": [
        (
            "Why should people be careful around hot soup?",
            "Hot soup can splash and make a messy, uncomfortable spill. That is why people carry it slowly and keep the cart or bowl steady."
        )
    ],
    "sandwich": [
        (
            "Why might a sandwich tower wobble?",
            "A tall stack can lean if the layers are uneven or if air moves around it. The higher it gets, the easier it is to tip."
        )
    ],
    "tray": [
        (
            "What does a serving tray do?",
            "A serving tray gives food a flat surface to rest on. It helps people support and carry dishes more safely."
        )
    ],
    "brake": [
        (
            "What does a cart brake do?",
            "A cart brake stops the wheels from rolling. That helps keep the cart still while someone serves or steadies it."
        )
    ],
    "towels": [
        (
            "Why can towels help with a wobble or spill?",
            "Folded towels can prop something a little, and towels can also soak up a mess. They are soft, useful helpers in a lunchroom."
        )
    ],
}

KNOWLEDGE_ORDER = [
    "luncheon",
    "teamwork",
    "rhyme",
    "sober",
    "juice",
    "soup",
    "sandwich",
    "tray",
    "brake",
    "towels",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    leader, partner = f["leader"], f["partner"]
    hazard, tool = f["hazard_cfg"], f["tool_cfg"]
    return [
        'Write a short superhero story for a 3-to-5-year-old that includes the words "luncheon" and "sober", uses teamwork, and includes a rhyme.',
        f"Tell a gentle superhero luncheon story where {leader.id} wants to make a flashy solo save, but {partner.id} asks for a sober plan and the team uses {tool.label} to handle a wobbling {hazard.label}.",
        "Write a child-facing story in which paper-cape heroes learn that real superpowers can look like calm thinking, helping hands, and a rhyme said together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    adult = f["adult"]
    hazard = f["hazard_cfg"]
    tool = f["tool_cfg"]
    helpers = f["helpers"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {leader.id} and {partner.id}, two children at a superhero luncheon. A careful adult was nearby while they tried to help."
        ),
        (
            "What problem appeared at the luncheon?",
            f"They noticed {hazard.phrase} {hazard.location} starting to wobble. That mattered because it could spill food and spoil the luncheon."
        ),
        (
            f"Why did {partner.id} ask for a sober plan?",
            f"{partner.id} did not want a flashy jump to make the wobble worse. A sober plan meant stopping to think so the team could help in a safer way."
        ),
        (
            "What did the rhyme do in the story?",
            "The rhyme helped the children move together instead of rushing in different ways. It turned their teamwork into one calm plan."
        ),
    ]
    if outcome == "saved":
        qa.append(
            (
                "How did the children save the luncheon?",
                f"They worked as a team of {helpers} and {tool.qa_text}. Because enough helpers moved together with the right tool, the wobble stopped before anything spilled."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with everyone sitting down to eat the luncheon, and the food was safe. The calm ending shows that teamwork changed danger into sharing."
            )
        )
    else:
        qa.append(
            (
                "Did their first rescue work?",
                f"No. They tried to help, but the problem was too hard in that moment and food spilled. Even so, they stayed to clean up together instead of giving up."
            )
        )
        qa.append(
            (
                f"What did {adult.label_word} teach them after the spill?",
                f"{adult.label_word.capitalize()} taught them that helping is not over when a mistake happens. Cleaning the mess together was another kind of hero work."
            )
        )
        qa.append(
            (
                "How did the story end?",
                "It ended quietly, with the room clean again and enough luncheon left to share. The children felt steadier because they had learned to help together after the mistake."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"luncheon", "teamwork", "rhyme", "sober"}
    hazard = f["hazard_cfg"]
    tool = f["tool_cfg"]
    if hazard.id == "juice_jug":
        tags.add("juice")
    elif hazard.id == "soup_tureen":
        tags.add("soup")
    elif hazard.id == "sandwich_tower":
        tags.add("sandwich")
    if tool.id == "tray":
        tags.add("tray")
    elif tool.id == "cart_brake":
        tags.add("brake")
    elif tool.id == "folded_towels":
        tags.add("towels")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:9} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        venue="cafeteria",
        hazard="juice_jug",
        tool="tray",
        leader="Lily",
        leader_gender="girl",
        partner="Tom",
        partner_gender="boy",
        adult="teacher_woman",
        helpers=2,
        delay=0,
        rhyme="steady",
    ),
    StoryParams(
        venue="community_hall",
        hazard="soup_tureen",
        tool="cart_brake",
        leader="Max",
        leader_gender="boy",
        partner="Mia",
        partner_gender="girl",
        adult="teacher_man",
        helpers=3,
        delay=0,
        rhyme="brace",
    ),
    StoryParams(
        venue="courtyard",
        hazard="sandwich_tower",
        tool="tray",
        leader="Ava",
        leader_gender="girl",
        partner="Ben",
        partner_gender="boy",
        adult="teacher_woman",
        helpers=2,
        delay=1,
        rhyme="carry",
    ),
    StoryParams(
        venue="cafeteria",
        hazard="soup_tureen",
        tool="folded_towels",
        leader="Sam",
        leader_gender="boy",
        partner="Zoe",
        partner_gender="girl",
        adult="teacher_man",
        helpers=2,
        delay=1,
        rhyme="brace",
    ),
]


def explain_rejection(venue: Venue, hazard: Hazard, tool: Tool) -> str:
    if hazard.id not in venue.affords:
        return (
            f"(No story: {venue.label} does not fit a {hazard.label} scene here. "
            f"Pick a hazard that this venue can reasonably host.)"
        )
    if tool.sense < SENSE_MIN:
        return (
            f"(Refusing tool '{tool.id}': it scores too low on common sense "
            f"(sense={tool.sense} < {SENSE_MIN}). This world prefers calm, sensible rescue tools.)"
        )
    return (
        f"(No story: {tool.label} does not really solve a {hazard.label} problem. "
        f"Pick a tool that can {hazard.needs} the lunch safely.)"
    )


def outcome_of(params: StoryParams) -> str:
    hazard = HAZARDS[params.hazard]
    tool = TOOLS[params.tool]
    return "saved" if is_saved(hazard, tool, params.helpers, params.delay) else "spilled"


ASP_RULES = r"""
% reasonableness gate
valid(V, H, T) :- venue(V), hazard(H), tool(T), affords(V, H), sensible(T), supports(T, Need), needs(H, Need).

% outcome model
saved :- chosen_hazard(H), chosen_tool(T), helpers(N), min_helpers(H, MH), N >= MH,
         power(T, P), risk(H, R), delay(D), P + N - D >= R + MH.
outcome(saved) :- saved.
outcome(spilled) :- not saved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for vid, venue in VENUES.items():
        lines.append(asp.fact("venue", vid))
        for hid in sorted(venue.affords):
            lines.append(asp.fact("affords", vid, hid))
    for hid, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("risk", hid, hazard.risk))
        lines.append(asp.fact("min_helpers", hid, hazard.min_helpers))
        lines.append(asp.fact("needs", hid, hazard.needs))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("power", tid, tool.power))
        lines.append(asp.fact("sense", tid, tool.sense))
        for tag in sorted(tool.tags):
            lines.append(asp.fact("supports", tid, tag))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append("sensible(T) :- tool(T), sense(T, S), sense_min(M), S >= M.")
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_hazard", params.hazard),
            asp.fact("chosen_tool", params.tool),
            asp.fact("helpers", params.helpers),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny superhero luncheon storyworld with teamwork, rhyme, and calm problem-solving."
    )
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helpers", type=int, choices=[1, 2, 3, 4], help="number of children helping in the rescue")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how much head start the wobble gets before the team acts")
    ap.add_argument("--adult", choices=["teacher_woman", "teacher_man"])
    ap.add_argument("--rhyme", choices=sorted(RHYMES))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.venue and args.hazard and args.tool:
        venue = VENUES[args.venue]
        hazard = HAZARDS[args.hazard]
        tool = TOOLS[args.tool]
        if args.hazard not in venue.affords or tool.sense < SENSE_MIN or not hazard_supported(hazard, tool):
            raise StoryError(explain_rejection(venue, hazard, tool))
    if args.tool:
        tool = TOOLS[args.tool]
        if tool.sense < SENSE_MIN:
            venue = VENUES[args.venue] if args.venue else next(iter(VENUES.values()))
            hazard = HAZARDS[args.hazard] if args.hazard else next(iter(HAZARDS.values()))
            raise StoryError(explain_rejection(venue, hazard, tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.venue is None or combo[0] == args.venue)
        and (args.hazard is None or combo[1] == args.hazard)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    venue_id, hazard_id, tool_id = rng.choice(combos)
    leader_gender = rng.choice(["girl", "boy"])
    partner_gender = rng.choice(["girl", "boy"])
    leader = _pick_name(rng, leader_gender)
    partner = _pick_name(rng, partner_gender, avoid=leader)
    adult = args.adult or rng.choice(["teacher_woman", "teacher_man"])
    helpers = args.helpers if args.helpers is not None else rng.choice([2, 2, 3, 3, 4])
    delay = args.delay if args.delay is not None else rng.choice([0, 0, 1])
    rhyme = args.rhyme or rng.choice(sorted(RHYMES))
    return StoryParams(
        venue=venue_id,
        hazard=hazard_id,
        tool=tool_id,
        leader=leader,
        leader_gender=leader_gender,
        partner=partner,
        partner_gender=partner_gender,
        adult=adult,
        helpers=helpers,
        delay=delay,
        rhyme=rhyme,
    )


def generate(params: StoryParams) -> StorySample:
    if params.venue not in VENUES:
        raise StoryError(f"(Unknown venue: {params.venue})")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard: {params.hazard})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.rhyme not in RHYMES:
        raise StoryError(f"(Unknown rhyme: {params.rhyme})")
    venue = VENUES[params.venue]
    hazard = HAZARDS[params.hazard]
    tool = TOOLS[params.tool]
    if params.hazard not in venue.affords or tool.sense < SENSE_MIN or not hazard_supported(hazard, tool):
        raise StoryError(explain_rejection(venue, hazard, tool))
    if params.helpers < 1:
        raise StoryError("(Helpers must be at least 1.)")

    world = tell(
        venue=venue,
        hazard=hazard,
        tool=tool,
        leader_name=params.leader,
        leader_gender=params.leader_gender,
        partner_name=params.partner,
        partner_gender=params.partner_gender,
        adult_type=params.adult,
        helpers=params.helpers,
        delay=params.delay,
        rhyme=params.rhyme,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    rc = 0

    py_combos = set(valid_combos())
    asp_combos = set(asp_valid_combos())
    if py_combos == asp_combos:
        print(f"OK: gate matches valid_combos() ({len(py_combos)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_combos - asp_combos:
            print("  only in python:", sorted(py_combos - asp_combos))
        if asp_combos - py_combos:
            print("  only in clingo:", sorted(asp_combos - py_combos))

    scenarios: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        scenarios.append(params)

    mismatches = []
    for params in scenarios:
        py_out = outcome_of(params)
        asp_out = asp_outcome(params)
        if py_out != asp_out:
            mismatches.append((params, py_out, asp_out))
    if not mismatches:
        print(f"OK: outcome model matches on {len(scenarios)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome differences.")
        for params, py_out, asp_out in mismatches[:5]:
            print(f"  {params} -> python={py_out} asp={asp_out}")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "luncheon" not in sample.story.lower():
            raise StoryError("(Smoke test failed: story did not render as expected.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (venue, hazard, tool) combos:\n")
        for venue, hazard, tool in combos:
            print(f"  {venue:14} {hazard:15} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.leader} & {p.partner}: {p.hazard} at {p.venue} with {p.tool} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
