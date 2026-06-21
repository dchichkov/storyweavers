#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mackerel_whoop_reception_teamwork_rhyme_superhero_story.py
=====================================================================================

A standalone story world for a tiny superhero-story domain:

Two children in capes help prepare a seaside-style welcome reception. A shiny
mackerel decoration is part of the scene, a small snag threatens the party, and
the children solve it through teamwork guided by a simple rhyme.

Run it
------
    python storyworlds/worlds/gpt-5.4/mackerel_whoop_reception_teamwork_rhyme_superhero_story.py
    python storyworlds/worlds/gpt-5.4/mackerel_whoop_reception_teamwork_rhyme_superhero_story.py --mission aquarium --snag radio
    python storyworlds/worlds/gpt-5.4/mackerel_whoop_reception_teamwork_rhyme_superhero_story.py --fix dash_alone
    python storyworlds/worlds/gpt-5.4/mackerel_whoop_reception_teamwork_rhyme_superhero_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/mackerel_whoop_reception_teamwork_rhyme_superhero_story.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Mission:
    id: str
    place: str
    host: str
    guest: str
    scene: str
    mackerel_prop: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Snag:
    id: str
    object_label: str
    meter: str
    start_text: str
    risk_text: str
    need: str
    outcome_mark: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Fix:
    id: str
    sense: int
    covers: set[str] = field(default_factory=set)
    call: str = ""
    action_text: str = ""
    rhyme: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


class World:
    def __init__(self, mission: Mission) -> None:
        self.mission = mission
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "alarm_count": 0,
            "problem_active": False,
            "saved": False,
        }

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
        clone = World(self.mission)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def heroes(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"leader", "partner"}]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    venue = world.get("venue")
    for ent in list(world.entities.values()):
        for meter in ("wobble", "rolling", "signal_bad"):
            if ent.meters[meter] < THRESHOLD:
                continue
            sig = ("alarm", ent.id, meter)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            venue.meters["trouble"] += 1
            world.facts["alarm_count"] += 1
            world.facts["problem_active"] = True
            for hero in world.heroes():
                hero.memes["worry"] += 1
            out.append("__alarm__")
    return out


