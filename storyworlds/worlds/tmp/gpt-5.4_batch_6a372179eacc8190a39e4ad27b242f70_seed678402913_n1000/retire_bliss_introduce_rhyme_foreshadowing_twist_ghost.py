#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/retire_bliss_introduce_rhyme_foreshadowing_twist_ghost.py
====================================================================================

A standalone storyworld about a child spending a night in an old place, hearing
a ghostly rhyme, and discovering a friendly spirit with one last duty. The
stories keep a gentle ghost-story mood: creaks, moonlight, and shivers, but the
twist is always that the ghost is helping, not hurting.

Seed constraints woven into the domain
--------------------------------------
- The word "retire" appears in the backstory of the old caretaker spirit.
- The word "bliss" appears in the quiet opening mood.
- The word "introduce" appears in the twist when the spirit speaks.
- Rhyme: the clue arrives as a short rhyming couplet.
- Foreshadowing: the elder mentions the old caretaker and the unfinished duty.
- Twist: the "haunting" is a helpful warning from a friendly ghost.

Run it
------
    python storyworlds/worlds/gpt-5.4/retire_bliss_introduce_rhyme_foreshadowing_twist_ghost.py
    python storyworlds/worlds/gpt-5.4/retire_bliss_introduce_rhyme_foreshadowing_twist_ghost.py --place lighthouse
    python storyworlds/worlds/gpt-5.4/retire_bliss_introduce_rhyme_foreshadowing_twist_ghost.py --response hide
    python storyworlds/worlds/gpt-5.4/retire_bliss_introduce_rhyme_foreshadowing_twist_ghost.py --all
    python storyworlds/worlds/gpt-5.4/retire_bliss_introduce_rhyme_foreshadowing_twist_ghost.py --qa --json
    python storyworlds/worlds/gpt-5.4/retire_bliss_introduce_rhyme_foreshadowing_twist_ghost.py --verify
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

# Make shared result containers importable when run directly from this nested
# directory: storyworlds/worlds/gpt-5.4/<file>.py -> add storyworlds/ to path.
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def elder_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    scene: str
    hush: str
    old_name: str
    old_role: str
    relic: str
    duty: str
    calm_end: str
    place_tag: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    place_tag: str
    hint_tag: str
    risk: str
    site: str
    fix: str
    solved_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Sign:
    id: str
    label: str
    place_tag: str
    hint_tag: str
    omen: str
    line1: str
    line2: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    action: str
    follow: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_threat(world: World) -> list[str]:
    problem = world.get("problem")
    if problem.meters["active"] < THRESHOLD:
        return []
    sig = ("threat", "problem")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("house").meters["danger"] += 1
    for eid in ("child", "elder"):
        if eid in world.entities:
            world.get(eid).memes["fear"] += 1
    return ["__threat__"]


def _r_relief(world: World) -> list[str]:
    problem = world.get("problem")
    if problem.meters["solved"] < THRESHOLD:
        return []
    sig = ("relief", "problem")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("house").meters["danger"] = 0.0
    for eid in ("child", "elder"):
        if eid in world.entities:
            world.get(eid).memes["relief"] += 1
            world.get(eid).memes["fear"] = 0.0
    if "spirit" in world.entities:
        world.get("spirit").memes["peace"] += 1
    return ["__relief__"]


