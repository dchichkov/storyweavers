#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/trapeze_quest_rhyme_detective_story.py
=================================================================

A standalone story world for a tiny child-facing detective quest: before a
trapeze practice can begin, a small show token goes missing. A child detective
uses a rhyming clue, follows sensible evidence, and finds the token in a place
that fits both the clue and the world.

The world is deliberately narrow. It prefers a few plausible detective stories
over broad but weak coverage. The core reasonableness rule is simple:

- each clue truthfully points to one hiding place
- each hiding place has a height (low or high)
- the chosen retrieval method must safely reach that height

So a low hiding place can be reached by hand, but a high perch near the trapeze
rig needs a grown-up with a ladder. Invalid choices are rejected with a clear
StoryError.

Run it
------
    python storyworlds/worlds/gpt-5.4/trapeze_quest_rhyme_detective_story.py
    python storyworlds/worlds/gpt-5.4/trapeze_quest_rhyme_detective_story.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/trapeze_quest_rhyme_detective_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/trapeze_quest_rhyme_detective_story.py --trace
    python storyworlds/worlds/gpt-5.4/trapeze_quest_rhyme_detective_story.py --asp
    python storyworlds/worlds/gpt-5.4/trapeze_quest_rhyme_detective_story.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "coach_f"}
        male = {"boy", "father", "man", "coach_m"}
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
            "coach_f": "coach",
            "coach_m": "coach",
        }.get(self.type, self.type)


@dataclass
class MissingItem:
    id: str
    label: str
    phrase: str
    use_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HidePlace:
    id: str
    label: str
    phrase: str
    height: str
    scene: str
    found_text: str
    glitter_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    answer: str
    line1: str
    line2: str
    rhyme_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Retrieval:
    id: str
    label: str
    reaches_high: bool
    text: str
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


def _r_worry(world: World) -> list[str]:
    token = world.get("token")
    if token.meters["missing"] < THRESHOLD:
        return []
    sig = ("worry", "token")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero = world.get("hero")
    helper = world.get("helper")
    coach = world.get("coach")
    hero.memes["concern"] += 1
    helper.memes["concern"] += 1
    coach.memes["concern"] += 1
    return []


def _r_confidence(world: World) -> list[str]:
    if world.get("hero").meters["case_progress"] < THRESHOLD:
        return []
    sig = ("confidence", "hero")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("hero").memes["confidence"] += 1
    world.get("helper").memes["hope"] += 1
    return []


def _r_relief(world: World) -> list[str]:
    token = world.get("token")
    if token.meters["found"] < THRESHOLD:
        return []
    sig = ("relief", "found")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for eid in ("hero", "helper", "coach"):
        world.get(eid).memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="worry", tag="emotion", apply=_r_worry),
    Rule(name="confidence", tag="emotion", apply=_r_confidence),
    Rule(name="relief", tag="emotion", apply=_r_relief),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def clue_matches_place(clue: Clue, place: HidePlace) -> bool:
    return clue.answer == place.id


def retrieval_works(method: Retrieval, place: HidePlace) -> bool:
    if place.height == "low":
        return True
    return method.reaches_high


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for item_id in ITEMS:
        for clue_id, clue in CLUES.items():
            for method_id, method in RETRIEVALS.items():
                place = PLACES[clue.answer]
                if clue_matches_place(clue, place) and retrieval_works(method, place):
                    out.append((item_id, clue_id, method_id))
    return out


def predict_case(item: MissingItem, clue: Clue, method: Retrieval) -> dict:
    place = PLACES[clue.answer]
    return {
        "place": place.id,
        "height": place.height,
        "solved": clue_matches_place(clue, place) and retrieval_works(method, place),
        "needs_help": place.height == "high",
    }


def introduce(world: World, hero: Entity, helper: Entity, coach: Entity, item: MissingItem) -> None:
    token = world.get("token")
    token.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"On the morning of the little circus show, {hero.id} walked into the practice tent with {helper.id} and noticed that the trapeze ropes hung still, as if they were waiting for a secret."
    )
    world.say(
        f"{coach.label_word.capitalize()} clapped once and then looked worried. {item.phrase.capitalize()} was missing, and without it the trapeze turn could not begin. It was the small sign that told everyone who was ready to fly."
    )


