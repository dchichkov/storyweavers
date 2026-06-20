#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/eva_clip_laundromat_mystery_to_solve_nursery.py
===============================================================================

A standalone story world for a tiny nursery-rhyme-style laundromat mystery.

Premise:
- Eva and Clip are at a laundromat.
- A small mystery appears: a washer makes a clink, a sock goes missing, or a
  note/pocket clue is found.
- They solve it with a calm helper, a simple search, and a safe ending.

The world is intentionally small and classical:
- typed entities with physical meters and emotional memes
- forward causal rules
- reasonableness gate and inline ASP twin
- three Q&A sets from world state, not by parsing rendered prose
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class Mystery:
    id: str
    clue: str
    missing: str
    place: str
    sound: str
    fix: str
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
class Helper:
    id: str
    label: str
    calm: int
    method: str
    tool: str
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
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def chars(self) -> list[Entity]:
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


@dataclass
class Rule:
    name: str
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
    clue = world.facts.get("clue")
    if not clue:
        return out
    for kid in world.chars():
        if kid.memes["curiosity"] >= THRESHOLD and kid.memes["worry"] < THRESHOLD:
            sig = ("worry", kid.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            kid.memes["worry"] += 1
            out.append(f"{kid.id} looked at the clue and grew quiet.")
    return out


def _r_found(world: World) -> list[str]:
    out: list[str] = []
    sock = world.get("sock")
    if sock.meters["hidden"] < THRESHOLD:
        sig = ("found", sock.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        sock.meters["found"] += 1
        out.append("__found__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("solved"):
        for kid in world.chars():
            if kid.memes["relief"] < THRESHOLD:
                sig = ("relief", kid.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                kid.memes["relief"] += 1
                out.append(f"{kid.id} felt light as a feather.")
    return out


RULES = [Rule("worry", _r_worry), Rule("found", _r_found), Rule("relief", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(mystery: Mystery, helper: Helper) -> bool:
    return mystery.id in MYSTERIES and helper.calm >= SENSE_MIN


def choose_hidden(mystery: Mystery) -> str:
    return mystery.missing


def search_find(world: World, mystery: Mystery) -> None:
    sock = world.get("sock")
    sock.meters["hidden"] = 0.0
    sock.meters["found"] = 1.0
    world.get("room").meters["mystery"] = 0.0
    world.facts["solved"] = True
    world.say(
        f"Eva and Clip tiptoed by the machines. Under a basket, under a chair, "
        f"they followed the little clue. There, where the dryer hummed like a bee, "
        f"they found the {mystery.missing}."
    )
    world.say(
        f"It had been hiding near {mystery.place}, right where {mystery.sound} had started the riddle."
    )


def opening(world: World, eva: Entity, clip: Entity, mystery: Mystery) -> None:
    world.say(
        f"At the laundromat bright and neat, Eva and Clip went on small feet. "
        f"Spin and swish, with baskets tall, the washers sang a silver call."
    )
    world.say(
        f"Then came a clink, a tiny wink; Eva said, \"Oh my, I think "
        f"something is missing from the wash!\""
    )


def clue_tension(world: World, eva: Entity, clip: Entity, mystery: Mystery) -> None:
    eva.memes["curiosity"] += 1
    clip.memes["curiosity"] += 1
    world.facts["clue"] = mystery.clue
    world.get("room").meters["mystery"] += 1
    world.say(
        f"Clip looked close and found a note: {mystery.clue}. "
        f"Eva nodded slow and soft. \"A mystery to solve,\" she said, "
        f"\"in the laundromat light.\""
    )
    propagate(world, narrate=True)


def helper_turn(world: World, helper: Entity, mystery: Mystery) -> None:
    helper.memes["calm"] += 1
    world.say(
        f"Then {helper.id} came with a smile. \"Look where the little things hide,\" "
        f"{helper.pronoun()} said, and showed them {helper.attrs['method']}."
    )
    world.say(
        f"\"A clip can click, a sock can slip, but careful eyes can solve the trip.\""
    )


def ending(world: World, eva: Entity, clip: Entity, mystery: Mystery) -> None:
    eva.memes["joy"] += 1
    clip.memes["joy"] += 1
    world.say(
        f"Eva clipped the sock to the line, Clip laughed, and everything felt fine. "
        f"With the mystery solved and the basket still bright, they skipped home "
        f"like moonbeams in white."
    )


def tell(mystery: Mystery, helper: Helper, eva_name: str = "Eva", clip_name: str = "Clip") -> World:
    world = World()
    eva = world.add(Entity(id=eva_name, kind="character", type="girl", role="solver"))
    clip = world.add(Entity(id=clip_name, kind="character", type="thing", role="helper"))
    helper_ent = world.add(Entity(id=helper.id, kind="character", type="adult", label=helper.label))
    room = world.add(Entity(id="room", type="room", label="the laundromat"))
    sock = world.add(Entity(id="sock", type="thing", label=mystery.missing))
    sock.meters["hidden"] = 1.0
    room.meters["mystery"] = 1.0

    eva.memes["curiosity"] = 1.0
    clip.memes["curiosity"] = 1.0
    helper_ent.memes["calm"] = float(helper.calm)
    helper_ent.attrs["method"] = helper.method

    opening(world, eva, clip, mystery)
    world.para()
    clue_tension(world, eva, clip, mystery)
    world.para()
    helper_turn(world, helper_ent, mystery)
    search_find(world, mystery)
    world.para()
    ending(world, eva, clip, mystery)

    world.facts.update(
        eva=eva,
        clip=clip,
        helper=helper_ent,
        room=room,
        sock=sock,
        mystery=mystery,
        solved=True,
    )
    return world


@dataclass
@dataclass
class StoryParams:
    mystery: str
    helper: str
    eva_name: str
    clip_name: str
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


MYSTERIES = {
    "sock": Mystery(
        "sock",
        clue="A tiny clip was holding a note that said, 'Look low and listen soft.'",
        missing="sock",
        place="the lint basket",
        sound="the dryer tick-tock",
        fix="find the sock",
        tags={"sock", "clip", "laundromat"},
    ),
    "clip": Mystery(
        "clip",
        clue="A bright clip was caught in a sleeve and gave a shiny clue.",
        missing="clip",
        place="the folding table",
        sound="the washer clink",
        fix="find the clip",
        tags={"clip", "laundromat"},
    ),
    "button": Mystery(
        "button",
        clue="A small button rolled away like a pearl on the tile.",
        missing="button",
        place="under the bench",
        sound="the spin cycle swish",
        fix="find the button",
        tags={"button", "laundromat"},
    ),
}

HELPERS = {
    "owner": Helper("owner", "the owner", 3, "check the pockets and the lint trap", "a little magnet", {"laundromat"}),
    "mom": Helper("mom", "mom", 3, "peek behind the baskets", "a small flashlight", {"laundromat"}),
    "neighbor": Helper("neighbor", "a kind neighbor", 2, "look on the floor by the dryers", "a bright basket", {"laundromat"}),
}

CURATED = [
    StoryParams("sock", "owner", "Eva", "Clip"),
    StoryParams("clip", "mom", "Eva", "Clip"),
    StoryParams("button", "neighbor", "Eva", "Clip"),
]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for mid in MYSTERIES:
        for hid, helper in HELPERS.items():
            if reasonableness_gate(MYSTERIES[mid], helper):
                out.append((mid, hid))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    helper: Entity = f["helper"]
    return [
        f'Write a nursery-rhyme-style mystery story set in a laundromat that includes the words "Eva" and "clip".',
        f"Tell a gentle laundromat mystery where Eva and Clip notice a clue, ask {helper.label_word} for help, and solve the mystery.",
        f'Write a short story with a rhyme-like feel where the clue says "{mystery.clue}" and the ending proves the missing thing was found.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    helper: Entity = f["helper"]
    eva: Entity = f["eva"]
    clip: Entity = f["clip"]
    sock: Entity = f["sock"]
    return [
        (
            "Who is the story about?",
            f"It is about {eva.id} and {clip.id}, who went to the laundromat and noticed a small mystery. They stayed together and worked through it as a pair.",
        ),
        (
            "What was the mystery?",
            f"The mystery was {mystery.fix}. The clue pointed them toward {mystery.place}, so they knew where to look next.",
        ),
        (
            f"How did {helper.label} help?",
            f"{helper.label_word.capitalize()} showed them a calm way to search, using {helper.method}. That helped them find the missing thing without making the moment more confusing.",
        ),
        (
            "How did they solve it?",
            f"They followed the clue, listened to the humming machines, and found the {sock.label}. The search worked because they looked carefully instead of rushing around.",
        ),
    ]


KNOWLEDGE = {
    "laundromat": [
        ("What is a laundromat?", "A laundromat is a place where people wash and dry clothes in big machines."),
        ("Why do clothes go in a washer?", "Clothes go in a washer so soap and water can clean them."),
    ],
    "sock": [
        ("What is a sock?", "A sock is a soft cloth piece that you wear on your foot."),
    ],
    "clip": [
        ("What is a clip?", "A clip is a small thing that can hold paper, cloth, or other light objects together."),
    ],
    "button": [
        ("What is a button?", "A button is a small round piece that helps fasten clothes."),
    ],
    "mystery": [
        ("What is a mystery?", "A mystery is a question about something missing, hidden, or not yet understood."),
    ],
}

KNOWLEDGE_ORDER = ["laundromat", "sock", "clip", "button", "mystery"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["mystery"].tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        if e.attrs:
            parts.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for t in sorted(m.tags):
            lines.append(asp.fact("tag", mid, t))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("calm", hid, h.calm))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(M,H) :- mystery(M), helper(H), calm(H,C), sense_min(S), C >= S.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    p = set(valid_combos())
    a = set(asp_valid_combos())
    if p == a:
        print(f"OK: ASP matches valid_combos() ({len(p)} combos).")
    else:
        rc = 1
        print("MISMATCH:")
        if a - p:
            print(" only in ASP:", sorted(a - p))
        if p - a:
            print(" only in Python:", sorted(p - a))

    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: default generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme laundromat mystery world.")
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--eva", default="Eva")
    ap.add_argument("--clip", default="Clip")
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
    if args.mystery and args.helper:
        if (args.mystery, args.helper) not in valid_combos():
            raise StoryError("(No valid mystery/helper combination matches the given options.)")
    combos = [
        c for c in valid_combos()
        if (args.mystery is None or c[0] == args.mystery)
        and (args.helper is None or c[1] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    mystery, helper = rng.choice(sorted(combos))
    return StoryParams(mystery, helper, args.eva, args.clip)


def generate(params: StoryParams) -> StorySample:
    world = tell(MYSTERIES[params.mystery], HELPERS[params.helper], params.eva_name, params.clip_name)
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
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible mystery/helper combos:\n")
        for m, h in combos:
            print(f"  {m:8} {h}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.eva_name} & {p.clip_name}: {p.mystery} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