CAUSAL_RULES = [
    Rule(name="threat", tag="physical", apply=_r_threat),
    Rule(name="relief", tag="emotional", apply=_r_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def problem_matches(place: Place, problem: Problem) -> bool:
    return place.place_tag == problem.place_tag


def sign_reveals(sign: Sign, problem: Problem, place: Place) -> bool:
    return sign.place_tag == place.place_tag and sign.hint_tag == problem.hint_tag


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for problem_id, problem in PROBLEMS.items():
            if not problem_matches(place, problem):
                continue
            for sign_id, sign in SIGNS.items():
                if sign_reveals(sign, problem, place):
                    combos.append((place_id, problem_id, sign_id))
    return combos


def predict_risk(place: Place, problem: Problem) -> dict:
    return {"danger": 1 if problem_matches(place, problem) else 0}


def arrive(world: World, child: Entity, elder: Entity, place: Place) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"{child.id} spent the evening with {child.pronoun('possessive')} {elder.elder_word} "
        f"inside {place.label}. {place.scene}"
    )
    world.say(
        f"For a little while, the whole place felt hushed and still, almost like bliss. {place.hush}"
    )


def foreshadow(world: World, elder: Entity, place: Place) -> None:
    world.say(
        f'{elder.elder_word.capitalize()} lit a small lamp and smiled at the old walls. '
        f'"This place once belonged to {place.old_name}, the {place.old_role}," '
        f'{elder.pronoun()} said.'
    )
    world.say(
        f'{elder.pronoun().capitalize()} lowered {elder.pronoun("possessive")} voice. '
        f'"People said {place.old_name} meant to retire one peaceful autumn, but never stopped '
        f'worrying about {place.duty}."'
    )


def omen(world: World, child: Entity, sign: Sign) -> None:
    child.memes["fear"] += 1
    child.memes["curiosity"] += 1
    world.say(sign.omen)
    world.say(f'"{sign.line1}"')
    world.say(f'"{sign.line2}"')


def worry(world: World, child: Entity, elder: Entity, place: Place, problem: Problem) -> None:
    pred = predict_risk(place, problem)
    world.facts["predicted_danger"] = pred["danger"]
    if pred["danger"]:
        elder.memes["concern"] += 1
        world.say(
            f'{child.id} pressed close to {elder.elder_word}. {elder.elder_word.capitalize()} listened hard '
            f'and frowned. "{problem.risk}," {elder.pronoun()} whispered.'
        )


def cower(world: World, child: Entity) -> None:
    child.memes["fear"] += 1
    world.say(
        f"{child.id} wanted to hide under the blanket and pretend the whisper had never come."
    )


def follow_clue(world: World, child: Entity, elder: Entity, response: Response, problem: Problem) -> None:
    child.memes["bravery"] += 1
    elder.memes["steady"] += 1
    world.say(
        f"{response.action} {response.follow}"
    )
    world.say(
        f"They moved toward {problem.site}, where the shadows looked deep enough to hide a secret."
    )


def spirit_intro(world: World, place: Place, sign: Sign) -> None:
    spirit = world.get("spirit")
    spirit.memes["kindness"] += 1
    world.say(
        f"Then the silver air gathered beside {place.relic}, and a pale figure took shape like mist remembering a person."
    )
    world.say(
        f'"Do not run," the figure said softly. "Let me introduce myself. I am {place.old_name}, '
        f'and I only wished to help."'
    )
    world.say(sign.reveal)


def solve_problem(world: World, child: Entity, elder: Entity, problem: Problem) -> None:
    problem_ent = world.get("problem")
    problem_ent.meters["solved"] += 1
    problem_ent.meters["active"] = 0.0
    child.memes["trust"] += 1
    elder.memes["trust"] += 1
    propagate(world, narrate=False)
    world.say(problem.fix)
    world.say(
        f"At once the mean little danger faded, as if the house itself had let out a long breath."
    )


def farewell(world: World, child: Entity, place: Place) -> None:
    spirit = world.get("spirit")
    spirit.memes["farewell"] += 1
    child.memes["wonder"] += 1
    world.say(
        f"{place.old_name} tipped a ghostly head in thanks. The moon thinned through the figure until only a kind smile remained."
    )
    world.say(
        f"After that, the night no longer felt hungry or strange. {place.calm_end}"
    )
    world.say(
        f"{child.id} went to sleep thinking that not every ghost comes to frighten; some stay because one gentle duty is still unfinished."
    )


def tell(place: Place, problem: Problem, sign: Sign, response: Response,
         child_name: str = "Nora", child_gender: str = "girl",
         elder_type: str = "grandmother", trait: str = "careful") -> World:
    world = World()
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        attrs={"name": child_name, "trait": trait},
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=elder_type,
        label="the elder",
        role="elder",
    ))
    spirit = world.add(Entity(
        id="spirit",
        kind="character",
        type="ghost",
        label=place.old_name,
        role="spirit",
    ))
    house = world.add(Entity(
        id="house",
        type="place",
        label=place.label,
        role="place",
    ))
    problem_ent = world.add(Entity(
        id="problem",
        type="problem",
        label=problem.label,
        role="problem",
        tags=set(problem.tags),
    ))
    problem_ent.meters["active"] = 1.0
    propagate(world, narrate=False)

    arrive(world, child, elder, place)
    foreshadow(world, elder, place)

    world.para()
    omen(world, child, sign)
    worry(world, child, elder, place, problem)

    world.para()
    if response.id == "hide":
        cower(world, child)
    follow_clue(world, child, elder, response, problem)
    spirit_intro(world, place, sign)
    solve_problem(world, child, elder, problem)
    farewell(world, child, place)

    world.facts.update(
        place=place,
        problem_cfg=problem,
        sign=sign,
        response=response,
        child=child,
        elder=elder,
        spirit=spirit,
        problem=problem_ent,
        solved=problem_ent.meters["solved"] >= THRESHOLD,
        twist_friendly=True,
    )
    return world


