#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/divert_flashback_happy_ending_teamwork_whodunit.py
==================================================================================

A standalone story world sketch for a child-friendly whodunit with a flashback,
teamwork, and a happy ending. The core premise is small and classical: something
goes missing, suspicion rises, the children follow clues, a flashback reveals a
useful memory, and the team diverts attention from the wrong suspect to the real
solution.

The story model is built around a tiny detective game:
- a prized object goes missing,
- one clue is misleading,
- a flashback shows where the object was last seen,
- teamwork helps the children divert attention and search the right place,
- the ending proves the mystery was solved kindly.

The word "divert" is used in-story in a concrete way: the children divert
attention, divert a pet, or divert a stream of worry away from the wrong guess.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/divert_flashback_happy_ending_teamwork_whodunit.py
    python storyworlds/worlds/gpt-5.4-mini/divert_flashback_happy_ending_teamwork_whodunit.py --all
    python storyworlds/worlds/gpt-5.4-mini/divert_flashback_happy_ending_teamwork_whodunit.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/divert_flashback_happy_ending_teamwork_whodunit.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/divert_flashback_happy_ending_teamwork_whodunit.py --verify
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    location: str = ""
    suspicious: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
    clue_spot: str
    weather: str = ""

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class MysteryObject:
    id: str
    label: str
    phrase: str
    hide_spot: str
    important: str
    suspicious_by_default: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Suspect:
    id: str
    label: str
    alibi: str
    clue: str
    innocent_reason: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Helper:
    id: str
    label: str
    action: str
    result: str
    divert_text: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    obj = world.get("mystery")
    if obj.meters["missing"] < THRESHOLD:
        return out
    sig = ("worry", obj.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ch in world.characters():
        ch.memes["worry"] += 1
    out.append("__worry__")
    return out


def _r_divert(world: World) -> list[str]:
    out: list[str] = []
    if world.get("pet").meters["distracted"] < THRESHOLD:
        return out
    sig = ("divert", "pet")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("pet").memes["calm"] += 1
    out.append("__divert__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("divert", "social", _r_divert)]


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


def clue_reaches_right_place(setting: Setting, mystery: MysteryObject, helper: Helper) -> bool:
    return setting.clue_spot == mystery.hide_spot and bool(helper.result)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for mid, m in MYSTERIES.items():
            for hid, h in HELPERS.items():
                for sus in SUSPECTS:
                    if clue_reaches_right_place(SETTINGS[sid], m, h):
                        combos.append((sid, mid, hid, sus))
    return combos


def story_line(world: World, narrator: Entity, friend: Entity, object_ent: Entity) -> None:
    world.say(
        f"At {world.facts['setting'].place}, {narrator.id} and {friend.id} were playing detective. "
        f"Then they noticed {object_ent.label} was gone."
    )
    world.say(
        f'"Who took it?" {narrator.id} asked, while {friend.id} looked at the clues around {world.facts["setting"].clue_spot}.'
    )


def flashback(world: World, narrator: Entity, friend: Entity, mystery: MysteryObject) -> None:
    narrator.memes["memory"] += 1
    friend.memes["memory"] += 1
    world.say(
        f"Then {narrator.id} had a flashback: {narrator.pronoun().capitalize()} remembered {mystery.phrase} being seen near {mystery.hide_spot}."
    )
    world.say(
        f'"That was where we last saw it," {friend.id} said. "We should divert our guesses and search there."'
    )


def teamwork(world: World, narrator: Entity, friend: Entity, helper: Helper, mystery: MysteryObject, suspect: Suspect) -> None:
    narrator.memes["teamwork"] += 1
    friend.memes["teamwork"] += 1
    world.say(
        f"The two friends worked together: one looked low, the other looked high, and they kept talking so no one got stuck on the wrong idea."
    )
    world.say(
        f"They even used teamwork to divert the pet away from the hall while they searched."
    )
    world.get("pet").meters["distracted"] += 1
    propagate(world, narrate=True)
    if helper.label:
        world.say(
            f"With {helper.label}'s help, they checked {mystery.hide_spot} and found the clue that mattered."
        )


def reveal(world: World, mystery: MysteryObject, suspect: Suspect) -> None:
    obj = world.get("mystery")
    obj.meters["missing"] = 0
    obj.location = mystery.hide_spot
    world.say(
        f"It was not {suspect.label} at all. The missing {mystery.label} had simply been tucked behind the {mystery.hide_spot}."
    )
    world.say(
        f"When they lifted it out, the whole room felt bright again."
    )


def ending(world: World, narrator: Entity, friend: Entity, mystery: MysteryObject, helper: Helper) -> None:
    for ch in (narrator, friend):
        ch.memes["joy"] += 1
        ch.memes["relief"] += 1
    world.say(
        f"{narrator.id} and {friend.id} laughed, thanked everyone, and put {mystery.label} back where it belonged."
    )
    world.say(
        f"That night, the case was solved, the pet was calm, and the friends had a happy ending because they stayed kind and worked as a team."
    )


def tell(setting: Setting, mystery: MysteryObject, suspect: Suspect, helper: Helper,
         n1: str = "Mia", t1: str = "girl", n2: str = "Leo", t2: str = "boy",
         parent_type: str = "mother") -> World:
    world = World()
    a = world.add(Entity(id=n1, kind="character", type=t1, role="detective"))
    b = world.add(Entity(id=n2, kind="character", type=t2, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    obj = world.add(Entity(id="mystery", type="thing", label=mystery.label, location=mystery.hide_spot, suspicious=mystery.suspicious_by_default))
    pet = world.add(Entity(id="pet", type="animal", label="the kitten"))
    world.add(Entity(id="suspect", type="person", label=suspect.label, suspicious=True))
    world.facts.update(setting=setting, mystery=mystery, suspect=suspect, helper=helper, parent=parent)

    story_line(world, a, b, obj)
    world.para()
    world.say(
        f"At first, {suspect.label} looked suspicious because {suspect.clue}."
    )
    world.say(
        f"But {n1} noticed a small detail: {suspect.innocent_reason}."
    )
    world.para()
    flashback(world, a, b, mystery)
    teamwork(world, a, b, helper, mystery, suspect)
    world.para()
    reveal(world, mystery, suspect)
    ending(world, a, b, mystery, helper)

    world.facts.update(narrator=a, friend=b, pet=pet, object=obj, outcome="happy")
    return world


SETTINGS = {
    "house": Setting("house", "a cozy house", "the hallway"),
    "library": Setting("library", "the little library", "the front desk"),
    "garden": Setting("garden", "the garden", "the flower bed"),
}

MYSTERIES = {
    "cookie": MysteryObject("cookie", "cookie jar", "a cookie jar", "the shelf", "snack time", suspicious_by_default=True),
    "paintbrush": MysteryObject("paintbrush", "paintbrush", "a paintbrush", "the art table", "painting time"),
    "ribbon": MysteryObject("ribbon", "blue ribbon", "a blue ribbon", "the basket", "show-and-tell"),
}

SUSPECTS = {
    "cat": Suspect("cat", "the cat", "she was near the room", "there were paw prints on the floor", "the cat was only napping"),
    "brother": Suspect("brother", "the older brother", "he had been reading quietly", "he held a book", "he never touched the shelf"),
    "neighbor": Suspect("neighbor", "the neighbor", "she brought flowers", "she was holding a vase", "she had just arrived"),
}

HELPERS = {
    "map": Helper("map", "a little map", "draw a path", "show the right corner", "divert their guesses"),
    "lantern": Helper("lantern", "a lantern", "light up the dark spot", "make the clue easy to see", "divert the darkness"),
    "notice": Helper("notice", "a notice board", "check the notes", "point to the last place", "divert attention to details"),
}

GIRL_NAMES = ["Mia", "Lila", "Zoe", "Nora", "Ava"]
BOY_NAMES = ["Leo", "Ben", "Max", "Eli", "Toby"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    mystery: str
    suspect: str
    helper: str
    name1: str
    gender1: str
    name2: str
    gender2: str
    parent: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
    ap = argparse.ArgumentParser(description="A tiny whodunit story world with a flashback, teamwork, and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--parent", choices=["mother", "father"])
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
        raise StoryError("No valid mystery story combos available.")
    filtered = [c for c in combos
                if (args.setting is None or c[0] == args.setting)
                and (args.mystery is None or c[1] == args.mystery)
                and (args.helper is None or c[2] == args.helper)
                and (args.suspect is None or c[3] == args.suspect)]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, helper, suspect = rng.choice(sorted(filtered))
    name1 = rng.choice(GIRL_NAMES + BOY_NAMES)
    name2 = rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name1])
    gender1 = rng.choice(["girl", "boy"])
    gender2 = rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, mystery, suspect, helper, name1, gender1, name2, gender2, parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly whodunit story that includes the word "divert" and ends happily in {f["setting"].place}.',
        f"Tell a mystery story where two children use teamwork, remember a flashback, and divert attention away from the wrong suspect before solving the case.",
        f"Write a short whodunit about a missing {f['mystery'].label} that turns into a happy ending after the children work together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    m: MysteryObject = f["mystery"]
    s: Suspect = f["suspect"]
    h: Helper = f["helper"]
    a: Entity = f["narrator"]
    b: Entity = f["friend"]
    return [
        ("What kind of story is this?", "It is a whodunit story, so the children look for clues and try to solve a small mystery."),
        ("What went missing?", f"The missing item was {m.label}. The story follows the clues until they find where it was hidden."),
        ("What did the flashback help them remember?", f"The flashback helped them remember that {m.phrase} was last seen near {m.hide_spot}. That memory pointed them to the right place."),
        ("How did teamwork help?", f"{a.id} and {b.id} searched together, kept each other focused, and used teamwork to divert attention from the wrong guess. Because they worked as a team, they solved the mystery kindly."),
        (f"Was {s.label} the thief?", f"No. {s.label} only looked suspicious at first, but the clue showed {s.innocent_reason}."),
        ("How did the story end?", "It ended happily. The missing thing was found, nobody was blamed unfairly, and everyone felt proud of the teamwork."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a clue?", "A clue is a small piece of information that helps you solve a mystery."),
        ("What is a flashback?", "A flashback is a memory scene that shows something from earlier, helping the character understand what happened."),
        ("What does teamwork mean?", "Teamwork means people help each other and do different parts of a job together."),
        ("What does divert mean?", "To divert something means to turn it aside or away from where it was going."),
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
        if e.location:
            bits.append(f"location={e.location}")
        if e.suspicious:
            bits.append("suspicious=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
missing(X) :- object(X), missing_obj(X).
worry(C) :- character(C), missing(mystery).
right_spot(S) :- setting(S), clue_spot(S).
found(M) :- mystery(M), location(M, L), clue_spot(L).
happy_end :- found(_), teamwork(_), flashback(_).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story
        print("OK: story generation smoke test passed.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        MYSTERIES[params.mystery],
        SUSPECTS[params.suspect],
        HELPERS[params.helper],
        params.name1, params.gender1, params.name2, params.gender2, params.parent,
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible combos:")
        for row in valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("house", "cookie", "cat", "map", "Mia", "girl", "Leo", "boy", "mother"),
            StoryParams("library", "paintbrush", "brother", "lantern", "Ava", "girl", "Ben", "boy", "father"),
            StoryParams("garden", "ribbon", "neighbor", "notice", "Zoe", "girl", "Toby", "boy", "mother"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
