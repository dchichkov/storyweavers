#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/kindle_pollen_responsive_curiosity_happy_ending_slice.py
========================================================================================

A standalone storyworld for a gentle slice-of-life tale about curiosity,
springtime pollen, and a responsive grown-up who turns a small hiccup into a
happy ending.

Seed words: kindle, pollen, responsive
Style: slice of life
Features: curiosity, happy ending

The world is small on purpose:
- a child notices something new on an ordinary day,
- pollen causes a little problem,
- a responsive adult notices quickly and helps,
- the child learns something concrete,
- the ending proves the day improved.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/kindle_pollen_responsive_curiosity_happy_ending_slice.py
    python storyworlds/worlds/gpt-5.4-mini/kindle_pollen_responsive_curiosity_happy_ending_slice.py --all
    python storyworlds/worlds/gpt-5.4-mini/kindle_pollen_responsive_curiosity_happy_ending_slice.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/kindle_pollen_responsive_curiosity_happy_ending_slice.py --verify
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"pollen": 0.0, "dust": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "comfort": 0.0, "sneeze": 0.0, "relief": 0.0}

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
class Place:
    id: str
    label: str
    pollen_rich: bool = False
    cozy: bool = False

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
    kind: str
    helpful: bool = False

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
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}
        self.place: Optional[Place] = None

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        clone.place = copy.deepcopy(self.place)
        return clone


@dataclass
@dataclass
class StoryParams:
    place: str
    child_name: str
    child_gender: str
    parent_gender: str
    item: str
    aid: str
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


PLACES = {
    "window": Place("window", "the sunny window nook", pollen_rich=True, cozy=True),
    "garden": Place("garden", "the little garden bench", pollen_rich=True, cozy=False),
    "bakery": Place("bakery", "the bakery patio", pollen_rich=True, cozy=True),
    "porch": Place("porch", "the front porch", pollen_rich=True, cozy=True),
}

ITEMS = {
    "book": ObjectThing("book", "a picture book", "book", helpful=True),
    "flowers": ObjectThing("flowers", "a jar of fresh flowers", "flowers", helpful=True),
    "lemonade": ObjectThing("lemonade", "a cool glass of lemonade", "lemonade", helpful=True),
}

AIDS = {
    "tissue": ObjectThing("tissue", "a soft tissue", "tissue", helpful=True),
    "water": ObjectThing("water", "a sip of water", "water", helpful=True),
    "blanket": ObjectThing("blanket", "a light blanket", "blanket", helpful=True),
}