def appoint_detective(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["curiosity"] += 1
    helper.memes["trust"] += 1
    world.say(
        f'{hero.id} straightened up at once. "This is a case," {hero.pronoun()} whispered. {helper.id} came closer, ready to be the best assistant a detective could have.'
    )


def discover_clue(world: World, hero: Entity, helper: Entity, clue: Clue) -> None:
    note = world.get("note")
    note.meters["noticed"] += 1
    world.say(
        f"Near the chalk bucket, {helper.id} found a folded paper with two careful lines on it."
    )
    world.say(f'"{clue.line1}"')
    world.say(f'"{clue.line2}"')
    world.say(
        f"The words made {hero.id}'s eyes shine. It was a rhyme, and in a detective case a rhyme could be as useful as a footprint."
    )


def inspect_path(world: World, hero: Entity, helper: Entity, place: HidePlace) -> None:
    hero.meters["case_progress"] += 1
    world.get("note").meters["understood"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} tapped a finger against {hero.pronoun("possessive")} chin. "The rhyme points to {place.phrase}," {hero.pronoun()} said.'
    )
    world.say(
        f"They crossed the tent slowly, looking for anything that matched the clue. On the way, they noticed {place.glitter_hint}, which made the guess feel stronger."
    )


def reach_low(world: World, hero: Entity, place: HidePlace, item: MissingItem, method: Retrieval) -> None:
    token = world.get("token")
    token.meters["found"] += 1
    token.meters["returned"] += 1
    token.meters["safe"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{place.found_text} {hero.id} {method.text} and lifted out {item.phrase}."
    )


def call_for_high_help(world: World, hero: Entity, helper: Entity, coach: Entity,
                       place: HidePlace, item: MissingItem, method: Retrieval) -> None:
    token = world.get("token")
    hero.memes["care"] += 1
    helper.memes["care"] += 1
    world.say(
        f"{place.found_text} It was too high for little hands, and {hero.id} did not try to scramble up near the trapeze."
    )
    world.say(
        f'"A good detective solves the case the safe way," {hero.id} said. {coach.label_word.capitalize()} nodded, brought {method.label}, and {method.text}.'
    )
    token.meters["found"] += 1
    token.meters["returned"] += 1
    token.meters["safe"] += 1
    propagate(world, narrate=False)
    world.say(f"Soon {item.phrase} was back in {coach.label_word}'s hands.")


def celebrate(world: World, hero: Entity, helper: Entity, coach: Entity, item: MissingItem) -> None:
    hero.memes["pride"] += 1
    helper.memes["joy"] += 1
    coach.memes["gratitude"] += 1
    world.say(
        f'{coach.label_word.capitalize()} smiled so wide that the whole tent seemed brighter. "{item.label.capitalize()} is back, and the case is closed," {coach.pronoun()} said.'
    )
    world.say(
        f"{hero.id} and {helper.id} stood by the mat while the trapeze finally began to swing. Above them, the bar traced a clean silver arc, and the missing {item.label} gleamed where it belonged."
    )


def tell(item: MissingItem, clue: Clue, method: Retrieval,
         hero_name: str = "Nora", hero_gender: str = "girl",
         helper_name: str = "Ben", helper_gender: str = "boy",
         coach_type: str = "coach_f") -> World:
    place = PLACES[clue.answer]
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        traits=["observant", "calm"],
        tags={"detective"},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        traits=["loyal", "bright"],
        tags={"assistant"},
    ))
    coach = world.add(Entity(
        id="Coach",
        kind="character",
        type=coach_type,
        role="coach",
        label="the coach",
        tags={"adult"},
    ))
    token = world.add(Entity(
        id="token",
        kind="thing",
        type="token",
        label=item.label,
        phrase=item.phrase,
        tags=set(item.tags),
    ))
    note = world.add(Entity(
        id="note",
        kind="thing",
        type="note",
        label="note",
        phrase="the folded note",
        tags={"rhyme", "clue"},
    ))
    hide = world.add(Entity(
        id="place",
        kind="thing",
        type="place",
        label=place.label,
        phrase=place.phrase,
        attrs={"height": place.height},
        tags=set(place.tags),
    ))

    introduce(world, hero, helper, coach, item)
    appoint_detective(world, hero, helper)

    world.para()
    discover_clue(world, hero, helper, clue)
    inspect_path(world, hero, helper, place)

    world.para()
    if place.height == "low":
        reach_low(world, hero, place, item, method)
    else:
        call_for_high_help(world, hero, helper, coach, place, item, method)

    world.para()
    celebrate(world, hero, helper, coach, item)

    world.facts.update(
        hero=hero,
        helper=helper,
        coach=coach,
        item=item,
        clue=clue,
        place_cfg=place,
        retrieval=method,
        solved=token.meters["found"] >= THRESHOLD,
        safe=token.meters["safe"] >= THRESHOLD,
        high=place.height == "high",
    )
    return world


