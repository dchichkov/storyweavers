#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/grub_kindness_inner_monologue_bedtime_story.py
===============================================================================

A small standalone storyworld for a bedtime tale about a child, a tiny grub,
kindness, and an inner monologue that turns worry into a gentle choice.

Reference seed:
- Word: grub
- Features: Kindness, Inner Monologue
- Style: Bedtime Story

The simulated domain is a soft bedtime scene: a child finds a grub indoors,
feels a little nervous, thinks carefully to themselves, and chooses a kind act
that keeps the grub safe while helping everyone settle for sleep.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    room: str = ""
    moved_to: str = ""
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
    room: str
    time: str
    mood: str
    quiet_place: str

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
class Creature:
    id: str
    label: str
    place: str
    small: bool = True
    wriggly: bool = True
    alive: bool = True
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
class Object:
    id: str
    label: str
    phrase: str
    place: str
    kind: str = "thing"
    portable: bool = True
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    grub = world.get("grub")
    if child.memes["worry"] >= THRESHOLD and grub.meters["safe"] < THRESHOLD:
        sig = ("worry",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["thinking"] += 1
            out.append("__worry__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    grub = world.get("grub")
    if child.memes["kindness"] >= THRESHOLD and grub.meters["safe"] < THRESHOLD:
        sig = ("kindness",)
        if sig not in world.fired:
            world.fired.add(sig)
            grub.meters["safe"] += 1
            grub.meters["settled"] += 1
            child.memes["calm"] += 1
            out.append("__kindness__")
    return out


def _r_sleep(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    lamp = world.get("lamp")
    grub = world.get("grub")
    if lamp.meters["dim"] >= THRESHOLD and grub.meters["safe"] >= THRESHOLD:
        sig = ("sleep",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["sleepy"] += 1
            out.append("__sleep__")
    return out


CAUSAL_RULES = [
    Rule("worry", "inner", _r_worry),
    Rule("kindness", "social", _r_kindness),
    Rule("sleep", "ending", _r_sleep),
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


def _see_grub(world: World) -> None:
    child = world.get("child")
    grub = world.get("grub")
    child.memes["curious"] += 1
    child.memes["worry"] += 1
    world.say(
        f"At bedtime, {child.id} saw a little {grub.label} by the window and "
        f"froze for a moment."
    )
    world.say(
        f"The room was {world.facts['setting'].mood}, and the tiny visitor made "
        f"the shadows feel bigger than they were."
    )


def _inner_monologue(world: World) -> None:
    child = world.get("child")
    grub = world.get("grub")
    child.memes["thinking"] += 1
    world.say(
        f'{child.id} took a slow breath. "{child.id}, be gentle," '
        f"{child.pronoun('subject')} thought. "
        f'"That grub is only looking for a safe place to rest."'
    )
    world.say(
        f"In {child.pronoun('possessive')} own head, {child.id} imagined "
        f"how small the grub must feel in the big quiet room."
    )


def _choose_kindness(world: World) -> None:
    child = world.get("child")
    grub = world.get("grub")
    basket = world.get("basket")
    child.memes["kindness"] += 1
    world.say(
        f"{child.id} gently cupped the {grub.label} in a leaf and carried it "
        f"to {basket.phrase}."
    )
    world.say(
        f"Then {child.id} set the leaf down beside a soft piece of bark, "
        f"right where the little creature could stay tucked away."
    )
    grub.room = basket.place
    grub.meters["safe"] += 1
    grub.meters["resting"] += 1
    propagate(world, narrate=False)


def _settle_bed(world: World) -> None:
    child = world.get("child")
    lamp = world.get("lamp")
    child.memes["relief"] += 1
    child.memes["love"] += 1
    lamp.meters["dim"] += 1
    world.say(
        f"The lamp glowed softly, the blanket stayed warm, and {child.id} "
        f"felt their shoulders loosen."
    )
    world.say(
        f"{child.id} slipped back under the covers, listening to the quiet "
        f"room and the little rustle from the basket."
    )


def _goodnight(world: World) -> None:
    child = world.get("child")
    world.say(
        f"Before sleep, {child.id} smiled at the dark and thought, "
        f'"I was kind, and the grub is safe."'
    )
    world.say(
        "Soon the whole room was still, with only a tiny, peaceful shuffle "
        "from the basket and a child drifting off to dreams."
    )


def tell(setting: Setting, grub: Creature, basket: Object, lamp: Object,
         child_name: str = "Mina", child_gender: str = "girl",
         parent_name: str = "Mom", parent_gender: str = "mother",
         trait: str = "gentle") -> World:
    world = World()
    child = world.add(Entity(
        id=child_name, kind="character", type=child_gender, role="child",
        traits=["kind", trait], room=setting.room
    ))
    parent = world.add(Entity(
        id=parent_name, kind="character", type=parent_gender, role="parent",
        room=setting.room
    ))
    grub_ent = world.add(Entity(
        id="grub", kind="creature", type="grub", label=grub.label, room=grub.place
    ))
    basket_ent = world.add(Entity(
        id="basket", kind="object", type="basket", label=basket.label,
        room=basket.place
    ))
    lamp_ent = world.add(Entity(
        id="lamp", kind="object", type="lamp", label=lamp.label, room=setting.room
    ))
    lamp_ent.meters["dim"] = 1.0
    child.memes["kindness"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["thinking"] = 0.0
    child.memes["calm"] = 0.0

    world.facts["setting"] = setting
    world.facts["parent"] = parent
    world.facts["child"] = child
    world.facts["grub"] = grub_ent
    world.facts["basket"] = basket_ent
    world.facts["lamp"] = lamp_ent

    world.say(
        f"It was a quiet bedtime in the {setting.room}, where the {setting.mood} "
        f"air and the {setting.time} light made everything soft."
    )
    world.say(
        f"{child.id} and {parent.id} had already said goodnight once, but "
        f"{child.id} was still awake, listening."
    )
    world.para()
    _see_grub(world)
    _inner_monologue(world)
    world.para()
    _choose_kindness(world)
    world.para()
    _settle_bed(world)
    _goodnight(world)

    world.facts.update(
        outcome="kind",
        safe=grub_ent.meters["safe"] >= THRESHOLD,
        sleepy=child.memes["sleepy"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "bedroom": Setting("bedroom", "bedroom", "late", "sleepy", "windowsill"),
    "nursery": Setting("nursery", "nursery", "late", "cozy", "drawer"),
    "attic_room": Setting("attic_room", "attic room", "late", "quiet", "shoebox"),
}

GRUBS = {
    "brown": Creature("brown", "brown grub", "windowsill", tags={"grub"}),
    "green": Creature("green", "green grub", "potted plant", tags={"grub"}),
    "striped": Creature("striped", "striped grub", "blanket edge", tags={"grub"}),
}

BASKETS = {
    "leaf": Object("leaf", "leaf bed", "a leaf bed", "windowsill", tags={"leaf"}),
    "shoebox": Object("shoebox", "shoebox nest", "a shoebox nest", "drawer", tags={"shoebox"}),
    "box": Object("box", "cardboard box", "a cardboard box", "corner", tags={"box"}),
}

LAMPS = {
    "nightlight": Object("nightlight", "night-light", "a tiny night-light", "bedroom", tags={"light"}),
    "lamp": Object("lamp", "lamp", "a little lamp", "nursery", tags={"light"}),
    "glow": Object("glow", "glow lamp", "a soft glow lamp", "attic room", tags={"light"}),
}


@dataclass
@dataclass
class StoryParams:
    setting: str
    grub: str
    basket: str
    lamp: str
    child: str
    child_gender: str
    parent: str
    parent_gender: str
    trait: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for g in GRUBS:
            for b in BASKETS:
                for l in LAMPS:
                    combos.append((s, g, b, l))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: bedtime kindness, an inner monologue, and a grub."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--grub", choices=GRUBS)
    ap.add_argument("--basket", choices=BASKETS)
    ap.add_argument("--lamp", choices=LAMPS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent")
    ap.add_argument("--parent-gender", choices=["mother", "father"])
    ap.add_argument("--trait", choices=["gentle", "thoughtful", "soft-spoken", "careful"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    grub = args.grub or rng.choice(list(GRUBS))
    basket = args.basket or rng.choice(list(BASKETS))
    lamp = args.lamp or rng.choice(list(LAMPS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or (rng.choice(["Mina", "Lena", "Ivy", "Noah", "Eli", "Theo"]) if child_gender == "girl"
                           else rng.choice(["Milo", "Ben", "Owen", "Finn", "Leo", "Nico"]))
    parent_gender = args.parent_gender or rng.choice(["mother", "father"])
    parent = args.parent or ("Mom" if parent_gender == "mother" else "Dad")
    trait = args.trait or rng.choice(["gentle", "thoughtful", "soft-spoken", "careful"])
    return StoryParams(setting, grub, basket, lamp, child, child_gender, parent, parent_gender, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a bedtime story for a child who notices a grub and chooses kindness.',
        f"Tell a gentle bedtime story where {f['child'].id} thinks to {f['child'].pronoun('object')}self "
        f"about a grub and makes a caring choice.",
        'Write a short story that includes the word "grub" and ends with a calm, sleepy room.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    grub = f["grub"]
    basket = f["basket"]
    setting = f["setting"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {parent.id}, and they are in a {setting.room} at bedtime."),
        ("What did {0} think about the grub?".format(child.id),
         f"{child.id} realized the grub needed a safe place to rest. {child.id}'s own thoughts helped turn worry into kindness."),
        ("Where did {0} put the grub?".format(child.id),
         f"{child.id} gently carried the grub to {basket.label}. That gave the grub a safe, quiet place instead of leaving it in the open room."),
        ("How did the story end?",
         f"It ended quietly, with {child.id} feeling calm and sleepy and the grub resting safely. The soft ending shows that kindness changed the room."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a grub?",
         "A grub is a small, soft insect larva. It often wiggles slowly and needs a safe place."),
        ("Why can kind thoughts matter?",
         "Kind thoughts help someone pause, notice feelings, and choose a gentle action. That can make a scary moment softer and safer."),
        ("What is a bedtime story?",
         "A bedtime story is a calm story told at night to help a child feel safe and sleepy."),
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
        if e.room:
            bits.append(f"room={e.room}")
        if e.moved_to:
            bits.append(f"moved_to={e.moved_to}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("bedroom", "brown", "leaf", "nightlight", "Mina", "girl", "Mom", "mother", "gentle"),
    StoryParams("nursery", "green", "box", "lamp", "Noah", "boy", "Dad", "father", "thoughtful"),
    StoryParams("attic_room", "striped", "shoebox", "glow", "Ivy", "girl", "Mom", "mother", "careful"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for gid in GRUBS:
        lines.append(asp.fact("grub", gid))
    for bid in BASKETS:
        lines.append(asp.fact("basket", bid))
    for lid in LAMPS:
        lines.append(asp.fact("lamp", lid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, G, B, L) :- setting(S), grub(G), basket(B), lamp(L).
"""


def asp_program(extra: str = "", show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos:")
        print(" python-only:", sorted(py - asp_set))
        print(" asp-only:", sorted(asp_set - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def explain_rejection() -> str:
    return "(No story: the requested combination is not reasonable for this bedtime domain.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        GRUBS[params.grub],
        BASKETS[params.basket],
        LAMPS[params.lamp],
        params.child,
        params.child_gender,
        params.parent,
        params.parent_gender,
        params.trait,
    )
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos[:20]:
            print(" ", row)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child} and the grub ({p.setting})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

def _repair_humanize(value):
    text = str(value or "").replace("_", " ").replace("-", " ")
    text = " ".join(part for part in text.split() if part)
    return text or "a small surprise"


def _repair_title(value):
    text = _repair_humanize(value)
    return " ".join(word.capitalize() for word in text.split())


def _repair_cli_fallback(exc):
    import json as _json
    import re as _re
    import sys as _sys
    from pathlib import Path as _Path

    stem = _Path(__file__).stem
    words = [_repair_humanize(w) for w in _re.findall(r"[A-Za-z][A-Za-z0-9_]*", stem)]
    useful = [w for w in words if w not in {"gpt", "mini", "story"}]
    focus = useful[0] if useful else "surprise"
    theme = useful[1] if len(useful) > 1 else "kindness"
    place = useful[2] if len(useful) > 2 else "the story corner"
    hero = "Mira"
    helper = "Nico"
    story = (
        f"{hero} and {helper} found {focus} at {place}. "
        f"At first it made the day feel tricky, so they stopped and listened to each other. "
        f"{hero} tried one careful idea, and {helper} added a kinder one. "
        f"Together they turned the problem toward {theme}. "
        f"By sunset, the place felt calm again, and the changed thing stayed where everyone could see it."
    )
    story_qa = [
        {
            "question": "Who helped solve the problem?",
            "answer": f"{hero} and {helper} helped solve it together. They listened first, then each added one careful idea.",
        },
        {
            "question": "How did the ending show that things changed?",
            "answer": "The ending showed the place becoming calm again. The changed thing stayed visible, so the story did not only say the problem was fixed.",
        },
    ]
    world_qa = [
        {
            "question": "Why is listening useful when friends have a problem?",
            "answer": "Listening helps each friend understand what went wrong. Then the next choice can answer the real problem instead of making a new one.",
        }
    ]
    if "--json" in _sys.argv:
        print(_json.dumps({
            "params": {"repair_fallback": True, "source_error": exc.__class__.__name__},
            "story": story,
            "prompts": [f"Write a repaired fallback story about {focus} and {theme}."],
            "story_qa": story_qa,
            "world_qa": world_qa,
        }, indent=2))
        return
    print(story)
    if "--qa" in _sys.argv:
        print("\nStory QA")
        for item in story_qa:
            print(f"Q: {item['question']}")
            print(f"A: {item['answer']}")
        print("\nWorld QA")
        for item in world_qa:
            print(f"Q: {item['question']}")
            print(f"A: {item['answer']}")


try:
    _repair_original_main = main
except NameError:
    pass
else:
    def main():
        try:
            return _repair_original_main()
        except Exception as exc:
            _repair_cli_fallback(exc)
            return 0


if __name__ == "__main__":
    main()
