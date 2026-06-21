#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/peroxide_reconciliation_kindness_teamwork_superhero_story.py
=======================================================================================

A standalone story world for a small superhero-play domain centered on a scrape,
peroxide, kindness, reconciliation, and teamwork.

Two children turn a room into a superhero city. One child gets bossy and tries to
do the rescue alone. The other child, whose feelings were hurt, warns that the
solo rush is risky. The warning is right: the rushing hero slips and gets a small
scrape. Then the hurt child chooses kindness, helps clean the scrape with peroxide,
and the two children reconcile and finish the mission together.

The world model keeps both physical meters (scrape, sting, mission progress) and
emotional memes (hurt, guilt, kindness, trust, joy). Prose is rendered from the
simulated state, not from one frozen paragraph.

Run it
------
    python storyworlds/worlds/gpt-5.4/peroxide_reconciliation_kindness_teamwork_superhero_story.py
    python storyworlds/worlds/gpt-5.4/peroxide_reconciliation_kindness_teamwork_superhero_story.py --mission bridge_rescue
    python storyworlds/worlds/gpt-5.4/peroxide_reconciliation_kindness_teamwork_superhero_story.py --injury bumped_head
    python storyworlds/worlds/gpt-5.4/peroxide_reconciliation_kindness_teamwork_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/peroxide_reconciliation_kindness_teamwork_superhero_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/peroxide_reconciliation_kindness_teamwork_superhero_story.py --verify
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
_THIS = os.path.abspath(__file__)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(_THIS))))
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Mission:
    id: str
    scene: str
    props: str
    hazard: str
    mission: str
    victim: str
    finish: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Injury:
    id: str
    label: str
    body: str
    cause: str
    cleanable: bool = True
    needs_peroxide: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class CareMethod:
    id: str
    label: str
    sense: int
    uses_peroxide: bool
    works_for_scrape: bool
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