PLACES = {
    "lighthouse": Place(
        id="lighthouse",
        label="the old lighthouse on the cliff",
        scene="Salt wind tapped the windows, and the round stairs curled up into the dark like a shell.",
        hush="Far below, the sea whispered against black rocks.",
        old_name="Captain Mara",
        old_role="keeper",
        relic="the brass lamp",
        duty="the storm shutter by the lamp room",
        calm_end="The brass lamp stood quiet, and the sea shone like folded silk below the cliff.",
        place_tag="coast",
        tags={"ghost", "lighthouse", "storm"},
    ),
    "theater": Place(
        id="theater",
        label="the old playhouse at the end of Willow Street",
        scene="Dust floated in the moonbeams, and red curtains hung like sleepy giants.",
        hush="Even the stage boards seemed to be holding their breath.",
        old_name="Mr. Vale",
        old_role="prompter",
        relic="the silver call bell",
        duty="the high backdrop rope above the stage",
        calm_end="The curtains rested softly, and pale moonlight lay across the stage like a blanket.",
        place_tag="stage",
        tags={"ghost", "theater", "rope"},
    ),
    "greenhouse": Place(
        id="greenhouse",
        label="the glass greenhouse behind the orchard",
        scene="Moonlight glazed the panes, and every leaf made a shadow shaped like a hand.",
        hush="A tiny drip from the watering can sounded loud in all that stillness.",
        old_name="Mrs. Fern",
        old_role="gardener",
        relic="the iron key",
        duty="the roof vent before the cold could bite the seedlings",
        calm_end="The seedlings slept in neat rows, and the glass roof gleamed milk-white under the moon.",
        place_tag="garden",
        tags={"ghost", "greenhouse", "cold"},
    ),
}

