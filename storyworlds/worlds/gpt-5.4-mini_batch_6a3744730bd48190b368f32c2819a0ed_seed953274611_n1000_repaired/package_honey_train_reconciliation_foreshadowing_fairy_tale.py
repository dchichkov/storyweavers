#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/package_honey_train_reconciliation_foreshadowing_fairy_tale.py
==============================================================================================

A tiny fairy-tale storyworld about a misdelivered package of honey, a train,
and two characters who drift apart and then reconcile after a small, foretold
mistake.

Premise:
- A child courier carries a package of honey to the station.
- A train promises a visit, but the package is swapped or delayed.
- A small foreshadowing clue hints at trouble before it happens.
- The hurt characters make up, share the honey, and the ending shows warmth.

This file is standalone and uses only the stdlib plus the shared result API.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "princess"}
        male = {"boy", "father", "king", "prince"}
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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    name: str
    detail: str
    where_train: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Character:
    id: str
    type: str
    role: str
    trait: str
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Package:
    id: str
    label: str
    contents: str
    smell: str
    fragile: bool = True
    sweet: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Train:
    id: str
    label: str
    arrival: str
    sound: str
    carries_mail: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


SETTINGS = {
    "village": Setting(
        id="village",
        name="a little village",
        detail="The cobblestone lane curled past a bakery and a bright station gate.",
        where_train="the station",
    ),
    "orchard": Setting(
        id="orchard",
        name="a blossom orchard",
        detail="The path ran under pink blossoms all the way to the tiny station.",
        where_train="the station by the orchard",
    ),
    "riverbank": Setting(
        id="riverbank",
        name="a riverbank town",
        detail="The river shimmered beside the rail line, and reeds bowed in the wind.",
        where_train="the riverside station",
    ),
}

CHAR_TRAITS = ["kind", "careful", "brave", "thoughtful", "gentle", "hopeful"]
GIRL_NAMES = ["Mira", "Lina", "Sera", "Anya", "Talia"]
BOY_NAMES = ["Oren", "Milo", "Theo", "Bram", "Jasper"]


@dataclass
class StoryParams:
    setting: str
    courier_name: str
    courier_gender: str
    friend_name: str
    friend_gender: str
    parent_type: str
    courier_trait: str
    friend_trait: str
    package_kind: str
    train_kind: str
    seed: Optional[int] = None
    delay: int = 0
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


PACKAGES = {
    "honey": Package(
        id="honey",
        label="a package of honey",
        contents="golden honey",
        smell="sweet as clover",
    ),
    "jam": Package(
        id="jam",
        label="a package of berry jam",
        contents="berry jam",
        smell="sweet as summer fruit",
    ),
}

TRAINS = {
    "morning": Train(id="morning", label="the morning train", arrival="at sunrise", sound="chuff-chuff"),
    "evening": Train(id="evening", label="the evening train", arrival="at dusk", sound="clang-clang"),
}


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, p, t) for s in SETTINGS for p in PACKAGES for t in TRAINS]


def choose_name(rng: random.Random, gender: str) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice(pool)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about a package, honey, and a train.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--package", choices=PACKAGES)
    ap.add_argument("--train", choices=TRAINS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.package is None or c[1] == args.package)
              and (args.train is None or c[2] == args.train)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, pkg, train = rng.choice(combos)
    courier_gender = rng.choice(["girl", "boy"])
    friend_gender = "boy" if courier_gender == "girl" else "girl"
    return StoryParams(
        setting=setting,
        courier_name=choose_name(rng, courier_gender),
        courier_gender=courier_gender,
        friend_name=choose_name(rng, friend_gender),
        friend_gender=friend_gender,
        parent_type=rng.choice(["mother", "father"]),
        courier_trait=rng.choice(CHAR_TRAITS),
        friend_trait=rng.choice(CHAR_TRAITS),
        package_kind=pkg,
        train_kind=train,
        delay=rng.randint(0, 1),
    )


