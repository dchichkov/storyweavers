#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/lad_dim_marathon_mystery_to_solve_comedy.py
============================================================================

A standalone story world for a small comedy mystery: a child-run marathon
practice goes funny-bad when the race number disappears, the kids search for the
missing clue, and a cheerful grown-up helps them solve it in a way that proves
what changed.

Seed words:
- lad-dim
- marathon

Style:
- Comedy

Feature:
- Mystery to Solve

The world uses typed entities with physical meters and emotional memes, a small
forward-chained rule set, a reasonableness gate, and a matching inline ASP twin.
It generates complete, child-facing stories plus grounded Q&A from world state.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
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
    details: str
    weather: str = ""

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
    phrase: str
    where: str
    is_lost: bool = True

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
    mystery_word: str
    question: str
    solution: str
    red_herring: str
    comedy_beat: str
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
class Fix:
    id: str
    sense: int
    text: str
    reveal: str
    qa_text: str
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


def _r_search(world: World) -> list[str]:
    out: list[str] = []
    clue = world.get("clue")
    if clue.meters["lost"] < THRESHOLD:
        return out
    if ("search_started", clue.id) in world.fired:
        return out
    world.fired.add(("search_started", clue.id))
    for e in list(world.entities.values()):
        if e.kind == "character":
            e.memes["curiosity"] += 1
    out.append("__search__")
    return out


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    if world.get("hero").memes["confusion"] < THRESHOLD:
        return out
    if ("laugh", "hero") in world.fired:
        return out
    world.fired.add(("laugh", "hero"))
    world.get("hero").memes["embarrassment"] += 1
    out.append("__laugh__")
    return out


CAUSAL_RULES = [Rule("search", "social", _r_search), Rule("laugh", "social", _r_laugh)]


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


def reasonableness_ok(setting: Setting, mystery: Mystery, clue: Clue, fix: Fix) -> bool:
    return clue.is_lost and fix.sense >= SENSE_MIN and mystery.id in {"marathon"} and setting.id in {"track", "park"}


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for mid in MYSTERIES:
            for cid in CLUES:
                for fid in FIXES:
                    if reasonableness_ok(SETTINGS[sid], MYSTERIES[mid], CLUES[cid], FIXES[fid]):
                        combos.append((sid, mid, cid, fid))
    return combos


def default_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: f.sense)


def _do_mystery(world: World, clue: Entity, narrate: bool = True) -> None:
    clue.meters["lost"] += 1
    clue.memes["mystery"] += 1
    propagate(world, narrate=narrate)


def introduction(world: World, hero: Entity, friend: Entity, mystery: Mystery) -> None:
    world.say(
        f"At {world.setting.place}, {hero.id} and {friend.id} were getting ready for a silly little marathon, "
        f"because {world.setting.details} made everything feel like a game."
    )
    world.say(
        f'They called it the "{mystery.mystery_word}" case, which sounded grand until everyone realized '
        f'they were looking for a missing race number.'
    )


def missing_clue(world: World, clue: Clue, mystery: Mystery) -> None:
    world.say(
        f"Then the clue went missing. The {clue.label} was supposed to be {clue.where}, but it was nowhere to be seen."
    )
    world.say(
        f'"{mystery.question}" asked {world.get("hero").id}, staring at the empty spot as if it had personally offended them.'
    )


def comic_search(world: World, hero: Entity, friend: Entity, clue: Clue, mystery: Mystery) -> None:
    hero.memes["determination"] += 1
    friend.memes["helpfulness"] += 1
    world.say(
        f"{hero.id} peeked under a bench. {friend.id} checked the water bottle table. Even the banana peel looked suspicious."
    )
    world.say(
        f"\"{mystery.red_herring},\" said {friend.id}, \"but I don't think a banana can steal a number badge.\""
    )


