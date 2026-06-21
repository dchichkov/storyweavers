#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/whats_conflict_mystery_to_solve_whodunit.py
===========================================================================

A standalone story world for a tiny whodunit-style mystery with conflict:
someone notices a missing object, the children disagree about what happened,
and a careful little sleuth solves the mystery by following physical clues.

Seed idea:
- Style: whodunit
- Words: "whats"
- Features: Conflict, Mystery to Solve

The world is built around a small household mystery. Each story starts with a
normal scene, introduces a disagreement, follows evidence through a few state
changes, and ends with the mystery solved in a concrete ending image.

This script follows the Storyweavers contract:
- typed entities with physical meters and emotional memes
- a Python reasonableness gate plus inline ASP twin
- StoryParams, build_parser, resolve_params, generate, emit, main
- QA generated from world state, not by parsing rendered story text
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
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
    intro: str

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
    clue_kind: str
    clue_phrase: str
    can_be_suspected: bool = True
    tags: set[str] = field(default_factory=set)

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
class MysteryItem:
    id: str
    label: str
    phrase: str
    hiding_spots: list[str]
    sticky: bool = False
    tags: set[str] = field(default_factory=set)

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
class Clue:
    id: str
    label: str
    phrase: str
    points_to: str
    tags: set[str] = field(default_factory=set)

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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    witness = world.get("witness")
    if detective.memes["doubt"] >= THRESHOLD and witness.memes["stress"] >= THRESHOLD:
        sig = ("conflict",)
        if sig not in world.fired:
            world.fired.add(sig)
            detective.memes["conflict"] += 1
            witness.memes["conflict"] += 1
            out.append("__conflict__")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    if detective.meters["observed"] < THRESHOLD:
        return out
    for clue in list(world.entities.values()):
        if clue.kind != "clue":
            continue
        sig = ("clue", clue.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        detective.memes["confidence"] += 1
        out.append(f"That clue made the answer feel closer.")
    return out


def _r_solve(world: World) -> list[str]:
    detective = world.get("detective")
    if detective.meters["solved"] < THRESHOLD:
        return []
    if ("solved",) in world.fired:
        return []
    world.fired.add(("solved",))
    detective.memes["relief"] += 1
    return ["__solve__"]


CAUSAL_RULES = [
    Rule("conflict", "social", _r_conflict),
    Rule("clue", "mystery", _r_clue),
    Rule("solve", "mystery", _r_solve),
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


def mystery_reasonable(suspect: Suspect, item: MysteryItem) -> bool:
    return suspect.can_be_suspected and item.sticky


SETTINGS = {
    "home": Setting("home", "the little house", "The little house felt quiet and tidy."),
    "school": Setting("school", "the classroom", "The classroom was bright, but one desk looked messy."),
    "library": Setting("library", "the library", "The library was calm, except for one missing thing."),
}

SUSPECTS = {
    "cat": Suspect("cat", "the cat", "fur on the chair", "a tuft of fur"),
    "wind": Suspect("wind", "the open window", "a paper trail", "slipped paper"),
    "brother": Suspect("brother", "the big brother", "sneakers by the door", "muddy sneakers"),
}

ITEMS = {
    "cookie": MysteryItem("cookie", "the missing cookie", "a cookie from the tin", ["jar", "plate"], sticky=True, tags={"food"}),
    "key": MysteryItem("key", "the lost key", "a small brass key", ["pocket", "rug"], sticky=True, tags={"metal"}),
    "note": MysteryItem("note", "the missing note", "a folded note", ["book", "drawer"], sticky=True, tags={"paper"}),
}

CLUES = {
    "crumbs": Clue("crumbs", "crumbs", "a trail of crumbs", "cookie", tags={"food"}),
    "scratch": Clue("scratch", "scratch marks", "tiny scratch marks", "cat", tags={"cat"}),
    "mud": Clue("mud", "muddy prints", "muddy prints by the door", "brother", tags={"mud"}),
    "draft": Clue("draft", "a draft", "the window was open", "wind", tags={"wind"}),
}

WORLD_KNOWLEDGE = {
    "cat": [("Why might a cat get blamed in a mystery?",
             "Cats often leave fur, make little messes, and like to sneak around, so they can look suspicious even when they did nothing wrong.")],
    "wind": [("What can wind do?",
              "Wind can move light things like papers or napkins from one place to another.")],
    "crumbs": [("What do crumbs tell you?",
                "Crumbs can tell you that someone ate a snack nearby.")],
    "scratch": [("What do scratch marks mean?",
                  "Scratch marks show that something rubbed or scraped against a surface.")],
    "mud": [("Why do muddy prints matter?",
             "Muddy prints can show who walked in from outside.")],
    "key": [("What is a key for?",
            "A key is used to open a lock.")],
}


@dataclass
@dataclass
class StoryParams:
    setting: str
    suspect: str
    item: str
    clue1: str
    clue2: str
    detective: str
    witness: str
    detective_gender: str
    witness_gender: str
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
    ap = argparse.ArgumentParser(description="A tiny whodunit mystery story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--clue1", choices=CLUES)
    ap.add_argument("--clue2", choices=CLUES)
    ap.add_argument("--detective")
    ap.add_argument("--witness")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--witness-gender", choices=["girl", "boy"])
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for suspect in SUSPECTS:
            for item in ITEMS:
                if mystery_reasonable(SUSPECTS[suspect], ITEMS[item]):
                    combos.append((s, suspect, item))
    return combos


def explain_rejection(suspect: Suspect, item: MysteryItem) -> str:
    if not item.sticky:
        return f"(No story: {item.label} would not make a mystery because it would not be missing in a useful way.)"
    if not suspect.can_be_suspected:
        return f"(No story: {suspect.label} cannot be treated as a suspect in this world.)"
    return "(No story: this combination does not make a good mystery.)"


def _pick_name(rng: random.Random, gender: str, used: str = "") -> str:
    pool = ["Lina", "Maya", "Nora", "Zoe"] if gender == "girl" else ["Ben", "Theo", "Max", "Leo"]
    choices = [n for n in pool if n != used]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.suspect and args.item and not mystery_reasonable(SUSPECTS[args.suspect], ITEMS[args.item]):
        raise StoryError(explain_rejection(SUSPECTS[args.suspect], ITEMS[args.item]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.suspect is None or c[1] == args.suspect)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, suspect, item = rng.choice(sorted(combos))
    clue_pool = [k for k, c in CLUES.items() if c.points_to == suspect or c.points_to == item]
    clue1, clue2 = rng.sample(clue_pool, 2 if len(clue_pool) >= 2 else 1)
    d_gender = args.detective_gender or rng.choice(["girl", "boy"])
    w_gender = args.witness_gender or rng.choice(["girl", "boy"])
    detective = args.detective or _pick_name(rng, d_gender)
    witness = args.witness or _pick_name(rng, w_gender, used=detective)
    return StoryParams(setting, suspect, item, clue1, clue2, detective, witness, d_gender, w_gender)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    detective = world.add(Entity(id=params.detective, kind="character", type=params.detective_gender, role="detective"))
    witness = world.add(Entity(id=params.witness, kind="character", type=params.witness_gender, role="witness"))
    suspect = world.add(Entity(id="suspect", kind="suspect", label=SUSPECTS[params.suspect].label))
    item = world.add(Entity(id="item", kind="item", label=ITEMS[params.item].label))
    clue_a = world.add(Entity(id=params.clue1, kind="clue", label=CLUES[params.clue1].label))
    clue_b = world.add(Entity(id=params.clue2, kind="clue", label=CLUES[params.clue2].label))

    detective.memes["curiosity"] += 1
    witness.memes["stress"] += 1
    world.say(f"{world.setting.intro} {detective.id} said, \"What’s going on here?\"")
    world.say(f"{witness.id} pointed at the empty spot where {ITEMS[params.item].label} should have been.")

    world.para()
    detective.memes["doubt"] += 1
    witness.memes["stress"] += 1
    world.say(f"At first, {detective.id} and {witness.id} disagreed about who had taken it.")
    world.say(f"{detective.id} wondered if {SUSPECTS[params.suspect].label} looked too suspicious.")

    world.para()
    detective.meters["observed"] += 1
    world.say(f"{detective.id} looked closer and found {CLUES[params.clue1].phrase}.")
    world.say(f"Then {detective.id} noticed {CLUES[params.clue2].phrase}.")
    if CLUES[params.clue1].points_to == params.suspect or CLUES[params.clue2].points_to == params.suspect:
        world.say(f"The clues did not match the first guess, so the mystery stayed open a little longer.")
    else:
        world.say(f"The clues began to point away from the loudest guess and toward the real answer.")

    world.para()
    detective.meters["solved"] += 1
    world.say(f"That was when {detective.id} solved it: {ITEMS[params.item].label} had simply been tucked away in a hiding spot.")
    world.say(f"It was not the cat, not the wind, and not any big trouble at all.")
    world.say(f"{detective.id} found it, and the room felt calm again.")

    propagate(world, narrate=True)

    world.facts.update(
        setting=SETTINGS[params.setting],
        suspect=SUSPECTS[params.suspect],
        item=ITEMS[params.item],
        clue1=CLUES[params.clue1],
        clue2=CLUES[params.clue2],
        detective=detective,
        witness=witness,
        outcome="solved",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a whodunit story for a young child that includes the word "whats" and ends with the mystery solved.',
        f"Tell a small mystery story where {f['detective'].id} and {f['witness'].id} disagree, then solve what happened to the missing {f['item'].label}.",
        f"Write a conflict-and-mystery story in a calm whodunit style, with clues that point to the truth instead of a big scary chase.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    item = f["item"]
    suspect = f["suspect"]
    return [
        QAItem(
            question="What was the mystery about?",
            answer=f"It was about the missing {item.label}. The story kept asking what happened until the clues made it clear.",
        ),
        QAItem(
            question="Why did the children argue at the start?",
            answer=f"They did not agree at first about what had happened to the {item.label}. That conflict made the mystery harder before the clues sorted it out.",
        ),
        QAItem(
            question=f"How did {detective.id} solve the mystery?",
            answer=f"{detective.id} looked at the clues and noticed they pointed to the real hiding spot. In the end, the answer was simple and the mystery was solved without any big trouble.",
        ),
        QAItem(
            question=f"Was {suspect.label} the answer?",
            answer=f"No, {suspect.label} only looked suspicious at first. The clues showed that the missing thing had been tucked away somewhere else.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set()
    for ent in world.facts.values():
        if hasattr(ent, "tags"):
            tags |= set(ent.tags)
    out: list[QAItem] = []
    for tag, items in WORLD_KNOWLEDGE.items():
        if tag in tags:
            for q, a in items:
                out.append(QAItem(q, a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
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
        if e.kind:
            bits.append(f"kind={e.kind}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
mystery_ok(S, U) :- suspect(S), item(U), sticky(U), can_be_suspected(S).
outcome(solved) :- detective_solves.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        if s.can_be_suspected:
            lines.append(asp.fact("can_be_suspected", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.sticky:
            lines.append(asp.fact("sticky", iid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show mystery_ok/2."))
    return sorted(set(asp.atoms(model, "mystery_ok")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set((s, i) for _, s, i in valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in ASP gate.")
        rc = 1
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    if not sample.story:
        print("MISMATCH: sample story empty.")
        rc = 1
    else:
        print("OK: generation smoke test passed.")
    return rc


CURATED = [
    StoryParams("home", "cat", "cookie", "crumbs", "scratch", "Lina", "Ben", "girl", "boy"),
    StoryParams("school", "wind", "note", "draft", "crumbs", "Maya", "Theo", "girl", "boy"),
    StoryParams("library", "brother", "key", "mud", "scratch", "Nora", "Max", "girl", "boy"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("", "#show mystery_ok/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid mystery combos:")
        for item in combos:
            print(item)
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
