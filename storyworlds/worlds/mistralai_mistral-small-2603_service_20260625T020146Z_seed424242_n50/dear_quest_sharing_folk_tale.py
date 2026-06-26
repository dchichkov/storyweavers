#!/usr/bin/env python3
"""
storyworlds/worlds/dear_quest_sharing_folk_tale.py
==================================================

A folk-tale style story world centered on a quest for something "dear"
and the virtue of sharing.  State-driven narrative driven by physical meters
and emotional memes.

Initial seed:
---
Once upon a time in a quiet village nestled between rolling green hills, there lived
a dear child named Elara. Every evening Elara would sit under the old oak tree
with their grandmother's locket held close, listening to tales of heroic quests.

One day Elara realized the locket's chain was broken. Without it, Elara felt
something important was missing. Elara pondered: "If I go on a quest to find
the pieces of the chain, where should I search?"

The village elder smiled thoughtfully and said, "The dearest treasures often
lie where sharing happens — in the giving and receiving, not just the finding.
Have you considered asking the travelers on the forest road?"

Elara set off toward the whispering pines where the forest road began.
Along the path, Elara met:
- A fox carrying berries who had lost three to a bird in need
- A squirrel who shared half of their winter nut store with a shivering sparrow
- A baker whose fresh bread was still warm enough to share with all who passed

Each sharing act lit Elara's path like lanterns. When Elara finally reached
the mossy bend where the chain pieces lay scattered, Elara understood:
the true dear wasn't the locket itself, but the connections made along the way.

Causal state updates:
---
    perform sharing act         -> actor.generosity += 1
                                   actor.belonging += 1 (recipient feels valued)
    receive sharing             -> actor.gratitude += 1
    wear dear object            -> actor.closeness += 1
    quest incomplete            -> actor.purpose += 1
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

# Make the shared result containers importable when this script is run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Threshold for narrating accumulated effects
THRESHOLD = 0.8

# Emotional metrics used in this domain
MEME_KEYS = {"generosity", "gratitude", "purpose", "regret", "belonging", "closeness"}

# Physical meters used
METER_KEYS = {"distance", "burden", "discoveries"}

# Regions in this forest world (foot path is the main route)
REGIONS = {"path", "glade", "hillside", "brookside"}

# ---------------------------------------------------------------------------
# Entities: characters, items, places share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "simple"           # child, elder, fox, squirrel, locket, chain, etc.
    label: str = ""                # short reference for narration
    phrase: str = ""               # full noun phrase
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    region: str = ""
    plural: bool = False
    # Two numeric dimensions, treated uniformly:
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "grandmother", "woman", "squirrel", "doe"}
        male = {"boy", "elder", "fox", "stag"}
        # Treat animals neutrally by default
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        it = "them" if self.plural else "it"
        return {"subject": it, "object": it, "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandmother", "elder": "elder", "doe": "doe"}.get(self.type, self.type)

# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this folk-tale domain.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str               # village, forest, glade, crossroads
    weather: str = ""
    indoor: bool = False
    affords: set[str] = field(default_factory=set)  # which activities this place supports

@dataclass
class Activity:
    """A key action in the quest/sharing narrative."""
    id: str                 # journey, sharing_help, quest_begin, etc.
    verb: str               # "start their quest"
    gerund: str             # "seeking their dearest treasure"
    effect: str = ""        # short descriptive effect clause
    cost: str = ""          # what it requires ("a kindness to share", "two days' travel")
    keyword: str = ""       # topic word for generation prompts
    tags: set[str] = field(default_factory=set)

@dataclass
class Prize:
    """The "dear" thing the hero seeks; can be object or virtue."""
    id: str
    label: str
    phrase: str
    type: str = "object"    # object OR virtue
    plural: bool = False
    holders: set[str] = field(default_factory=set)  # who plausibly values this

@dataclass
class Companion:
    """Ally encountered along the quest who embodies sharing."""
    id: str
    label: str
    phrase: str
    trait: str = ""         # "generous", "wise", etc.
    offers: set[str] = field(default_factory=set)  # what they can share
    region: str = ""

# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()       # idempotency for rule engine
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()          # current story zone
        self.choices: list[tuple] = []       # key choices made during story
        # Facts recorded during the screenplay for grounded Q&A
        self.facts: dict = {}

    # -- entity helpers -----------------------------------------------------
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def items(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "thing"]

    def owned_by(self, actor: Entity) -> list[Entity]:
        return [e for e in self.items() if e.owner == actor.id]

    # -- narration helpers --------------------------------------------------
    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        """Throwaway clone used for forward-simulation (prediction)."""
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.choices = list(self.choices)
        clone.paragraphs = [[]]  # predictions are silent
        return clone

# ---------------------------------------------------------------------------
# Causal rules: forward-chained to a fixpoint.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_purpose_from_journey(world: World) -> list[str]:
    """Completing each leg of the journey increases purpose."""
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["purpose"] > 0:
            continue
        # Mark journey completion; actual narration uses screenplay verbs
        for leg in ("path", "glade", "brookside"):
            sig = ("journey_leg", actor.id, leg)
            if sig not in world.fired and world.zone and leg in world.zone:
                world.fired.add(sig)
                continue
        pass  # Rule fires through screenplay verbs below; this rule handles embedded effects
    return out

def _r_embodied_sharing(world: World) -> list[str]:
    """Performing sharing acts leaves emotional traces."""
    out: list[str] = []
    for actor in world.characters():
        gen = actor.memes.get("generosity", 0)
        if gen >= THRESHOLD:
            sig = ("sharing_trace", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                out.append(f"{actor.pronoun().capitalize()} felt warmth inside from the sharing.")
        # Receiving help also leaves traces
        grat = actor.memes.get("gratitude", 0)
        if grat >= THRESHOLD:
            sig = ("gratitude_trace", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                out.append(f"{actor.pronoun().capitalize()} carried the kindness close afterward.")
    return out

def _r_dear_object_connection(world: World) -> list[str]:
    """Wearing or holding a dear object increases closeness to it."""
    for actor in world.characters():
        for item in world.items():
            if item.owner == actor.id and "dear" in item.phrase.lower():
                sig = ("wear_dear", actor.id, item.id)
                if sig not in world.fired and item.meters.get("closeness", 0) >= THRESHOLD:
                    world.fired.add(sig)
                    item.meters["closeness"] += 1
                    out = [f"{item.phrase} felt like part of {actor.pronoun('object')} now."]
                    return out
    return []

CAUSAL_RULES: list[Rule] = [
    Rule(name="purpose", tag="quest", apply=_r_purpose_from_journey),
    Rule(name="sharing_trace", tag="social", apply=_r_embodied_sharing),
    Rule(name="dear_connection", tag="object", apply=_r_dear_object_connection),
]

def propagate(world: World, narrate: bool = True) -> list[str]:
    """Apply all rules until nothing new fires (forward chaining)."""
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced

# ---------------------------------------------------------------------------
# Constraint helpers and registry logics.
# ---------------------------------------------------------------------------
def prize_is_valued(activity: Activity, prize: Prize) -> bool:
    """Does the quest make sense for this prize?"""
    return "quest" in activity.tags and prize.type == "virtue"

def sharing_matches(activity: Activity, companion: Companion) -> bool:
    """Does this companion's sharing align with the activity?"""
    return "sharing" in activity.tags and "sharing" in companion.offers

