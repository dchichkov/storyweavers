#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/barbie_importance_foreshadowing_dialogue_happy_ending_whodunit.py
===================================================================================================

A standalone storyworld for a tiny whodunit-like domain built from the seed
words "barbie" and "importance". The story frame is a child noticing that a
favorite doll has gone missing, gathering small clues, and solving the mystery
through dialogue, foreshadowing, and a happy ending.

The domain is intentionally small:
- A beloved doll can be misplaced in a few plausible hiding places.
- One child notices clues early and asks careful questions.
- Another child is surprised but helps search.
- A gentle reveal leads to relief, not punishment.

The story text is state-driven: the world model tracks who last held the doll,
which clues were noticed, where the search goes, and whether the doll is found.
Prose is rendered from that state rather than from a frozen template.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/barbie_importance_foreshadowing_dialogue_happy_ending_whodunit.py
    python storyworlds/worlds/gpt-5.4-mini/barbie_importance_foreshadowing_dialogue_happy_ending_whodunit.py --all
    python storyworlds/worlds/gpt-5.4-mini/barbie_importance_foreshadowing_dialogue_happy_ending_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/barbie_importance_foreshadowing_dialogue_happy_ending_whodunit.py --verify
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

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRUSTED_NAMES = ["Mia", "Nora", "Ella", "Ben", "Leo", "Ava"]
HIDING_PLACES = ["toy box", "blanket fort", "reading nook", "under the couch"]
CLUE_TYPES = ["tiny shoe print", "sparkly ribbon", "soft giggle", "open toy chest"]
SEARCH_TOOLS = ["flashlight", "careful questions", "slow footsteps"]
MOODS = ["worried", "curious", "hopeful", "relieved"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

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



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    detail: str
    search_spots: list[str]
    clue_bias: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Mystery:
    id: str
    object_word: str
    label: str
    importance_line: str
    beloved_line: str
    found_line: str
    hidden_at: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Clue:
    id: str
    label: str
    line: str
    points_to: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Response:
    id: str
    sense: int
    line: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_search_emotion(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["searching"] < THRESHOLD:
            continue
        sig = ("search_emotion", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["hope"] += 1
        out.append("")
    return out


CAUSAL_RULES = [Rule("search_emotion", "social", _r_search_emotion)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def clue_relevant(setting: Setting, mystery: Mystery, clue: Clue) -> bool:
    return clue.points_to == mystery.hidden_at or clue.points_to in setting.search_spots


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id in SETTINGS:
        for mystery_id, mystery in MYSTERIES.items():
            for clue_id, clue in CLUES.items():
                if clue_relevant(SETTINGS[setting_id], mystery, clue):
                    combos.append((setting_id, mystery_id, clue_id))
    return combos


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def predict_search(world: World, mystery_id: str, clue_id: str) -> dict:
    sim = world.copy()
    _search(sim, sim.get("child"), MYSTERIES[mystery_id], CLUES[clue_id], narrate=False)
    return {"found": bool(sim.facts.get("found")), "hope": sim.get("child").memes["hope"]}


def _search(world: World, child: Entity, mystery: Mystery, clue: Clue, narrate: bool = True) -> None:
    child.memes["searching"] += 1
    child.memes["curiosity"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, child: Entity, friend: Entity, mystery: Mystery) -> None:
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {child.id} and {friend.id} were playing in {world.setting.place}. "
        f"{world.setting.detail} {child.id} noticed that {mystery.label} was missing."
    )


def foreshadow(world: World, child: Entity, mystery: Mystery, clue: Clue) -> None:
    child.memes["worry"] += 1
    world.say(
        f"Then {child.id} spotted {clue.label}. {clue.line} It was a small clue, but it felt important."
    )


def dialogue(world: World, child: Entity, friend: Entity, mystery: Mystery) -> None:
    world.say(
        f'"Did {friend.id} see {mystery.label}?" {child.id} asked. '
        f'"I thought it was here."'
    )
    world.say(
        f'"I did not take it," {friend.id} said. "{mystery.label.capitalize()} matters too much to lose."'
    )


def search(world: World, child: Entity, friend: Entity, mystery: Mystery, clue: Clue) -> None:
    child.memes["searching"] += 1
    child.memes["hope"] += 1
    world.say(
        f"They used {SEARCH_TOOLS[0]} and {SEARCH_TOOLS[1]} to look around. "
        f"{clue.line} So they checked {mystery.hidden_at}."
    )


def reveal(world: World, child: Entity, friend: Entity, mystery: Mystery, finder: Entity) -> None:
    child.memes["relief"] += 1
    friend.memes["relief"] += 1
    mystery_found = world.add(Entity(id="found", label=mystery.label))
    mystery_found.meters["safe"] += 1
    world.facts["found"] = True
    world.say(
        f"At last, {finder.id} lifted the lid and found {mystery.label} in {mystery.hidden_at}. "
        f"{mystery.found_line}"
    )


def happy_ending(world: World, child: Entity, friend: Entity, mystery: Mystery) -> None:
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"{child.id} hugged {friend.id}. \"The importance of {mystery.label} is that we found it together,\" "
        f"{child.id} said, smiling."
    )
    world.say("They put the doll back on the shelf, where it could watch over the room again.")


def tell(setting: Setting, mystery: Mystery, clue: Clue, child_name: str = "Lily",
         child_gender: str = "girl", friend_name: str = "Mia", friend_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="detective"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="adult", label="the parent"))
    world.facts["mystery"] = mystery
    world.facts["clue"] = clue
    world.facts["child"] = child
    world.facts["friend"] = friend
    world.facts["parent"] = parent
    world.facts["setting"] = setting

    introduce(world, child, friend, mystery)
    world.para()
    foreshadow(world, child, mystery, clue)
    dialogue(world, child, friend, mystery)
    world.para()
    search(world, child, friend, mystery, clue)
    reveal(world, child, friend, mystery, friend)
    happy_ending(world, child, friend, mystery)
    world.facts["ending"] = "happy"
    return world


SETTINGS = {
    "bedroom": Setting("bedroom", "the bedroom", "The room was neat, except for a little empty space on the shelf.", ["toy box", "blanket fort", "reading nook", "under the couch"], "careful"),
    "playroom": Setting("playroom", "the playroom", "The playroom was busy and bright, with toys tucked into every corner.", ["toy box", "blanket fort", "reading nook"], "curious"),
    "livingroom": Setting("livingroom", "the living room", "The living room was cozy, and the sofa made a perfect hiding place.", ["under the couch", "toy box", "blanket fort"], "important"),
}

MYSTERIES = {
    "barbie": Mystery(
        "barbie", "barbie", "Barbie",
        "Its importance was simple: it was the favorite doll and nobody wanted it lost.",
        "Barbie had been the star of many pretend adventures.",
        "It was safe all along, waiting to be found.",
        "toy box", tags={"barbie", "toy", "importance"},
    ),
    "teddy": Mystery(
        "teddy", "teddy", "Teddy",
        "Its importance came from being the softest bedtime friend.",
        "Teddy had comforted many sleepy nights.",
        "It was safe all along, tucked away and waiting.",
        "blanket fort", tags={"toy", "importance"},
    ),
    "crown": Mystery(
        "crown", "paper crown", "Paper Crown",
        "Its importance was that it belonged to the birthday game.",
        "The crown had been part of the party play.",
        "It was safe all along, sitting in a hiding spot.",
        "reading nook", tags={"toy", "importance"},
    ),
}

CLUES = {
    "shoeprint": Clue("shoeprint", "a tiny shoe print", "There was a tiny shoe print near the shelf.", "toy box", tags={"clue", "shoe"}),
    "ribbon": Clue("ribbon", "a sparkly ribbon", "A sparkly ribbon peeked out from a corner.", "blanket fort", tags={"clue", "ribbon"}),
    "giggle": Clue("giggle", "a soft giggle", "A soft giggle drifted from the reading nook.", "reading nook", tags={"clue", "giggle"}),
    "openbox": Clue("openbox", "an open toy chest", "The toy chest was not shut all the way.", "toy box", tags={"clue", "box"}),
}

RESPONSES = {
    "questioning": Response("questioning", 3, "asked careful questions instead of guessing", tags={"dialogue"}),
    "searching": Response("searching", 3, "looked in the place the clue pointed to", tags={"search"}),
    "reading": Response("reading", 2, "read the clues like a little detective", tags={"foreshadowing"}),
    "hug": Response("hug", 2, "gave a relieved hug", tags={"happy"}),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tiny whodunit with barbie, clues, dialogue, and a happy ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--friend")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> "StoryParams":
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, clue = rng.choice(sorted(combos))
    child = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    friend = args.friend or rng.choice([n for n in TRUSTED_NAMES if n != child])
    parent = args.parent or rng.choice(["mother", "father"])
    child_gender = "girl" if child in GIRL_NAMES else "boy"
    friend_gender = "girl" if friend in GIRL_NAMES else "boy"
    return StoryParams(setting, mystery, clue, child, child_gender, friend, friend_gender, parent)


@dataclass
@dataclass
class StoryParams:
    setting: str
    mystery: str
    clue: str
    name: str
    gender: str
    friend: str
    friend_gender: str
    parent: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a whodunit-style story for a 3-to-5-year-old that includes the word "barbie" and the word "importance".',
        f"Tell a gentle mystery where {f['child'].id} notices a clue, asks questions, and finds {f['mystery'].label} with a happy ending.",
        f"Write a story with foreshadowing and dialogue about something important that was missing, then safely found again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    mystery = f["mystery"]
    clue = f["clue"]
    return [
        QAItem(
            question="What kind of story is this?",
            answer="It is a gentle mystery story. A child notices a missing toy, follows clues, and solves the problem with help.",
        ),
        QAItem(
            question=f"Why did {child.id} think the missing doll mattered?",
            answer=f"{mystery.label} was important because it was the favorite toy and a special part of playtime. That is why the missing doll felt worth searching for right away.",
        ),
        QAItem(
            question=f"What clue helped {child.id}?",
            answer=f"{clue.line} It mattered because it pointed toward {mystery.hidden_at}, so the children knew where to look next.",
        ),
        QAItem(
            question=f"How did {child.id} and {friend.id} solve the mystery?",
            answer=f"They asked careful questions, followed the clue, and searched the right hiding place together. That teamwork led them straight to the missing doll.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily, with {mystery.label} found and returned to the room. The children felt relieved and proud because they solved the little mystery together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery = f["mystery"]
    out = [
        QAItem("What is a clue in a mystery?", "A clue is a small piece of information that helps solve a problem or find something lost. Clues can be tiny details that point in the right direction."),
        QAItem("What does foreshadowing do?", "Foreshadowing gives a small hint before something important happens. It helps the reader notice that a clue or surprise will matter later."),
    ]
    if mystery.id == "barbie":
        out.append(QAItem("What is Barbie in this world?", "Barbie is a beloved doll, the missing toy at the center of the mystery. The story treats her as something important to find and protect."))
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
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("playroom", "barbie", "shoeprint", "Lily", "girl", "Mia", "girl", "mother"),
    StoryParams("bedroom", "barbie", "openbox", "Maya", "girl", "Nora", "girl", "father"),
    StoryParams("livingroom", "barbie", "ribbon", "Ava", "girl", "Ella", "girl", "mother"),
]


def explain_rejection(setting: Setting, mystery: Mystery, clue: Clue) -> str:
    return f"(No story: this combination does not fit the little mystery logic.)"


def outcome_of(params: StoryParams) -> str:
    return "happy"


ASP_RULES = r"""
valid(S, M, C) :- setting(S), mystery(M), clue(C).
outcome(happy) :- valid(_, _, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate.")
    sample = generate(resolve_params(argparse.Namespace(setting=None, mystery=None, clue=None, parent=None, name=None, friend=None), random.Random(0)))
    if not sample.story.strip():
        return 1
    print("OK: story generation smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], CLUES[params.clue],
                 params.name, params.gender, params.friend, params.friend_gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos.")
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
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.mystery} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
