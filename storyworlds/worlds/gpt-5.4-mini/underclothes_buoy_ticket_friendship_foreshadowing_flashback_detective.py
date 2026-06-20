#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/underclothes_buoy_ticket_friendship_foreshadowing_flashback_detective.py
========================================================================================================

A small detective-story world for a child-friendly mystery about a missing
ticket, a stray buoy, underclothes on the laundry line, friendship, and a clue
that pays off with foreshadowing and a flashback.

The world is intentionally tiny: one child finds a problem, a friend notices a
pattern, a flashback explains the odd clue, and a grown-up helps the pair solve
the case. The key nouns from the seed are embedded as real world objects and
events, not as swapped-in labels.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/underclothes_buoy_ticket_friendship_foreshadowing_flashback_detective.py
    python storyworlds/worlds/gpt-5.4-mini/underclothes_buoy_ticket_friendship_foreshadowing_flashback_detective.py --all
    python storyworlds/worlds/gpt-5.4-mini/underclothes_buoy_ticket_friendship_foreshadowing_flashback_detective.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/underclothes_buoy_ticket_friendship_foreshadowing_flashback_detective.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        from collections import defaultdict
        if not isinstance(self.meters, defaultdict):
            self.meters = defaultdict(float, self.meters)
        if not isinstance(self.memes, defaultdict):
            self.memes = defaultdict(float, self.memes)

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
    water: str
    affords: set[str] = field(default_factory=set)

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
class ObjectCfg:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)

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
class CharacterCfg:
    id: str
    type: str
    gender: str
    role: str

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
@dataclass
class StoryParams:
    setting: str
    child: str
    friend: str
    parent: str
    ticket: str
    buoy: str
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


SETTINGS = {
    "harbor": Setting("harbor", "the harbor walk", "the water"),
    "beach": Setting("beach", "the beach boardwalk", "the tide"),
    "lake": Setting("lake", "the lakeside path", "the lake"),
}

CHILDREN = {
    "Nina": CharacterCfg("Nina", "girl", "girl", "detective"),
    "Milo": CharacterCfg("Milo", "boy", "boy", "detective"),
    "June": CharacterCfg("June", "girl", "girl", "detective"),
    "Owen": CharacterCfg("Owen", "boy", "boy", "detective"),
}

FRIENDS = {
    "Pip": CharacterCfg("Pip", "girl", "girl", "friend"),
    "Toby": CharacterCfg("Toby", "boy", "boy", "friend"),
    "Bea": CharacterCfg("Bea", "girl", "girl", "friend"),
    "Sam": CharacterCfg("Sam", "boy", "boy", "friend"),
}

PARENTS = {
    "mom": "mother",
    "dad": "father",
}

TICKETS = {
    "ticket": ObjectCfg("ticket", "ticket", "a ticket to the boat show", {"paper", "important"}),
    "blue_ticket": ObjectCfg("blue_ticket", "blue ticket", "a blue ticket with a star on it", {"paper", "important"}),
}

BUOYS = {
    "red_buoy": ObjectCfg("red_buoy", "red buoy", "a red buoy with chipped paint", {"water", "marker"}),
    "striped_buoy": ObjectCfg("striped_buoy", "striped buoy", "a striped buoy bobbing near the dock", {"water", "marker"}),
}

UNDERCLOTHES = {
    "socks": ObjectCfg("socks", "underclothes", "a line of underclothes drying on the balcony", {"cloth", "drying"}),
    "undershirt": ObjectCfg("undershirt", "underclothes", "an undershirt on the laundry line", {"cloth", "drying"}),
}