# ---------------------------------------------------------------------------
# Prediction helpers for the world model.
# ---------------------------------------------------------------------------
def predict_completion(world: World, actor: Entity, activity: Activity, prize: Prize) -> dict:
    """Simulate quest completion to verify reasonable ending."""
    sim = world.copy()
    # Simulate journey completion
    sim.zone = set(world.zone)
    sim.get(actor.id).memes["purpose"] = 1.2
    return {"fulfilled": True, "reward": "deepened_understanding"}

# ---------------------------------------------------------------------------
# Verbs and screenplay beats that mutate state.
# ---------------------------------------------------------------------------
def begin_quest(world: World, actor: Entity, prize: Prize) -> None:
    actor.memes["purpose"] += 1.0
    world.say(
        f"{actor.pronoun().capitalize()} adjusted {actor.pronoun('possessive')} "
        f"{prize.label} close and set {actor.pronoun('object')} off toward "
        f"{world.setting.place}."
    )
    world.facts["quest_begin"] = True

def meet_companion(world: World, actor: Entity, companion: Companion) -> None:
    actor.memes["gratitude"] += 0.8
    companion.memes["generosity"] += 0.7
    world.zone.update([companion.region])
    world.say(
        f"As {actor.pronoun()} walked {world.zone.pop() if world.zone else 'along the path'}, "
        f"{companion.id} appeared from behind {companion.labels.split()[0]}."
    )
    world.say(
        f'"Follow the lantern path," {companion.id} offered, "where sharing keeps the '
        f'forest bright."'
    )

