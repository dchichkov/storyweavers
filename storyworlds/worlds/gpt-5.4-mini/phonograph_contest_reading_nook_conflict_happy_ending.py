#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/phonograph_contest_reading_nook_conflict_happy_ending.py
========================================================================================

A standalone storyworld for a tiny **mystery** set in a **reading nook**.

Seed premise:
- Words: phonograph, contest
- Setting: reading nook
- Features: Conflict, Happy Ending
- Style: Mystery

Core idea:
A child hosts a quiet mystery contest in a reading nook, but an old phonograph
starts making a strange sound and creates a conflict. The children investigate,
discover a simple cause, and end with a calm, happy solution that makes the nook
feel cozy and safe again.

The world is intentionally small and classical:
- typed entities with physical ``meters`` and emotional ``memes``
- state-driven causality
- a Python reasonableness gate plus an inline ASP twin
- three QA sets grounded in simulated world state
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "librarian"}
        male = {"boy", "father", "dad", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "librarian": "librarian"}.get(self.type, self.type)



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
    cozy: str
    dark_spot: str
    afford: set[str] = field(default_factory=set)

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
class ObjectThing:
    id: str
    label: str
    phrase: str
    type: str = "thing"
    uses: set[str] = field(default_factory=set)
    noisy: bool = False
    movable: bool = True
    fragile: bool = False

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
    power: int
    text: str
    fail: str
    qa_text: str

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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


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


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    needle = world.facts.get("needle")
    phonograph = world.facts.get("phonograph_ent")
    if not needle or not phonograph:
        return out
    if phonograph.meters["scratch"] < THRESHOLD:
        return out
    sig = ("noise", phonograph.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ch in world.characters():
        ch.memes["unease"] += 1
        ch.memes["curiosity"] += 1
    world.get("room").meters["mystery"] += 1
    out.append("__noise__")
    return out


CAUSAL_RULES = [Rule("noise", "social", _r_noise)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(s for s in items if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def hazard_at_risk(tool: ObjectThing, target: ObjectThing) -> bool:
    return tool.noisy and target.fragile


def mystery_level(room: Entity) -> bool:
    return room.memes["mystery"] >= THRESHOLD


def can_resolve(resp: Response, delay: int) -> bool:
    return resp.power >= 1 + delay


def _scrape_phonograph(world: World, phonograph: Entity) -> None:
    phonograph.meters["scratch"] += 1
    phonograph.meters["noise"] += 1
    propagate(world, narrate=False)


def setup(world: World, child: Entity, friend: Entity, setting: Setting) -> None:
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On a quiet afternoon, {child.id} and {friend.id} settled into {setting.place}. "
        f"{setting.cozy}"
    )
    world.say(
        f"They whispered about a little contest: who could solve the odd mystery in {setting.place} first."
    )


def hint(world: World, child: Entity, friend: Entity, clue: ObjectThing) -> None:
    world.say(
        f"Near {setting_label(world.setting)}, {clue.phrase} seemed out of place, like a clue waiting to be noticed."
    )
    world.say(
        f"{friend.id} leaned closer and listened. {friend.pronoun().capitalize()} said the strange sound was coming from somewhere nearby."
    )


def conflict(world: World, child: Entity, friend: Entity, phonograph: Entity, needle: ObjectThing) -> None:
    child.memes["determination"] += 1
    friend.memes["worry"] += 1
    world.say(
        f"{child.id} reached for the old phonograph, hoping the contest could begin with music."
    )
    world.say(
        f"But {friend.id} bit {friend.pronoun('possessive')} lip. \"Wait,\" {friend.id} said, \"that needle looks sharp, and the sound is getting stranger.\""
    )


def accident(world: World, phonograph: Entity, needle: ObjectThing) -> None:
    _scrape_phonograph(world, phonograph)
    world.say(
        f"Scritch! The phonograph needle tapped the record the wrong way, and a scratchy sound spilled through the nook."
    )


def reveal(world: World, child: Entity, friend: Entity, phonograph: Entity, clue: ObjectThing) -> None:
    world.say(
        f"{child.id} and {friend.id} followed the sound like detectives."
    )
    world.say(
        f"They found {clue.phrase} near the phonograph, and the problem was simple: the needle had slipped off its spot."
    )


def fix(world: World, child: Entity, friend: Entity, phonograph: Entity, resp: Response) -> None:
    phonograph.meters["scratch"] = 0
    phonograph.meters["noise"] = 0
    child.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.get("room").meters["mystery"] = 0
    world.say(
        f"A careful grown-up came over, {resp.text}."
    )
    world.say(
        f"The sound faded at once, and the reading nook grew quiet again."
    )


def happy_end(world: World, child: Entity, friend: Entity, setting: Setting, resp: Response) -> None:
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"After that, the contest turned gentle and fun. The children took turns listening, guessing, and grinning at each clue."
    )
    world.say(
        f"By the end, {setting.place} felt cozy and calm, and even the old phonograph sounded ready for its next safe song."
    )


def setting_label(setting: Setting) -> str:
    return setting.place


def tell(setting: Setting, child_name: str = "Maya", child_type: str = "girl",
         friend_name: str = "Noah", friend_type: str = "boy",
         parent_type: str = "librarian", delay: int = 0,
         response: Response = None) -> World:
    world = World(setting)
    child = world.add(Entity(child_name, kind="character", type=child_type, role="child"))
    friend = world.add(Entity(friend_name, kind="character", type=friend_type, role="friend"))
    helper = world.add(Entity("Helper", kind="character", type=parent_type, label="the helper"))
    room = world.add(Entity("room", type="room", label=setting.place))
    phonograph = world.add(Entity("phonograph", type="phonograph", label="the phonograph"))
    needle = ObjectThing("needle", "needle", "a tiny metal needle", noisy=True, fragile=True)
    clue = ObjectThing("clue", "clue", "a small ribbon bookmark", movable=False)

    world.facts["phonograph_ent"] = phonograph
    world.facts["needle"] = needle
    world.facts["helper"] = helper
    world.facts["child"] = child
    world.facts["friend"] = friend
    world.facts["room"] = room
    world.facts["clue"] = clue
    world.facts["response"] = response
    world.facts["delay"] = delay

    setup(world, child, friend, setting)
    world.para()
    hint(world, child, friend, clue)
    conflict(world, child, friend, phonograph, needle)
    accident(world, phonograph, needle)
    world.para()
    reveal(world, child, friend, phonograph, clue)
    if response is None:
        response = best_response()
    fix(world, child, friend, phonograph, response)
    world.para()
    happy_end(world, child, friend, setting, response)

    world.facts["outcome"] = "happy"
    world.facts["mystery_resolved"] = True
    world.facts["noise_happened"] = True
    return world


SETTINGS = {
    "reading_nook": Setting(
        "reading_nook",
        "the reading nook",
        "Soft cushions made a nest beside the shelves, and a little lamp glowed over the books.",
        "the phonograph corner",
        afford={"listen", "investigate"},
    )
}

TOOLS = {
    "phonograph": ObjectThing("phonograph_tool", "phonograph", "an old phonograph", noisy=True, movable=True),
}

CLUES = {
    "needle": ObjectThing("needle", "needle", "a tiny needle", noisy=True, fragile=True),
    "bookmark": ObjectThing("bookmark", "bookmark", "a ribbon bookmark", movable=False),
}

RESPONSES = {
    "repair": Response(
        "repair",
        3,
        2,
        "checked the needle, lifted it back into place, and wound the phonograph gently",
        "tried to fix it, but the mechanism kept scratching and the sound would not settle",
        "checked the needle and fixed the phonograph",
    ),
    "silence": Response(
        "silence",
        2,
        1,
        "closed the lid and set the phonograph aside for later",
        "closed the lid, but the scratching sound had already spread into the room",
        "closed the lid and set it aside",
    ),
    "cleaning": Response(
        "cleaning",
        2,
        2,
        "brushed the dust away from the record and wiped the needle clean",
        "wiped it clean, but the scratch had already made too much noise",
        "brushed the dust away and wiped the needle clean",
    ),
    "water": Response(
        "water",
        1,
        0,
        "splashed water on the phonograph",
        "splashed water on it, but that only made things worse",
        "splashed water on it",
    ),
}

NAMES_GIRL = ["Maya", "Lina", "Nora", "Ava", "Iris"]
NAMES_BOY = ["Noah", "Eli", "Theo", "Finn", "Leo"]
TRAITS = ["curious", "careful", "quiet", "thoughtful"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for rid, resp in RESPONSES.items():
            if resp.sense >= SENSE_MIN:
                combos.append((sid, rid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    response: str
    child_name: str
    child_type: str
    friend_name: str
    friend_type: str
    helper_type: str
    trait: str
    delay: int = 0
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery story world in a reading nook.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["librarian", "mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid story combinations.")
    setting = args.setting or rng.choice(sorted(SETTINGS))
    response = args.response or rng.choice(sorted(rid for _, rid in combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or ("boy" if child_type == "girl" else "girl")
    child_name = args.child_name or rng.choice(NAMES_GIRL if child_type == "girl" else NAMES_BOY)
    friend_name = args.friend_name or rng.choice(NAMES_BOY if friend_type == "boy" else NAMES_GIRL)
    helper_type = args.helper_type or rng.choice(["librarian", "mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    if RESPONSES[response].sense < SENSE_MIN:
        raise StoryError(f"Response {response} is too low-sense.")
    return StoryParams(setting, response, child_name, child_type, friend_name, friend_type, helper_type, trait, delay)


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mystery story for a 3-to-5-year-old set in a reading nook. Include the words "phonograph" and "contest".',
        f"Tell a calm detective story where {f['child'].id} and {f['friend'].id} have a contest in a reading nook and investigate a strange sound from the phonograph.",
        f"Write a happy-ending mystery about a reading nook, an old phonograph, and a contest that turns into a problem-solving game.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, friend, helper = f["child"], f["friend"], f["helper"]
    resp: Response = f["response"]
    qa = [
        ("Where was the story set?",
         "It was set in a reading nook, with cushions, books, and a little lamp making the place feel cozy."),
        ("What were the children doing?",
         f"They were having a contest to solve a small mystery. They listened closely and tried to figure out why the phonograph sounded strange."),
        ("What caused the conflict?",
         "The phonograph made a scratchy noise when the needle slipped. That made the contest tense for a moment because the sound felt mysterious and wrong."),
        ("How was the problem fixed?",
         f"A careful grown-up {resp.qa_text}. That stopped the scratchy noise and let the children go back to their contest."),
    ]
    if f.get("mystery_resolved"):
        qa.append(
            ("How did the children feel at the end?",
             "They felt relieved, proud, and happy. The mystery was solved, so the reading nook became calm again.")
        )
        qa.append(
            ("Why is the ending happy?",
             "Because the problem was solved without anyone getting hurt. The phonograph was fixed, and the children could keep enjoying their contest.")
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a phonograph?",
         "A phonograph is an old machine that plays sound from a record. It is something people can listen to, but it needs careful handling."),
        ("What is a contest?",
         "A contest is a game or challenge where people try to do something and see who solves it best or fastest."),
        ("Why are reading nooks cozy?",
         "Reading nooks are cozy because they usually have soft seats, quiet corners, and good light for books."),
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        child_name=params.child_name,
        child_type=params.child_type,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
        parent_type=params.helper_type,
        delay=params.delay,
        response=RESPONSES[params.response],
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


CURATED = [
    StoryParams("reading_nook", "repair", "Maya", "girl", "Noah", "boy", "librarian", "curious", 0),
    StoryParams("reading_nook", "cleaning", "Lina", "girl", "Eli", "boy", "mother", "thoughtful", 1),
    StoryParams("reading_nook", "silence", "Theo", "boy", "Nora", "girl", "father", "quiet", 2),
]


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}).)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(S,R) :- setting(S), response(R), sensible(R).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    import asp
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate")
    sample = generate(CURATED[0])
    if not sample.story or "phonograph" not in sample.story or "contest" not in sample.story:
        print("MISMATCH: sample story is malformed.")
        rc = 1
    else:
        print("OK: story generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld in a reading nook.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["librarian", "mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("sensible responses:", ", ".join(asp_sensible()))
        print()
        for s, r in asp_valid_combos():
            print(f"{s:12} {r}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.child_name} and {p.friend_name}: {p.setting}, {p.response}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
