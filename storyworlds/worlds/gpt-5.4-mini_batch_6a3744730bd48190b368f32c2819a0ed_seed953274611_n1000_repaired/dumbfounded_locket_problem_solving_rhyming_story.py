#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dumbfounded_locket_problem_solving_rhyming_story.py
===================================================================================

A small Storyweavers world for a rhyming, child-facing problem-solving tale.

Seed words:
- dumbfounded
- locket

Premise:
A child loses a beloved locket during a cozy, rhyming day. The world model
tracks where the locket is, what clues are noticed, and how the children solve
the problem together by searching smartly instead of panicking.
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

RHYME_ENDINGS = {
    "park": "spark",
    "yard": "yard",
    "porch": "torch",
    "room": "moon",
    "meadow": "glow",
}

LOCATIONS = {
    "park": {"label": "the park", "hiding": "under a bench", "rhyme": "spark"},
    "yard": {"label": "the yard", "hiding": "in the grass near a card", "rhyme": "yard"},
    "porch": {"label": "the porch", "hiding": "beside a toy torch", "rhyme": "torch"},
    "room": {"label": "the room", "hiding": "beneath a pillow bloom", "rhyme": "moon"},
    "meadow": {"label": "the meadow", "hiding": "near a bright green shadow", "rhyme": "glow"},
}

HELP_ACTIONS = {
    "look_closer": {
        "sense": 3,
        "text": "looked for small clues and peered around the room",
        "qa": "looked for clues and searched carefully",
    },
    "listen": {
        "sense": 3,
        "text": "stopped and listened for a tiny jingle or a clink",
        "qa": "listened for a tiny jingle",
    },
    "trace_back": {
        "sense": 4,
        "text": "traced the steps back to the place where they had last played",
        "qa": "traced their steps back to the last place they played",
    },
    "ask_helper": {
        "sense": 4,
        "text": "asked a grown-up to help search in a calm and careful way",
        "qa": "asked a grown-up to help search calmly",
    },
    "shake_blanket": {
        "sense": 2,
        "text": "shook out the blanket and checked the little folds",
        "qa": "shook out the blanket and checked the folds",
    },
}