PROBLEMS = {
    "shutter": Problem(
        id="shutter",
        label="the loose storm shutter",
        place_tag="coast",
        hint_tag="latch",
        risk="The shutter must be banging loose, and the wind could crack the lamp-room glass",
        site="the lamp room",
        fix="Grandma lifted the hook and fastened the storm shutter tight while the child held the lamp steady.",
        solved_image="the shutter sat still against the wall",
        tags={"storm", "window"},
    ),
    "rope": Problem(
        id="rope",
        label="the frayed backdrop rope",
        place_tag="stage",
        hint_tag="rope",
        risk="That old rope must be slipping, and the painted backdrop could tumble by morning",
        site="the side stairs beside the stage",
        fix="Grandpa pulled the loose rope down, and the child helped loop it around the cleat until the backdrop stood safe again.",
        solved_image="the backdrop hung firm and straight",
        tags={"rope", "stage"},
    ),
    "vent": Problem(
        id="vent",
        label="the open roof vent",
        place_tag="garden",
        hint_tag="wheel",
        risk="The roof vent must still be open, and the cold air could nip every tender seedling before dawn",
        site="the ladder under the roof vent",
        fix="Grandma climbed two careful steps and turned the little wheel closed while the child held the ladder still.",
        solved_image="the vent shut with a soft click",
        tags={"cold", "plants"},
    ),
}

SIGNS = {
    "lantern_rhyme": Sign(
        id="lantern_rhyme",
        label="a lantern rhyme",
        place_tag="coast",
        hint_tag="latch",
        omen="A cold glow skimmed across the wall, though no one had touched the brass lamp.",
        line1="When sea-wind knocks and hinges chat,",
        line2="Lift the latch and quiet that.",
        reveal='"I rattled the lamp light so you would look up in time," the spirit said. "The glass matters on stormy nights."',
        tags={"rhyme", "lighthouse"},
    ),
    "bell_rhyme": Sign(
        id="bell_rhyme",
        label="a bell rhyme",
        place_tag="stage",
        hint_tag="rope",
        omen="The silver call bell rang once by itself, a clear note in the dusty dark.",
        line1="When painted clouds begin to droop,",
        line2="Find the rope and make it loop.",
        reveal='"I rang the bell because the stage still needs watching," the spirit said. "A playhouse should wake to safe curtains."',
        tags={"rhyme", "theater"},
    ),
    "dew_rhyme": Sign(
        id="dew_rhyme",
        label="a dew rhyme",
        place_tag="garden",
        hint_tag="wheel",
        omen="A ring of silver dew brightened on the floor, though the night inside had been dry.",
        line1="When moon-breath slips through window wheel,",
        line2="Turn it shut and frost will heal.",
        reveal='"I drew the dew there to show the draft," the spirit said. "Small green things cannot ask for help with words."',
        tags={"rhyme", "greenhouse"},
    ),
}

RESPONSES = {
    "listen": Response(
        id="listen",
        sense=3,
        action="Grandma took the rhyme seriously, and together they followed the sound instead of running from it.",
        follow="The child kept one hand in hers and one hand on the warm lamp handle.",
        qa_text="They listened carefully and followed the clue together.",
        tags={"listen", "adult_help"},
    ),
    "lantern": Response(
        id="lantern",
        sense=3,
        action="Grandpa lifted a lantern, and together they went to test the strange warning instead of laughing it away.",
        follow="Its small gold circle made the dark corners feel less wild.",
        qa_text="They brought a light and checked the clue together.",
        tags={"light", "adult_help"},
    ),
    "hide": Response(
        id="hide",
        sense=1,
        action="The child pulled the blanket up to the chin for one breath.",
        follow="But fear was no fix for a real problem.",
        qa_text="They hid instead of checking, which would not solve the problem.",
        tags={"fear"},
    ),
}

GIRL_NAMES = ["Nora", "Lila", "Mina", "Rose", "Tess", "Ivy", "Ada", "June"]
BOY_NAMES = ["Eli", "Sam", "Owen", "Finn", "Theo", "Max", "Noah", "Jude"]
TRAITS = ["careful", "curious", "brave", "quiet", "thoughtful", "gentle"]