def reveal(world: World, parent: Entity, fix: Fix, clue: Clue, mystery: Mystery) -> None:
    clue.meters["lost"] = 0.0
    clue.meters["found"] += 1
    world.get("hero").memes["relief"] += 1
    world.get("friend").memes["relief"] += 1
    world.say(
        f"Then {parent.label_word} came over, laughed, and {fix.text}."
    )
    world.say(
        f"The mystery was solved: {fix.reveal}, and the missing {clue.label} was back where everyone could see it."
    )
    world.say(
        f"\"{mystery.comedy_beat}\""
    )


def ending(world: World, hero: Entity, friend: Entity, clue: Clue, mystery: Mystery) -> None:
    world.say(
        f"In the end, {hero.id} wore the {clue.label} like a medal, {friend.id} grinned, and the marathon could finally begin."
    )
    world.say(
        f"That tiny case made a big funny day, and the race line felt brighter than before."
    )


def tell(setting: Setting, mystery: Mystery, clue_cfg: Clue, fix: Fix,
         hero_name: str = "Lad-Dim", hero_gender: str = "boy",
         friend_name: str = "Mina", friend_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    clue = world.add(Entity(id="clue", type="thing", label=clue_cfg.label, attrs={"where": clue_cfg.where}))
    clue.meters["lost"] = 1.0

    world.facts.update(setting=setting, mystery=mystery, clue_cfg=clue_cfg, fix=fix,
                       hero=hero, friend=friend, parent=parent, clue=clue)
    introduction(world, hero, friend, mystery)
    world.para()
    missing_clue(world, clue_cfg, mystery)
    comic_search(world, hero, friend, clue_cfg, mystery)
    _do_mystery(world, clue, narrate=False)
    world.para()
    reveal(world, parent, fix, clue_cfg, mystery)
    ending(world, hero, friend, clue_cfg, mystery)
    world.facts["solved"] = True
    return world


SETTINGS = {
    "track": Setting("track", "the school track", "the track was bright and chalky, with cones standing in a very serious line"),
    "park": Setting("park", "the park path", "the park path curled past swings, trees, and one suspicious sandwich wrapper"),
}

MYSTERIES = {
    "marathon": Mystery(
        "marathon", "lad-dim marathon", "Where did the missing race number go?",
        "It had slipped into the snack box", "the banana peel was too smug to trust",
        "the case was so tiny it nearly needed a magnifying glass for a peanut",
        tags={"marathon", "mystery"},
    ),
}

CLUES = {
    "number": Clue("number", "race number", "a paper race number", "on the clipboard"),
    "pin": Clue("pin", "safety pin", "a shiny safety pin", "in the start kit"),
}

FIXES = {
    "snack_box": Fix(
        "snack_box", 3,
        "looked in the snack box and found the number tucked beside a cookie",
        "the number had slipped into the snack box during the snack break",
        "looked in the snack box and found the missing race number",
        tags={"marathon", "found"},
    ),
    "pocket": Fix(
        "pocket", 2,
        "reached into a pocket and found the number folded up like a tiny map",
        "the number had fallen into a pocket",
        "found the missing race number in a pocket",
        tags={"marathon", "found"},
    ),
    "banana": Fix(
        "banana", 1,
        "asked the banana peel to confess, but it only slid away and made everyone laugh",
        "the banana peel was innocent, alas",
        "the banana peel was not the culprit",
        tags={"marathon", "comedy"},
    ),
}

GIRL_NAMES = ["Mina", "Zoe", "Lila", "Nora", "Ava"]
BOY_NAMES = ["Lad-Dim", "Timo", "Finn", "Eli", "Noah"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    mystery: str
    clue: str
    fix: str
    hero: str
    hero_gender: str
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


KNOWLEDGE = {
    "marathon": [("What is a marathon?",
                  "A marathon is a long race where people keep running for a very long time.")],
    "mystery": [("What is a mystery?",
                 "A mystery is a question with a missing answer that people try to solve.")],
    "track": [("What is a running track?",
               "A running track is a marked path where people run laps.")],
    "park": [("What is a park?",
              "A park is a place with open space, trees, and room to play or walk.")],
    "snack_box": [("What is a snack box for?",
                    "A snack box holds food so people can eat a little and keep going.")],
    "pocket": [("What is a pocket?",
                "A pocket is a little cloth pouch in clothes where small things can hide.")],
}
KNOWLEDGE_ORDER = ["marathon", "mystery", "track", "park", "snack_box", "pocket"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny mystery story for a child that uses the words "lad-dim" and "marathon".',
        f"Tell a comedy story where {f['hero'].id} and {f['friend'].id} search for a missing race number before the marathon begins.",
        f'Write a playful story about a tiny mystery at {f["setting"].place} that gets solved with a laugh.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend, parent, clue_cfg, fix = f["hero"], f["friend"], f["parent"], f["clue_cfg"], f["fix"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id} and {friend.id}, who were trying to get ready for a marathon and solve a missing-number mystery."),
        ("What was missing?",
         f"The missing thing was {clue_cfg.label}, the little paper number for the race. It was supposed to be {clue_cfg.where}."),
        ("How was the mystery solved?",
         f"{parent.label_word.capitalize()} helped by {fix.qa_text}. That found the missing race number and ended the search."),
        ("How did the story end?",
         f"It ended with the race ready to begin and everyone laughing. The funny mystery was solved, so the marathon could start at last."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["mystery"].tags) | set(world.facts["fix"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
    StoryParams("track", "marathon", "number", "snack_box", "Lad-Dim", "boy", "Mina", "girl", "mother"),
    StoryParams("park", "marathon", "pin", "pocket", "Timo", "boy", "Nora", "girl", "father"),
]


def explain_rejection(setting: Setting, mystery: Mystery, clue: Clue, fix: Fix) -> str:
    if fix.sense < SENSE_MIN:
        return f"(No story: the fix '{fix.id}' is too goofy to solve the mystery in a sensible way.)"
    if not clue.is_lost:
        return "(No story: the clue is not lost, so there is no mystery to solve.)"
    return "(No story: this combination does not fit the comedy mystery world.)"


def valid_story_params(params: StoryParams) -> bool:
    return reasonableness_ok(SETTINGS[params.setting], MYSTERIES[params.mystery], CLUES[params.clue], FIXES[params.fix])


ASP_RULES = r"""
lost(C) :- clue(C).
sensible(F) :- fix(F), sense(F,S), sense_min(M), S >= M.
valid(S, M, C, F) :- setting(S), mystery(M), clue(C), fix(F), lost(C), sensible(F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if c.is_lost:
            lines.append(asp.fact("lost", cid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, f.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(fid for (fid,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos")
    if set(asp_sensible()) != {fid for fid, f in FIXES.items() if f.sense >= SENSE_MIN}:
        rc = 1
        print("MISMATCH in sensible fixes")
    sample = generate(resolve_params(argparse.Namespace(setting=None, mystery=None, clue=None, fix=None, hero=None, hero_gender=None, friend=None, friend_gender=None, parent=None), random.Random(777)))
    if not sample.story.strip():
        rc = 1
        print("MISMATCH: generated story is empty")
    else:
        print("OK: generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy mystery world with a marathon and a missing clue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["boy", "girl"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["boy", "girl"])
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
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_rejection(SETTINGS["track"], MYSTERIES["marathon"], CLUES["number"], FIXES[args.fix]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.clue is None or c[2] == args.clue)
              and (args.fix is None or c[3] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, clue, fix = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or "boy"
    friend_gender = args.friend_gender or "girl"
    hero = args.hero or ("Lad-Dim" if hero_gender == "boy" else rng.choice(["Mina", "Nora"]))
    friend = args.friend or ("Mina" if friend_gender == "girl" else rng.choice(["Timo", "Finn"]))
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, mystery, clue, fix, hero, hero_gender, friend, friend_gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], CLUES[params.clue], FIXES[params.fix],
                 params.hero, params.hero_gender, params.friend, params.friend_gender, params.parent)
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
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