ITEMS = {
    "star_pin": MissingItem(
        id="star_pin",
        label="star pin",
        phrase="the little silver star pin",
        use_text="It clipped to the flyer's costume before the trapeze turn.",
        tags={"star", "costume"},
    ),
    "blue_ribbon": MissingItem(
        id="blue_ribbon",
        label="blue ribbon",
        phrase="the blue ribbon of the trapeze team",
        use_text="It was tied on before the trapeze turn to show who practiced next.",
        tags={"ribbon", "costume"},
    ),
    "bell_charm": MissingItem(
        id="bell_charm",
        label="bell charm",
        phrase="the tiny bell charm for the show sash",
        use_text="It tinkled when the trapeze turn began.",
        tags={"bell", "costume"},
    ),
}

PLACES = {
    "drum": HidePlace(
        id="drum",
        label="drum",
        phrase="the red drum by the ring",
        height="low",
        scene="by the ring",
        found_text="Inside the red drum, under a curl of shiny paper, something winked.",
        glitter_hint="a few silver sparkles beside the red drum",
        tags={"drum", "ring"},
    ),
    "trunk": HidePlace(
        id="trunk",
        label="trunk",
        phrase="the costume trunk near the curtain",
        height="low",
        scene="near the curtain",
        found_text="When they lifted the lid of the costume trunk, there it was between two feathery capes.",
        glitter_hint="a trail of blue thread leading toward the costume trunk",
        tags={"trunk", "costume"},
    ),
    "perch": HidePlace(
        id="perch",
        label="high perch",
        phrase="the high perch above the trapeze net",
        height="high",
        scene="above the net",
        found_text="High above the net, on a narrow perch near the trapeze rig, the missing thing glimmered in a sun stripe.",
        glitter_hint="a bright speck far above the net where only grown-ups should reach",
        tags={"trapeze", "high"},
    ),
}

CLUES = {
    "ring_drum": Clue(
        id="ring_drum",
        answer="drum",
        line1="Look by the ring for a round red drum.",
        line2="Tap-tap near the drum, and the missing piece may come.",
        rhyme_word="drum",
        tags={"rhyme", "drum"},
    ),
    "cape_trunk": Clue(
        id="cape_trunk",
        answer="trunk",
        line1="Where capes are hung and costumes clunk,",
        line2="peek with care inside the trunk.",
        rhyme_word="trunk",
        tags={"rhyme", "trunk"},
    ),
    "net_perch": Clue(
        id="net_perch",
        answer="perch",
        line1="If flyers search above the net,",
        line2="look to the perch where bright things set.",
        rhyme_word="perch",
        tags={"rhyme", "trapeze"},
    ),
}

RETRIEVALS = {
    "reach": Retrieval(
        id="reach",
        label="careful hands",
        reaches_high=False,
        text="used careful hands",
        qa_text="reached in carefully and took it out",
        tags={"reach"},
    ),
    "coach_ladder": Retrieval(
        id="coach_ladder",
        label="the coach's ladder",
        reaches_high=True,
        text="used the coach's ladder to bring it down safely",
        qa_text="asked the coach to use a ladder and bring it down safely",
        tags={"ladder", "adult_help"},
    ),
}


GIRL_NAMES = ["Nora", "Mia", "Lily", "Ava", "Zoe", "Ella", "Ruby", "Tess"]
BOY_NAMES = ["Ben", "Max", "Leo", "Finn", "Theo", "Sam", "Eli", "Jack"]