def perform_sharing(world: World, actor: Entity, companion: Companion) -> None:
    actor.memes["generosity"] += 0.6
    companion.memes["gratitude"] += 0.5
    world.say(
        f"{actor.id} paused and {actor.pronoun('object')} had — a small kindness to share. "
        f"{actor.pronoun().capitalize()} {actor.pronoun('object')} with {companion.pronoun('object')}, "
        f"and {companion.pronoun()} smiled as {companion.pronoun('object')} accepted."
    )
    world.choices.append(("share", companion.id))

def reflect_on_dear(world: World, actor: Entity, prize: Prize) -> None:
    actor.memes["closeness"] += 0.9
    prize.meters["closeness"] += 0.9
    world.say(
        f"Later, under the starlight, {actor.id} held {prize.phrase} and realized "
        f"that {prize.it()} was {prize.phrase} all along — not the thing itself, "
        f"but the way {actor.id} had {actor.pronoun('object')} with {actor.pronoun('possessive')} world."
    )
    world.facts["quest_resolved"] = True

def return_home(world: World, actor: Entity, prize: Prize) -> None:
    world.say(
        f"When {actor.id} stepped back into the village, "
        f"their {prize.label} felt lighter and their heart felt fuller. "
        f"'What a quest!' {actor.pronoun('possessive')} {prize.label_word} remarked with a nod."
    )
    world.facts["quest_complete"] = True

# ---------------------------------------------------------------------------
# Narration fragments by activity/topic.
# ---------------------------------------------------------------------------
def story_openers(setting: Setting) -> list[str]:
    indoor = "indoors" if setting.indoor else "out beneath the open sky"
    weather = {"rainy": "soft rain", "sunny": "warm sunshine"}.get(setting.weather, "quiet evening")
    place_name = setting.place.replace("_", " ")
    return [
        f"Once there was a village {indoor} where {place_name} sat waiting under {weather}.",
        f"Long ago, in a land where the trees remember old stories, there stood {setting.place}.",
        f"It was an evening like any other in the quiet village of {place_name if not setting.indoor else 'the cottage'}, "
        f"until someone knew it was time for a quest.",
    ]

def quest_detail(activity: Activity) -> str:
    return {
        "journey": "the winding path between village and forest",
        "sharing_help": "the gentle exchange of small but meaningful gifts",
        "quest_begin": "a promise to learn what matters most",
    }.get(activity.id, "the journey home with a new understanding")