@dataclass
class StoryParams:
    place: str
    problem: str
    sign: str
    response: str
    child_name: str
    child_gender: str
    elder_type: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a story with spooky feelings, strange sounds, or a spirit. It can be scary, but gentle ghost stories end with understanding instead of harm.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is when words have matching sounds at the end, like chat and that. Rhymes can make a clue easier to remember.",
        )
    ],
    "storm": [
        (
            "Why do shutters matter in a storm?",
            "Shutters help protect windows when strong wind blows things around. If one hangs loose, the wind can bang it hard and break glass.",
        )
    ],
    "rope": [
        (
            "Why must stage ropes be tied safely?",
            "Stage ropes hold curtains and painted backdrops up high. If a rope slips, heavy cloth can fall down suddenly.",
        )
    ],
    "cold": [
        (
            "Why can cold air hurt seedlings?",
            "Seedlings are tiny new plants, and cold air can damage them before they grow strong. A closed vent helps keep them warmer at night.",
        )
    ],
    "adult_help": [
        (
            "Why is it smart to ask a grown-up for help when something feels spooky or dangerous?",
            "A grown-up can stay calm, bring a light, and check what is really wrong. That makes it easier to solve the problem safely.",
        )
    ],
    "light": [
        (
            "Why does bringing a light help in the dark?",
            "A light helps people see corners, stairs, and small clues. When you can see clearly, the dark feels less confusing.",
        )
    ],
}

KNOWLEDGE_ORDER = ["ghost", "rhyme", "storm", "rope", "cold", "adult_help", "light"]


def child_name(world: World) -> str:
    return world.facts["child"].attrs.get("name", "the child")


def generation_prompts(world: World) -> list[str]:
    place = world.facts["place"]
    problem = world.facts["problem_cfg"]
    child = world.facts["child"]
    elder = world.facts["elder"]
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old that includes the words "retire", "bliss", and "introduce". Use a rhyming clue and a friendly twist.',
        f"Tell a spooky-but-kind story where a {child.type} spends the night in {place.label}, hears a rhyme in the dark, and discovers a ghost warning about {problem.label}.",
        f"Write a story with foreshadowing: {child_name(world)} hears that {place.old_name} meant to retire, and later learns the spirit stayed to finish one last duty with {elder.elder_word}'s help.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    place = world.facts["place"]
    problem = world.facts["problem_cfg"]
    sign = world.facts["sign"]
    response = world.facts["response"]
    child = world.facts["child"]
    elder = world.facts["elder"]
    name = child_name(world)
    elder_word = elder.elder_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name}, {name}'s {elder_word}, and the spirit of {place.old_name} in {place.label}. The story begins with a spooky night and ends with everyone understanding one another.",
        ),
        (
            f"Why did the night feel spooky at first?",
            f"It felt spooky because {sign.omen.lower()} Then the rhyming voice made the dark seem even stranger.",
        ),
        (
            f"What did {elder_word} say before the ghost appeared?",
            f"{elder_word.capitalize()} said that {place.old_name} had meant to retire but never stopped worrying about {place.duty}. That foreshadowed that the haunting might be about unfinished care, not meanness.",
        ),
        (
            "What was the twist?",
            f"The twist was that the ghost was friendly and wanted to help. {place.old_name} used the rhyme to warn them about {problem.label}, not to scare them for fun.",
        ),
        (
            f"How did they solve the problem?",
            f"{response.qa_text} Then {problem.fix[0].lower() + problem.fix[1:]} The danger ended as soon as the real problem was fixed.",
        ),
        (
            f"How did the story end?",
            f"It ended peacefully. {place.calm_end} That ending image shows the place had become safe and calm again.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ghost", "rhyme", "adult_help"} | set(world.facts["place"].tags) | set(world.facts["response"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="lighthouse",
        problem="shutter",
        sign="lantern_rhyme",
        response="listen",
        child_name="Nora",
        child_gender="girl",
        elder_type="grandmother",
        trait="careful",
    ),
    StoryParams(
        place="theater",
        problem="rope",
        sign="bell_rhyme",
        response="lantern",
        child_name="Theo",
        child_gender="boy",
        elder_type="grandfather",
        trait="curious",
    ),
    StoryParams(
        place="greenhouse",
        problem="vent",
        sign="dew_rhyme",
        response="listen",
        child_name="Ivy",
        child_gender="girl",
        elder_type="grandmother",
        trait="gentle",
    ),
]