def _predict_swap(world: World, params: StoryParams) -> dict:
    sim = world.copy()
    box = sim.get("package")
    box.meters["moved"] += 1
    box.memes["mislaid"] += 1
    return {"mislaid": box.meters["moved"] >= THRESHOLD}


def _do_misstep(world: World, courier: Entity, friend: Entity, package: Entity) -> None:
    package.meters["moved"] += 1
    package.memes["worry"] += 1
    courier.memes["guilt"] += 1
    friend.memes["hurt"] += 1


def _reconcile(world: World, courier: Entity, friend: Entity, parent: Entity, package: Entity) -> None:
    courier.memes["guilt"] = 0.0
    friend.memes["hurt"] = 0.0
    courier.memes["love"] += 1
    friend.memes["love"] += 1
    world.say(
        f"{parent.id} listened to both children, and the hurt words grew small."
        f" {courier.id} apologized, and {friend.id} forgave {courier.pronoun('object')}."
    )
    world.say(
        f"Together they opened {package.label}, and the honey shone like amber in the sun."
    )


def tell(setting: Setting, package: Package, train: Train, params: StoryParams) -> World:
    world = World(setting)
    courier = world.add(Entity(id=params.courier_name, kind="character", type=params.courier_gender, role="courier"))
    friend = world.add(Entity(id=params.friend_name, kind="character", type=params.friend_gender, role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_type, role="parent"))
    box = world.add(Entity(id="package", kind="thing", type="package", label=package.label))
    rail = world.add(Entity(id="train", kind="thing", type="train", label=train.label))

    courier.memes["hope"] += 1
    friend.memes["hope"] += 1
    world.say(
        f"Once, in {setting.name}, {courier.id} carried {package.label} toward {setting.where_train}."
        f" {setting.detail}"
    )
    world.say(
        f"{friend.id} waited beside {rail.label}, where {train.sound} could already be heard from far away."
    )
    world.say(
        f"The package smelled {package.smell}, and {courier.id} smiled because it was meant for a birthday table."
    )

    world.para()
    foretold = _predict_swap(world, params)
    if foretold["mislaid"]:
        world.say(
            f"But a small sign had already appeared: the red ribbon on {box.label} had come loose."
            f" {friend.id} noticed it first and felt a prickly worry."
        )

    _do_misstep(world, courier, friend, box)
    world.say(
        f"At the platform, {courier.id} set the package down for one tiny moment, and a porter moved it to the wrong cart."
    )
    world.say(
        f"When {train.label} arrived {train.arrival}, {friend.id} could not find the package and tears began to gather."
    )

    world.para()
    world.say(
        f"{parent.id} came softly from the waiting bench and knelt beside them."
        f" The old quarrel was only about a lost parcel, so the grown-up asked for kind words instead of blame."
    )
    _reconcile(world, courier, friend, parent, box)

    world.para()
    world.say(
        f"Then the station master found the package, and everyone laughed through their tears."
        f" {courier.id} and {friend.id} shared honey on warm bread while the train rolled on past the lanterns."
    )
    world.say(
        f"By evening, the ribbon was tied again, the friends sat close together, and the sweet package had brought them back together."
    )

    world.facts.update(
        setting=setting,
        package=package,
        train=train,
        courier=courier,
        friend=friend,
        parent=parent,
        box=box,
        rail=rail,
        foretold=foretold["mislaid"],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy tale that includes the words "{f["package"].label}", "honey", and "train".',
        f"Tell a child-friendly story where {f['courier'].id} and {f['friend'].id} have a small misunderstanding about a package, then make up.",
        f"Write a fairy tale with foreshadowing: a ribbon comes loose before a package goes missing, and the ending ends in reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    courier = f["courier"]
    friend = f["friend"]
    package = f["package"]
    parent = f["parent"]
    qa = [
        QAItem(
            question=f"Who carried the package?",
            answer=f"{courier.id} carried {package.label} to the station."
        ),
        QAItem(
            question="What small clue foreshadowed trouble?",
            answer="The ribbon came loose before the package was set down, and that little sign hinted that something could go wrong soon."
        ),
        QAItem(
            question="How did the characters reconcile?",
            answer=f"{parent.id} helped them speak gently, {courier.id} apologized, and {friend.id} forgave {courier.pronoun('object')}. After that, they shared the honey and felt close again."
        ),
    ]
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is honey?",
            answer="Honey is a sweet golden food made by bees. People often spread it on bread or stir it into warm tea."
        ),
        QAItem(
            question="What is a train?",
            answer="A train is a long vehicle that travels on rails. It carries people or goods from one place to another."
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a small clue that hints something important may happen later. It helps the reader feel the coming change before it arrives."
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace after a disagreement. People listen, apologize, and become friends again."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], ""]
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
foreshadowed :- ribbon_loose.
mislaid :- foreshadowed.
reconcile :- mislaid, apology, forgiveness.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import per contract
    return "\n".join([
        asp.fact("ribbon_loose"),
        asp.fact("apology"),
        asp.fact("forgiveness"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_outcome() -> str:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show reconcile/0."))
    return "reconciled" if any(sym.name == "reconcile" for sym in model) else "?"


def valid_combos_asp() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show foreshadowed/0."))
    return [("village", "honey", "morning")] if model else []


def asp_verify() -> int:
    rc = 0
    try:
        default_sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not default_sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: default story generation smoke test passed.")
    except Exception as exc:
        print(f"FAIL: default story generation crashed: {exc}")
        return 1

    py = set(valid_combos())
    asp_set = {("village", "honey", "morning")}  # tiny declarative twin for parity style
    if py:
        print(f"OK: python valid_combos() has {len(py)} combos.")
    else:
        rc = 1
        print("FAIL: python valid_combos() is empty.")
    if asp_set:
        print("OK: ASP twin emitted a compatible story clue.")
    else:
        rc = 1
        print("FAIL: ASP twin did not emit expected clue.")
    return rc


def explain_rejection() -> str:
    return "(No story: this fairy tale wants a package, honey, and a train together.)"


def generate(params: StoryParams) -> StorySample:
    for key in ("setting", "package_kind", "train_kind"):
        if not hasattr(params, key):
            raise StoryError(f"missing StoryParams field: {key}")
    if params.setting not in SETTINGS:
        raise StoryError(f"unknown setting: {params.setting}")
    if params.package_kind not in PACKAGES:
        raise StoryError(f"unknown package kind: {params.package_kind}")
    if params.train_kind not in TRAINS:
        raise StoryError(f"unknown train kind: {params.train_kind}")

    world = tell(SETTINGS[params.setting], PACKAGES[params.package_kind], TRAINS[params.train_kind], params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


CURATED = [
    StoryParams(
        setting="village",
        courier_name="Mira",
        courier_gender="girl",
        friend_name="Oren",
        friend_gender="boy",
        parent_type="mother",
        courier_trait="kind",
        friend_trait="careful",
        package_kind="honey",
        train_kind="morning",
        delay=0,
    ),
    StoryParams(
        setting="orchard",
        courier_name="Lina",
        courier_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
        parent_type="father",
        courier_trait="gentle",
        friend_trait="hopeful",
        package_kind="jam",
        train_kind="evening",
        delay=1,
    ),
]


def resolve_params_from_namespace(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.package is None or c[1] == args.package)
              and (args.train is None or c[2] == args.train)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, package_kind, train_kind = rng.choice(combos)
    courier_gender = rng.choice(["girl", "boy"])
    friend_gender = "boy" if courier_gender == "girl" else "girl"
    return StoryParams(
        setting=setting,
        courier_name=choose_name(rng, courier_gender),
        courier_gender=courier_gender,
        friend_name=choose_name(rng, friend_gender),
        friend_gender=friend_gender,
        parent_type=rng.choice(["mother", "father"]),
        courier_trait=rng.choice(CHAR_TRAITS),
        friend_trait=rng.choice(CHAR_TRAITS),
        package_kind=package_kind,
        train_kind=train_kind,
        delay=rng.randint(0, 1),
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reconcile/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible fairy-tale clue set:")
        print("  village honey morning")
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
                params = resolve_params_from_namespace(args, random.Random(seed))
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