# ---------------------------------------------------------------------------
# The screenplay: three-act folk tale.
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize: Prize,
         hero_name: str = "Elara", hero_gender: str = "girl",
         companion_types: Optional[list[str]] = None) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label="young one",
        phrase=f"Elara the {hero_gender}",
        traits=["curious", "kind-hearted"],
    ))

    dear_obj = world.add(Entity(
        id="cherished",
        kind="thing",
        type="dear_object",
        label=prize.label,
        phrase=prize.phrase,
        owner=hero.id,
    ))

    # Act 1: The Broken Dear
    world.paragraphs = [[]]
    opener = random.choice(story_openers(setting))
    world.say(opener)
    world.para()

    if prize.type == "object":
        world.say(
            f"Every week {hero.id} visited the old oak to hold {dear_obj.phrase}, "
            f"but this morning {dear_obj.it()} felt different."
        )
        world.say(f"Then {hero.pronoun()} saw — {dear_obj.label}’s silver chain was broken.")
        hero.memes["regret"] = 0.7
    else:  # virtue quest
        world.say(
            f"{hero.id} had heard whispers in the hearth-fire that something "
            f"precious to the village was fading — {prize.phrase}."
        )
        hero.memes["purpose"] = 0.5

    world.say(f"{hero.pronoun().capitalize()} knew what to do: {activity.verb}.")
    world.para()

    # Act 2: Companions and Sharing
    companions = companion_types or ["fox", "squirrel", "elder"]
    for cid in companions[:2]:  # pick two companions
        companion = COMPANIONS[cid]
        meet_companion(world, hero, companion)
        world.para()
        perform_sharing(world, hero, companion)
        hero.meters["discoveries"] = (hero.meters.get("discoveries", 0) or 0) + 0.4

    world.para()

    # Act 3: Realization and Return
    if prize.type == "object":
        world.say(
            f"{hero.id} reached the mossy bend where the chain pieces lay scattered. "
            f"The fireflies flickered as if to guide {hero.pronoun('object')}."
        )
        world.say(f"Then {hero.pronoun()} understood — the dearest thing wasn't the locket.")
    reflect_on_dear(world, hero, dear_obj)

    world.para()
    begin_quest(world, hero, dear_obj)  # framed as returning quest
    world.para()
    return_home(world, hero, dear_obj)

    # Record facts for grounded Q&A
    world.facts.update(
        hero=hero,
        prize=prize,
        activity=activity,
        setting=setting,
        quest_complete=world.facts.get("quest_complete", False),
        treasures_shared=len([ch for act, ch in world.choices if act == "share"]),
    )
    return world

# ---------------------------------------------------------------------------
# Content registries for this folk-tale world.
# ---------------------------------------------------------------------------
SETTINGS = {
    "village": Setting(
        place="the quiet village",
        indoor=False,
        affords={"journey", "sharing_help"},
    ),
    "glade": Setting(
        place="the enchanted glade",
        weather="sunny",
        indoor=False,
        affords={"quest_begin", "sharing_help"},
    ),
    "hearth_room": Setting(
        place="the cottage hearth room",
        indoor=True,
        affords={"reflect"},
    ),
}

ACTIVITIES = {
    "journey": Activity(
        id="journey",
        verb="start their quest for the dearest treasure",
        gerund="searching for what matters most",
        effect="the path ahead felt lighter when shared with others",
        cost="a willingness to let go of small treasures",
        keyword="dearest",
        tags={"quest", "sharing"},
    ),
    "sharing_help": Activity(
        id="sharing_help",
        verb="go among the travelers",
        gerund="offering kindness at every crossroads",
        effect="each shared moment lit a lantern toward home",
        cost="remembering to give before taking",
        keyword="lanterns",
        tags={"sharing"},
    ),
}

PRIZES = {
    "family_locket": Prize(
        id="family_locket",
        label="silver locket",
        phrase="family locket with grandmother’s portrait",
        type="object",
        plural=False,
        holders={"child", "grandmother"},
    ),
    "cherished_teacup": Prize(
        id="cherished_teacup",
        label="tea cup",
        phrase="red teacup with blue flowers",
        type="object",
        plural=False,
        holders={"elder", "child"},
    ),
    "true_sharing": Prize(
        id="true_sharing",
        label="true sharing",
        phrase="the understanding that sharing is its own reward",
        type="virtue",
        plural=False,
        holders={"everyone"},
    ),
}

COMPANIONS = {
    "fox": Companion(
        id="fox_companion",
        label="clever fox",
        phrase="a red fox with quick eyes",
        trait="generous",
        offers={"berries", "wisdom"},
        region="forest_path",
    ),
    "squirrel": Companion(
        id="squirrel_companion",
        label="generous squirrel",
        phrase="a plump squirrel with a bushy tail",
        trait="thoughtful",
        offers={"nuts", "shelter"},
        region="oak_grove",
    ),
    "elder": Companion(
        id="village_elder",
        label="wise elder",
        phrase="the oldest one in the village",
        trait="patient",
        offers={"stories", "advice"},
        region="village_center",
    ),
    "doe": Companion(
        id="doe_companion",
        label="gentle doe",
        phrase="a brown doe with kind eyes",
        trait="calm",
        offers={"berries", "guidance"},
        region="brookside",
    ),
}

