#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/chinese_abbey_meet_sharing_fable.py
===============================================================================================================

A small fable-style storyworld about a child, a friendly abbey garden, a meeting,
and the wisdom of sharing Chinese treats.
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
    phrase: str = ""
    role: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wears: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    scent: str
    allows: set[str] = field(default_factory=set)
    calm: str = ""


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    taste: str
    sharing_easy: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class ShareTool:
    id: str
    label: str
    phrase: str
    helps: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: str = place.id

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class StoryParams:
    place: str
    treat: str
    tool: str
    child: str
    helper: str
    seed: Optional[int] = None


PLACES = {
    "abbey_garden": Place("abbey_garden", "the abbey garden", "stone and mint", {"meet", "share"}, "The garden felt quiet and kind."),
    "abbey_kitchen": Place("abbey_kitchen", "the abbey kitchen", "warm tea and rice", {"meet", "share"}, "The kitchen hummed softly."),
    "abbey_hall": Place("abbey_hall", "the abbey hall", "wax and bread", {"meet", "share"}, "The hall made every footstep gentle."),
    "abbey_gate": Place("abbey_gate", "the abbey gate", "rain on old wood", {"meet", "share"}, "The gate stood open to travelers."),
}

TREATS = {
    "dumplings": Treat("dumplings", "a basket of dumplings", "fresh dumplings", "savory and soft", True, {"chinese", "food"}),
    "noodles": Treat("noodles", "a bowl of noodles", "steaming noodles", "slippery and warm", True, {"chinese", "food"}),
    "tea_cakes": Treat("tea_cakes", "tea cakes", "little tea cakes", "sweet and crumbly", True, {"tea", "food"}),
    "rice_puffs": Treat("rice_puffs", "rice puffs", "crispy rice puffs", "light and crunchy", True, {"chinese", "food"}),
    "oranges": Treat("oranges", "orange slices", "bright orange slices", "juicy and bright", True, {"fruit"}),
}

TOOLS = {
    "bowl": ShareTool("bowl", "a big bowl", "a big bowl", "kept things from spilling", {"share"}),
    "cloth": ShareTool("cloth", "a clean cloth", "a clean cloth", "made a neat picnic corner", {"share"}),
    "tray": ShareTool("tray", "a flat tray", "a flat tray", "held enough for everyone", {"share"}),
    "bench": ShareTool("bench", "a long bench", "a long bench", "gave everyone a place to sit", {"share"}),
}

CHILD_NAMES = ["Mina", "Jun", "Lina", "Kai", "Anya", "Tao", "Maya", "Bo"]
HELPER_NAMES = ["Brother Eli", "Sister Ruth", "Brother Sam", "Sister Mei"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, t, u) for p in PLACES for t in TREATS for u in TOOLS if t in {"dumplings", "noodles", "rice_puffs", "tea_cakes", "oranges"}]


def make_world(params: StoryParams) -> World:
    place = PLACES.get(params.place)
    treat = TREATS.get(params.treat)
    tool = TOOLS.get(params.tool)
    if not place or not treat or not tool:
        raise StoryError("Unknown story choices.")
    if "share" not in place.allows:
        raise StoryError("This place does not fit a sharing fable.")
    if not treat.sharing_easy:
        raise StoryError("That treat would not fit a sharing story.")
    world = World(place)
    child = world.add(Entity(id=params.child, kind="character", type="child", label=params.child, role="seeker"))
    helper = world.add(Entity(id=params.helper, kind="character", type="adult", label=params.helper, role="helper"))
    snack = world.add(Entity(id="snack", type="thing", label=treat.label, phrase=treat.phrase, owner=child.id, caretaker=helper.id, plural=True))
    utensil = world.add(Entity(id="utensil", type="thing", label=tool.label, phrase=tool.phrase))
    world.facts.update(child=child, helper=helper, snack=snack, utensil=utensil, treat=treat, tool=tool, place=place)
    return world