@dataclass
class StoryParams:
    item: str
    clue: str
    retrieval: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    coach_type: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "trapeze": [
        (
            "What is a trapeze?",
            "A trapeze is a bar hanging from strong ropes. A performer can hold it and swing high in the air."
        )
    ],
    "rhyme": [
        (
            "What is a rhyme clue?",
            "A rhyme clue is a hint that uses words with matching sounds. It can help you remember where to look."
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective notices clues and asks what they mean. Then the detective uses those clues to solve a mystery."
        )
    ],
    "ladder": [
        (
            "Why should a grown-up use a ladder for high things?",
            "A ladder can help reach high places, but it must be used carefully. A grown-up should handle it so children stay safe on the ground."
        )
    ],
    "costume": [
        (
            "Why do performers keep costumes and show things together?",
            "Keeping show things near costumes helps everyone find what they need before a performance. It makes getting ready quicker and tidier."
        )
    ],
    "drum": [
        (
            "What is a drum?",
            "A drum is a round instrument you tap to make a beat. In a circus tent, it can help make a show feel exciting."
        )
    ],
}
KNOWLEDGE_ORDER = ["trapeze", "detective", "rhyme", "ladder", "costume", "drum"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    item = f["item"]
    clue = f["clue"]
    place = f["place_cfg"]
    return [
        'Write a short detective story for a 3-to-5-year-old that includes the word "trapeze" and uses a rhyming clue in a quest to find something missing.',
        f"Tell a gentle mystery where {hero.id} and {helper.id} solve the case of a missing {item.label} before trapeze practice can begin.",
        f'Write a child-facing quest story in detective style where the rhyme "{clue.line2}" helps lead the children to {place.phrase}.',
    ]


def pair_noun(hero: Entity, helper: Entity) -> str:
    if hero.type == "girl" and helper.type == "girl":
        return "two young detectives"
    if hero.type == "boy" and helper.type == "boy":
        return "two young detectives"
    return "two young detectives"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    coach = f["coach"]
    item = f["item"]
    clue = f["clue"]
    place = f["place_cfg"]
    retrieval = f["retrieval"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(hero, helper)}, {hero.id} and {helper.id}, and their coach in the circus tent. They work together to solve a small mystery before the trapeze turn can begin."
        ),
        (
            f"What was missing?",
            f"The missing thing was {item.phrase}. It mattered because {item.use_text}"
        ),
        (
            "What clue did they find?",
            f"They found a folded note with a rhyme on it. The rhyme said, \"{clue.line1}\" and \"{clue.line2}\" and pointed them toward {place.phrase}."
        ),
        (
            f"How did {hero.id} solve the case?",
            f"{hero.id} listened to the rhyme, matched it to the right place, and then checked for small signs that the clue was true. The glitter and threads they noticed made the guess feel like careful detective work, not just luck."
        ),
    ]
    if place.height == "high":
        out.append(
            (
                f"Why did {hero.id} ask for help instead of climbing up?",
                f"{hero.id} saw that the missing {item.label} was high near the trapeze rig. A good detective also stays safe, so {hero.pronoun()} asked {coach.label_word} to help with a ladder instead of scrambling up."
            )
        )
        out.append(
            (
                f"How did they get the {item.label} down?",
                f"They {retrieval.qa_text}. That solved the mystery and kept the children safe on the ground."
            )
        )
    else:
        out.append(
            (
                f"Where did they find the {item.label}?",
                f"They found it at {place.phrase}. The rhyme led them there, and then {hero.id} {retrieval.qa_text}."
            )
        )
    out.append(
        (
            "How did the story end?",
            f"It ended with the missing {item.label} returned and the trapeze finally swinging again. The ending image shows the mystery is over because the show can begin."
        )
    )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"trapeze", "detective", "rhyme"}
    place = world.facts["place_cfg"]
    if place.id == "perch":
        tags.add("ladder")
    if place.id == "trunk":
        tags.add("costume")
    if place.id == "drum":
        tags.add("drum")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        item="star_pin",
        clue="ring_drum",
        retrieval="reach",
        hero_name="Nora",
        hero_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        coach_type="coach_f",
    ),
    StoryParams(
        item="blue_ribbon",
        clue="cape_trunk",
        retrieval="reach",
        hero_name="Leo",
        hero_gender="boy",
        helper_name="Mia",
        helper_gender="girl",
        coach_type="coach_m",
    ),
    StoryParams(
        item="bell_charm",
        clue="net_perch",
        retrieval="coach_ladder",
        hero_name="Ruby",
        hero_gender="girl",
        helper_name="Finn",
        helper_gender="boy",
        coach_type="coach_f",
    ),
]