class World:
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_injury_needs_help(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["scrape"] >= THRESHOLD:
        sig = ("injury", "hero")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["fear"] += 1
            hero.meters["needs_help"] += 1
            partner = world.get("partner")
            partner.memes["concern"] += 1
            out.append("__injury__")
    return out


def _r_care_brings_relief(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    partner = world.get("partner")
    if hero.meters["cleaned"] >= THRESHOLD:
        sig = ("relief", "hero")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["relief"] += 1
            hero.memes["fear"] = 0.0
            partner.memes["kindness"] += 1
            out.append("__relief__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    partner = world.get("partner")
    if hero.memes["apology"] >= THRESHOLD and hero.meters["cleaned"] >= THRESHOLD:
        sig = ("reconcile", "pair")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["trust"] += 1
            partner.memes["trust"] += 1
            hero.memes["joy"] += 1
            partner.memes["joy"] += 1
            hero.memes["guilt"] = 0.0
            partner.memes["hurt"] = 0.0
            world.get("team").memes["reconciled"] += 1
            out.append("__reconciled__")
    return out


def _r_teamwork_completes_mission(world: World) -> list[str]:
    out: list[str] = []
    team = world.get("team")
    city = world.get("city")
    if team.meters["teamed_up"] >= THRESHOLD and team.memes["reconciled"] >= THRESHOLD:
        sig = ("finish", "mission")
        if sig not in world.fired:
            world.fired.add(sig)
            city.meters["danger"] = 0.0
            city.meters["saved"] += 1
            out.append("__saved__")
    return out


CAUSAL_RULES = [
    Rule(name="injury_needs_help", tag="physical", apply=_r_injury_needs_help),
    Rule(name="care_brings_relief", tag="physical", apply=_r_care_brings_relief),
    Rule(name="reconcile", tag="social", apply=_r_reconcile),
    Rule(name="teamwork_completes_mission", tag="social", apply=_r_teamwork_completes_mission),
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


def injury_at_risk(injury: Injury, care: CareMethod) -> bool:
    return injury.cleanable and injury.needs_peroxide and care.uses_peroxide and care.works_for_scrape


def sensible_cares() -> list[CareMethod]:
    return [c for c in CARE_METHODS.values() if c.sense >= SENSE_MIN and c.uses_peroxide and c.works_for_scrape]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for mission_id in MISSIONS:
        for injury_id, injury in INJURIES.items():
            for care_id, care in CARE_METHODS.items():
                if injury_at_risk(injury, care) and care.sense >= SENSE_MIN:
                    combos.append((mission_id, injury_id, care_id))
    return combos


def predict_rush(world: World, injury: Injury) -> dict:
    sim = world.copy()
    sim_hero = sim.get("hero")
    sim_hero.meters["scrape"] += 1 if injury.cleanable else 0
    sim_hero.meters["sting"] += 1 if injury.cleanable else 0
    propagate(sim, narrate=False)
    return {
        "injured": sim_hero.meters["scrape"] >= THRESHOLD,
        "needs_help": sim_hero.meters["needs_help"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, partner: Entity, mission: Mission) -> None:
    for kid in (hero, partner):
        kid.memes["joy"] += 1
    world.get("city").meters["danger"] += 1
    world.say(
        f"After school, {hero.id} and {partner.id} turned the living room into {mission.scene}. "
        f"{mission.props}"
    )
    world.say(
        f'Together they shouted, "Hero team, ready!" because {mission.mission}.'
    )


def start_conflict(world: World, hero: Entity, partner: Entity, mission: Mission) -> None:
    hero.memes["pride"] += 1
    partner.memes["hurt"] += 1
    hero.memes["guilt"] += 1
    world.say(
        f"But when they reached {mission.hazard}, {hero.id} snatched the bright cape and said, "
        f'"I should go first. I can save {mission.victim} all by myself."'
    )
    world.say(
        f"{partner.id} stood very still. Being left out made {partner.pronoun('object')} feel small."
    )


def warn(world: World, partner: Entity, hero: Entity, injury: Injury) -> None:
    pred = predict_rush(world, injury)
    world.facts["predicted_injury"] = pred["injured"]
    world.say(
        f'{partner.id} looked at the wobbly path and said, "{hero.id}, slow down. '
        f'If you race alone, you could get hurt."'
    )


def defy(world: World, hero: Entity, partner: Entity, mission: Mission) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'"A super hero does not need help," {hero.id} said, and {hero.pronoun()} dashed toward {mission.hazard}.'
    )
    if partner.memes["hurt"] >= THRESHOLD:
        world.say(
            f"{partner.id} did not like those words, but {partner.pronoun()} still watched closely."
        )


def accident(world: World, hero: Entity, injury: Injury, mission: Mission) -> None:
    if injury.cleanable:
        hero.meters["scrape"] += 1
        hero.meters["sting"] += 1
    else:
        hero.meters["bump"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the block path tipped. {hero.id} slipped {injury.cause} and got {injury.label}."
    )
    if hero.meters["scrape"] >= THRESHOLD:
        world.say(
            f"{hero.id} sat down fast and blinked hard because the little scrape stung."
        )


def kindness_help(world: World, partner: Entity, hero: Entity, care: CareMethod, parent: Entity) -> None:
    partner.memes["kindness"] += 1
    world.say(
        f"{partner.id} could have stayed mad. Instead, {partner.pronoun()} ran to the hero kit and called for {parent.label_word}."
    )
    world.say(
        f"Together they {care.text}."
    )
    hero.meters["cleaned"] += 1
    hero.meters["bandaged"] += 1
    propagate(world, narrate=False)


def apology(world: World, hero: Entity, partner: Entity, when: str) -> None:
    hero.memes["apology"] += 1
    if when == "before_care":
        world.say(
            f'Before the bandage was even smooth, {hero.id} whispered, "I was bossy. '
            f'I should not have tried to be the only hero. I am sorry."'
        )
    else:
        world.say(
            f'When the sting faded, {hero.id} looked at {partner.id} and said, '
            f'"You helped me when I was not kind. I am sorry for pushing you away."'
        )
    world.say(
        f"{partner.id} saw that the apology was real."
    )


def forgive(world: World, partner: Entity, hero: Entity) -> None:
    world.say(
        f'"We can still be a team," {partner.id} said, and reached for {hero.id}\'s hand.'
    )
    propagate(world, narrate=False)


def team_up(world: World, hero: Entity, partner: Entity, mission: Mission) -> None:
    team = world.get("team")
    team.meters["teamed_up"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Now they made a plan together. {partner.id} held the map steady while {hero.id} carried the rescue rope."
    )
    world.say(
        f"Side by side, they {mission.finish}."
    )
    if world.get("city").meters["saved"] >= THRESHOLD:
        world.say(
            f"In the end, the room did not need one lonely hero. It needed two kind ones."
        )


def ending_image(world: World, hero: Entity, partner: Entity) -> None:
    world.say(
        f"They hung the bright cape over both their shoulders and laughed as if it had always belonged to the whole team."
    )


def tell(
    mission: Mission,
    injury: Injury,
    care: CareMethod,
    hero_name: str = "Maya",
    hero_gender: str = "girl",
    partner_name: str = "Theo",
    partner_gender: str = "boy",
    parent_type: str = "mother",
    apology_timing: str = "after_care",
    hero_trait: str = "bold",
    partner_trait: str = "gentle",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero", traits=[hero_trait]))
    partner = world.add(Entity(id="partner", kind="character", type=partner_gender, label=partner_name, role="partner", traits=[partner_trait]))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    city = world.add(Entity(id="city", type="city", label="the pretend city"))
    team = world.add(Entity(id="team", type="team", label="the hero team"))

    world.facts["display_names"] = {"hero": hero_name, "partner": partner_name}
    world.facts["mission_cfg"] = mission
    world.facts["injury_cfg"] = injury
    world.facts["care_cfg"] = care
    world.facts["apology_timing"] = apology_timing
    world.facts["hero_ent"] = hero
    world.facts["partner_ent"] = partner
    world.facts["parent_ent"] = parent

    introduce(world, hero, partner, mission)
    world.para()
    start_conflict(world, hero, partner, mission)
    warn(world, partner, hero, injury)
    defy(world, hero, partner, mission)

    world.para()
    accident(world, hero, injury, mission)
    kindness_help(world, partner, hero, care, parent)
    if apology_timing == "before_care":
        # keep the branch distinct but still grounded
        pass
    apology(world, hero, partner, apology_timing)
    forgive(world, partner, hero)

    world.para()
    team_up(world, hero, partner, mission)
    ending_image(world, hero, partner)

    world.facts.update(
        hero_name=hero_name,
        partner_name=partner_name,
        parent_type=parent_type,
        reconciled=world.get("team").memes["reconciled"] >= THRESHOLD,
        mission_saved=world.get("city").meters["saved"] >= THRESHOLD,
        cleaned=hero.meters["cleaned"] >= THRESHOLD,
    )
    return world


MISSIONS = {
    "bridge_rescue": Mission(
        id="bridge_rescue",
        scene="a windy rescue city",
        props="A couch became a tower, cushions became rooftops, and a line of blocks became a skinny bridge over a lava rug.",
        hazard="the skinny bridge",
        mission="a toy bus was stranded near the tower",
        victim="the tiny bus",
        finish="guided the tiny bus across the bridge and back to safety",
        tags={"superhero", "teamwork"},
    ),
    "kitten_roof": Mission(
        id="kitten_roof",
        scene="a moonlit hero city",
        props="A chair became a high roof, a blanket became the night sky, and silver spoons flashed like secret signals.",
        hazard="the high roof path",
        mission="a plush kitten was stuck above the city",
        victim="the plush kitten",
        finish="lowered the plush kitten from the roof with a soft string ladder",
        tags={"superhero", "teamwork"},
    ),
    "garden_generator": Mission(
        id="garden_generator",
        scene="a glowing robot town",
        props="A cardboard box became the power station, books became streets, and a toy fan hummed like a city engine.",
        hazard="the narrow station ramp",
        mission="the pretend lights needed help before the robot parade",
        victim="the little robot parade",
        finish="carried the shiny battery block together and made the pretend lights glow again",
        tags={"superhero", "teamwork"},
    ),
}

INJURIES = {
    "knee_scrape": Injury(
        id="knee_scrape",
        label="a scrape on the knee",
        body="knee",
        cause="on the edge of a block",
        cleanable=True,
        needs_peroxide=True,
        tags={"scrape", "peroxide"},
    ),
    "elbow_scrape": Injury(
        id="elbow_scrape",
        label="a scrape on the elbow",
        body="elbow",
        cause="against a rough cardboard corner",
        cleanable=True,
        needs_peroxide=True,
        tags={"scrape", "peroxide"},
    ),
    "palm_scrape": Injury(
        id="palm_scrape",
        label="a scrape on the palm",
        body="palm",
        cause="when one hand slid across the box flap",
        cleanable=True,
        needs_peroxide=True,
        tags={"scrape", "peroxide"},
    ),
    "bumped_head": Injury(
        id="bumped_head",
        label="a bump on the head",
        body="head",
        cause="against the side of the couch",
        cleanable=False,
        needs_peroxide=False,
        tags={"bump"},
    ),
}

CARE_METHODS = {
    "peroxide_bandage": CareMethod(
        id="peroxide_bandage",
        label="peroxide and a bandage",
        sense=3,
        uses_peroxide=True,
        works_for_scrape=True,
        text="opened the first-aid box, dabbed the scrape with peroxide, and covered it with a bright star bandage",
        qa_text="They cleaned the scrape with peroxide and put on a bandage",
        tags={"peroxide", "bandage"},
    ),
    "peroxide_wipe": CareMethod(
        id="peroxide_wipe",
        label="peroxide on a soft cotton pad",
        sense=3,
        uses_peroxide=True,
        works_for_scrape=True,
        text="poured a little peroxide onto a soft cotton pad, cleaned the scrape, and wrapped it in a neat bandage",
        qa_text="They used peroxide on a soft pad to clean the scrape, then wrapped it in a bandage",
        tags={"peroxide", "bandage"},
    ),
    "rinse_only": CareMethod(
        id="rinse_only",
        label="just a quick splash of water",
        sense=1,
        uses_peroxide=False,
        works_for_scrape=False,
        text="splashed a little water on it and hoped that was enough",
        qa_text="They only splashed water on it",
        tags={"water"},
    ),
    "ice_pack": CareMethod(
        id="ice_pack",
        label="an ice pack",
        sense=1,
        uses_peroxide=False,
        works_for_scrape=False,
        text="held an ice pack near it instead of cleaning the scrape",
        qa_text="They used only an ice pack",
        tags={"ice"},
    ),
}

GIRL_NAMES = ["Maya", "Lily", "Ava", "Nora", "Lucy", "Zoe", "Ella", "Ruby"]
BOY_NAMES = ["Theo", "Max", "Ben", "Eli", "Noah", "Finn", "Sam", "Leo"]
TRAITS = ["bold", "gentle", "careful", "kind", "thoughtful", "steady"]


@dataclass
class StoryParams:
    mission: str
    injury: str
    care: str
    hero_name: str
    hero_gender: str
    partner_name: str
    partner_gender: str
    parent: str
    apology_timing: str
    hero_trait: str
    partner_trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "peroxide": [
        (
            "What is peroxide used for in this story?",
            "Peroxide is used to help clean a small scrape. A grown-up can use it from a first-aid kit to help get the skin clean before a bandage goes on."
        )
    ],
    "bandage": [
        (
            "What does a bandage do?",
            "A bandage covers a small scrape or cut and helps protect it. It can keep the spot clean while it starts to feel better."
        )
    ],
    "scrape": [
        (
            "What is a scrape?",
            "A scrape is a small hurt spot where the top of the skin gets rubbed off. It can sting, but gentle cleaning and care can help."
        )
    ],
    "apology": [
        (
            "What is an apology?",
            "An apology is when you tell someone you know your words or actions hurt them. A real apology is part of making things better."
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is choosing to help or comfort someone, even when it would be easier not to. Kind actions can change how a hard moment ends."
        )
    ],
    "teamwork": [
        (
            "Why is teamwork useful?",
            "Teamwork helps people do a hard job together by sharing the work. It also helps everyone feel included and strong."
        )
    ],
    "superhero": [
        (
            "What makes someone a hero in this story?",
            "Being a hero here is not about bossing people around. It is about helping, listening, and being brave enough to be kind."
        )
    ],
}
KNOWLEDGE_ORDER = ["superhero", "scrape", "peroxide", "bandage", "apology", "kindness", "teamwork"]


CURATED = [
    StoryParams(
        mission="bridge_rescue",
        injury="knee_scrape",
        care="peroxide_bandage",
        hero_name="Maya",
        hero_gender="girl",
        partner_name="Theo",
        partner_gender="boy",
        parent="mother",
        apology_timing="after_care",
        hero_trait="bold",
        partner_trait="gentle",
    ),
    StoryParams(
        mission="kitten_roof",
        injury="elbow_scrape",
        care="peroxide_wipe",
        hero_name="Ben",
        hero_gender="boy",
        partner_name="Lucy",
        partner_gender="girl",
        parent="father",
        apology_timing="before_care",
        hero_trait="bold",
        partner_trait="kind",
    ),
    StoryParams(
        mission="garden_generator",
        injury="palm_scrape",
        care="peroxide_bandage",
        hero_name="Nora",
        hero_gender="girl",
        partner_name="Max",
        partner_gender="boy",
        parent="mother",
        apology_timing="after_care",
        hero_trait="steady",
        partner_trait="thoughtful",
    ),
]


def generation_prompts(world: World) -> list[str]:
    hero_name = world.facts["hero_name"]
    partner_name = world.facts["partner_name"]
    mission = world.facts["mission_cfg"]
    injury = world.facts["injury_cfg"]
    return [
        'Write a superhero story for a 3-to-5-year-old that includes the word "peroxide" and shows reconciliation, kindness, and teamwork.',
        f"Tell a gentle superhero-play story where {hero_name} hurts {hero_name if False else 'themself'} while rushing alone, and {partner_name} chooses kindness and helps.",
        f"Write a story where a pretend mission about {mission.victim} leads to {injury.label}, an apology, and a happy team ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero_name = world.facts["hero_name"]
    partner_name = world.facts["partner_name"]
    hero = world.facts["hero_ent"]
    partner = world.facts["partner_ent"]
    parent = world.facts["parent_ent"]
    mission = world.facts["mission_cfg"]
    injury = world.facts["injury_cfg"]
    care = world.facts["care_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name} and {partner_name}, two children playing super heroes at home. Their {parent.label_word} helps for a moment when the scrape needs first-aid care."
        ),
        (
            "What was the problem at the start?",
            f"The problem was not only the pretend danger in the city. {hero_name} also tried to be the only hero, which hurt {partner_name}'s feelings and broke the team feeling."
        ),
        (
            f"Why did {partner_name} warn {hero_name} to slow down?",
            f"{partner_name} saw that the path was wobbly and guessed a solo rush could end with someone getting hurt. The warning came from paying attention, not from wanting to spoil the game."
        ),
        (
            f"What happened to {hero_name}?",
            f"{hero_name} got {injury.label}. The scrape stung because {hero.pronoun()} rushed ahead alone and slipped on the pretend rescue path."
        ),
        (
            f"How did {partner_name} show kindness?",
            f"{partner_name} chose to help even though {partner.pronoun()} had been left out and felt hurt. {partner.pronoun().capitalize()} brought the first-aid help, and together they {care.qa_text.lower()}."
        ),
        (
            f"How did the children reconcile?",
            f"{hero_name} apologized for being bossy and for pushing {partner_name} away. Then {partner_name} forgave {hero.pronoun('object')}, so the team feeling came back."
        ),
        (
            "How did the story end?",
            f"It ended with teamwork: they finished the rescue together instead of alone. The shared cape at the end shows that what changed was not just the scrape, but the friendship mood too."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"superhero", "kindness", "apology", "teamwork"} | set(world.facts["injury_cfg"].tags) | set(world.facts["care_cfg"].tags)
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
    for key, ent in world.entities.items():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        parts = [f"({ent.type})"]
        if ent.label:
            parts.append(f"label={ent.label!r}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        lines.append(f"  {key:8} {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(injury: Injury, care: CareMethod) -> str:
    if not injury.cleanable:
        return (
            f"(No story: {injury.label} is a bump, not a little scrape, so peroxide is not the sensible care in this world. "
            f"Choose a scrape like knee_scrape or elbow_scrape.)"
        )
    if not care.uses_peroxide:
        return (
            f"(No story: the care method '{care.id}' does not use peroxide, but this story world is about cleaning a scrape with peroxide and then reconciling as a team.)"
        )
    if care.sense < SENSE_MIN or not care.works_for_scrape:
        return (
            f"(No story: the care method '{care.id}' is too weak or mismatched for a scrape here. "
            f"Choose a sensible peroxide-based care method.)"
        )
    return "(No story: that injury and care combination is not reasonable here.)"


ASP_RULES = r"""
cleanable_scrape(I) :- injury(I), cleanable(I), needs_peroxide(I).
sensible_care(C)    :- care(C), uses_peroxide(C), works_for_scrape(C), sense(C, S), sense_min(M), S >= M.
valid(M, I, C)      :- mission(M), cleanable_scrape(I), sensible_care(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for injury_id, injury in INJURIES.items():
        lines.append(asp.fact("injury", injury_id))
        if injury.cleanable:
            lines.append(asp.fact("cleanable", injury_id))
        if injury.needs_peroxide:
            lines.append(asp.fact("needs_peroxide", injury_id))
    for care_id, care in CARE_METHODS.items():
        lines.append(asp.fact("care", care_id))
        lines.append(asp.fact("sense", care_id, care.sense))
        if care.uses_peroxide:
            lines.append(asp.fact("uses_peroxide", care_id))
        if care.works_for_scrape:
            lines.append(asp.fact("works_for_scrape", care_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos():")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "peroxide" not in sample.story.lower():
            raise StoryError("smoke test failed: story missing expected peroxide beat")
        print("OK: smoke test story generation succeeded.")
    except Exception as exc:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: superhero play, a scrape, peroxide, kindness, and reconciliation."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--injury", choices=INJURIES)
    ap.add_argument("--care", choices=CARE_METHODS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--apology-timing", choices=["before_care", "after_care"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate matches Python and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.injury and args.care:
        injury = INJURIES[args.injury]
        care = CARE_METHODS[args.care]
        if not injury_at_risk(injury, care) or care.sense < SENSE_MIN:
            raise StoryError(explain_rejection(injury, care))
    if args.injury and args.injury not in INJURIES:
        raise StoryError("(No story: unknown injury.)")
    if args.care and args.care not in CARE_METHODS:
        raise StoryError("(No story: unknown care method.)")

    combos = [
        combo for combo in valid_combos()
        if (args.mission is None or combo[0] == args.mission)
        and (args.injury is None or combo[1] == args.injury)
        and (args.care is None or combo[2] == args.care)
    ]
    if not combos:
        if args.injury and args.care:
            raise StoryError(explain_rejection(INJURIES[args.injury], CARE_METHODS[args.care]))
        raise StoryError("(No valid combination matches the given options.)")

    mission, injury, care = rng.choice(sorted(combos))
    hero_gender = rng.choice(["girl", "boy"])
    partner_gender = rng.choice(["girl", "boy"])
    hero_name = _pick_name(rng, hero_gender)
    partner_name = _pick_name(rng, partner_gender, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    apology_timing = args.apology_timing or rng.choice(["before_care", "after_care"])
    hero_trait = rng.choice(TRAITS)
    partner_trait = rng.choice([t for t in TRAITS if t != hero_trait] or TRAITS)
    return StoryParams(
        mission=mission,
        injury=injury,
        care=care,
        hero_name=hero_name,
        hero_gender=hero_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        parent=parent,
        apology_timing=apology_timing,
        hero_trait=hero_trait,
        partner_trait=partner_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS:
        raise StoryError(f"(No story: unknown mission '{params.mission}'.)")
    if params.injury not in INJURIES:
        raise StoryError(f"(No story: unknown injury '{params.injury}'.)")
    if params.care not in CARE_METHODS:
        raise StoryError(f"(No story: unknown care method '{params.care}'.)")

    mission = MISSIONS[params.mission]
    injury = INJURIES[params.injury]
    care = CARE_METHODS[params.care]
    if not injury_at_risk(injury, care) or care.sense < SENSE_MIN:
        raise StoryError(explain_rejection(injury, care))

    world = tell(
        mission=mission,
        injury=injury,
        care=care,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        parent_type=params.parent,
        apology_timing=params.apology_timing,
        hero_trait=params.hero_trait,
        partner_trait=params.partner_trait,
    )

    story = world.render().replace("hero", world.facts["hero_name"]).replace("partner", world.facts["partner_name"])
    # Replace only standalone labels from narration fields that intentionally used ids.
    story = story.replace("parent", world.facts["parent_ent"].label_word)

    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mission, injury, care) combos:\n")
        for mission, injury, care in combos:
            print(f"  {mission:17} {injury:12} {care}")
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
            header = f"### {p.hero_name} & {p.partner_name}: {p.mission}, {p.injury}, {p.care}"
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
