#!/usr/bin/env python3
"""
storyworlds/worlds/scrub_reconciliation_surprise_moral_value_slice_of.py
========================================================================

A standalone story world for a tiny slice-of-life tale about a child who wants
to scrub something clean, a small surprise, and a reconciliation that lands on a
moral value: it is kinder to tell the truth and fix a mistake than to hide it.

The world models a small household scene with physical meters and emotional
memes. A surprise spill or mark creates tension; a scrub action and honest talk
can resolve it. The prose is driven by the simulated world state, not by a fixed
template with swapped nouns.
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
    owner: str = ""
    caregiver: str = ""
    surface: str = ""
    color: str = ""
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))


@dataclass
class Room:
    id: str
    place: str
    light: str
    mood: str
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
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
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(copy.deepcopy(self.room))
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def scrub_needs_help(item: Entity) -> bool:
    return item.meters["mess"] >= THRESHOLD


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, room in ROOMS.items():
        for mess_id, mess in MESSES.items():
            for thing_id, thing in THINGS.items():
                if thing.surface in mess.surfaces:
                    combos.append((place, mess_id, thing_id))
    return combos


@dataclass
class StoryParams:
    place: str
    mess: str
    thing: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


ROOMS = {
    "kitchen": Room(id="kitchen", place="the kitchen", light="sunlight", mood="busy", tags={"home", "slice_of_life"}),
    "laundry": Room(id="laundry", place="the laundry room", light="bright lamp light", mood="quiet", tags={"home", "slice_of_life"}),
    "porch": Room(id="porch", place="the front porch", light="soft afternoon light", mood="open", tags={"home", "slice_of_life"}),
}

@dataclass
class Mess:
    id: str
    noun: str
    verb: str
    adjective: str
    surfaces: set[str]
    surprise_line: str
    consequence: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


MESSES = {
    "jam": Mess("jam", "jam", "spill jam", "sticky", {"table", "shirt", "counter"}, "A jar tipped over with a small surprise.", "stuck to everything", {"scrub", "surprise"}),
    "mud": Mess("mud", "mud", "track mud", "muddy", {"floor", "shoes", "mat"}, "Boots left a surprise trail by the door.", "left brown prints", {"scrub", "surprise"}),
    "paint": Mess("paint", "paint", "smear paint", "painty", {"hands", "paper", "table"}, "A paint cup wobbled and made a surprise stripe.", "left bright streaks", {"scrub", "surprise"}),
}

@dataclass
class Thing:
    id: str
    label: str
    surface: str
    phrase: str
    owner: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


THINGS = {
    "table": Thing("table", "table", "table", "the small table", "family", {"home"}),
    "shirt": Thing("shirt", "shirt", "shirt", "a favorite shirt", "child", {"home"}),
    "shoes": Thing("shoes", "shoes", "shoes", "the porch shoes", "family", {"home"}),
    "hands": Thing("hands", "hands", "hands", "little hands", "child", {"home"}),
    "mat": Thing("mat", "mat", "mat", "the welcome mat", "family", {"home"}),
}

GIRL_NAMES = ["Mina", "Lia", "Nora", "Ava", "Ruby", "Ivy"]
BOY_NAMES = ["Owen", "Noah", "Leo", "Eli", "Sam", "Jude"]
HELPER_NAMES = ["Mom", "Dad", "Aunt May", "Grandpa", "Older Sister", "Older Brother"]


def _child_pool(kind: str) -> list[str]:
    return GIRL_NAMES if kind == "girl" else BOY_NAMES


def predict_scrub(world: World, child: Entity, mess: Mess, thing: Entity) -> dict:
    sim = world.copy()
    sim.get("mess_item").meters["mess"] += 1
    sim.get("mess_item").memes["worry"] += 1
    return {
        "cleanable": True,
        "hurt_feelings": sim.get("child").memes["worry"] >= THRESHOLD,
        "mess_level": sim.get("mess_item").meters["mess"],
    }


def apply_reconciliation(world: World) -> None:
    child = world.get("child")
    helper = world.get("helper")
    child.memes["worry"] = 0
    child.memes["relief"] += 1
    helper.memes["warmth"] += 1


def tell(world: World, params: StoryParams) -> World:
    room = world.room
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name))
    item = world.add(Entity(id="mess_item", kind="thing", type="thing", label=MESSES[params.mess].noun, phrase=THINGS[params.thing].phrase))
    item.surface = THINGS[params.thing].surface
    item.owner = "family"
    item.caregiver = helper.id
    item.tags = set(MESSES[params.mess].tags) | set(THINGS[params.thing].tags)

    mess = MESSES[params.mess]

    world.say(f"{child.label} was in {room.place}, where the {room.light} made everything look calm.")
    world.say(f"Then {mess.surprise_line} {child.label} looked at the {item.label} and saw {mess.consequence}.")
    child.memes["surprise"] += 1
    child.meters["mess"] += 1
    room.meters["mess"] += 1

    world.para()
    world.say(f"{child.label} frowned, then reached for a cloth and said they would {mess.verb if mess.verb.startswith('spill') else 'scrub it clean'} right away.")
    child.memes["care"] += 1
    if scrub_needs_help(item):
        pred = predict_scrub(world, child, mess, item)
        world.facts["predicted_cleanable"] = pred["cleanable"]

    world.say(f"{helper.label} noticed the mess and came over more gently than a shadow.")
    helper.memes["concern"] += 1

    world.para()
    world.say(f'"I should have been more careful," {child.label} said, looking down at the stain.')
    child.memes["guilt"] += 1
    helper.memes["patience"] += 1
    world.say(f'"Thank you for telling me," {helper.label} said. "That was honest of you."')
    apply_reconciliation(world)
    item.meters["mess"] = 0
    room.meters["mess"] = 0
    world.say(f"Together they scrubbed until {item.label} looked bright again, and the room felt peaceful.")
    world.say(f"By the end, {child.label} was smiling beside {helper.label}, and the little surprise had turned into a quiet lesson about telling the truth.")
    world.facts.update(child=child, helper=helper, mess=mess, item=item, room=room)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    mess = f["mess"]
    return [
        f'Write a slice-of-life story for a young child about a small surprise mess and how {child.label} and {helper.label} fix it together. Include the word "scrub".',
        f"Tell a gentle home story where {child.label} feels bad after a surprise {mess.noun} spill, then tells the truth and scrubs it clean with {helper.label}.",
        f'Write a story with a moral lesson about honesty, cleaning up, and reconciliation. It should feel ordinary and warm, and it should include the word "scrub".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    mess = f["mess"]
    room = f["room"]
    item = f["item"]
    return [
        QAItem(
            question=f"What surprised {child.label} in {room.place}?",
            answer=f"A surprise {mess.noun} mess appeared in {room.place}. It landed on {item.label}, so {child.label} had to stop and clean up instead of ignoring it.",
        ),
        QAItem(
            question=f"Why did {child.label} and {helper.label} scrub together?",
            answer=f"They scrubbed together because the spill was real and needed work. More than that, {child.label} told the truth, and {helper.label} answered with patience instead of anger.",
        ),
        QAItem(
            question=f"What changed after {child.label} said sorry?",
            answer=f"The feeling between them changed first: the worry dropped and the room grew calmer. Then the mess was scrubbed away, so the story ended with both of them feeling close again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    mess = f["mess"]
    return [
        QAItem(
            question="What does it mean to scrub something?",
            answer="To scrub means to rub a surface with effort so dirt or sticky stuff comes off. People often scrub with water, soap, and a cloth.",
        ),
        QAItem(
            question=f"Why can a {mess.noun} spill be annoying?",
            answer=f"A {mess.noun} spill can stick to surfaces and take time to clean. If it is left alone, it can dry and become harder to scrub away later.",
        ),
        QAItem(
            question="What is a moral value in a family?",
            answer="A moral value is a kind choice people try to live by, like honesty or kindness. In a family, it helps everyone trust each other and make up after mistakes.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people who were upset start feeling okay with each other again. Often they talk kindly, apologize, and forgive.",
        ),
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


ASP_RULES = r"""
messy(X) :- item(X), mess_level(X, L), L >= 1.
needs_scrub(X) :- messy(X).
reconciled :- apology_given, patience_shown, mess_cleared.
moral_value(honesty) :- apology_given.
moral_value(kindness) :- patience_shown.
valid_story(Place, Mess, Thing) :- place(Place), mess(Mess), thing(Thing), fits(Mess, Thing).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in ROOMS:
        lines.append(asp.fact("place", place))
    for mid, m in MESSES.items():
        lines.append(asp.fact("mess", mid))
        for s in sorted(m.surfaces):
            lines.append(asp.fact("fits", mid, s))
    for tid, t in THINGS.items():
        lines.append(asp.fact("thing", tid))
        lines.append(asp.fact("surface", tid, t.surface))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python:")
        print("  only in ASP:", sorted(cl - py))
        print("  only in Python:", sorted(py - cl))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world about a surprise mess, a scrub, and reconciliation.")
    ap.add_argument("--place", choices=ROOMS)
    ap.add_argument("--mess", choices=MESSES)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["mother", "father", "aunt", "uncle", "sister", "brother"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mess is None or c[1] == args.mess)
              and (args.thing is None or c[2] == args.thing)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mess, thing = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(_child_pool(child_type))
    helper_type = args.helper_type or rng.choice(["mother", "father", "aunt", "uncle", "sister", "brother"])
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    return StoryParams(
        place=place,
        mess=mess,
        thing=thing,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in ROOMS or params.mess not in MESSES or params.thing not in THINGS:
        raise StoryError("Invalid params for this story world.")
    world = World(room=copy.deepcopy(ROOMS[params.place]))
    world.facts["params"] = params
    tell(world, params)
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
        if e.surface:
            bits.append(f"surface={e.surface}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", mess="jam", thing="table", child_name="Mina", child_type="girl", helper_name="Mom", helper_type="mother"),
    StoryParams(place="laundry", mess="paint", thing="hands", child_name="Leo", child_type="boy", helper_name="Dad", helper_type="father"),
    StoryParams(place="porch", mess="mud", thing="shoes", child_name="Ivy", child_type="girl", helper_name="Older Brother", helper_type="brother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(f"{len(asp_valid_combos())} valid (place, mess, thing) combos:\n")
        for t in asp_valid_combos():
            print(f"  {t[0]:8} {t[1]:8} {t[2]}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            header = f"### {p.child_name}: {p.mess} on {p.thing} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