def explain_rejection(clue: Clue, method: Retrieval) -> str:
    place = PLACES[clue.answer]
    if place.height == "high" and not method.reaches_high:
        return (
            f"(No story: the rhyme points to {place.phrase}, which is high near the trapeze. "
            f"The method '{method.id}' cannot safely reach that place; use a ladder-and-grown-up method instead.)"
        )
    return "(No story: this clue and retrieval method do not make a sensible detective case.)"


ASP_RULES = r"""
place_of(C, P) :- clue(C), clue_answer(C, P).
works(R, P) :- retrieval(R), place(P), height(P, low).
works(R, P) :- retrieval(R), place(P), height(P, high), reaches_high(R).

valid(I, C, R) :- item(I), clue(C), retrieval(R), place_of(C, P), works(R, P).

solved :- chosen_clue(C), chosen_retrieval(R), place_of(C, P), works(R, P).
outcome(solved) :- solved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for item_id in ITEMS:
        lines.append(asp.fact("item", item_id))
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("height", place_id, place.height))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("clue_answer", clue_id, clue.answer))
    for retrieval_id, retrieval in RETRIEVALS.items():
        lines.append(asp.fact("retrieval", retrieval_id))
        if retrieval.reaches_high:
            lines.append(asp.fact("reaches_high", retrieval_id))
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
            asp.fact("chosen_clue", params.clue),
            asp.fact("chosen_retrieval", params.retrieval),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    clue = CLUES[params.clue]
    method = RETRIEVALS[params.retrieval]
    return "solved" if retrieval_works(method, PLACES[clue.answer]) else "?"


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("(Smoke test failed: generated story was empty.)")
    emit(sample, trace=False, qa=False, header="")


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatch = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        smoke_test()
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover - defensive verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tiny detective quest with rhyme clues in a trapeze tent."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--retrieval", choices=RETRIEVALS)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--coach", choices=["coach_f", "coach_m"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.clue and args.retrieval:
        clue = CLUES[args.clue]
        retrieval = RETRIEVALS[args.retrieval]
        if not retrieval_works(retrieval, PLACES[clue.answer]):
            raise StoryError(explain_rejection(clue, retrieval))

    combos = [
        combo
        for combo in valid_combos()
        if (args.item is None or combo[0] == args.item)
        and (args.clue is None or combo[1] == args.clue)
        and (args.retrieval is None or combo[2] == args.retrieval)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item_id, clue_id, retrieval_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or pick_name(rng, hero_gender)
    helper_name = args.helper_name or pick_name(rng, helper_gender, avoid=hero_name)
    coach_type = args.coach or rng.choice(["coach_f", "coach_m"])
    return StoryParams(
        item=item_id,
        clue=clue_id,
        retrieval=retrieval_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        coach_type=coach_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.item not in ITEMS:
        raise StoryError(f"(Invalid item: {params.item})")
    if params.clue not in CLUES:
        raise StoryError(f"(Invalid clue: {params.clue})")
    if params.retrieval not in RETRIEVALS:
        raise StoryError(f"(Invalid retrieval method: {params.retrieval})")
    clue = CLUES[params.clue]
    retrieval = RETRIEVALS[params.retrieval]
    if not retrieval_works(retrieval, PLACES[clue.answer]):
        raise StoryError(explain_rejection(clue, retrieval))

    world = tell(
        item=ITEMS[params.item],
        clue=clue,
        method=retrieval,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        coach_type=params.coach_type,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (item, clue, retrieval) combos:\n")
        for item_id, clue_id, retrieval_id in combos:
            place_id = CLUES[clue_id].answer
            print(f"  {item_id:11} {clue_id:10} {retrieval_id:12} -> {place_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} and {p.helper_name}: {p.item} / {p.clue} / {p.retrieval}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
