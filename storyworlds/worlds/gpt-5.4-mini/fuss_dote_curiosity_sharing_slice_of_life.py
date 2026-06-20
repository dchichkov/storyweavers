#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fuss_dote_curiosity_sharing_slice_of_life.py
=============================================================================

A small, slice-of-life storyworld about a curious child, a careful grown-up,
and a tiny sharing moment that turns a fuss into a calm dote.

Seed words: fuss, dote
Features: Curiosity, Sharing
Style: Slice of Life
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

# Make shared result containers importable when run directly.
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {"order": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"curiosity": 0.0, "fuss": 0.0,
                                                             "dote": 0.0, "warmth": 0.0})

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
class Place:
    id: str
    label: str
    mood: str
    shared_spot: str
    cozy_detail: str

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
class Item:
    id: str
    label: str
    phrase: str
    shareable: bool = True
    plural: bool = False

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
class Treat:
    id: str
    label: str
    phrase: str
    crumbs: str
    shareable: bool = True

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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone.facts = copy.deepcopy(self.facts)
        clone.place = copy.deepcopy(self.place)
        return clone


@dataclass
@dataclass
class StoryParams:
    place: str
    child_name: str
    child_gender: str
    grownup_name: str
    grownup_gender: str
    item: str
    treat: str
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
    "kitchen": Place("kitchen", "the kitchen", "sunlit and busy", "the counter", "a clean table"),
    "living_room": Place("living_room", "the living room", "soft and quiet", "the rug", "a little couch"),
    "porch": Place("porch", "the porch", "breezy and bright", "the step", "a low chair"),
}

ITEMS = {
    "picture_book": Item("picture_book", "picture book", "a picture book with big pages"),
    "toy_tea_set": Item("toy_tea_set", "toy tea set", "a little toy tea set"),
    "puzzle": Item("puzzle", "puzzle", "a puzzle with shiny pieces"),
    "crayons": Item("crayons", "crayons", "a box of crayons", plural=True),
}

TREATS = {
    "cookies": Treat("cookies", "cookies", "warm cookies", "sweet crumbs"),
    "berries": Treat("berries", "berries", "a bowl of berries", "tiny purple stains"),
    "milk": Treat("milk", "milk", "a cup of milk", "little white drips"),
}

CHILD_NAMES = ["Mia", "Noah", "Ivy", "Leo", "Nora", "Finn", "Luna", "Ava"]
GROWNUP_NAMES = ["Mom", "Dad", "Aunt May", "Grandma Jo"]
TRUTHS = ["curious", "careful", "gentle", "patient", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for item in ITEMS:
            for treat in TREATS:
                combos.append((place, item, treat))
    return combos


def fuss_risk(item: Item, treat: Treat) -> bool:
    return item.shareable and treat.shareable


def predict_spill(world: World, child: Entity, item: Item, treat: Treat) -> dict:
    sim = world.copy()
    sim.get(child.id).memes["fuss"] += 1
    sim.get(child.id).memes["curiosity"] += 1
    return {
        "spotted": fuss_risk(item, treat),
        "spill": item.shareable and treat.shareable,
    }


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    for child in world.characters():
        if child.memes["fuss"] < THRESHOLD:
            continue
        sig = ("settle", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child.memes["warmth"] += 1
        out.append("__settle__")
    return out


CAUSAL_RULES = [_r_settle]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    speeches: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule(world)
            if s:
                changed = True
                speeches.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for s in speeches:
            world.say(s)


def introduce(world: World, child: Entity, grownup: Entity, place: Place) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} was a {child.traits[0]} little {child.type} who liked to notice "
        f"every small thing at {place.label}."
    )
    world.say(
        f"{grownup.id} liked to {grownup.attrs.get('care', 'look after little things')} "
        f"and always seemed to know where the snacks and napkins were."
    )


def setup_scene(world: World, place: Place, treat: Treat, item: Item) -> None:
    world.say(
        f"One afternoon, the family was at {place.label}. The air felt {place.mood}, "
        f"and {place.cozy_detail} sat nearby."
    )
    world.say(
        f"On the {place.shared_spot}, there was {treat.phrase}, and beside it rested "
        f"{item.phrase}."
    )


def wonder(world: World, child: Entity, item: Item, treat: Treat) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} leaned close and asked, \"Why is {treat.label} next to the {item.label}?\""
    )
    world.say(
        f"The question made a little fuss inside {child.pronoun('possessive')} chest, "
        f"because {child.pronoun()} wanted to touch everything at once."
    )


def warning(world: World, grownup: Entity, child: Entity, item: Item, treat: Treat) -> None:
    pred = predict_spill(world, child, item, treat)
    if pred["spill"]:
        grownup.memes["dote"] += 1
        world.say(
            f"{grownup.id} smiled and shook {grownup.pronoun('possessive')} head. "
            f"\"Careful,\" {grownup.pronoun()} said. \"If we rush, the {item.label} could "
            f"get messy, and then we would all have more work.\""
        )


def fuss(world: World, child: Entity, item: Item, treat: Treat) -> None:
    child.memes["fuss"] += 1
    world.say(
        f"{child.id} started to fuss and reached for the {item.label} with sticky fingers."
    )
    world.say(
        f"For a moment, the room felt too small for {child.pronoun('possessive')} big idea."
    )


