#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/motley_stock_gerund_burn_reconciliation_friendship_fairy.py
==========================================================================================

A tiny fairy-tale storyworld about a motley patchwork cloak, a stock-gerund
("stocking"), a burn risk, and a reconciliation between friends.

The world keeps a small simulation with typed entities, physical meters, and
emotional memes. The story is not a frozen template; the state drives the prose:
one friend makes a risky choice, something singes, a wise helper intervenes, and
the friends reconcile through a mending act that leaves the ending image changed.

Seed words and features:
- motley
- stock-gerund
- burn
- reconciliation
- friendship
- fairy-tale style
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
FIRE_BURN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    flammable: bool = False
    can_mend: bool = False
    can_light: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "fairy", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Motif:
    id: str
    realm: str
    cloak: str
    gathering: str
    title: str
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
class Hazard:
    id: str
    label: str
    phrase: str
    flares: bool = True
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
class Helper:
    id: str
    label: str
    action: str
    remedy: str
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
    motif: str
    hazard: str
    helper: str
    name1: str
    type1: str
    name2: str
    type2: str
    reconciler: str
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
    def __init__(self) -> None:
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for mid, motif in MOTIFS.items():
        for hid, hz in HAZARDS.items():
            for aid, helper in HELPERS.items():
                if motif.cloak == "stocking" and hz.flares and helper.can_mend:
                    combos.append((mid, hid, aid))
    return combos


def reasonableness_gate(motif: Motif, hazard: Hazard, helper: Helper) -> bool:
    return motif.cloak == "stocking" and hazard.flares and helper.can_mend


def predict_burn(world: World, hazard_id: str) -> dict:
    sim = world.copy()
    _ignite(sim, sim.get(hazard_id), narrate=False)
    return {
        "burned": sim.get(hazard_id).meters["burned"] >= THRESHOLD,
        "spark": sim.get("cloak").meters["burned"] >= THRESHOLD,
    }


def _ignite(world: World, hazard_ent: Entity, narrate: bool = True) -> None:
    if hazard_ent.meters["burned"] >= THRESHOLD:
        return
    hazard_ent.meters["burned"] += 1
    cloak = world.get("cloak")
    cloak.meters["burned"] += 1
    cloak.memes["alarm"] += 1
    world.get("friend1").memes["fear"] += 1
    world.get("friend2").memes["fear"] += 1
    if narrate:
        world.say(
            f"The little flame licked the {cloak.label} and left a brown singe."
        )


def setup(world: World, a: Entity, b: Entity, motif: Motif) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"Once upon a bright evening, {a.id} and {b.id} made a motley game in "
        f"{motif.realm}. {motif.cloak}"
    )
    world.say(
        f"They laughed as if the whole grove were their hall, and they called "
        f"their play the {motif.gathering}."
    )


def temptation(world: World, a: Entity, b: Entity, hazard: Hazard) -> None:
    a.memes["boldness"] += 1
    world.say(
        f'But {a.id} saw {hazard.phrase} glowing near the candle and whispered, '
        f'"Just a little closer."'
    )
    world.say(f"{b.id} frowned, for the air had gone thin and dry.")


def warning(world: World, b: Entity, a: Entity, hazard: Hazard) -> None:
    pred = predict_burn(world, "spark")
    b.memes["care"] += 1
    world.facts["predicted_burn"] = pred["burned"]
    world.say(
        f'"No," said {b.id}. "A flame can burn the stock and the cloak with one '
        f"small kiss. Come back from the candle, {a.id}.""
    )


def quarrel(world: World, a: Entity, b: Entity) -> None:
    a.memes["stubborn"] += 1
    b.memes["hurt"] += 1
    world.say(
        f"{a.id} crossed {a.pronoun('possessive')} arms, and the two friends "
        f"turned away from one another."
    )


def mend_turn(world: World, helper: Entity, a: Entity, b: Entity, motif: Motif) -> None:
    helper.memes["kindness"] += 1
    a.memes["guilt"] += 1
    b.memes["hope"] += 1
    world.say(
        f"Then {helper.id} arrived with {helper.label} and {helper.action}, "
        f"and the room grew quiet."
    )
    world.say(
        f'"A singe is not the end of a story," said {helper.id}. "You may mend '
        f"the {motif.cloak} together, one careful stitch at a time."'
    )


def reconcile(world: World, a: Entity, b: Entity, helper: Entity, motif: Motif) -> None:
    cloak = world.get("cloak")
    cloak.meters["mended"] += 1
    a.memes["guilt"] = 0.0
    b.memes["hurt"] = 0.0
    a.memes["love"] += 1
    b.memes["love"] += 1
    a.memes["friendship"] += 1
    b.memes["friendship"] += 1
    world.say(
        f"{a.id} and {b.id} sat side by side and mended the {motif.cloak} until "
        f"the torn place became a bright new patch."
    )
    world.say(
        f"They forgave each other, and their friendship returned warmer than "
        f"before."
    )