def _r_share(world: World) -> list[str]:
    child = world.facts["child"]
    snack = world.facts["snack"]
    if child.memes["sharing"] < THRESHOLD:
        return []
    sig = ("share", snack.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    snack.meters["shared"] += 1
    return ["__shared__"]


def propagate(world: World, narrate: bool = True) -> None:
    out = _r_share(world)
    if narrate:
        for s in out:
            if s != "__shared__":
                world.say(s)


ASP_RULES = r"""
shared(S) :- child_share(C,S).
valid(P,T,U) :- place(P), treat(T), tool(U), allowed(P,meet), allowed(P,share).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.allows):
            lines.append(asp.fact("allowed", pid, a))
    for tid in TREATS:
        lines.append(asp.fact("treat", tid))
    for uid in TOOLS:
        lines.append(asp.fact("tool", uid))
    lines.append(asp.fact("allowed", "abbey_garden", "meet"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def story_text(world: World) -> None:
    child = world.facts["child"]
    helper = world.facts["helper"]
    treat = world.facts["treat"]
    tool = world.facts["tool"]
    place = world.facts["place"]
    child.memes["want"] += 1
    world.say(f"{child.id} came to {place.label} and noticed {treat.phrase} waiting by {tool.phrase}.")
    world.say(f"The air smelled of {place.scent}, and {child.id} wanted to meet someone kind there.")
    world.para()
    world.say(f"Then {helper.id} arrived with a calm smile and asked if {child.id} would share.")
    world.say(f"{child.id} held the bowl close at first, because it looked so tasty.")
    child.memes["sharing"] += 1
    propagate(world, narrate=False)
    world.para()
    world.say(f"{child.id} nodded and let the food go around. {helper.id} used {tool.label_word if hasattr(tool, 'label_word') else tool.label} to keep it neat.")
    world.say(f"Soon the {treat.label} were passed in small pieces, and {child.id} and {helper.id} met each other's eyes with warm smiles.")
    world.say(f"At the end, the bowl was lighter, and the abbey garden felt brighter than before.")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for a young child that uses the words "chinese", "abbey", and "meet".',
        f"Tell a gentle story in an abbey where {f['child'].id} learns to share {f['treat'].phrase} with {f['helper'].id}.",
        f"Write a child-facing fable about meeting in {f['place'].label} and discovering that sharing makes the meal better.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c, h, t, p = f["child"], f["helper"], f["treat"], f["place"]
    return [
        QAItem(
            question=f"Where did {c.id} and {h.id} meet?",
            answer=f"They met in {p.label}. It was a calm place, so the meeting could turn into a sharing lesson.",
        ),
        QAItem(
            question=f"What did {c.id} learn to do with {t.label}?",
            answer=f"{c.id} learned to share it. Once {c.id} shared the food, the meal felt warmer and friendlier for everyone.",
        ),
        QAItem(
            question=f"Why did the story include the word chinese?",
            answer=f"It pointed to the kind of food being shared, like dumplings or noodles. That made the fable feel specific instead of vague.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is an abbey?", "An abbey is a quiet place where people live, pray, and work together."),
        QAItem("What does it mean to meet?", "To meet means to come together and see one another in the same place."),
        QAItem("What is sharing?", "Sharing means giving some of what you have so another person can enjoy it too."),
    ]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable about sharing in an abbey.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child")
    ap.add_argument("--helper")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.treat:
        combos = [c for c in combos if c[1] == args.treat]
    if args.tool:
        combos = [c for c in combos if c[2] == args.tool]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, treat, tool = rng.choice(sorted(combos))
    child = args.child or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(place=place, treat=treat, tool=tool, child=child, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    story_text(world)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            print(e.id, meters, memes)
    if qa:
        print()
        for section, items in (("prompts", sample.prompts), ("story", sample.story_qa), ("world", sample.world_qa)):
            print(f"== {section} ==")
            if section == "prompts":
                for i, q in enumerate(items, 1):
                    print(f"{i}. {q}")
            else:
                for item in items:
                    print(f"Q: {item.question}\nA: {item.answer}")


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH")
        print("only python", sorted(py - cl))
        print("only clingo", sorted(cl - py))
        return 1
    try:
        sample = generate(StoryParams(place="abbey_garden", treat="dumplings", tool="bowl", child="Mina", helper="Brother Eli"))
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print(f"OK: {len(py)} combos; smoke test passed.")
    return 0


CURATED = [
    StoryParams(place="abbey_garden", treat="dumplings", tool="bowl", child="Mina", helper="Brother Eli"),
    StoryParams(place="abbey_kitchen", treat="noodles", tool="cloth", child="Jun", helper="Sister Mei"),
    StoryParams(place="abbey_hall", treat="rice_puffs", tool="tray", child="Lina", helper="Brother Sam"),
    StoryParams(place="abbey_gate", treat="tea_cakes", tool="bench", child="Kai", helper="Sister Ruth"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    rng_base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(rng_base + i))
            params.seed = rng_base + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
