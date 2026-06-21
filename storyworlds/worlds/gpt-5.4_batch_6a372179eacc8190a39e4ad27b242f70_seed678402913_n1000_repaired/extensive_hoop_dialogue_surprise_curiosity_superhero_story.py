#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/extensive_hoop_dialogue_surprise_curiosity_superhero_story.py
=========================================================================================

A standalone story world for a tiny superhero-style tale about a child who spots
a mystery tucked in a hoop during practice, grows curious, and reaches it the
safe way with help.

This world emphasizes:
- the seed words "extensive" and "hoop"
- dialogue as a major storytelling tool
- curiosity as the motivating tension
- a surprise reveal at the end
- a bright, child-facing superhero tone

Run it
------
    python storyworlds/worlds/gpt-5.4/extensive_hoop_dialogue_surprise_curiosity_superhero_story.py
    python storyworlds/worlds/gpt-5.4/extensive_hoop_dialogue_surprise_curiosity_superhero_story.py --place gym --hoop hanging_ring --surprise badge_envelope
    python storyworlds/worlds/gpt-5.4/extensive_hoop_dialogue_surprise_curiosity_superhero_story.py --method rolling_chair
    python storyworlds/worlds/gpt-5.4/extensive_hoop_dialogue_surprise_curiosity_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/extensive_hoop_dialogue_surprise_curiosity_superhero_story.py --verify
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
SENSE_MIN = 2


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
        female = {"girl", "mother", "mom", "woman", "coach_woman"}
        male = {"boy", "father", "dad", "man", "coach_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "coach_woman": "coach",
            "coach_man": "coach",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    intro: str
    course: str
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class HoopSite:
    id: str
    label: str
    phrase: str
    height: int
    peek: str
    risky: str
    access: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str
    label: str
    phrase: str
    reveal: str
    ending: str
    fragile: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    sense: int
    reach: int
    gentle: bool
    setup: str
    success: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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


def _r_curiosity_to_wonder(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if hero is None:
        return out
    if hero.memes["curiosity"] >= THRESHOLD and ("wonder", hero.id) not in world.fired:
        world.fired.add(("wonder", hero.id))
        hero.memes["wonder"] += 1
        out.append("__wonder__")
    return out


def _r_risk_to_alarm(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if hero is None:
        return out
    if hero.meters["risk"] >= THRESHOLD and ("alarm", hero.id) not in world.fired:
        world.fired.add(("alarm", hero.id))
        hero.memes["worry"] += 1
        out.append("__alarm__")
    return out


def _r_reached_to_relief(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if hero is None:
        return out
    if hero.meters["reached"] >= THRESHOLD and ("relief", hero.id) not in world.fired:
        world.fired.add(("relief", hero.id))
        hero.memes["relief"] += 1
        hero.memes["pride"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="curiosity_to_wonder", tag="emotion", apply=_r_curiosity_to_wonder),
    Rule(name="risk_to_alarm", tag="safety", apply=_r_risk_to_alarm),
    Rule(name="reached_to_relief", tag="emotion", apply=_r_reached_to_relief),
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


PLACES = {
    "gym": Place(
        id="gym",
        label="the neighborhood gym",
        intro="The lights shone on blue mats, bright cones, and a painted wall of stars.",
        course="An extensive superhero practice course zigzagged from the mats to the climbing rope.",
        supports={"practice_hoop", "hanging_ring", "ceiling_hoop"},
        tags={"gym", "training"},
    ),
    "playground": Place(
        id="playground",
        label="the playground",
        intro="The monkey bars gleamed, and the slide flashed silver in the sun.",
        course="An extensive superhero practice course wound between chalk arrows, beanbags, and a rope line.",
        supports={"practice_hoop", "hanging_ring"},
        tags={"playground", "outside"},
    ),
    "hall": Place(
        id="hall",
        label="the community hall",
        intro="Paper stars swung gently above the polished floor.",
        course="An extensive superhero practice course stretched past chairs, soft blocks, and a cape rack.",
        supports={"practice_hoop", "ceiling_hoop"},
        tags={"hall", "party"},
    ),
}

HOOPS = {
    "practice_hoop": HoopSite(
        id="practice_hoop",
        label="practice hoop",
        phrase="a red practice hoop",
        height=1,
        peek="something shiny peeking from the side of the hoop",
        risky="hop onto a nearby foam block and snatch at it",
        access="right at hero height",
        tags={"hoop", "low"},
    ),
    "hanging_ring": HoopSite(
        id="hanging_ring",
        label="hanging hoop",
        phrase="a hanging hoop",
        height=2,
        peek="a silver corner sticking out of the hanging hoop",
        risky="stack two wobbling mats and reach from the top",
        access="just high enough to make a child stretch and guess",
        tags={"hoop", "medium"},
    ),
    "ceiling_hoop": HoopSite(
        id="ceiling_hoop",
        label="ceiling hoop",
        phrase="a gold hoop hanging near the ceiling",
        height=3,
        peek="a tiny flash of paper caught in the gold hoop",
        risky="climb the cape rack and grab for it",
        access="so high that it looked almost like a cloud ring",
        tags={"hoop", "high"},
    ),
}

SURPRISES = {
    "badge_envelope": Surprise(
        id="badge_envelope",
        label="badge envelope",
        phrase="a silver envelope",
        reveal='Inside was a shiny Junior Hero badge with a lightning bolt in the middle.',
        ending="The badge winked on hero's shirt while hero marched the course with an even taller smile.",
        fragile=False,
        tags={"badge", "surprise"},
    ),
    "thank_you_note": Surprise(
        id="thank_you_note",
        label="thank-you note",
        phrase="a folded star note",
        reveal='Inside was a thank-you note that said, "For brave helping and careful choices."',
        ending="Hero tucked the note beside hero_pos cape and felt warm all the way to hero_pos toes.",
        fragile=True,
        tags={"note", "surprise"},
    ),
    "cape_patch": Surprise(
        id="cape_patch",
        label="cape patch",
        phrase="a little paper packet",
        reveal='Inside was a bright patch shaped like a comet, made to pin on a cape.',
        ending="Soon the new patch fluttered on the cape while hero ran another lap as if the room had grown brighter.",
        fragile=False,
        tags={"cape", "surprise"},
    ),
}

METHODS = {
    "jump": Method(
        id="jump",
        label="a careful jump",
        sense=2,
        reach=1,
        gentle=True,
        setup="bent hero_pos knees and took one careful superhero jump",
        success="jumped neatly and reached the surprise without bumping the hoop",
        qa_text="used one careful jump to reach it",
        tags={"jump"},
    ),
    "stool": Method(
        id="stool",
        label="a small step stool",
        sense=3,
        reach=2,
        gentle=True,
        setup="opened a small step stool and held it steady",
        success="stepped up, stretched, and lifted the surprise free with two calm hands",
        qa_text="used a steady step stool and lifted it down",
        tags={"stool", "safe_tool"},
    ),
    "grabber": Method(
        id="grabber",
        label="a long grabber tool",
        sense=3,
        reach=3,
        gentle=True,
        setup="fetched the long grabber from the supply bin and showed hero how to squeeze it slowly",
        success="reached up with the grabber, pinched the surprise softly, and brought it down",
        qa_text="used a long grabber to bring it down softly",
        tags={"grabber", "safe_tool"},
    ),
    "rolling_chair": Method(
        id="rolling_chair",
        label="a rolling chair",
        sense=1,
        reach=2,
        gentle=False,
        setup="dragged over a rolling chair",
        success="balanced on the chair and somehow got it down",
        qa_text="stood on a rolling chair",
        tags={"chair", "unsafe"},
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for hoop_id in place.supports:
            for surprise_id in SURPRISES:
                combos.append((place_id, hoop_id, surprise_id))
    return sorted(combos)


@dataclass
class StoryParams:
    place: str
    hoop: str
    surprise: str
    method: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    relation: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="gym",
        hoop="hanging_ring",
        surprise="badge_envelope",
        method="stool",
        hero_name="Maya",
        hero_type="girl",
        helper_name="Coach Ben",
        helper_type="coach_man",
        relation="coach",
        trait="curious",
    ),
    StoryParams(
        place="playground",
        hoop="practice_hoop",
        surprise="cape_patch",
        method="jump",
        hero_name="Leo",
        hero_type="boy",
        helper_name="Dad",
        helper_type="father",
        relation="parent",
        trait="eager",
    ),
    StoryParams(
        place="hall",
        hoop="ceiling_hoop",
        surprise="thank_you_note",
        method="grabber",
        hero_name="Nora",
        hero_type="girl",
        helper_name="Coach Ava",
        helper_type="coach_woman",
        relation="coach",
        trait="thoughtful",
    ),
    StoryParams(
        place="gym",
        hoop="practice_hoop",
        surprise="thank_you_note",
        method="jump",
        hero_name="Finn",
        hero_type="boy",
        helper_name="Mom",
        helper_type="mother",
        relation="parent",
        trait="gentle",
    ),
]


GIRL_NAMES = ["Lily", "Maya", "Nora", "Ava", "Zoe", "Ruby", "Ella", "Lucy"]
BOY_NAMES = ["Leo", "Max", "Finn", "Theo", "Sam", "Eli", "Ben", "Noah"]
TRAITS = ["curious", "eager", "thoughtful", "bold", "gentle", "careful"]


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def method_works(method: Method, hoop: HoopSite, surprise: Surprise) -> bool:
    if method.sense < SENSE_MIN:
        return False
    if method.reach < hoop.height:
        return False
    if surprise.fragile and not method.gentle:
        return False
    return True


def explain_method(method_id: str, hoop: HoopSite, surprise: Surprise) -> str:
    method = METHODS[method_id]
    if method.sense < SENSE_MIN:
        better = ", ".join(sorted(m.id for m in sensible_methods()))
        return (
            f"(Refusing method '{method_id}': it is too unsafe for this world "
            f"(sense={method.sense} < {SENSE_MIN}). Try one of: {better}.)"
        )
    if method.reach < hoop.height:
        return (
            f"(Refusing method '{method_id}': {method.label} cannot reach the "
            f"{hoop.label}, which is {hoop.access}. Pick a method with more reach.)"
        )
    if surprise.fragile and not method.gentle:
        return (
            f"(Refusing method '{method_id}': {surprise.phrase} should be brought "
            f"down gently, not with a rough method.)"
        )
    return "(Refusing method: it does not fit the story's safety rules.)"


def explain_combo(place: Place, hoop_id: str) -> str:
    return (
        f"(No story: {place.label} does not have the right setup for the "
        f"{HOOPS[hoop_id].label}. Pick a hoop that belongs in that place.)"
    )


def predict_attempt(world: World, method: Method, hoop: HoopSite, surprise: Surprise) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    if method.reach < hoop.height:
        hero.meters["risk"] += 1
    if surprise.fragile and not method.gentle:
        hero.meters["risk"] += 1
    if method_works(method, hoop, surprise):
        hero.meters["reached"] += 1
    propagate(sim, narrate=False)
    return {
        "risk": hero.meters["risk"],
        "reached": hero.meters["reached"],
        "worry": hero.memes["worry"],
    }


def introduce(world: World, hero: Entity, helper: Entity, place: Place) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} clipped on hero_pos cape and hurried into {place.label} with "
        f"{helper.id}. {place.intro}"
        .replace("hero_pos", hero.pronoun("possessive"))
    )
    world.say(place.course)


def notice_peek(world: World, hero: Entity, hoop: HoopSite, surprise: Surprise) -> None:
    hero.memes["curiosity"] += 1
    world.get("hoop").meters["holds_surprise"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {hero.id} stopped short. In {hoop.phrase}, {hero.pronoun()} saw "
        f"{hoop.peek}."
    )
    world.say(
        f'"What is that?" {hero.id} whispered. "{surprise.phrase.capitalize()}? '
        f'In the hoop?"'
    )


def ask_questions(world: World, hero: Entity, helper: Entity, hoop: HoopSite) -> None:
    hero.memes["curiosity"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} took one step closer. "Did a superhero hide it there?" '
        f'{hero.pronoun()} asked.'
    )
    world.say(
        f'"Maybe," said {helper.id}. "What do you think?"'
    )
    world.say(
        f'"I want to know right now," said {hero.id}. "Why would someone tuck '
        f'a surprise into a {hoop.label}?"'
    )


def risky_idea(world: World, hero: Entity, hoop: HoopSite) -> None:
    hero.meters["risk"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} pointed up. "I could just {hoop.risky}," {hero.pronoun()} said.'
    )