GIRL_NAMES = ["Lily", "Maya", "Nora", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Finn", "Theo", "Noah", "Leo", "Ben", "Max"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small slice-of-life storyworld about curiosity, pollen, and a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for i in ITEMS:
            for a in AIDS:
                combos.append((p, i, a))
    return combos


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for i in ITEMS:
        lines.append(asp.fact("item", i))
    for a in AIDS:
        lines.append(asp.fact("aid", a))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, I, A) :- place(P), item(I), aid(A).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def predict_pollen(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    if sim.place and sim.place.pollen_rich:
        child.meters["pollen"] += 1
        child.memes["sneeze"] += 1
    return {"sneeze": child.memes["sneeze"] >= THRESHOLD, "pollen": child.meters["pollen"]}


def tell(params: StoryParams) -> World:
    world = World()
    place = PLACES[params.place]
    world.place = place
    child = world.add(Entity("child", kind="character", type=params.child_gender, role="curious"))
    parent = world.add(Entity("parent", kind="character", type=params.parent_gender))
    item = world.add(Entity("item", type="thing", label=ITEMS[params.item].label))
    aid = world.add(Entity("aid", type="thing", label=AIDS[params.aid].label, attrs={"helpful": True}))

    child.memes["curiosity"] = 2.0
    parent.memes["comfort"] = 1.0

    world.say(
        f"One warm afternoon, {params.child_name} and {parent.label_word} sat at {place.label}. "
        f"On the table was {item.label}, and the day felt calm and ordinary."
    )
    world.say(
        f"{params.child_name} noticed tiny specks on the sunlight and asked, "
        f'"What is that floating around?" {parent.label_word.capitalize()} smiled. '
        f'"That is pollen," {parent.pronoun()} said, and the question kindled {params.child_name}\'s curiosity.'
    )

    world.para()
    world.say(
        f"{params.child_name} leaned closer to the bright air to look, and a little cloud of pollen drifted up. "
        f"{params.child_name} sneezed once, then blinked with watery eyes."
    )
    child.meters["pollen"] += 1
    child.memes["sneeze"] += 1

    if place.pollen_rich:
        world.say("The air outside was full of spring pollen, so the sneeze came quickly.")

    world.para()
    pred = predict_pollen(world)
    world.facts["predicted"] = pred
    if pred["sneeze"]:
        world.say(
            f"{parent.label_word.capitalize()} was responsive right away. "
            f"{parent.pronoun().capitalize()} handed over {aid.label}, brought {params.child_name} a sip of water, "
            f"and moved the two of them a little farther from the flowers."
        )
        child.memes["relief"] += 2
        child.memes["comfort"] += 2
        child.meters["pollen"] = 0.0
        world.say(
            f"The sneeze settled down, the eyes stopped stinging, and {params.child_name} could breathe easily again."
        )
    else:
        world.say(f"{parent.label_word.capitalize()} listened and stayed close, but nothing more was needed.")

    world.para()
    world.say(
        f"After that, {params.child_name} looked at the floating specks with a new kind of curiosity. "
        f"{parent.label_word.capitalize()} opened {item.label} and read a few pages while the breeze moved softly through the {place.label}."
    )
    world.say(
        f"It was still a normal afternoon, only now {params.child_name} knew a little more about the world, "
        f"and the day ended with a calm smile instead of a sneezy frown."
    )

    world.facts.update(
        child=child,
        parent=parent,
        item=item,
        aid=aid,
        place=place,
        outcome="happy",
    )
    return world


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    place = f["place"]
    item = f["item"]
    aid = f["aid"]
    return [
        (
            "What made the child curious?",
            f"The child noticed pollen floating in the sunlight and wanted to know what it was. That little question kindled the child's curiosity right away."
        ),
        (
            "Why did the child sneeze?",
            f"The air around {place.label} had lots of pollen in it, so the child sneezed when the specks drifted up. The sneeze happened because the day was full of spring pollen."
        ),
        (
            "How did the parent help?",
            f"{parent.label_word.capitalize()} was responsive and quickly handed over {aid.label}. {parent.label_word.capitalize()} also gave water and moved the child a little away from the flowers, which helped the sneeze settle down."
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.facts["place"]
    return [
        f'Write a slice-of-life story for a young child that includes the word "pollen" and takes place at {p.label}.',
        f'Tell a gentle story where curiosity is kindled by a small question about pollen, and a responsive grown-up helps quickly.',
        f'Write a happy-ending story with ordinary details, a sneeze, and a calm solution that includes the word "kindle".',
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is pollen?", "Pollen is a very tiny powder that comes from flowers and plants. It can float in the air in spring."),
        ("Why do some people sneeze around pollen?", "Pollen can tickle a person's nose and eyes. When that happens, they may sneeze or rub their eyes."),
        ("What does responsive mean?", "Responsive means noticing a problem quickly and answering or helping right away."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        out.append(f"{i}. {q}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: meters={e.meters} memes={e.memes} attrs={e.attrs}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place or args.item or args.aid:
        combos = [c for c in combos if (args.place is None or c[0] == args.place) and (args.item is None or c[1] == args.item) and (args.aid is None or c[2] == args.aid)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item, aid = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place, name, gender, parent, item, aid)


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
    import asp
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP gate matches Python valid_combos().")
    else:
        print("MISMATCH: ASP and Python disagree.")
        return 1
    try:
        generate(resolve_params(argparse.Namespace(place=None, item=None, aid=None, name=None, gender=None, parent=None), random.Random(7)))
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: generation smoke test passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("window", "Lily", "girl", "mother", "book", "tissue"),
            StoryParams("garden", "Noah", "boy", "father", "flowers", "water"),
            StoryParams("porch", "Maya", "girl", "mother", "lemonade", "blanket"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
