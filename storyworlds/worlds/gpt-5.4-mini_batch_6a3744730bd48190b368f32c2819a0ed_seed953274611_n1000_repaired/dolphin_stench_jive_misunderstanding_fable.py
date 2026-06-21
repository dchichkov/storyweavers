#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dolphin_stench_jive_misunderstanding_fable.py
==============================================================================

A small, self-contained storyworld for a fable about a dolphin, a stench, and a
jive misunderstanding. The simulated world tracks a tiny streamside stage, a
lost bundle, a mistaken rumor, and a wise ending image where the truth is shown
through action rather than argument.

The world is built for children: concrete, causal, and gently moral.
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
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    water: bool = False
    open_air: bool = False
    smell_carries: bool = True
    tags: set[str] = field(default_factory=set)
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


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    smell: str
    loseable: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Mischief:
    id: str
    label: str
    verb: str
    sound: str
    clever: str
    tags: set[str] = field(default_factory=set)
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


@dataclass
class Wisdom:
    id: str
    label: str
    action: str
    result: str
    tags: set[str] = field(default_factory=set)
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


@dataclass
class StoryParams:
    place: str = "riverbank"
    item: str = "fish_bucket"
    misunderstanding: str = "fishy_stench"
    mischief: str = "jive"
    wisdom: str = "ask_and_wash"
    dolphin_name: str = "Della"
    helper_name: str = "Milo"
    dolphin_gender: str = "girl"
    helper_gender: str = "boy"
    parent_name: str = "Riverkeeper"
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable
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


def _r_misread(world: World) -> list[str]:
    out: list[str] = []
    d = world.get("dolphin")
    helper = world.get("helper")
    item = world.get("item")
    if d.meters["stink"] >= THRESHOLD and helper.memes["embarrassment"] >= THRESHOLD:
        sig = ("misread",)
        if sig not in world.fired:
            world.fired.add(sig)
            helper.memes["misunderstanding"] += 1
            out.append("__misunderstanding__")
    if item.meters["clean"] >= THRESHOLD and d.meters["stink"] < THRESHOLD:
        sig = ("clear",)
        if sig not in world.fired:
            world.fired.add(sig)
            helper.memes["relief"] += 1
    return out