def explain_rejection(place: Place, problem: Problem, sign: Optional[Sign] = None) -> str:
    if not problem_matches(place, problem):
        return (
            f"(No story: {problem.label} does not belong in {place.label}. "
            f"This world only uses problems that fit the place's real old duty.)"
        )
    if sign is not None and not sign_reveals(sign, problem, place):
        return (
            f"(No story: {sign.label} would not honestly point to {problem.label} in {place.label}. "
            f"The ghost's rhyme must reveal the right clue.)"
        )
    return "(No story: this combination is not reasonable in the world model.)"


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). The child needs a calm, useful response. "
        f"Try one of: {better}.)"
    )


ASP_RULES = r"""
matches_place(Pl, Pr) :- place_tag(Pl, T), problem_tag(Pr, T).
reveals(S, Pr, Pl) :- sign_place_tag(S, PT), place_tag(Pl, PT),
                      sign_hint_tag(S, HT), problem_hint_tag(Pr, HT).
valid(Pl, Pr, S) :- place(Pl), problem(Pr), sign(S), matches_place(Pl, Pr), reveals(S, Pr, Pl).
sensible(R) :- response(R), sense(R, V), sense_min(M), V >= M.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("place_tag", pid, place.place_tag))
    for prid, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", prid))
        lines.append(asp.fact("problem_tag", prid, problem.place_tag))
        lines.append(asp.fact("problem_hint_tag", prid, problem.hint_tag))
    for sid, sign in SIGNS.items():
        lines.append(asp.fact("sign", sid))
        lines.append(asp.fact("sign_place_tag", sid, sign.place_tag))
        lines.append(asp.fact("sign_hint_tag", sid, sign.hint_tag))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a child hears a ghostly rhyme and discovers a friendly spirit with one last duty."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, problem, sign) triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.place and args.problem:
        place = PLACES[args.place]
        problem = PROBLEMS[args.problem]
        if not problem_matches(place, problem):
            raise StoryError(explain_rejection(place, problem))
    if args.place and args.problem and args.sign:
        place = PLACES[args.place]
        problem = PROBLEMS[args.problem]
        sign = SIGNS[args.sign]
        if not sign_reveals(sign, problem, place):
            raise StoryError(explain_rejection(place, problem, sign))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.problem is None or combo[1] == args.problem)
        and (args.sign is None or combo[2] == args.sign)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, problem_id, sign_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        problem=problem_id,
        sign=sign_id,
        response=response_id,
        child_name=name,
        child_gender=gender,
        elder_type=elder,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.sign not in SIGNS:
        raise StoryError(f"(Unknown sign: {params.sign})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    place = PLACES[params.place]
    problem = PROBLEMS[params.problem]
    sign = SIGNS[params.sign]
    response = RESPONSES[params.response]

    if not problem_matches(place, problem):
        raise StoryError(explain_rejection(place, problem))
    if not sign_reveals(sign, problem, place):
        raise StoryError(explain_rejection(place, problem, sign))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        place=place,
        problem=problem,
        sign=sign,
        response=response,
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render().replace("child", params.child_name),
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
    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: gate matches valid_combos() ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    clingo_sens = set(asp_sensible())
    python_sens = {r.id for r in sensible_responses()}
    if clingo_sens == python_sens:
        print(f"OK: sensible responses match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        params = resolve_params(build_parser().parse_args([]), random.Random(7))
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("generated empty story from random params")
        print("OK: random generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"RANDOM GENERATION FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, problem, sign) combos:\n")
        for place, problem, sign in combos:
            print(f"  {place:10} {problem:8} {sign}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.place} / {p.problem} / {p.sign}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