def dote_offer(world: World, grownup: Entity, child: Entity, item: Item, treat: Treat) -> None:
    grownup.memes["dote"] += 1
    grownup.memes["warmth"] += 1
    world.say(
        f"Then {grownup.id} dote-said, \"Let's share nicely. You can help me carry "
        f"one {item.label} first, and I will hold the {treat.label}.\""
    )


def share(world: World, grownup: Entity, child: Entity, item: Item, treat: Treat) -> None:
    child.memes["fuss"] = 0.0
    child.memes["warmth"] += 1
    grownup.memes["warmth"] += 1
    world.say(
        f"{child.id} took a breath and nodded. Together they shared the work: "
        f"{grownup.id} passed over the {item.label}, and {child.id} carried it carefully."
    )
    world.say(
        f"After that, they split the {treat.label} into a small plate, so nobody had to hurry."
    )


def ending_image(world: World, child: Entity, grownup: Entity, place: Place, item: Item, treat: Treat) -> None:
    world.say(
        f"By the end, the {item.label} sat neat again, the {treat.label} was shared, "
        f"and {child.id} was smiling at {grownup.id} beside {place.label}."
    )
    world.say(
        f"It was a quiet little day, the kind where a fuss turns into a kind dote "
        f"and everyone feels closer."
    )


def tell(params: StoryParams) -> World:
    world = World()
    place = PLACES[params.place]
    item = ITEMS[params.item]
    treat = TREATS[params.treat]
    world.place = place
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender,
                             traits=[rng_trait for rng_trait in [random.choice(TRUTHS)]],
                             attrs={"curious": True}))
    grownup = world.add(Entity(id=params.grownup_name, kind="character", type=params.grownup_gender,
                               role="grownup", attrs={"care": "dote over the snacks"}))
    introduce(world, child, grownup, place)
    world.para()
    setup_scene(world, place, treat, item)
    wonder(world, child, item, treat)
    warning(world, grownup, child, item, treat)
    fuss(world, child, item, treat)
    dote_offer(world, grownup, child, item, treat)
    share(world, grownup, child, item, treat)
    world.para()
    ending_image(world, child, grownup, place, item, treat)
    world.facts.update(child=child, grownup=grownup, place=place, item=item, treat=treat)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, grownup, place, item, treat = f["child"], f["grownup"], f["place"], f["item"], f["treat"]
    return [
        f"Write a slice-of-life story for a young child that includes the words fuss and dote.",
        f"Tell a gentle everyday story where {child.id} is curious about {treat.label} and {item.label}, then shares nicely with {grownup.id}.",
        f"Write a simple home story about curiosity and sharing at {place.label} that ends with a calm, happy feeling.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, grownup, place, item, treat = f["child"], f["grownup"], f["place"], f["item"], f["treat"]
    return [
        QAItem(
            question=f"Why did {child.id} start to fuss?",
            answer=(
                f"{child.id} started to fuss because {child.pronoun()} was very curious and wanted to touch the {item.label} right away. "
                f"{grownup.id} helped by slowing the moment down and offering a way to share instead."
            ),
        ),
        QAItem(
            question=f"How did {grownup.id} help at the end?",
            answer=(
                f"{grownup.id} helped by dote-offering a calmer plan and sharing the work with {child.id}. "
                f"That turned the big urge into a gentle job they could do together."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"It ended with the {item.label} tidy again and the {treat.label} shared on a small plate. "
                f"{child.id} and {grownup.id} were smiling beside {place.label}, which shows the fuss had settled down."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to be curious?",
            answer="Being curious means wanting to know more, ask questions, and look closely at things.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something with you, or taking turns so both people can have some.",
        ),
        QAItem(
            question="What is a fuss?",
            answer="A fuss is a noisy upset moment when someone wants something right away or feels restless.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story Q&A ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge Q&A ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "Mia", "girl", "Mom", "mother", "picture_book", "cookies"),
    StoryParams("living_room", "Noah", "boy", "Dad", "father", "toy_tea_set", "berries"),
    StoryParams("porch", "Ivy", "girl", "Grandma Jo", "woman", "crayons", "milk"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about curiosity, fuss, and sharing.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name", help="child name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=["Mom", "Dad", "Aunt May", "Grandma Jo"])
    ap.add_argument("--grownup-gender", choices=["mother", "father", "woman", "man"])
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--treat", choices=TREATS)
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
    if args.item and args.treat and not fuss_risk(ITEMS[args.item], TREATS[args.treat]):
        raise StoryError("No story: this item and treat do not create a meaningful fuss.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)
              and (args.treat is None or c[2] == args.treat)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item, treat = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES)
    grownup = args.grownup or rng.choice(GROWNUP_NAMES)
    grownup_gender = args.grownup_gender or rng.choice(["mother", "father", "woman", "man"])
    return StoryParams(place, name, gender, grownup, grownup_gender, item, treat)


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


ASP_RULES = r"""
fuss_risk(I, T) :- item(I), treat(T).
valid(P, I, T) :- place(P), item(I), treat(T), fuss_risk(I, T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for i in ITEMS:
        lines.append(asp.fact("item", i))
    for t in TREATS:
        lines.append(asp.fact("treat", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib

    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid combo sets differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        emit(sample, trace=False, qa=False)
    if not buf.getvalue().strip():
        print("SMOKE TEST FAILED: emit produced no output.")
        rc = 1
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos.")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
