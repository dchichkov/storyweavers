#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/goods_swoosh_surprise_cautionary_nursery_rhyme.py
=================================================================================

A tiny storyworld in a nursery-rhyme style: a child or two carry a little bundle
of goods, a swooshy surprise sends the goods flying, and a cautious helper keeps
the trouble small. The domain is small on purpose: one package, one risky path,
one sensible warning, and one bright ending image.

The story stays grounded in the simulated world:
- goods have physical state (meters) and emotional state (memes)
- a swoosh can knock the goods loose
- a surprise helper can avert or soften the spill
- a cautious helper warns before the swoosh goes too far

The prose aims for a gentle, rhythmic feel without becoming a frozen template.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CAUTION_MIN = 2.0
SURPRISE_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Goods:
    id: str
    label: str
    phrase: str
    contents: str
    weight: int
    fragile: bool
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
class Path:
    id: str
    label: str
    swoosh_word: str
    breeze: str
    risk_image: str
    spread: int
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
class Surprise:
    id: str
    label: str
    phrase: str
    reveal: str
    help_text: str
    help_power: int
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
class Caution:
    id: str
    label: str
    warning: str
    good_sentence: str
    sense: int
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["wobble"] < THRESHOLD:
            continue
        sig = ("spill", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["spill"] += 1
        e.memes["worry"] += 1
        goods = world.entities.get("goods")
        if goods:
            goods.meters["scatter"] += 1
            goods.memes["alarm"] += 1
        out.append("__spill__")
    return out


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["calm"] < THRESHOLD:
            continue
        sig = ("settle", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        goods = world.entities.get("goods")
        if goods:
            goods.meters["scatter"] = max(0.0, goods.meters["scatter"] - 1)
            goods.memes["safe"] += 1
        out.append("__settle__")
    return out


CAUSAL_RULES = [Rule("spill", "physical", _r_spill), Rule("settle", "social", _r_settle)]


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


def _do_swoosh(world: World, path: Entity, goods: Entity, narrate: bool = True) -> None:
    path.meters["wobble"] += 1
    goods.meters["spill"] += 1
    goods.memes["startle"] += 1
    propagate(world, narrate=narrate)


def _do_calm(world: World, helper: Entity) -> None:
    helper.memes["care"] += 1
    helper.meters["calm"] += 1
    propagate(world, narrate=False)


def hazard_at_risk(goods: Goods, path: Path) -> bool:
    return goods.fragile and path.spread >= 1


def sensible_surprise(surprise: Surprise) -> bool:
    return surprise.help_power >= 1


def sensible_caution(caution: Caution) -> bool:
    return caution.sense >= CAUTION_MIN


def outcome_of(params: "StoryParams") -> str:
    if params.caution == "none":
        return "spill"
    if params.path == "windy_lane" and params.surprise == "helper_cat":
        return "safe"
    return "spill"


def tell(goods: Goods, path: Path, surprise: Surprise, caution: Caution,
         child_name: str = "Mimi", child_type: str = "girl",
         helper_name: str = "Nell", helper_type: str = "girl") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    pack = world.add(Entity(id="goods", kind="thing", type="goods", label=goods.label))
    lane = world.add(Entity(id="path", kind="thing", type="path", label=path.label))

    child.memes["joy"] += 1
    helper.memes["care"] += 1

    world.say(
        f"Little {child.id} went a-tripping down the lane, with {goods.phrase} held neat and plain."
    )
    world.say(
        f"'{surprise.phrase},' came a cheerful cry, and the breeze went {path.swoosh_word} by.'"
    )

    world.para()
    world.say(
        f"But {helper.id} gave a tiny warning: \"{caution.warning} {caution.good_sentence}\""
    )

    if caution.sense >= CAUTION_MIN:
        _do_calm(world, helper)
        helper.memes["relief"] += 1
    else:
        helper.memes["doubt"] += 1

    if surprise.help_power > 1:
        child.memes["surprise"] += 1

    if path.spread and goods.fragile:
        _do_swoosh(world, lane, pack, narrate=False)
        world.say(
            f"Then came a great {path.swoosh_word} and the bundle went wobble and whirr."
        )
        if surprise.help_power >= 2:
            pack.meters["scatter"] = max(0.0, pack.meters["scatter"] - 1)
            world.say(
                f"{surprise.help_text}, and the little goods stayed mostly together."
            )
        else:
            world.say(
                f"The goods popped apart, one by one, with a soft little clatter."
            )
    else:
        world.say(
            f"The lane stayed calm, and the {goods.label} rode on safely."
        )

    world.para()
    if pack.meters["scatter"] >= THRESHOLD:
        world.say(
            f"{helper.id} bent down, gathered the {goods.label}, and tied them back with a ribbon."
        )
        world.say(
            f"{child.id} hugged {helper.pronoun('object')} tight, and the night grew warm and still."
        )
    else:
        world.say(
            f"{surprise.reveal} The goods were safe, and {child.id} laughed at the tidy little save."
        )

    world.facts.update(
        child=child,
        helper=helper,
        goods_cfg=goods,
        path_cfg=path,
        surprise_cfg=surprise,
        caution_cfg=caution,
        pack=pack,
        lane=lane,
        outcome="safe" if pack.meters["scatter"] < THRESHOLD else "spill",
    )
    return world


GOODS = {
    "basket": Goods(
        id="basket",
        label="basket",
        phrase="a basket of goods",
        contents="apples and buns",
        weight=2,
        fragile=True,
        tags={"goods", "basket"},
    ),
    "parcel": Goods(
        id="parcel",
        label="parcel",
        phrase="a parcel of goods",
        contents="buttons and thread",
        weight=1,
        fragile=True,
        tags={"goods", "parcel"},
    ),
    "bundle": Goods(
        id="bundle",
        label="bundle",
        phrase="a bundle of goods",
        contents="candies and cloth",
        weight=1,
        fragile=False,
        tags={"goods", "bundle"},
    ),
}

PATHS = {
    "windy_lane": Path(
        id="windy_lane",
        label="the windy lane",
        swoosh_word="swoosh",
        breeze="a brisk little breeze",
        risk_image="the basket edge",
        spread=1,
        tags={"swoosh", "wind"},
    ),
    "river_walk": Path(
        id="river_walk",
        label="the river walk",
        swoosh_word="whoosh",
        breeze="a cool river breeze",
        risk_image="the parcel string",
        spread=1,
        tags={"swoosh", "water"},
    ),
}

SURPRISES = {
    "helper_cat": Surprise(
        id="helper_cat",
        label="a helper cat",
        phrase="out popped a helper cat",
        reveal="And what a surprise, the cat wore a red scarf!",
        help_text="The cat batted the basket back with a paw.",
        help_power=2,
        tags={"surprise", "cat"},
    ),
    "towel": Surprise(
        id="towel",
        label="a towel",
        phrase="up flew a fluttery towel",
        reveal="And what a surprise, a towel came drifting down like snow!",
        help_text="The towel wrapped the goods in a snug little fold.",
        help_power=1,
        tags={"surprise", "towel"},
    ),
}

CAUTIONS = {
    "gentle_stop": Caution(
        id="gentle_stop",
        label="gentle stop",
        warning="Mind the swoosh, dear heart,",
        good_sentence="let us hold the goods with both hands.",
        sense=2,
        tags={"caution"},
    ),
    "step_aside": Caution(
        id="step_aside",
        label="step aside",
        warning="Stand a little back, now,",
        good_sentence="and keep the parcel from the breeze.",
        sense=3,
        tags={"caution"},
    ),
    "none": Caution(
        id="none",
        label="none",
        warning="",
        good_sentence="",
        sense=0,
        tags=set(),
    ),
}


@dataclass
class StoryParams:
    goods: str
    path: str
    surprise: str
    caution: str
    child: str
    child_type: str
    helper: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for g in GOODS.values():
        for p in PATHS.values():
            if not hazard_at_risk(g, p):
                continue
            for s in SURPRISES.values():
                if not sensible_surprise(s):
                    continue
                for c in CAUTIONS.values():
                    if sensible_caution(c):
                        combos.append((g.id, p.id, s.id, c.id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A little nursery-rhyme storyworld of goods, swoosh, surprise, and caution.")
    ap.add_argument("--goods", choices=GOODS)
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--caution", choices=CAUTIONS)
    ap.add_argument("--child")
    ap.add_argument("--helper")
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
    if args.caution and args.caution not in CAUTIONS:
        raise StoryError("Unknown caution choice.")
    combos = [c for c in valid_combos()
              if (args.goods is None or c[0] == args.goods)
              and (args.path is None or c[1] == args.path)
              and (args.surprise is None or c[2] == args.surprise)
              and (args.caution is None or c[3] == args.caution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    goods, path, surprise, caution = rng.choice(sorted(combos))
    child = args.child or rng.choice(["Mimi", "Lily", "Nora", "Toby"])
    helper = args.helper or rng.choice(["Nell", "Mabel", "Joan", "Pip"])
    child_type = "girl" if child in {"Mimi", "Lily", "Nora"} else "boy"
    helper_type = "girl" if helper in {"Nell", "Mabel", "Joan"} else "boy"
    return StoryParams(goods=goods, path=path, surprise=surprise, caution=caution,
                       child=child, child_type=child_type, helper=helper, helper_type=helper_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a nursery-rhyme story with the words goods and swoosh about {f['child'].id} carrying goods on {f['path_cfg'].label}.",
        f"Tell a cautious little story where {f['helper'].id} warns about the swoosh and a surprise helps save the goods.",
        f"Make a gentle cautionary rhyme about a bundle of goods, a sudden swoosh, and a safe ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper = f["child"], f["helper"]
    goods, path, surprise, caution = f["goods_cfg"], f["path_cfg"], f["surprise_cfg"], f["caution_cfg"]
    pack = f["pack"]
    answers = [
        QAItem(
            question="What were the goods like?",
            answer=f"They were {goods.phrase}, and they were small enough to carry but easy to scatter. That made the swooshy path risky for them."
        ),
        QAItem(
            question="What did the helper say?",
            answer=f"{helper.id} said, \"{caution.warning} {caution.good_sentence}\" The warning mattered because the path could send the goods wobbling."
        ),
        QAItem(
            question="What happened to the goods?",
            answer=(
                f"{'They stayed together with help from the surprise.' if pack.meters['scatter'] < THRESHOLD else 'They scattered, then were gathered back up.'} "
                f"The ending shows whether the swoosh was calmed in time."
            ),
        ),
    ]
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    items = [
        QAItem(
            question="What is a swoosh?",
            answer="A swoosh is a swift whooshing movement or sound, like wind or a fast swish in the air. It can jostle light things that are not held carefully."
        ),
        QAItem(
            question="Why is caution useful?",
            answer="Caution helps you slow down and notice a danger before it grows. A warning can keep small things from becoming messy or lost."
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is something unexpected that pops up at just the right moment. In this story, the surprise can help the goods stay safe."
        ),
        QAItem(
            question="What are goods?",
            answer="Goods are things being carried or kept together, like a little bundle, basket, or parcel. They can be precious even when they are small."
        ),
    ]
    return items


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for gid, g in GOODS.items():
        lines.append(asp.fact("goods", gid))
        if g.fragile:
            lines.append(asp.fact("fragile", gid))
    for pid, p in PATHS.items():
        lines.append(asp.fact("path", pid))
        lines.append(asp.fact("spread", pid, p.spread))
        lines.append(asp.fact("swoosh_word", pid, p.swoosh_word))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise", sid))
        lines.append(asp.fact("help_power", sid, s.help_power))
    for cid, c in CAUTIONS.items():
        lines.append(asp.fact("caution", cid))
        lines.append(asp.fact("sense", cid, c.sense))
    lines.append(asp.fact("sense_min", CAUTION_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
hazard(G,P) :- goods(G), path(P), fragile(G), spread(P,S), S >= 1.
sensible_caution(C) :- caution(C), sense(C,S), sense_min(M), S >= M.
valid(G,P,S,C) :- hazard(G,P), surprise(S), sensible_caution(C).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_cautions() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible_caution/1."))
    return sorted(c for (c,) in asp.atoms(model, "sensible_caution"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos.")
        rc = 1
    else:
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    if set(asp_sensible_cautions()) != {c.id for c in CAUTIONS.values() if c.sense >= CAUTION_MIN}:
        print("MISMATCH in caution sensibility.")
        rc = 1
    else:
        print("OK: sensible cautions match.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: ordinary story generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def explain_rejection() -> str:
    return "No story: the goods and the swoosh must make a real little risk, with a sensible caution and a helpful surprise."


def generate(params: StoryParams) -> StorySample:
    if params.goods not in GOODS or params.path not in PATHS or params.surprise not in SURPRISES or params.caution not in CAUTIONS:
        raise StoryError("Invalid parameter key.")
    goods = GOODS[params.goods]
    path = PATHS[params.path]
    surprise = SURPRISES[params.surprise]
    caution = CAUTIONS[params.caution]
    if not hazard_at_risk(goods, path):
        raise StoryError(explain_rejection())
    if not sensible_surprise(surprise):
        raise StoryError("No story: the surprise must be able to help.")
    if not sensible_caution(caution):
        raise StoryError("No story: the caution must be wise enough to matter.")
    world = tell(goods, path, surprise, caution, params.child, params.child_type, params.helper, params.helper_type)
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


def resolve_params_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.goods is None or c[0] == args.goods)
              and (args.path is None or c[1] == args.path)
              and (args.surprise is None or c[2] == args.surprise)
              and (args.caution is None or c[3] == args.caution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    goods, path, surprise, caution = rng.choice(sorted(combos))
    child = args.child or rng.choice(["Mimi", "Lily", "Nora", "Toby"])
    helper = args.helper or rng.choice(["Nell", "Mabel", "Joan", "Pip"])
    child_type = "girl" if child in {"Mimi", "Lily", "Nora"} else "boy"
    helper_type = "girl" if helper in {"Nell", "Mabel", "Joan"} else "boy"
    return StoryParams(goods=goods, path=path, surprise=surprise, caution=caution,
                       child=child, child_type=child_type, helper=helper, helper_type=helper_type)


def build_parser_alias() -> argparse.ArgumentParser:
    return build_parser()


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params_from_args(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4.\n#show sensible_caution/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (goods, path, surprise, caution) combos:\n")
        for item in asp_valid_combos():
            print("  ", item)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(goods="basket", path="windy_lane", surprise="helper_cat", caution="step_aside", child="Mimi", child_type="girl", helper="Nell", helper_type="girl"),
            StoryParams(goods="parcel", path="river_walk", surprise="towel", caution="gentle_stop", child="Toby", child_type="boy", helper="Pip", helper_type="boy"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