def ending(world: World, a: Entity, b: Entity, motif: Motif) -> None:
    cloak = world.get("cloak")
    if cloak.meters["mended"] >= THRESHOLD:
        world.say(
            f"In the end, the motley cloak shone again, stitched with a fresh "
            f"patch where the burn had been."
        )
    else:
        world.say(
            f"In the end, they kept the cloak away from the candle and watched it "
            f"flutter safely in the dusk."
        )


def tell(motif: Motif, hazard: Hazard, helper: Helper, name1: str, type1: str,
         name2: str, type2: str, reconciler: str) -> World:
    world = World()
    a = world.add(Entity(id=name1, kind="character", type=type1, role="friend1"))
    b = world.add(Entity(id=name2, kind="character", type=type2, role="friend2"))
    h = world.add(Entity(id=reconciler, kind="character", type="fairy", role="reconciler"))
    cloak = world.add(Entity(id="cloak", type="thing", label=motif.cloak, flammable=True))
    spark = world.add(Entity(id="spark", type="thing", label=hazard.label, flammable=False))
    world.facts.update(motif=motif, hazard=hazard, helper=helper, spark=spark)

    setup(world, a, b, motif)
    world.para()
    temptation(world, a, b, hazard)
    warning(world, b, a, hazard)
    quarrel(world, a, b)
    world.para()

    ignite = True
    if not hazard.flares:
        ignite = False
    if ignite:
        _ignite(world, world.get("spark"), narrate=True)
    mend_turn(world, h, a, b, motif)
    world.para()
    reconcile(world, a, b, h, motif)
    ending(world, a, b, motif)

    world.facts.update(
        friend1=a, friend2=b, reconciler=h, cloak=cloak, outcome="reconciled",
        burned=cloak.meters["burned"] >= THRESHOLD,
        mended=cloak.meters["mended"] >= THRESHOLD,
    )
    return world


MOTIFS = {
    "motley": Motif(
        id="motley",
        realm="the greenwood",
        cloak="motley cloak",
        gathering="motley dance",
        title="The Motley Cloak",
    ),
    "lantern": Motif(
        id="lantern",
        realm="the moonlit glade",
        cloak="stocking",
        gathering="stocking song",
        title="The Stocking and the Lantern",
    ),
    "stitch": Motif(
        id="stitch",
        realm="the old garden",
        cloak="stocking cloak",
        gathering="stocking parade",
        title="The Stitching Fair",
    ),
}

HAZARDS = {
    "candle": Hazard(
        id="candle",
        label="candle flame",
        phrase="a candle flame",
        flares=True,
        tags={"burn", "fire"},
    ),
    "embers": Hazard(
        id="embers",
        label="ember",
        phrase="a handful of embers",
        flares=True,
        tags={"burn", "fire"},
    ),
}

HELPERS = {
    "fairy": Helper(
        id="fairy",
        label="a silver needle",
        action="mended the torn edge with silver thread",
        remedy="reconcile",
        tags={"reconciliation", "friendship"},
    ),
    "grandmother": Helper(
        id="grandmother",
        label="a wooden hoop",
        action="held the cloth steady with gentle hands",
        remedy="reconcile",
        tags={"reconciliation", "friendship"},
    ),
}

NAMES = ["Iris", "Pip", "Mina", "Rowan", "Elsie", "Tobin"]
TYPES = ["girl", "boy"]


@dataclass
class WorldKnowledge:
    prompt: str
    answer: str
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