GIRL_NAMES = ["Elara", "Liora", "Thalia", "Maya", "Sylvie"]
BOY_NAMES = ["Eamon", "Kian", "Asher", "Finn", "Robin"]
ADJECTIVES = ["gentle", "quiet", "bright", "little", "wise"]

def valid_combos() -> list[tuple[str, str, str]]:
    """Return all (place, activity, prize_id) combos that make folk-tale sense."""
    combos = []
    for place, s in SETTINGS.items():
        for act_id in s.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_is_valued(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos

# ---------------------------------------------------------------------------
# Per-world parameters dataclass.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Parameters to reproduce a single folk-tale story."""
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    companions: list[str] = field(default_factory=lambda: ["fox", "squirrel"])
    adjective: str = "gentle"
    seed: Optional[int] = None

# ---------------------------------------------------------------------------
# Q&A generation: three separate sets.
# ---------------------------------------------------------------------------
# Child world knowledge — without the story
KNOWLEDGE = {
    "dear": [
        ("What does 'dear' mean?",
         "'Dear' means something precious or loved very much, like a family heirloom."),
        ("Can people share dear things?",
         "Yes — sharing something dear doesn't lessen its value; it can make it even more special."),
    ],
    "quest": [("What is a quest?",
               "A quest is a journey to find or do something very important or precious.")],
    "sharing": [
        ("Why is sharing important?",
         "Sharing helps others feel cared for and creates connections that last."),
        ("Is sharing only about objects?",
         "No — sharing can be gifts, time, kindness, or even comforting someone."),
    ],
}
KNOWLEDGE_ORDER = ["dear", "sharing", "quest"]

def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this folk tale."""
    f = world.facts
    hero, act = f["hero"], f["activity"]
    kw = act.keyword or "dear"
    return [
        f'Write a folk-tale for ages 4–6 about "{kw}" and sharing that uses the word "lanterns". '
        f'Start with "Once upon a time..."',
        f"Tell a gentle story where a small {hero.type} named {hero.id} goes on a quest "
        f"and learns lessons through sharing.",
        f'Craft a short tale with a forest scene, two helpful animals, and ends with a warm homecoming.',
    ]

def story_qa(world: World) -> list[QAItem]:
    """(2) Questions answerable from THIS story's text."""
    f = world.facts
    hero = f["hero"]
    prize = PRIZES[f["prize"]]
    act = ACTIVITIES[f["activity"]]
    sub, pos = hero.pronoun("subject"), hero.pronoun("possessive")
    trait = hero.traits[0] if hero.traits else "kind-hearted"

    qa: list[QAItem] = [
        QAItem(
            question=f"Who went on the quest to find {pos} {prize.label}?",
            answer=f"{sub.capitalize()} {hero.id}, a {trait} {hero.type}, set {pos} on a quest.",
        ),
        QAItem(
            question=f"What happened to make {hero.id} start {act.gerund}?",
            answer=(
                f"{sub.capitalize()} {act.verb} because something important was "
                f"waiting to be understood — the {prize.phrase}."
            ),
        ),
    ]

    if f.get("treasures_shared", 0) >= 1:
        qa.append(QAItem(
            question=f"How many sharing moments did {hero.id} have on the quest?",
            answer=f"{hero.id} paused twice to share kindness with travelers.",
        ))
    if prize.type == "object":
        qa.append(QAItem(
            question=f"What did {hero.id} realize about {pos} {prize.label} at the end?",
            answer=(
                f"{sub.capitalize()} saw that {pos} {prize.label} was not just an object, "
                f"but the sharing along the way made it precious."
            ),
        ))
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Child-level world knowledge, no story needed."""
    tags = set()
    f = world.facts
    tags.add("dear")
    if f.get("activity"):
        tags.update(f["activity"].tags)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
    return out

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# CLI / trace helpers.
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v >= 0.1}
        memes = {k: v for k, v in e.memes.items() if v >= 0.1}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.region:
            bits.append(f"region={e.region}")
        notes = []
        if any(n for n, _ in world.fired if n.startswith("journey")):
            notes.append("journey_progress")
        if e.type == "dear_object":
            notes.append("dear_object")
        status = ", ".join(bits + notes)
        lines.append(f"  {e.id:12} ({e.type:12}) {status}")
    lines.append(f"  fired: {sorted({n for n,_ in world.fired})[:10]}")
    return "\n".join(lines)

# Hand-curated set used by --all
CURATED = [
    StoryParams(
        place="village",
        activity="journey",
        prize="family_locket",
        name="Elara",
        gender="girl",
        adjective="little",
    ),
    StoryParams(
        place="glade",
        activity="sharing_help",
        prize="true_sharing",
        name="Eamon",
        gender="boy",
        companions=["fox", "doe"],
        adjective="quiet",
    ),
    StoryParams(
        place="hearth_room",
        activity="journey",
        prize="cherished_teacup",
        name="Thalia",
        gender="girl",
        adjective="bright",
    ),
]

# Clingo (ASP) reasoner — declarative twin of valid_combos so they never drift
ASP_RULES = r"""
% A story is valid if the prize matches the quest theme and the setting affords the activity
prize_quest(P, A) :- prize(P), quest_activity(A), type_of(P, virtue).
companions_available(C, S) :- companion(C), setting(S), region_of(C, R), afford_path(S, R).

% Show only the stories that are valid
:- not prize_quest(Prize, Activity), place_setting(Place, Activity).
valid(Place, Activity, Prize) :- place_setting(Place, Activity), prize_quest(Prize, Activity).

% A story is complete if it has two companions along the way
quest_complete(Place, Activity, Prize) :- valid(Place, Activity, Prize),
                                          companions_available(_, Place),
                                          #max_companions(2).
"""

def asp_facts() -> str:
    """Emit the world registries as ASP base facts."""
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place_setting", pid))
        lines.append(asp.fact("indoor", pid, s.indoor))
        for a in sorted(s.affords):
            lines.append(asp.fact("afford_path", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for tag in sorted(a.tags):
            lines.append(asp.fact("quest_activity", aid, tag))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("type_of", pid, p.type))
    for cid, c in COMPANIONS.items():
        lines.append(asp.fact("companion", cid))
        lines.append(asp.fact("region_of", cid, c.region))
    return "\n".join(lines)

def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    """Check that Python and ASP agree on valid combinations."""
    import asp
    clingo_set = set(asp.atoms(asp.one_model(asp_program("#show valid/3.")), "valid"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    sym_diff = [t for t in clingo_set ^ python_set]
    if sym_diff:
        print("  differing:", sorted(sym_diff)[:20])
    return 1

# ---------------------------------------------------------------------------
# Standard storyworld interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale story world centered on quests for 'dear' things "
                    "and the virtue of sharing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1,
                    help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true", help="render curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos via clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    """Fill any unspecified choices with valid random combinations."""
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError(
            f"No valid folk-tale combo matches: place={args.place} "
            f"activity={args.activity} prize={args.prize}"
        )

    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    name = args.name or rng.choice(GIRL_NAMES if args.gender == "girl" else BOY_NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    companions = rng.sample(list(COMPANIONS), 2)
    adjective = rng.choice(ADJECTIVES)
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize_id,
        name=name,
        gender=gender,
        companions=[c.id for c in companions],
        adjective=adjective,
    )

def generate(params: StoryParams) -> StorySample:
    """Construct the folk-tale world and bundle story + Q&A."""
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        hero_name=params.name,
        hero_gender=params.gender,
        companion_types=params.companions,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        atoms = asp.atoms(model, "valid")
        print(f"{len(atoms)} valid folk-tale combos:\n")
        for place, act, prize in sorted(atoms):
            print(f"  {place:12} {act:12} {prize}")
        return

    base_seed = args.seed or random.randrange(2 ** 31)
    rng = random.Random(base_seed)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        while len(samples) < args.n:
            params = resolve_params(args, rng)
            params.seed = base_seed + len(samples)
            sample = generate(params)
            story_str = sample.story
            if story_str in seen:
                continue
            seen.add(story_str)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}{', ' + p.place if p.place != 'village' else ''}: {p.activity} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i+1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples)-1:
            print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
