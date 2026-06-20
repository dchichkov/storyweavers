#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/potent_cinnamon_lid_dialogue_misunderstanding_repetition_heartwarming.py
===========================================================================================================

A small heartwarming storyworld about a child, a grandparent, and a kitchen
mix-up with a jar of cinnamon. The core seed is a polite misunderstanding:
someone thinks "potent" means "too strong to use," while someone else means
"powerful in a good way." Repetition and dialogue carry the resolution.

This script is self-contained, uses only the stdlib, and follows the shared
Storyweavers contract.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Vessel:
    id: str
    label: str
    phrase: str
    has_lid: bool = True
    openable: bool = True
    fragrance: str = ""
    comforting: bool = False
    gentle_use: str = ""

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
class Event:
    id: str
    text: str

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
        self.events: list[Event] = []
        self.fired: set[str] = set()
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.events = copy.deepcopy(self.events)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    # Only one simple causal rule: opening the lid lets the cinnamon aroma spread.
    if "cinnamon_open" in world.fired:
        return []
    if world.facts.get("lid_open"):
        world.fired.add("cinnamon_open")
        world.get("jar").meters["aroma"] += 1
        world.get("child").memes["curiosity"] += 1
        out.append("A warm cinnamon smell drifted across the kitchen.")
    if narrate:
        for line in out:
            world.say(line)
    return out


def _story_titles() -> list[str]:
    return ["potent", "cinnamon", "lid"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming storyworld about a potent cinnamon jar and a lid misunderstanding."
    )
    ap.add_argument("--theme", choices=["kitchen"], default="kitchen")
    ap.add_argument("--word1", choices=["potent"], default="potent")
    ap.add_argument("--word2", choices=["cinnamon"], default="cinnamon")
    ap.add_argument("--word3", choices=["lid"], default="lid")
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


@dataclass
@dataclass
class StoryParams:
    theme: str
    child_name: str
    child_gender: str
    adult_name: str
    adult_gender: str
    vessel: str
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


KIDS = [("Mia", "girl"), ("Nico", "boy"), ("Tia", "girl"), ("Owen", "boy")]
ADULTS = [("Grandma", "grandmother"), ("Grandpa", "grandfather"), ("Aunt June", "woman")]
VESSELS = {
    "jar": Vessel("jar", "jar", "a little jar of cinnamon", has_lid=True, openable=True,
                  fragrance="warm and spicy", comforting=True, gentle_use="sprinkle it on toast"),
}

CURATED = [
    StoryParams("kitchen", "Mia", "girl", "Grandma", "grandmother", "jar"),
    StoryParams("kitchen", "Nico", "boy", "Grandpa", "grandfather", "jar"),
]


def valid_combos() -> list[tuple[str, str]]:
    return [("kitchen", "jar")]


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("theme", "kitchen"),
        asp.fact("vessel", "jar"),
        asp.fact("has_lid", "jar"),
        asp.fact("openable", "jar"),
    ])


ASP_RULES = r"""
valid(T,V) :- theme(T), vessel(V), has_lid(V), openable(V).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH: ASP gate differs from Python.")
    try:
        generate(CURATED[0])
    except Exception as e:
        ok = False
        print(f"MISMATCH: normal generate() crashed: {e}")
    if ok:
        print("OK: ASP parity and smoke test passed.")
        return 0
    return 1


def tell(params: StoryParams) -> World:
    w = World()
    child = w.add(Entity("child", "character", params.child_gender, params.child_name, role="child"))
    adult = w.add(Entity("adult", "character", params.adult_gender, params.adult_name, role="adult"))
    jar = w.add(Entity("jar", "thing", "jar", "the cinnamon jar"))

    w.facts.update(child=child, adult=adult, jar=jar, lid_open=False)

    child.memes["curiosity"] += 1
    adult.memes["warmth"] += 1

    w.say(f"On a quiet morning, {child.id} and {adult.id} stood in the kitchen by a small counter.")
    w.say(
        f"{child.id} pointed at {jar.label_word} and asked, "
        f'"Is it really { _story_titles()[0] } enough to need a careful lid?"'
    )
    w.say(
        f'{adult.id} smiled. "Potent means strong," {adult.id} said. '
        f'"It can be strong in a good way too."'
    )

    w.para()
    w.say(
        f"{child.id} looked uncertain. '{_story_titles()[1]} is such a big word,' "
        f"{child.id} said. 'Maybe it means the jar should stay shut forever.'"
    )
    w.say(
        f"{adult.id} shook {adult.pronoun('possessive')} head gently. "
        f'"No, sweetheart. The { _story_titles()[2] } keeps it fresh. We can open it a little, not a lot."'
    )
    w.say(f'{child.id} asked, "A little?"')
    w.say(f'{adult.id} repeated, "A little. Just a little."')

    w.para()
    w.facts["lid_open"] = True
    jar.meters["opened"] += 1
    propagate(w, narrate=True)

    w.say(
        f'{child.id} leaned closer and sniffed. "It smells like warm cookies," '
        f'{child.id} said.'
    )
    w.say(
        f'{adult.id} laughed softly. "That is exactly why we keep it in a jar with a lid."'
    )
    w.say(
        f'Together they sprinkled a tiny bit on toast. The kitchen smelled sweet, and '
        f'{child.id} grinned at the tiny brown dust that had turned breakfast kind.'
    )
    w.say(
        f'"Potent can be nice," {child.id} said. "And a lid can be kind too."'
    )
    w.say(
        f'"Exactly," {adult.id} said, and they ate their toast side by side.'
    )

    w.facts.update(outcome="warm", repetition=True, misunderstanding=True)
    return w


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a heartwarming story for a young child that includes the words "potent", "cinnamon", and "lid".',
        'Tell a gentle story with dialogue where a child misunderstands the word "potent" but a grown-up explains it kindly.',
        'Write a cozy kitchen story that uses repetition like "A little. Just a little." and ends happily.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    c = world.facts["child"]
    a = world.facts["adult"]
    jar = world.facts["jar"]
    qa = [
        ("What did the child think at first?",
         f"{c.id} thought the jar might need to stay closed forever because the word potent sounded very serious. That was a misunderstanding about what the word meant."),
        ("How did the grown-up explain potent?",
         f"{a.id} explained that potent means strong, and that strong can be good. The cinnamon was potent because it had a warm, rich smell and flavor."),
        ("What did they repeat?",
         'They repeated, "A little. Just a little." That helped them open the lid carefully without making a mess.'),
        ("How did the story end?",
         f"They sprinkled a tiny bit of cinnamon on toast and shared breakfast together. The lid kept the jar fresh, and the kitchen felt cozy and kind."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is cinnamon?",
         "Cinnamon is a warm, sweet spice that people often use in baking and breakfast foods."),
        ("What does a lid do?",
         "A lid covers a jar or container so the food inside stays protected and fresh."),
        ("What does potent mean?",
         "Potent means strong or powerful. A smell, taste, or tool can be potent if it has a strong effect."),
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
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.theme != "kitchen":
        raise StoryError("This tiny world only supports a kitchen setting.")
    child_name, child_gender = rng.choice(KIDS)
    adult_name, adult_gender = rng.choice(ADULTS)
    return StoryParams("kitchen", child_name, child_gender, adult_name, adult_gender, "jar")


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
        print("compatible combos:")
        for t, v in asp_valid_combos():
            print(f"  {t} {v}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