def guide_choice(world: World, hero: Entity, helper: Entity, hoop: HoopSite, method: Method, surprise: Surprise) -> None:
    prediction = predict_attempt(world, method, hoop, surprise)
    world.facts["predicted_risk"] = prediction["risk"]
    world.facts["predicted_reached"] = prediction["reached"]
    if prediction["risk"] >= THRESHOLD:
        world.say(
            f'"Let\'s slow our superhero feet," said {helper.id}. "That way could '
            f'wobble or squash the surprise."'
        )
    else:
        world.say(
            f'"Good wondering," said {helper.id}. "A real hero uses a safe plan '
            f'when curiosity grows big."'
        )
    world.say(
        f'"Then what should we do?" asked {hero.id}.'
    )
    world.say(
        f'{helper.id} smiled. "We will use {method.label}."'
    )


def use_method(world: World, hero: Entity, helper: Entity, method: Method, hoop: HoopSite, surprise: Surprise) -> None:
    world.say(
        method.setup
        .replace("hero_pos", hero.pronoun("possessive"))
    )
    if not method_works(method, hoop, surprise):
        raise StoryError(explain_method(method.id, hoop, surprise))
    hero.meters["reached"] += 1
    hero.meters["risk"] = 0.0
    world.get("surprise").meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Together they {method.success}."
    )