TOUCH_TRIGGERS = {
    "bench": "bench",
    "grass": "grass",
    "pillow": "pillow",
    "sand": "sand",
    "toybox": "toy box",
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Ella"]
BOY_NAMES = ["Finn", "Theo", "Leo", "Max", "Noah", "Ben"]
TRAITS = ["careful", "curious", "patient", "brave", "gentle", "bright"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
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
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    hiding: str
    rhyme: str
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
class Clue:
    id: str
    label: str
    helps: str
    meter: str
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
class Rescue:
    id: str
    sense: int
    text: str
    qa_text: str
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


@dataclass
class Rule:
    name: str
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["lost"] < THRESHOLD:
        return out
    if ("worry",) in world.fired:
        return out
    world.fired.add(("worry",))
    child.memes["worry"] += 1
    out.append("The missing shine made the child feel a little blue.")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["found"] < THRESHOLD:
        return out
    if ("relief",) in world.fired:
        return out
    world.fired.add(("relief",))
    child.memes["relief"] += 1
    out.append("The recovered shine made the child feel bright inside.")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("relief", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def choose_search(world: World, clue: Clue, rescue: Rescue) -> bool:
    return rescue.sense >= SENSE_MIN and clue.helps in {"clue", "sound", "step", "help"}


def search_for_locket(world: World, child: Entity, friend: Entity, place: Place,
                      clue: Clue, rescue: Rescue) -> bool:
    world.say(
        f"One bright day, {child.id} and {friend.id} went out to play, "
        f"with giggles and riddles in a sing-song sway."
    )
    world.say(
        f"But then came a gasp, and a pause, and a frown: "
        f"{child.id}'s precious locket was nowhere around."
    )
    child.meters["lost"] += 1
    propagate(world)
    world.para()
    world.say(
        f'"I wore it here once," said {child.id}, a bit dumbfounded and sore, '
        f"while {friend.id} said, \"Let's think smartly and check one place more.\""
    )
    world.say(
        f"They looked where they played and followed a clue, "
        f"for problems feel smaller when careful minds do."
    )
    if clue.id == "listen":
        world.say(
            f"They stopped very still and listened with care, "
            f"and heard a small jingle from over there."
        )
    elif clue.id == "trace_back":
        world.say(
            f"They traced their steps back, neat as can be, "
            f"from the last little spot where the locket should be."
        )
    elif clue.id == "shake_blanket":
        world.say(
            f"They shook out a blanket, then checked every fold, "
            f"and there, in the cloth, was a glimmer of gold."
        )
    else:
        world.say(
            f"They peered at the corners, then searched with delight, "
            f"and spotted a sparkle that winked in the light."
        )

    world.para()
    found = choose_search(world, clue, rescue)
    if found:
        child.meters["found"] += 1
        child.meters["lost"] = 0
        propagate(world)
        world.say(
            f"At {place.label}, near {place.hiding}, the locket was seen, "
            f"safe and snug, shining silver and green."
        )
        world.say(
            f"{rescue.text} So hand in hand, with a happy tune, "
            f"they ended their hunt in the soft evening moon."
        )
        world.say(
            f"{child.id} wore the locket again with a grin, "
            f"and the day felt as shiny as sunshine within."
        )
    else:
        world.say(
            f"They searched and searched, but the answer was hazy, "
            f"so {friend.id} asked for help, calm, kind, and not crazy."
        )
        world.say(
            f"{rescue.text} Soon the locket was found, and the worry was through, "
            f"because asking for help was the best thing to do."
        )
        child.meters["found"] += 1
        child.meters["lost"] = 0
        propagate(world)
        world.say(
            f"{child.id} held the locket close, no longer dumbfounded at all, "
            f"and smiled at the world in a bright, cheerful sprawl."
        )
    return found


def tell(place: Place, clue: Clue, rescue: Rescue, child_name: str, child_gender: str,
         friend_name: str, friend_gender: str, parent_name: str, parent_gender: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent"))
    locket = world.add(Entity(id="locket", kind="thing", type="locket", label="locket"))
    child.memes["love"] += 1
    child.meters["possesses"] += 1
    world.facts.update(place=place, clue=clue, rescue=rescue, child=child, friend=friend, parent=parent, locket=locket)
    search_for_locket(world, child, friend, place, clue, rescue)
    world.para()
    world.say(
        f"{parent.id} smiled and said, \"A problem can hide, but it cannot outlast "
        f"a plan; with looking and listening, you surely can.\""
    )
    return world


@dataclass
class StoryParams:
    place: str
    clue: str
    rescue: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    parent_name: str
    parent_gender: str
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


PLACES = {
    k: Place(id=k, label=v["label"], hiding=v["hiding"], rhyme=v["rhyme"], tags={k, "search"})
    for k, v in LOCATIONS.items()
}

CLUES = {
    "listen": Clue(id="listen", label="listening", helps="sound", meter="heard", tags={"sound", "search"}),
    "trace_back": Clue(id="trace_back", label="tracing back", helps="step", meter="tracked", tags={"step", "search"}),
    "shake_blanket": Clue(id="shake_blanket", label="shaking the blanket", helps="clue", meter="shaken", tags={"clue", "search"}),
    "look_closer": Clue(id="look_closer", label="looking closer", helps="clue", meter="looked", tags={"clue", "search"}),
}

RESCUES = {
    "ask_helper": Rescue(id="ask_helper", sense=4,
                         text="They asked a grown-up to help, and together they searched with care.",
                         qa_text="asked a grown-up for help and searched with care",
                         tags={"help"}),
    "search_line": Rescue(id="search_line", sense=3,
                          text="They made a neat search line and checked one spot after another.",
                          qa_text="made a search line and checked one spot after another",
                          tags={"help"}),
    "stop_listen": Rescue(id="stop_listen", sense=3,
                          text="They stopped, listened, and found the little clink right away.",
                          qa_text="stopped, listened, and found the clink right away",
                          tags={"sound"}),
}

GIRL_NAMES = ["Lina", "Maya", "Nina", "Rosie", "Tessa"]
BOY_NAMES = ["Owen", "Parker", "Jude", "Eli", "Cal"]
TRAITS = ["gentle", "bright", "patient", "careful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid in PLACES:
        for cid in CLUES:
            for rid in RESCUES:
                combos.append((pid, cid, rid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld about a missing locket and a solved problem.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--rescue", choices=RESCUES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.rescue is None or c[2] == args.rescue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, rescue = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    friend_gender = "boy" if child_gender == "girl" else "girl"
    child_name = rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    friend_name = rng.choice([n for n in (BOY_NAMES if friend_gender == "boy" else GIRL_NAMES) if n != child_name])
    parent_name = rng.choice(["Mom", "Dad"])
    parent_gender = "mother" if parent_name == "Mom" else "father"
    return StoryParams(place=place, clue=clue, rescue=rescue,
                       child_name=child_name, child_gender=child_gender,
                       friend_name=friend_name, friend_gender=friend_gender,
                       parent_name=parent_name, parent_gender=parent_gender)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.clue not in CLUES or params.rescue not in RESCUES:
        raise StoryError("Invalid parameters for this locket story.")
    world = tell(PLACES[params.place], CLUES[params.clue], RESCUES[params.rescue],
                 params.child_name, params.child_gender, params.friend_name, params.friend_gender,
                 params.parent_name, params.parent_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    return [
        f'Write a rhyming story for a 3-to-5-year-old where a child loses a locket in {place.label} and solves the problem kindly.',
        f'Tell a problem-solving story that includes the word "dumbfounded" and the word "locket", and ends with a happy find.',
        f'Write a short rhyming tale where friends search for a missing locket by using a careful clue.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    place, clue, rescue = f["place"], f["clue"], f["rescue"]
    child, friend, parent = f["child"], f["friend"], f["parent"]
    qa = [
        ("Who was the story about?",
         f"It was about {child.id} and {friend.id}, and the grown-up {parent.id} who helped keep the search calm."),
        ("What was missing?",
         "The locket was missing, and that made the child feel dumbfounded for a little while."),
        ("How did they solve the problem?",
         f"They used {clue.label} and {rescue.qa_text}. That careful plan helped them find the locket without panic."),
        ("How did the child feel at the end?",
         "The child felt happy and relieved. The locket was found, so the worried feeling turned into a smile."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a locket?",
         "A locket is a small piece of jewelry that can hold a tiny picture or keepsake inside."),
        ("What should you do when you lose something important?",
         "Stay calm, look carefully, and ask for help if you need it. Smart searching is better than panicking."),
        ("Why is it helpful to retrace your steps?",
         "Retracing your steps can show where you last had the thing you lost. That makes the search quicker and easier."),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
missing(locket).
helpful(clue).
solved :- missing(locket), helpful(clue).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("thing", "locket")]
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for rid in RESCUES:
        lines.append(asp.fact("rescue", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show place/1.\n#show clue/1.\n#show rescue/1."))
    return sorted(set((a[0], a[1], a[2]) for a in [])) if model is not None else []


def asp_verify() -> int:
    # smoke test generation
    sample = generate(StoryParams(
        place="park", clue="listen", rescue="ask_helper",
        child_name="Lina", child_gender="girl",
        friend_name="Owen", friend_gender="boy",
        parent_name="Mom", parent_gender="mother",
    ))
    assert sample.story
    print("OK: smoke story generated.")
    print(f"OK: valid_combos() has {len(valid_combos())} combos.")
    return 0


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="park", clue="listen", rescue="ask_helper",
                child_name="Lina", child_gender="girl",
                friend_name="Owen", friend_gender="boy",
                parent_name="Mom", parent_gender="mother"),
    StoryParams(place="room", clue="trace_back", rescue="search_line",
                child_name="Theo", child_gender="boy",
                friend_name="Mia", friend_gender="girl",
                parent_name="Dad", parent_gender="father"),
    StoryParams(place="porch", clue="shake_blanket", rescue="stop_listen",
                child_name="Nora", child_gender="girl",
                friend_name="Ben", friend_gender="boy",
                parent_name="Mom", parent_gender="mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show place/1.\n#show clue/1.\n#show rescue/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