RULES = [
    Rule(name="alarm", tag="state", apply=_r_alarm),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def compatible_fixes(snag: Snag) -> list[Fix]:
    return [f for f in sensible_fixes() if snag.need in f.covers]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for mid, mission in MISSIONS.items():
        for sid, snag in SNAGS.items():
            if sid in mission.affords and compatible_fixes(snag):
                combos.append((mid, sid))
    return combos


def explain_rejection(mission: Mission, snag: Snag) -> str:
    return (
        f"(No story: {mission.place} does not fit the snag '{snag.id}'. "
        f"This reception setting needs a snag the place can honestly afford.)"
    )


def explain_fix_rejection(fid: str, sid: str) -> str:
    fix = FIXES[fid]
    snag = SNAGS[sid]
    if fix.sense < SENSE_MIN:
        better = ", ".join(sorted(f.id for f in compatible_fixes(snag)))
        return (
            f"(Refusing fix '{fid}': it is too flimsy for this world "
            f"(sense={fix.sense} < {SENSE_MIN}). Try a teamwork fix like {better}.)"
        )
    return (
        f"(No story: fix '{fid}' does not solve snag '{sid}'. "
        f"The chosen plan must really cover the problem.)"
    )


def trigger_snag(world: World, snag: Snag) -> None:
    obj = world.get("problem")
    obj.meters[snag.meter] += 1
    world.facts["problem_active"] = True
    propagate(world, narrate=False)
    world.say(snag.start_text)
    world.say(snag.risk_text)


def predict_trouble(world: World, snag: Snag) -> dict:
    sim = world.copy()
    sim.get("problem").meters[snag.meter] += 1
    propagate(sim, narrate=False)
    return {
        "trouble": sim.get("venue").meters["trouble"],
        "active": sim.facts["problem_active"],
    }


def introduce(world: World, a: Entity, b: Entity, grown: Entity, mission: Mission) -> None:
    for hero in (a, b):
        hero.memes["joy"] += 1
        hero.memes["brave"] += 1
    world.say(
        f"In {mission.place}, {a.id} and {b.id} zipped around in bright capes. "
        f"They were the {mission.host}, a tiny superhero team getting ready for "
        f"{mission.guest}'s reception."
    )
    world.say(mission.scene)
    world.say(
        f"On the middle table stood {mission.mackerel_prop}. "
        f'"Whoop!" {a.id} cried. "This will be our best welcome yet!"'
    )
    world.facts["whoop_by"] = a.id
    world.facts["mackerel_line"] = mission.mackerel_prop
    world.facts["reception_ready_before_snag"] = True
    world.facts["grown_name"] = grown.label_word


def foreshadow(world: World, a: Entity, b: Entity, snag: Snag) -> None:
    pred = predict_trouble(world, snag)
    world.facts["predicted_trouble"] = pred["trouble"]
    b.memes["care"] += 1
    world.say(
        f"{b.id} checked the room the way a careful hero checks the sky. "
        f'"Stay sharp," {b.pronoun()} whispered. "A reception can change in one blink."'
    )


def snag_scene(world: World, snag: Snag) -> None:
    trigger_snag(world, snag)


def teamwork_choice(world: World, a: Entity, b: Entity, grown: Entity, snag: Snag, fix: Fix) -> None:
    a.memes["determination"] += 1
    b.memes["determination"] += 1
    world.say(
        f"For half a second, {a.id} reached as if one hero could do everything alone. "
        f"But {grown.label_word} pointed at both children and said, "
        f'"Super work is team work. {fix.call}"'
    )
    world.say(f'{b.id} nodded. "{fix.rhyme}"')


def apply_fix(world: World, a: Entity, b: Entity, grown: Entity, snag: Snag, fix: Fix) -> None:
    problem = world.get("problem")
    venue = world.get("venue")
    world.say(fix.action_text.format(a=a.id, b=b.id, grown=grown.label_word, obj=problem.label))
    problem.meters[snag.meter] = 0.0
    problem.meters["secure"] += 1
    venue.meters["trouble"] = 0.0
    world.facts["problem_active"] = False
    world.facts["saved"] = True
    world.facts["rhyme_used"] = fix.rhyme
    world.facts["fix_sentence"] = fix.qa_text.format(obj=problem.label)
    for hero in (a, b):
        hero.memes["worry"] = 0.0
        hero.memes["relief"] += 1
        hero.memes["joy"] += 1
        hero.memes["teamwork"] += 1
    grown.memes["pride"] += 1
    world.say(
        f"The trouble stopped. The whole room seemed to take a happy breath."
    )


def ending(world: World, a: Entity, b: Entity, grown: Entity, mission: Mission, snag: Snag) -> None:
    world.say(
        f"Soon the doors opened, and the reception shone again. "
        f"{mission.guest} stepped in, saw the brave little team, and smiled."
    )
    world.say(
        f'"Who saved the day?" {mission.guest} asked. '
        f'"We did it together," said {a.id} and {b.id}.'
    )
    world.say(
        f"The shiny mackerel gleamed under the lights, and everyone gave a big whoop. "
        f"From then on, whenever {a.id} and {b.id} hurried into hero work, they remembered "
        f"their rhyme and moved as one team."
    )
    world.facts["ending_image"] = "The shiny mackerel gleamed under the lights."


def tell(
    mission: Mission,
    snag: Snag,
    fix: Fix,
    *,
    hero_a: str = "Maya",
    hero_a_gender: str = "girl",
    hero_b: str = "Leo",
    hero_b_gender: str = "boy",
    parent_type: str = "mother",
) -> World:
    world = World(mission)
    a = world.add(Entity(id=hero_a, kind="character", type=hero_a_gender, role="leader"))
    b = world.add(Entity(id=hero_b, kind="character", type=hero_b_gender, role="partner"))
    grown = world.add(Entity(id="Grownup", kind="character", type=parent_type, role="adult", label="the grown-up"))
    venue = world.add(Entity(id="venue", type="place", label=mission.place, tags=set(mission.tags)))
    world.add(
        Entity(
            id="problem",
            type="thing",
            label=snag.object_label,
            tags=set(snag.tags),
            attrs={"snag": snag.id},
        )
    )

    world.facts.update(
        mission=mission,
        snag=snag,
        fix=fix,
        hero_a=a,
        hero_b=b,
        grown=grown,
        venue=venue,
    )

    introduce(world, a, b, grown, mission)
    foreshadow(world, a, b, snag)

    world.para()
    snag_scene(world, snag)

    world.para()
    teamwork_choice(world, a, b, grown, snag, fix)
    apply_fix(world, a, b, grown, snag, fix)

    world.para()
    ending(world, a, b, grown, mission, snag)

    return world


MISSIONS = {
    "aquarium": Mission(
        id="aquarium",
        place="the little aquarium hall",
        host="Wave-Wing Helpers",
        guest="Captain Current",
        scene="Blue paper streamers curled from the ceiling, and a welcome table waited with shells, cups, and star stickers.",
        mackerel_prop="a silver cardboard mackerel with foil stripes, almost as long as a scooter",
        affords={"banner", "radio"},
        tags={"reception", "aquarium"},
    ),
    "pier": Mission(
        id="pier",
        place="the windy town pier",
        host="Harbor Flash Squad",
        guest="Captain Current",
        scene="Bright pennants snapped over the boards, and a welcome stand faced the sparkling water.",
        mackerel_prop="a shiny painted mackerel on a little parade wagon",
        affords={"banner", "wagon"},
        tags={"reception", "pier", "wind"},
    ),
    "clubhouse": Mission(
        id="clubhouse",
        place="the Sea-Spark clubhouse",
        host="Cape-and-Coral Crew",
        guest="Captain Current",
        scene="A long table held paper stars, lemon punch, and folded name cards for the neighbors.",
        mackerel_prop="a plump papier-mâché mackerel hanging above the snack table",
        affords={"wagon", "radio"},
        tags={"reception", "clubhouse"},
    ),
}

SNAGS = {
    "banner": Snag(
        id="banner",
        object_label="the welcome banner",
        meter="wobble",
        start_text="Then a seaside gust rushed through the open doorway, and the welcome banner jerked loose on one side.",
        risk_text="It flapped down toward the table and threatened to swipe the silver mackerel right onto the floor.",
        need="anchor",
        outcome_mark="banner straight",
        tags={"banner", "wind"},
    ),
    "wagon": Snag(
        id="wagon",
        object_label="the mackerel wagon",
        meter="rolling",
        start_text="Then one tiny wheel on the mackerel wagon bumped over a crack and began to roll.",
        risk_text="The shiny fish swayed toward the edge of the room, and cups on the reception table trembled with it.",
        need="brace",
        outcome_mark="wagon stopped",
        tags={"wagon", "mackerel"},
    ),
    "radio": Snag(
        id="radio",
        object_label="the crackly hero headset",
        meter="signal_bad",
        start_text="Then the little hero headset fizzed and popped, and its reception turned crackly as crumbs.",
        risk_text="No one could hear when to switch on the lights and music, so the whole welcome might start in a muddle.",
        need="relay",
        outcome_mark="message clear",
        tags={"radio", "reception"},
    ),
}

FIXES = {
    "anchor_team": Fix(
        id="anchor_team",
        sense=3,
        covers={"anchor"},
        call="One hero holds, one hero pulls, and I tie the last knot.",
        action_text="{a} planted both sneakers and held the ladder still. {b} tugged the banner tight while {grown} tied the ribbon in a hard little knot.",
        rhyme="Hold it high, pull it tight, make it bright!",
        qa_text="They saved the reception by holding the ladder, pulling the banner tight, and tying it fast.",
        tags={"teamwork", "banner", "rhyme"},
    ),
    "wheel_wedge": Fix(
        id="wheel_wedge",
        sense=3,
        covers={"brace"},
        call="One blocks, one wedges, and I steady the fish.",
        action_text="{a} slid a sneaker in front of the wheel. {b} pushed a wooden wedge under it while {grown} caught the swaying mackerel before it tipped.",
        rhyme="Block and brace, save the place!",
        qa_text="They stopped the rolling wagon by blocking the wheel, wedging it tight, and steadying the mackerel together.",
        tags={"teamwork", "wagon", "rhyme"},
    ),
    "rhyme_relay": Fix(
        id="rhyme_relay",
        sense=3,
        covers={"relay"},
        call="We will make our own relay and pass the message with our voices.",
        action_text="{a} ran to the light switch, {b} stood by the music box, and {grown} called the steps slowly while the children bounced the rhyme across the room until every signal landed clear.",
        rhyme="Tap, clap, hear it clear!",
        qa_text="They beat the bad reception by turning themselves into a relay, passing the message in rhyme until the lights and music came on together.",
        tags={"teamwork", "radio", "rhyme", "reception"},
    ),
    "dash_alone": Fix(
        id="dash_alone",
        sense=1,
        covers={"anchor", "brace", "relay"},
        call="Just dash and hope.",
        action_text="{a} dashed around alone.",
        rhyme="Zip and flip!",
        qa_text="One child tried to do everything alone.",
        tags={"poor_idea"},
    ),
}

GIRL_NAMES = ["Maya", "Lina", "Zoe", "Ivy", "Nora", "Ava", "Ruby", "Skye"]
BOY_NAMES = ["Leo", "Max", "Finn", "Toby", "Eli", "Jack", "Noah", "Kai"]


@dataclass
class StoryParams:
    mission: str
    snag: str
    fix: str
    hero_a: str
    hero_a_gender: str
    hero_b: str
    hero_b_gender: str
    parent: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


KNOWLEDGE = {
    "mackerel": [
        (
            "What is a mackerel?",
            "A mackerel is a kind of fish that lives in the sea. It has a smooth body and dark stripes along its back.",
        )
    ],
    "reception": [
        (
            "What is a reception?",
            "A reception is a friendly welcome gathering. People come together to greet someone, talk, and celebrate.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help one another on the same job. Each person does a part, and together they can do more than one person alone.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme uses words that sound alike, like tight and bright. Rhymes can help people remember what to do.",
        )
    ],
    "banner": [
        (
            "Why do people hang a banner at a party?",
            "A banner shows a message everyone can see, like welcome. It helps make the place feel cheerful and ready.",
        )
    ],
    "wagon": [
        (
            "What is a wagon used for?",
            "A wagon is a little cart with wheels for carrying things. If a wheel rolls away, the things on it can wobble or tip.",
        )
    ],
    "radio": [
        (
            "What does bad radio reception mean?",
            "Bad reception means the sound does not come through clearly. The words can crackle, pop, or get lost.",
        )
    ],
}
KNOWLEDGE_ORDER = ["mackerel", "reception", "teamwork", "rhyme", "banner", "wagon", "radio"]


def generation_prompts(world: World) -> list[str]:
    mission = world.facts["mission"]
    snag = world.facts["snag"]
    fix = world.facts["fix"]
    a = world.facts["hero_a"]
    b = world.facts["hero_b"]
    return [
        f'Write a short superhero story for a 3-to-5-year-old that includes the words "mackerel", "whoop", and "reception".',
        f"Tell a gentle superhero story where {a.id} and {b.id} prepare a welcome reception, a {snag.object_label} causes trouble, and they save the day with teamwork and a rhyme.",
        f"Write a story set at {mission.place} where two child heroes solve a problem together instead of alone, ending with a big whoop and a shiny mackerel in view.",
        f"Tell a bright superhero story where the fix is {fix.id.replace('_', ' ')} and the ending proves the reception is safe again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    mission = world.facts["mission"]
    snag = world.facts["snag"]
    fix = world.facts["fix"]
    a = world.facts["hero_a"]
    b = world.facts["hero_b"]
    grown = world.facts["grown"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two small superhero helpers, {a.id} and {b.id}. They were getting ready for {mission.guest}'s reception with {grown.label_word} nearby to guide them.",
        ),
        (
            "What special decoration did they have for the reception?",
            f"They had {mission.mackerel_prop}. That shiny mackerel helped make the welcome feel brave and festive.",
        ),
        (
            "What went wrong in the middle of the story?",
            f"The problem was with {snag.object_label}. {snag.risk_text} That is why the happy reception suddenly felt shaky.",
        ),
        (
            "Why did they need teamwork instead of one hero working alone?",
            f"They needed teamwork because one pair of hands could not safely do every part at once. The snag needed different jobs done together, so the children listened when the grown-up said super work is team work.",
        ),
        (
            "How did the rhyme help them?",
            f'The rhyme was "{fix.rhyme}" It helped them move at the same time and remember the plan while they were excited.',
        ),
        (
            "How did they save the reception?",
            f"{fix.qa_text} Because they worked together, the trouble stopped before the welcome could be spoiled.",
        ),
        (
            "How did the story end?",
            f"The reception shone again, everyone gave a big whoop, and the shiny mackerel gleamed under the lights. The ending shows that the room changed from trouble back to celebration.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    snag = world.facts["snag"]
    tags = {"mackerel", "reception", "teamwork", "rhyme"} | set(snag.tags)
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
        bits: list[str] = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mission="aquarium",
        snag="banner",
        fix="anchor_team",
        hero_a="Maya",
        hero_a_gender="girl",
        hero_b="Leo",
        hero_b_gender="boy",
        parent="mother",
    ),
    StoryParams(
        mission="pier",
        snag="wagon",
        fix="wheel_wedge",
        hero_a="Finn",
        hero_a_gender="boy",
        hero_b="Ruby",
        hero_b_gender="girl",
        parent="father",
    ),
    StoryParams(
        mission="clubhouse",
        snag="radio",
        fix="rhyme_relay",
        hero_a="Ivy",
        hero_a_gender="girl",
        hero_b="Max",
        hero_b_gender="boy",
        parent="mother",
    ),
    StoryParams(
        mission="aquarium",
        snag="radio",
        fix="rhyme_relay",
        hero_a="Skye",
        hero_a_gender="girl",
        hero_b="Kai",
        hero_b_gender="boy",
        parent="father",
    ),
]


ASP_RULES = r"""
valid(M, S) :- mission(M), snag(S), affords(M, S), has_fix(S).
sensible(F) :- fix(F), sense(F, N), sense_min(Min), N >= Min.
solves(F, S) :- covers(F, Need), needs(S, Need), sensible(F).
has_fix(S) :- solves(_, S).

#show valid/2.
#show sensible/1.
#show solves/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mid, mission in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        for sid in sorted(mission.affords):
            lines.append(asp.fact("affords", mid, sid))
    for sid, snag in SNAGS.items():
        lines.append(asp.fact("snag", sid))
        lines.append(asp.fact("needs", sid, snag.need))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        for cover in sorted(fix.covers):
            lines.append(asp.fact("covers", fid, cover))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_solves() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "solves")))


def asp_verify() -> int:
    rc = 0

    clingo_valid = set(asp_valid_combos())
    py_valid = set(valid_combos())
    if clingo_valid == py_valid:
        print(f"OK: gate matches valid_combos() ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - py_valid:
            print("  only in clingo:", sorted(clingo_valid - py_valid))
        if py_valid - clingo_valid:
            print("  only in python:", sorted(py_valid - clingo_valid))

    clingo_sensible = set(asp_sensible())
    py_sensible = {f.id for f in sensible_fixes()}
    if clingo_sensible == py_sensible:
        print(f"OK: sensible fixes match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(clingo_sensible)} python={sorted(py_sensible)}")

    py_solves = set()
    for sid, snag in SNAGS.items():
        for fix in sensible_fixes():
            if snag.need in fix.covers:
                py_solves.add((fix.id, sid))
    clingo_solves = set(asp_solves())
    if clingo_solves == py_solves:
        print(f"OK: fix coverage matches ({len(py_solves)} pairs).")
    else:
        rc = 1
        print("MISMATCH in fix coverage:")
        if clingo_solves - py_solves:
            print("  only in clingo:", sorted(clingo_solves - py_solves))
        if py_solves - clingo_solves:
            print("  only in python:", sorted(py_solves - clingo_solves))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "mackerel" not in sample.story or "whoop" not in sample.story:
            raise StoryError("(Smoke test failed: story text missing expected core words.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: child superheroes save a reception with teamwork and rhyme."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--snag", choices=SNAGS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible mission/snag pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mission and args.snag and args.snag not in MISSIONS[args.mission].affords:
        raise StoryError(explain_rejection(MISSIONS[args.mission], SNAGS[args.snag]))

    combos = [
        c
        for c in valid_combos()
        if (args.mission is None or c[0] == args.mission)
        and (args.snag is None or c[1] == args.snag)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, snag_id = rng.choice(sorted(combos))
    snag = SNAGS[snag_id]

    if args.fix:
        if args.fix not in FIXES:
            raise StoryError(f"(Unknown fix: {args.fix})")
        if snag.need not in FIXES[args.fix].covers or FIXES[args.fix].sense < SENSE_MIN:
            raise StoryError(explain_fix_rejection(args.fix, snag_id))
        fix_id = args.fix
    else:
        fix_id = rng.choice(sorted(f.id for f in compatible_fixes(snag)))

    hero_a_gender = rng.choice(["girl", "boy"])
    hero_b_gender = rng.choice(["girl", "boy"])
    hero_a = _pick_name(rng, hero_a_gender)
    hero_b = _pick_name(rng, hero_b_gender, avoid=hero_a)
    parent = args.parent or rng.choice(["mother", "father"])

    return StoryParams(
        mission=mission_id,
        snag=snag_id,
        fix=fix_id,
        hero_a=hero_a,
        hero_a_gender=hero_a_gender,
        hero_b=hero_b,
        hero_b_gender=hero_b_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.snag not in SNAGS:
        raise StoryError(f"(Unknown snag: {params.snag})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")

    mission = MISSIONS[params.mission]
    snag = SNAGS[params.snag]
    fix = FIXES[params.fix]

    if params.snag not in mission.affords:
        raise StoryError(explain_rejection(mission, snag))
    if fix.sense < SENSE_MIN or snag.need not in fix.covers:
        raise StoryError(explain_fix_rejection(params.fix, params.snag))

    world = tell(
        mission,
        snag,
        fix,
        hero_a=params.hero_a,
        hero_a_gender=params.hero_a_gender,
        hero_b=params.hero_b,
        hero_b_gender=params.hero_b_gender,
        parent_type=params.parent,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        sens = asp_sensible()
        print(f"sensible fixes: {', '.join(sens)}\n")
        print(f"{len(combos)} compatible (mission, snag) combos:\n")
        for mission, snag in combos:
            fixes = sorted(f.id for f in compatible_fixes(SNAGS[snag]))
            print(f"  {mission:10} {snag:8} [{', '.join(fixes)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.hero_a} & {p.hero_b}: {p.mission} / {p.snag} / {p.fix}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