GADGETS = {
    "magnifier": ObjectCfg("magnifier", "magnifying glass", "a round magnifying glass", {"detective"}),
    "notebook": ObjectCfg("notebook", "little notebook", "a little notebook for clues", {"detective"}),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--child", choices=CHILDREN)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--ticket", choices=TICKETS)
    ap.add_argument("--buoy", choices=BUOYS)
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
    return [(s, t, b) for s in SETTINGS for t in TICKETS for b in BUOYS]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TICKETS:
        lines.append(asp.fact("ticket", tid))
    for bid in BUOYS:
        lines.append(asp.fact("buoy", bid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, T, B) :- setting(S), ticket(T), buoy(B).
"""


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.ticket is None or c[1] == args.ticket)
              and (args.buoy is None or c[2] == args.buoy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, ticket, buoy = rng.choice(sorted(combos))
    child = args.child or rng.choice(sorted(CHILDREN))
    friend = args.friend or rng.choice(sorted(FRIENDS))
    parent = args.parent or rng.choice(sorted(PARENTS))
    return StoryParams(setting, child, friend, parent, ticket, buoy)


def predict(world: World, ticket: Entity, buoy: Entity) -> dict:
    sim = world.copy()
    sim.get(ticket.id).memes["missing"] += 1
    sim.get(buoy.id).memes["noticed"] += 1
    return {
        "ticket_missing": sim.get(ticket.id).memes["missing"] >= THRESHOLD,
        "buoy_noticed": sim.get(buoy.id).memes["noticed"] >= THRESHOLD,
    }


def tell(setting: Setting, child: CharacterCfg, friend: CharacterCfg, parent: str,
         ticket: ObjectCfg, buoy: ObjectCfg) -> World:
    w = World(setting)
    kid = w.add(Entity(child.id, "character", child.gender, role="detective"))
    pal = w.add(Entity(friend.id, "character", friend.gender, role="friend"))
    grown = w.add(Entity(parent, "character", PARENTS[parent], role="parent", label=f"the {parent}"))
    tick = w.add(Entity(ticket.id, "thing", "thing", label=ticket.label))
    buoy_e = w.add(Entity(buoy.id, "thing", "thing", label=buoy.label))
    cloth = w.add(Entity("underclothes", "thing", "thing", label="underclothes"))
    gadget = w.add(Entity("notebook", "thing", "thing", label="little notebook"))

    kid.memes["curious"] += 1
    pal.memes["loyal"] += 1
    kid.memes["friendship"] += 1
    pal.memes["friendship"] += 1

    w.say(
        f"{kid.id} and {pal.id} were playing detective on {setting.place}. "
        f"{kid.id} carried {gadget.label}, and {pal.id} kept an eye on the path."
    )
    w.say(
        f"Near the fence, they noticed {cloth.label} on the line, {buoy.phrase}, "
        f"and a gap where {ticket.phrase} should have been."
    )
    w.say(
        f'"That is odd," said {pal.id}. "{buoy.label} does not belong by the laundry."'
    )
    w.para()
    kid.memes["foreshadowing"] += 1
    w.say(
        f"Earlier that morning, {kid.id} had seen {buoy.label} tied to a cart by the harbor. "
        f"That memory flickered back now like a clue waiting to be found."
    )
    pred = predict(w, tick, buoy_e)
    if pred["ticket_missing"]:
        kid.memes["focus"] += 1
        w.say(
            f'{kid.id} touched {kid.pronoun("possessive")} chin. '
            f'"The ticket must have blown away when someone carried the buoy."'
        )
    w.para()
    tick.meters["searched"] += 1
    buoy_e.meters["noticed"] += 1
    w.say(
        f"They followed the clue trail from the laundry line to the dock, where a trail of wet footprints led to the lost ticket."
    )
    w.say(
        f"Their {grown.label_word} came over, smiled, and lifted the ticket from a hook beside the boat rope."
    )
    w.say(
        f'"You found it," said {grown.id}. "And you found it together."'
    )
    w.say(
        f"{kid.id} grinned at {pal.id}. The two friends tucked the ticket safely into the notebook, and the red buoy bobbed quietly in the water again."
    )
    kid.memes["joy"] += 1
    pal.memes["joy"] += 1
    grown.memes["pride"] += 1
    w.facts.update(
        child=kid, friend=pal, parent=grown, ticket=tick, buoy=buoy_e, cloth=cloth,
        gadget=gadget, setting=setting, outcome="solved",
        flashback=True, foreshadowing=True, friendship=True,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a child-friendly detective story that includes the words underclothes, buoy, and ticket.",
        f"Tell a friendship mystery where {f['child'].id} and {f['friend'].id} solve a missing ticket case near the harbor.",
        "Use a flashback and a little foreshadowing to explain why a buoy becomes an important clue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid, pal, grown = f["child"], f["friend"], f["parent"]
    return [
        QAItem(
            question="What kind of story is this?",
            answer="It is a detective story about two friends following clues. They work together, notice small details, and solve a missing ticket mystery."
        ),
        QAItem(
            question="Why did the buoy matter?",
            answer="The buoy mattered because it was the clue that pointed them toward the dock. They had seen it earlier, so the flashback helped them remember where to look."
        ),
        QAItem(
            question="How did friendship help the case?",
            answer=f"{kid.id} and {pal.id} each noticed different clues, and they trusted each other. Working together helped them solve the mystery faster than either one could alone."
        ),
        QAItem(
            question="What was found at the end?",
            answer="The missing ticket was found safely by the boat rope. The friends put it away in the notebook, and the case was over."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a buoy?",
            answer="A buoy is a floating object in water that helps people notice a place or stay safe near boats."
        ),
        QAItem(
            question="What is a ticket?",
            answer="A ticket is a small paper that can show you are allowed to go somewhere or do something."
        ),
        QAItem(
            question="What are underclothes?",
            answer="Underclothes are clothes worn under other clothes, like an undershirt or socks."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], "",
             "== (2) Story questions =="]
    for item in sample.story_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
    lines += ["", "== (3) World-knowledge questions =="]
    for item in sample.world_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("harbor", "Nina", "Pip", "mom", "ticket", "red_buoy"),
    StoryParams("beach", "Milo", "Toby", "dad", "blue_ticket", "striped_buoy"),
    StoryParams("lake", "June", "Bea", "mom", "ticket", "striped_buoy"),
]


def generate(params: StoryParams) -> StorySample:
    w = tell(SETTINGS[params.setting], CHILDREN[params.child], FRIENDS[params.friend],
             params.parent, TICKETS[params.ticket], BUOYS[params.buoy])
    return StorySample(
        params=params,
        story=w.render(),
        prompts=generation_prompts(w),
        story_qa=story_qa(w),
        world_qa=world_knowledge_qa(w),
        world=w,
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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH between Python and ASP valid-combos:")
        if cl - py:
            print(" only in clingo:", sorted(cl - py))
        if py - cl:
            print(" only in python:", sorted(py - cl))
        return 1
    try:
        sample = generate(CURATED[0])
        assert sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print(f"OK: ASP parity and smoke test passed ({len(py)} combos).")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
