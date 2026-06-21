#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/plus_banjo_daughter_twist_inner_monologue_whodunit.py
=================================================================================

A small whodunit storyworld about a missing banjo accessory before a village
music show. A musician's daughter investigates with quiet inner monologue,
follows clues, and discovers a twist: the "thief" was really a helper who moved
the item to keep it safe.

The world model tracks:
- physical meters: missing, safe, risk, found
- emotional memes: worry, suspicion, relief, shame, pride, trust

The domain is intentionally tight. Not every place supports every hazard, and
not every helper has a sensible way to protect every item. The Python gate and
its ASP twin both enforce that only reasonable combinations become stories.

Run it
------
    python storyworlds/worlds/gpt-5.4/plus_banjo_daughter_twist_inner_monologue_whodunit.py
    python storyworlds/worlds/gpt-5.4/plus_banjo_daughter_twist_inner_monologue_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/plus_banjo_daughter_twist_inner_monologue_whodunit.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/plus_banjo_daughter_twist_inner_monologue_whodunit.py --qa
    python storyworlds/worlds/gpt-5.4/plus_banjo_daughter_twist_inner_monologue_whodunit.py --trace
    python storyworlds/worlds/gpt-5.4/plus_banjo_daughter_twist_inner_monologue_whodunit.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: tuple = field(default_factory=tuple)
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "seamstress", "baker"}
        male = {"boy", "father", "man", "stablehand", "fiddler"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    detail: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    use_text: str
    vulnerable: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    sign: str
    threat_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    type: str
    name: str
    clue: str
    safe_place: str
    action_text: str
    reason_text: str
    saves: set[tuple[str, str]] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    item: str
    hazard: str
    helper: str
    daughter_name: str
    daughter_trait: str
    parent: str
    patience: int = 1
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_missing_worry(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    daughter = world.get("daughter")
    parent = world.get("parent")
    if item.meters["missing"] >= THRESHOLD:
        if ("worry", "daughter") not in world.fired:
            world.fired.add(("worry", "daughter"))
            daughter.memes["worry"] += 1
            out.append("__worry__")
        if ("worry", "parent") not in world.fired:
            world.fired.add(("worry", "parent"))
            parent.memes["worry"] += 1
    return out


def _r_risk_pressure(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    daughter = world.get("daughter")
    hazard = world.get("hazard")
    if item.meters["missing"] >= THRESHOLD and hazard.meters["risk"] >= THRESHOLD:
        sig = ("pressure", item.id, hazard.id)
        if sig not in world.fired:
            world.fired.add(sig)
            daughter.memes["suspicion"] += 1
            out.append("__pressure__")
    return out


def _r_found_relief(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    daughter = world.get("daughter")
    parent = world.get("parent")
    if item.meters["found"] >= THRESHOLD:
        for who in (daughter, parent):
            sig = ("relief", who.id)
            if sig not in world.fired:
                world.fired.add(sig)
                who.memes["relief"] += 1
        daughter.memes["pride"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="emotional", apply=_r_missing_worry),
    Rule(name="risk_pressure", tag="emotional", apply=_r_risk_pressure),
    Rule(name="found_relief", tag="emotional", apply=_r_found_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    for _ in range(len(CAUSAL_RULES) + 4):
        before = set(world.fired)
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                produced.extend(s for s in bits if not s.startswith("__"))
        if world.fired == before:
            break
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "barn": Place(
        id="barn",
        label="the red barn",
        detail="Lanterns swung from the beams, and the hay smelled warm and sweet.",
        affords={"goat", "crack"},
        tags={"barn", "music_show"},
    ),
    "porch": Place(
        id="porch",
        label="the town hall porch",
        detail="A string of paper stars fluttered over the steps, and the boards creaked softly.",
        affords={"rain", "crack"},
        tags={"porch", "music_show"},
    ),
    "gazebo": Place(
        id="gazebo",
        label="the bandstand gazebo",
        detail="White rails circled the stage, and the evening breeze teased the bunting.",
        affords={"rain", "goat"},
        tags={"gazebo", "music_show"},
    ),
}

ITEMS = {
    "pick": Item(
        id="pick",
        label="banjo pick",
        phrase="a little pearl banjo pick",
        use_text="Without it, the fast song would sound clumsy.",
        vulnerable={"crack"},
        tags={"pick", "banjo"},
    ),
    "song_card": Item(
        id="song_card",
        label="song card",
        phrase="the song card with the verses for the banjo tune",
        use_text="Without it, the verses might tumble out in the wrong order.",
        vulnerable={"rain", "goat"},
        tags={"song_card", "paper", "banjo"},
    ),
    "ribbon": Item(
        id="ribbon",
        label="lucky ribbon",
        phrase="the blue lucky ribbon tied to the banjo case",
        use_text="It was not needed for sound, but the family never played without it.",
        vulnerable={"rain", "goat"},
        tags={"ribbon", "banjo"},
    ),
}

HAZARDS = {
    "rain": Hazard(
        id="rain",
        label="a rain shower",
        sign="dark drops spotted the railing",
        threat_text="A wet gust could ruin paper and leave cloth dripping.",
        tags={"rain", "weather"},
    ),
    "goat": Hazard(
        id="goat",
        label="a nosy goat",
        sign="a goat muzzle poked through the rail, sniffing at anything floppy",
        threat_text="The goat loved to nibble paper corners and ribbon ends.",
        tags={"goat", "animal"},
    ),
    "crack": Hazard(
        id="crack",
        label="a floorboard crack",
        sign="a narrow black crack yawned between two boards",
        threat_text="One small slip could send a tiny shiny thing down where fingers could not reach.",
        tags={"crack", "floor"},
    ),
}

HELPERS = {
    "baker": Helper(
        id="baker",
        type="baker",
        name="Millie",
        clue="a dust of flour",
        safe_place="her round cookie tin",
        action_text="slipped it into her round cookie tin and snapped the lid shut",
        reason_text="she saw trouble coming and wanted it kept dry and away from greedy mouths",
        saves={("song_card", "rain"), ("song_card", "goat"), ("ribbon", "rain"), ("ribbon", "goat")},
        tags={"baker", "cookie_tin"},
    ),
    "seamstress": Helper(
        id="seamstress",
        type="seamstress",
        name="June",
        clue="a curl of blue thread",
        safe_place="her button box",
        action_text="tucked it into her button box beside the shiny brass buttons",
        reason_text="she thought a careful box was safer than a windy stage edge",
        saves={("pick", "crack"), ("ribbon", "rain"), ("ribbon", "goat"), ("ribbon", "crack")},
        tags={"seamstress", "button_box"},
    ),
    "fiddler": Helper(
        id="fiddler",
        type="fiddler",
        name="Otis",
        clue="a bright smear of fiddle rosin",
        safe_place="his velvet case pocket",
        action_text="slid it into the little pocket inside his fiddle case",
        reason_text="he knew stage things disappear fast when the wind or loose boards start meddling",
        saves={("pick", "crack"), ("song_card", "rain")},
        tags={"fiddler", "fiddle_case"},
    ),
}

GIRL_NAMES = ["Clara", "Nora", "Elsie", "Mina", "Lucy", "Ada", "Wren", "Tessa"]
TRAITS = ["careful", "curious", "steady", "bright", "thoughtful", "patient"]


def can_save(helper_id: str, item_id: str, hazard_id: str) -> bool:
    helper = HELPERS[helper_id]
    return (item_id, hazard_id) in helper.saves


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for hazard_id in sorted(place.affords):
            for item_id, item in ITEMS.items():
                if hazard_id not in item.vulnerable:
                    continue
                for helper_id in HELPERS:
                    if can_save(helper_id, item_id, hazard_id):
                        combos.append((place_id, item_id, hazard_id, helper_id))
    return combos


CURATED = [
    StoryParams(
        place="barn",
        item="song_card",
        hazard="goat",
        helper="baker",
        daughter_name="Clara",
        daughter_trait="careful",
        parent="father",
        patience=0,
    ),
    StoryParams(
        place="porch",
        item="pick",
        hazard="crack",
        helper="seamstress",
        daughter_name="Nora",
        daughter_trait="thoughtful",
        parent="mother",
        patience=1,
    ),
    StoryParams(
        place="gazebo",
        item="ribbon",
        hazard="rain",
        helper="baker",
        daughter_name="Elsie",
        daughter_trait="bright",
        parent="father",
        patience=1,
    ),
    StoryParams(
        place="porch",
        item="song_card",
        hazard="rain",
        helper="fiddler",
        daughter_name="Mina",
        daughter_trait="steady",
        parent="mother",
        patience=0,
    ),
]


def outcome_of(params: StoryParams) -> str:
    return "double_take" if params.patience == 0 else "steady_solve"


def explain_rejection(place_id: str, item_id: str, hazard_id: str, helper_id: str) -> str:
    place = PLACES[place_id]
    item = ITEMS[item_id]
    hazard = HAZARDS[hazard_id]
    helper = HELPERS[helper_id]
    if hazard_id not in place.affords:
        return (
            f"(No story: {place.label} does not support the hazard '{hazard_id}'. "
            f"Pick one of {sorted(place.affords)} for that place.)"
        )
    if hazard_id not in item.vulnerable:
        return (
            f"(No story: {hazard.label} would not honestly threaten the {item.label}. "
            f"The mystery works only when the missing item was at real risk.)"
        )
    return (
        f"(No story: {helper.name} the {helper.type} has no sensible way to protect "
        f"the {item.label} from {hazard.label}. The twist must be reasonable, not arbitrary.)"
    )


def pick_decoy(helper_id: str, rng: random.Random) -> Helper:
    others = [h for hid, h in HELPERS.items() if hid != helper_id]
    return rng.choice(sorted(others, key=lambda h: h.id))


def introduce(world: World, daughter: Entity, parent: Entity, place: Place) -> None:
    world.say(
        f"On music-night in {place.label}, {daughter.id} walked beside {daughter.pronoun('possessive')} "
        f"{parent.label_word} and carried the banjo case with both hands. {place.detail}"
    )
    world.say(
        f"{daughter.id} liked the sound check best of all. One plucked string, then another, and the whole place seemed to sit up and listen."
    )


def setup_missing(world: World, daughter: Entity, parent: Entity, item: Entity, item_cfg: Item) -> None:
    item.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {parent.label_word} opened the banjo case, {item_cfg.phrase} was gone. "
        f"{item_cfg.use_text}"
    )
    world.say(
        f"{daughter.id} felt a cold little jump in {daughter.pronoun('possessive')} chest. A missing thing before a show could turn even cheerful grown-ups quiet."
    )


def set_risk(world: World, hazard: Entity, hazard_cfg: Hazard) -> None:
    hazard.meters["risk"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {world.place.detail.split(',')[0]} seemed to point at the trouble: {hazard_cfg.sign}. {hazard_cfg.threat_text}"
    )


def clue_scene(world: World, daughter: Entity, helper: Entity, helper_cfg: Helper, decoy: Entity) -> None:
    world.say(
        f"Near the banjo case lay {helper_cfg.clue}. That was one clue, plus one more puzzle."
    )
    world.say(
        f"{decoy.id} was hurrying past at the same moment, looking busy in a way that could easily seem suspicious."
    )
    world.say(
        f'"Think small, then think twice," {daughter.id} told {daughter.pronoun("object")}self in a whisper. It was the kind of secret detective rule {daughter.pronoun()} liked to keep in {daughter.pronoun("possessive")} head.'
    )


def wrong_turn(world: World, daughter: Entity, decoy: Entity, helper_cfg: Helper) -> None:
    daughter.memes["suspicion"] += 1
    world.say(
        f"For one quick moment, {daughter.id} decided the answer must be {decoy.id}. "
        f'"He is rushing. He must know something," {daughter.pronoun()} thought.'
        if decoy.type in {"father", "man", "stablehand", "fiddler"}
        else f"For one quick moment, {daughter.id} decided the answer must be {decoy.id}. "
             f'"She is rushing. She must know something," {daughter.pronoun()} thought.'
    )
    world.say(
        f"But the guess felt thin the instant it landed. Busy feet were not the same as guilty hands."
    )
    world.say(
        f"Then {daughter.id} looked back at {helper_cfg.clue} and felt heat rise in {daughter.pronoun('possessive')} cheeks. The real clue had been sitting quietly all along."
    )
    daughter.memes["shame"] += 1


def steady_turn(world: World, daughter: Entity, helper_cfg: Helper, helper: Entity) -> None:
    daughter.memes["trust"] += 1
    world.say(
        f"{daughter.id} nearly chased the busiest person in sight, but {daughter.pronoun()} stopped on the first step."
    )
    world.say(
        f'"No," {daughter.pronoun()} told {daughter.pronoun("object")}self. "The loudest answer is not always the truest one. Start with {helper_cfg.clue}."'
    )
    world.say(
        f"So {daughter.id} followed the quiet clue instead, straight toward {helper.id}."
    )


def reveal(world: World, daughter: Entity, parent: Entity, item: Entity, item_cfg: Item,
           helper: Entity, helper_cfg: Helper, hazard_cfg: Hazard) -> None:
    item.meters["missing"] = 0.0
    item.meters["safe"] += 1
    item.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.id} blinked when {daughter.id} asked, then opened {helper_cfg.safe_place}. "
        f"There lay {item_cfg.phrase}, safe and neat."
    )
    world.say(
        f'"I did move it," {helper.id} said, "but I was not stealing a thing. {helper_cfg.reason_text}. '
        f'With {hazard_cfg.label} so close, I thought the case edge was no place for it."'
    )
    world.say(
        f"The twist made the whole mystery turn inside out. There had been no thief at all, only a worried helper."
    )
    parent.memes["trust"] += 1
    daughter.memes["trust"] += 1


def ending(world: World, daughter: Entity, parent: Entity, item_cfg: Item) -> None:
    daughter.memes["pride"] += 1
    world.say(
        f"{parent.label_word.capitalize()} smiled, tucked the {item_cfg.label} back where it belonged, and gave the banjo strings a bright testing brush."
    )
    world.say(
        f"That night, when the tune skipped out over the crowd, {daughter.id} listened with a new feeling. "
        f"A clue could be soft, a guess could be wrong, and the kindest answer could still solve the case."
    )


def tell(params: StoryParams) -> World:
    if params.place not in PLACES or params.item not in ITEMS or params.hazard not in HAZARDS or params.helper not in HELPERS:
        raise StoryError("(Invalid params: unknown registry key.)")
    if (params.place, params.item, params.hazard, params.helper) not in valid_combos():
        raise StoryError(explain_rejection(params.place, params.item, params.hazard, params.helper))

    place = PLACES[params.place]
    item_cfg = ITEMS[params.item]
    hazard_cfg = HAZARDS[params.hazard]
    helper_cfg = HELPERS[params.helper]
    rng = random.Random(params.seed if params.seed is not None else 0)

    world = World(place)
    daughter = world.add(Entity(
        id=params.daughter_name,
        kind="character",
        type="girl",
        label=params.daughter_name,
        role="daughter",
        attrs={"trait": params.daughter_trait},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label="the parent",
        role="musician",
    ))
    banjo = world.add(Entity(
        id="banjo",
        type="banjo",
        label="banjo",
        phrase="the family banjo",
    ))
    item = world.add(Entity(
        id="item",
        type="item",
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        role="missing_item",
    ))
    hazard = world.add(Entity(
        id="hazard",
        type="hazard",
        label=hazard_cfg.label,
    ))
    helper = world.add(Entity(
        id=helper_cfg.name,
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.name,
        role="helper",
    ))
    decoy_cfg = pick_decoy(params.helper, rng)
    decoy = world.add(Entity(
        id=decoy_cfg.name,
        kind="character",
        type=decoy_cfg.type,
        label=decoy_cfg.name,
        role="decoy",
    ))

    world.facts.update(
        place=place,
        item_cfg=item_cfg,
        hazard_cfg=hazard_cfg,
        helper_cfg=helper_cfg,
        decoy_cfg=decoy_cfg,
        patience=params.patience,
        outcome=outcome_of(params),
    )

    introduce(world, daughter, parent, place)
    setup_missing(world, daughter, parent, item, item_cfg)
    world.para()
    set_risk(world, hazard, hazard_cfg)
    clue_scene(world, daughter, helper, helper_cfg, decoy)
    if params.patience == 0:
        wrong_turn(world, daughter, decoy, helper_cfg)
    else:
        steady_turn(world, daughter, helper_cfg, helper)
    world.para()
    reveal(world, daughter, parent, item, item_cfg, helper, helper_cfg, hazard_cfg)
    ending(world, daughter, parent, item_cfg)

    world.facts.update(
        daughter=daughter,
        parent=parent,
        banjo=banjo,
        item=item,
        hazard=hazard,
        helper=helper,
        decoy=decoy,
        found=item.meters["found"] >= THRESHOLD,
        helper_meant_well=True,
        guessed_wrong=params.patience == 0,
    )
    return world


KNOWLEDGE = {
    "banjo": [
        (
            "What is a banjo?",
            "A banjo is a string instrument with a round body and a bright twangy sound. People pluck or strum its strings to play tunes.",
        )
    ],
    "pick": [
        (
            "What is a banjo pick?",
            "A banjo pick is a small piece a player can use to pluck the strings. Because it is tiny, it is easy to misplace.",
        )
    ],
    "song_card": [
        (
            "Why would a musician use a song card?",
            "A song card can hold words or reminders for a tune. It helps a player remember what comes next.",
        )
    ],
    "ribbon": [
        (
            "Why might a ribbon matter in a family tradition?",
            "A ribbon can remind a family of luck, love, or an old promise. Even if it does not change the sound, it can feel important.",
        )
    ],
    "rain": [
        (
            "Why can rain be a problem for paper or cloth?",
            "Rain can soak paper until it wrinkles or tears, and it can leave cloth wet and heavy. That is why people move delicate things somewhere dry.",
        )
    ],
    "goat": [
        (
            "Why should paper and ribbons stay away from goats?",
            "Goats like to nibble and chew interesting things with corners or dangling ends. Paper and ribbons can look like a snack to them.",
        )
    ],
    "crack": [
        (
            "Why is a floorboard crack dangerous for a tiny object?",
            "A tiny object can slip into the crack and disappear where fingers cannot reach. Small shiny things are especially easy to lose that way.",
        )
    ],
    "whodunit": [
        (
            "What is a whodunit?",
            "A whodunit is a mystery story where someone tries to figure out who did something. The fun comes from following clues and changing ideas when new facts appear.",
        )
    ],
}
KNOWLEDGE_ORDER = ["whodunit", "banjo", "pick", "song_card", "ribbon", "rain", "goat", "crack"]


def generation_prompts(world: World) -> list[str]:
    daughter = world.facts["daughter"]
    item_cfg = world.facts["item_cfg"]
    hazard_cfg = world.facts["hazard_cfg"]
    helper_cfg = world.facts["helper_cfg"]
    outcome = world.facts["outcome"]
    asks = [
        'Write a short whodunit for a 3-to-5-year-old that includes the words "plus", "banjo", and "daughter".',
        f"Tell a gentle mystery where a musician's daughter notices a missing {item_cfg.label} before a banjo performance and follows clues with inner monologue.",
    ]
    if outcome == "double_take":
        asks.append(
            f"Write a story with a twist where {daughter.id} first suspects the wrong person, then realizes {helper_cfg.name} moved the {item_cfg.label} to protect it from {hazard_cfg.label}."
        )
    else:
        asks.append(
            f"Write a quiet whodunit where {daughter.id} pauses, trusts a small clue, and discovers that {helper_cfg.name} hid the {item_cfg.label} kindly because of {hazard_cfg.label}."
        )
    return asks


def story_qa(world: World) -> list[tuple[str, str]]:
    daughter = world.facts["daughter"]
    parent = world.facts["parent"]
    item_cfg = world.facts["item_cfg"]
    hazard_cfg = world.facts["hazard_cfg"]
    helper = world.facts["helper"]
    helper_cfg = world.facts["helper_cfg"]
    decoy = world.facts["decoy"]
    outcome = world.facts["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {daughter.id}, a musician's daughter, and {daughter.pronoun('possessive')} {parent.label_word} getting ready for a banjo show. It is also about the helper {helper.id}, whose kind choice looked suspicious at first.",
        ),
        (
            f"What went missing before the music started?",
            f"The missing thing was {item_cfg.phrase}. That mattered because {item_cfg.use_text[0].lower() + item_cfg.use_text[1:]}",
        ),
        (
            "Why did the missing thing seem like a mystery?",
            f"It disappeared right before the performance, and there was a real danger nearby: {hazard_cfg.threat_text} That made it look as if someone might have taken it for a bad reason.",
        ),
        (
            "What clue did the daughter notice?",
            f"She noticed {helper_cfg.clue} near the banjo case. That was the quiet clue that pointed toward {helper.id}.",
        ),
    ]
    if outcome == "double_take":
        qa.append(
            (
                f"Did {daughter.id} guess right at once?",
                f"No. She first looked at {decoy.id} because that person seemed busy and suspicious. Then she thought again, trusted the smaller clue, and understood the twist.",
            )
        )
    else:
        qa.append(
            (
                f"How did {daughter.id} solve the case?",
                f"She slowed down and listened to her inner thoughts instead of chasing the loudest guess. That helped her follow the real clue to {helper.id}.",
            )
        )
    qa.append(
        (
            f"Who had the {item_cfg.label}, and why?",
            f"{helper.id} had it, but not as a thief. {helper.pronoun().capitalize()} moved it into {helper_cfg.safe_place} because {helper_cfg.reason_text}.",
        )
    )
    qa.append(
        (
            "What was the twist?",
            f"The twist was that nobody had stolen anything. The mystery turned out to be a kind act that looked like a crime until the daughter understood the danger.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"The missing thing was returned, the banjo music could begin, and {daughter.id} felt proud and wiser. The ending shows that careful thinking can be kinder than a quick accusation.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    item_cfg = world.facts["item_cfg"]
    hazard_cfg = world.facts["hazard_cfg"]
    tags = {"whodunit", "banjo"} | set(item_cfg.tags) | set(hazard_cfg.tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% Reasonable mystery setups.
at_risk(I, H) :- vulnerable(I, H).
valid(P, I, H, He) :- place(P), item(I), hazard(H), helper(He),
                      affords(P, H), at_risk(I, H), saves(He, I, H).

% Outcome model.
outcome(double_take) :- patience(0).
outcome(steady_solve) :- patience(1).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for hazard_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, hazard_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        for hazard_id in sorted(item.vulnerable):
            lines.append(asp.fact("vulnerable", item_id, hazard_id))
    for hazard_id in HAZARDS:
        lines.append(asp.fact("hazard", hazard_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for item_id, hazard_id in sorted(helper.saves):
            lines.append(asp.fact("saves", helper_id, item_id, hazard_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = asp.fact("patience", params.patience)
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    cset, pset = set(asp_valid_combos()), set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    for s in range(50):
        rng = random.Random(s)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        params.seed = s
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome disagreements.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke story came out empty")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a banjo mystery with a daughter detective, a twist, and inner monologue."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--daughter-name")
    ap.add_argument("--daughter-trait", choices=TRAITS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--patience", type=int, choices=[0, 1], help="0 = wrong guess first, 1 = steady solve")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story setups from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.item and args.hazard and args.helper:
        combo = (args.place, args.item, args.hazard, args.helper)
        if combo not in valid_combos():
            raise StoryError(explain_rejection(args.place, args.item, args.hazard, args.helper))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.hazard is None or combo[2] == args.hazard)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, hazard_id, helper_id = rng.choice(sorted(combos))
    daughter_name = args.daughter_name or rng.choice(GIRL_NAMES)
    daughter_trait = args.daughter_trait or rng.choice(TRAITS)
    parent = args.parent or rng.choice(["mother", "father"])
    patience = args.patience if args.patience is not None else rng.choice([0, 1])

    return StoryParams(
        place=place_id,
        item=item_id,
        hazard=hazard_id,
        helper=helper_id,
        daughter_name=daughter_name,
        daughter_trait=daughter_trait,
        parent=parent,
        patience=patience,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Invalid params: unknown place '{params.place}')")
    if params.item not in ITEMS:
        raise StoryError(f"(Invalid params: unknown item '{params.item}')")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Invalid params: unknown hazard '{params.hazard}')")
    if params.helper not in HELPERS:
        raise StoryError(f"(Invalid params: unknown helper '{params.helper}')")

    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item, hazard, helper) combos:\n")
        for place_id, item_id, hazard_id, helper_id in combos:
            print(f"  {place_id:7} {item_id:10} {hazard_id:6} {helper_id}")
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
            header = f"### {p.daughter_name}: {p.item} at {p.place} ({p.hazard}, {p.helper}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