def reveal_surprise(world: World, hero: Entity, helper: Entity, surprise: Surprise) -> None:
    hero.memes["surprise"] += 1
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f'"Open it, open it!" said {hero.id}.'
    )
    world.say(
        f"{helper.id} placed the surprise in {hero.pronoun('possessive')} hands. "
        f"{surprise.reveal}"
    )
    world.say(
        f'{hero.id} gasped. "For me?"'
    )
    if world.facts.get("relation") == "coach":
        world.say(
            f'"For you," said {helper.id}, "because heroes are not only brave. '
            f'They are careful too."'
        )
    else:
        world.say(
            f'"For you," said {helper.id}. "You asked questions, listened, and '
            f'chose the safe way."'
        )


def ending(world: World, hero: Entity, surprise: Surprise) -> None:
    hero_pos = hero.pronoun("possessive")
    world.say(
        surprise.ending.replace("hero", hero.id).replace("hero_pos", hero_pos)
    )


def tell(
    place: Place,
    hoop: HoopSite,
    surprise_cfg: Surprise,
    method: Method,
    hero_name: str,
    hero_type: str,
    helper_name: str,
    helper_type: str,
    relation: str,
    trait: str,
) -> World:
    world = World(place)
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type=hero_type,
            label=hero_name,
            phrase=hero_name,
            role="hero",
            attrs={"display": hero_name, "trait": trait},
            tags={"hero"},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_type,
            label=helper_name,
            phrase=helper_name,
            role="helper",
            attrs={"display": helper_name, "relation": relation},
            tags={"helper"},
        )
    )
    hoop_ent = world.add(
        Entity(
            id="hoop",
            kind="thing",
            type="hoop",
            label=hoop.label,
            phrase=hoop.phrase,
            role="hoop",
            tags=set(hoop.tags),
        )
    )
    surprise_ent = world.add(
        Entity(
            id="surprise",
            kind="thing",
            type="surprise",
            label=surprise_cfg.label,
            phrase=surprise_cfg.phrase,
            role="surprise",
            tags=set(surprise_cfg.tags),
        )
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        hoop_cfg=hoop,
        hoop=hoop_ent,
        surprise_cfg=surprise_cfg,
        surprise=surprise_ent,
        method=method,
        place=place,
        relation=relation,
    )

    introduce(world, hero=hero, helper=helper, place=place)
    notice_peek(world, hero=hero, hoop=hoop, surprise=surprise_cfg)
    ask_questions(world, hero=hero, helper=helper, hoop=hoop)

    world.para()
    risky_idea(world, hero=hero, hoop=hoop)
    guide_choice(world, hero=hero, helper=helper, hoop=hoop, method=method, surprise=surprise_cfg)

    world.para()
    use_method(world, hero=hero, helper=helper, method=method, hoop=hoop, surprise=surprise_cfg)
    reveal_surprise(world, hero=hero, helper=helper, surprise=surprise_cfg)

    world.para()
    ending(world, hero=hero, surprise=surprise_cfg)
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    hoop = world.facts["hoop_cfg"]
    surprise = world.facts["surprise_cfg"]
    place = world.facts["place"]
    return [
        'Write a short superhero story for a 3-to-5-year-old that includes the words "extensive" and "hoop".',
        f"Tell a superhero story where {hero.label} spots {surprise.phrase} in {hoop.phrase} at {place.label}, grows curious, and asks lots of questions.",
        f"Write a dialogue-rich story where {helper.label_word} {helper.label} helps a child investigate a mystery in a hoop and the ending includes a gentle surprise.",
    ]