KNOWLEDGE = {
    "burn": [
        WorldKnowledge(
            prompt="Why can a candle burn cloth?",
            answer="A candle flame is hot enough to singe cloth. Thin cloth can catch a burn mark very quickly if it touches the flame.",
        )
    ],
    "friendship": [
        WorldKnowledge(
            prompt="What helps friends stay friends after a quarrel?",
            answer="Talking kindly, saying sorry, and doing something gentle together can help friends stay friends after a quarrel.",
        )
    ],
    "reconciliation": [
        WorldKnowledge(
            prompt="What is reconciliation?",
            answer="Reconciliation is when people stop arguing, forgive one another, and become friendly again.",
        )
    ],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale storyworld with motley cloth, a burn risk, and reconciliation.")
    ap.add_argument("--motif", choices=sorted(MOTIFS))
    ap.add_argument("--hazard", choices=sorted(HAZARDS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--name1")
    ap.add_argument("--type1", choices=TYPES)
    ap.add_argument("--name2")
    ap.add_argument("--type2", choices=TYPES)
    ap.add_argument("--reconciler")
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
    if args.motif and args.hazard and args.helper:
        if not reasonableness_gate(MOTIFS[args.motif], HAZARDS[args.hazard], HELPERS[args.helper]):
            raise StoryError("No story: this fairy tale needs a burn risk, a motley cloth, and a mending helper.")
    combos = [c for c in valid_combos()
              if (args.motif is None or c[0] == args.motif)
              and (args.hazard is None or c[1] == args.hazard)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    motif, hazard, helper = rng.choice(sorted(combos))
    name1 = args.name1 or rng.choice(NAMES)
    name2 = args.name2 or rng.choice([n for n in NAMES if n != name1])
    type1 = args.type1 or rng.choice(TYPES)
    type2 = args.type2 or rng.choice([t for t in TYPES])
    reconciler = args.reconciler or rng.choice(["Thistledown", "Bracken", "Willow"])
    return StoryParams(
        motif=motif,
        hazard=hazard,
        helper=helper,
        name1=name1,
        type1=type1,
        name2=name2,
        type2=type2,
        reconciler=reconciler,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    motif: Motif = f["motif"]
    hazard: Hazard = f["hazard"]
    return [
        f'Write a fairy tale for a young child that uses the words "{motif.id}", "{hazard.id}", and "reconciliation".',
        f"Tell a friendship story where two little friends argue near a candle and later make up while mending a {motif.cloak}.",
        f'Write a gentle tale with a motley mood, a burn scare, and a happy ending about friends becoming kind again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a: Entity = f["friend1"]
    b: Entity = f["friend2"]
    h: Entity = f["reconciler"]
    motif: Motif = f["motif"]
    answered = [
        QAItem(
            question="Who are the story friends?",
            answer=f"The story is about {a.id} and {b.id}, two friends who begin the tale in a motley little quarrel and end it reconciled.",
        ),
        QAItem(
            question="What caused the trouble?",
            answer=f"{a.id} leaned too near {f['hazard'].phrase}, and the flame singed the {motif.cloak}. That made the friends upset before {h.id} helped them mend it.",
        ),
        QAItem(
            question="How did the friends become friendly again?",
            answer=f"{h.id} brought a gentle mending task, and {a.id} and {b.id} worked together until the torn place became a fresh patch. That shared work turned their quarrel into reconciliation.",
        ),
    ]
    return answered


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = set(world.facts["hazard"].tags) | {"friendship", "reconciliation"}
    for key, items in KNOWLEDGE.items():
        if key in tags:
            for item in items:
                out.append(QAItem(question=item.prompt, answer=item.answer))
    return out


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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.can_mend:
            bits.append("can_mend=True")
        if e.flammable:
            bits.append("flammable=True")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
motif_ok(M) :- motif(M).
hazard_ok(H) :- hazard(H), flares(H).
helper_ok(K) :- helper(K), can_mend(K).
valid(M,H,K) :- motif_ok(M), hazard_ok(H), helper_ok(K).
burn(H) :- hazard(H), flares(H).
reconcile :- valid(M,H,K).
#show valid/3.
#show burn/1.
#show reconcile/0.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mid in MOTIFS:
        lines.append(asp.fact("motif", mid))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        if h.flares:
            lines.append(asp.fact("flares", hid))
    for kid in HELPERS:
        lines.append(asp.fact("helper", kid))
        lines.append(asp.fact("can_mend", kid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH between ASP and Python valid_combos().")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as exc:
        print(f"FAIL: story generation crashed: {exc}")
        return 1
    if rc == 0:
        print("OK: ASP and Python parity checks passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.motif not in MOTIFS or params.hazard not in HAZARDS or params.helper not in HELPERS:
        raise StoryError("Invalid story parameters.")
    motif = MOTIFS[params.motif]
    hazard = HAZARDS[params.hazard]
    helper = HELPERS[params.helper]
    if not reasonableness_gate(motif, hazard, helper):
        raise StoryError("No story: the chosen pieces do not make a fairytale burn-and-mending scene.")
    world = tell(motif, hazard, helper, params.name1, params.type1, params.name2, params.type2, params.reconciler)
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


CURATED = [
    StoryParams(motif="motley", hazard="candle", helper="fairy", name1="Iris", type1="girl", name2="Pip", type2="boy", reconciler="Thistledown"),
    StoryParams(motif="lantern", hazard="embers", helper="grandmother", name1="Mina", type1="girl", name2="Tobin", type2="boy", reconciler="Willow"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show burn/1.\n#show reconcile/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for m, h, k in combos:
            print(f"  {m:8} {h:8} {k}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
