#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/nostril_kernel_bale_snowy_curb_kindness_lesson.py
==================================================================================

A tiny fable-like storyworld set on a snowy curb.

Premise:
- A child finds a kernel in a bale of hay beside a snowy curb.
- A small animal sneezes, leading to a misunderstanding and a tease.
- Kindness changes the moment into reconciliation and a lesson learned.

The domain is intentionally small and state-driven:
- physical meters: snow, cold, worry, warmth, spilled, gathered
- emotional memes: pride, shame, kindness, trust, hurt, lesson, reconciliation

This script is standalone and uses only stdlib plus the shared Storyweavers
result/ASP helpers.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    meters: dict[str, float] = field(default_factory=lambda: {"snow": 0.0, "cold": 0.0, "worry": 0.0, "warmth": 0.0, "spilled": 0.0, "gathered": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"pride": 0.0, "shame": 0.0, "kindness": 0.0, "trust": 0.0, "hurt": 0.0, "lesson": 0.0, "reconciliation": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
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
class StoryParams:
    setting: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    elder_name: str
    elder_type: str
    kernel_kind: str
    bale_kind: str
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


@dataclass
class Setting:
    id: str
    place: str
    curb: str
    weather: str
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
class ObjectCfg:
    id: str
    label: str
    article: str
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c
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
class Rule:
    name: str
    apply: Callable[[World], list[str]]
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


SETTINGS = {
    "snowy_curb": Setting(id="snowy_curb", place="the snowy curb", curb="curb", weather="snowy", tags={"snow", "curb"}),
    "quiet_lane": Setting(id="quiet_lane", place="a quiet snowy lane", curb="curb", weather="snowy", tags={"snow", "curb"}),
}

KERNELS = {
    "corn": ObjectCfg(id="corn", label="corn kernel", article="a", tags={"kernel", "corn"}),
    "sunflower": ObjectCfg(id="sunflower", label="sunflower kernel", article="a", tags={"kernel", "sunflower"}),
}

BALES = {
    "hay": ObjectCfg(id="hay", label="bale of hay", article="a", tags={"bale", "hay"}),
    "straw": ObjectCfg(id="straw", label="bale of straw", article="a", tags={"bale", "straw"}),
}

CHILD_NAMES = ["Mina", "Otto", "Lina", "Toby", "Iris", "Pip"]
ELDER_NAMES = ["Grandma", "Grandpa", "Aunt June", "Uncle Reed", "Old Bear"]
HELPER_NAMES = ["Blue Jay", "Mole", "Sparrow", "Mouse", "Rabbit"]


def _r_warmth(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    if helper.memes["kindness"] >= THRESHOLD and child.memes["hurt"] >= THRESHOLD:
        sig = ("warmth",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["warmth"] += 1
            helper.meters["warmth"] += 1
            child.memes["trust"] += 1
            out.append("__warmth__")
    return out


def _r_reconcile(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    elder = world.get("elder")
    if child.memes["kindness"] >= THRESHOLD and helper.memes["kindness"] >= THRESHOLD:
        sig = ("reconcile",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["reconciliation"] += 1
            helper.memes["reconciliation"] += 1
            elder.memes["reconciliation"] += 1
            elder.memes["lesson"] += 1
            return ["__reconcile__"]
    return []


CAUSAL_RULES = [Rule("warmth", _r_warmth), Rule("reconcile", _r_reconcile)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
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


def _do_scene(world: World, child: Entity, helper: Entity, elder: Entity, kernel: ObjectCfg, bale: ObjectCfg, setting: Setting) -> None:
    world.say(
        f"On {setting.place}, the snow lay soft along the curb, and beside it stood {bale.article} {bale.label}."
    )
    world.say(
        f"{child.id} found {kernel.article} {kernel.label} tucked in the hay, and {helper.id} peeped from a hollow in the snow."
    )


def _sneeze(world: World, helper: Entity, child: Entity, kernel: ObjectCfg, bale: ObjectCfg) -> None:
    helper.meters["cold"] += 1
    helper.memes["hurt"] += 1
    world.say(
        f"Then {helper.id}'s little nostril twitched. \"Achoo!\" went the sneeze, and {kernel.label} bounced from the {bale.label} into the snow."
    )
    child.memes["pride"] += 1
    child.memes["hurt"] += 1
    world.say(
        f"{child.id} laughed a sharp laugh and said the sneeze was clumsy."
    )


def _kindness(world: World, child: Entity, helper: Entity, elder: Entity, kernel: ObjectCfg, bale: ObjectCfg) -> None:
    child.memes["kindness"] += 1
    helper.memes["kindness"] += 1
    world.say(
        f"But {child.id} looked at {helper.id}'s wet whiskers, softened their heart, and picked up the {kernel.label} with care."
    )
    world.say(
        f'"Here," {child.id} said, "you can have it back. I should not have teased you."'
    )


def _lesson(world: World, elder: Entity, child: Entity, helper: Entity) -> None:
    elder.memes["lesson"] += 1
    world.say(
        f"{elder.id} nodded beside the snowy curb. \"A kind word warms faster than a hard one,\" {elder.pronoun()} said."
    )
    world.say(
        f"{child.id} and {helper.id} stood close together, and the cold no longer felt so sharp."
    )


def _reconcile(world: World, child: Entity, helper: Entity, elder: Entity, kernel: ObjectCfg, bale: ObjectCfg) -> None:
    child.memes["reconciliation"] += 1
    helper.memes["reconciliation"] += 1
    elder.memes["reconciliation"] += 1
    world.say(
        f"{child.id} placed the {kernel.label} back in the {bale.label}, and {helper.id} tucked it safe inside again."
    )
    world.say(
        f"After that, they walked the curb together, not as rivals but as friends."
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS.get(params.setting)
    kernel = KERNELS.get(params.kernel_kind)
    bale = BALES.get(params.bale_kind)
    if setting is None:
        raise StoryError("Unknown setting.")
    if kernel is None:
        raise StoryError("Unknown kernel.")
    if bale is None:
        raise StoryError("Unknown bale.")
    if "snow" not in setting.tags or "curb" not in setting.tags:
        raise StoryError("This fable must be set on a snowy curb.")

    world = World()
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type, role="child"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type, role="helper"))
    elder = world.add(Entity(id=params.elder_name, kind="character", type=params.elder_type, role="elder"))
    world.facts.update(setting=setting, child=child, helper=helper, elder=elder, kernel=kernel, bale=bale)

    _do_scene(world, child, helper, elder, kernel, bale, setting)
    world.para()
    _sneeze(world, helper, child, kernel, bale)
    world.para()
    _kindness(world, child, helper, elder, kernel, bale)
    propagate(world, narrate=True)
    world.para()
    _lesson(world, elder, child, helper)
    _reconcile(world, child, helper, elder, kernel, bale)

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable set on a snowy curb that includes the words "{f["kernel"].label}", "{f["bale"].label}", and "nostril".',
        f"Tell a short story about kindness, a lesson learned, and reconciliation when {f['helper'].id} sneezes and {f['child'].id} has to choose a kinder response.",
        f'Write a child-friendly fable where someone is teased, then forgiven, and the ending shows reconciliation beside a snowy curb.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, elder, kernel, bale = f["child"], f["helper"], f["elder"], f["kernel"], f["bale"]
    return [
        ("Where does the story happen?",
         f"It happens on a snowy curb beside a {bale.label}. The cold setting matters because it makes the characters notice warmth and kindness more clearly."),
        ("What caused the trouble?",
         f"{helper.id} sneezed, and the {kernel.label} bounced into the snow. That small accident led {child.id} to tease {helper.id} before kindness changed the moment."),
        ("How did the story end?",
         f"It ended with reconciliation. {child.id} gave the {kernel.label} back, the friends forgave each other, and the elder's lesson helped them all feel warm again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a nostril?",
         "A nostril is one of the two openings in a nose where air goes in and out. People and animals sneeze through their noses."),
        ("What is a kernel?",
         "A kernel is a small seed or grain. Corn kernels and sunflower kernels are both tiny pieces that can be found inside a husk or shell."),
        ("What is a bale?",
         "A bale is a large bundle tied together, often of hay or straw. Farmers stack bales to store them neatly."),
        ("What does kindness do in a story?",
         "Kindness helps characters stop hurting each other and choose a better way. It can turn a mistake into forgiveness and peace."),
        ("What is reconciliation?",
         "Reconciliation means making friends again after a disagreement. It happens when people stop being upset and decide to care for one another."),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    return [("snowy_curb", cn, ht, "corn", "hay") for cn in CHILD_NAMES for ht in HELPER_NAMES][:8]


ASP_RULES = r"""
setting(snowy_curb).
kernel(corn).
bale(hay).
snowy_curb_setting(S) :- setting(S).
valid(S,C,H,K,B) :- setting(S), kernel(K), bale(B), character(C), character(H), C != H.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("setting", "snowy_curb"),
        asp.fact("kernel", "corn"),
        asp.fact("bale", "hay"),
    ]
    for n in CHILD_NAMES:
        lines.append(asp.fact("character", n))
    for n in HELPER_NAMES:
        lines.append(asp.fact("character", n))
    for n in ELDER_NAMES:
        lines.append(asp.fact("character", n))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/5."))
    asp_set = set(asp.atoms(model, "valid"))
    py_set = set(valid_combos())
    if asp_set != py_set:
        print("MISMATCH between ASP and Python.")
        print("ASP:", sorted(asp_set))
        print("PY :", sorted(py_set))
        return 1
    print(f"OK: ASP and Python agree on {len(py_set)} combos.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world on a snowy curb.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--kernel", choices=KERNELS)
    ap.add_argument("--bale", choices=BALES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--elder")
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
    setting = args.setting or "snowy_curb"
    kernel = args.kernel or "corn"
    bale = args.bale or "hay"
    child_name = args.name or rng.choice(CHILD_NAMES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    elder_name = args.elder or rng.choice(ELDER_NAMES)
    return StoryParams(
        setting=setting,
        child_name=child_name,
        child_type="girl" if child_name in {"Mina", "Lina", "Iris"} else "boy",
        helper_name=helper_name,
        helper_type="bird" if helper_name in {"Blue Jay", "Sparrow"} else "mouse",
        elder_name=elder_name,
        elder_type="woman" if elder_name in {"Grandma", "Aunt June"} else "man",
        kernel_kind=kernel,
        bale_kind=bale,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams(
        setting="snowy_curb",
        child_name="Mina",
        child_type="girl",
        helper_name="Mouse",
        helper_type="mouse",
        elder_name="Grandma",
        elder_type="woman",
        kernel_kind="corn",
        bale_kind="hay",
    ),
    StoryParams(
        setting="quiet_lane",
        child_name="Otto",
        child_type="boy",
        helper_name="Rabbit",
        helper_type="rabbit",
        elder_name="Uncle Reed",
        elder_type="man",
        kernel_kind="sunflower",
        bale_kind="straw",
    ),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        try:
            sample = generate(CURATED[0])
            if not sample.story:
                raise RuntimeError("empty story")
            emit(sample)
        except Exception as exc:
            print(f"SMOKE TEST FAILED: {exc}")
            sys.exit(1)
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/5."))
        combos = sorted(set(asp.atoms(model, "valid")))
        for combo in combos:
            print(combo)
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