CAUSAL_RULES = [Rule("misread", _r_misread)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def predict_confusion(world: World) -> bool:
    sim = world.copy()
    sim.get("dolphin").meters["stink"] += 1
    propagate(sim, narrate=False)
    return sim.get("helper").memes["misunderstanding"] >= THRESHOLD


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in PLACES:
        for item in ITEMS:
            for mischief in MISCHIEFS:
                if place.water and item.loseable and mischief.id == "jive":
                    combos.append((place.id, item.id, mischief.id))
    return combos


def _do_misread(world: World, item: Entity) -> None:
    item.meters["stink"] += 1
    propagate(world, narrate=False)


def opening(world: World, dolphin: Entity, helper: Entity, place: Place, item: Item) -> None:
    world.say(
        f"At {place.label}, {dolphin.id} the dolphin and {helper.id} the helper "
        f"found a lost little bundle by the water."
    )
    world.say(
        f"The bundle smelled odd, and the air carried a stench that made {helper.id} wrinkle "
        f"{helper.pronoun('possessive')} nose."
    )


def misunderstanding(world: World, dolphin: Entity, helper: Entity, mischief: Mischief, item: Item) -> None:
    helper.memes["embarrassment"] += 1
    world.say(
        f'{helper.id} thought the stench meant {dolphin.id} had been up to a prank. '
        f'"That must be from your {mischief.label}!" {helper.id} said.'
    )
    world.say(
        f"{dolphin.id} blinked. {dolphin.pronoun().capitalize()} only wanted to help, "
        f"but the rumor sounded rude."
    )


def jive(world: World, dolphin: Entity, helper: Entity, mischief: Mischief, item: Item) -> None:
    dolphin.memes["hurt"] += 1
    helper.memes["worry"] += 1
    world.say(
        f"To show {helper.id} the truth, {dolphin.id} gave a quick {mischief.label}, "
        f"{mischief.sound} across the wet stones."
    )
    world.say(
        f"It was a clever little {mischief.label_word if hasattr(mischief, 'label_word') else mischief.label}, "
        f"but the misunderstanding only grew."
    )


def wise_turn(world: World, parent: Entity, dolphin: Entity, helper: Entity, wisdom: Wisdom, item: Item) -> None:
    if not predict_confusion(world):
        return
    world.say(
        f"Then {parent.id} came by and laughed softly. '{dolphin.id} was not making trouble,' "
        f"{parent.pronoun()} said. '{wisdom.action} is the wiser way.'"
    )
    world.say(
        f"{dolphin.id} pointed at the bundle and {wisdom.result}, and at once the stench made sense."
    )


def resolution(world: World, dolphin: Entity, helper: Entity, item: Entity) -> None:
    dolphin.memes["relief"] += 1
    helper.memes["relief"] += 1
    item.meters["clean"] += 1
    item.meters["open"] += 1
    world.say(
        f"Together they rinsed the bundle clean and found it was only old bait cloth, not a bad joke."
    )
    world.say(
        f"The stench washed away, {helper.id} apologized, and {dolphin.id} answered with a happy little jive on the shore."
    )
    world.say(
        f"By sunset, the water was calm again, and the dolphin's dance was understood at last."
    )


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    item_cfg = ITEMS[params.item]
    mischief = MISCHIEFS[params.mischief]
    wisdom = WISDOMS[params.wisdom]
    if not place.water:
        raise StoryError("This fable needs water nearby for a dolphin to belong in the scene.")
    world = World(place)
    dolphin = world.add(Entity(id="dolphin", kind="character", type=params.dolphin_gender, role="hero", label="dolphin"))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, role="friend", label="helper"))
    parent = world.add(Entity(id=params.parent_name, kind="character", type="adult", role="wise", label=params.parent_name))
    item = world.add(Entity(id="item", kind="thing", type="thing", label=item_cfg.label, attrs={"smell": item_cfg.smell}))
    world.facts.update(place=place, item_cfg=item_cfg, mischief=mischief, wisdom=wisdom)

    opening(world, dolphin, helper, place, item_cfg)
    world.para()
    misunderstanding(world, dolphin, helper, mischief, item_cfg)
    _do_misread(world, item)
    jive(world, dolphin, helper, mischief, item_cfg)
    world.para()
    wise_turn(world, parent, dolphin, helper, wisdom, item_cfg)
    resolution(world, dolphin, helper, item)
    world.facts.update(dolphin=dolphin, helper=helper, parent=parent, item=item)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable for young children that includes the words "{f["place"].label}", "dolphin", "stench", and "jive".',
        f"Tell a short moral story where a dolphin is misunderstood because of a stench, then the truth is cleared up with a gentle jive.",
        "Write a story about a misunderstanding near water, with a wise adult, a mistaken rumor, and a happy ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    dolphin, helper, parent = f["dolphin"], f["helper"], f["parent"]
    item_cfg: Item = f["item_cfg"]
    qa = [
        ("Who is the story about?",
         f"It is about {dolphin.id} the dolphin and {helper.id}, who were beside the water when the misunderstanding began."),
        ("Why did the helper get upset?",
         f"{helper.id} smelled the stench and guessed it meant {dolphin.id} had done something bad. That was a misunderstanding, because the smell came from the bundle instead."),
        ("How was the mistake fixed?",
         f"{parent.id} explained the truth, and {dolphin.id} showed a gentle jive while the bundle was washed clean. After that, everyone could see that the smell was not a prank."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a dolphin?",
         "A dolphin is a smart sea animal that swims in water and can leap above the waves."),
        ("What is a stench?",
         "A stench is a very strong, bad smell that people notice right away."),
        ("What is a jive?",
         "A jive is a lively dance step with quick moves and a cheerful rhythm."),
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(place: Place) -> str:
    return "(No story: this fable needs water near the dolphin, or there is no believable stage for the misunderstanding.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.water:
            lines.append(asp.fact("water", pid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for mid in MISCHIEFS:
        lines.append(asp.fact("mischief", mid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,I,M) :- place(P), water(P), item(I), mischief(M), M = jive.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import tempfile
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid-combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, item=None, misunderstanding=None, mischief=None, wisdom=None, dolphin_name=None, helper_name=None, dolphin_gender=None, helper_gender=None, parent_name=None), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable world with dolphin, stench, jive, and misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--mischief", choices=MISCHIEFS)
    ap.add_argument("--wisdom", choices=WISDOMS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)
              and (args.mischief is None or c[2] == args.mischief)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item, mischief = rng.choice(sorted(combos))
    misunderstanding = args.misunderstanding or "fishy_stench"
    wisdom = args.wisdom or rng.choice(sorted(WISDOMS))
    dolphin_name = args.dolphin_name if hasattr(args, "dolphin_name") and args.dolphin_name else rng.choice(DOLPHIN_NAMES)
    helper_name = args.helper_name if hasattr(args, "helper_name") and args.helper_name else rng.choice(HELPER_NAMES)
    dolphin_gender = getattr(args, "dolphin_gender", None) or rng.choice(["girl", "boy"])
    helper_gender = getattr(args, "helper_gender", None) or rng.choice(["girl", "boy"])
    parent_name = getattr(args, "parent_name", None) or rng.choice(PARENT_NAMES)
    return StoryParams(place=place, item=item, misunderstanding=misunderstanding, mischief=mischief, wisdom=wisdom, dolphin_name=dolphin_name, helper_name=helper_name, dolphin_gender=dolphin_gender, helper_gender=helper_gender, parent_name=parent_name)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.item not in ITEMS or params.mischief not in MISCHIEFS or params.wisdom not in WISDOMS:
        raise StoryError("Invalid story parameters.")
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


PLACES = {
    "riverbank": Place(id="riverbank", label="the riverbank", water=True, open_air=True, tags={"water", "river"}),
    "harbor": Place(id="harbor", label="the harbor", water=True, open_air=True, tags={"water", "boats"}),
    "pond": Place(id="pond", label="the pond", water=True, open_air=True, tags={"water", "pond"}),
}
ITEMS = {
    "fish_bucket": Item(id="fish_bucket", label="a fish bucket", phrase="a fish bucket", smell="fishy", tags={"smell"}),
    "seaweed_boots": Item(id="seaweed_boots", label="a pile of seaweed boots", phrase="a pile of seaweed boots", smell="stinky", tags={"smell"}),
    "bait_cloth": Item(id="bait_cloth", label="an old bait cloth", phrase="an old bait cloth", smell="fishy", tags={"smell"}),
}
MISUNDERSTANDINGS = {"fishy_stench": "fishy_stench"}
MISCHIEFS = {
    "jive": Mischief(id="jive", label="jive", verb="jive", sound="jive-jive", clever="quick and bright", tags={"dance"}),
    "shuffle": Mischief(id="shuffle", label="shuffle", verb="shuffle", sound="shuf-shuf", clever="small and neat", tags={"dance"}),
}
WISDOMS = {
    "ask_and_wash": Wisdom(id="ask_and_wash", label="ask and wash", action="ask a question instead of guessing", result="they washed the bundle and peeked inside", tags={"wisdom"}),
    "look_closer": Wisdom(id="look_closer", label="look closer", action="look closer before talking", result="they looked closer and saw the truth", tags={"wisdom"}),
}
DOLPHIN_NAMES = ["Della", "Nori", "Pip", "Mina", "Sera"]
HELPER_NAMES = ["Milo", "Tess", "Ravi", "June", "Oli"]
PARENT_NAMES = ["Captain Reed", "Aunt Harbor", "Old Net", "Riverkeeper"]


CURATED = [
    StoryParams(place="riverbank", item="fish_bucket", misunderstanding="fishy_stench", mischief="jive", wisdom="ask_and_wash", dolphin_name="Della", helper_name="Milo", dolphin_gender="girl", helper_gender="boy", parent_name="Riverkeeper"),
    StoryParams(place="harbor", item="bait_cloth", misunderstanding="fishy_stench", mischief="jive", wisdom="look_closer", dolphin_name="Nori", helper_name="Tess", dolphin_gender="boy", helper_gender="girl", parent_name="Captain Reed"),
]


def generation_prompts(_world: World) -> list[str]:
    return [
        'Write a fable that includes the words "dolphin", "stench", and "jive", and features a misunderstanding that gets resolved wisely.',
        "Tell a short moral story about a dolphin whose good deed is mistaken because of a bad smell, then set right by a wise adult.",
        "Write a child-friendly fable with water, rumor, apology, and a happy ending where a jive helps show the truth.",
    ]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(str(t) for t in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            i += 1
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