KNOWLEDGE = {
    "hoop": [
        (
            "What is a hoop?",
            "A hoop is a round ring. Children can jump through it, toss it, or use it in games and practice."
        )
    ],
    "curiosity": [
        (
            "What is curiosity?",
            "Curiosity is the feeling that makes you want to know more. It can help you learn when you ask questions and look carefully."
        )
    ],
    "surprise": [
        (
            "What is a surprise?",
            "A surprise is something you do not expect at first. It can make people open their eyes wide and smile."
        )
    ],
    "stool": [
        (
            "What is a step stool for?",
            "A step stool helps you reach something a little higher. A grown-up should make sure it is steady."
        )
    ],
    "grabber": [
        (
            "What is a grabber tool?",
            "A grabber is a long tool that helps you pick something up from far away or high up. It lets you reach without climbing."
        )
    ],
    "safe_tool": [
        (
            "Why do safe tools matter?",
            "Safe tools help you do a job without wobbling or falling. They make careful choices easier."
        )
    ],
    "badge": [
        (
            "What is a badge?",
            "A badge is a little sign or token that shows someone did something special. Children often wear one with pride."
        )
    ],
    "note": [
        (
            "What is a note?",
            "A note is a short written message. It can tell someone thank you or share an idea."
        )
    ],
    "cape": [
        (
            "What is a cape?",
            "A cape is a piece of cloth that hangs from your shoulders. In pretend play, it can make someone feel like a superhero."
        )
    ],
}
KNOWLEDGE_ORDER = ["hoop", "curiosity", "surprise", "stool", "grabber", "safe_tool", "badge", "note", "cape"]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    hoop = world.facts["hoop_cfg"]
    surprise = world.facts["surprise_cfg"]
    method = world.facts["method"]
    place = world.facts["place"]
    risk = world.facts.get("predicted_risk", 0)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child pretending to be a superhero, and {helper.label}, the helper nearby. They were together at {place.label}."
        ),
        (
            "What made the hero curious?",
            f"{hero.label} saw {hoop.peek} in {hoop.phrase}. That tiny sight made {hero.pronoun('object')} want to know what was hiding there."
        ),
        (
            "Why did the story have so much dialogue?",
            f"The dialogue shows how curiosity grew. {hero.label} kept asking questions, and {helper.label} answered with a calm plan."
        ),
    ]
    if risk >= THRESHOLD:
        qa.append(
            (
                f"Why did {helper.label} slow {hero.label} down?",
                f"{helper.label} wanted to stop a risky shortcut before it turned wobbly or rough. The mystery was high in the hoop, so a safe tool was better than grabbing in a rush."
            )
        )
    qa.append(
        (
            f"How did they get the surprise down?",
            f"They used {method.label}. That worked because it could reach the {hoop.label} and bring the surprise down carefully."
        )
    )
    qa.append(
        (
            "What was the surprise at the end?",
            f"The surprise was {surprise.reveal[10:] if surprise.reveal.startswith('Inside was ') else surprise.reveal} The ending feels happy because curiosity led to a kind reward instead of trouble."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    method = world.facts["method"]
    surprise = world.facts["surprise_cfg"]
    tags = {"hoop", "curiosity", "surprise"} | set(method.tags) | set(surprise.tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, H, S) :- place(P), hoop(H), surprise(S), supported(P, H).

sensible(M) :- method(M), sense(M, V), sense_min(Min), V >= Min.
works(M, H, S) :- sensible(M), reach(M, R), height(H, Need), R >= Need,
                  not needs_gentle(S), not gentle(M, 0).
works(M, H, S) :- sensible(M), reach(M, R), height(H, Need), R >= Need,
                  not needs_gentle(S), gentle(M, 1).
works(M, H, S) :- sensible(M), reach(M, R), height(H, Need), R >= Need,
                  needs_gentle(S), gentle(M, 1).

story_ok(P, H, S, M) :- valid(P, H, S), works(M, H, S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for hoop_id in sorted(place.supports):
            lines.append(asp.fact("supported", place_id, hoop_id))
    for hoop_id, hoop in HOOPS.items():
        lines.append(asp.fact("hoop", hoop_id))
        lines.append(asp.fact("height", hoop_id, hoop.height))
    for surprise_id, surprise in SURPRISES.items():
        lines.append(asp.fact("surprise", surprise_id))
        if surprise.fragile:
            lines.append(asp.fact("needs_gentle", surprise_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        lines.append(asp.fact("reach", method_id, method.reach))
        lines.append(asp.fact("gentle", method_id, 1 if method.gentle else 0))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_story_ok() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show story_ok/4."))
    return sorted(set(asp.atoms(model, "story_ok")))


def python_story_ok() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for place_id, hoop_id, surprise_id in valid_combos():
        hoop = HOOPS[hoop_id]
        surprise = SURPRISES[surprise_id]
        for method in METHODS.values():
            if method_works(method, hoop, surprise):
                out.append((place_id, hoop_id, surprise_id, method.id))
    return sorted(out)


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

    clingo_story = set(asp_story_ok())
    py_story = set(python_story_ok())
    if clingo_story == py_story:
        print(f"OK: story_ok matches Python method checks ({len(clingo_story)} cases).")
    else:
        rc = 1
        print("MISMATCH in story_ok:")
        if clingo_story - py_story:
            print("  only in clingo:", sorted(clingo_story - py_story))
        if py_story - clingo_story:
            print("  only in python:", sorted(py_story - clingo_story))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Superhero story world: a child spots a mystery in a hoop and reaches it safely."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hoop", choices=HOOPS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--hero-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "coach_woman", "coach_man"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the clingo-compatible story set")
    ap.add_argument("--verify", action="store_true", help="verify ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the inline ASP program")
    return ap


def helper_display(helper_type: str, rng: random.Random) -> str:
    if helper_type == "mother":
        return "Mom"
    if helper_type == "father":
        return "Dad"
    if helper_type == "coach_woman":
        return rng.choice(["Coach Ava", "Coach Nina", "Coach June"])
    return rng.choice(["Coach Ben", "Coach Max", "Coach Eli"])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.hoop and args.hoop not in PLACES[args.place].supports:
        raise StoryError(explain_combo(PLACES[args.place], args.hoop))

    place_choices = [p for p in PLACES if args.place is None or p == args.place]
    if not place_choices:
        raise StoryError("(No valid place matches the given options.)")
    place_id = rng.choice(sorted(place_choices))
    place = PLACES[place_id]

    hoop_choices = [h for h in place.supports if args.hoop is None or h == args.hoop]
    if not hoop_choices:
        if args.hoop is not None:
            raise StoryError(explain_combo(place, args.hoop))
        raise StoryError("(No valid hoop matches the given options.)")
    hoop_id = rng.choice(sorted(hoop_choices))

    surprise_choices = [s for s in SURPRISES if args.surprise is None or s == args.surprise]
    if not surprise_choices:
        raise StoryError("(No valid surprise matches the given options.)")
    surprise_id = rng.choice(sorted(surprise_choices))

    hoop = HOOPS[hoop_id]
    surprise = SURPRISES[surprise_id]

    if args.method is not None:
        if args.method not in METHODS:
            raise StoryError("(No valid method matches the given options.)")
        if not method_works(METHODS[args.method], hoop, surprise):
            raise StoryError(explain_method(args.method, hoop, surprise))
        method_id = args.method
    else:
        candidates = [m.id for m in sensible_methods() if method_works(m, hoop, surprise)]
        if not candidates:
            raise StoryError("(No safe method works for that hoop and surprise.)")
        method_id = rng.choice(sorted(candidates))

    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_type = args.helper or rng.choice(["mother", "father", "coach_woman", "coach_man"])
    relation = "coach" if helper_type.startswith("coach") else "parent"
    helper_name = helper_display(helper_type, rng)
    trait = rng.choice(TRAITS)

    return StoryParams(
        place=place_id,
        hoop=hoop_id,
        surprise=surprise_id,
        method=method_id,
        hero_name=hero_name,
        hero_type=gender,
        helper_name=helper_name,
        helper_type=helper_type,
        relation=relation,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place '{params.place}'.)")
    if params.hoop not in HOOPS:
        raise StoryError(f"(Unknown hoop '{params.hoop}'.)")
    if params.surprise not in SURPRISES:
        raise StoryError(f"(Unknown surprise '{params.surprise}'.)")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method '{params.method}'.)")
    if params.hoop not in PLACES[params.place].supports:
        raise StoryError(explain_combo(PLACES[params.place], params.hoop))
    if not method_works(METHODS[params.method], HOOPS[params.hoop], SURPRISES[params.surprise]):
        raise StoryError(explain_method(params.method, HOOPS[params.hoop], SURPRISES[params.surprise]))

    world = tell(
        place=PLACES[params.place],
        hoop=HOOPS[params.hoop],
        surprise_cfg=SURPRISES[params.surprise],
        method=METHODS[params.method],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        relation=params.relation,
        trait=params.trait,
    )

    story_text = world.render()
    hero_name = params.hero_name
    helper_name = params.helper_name
    story_text = story_text.replace("hero", hero_name).replace("helper", helper_name)

    return StorySample(
        params=params,
        story=story_text,
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
        print(asp_program("", "#show valid/3.\n#show story_ok/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        stories = asp_story_ok()
        print(f"{len(combos)} compatible (place, hoop, surprise) combos:\n")
        for place_id, hoop_id, surprise_id in combos:
            methods = sorted(m for (p, h, s, m) in stories if (p, h, s) == (place_id, hoop_id, surprise_id))
            print(f"  {place_id:10} {hoop_id:14} {surprise_id:14}  [{', '.join(methods)}]")
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
            header = f"### {p.hero_name}: {p.surprise} in {p.hoop} at {p.place} ({p.method})"
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
