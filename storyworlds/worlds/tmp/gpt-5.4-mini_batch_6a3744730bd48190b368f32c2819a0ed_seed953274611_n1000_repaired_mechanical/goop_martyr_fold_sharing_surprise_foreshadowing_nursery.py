#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/goop_martyr_fold_sharing_surprise_foreshadowing_nursery.py
===========================================================================================

A tiny nursery-rhyme storyworld about a child, a sticky goop, a folded paper
gift, sharing, a surprise, and a little foreshadowed turn.

The world is built as a small simulation: typed entities carry physical meters
and emotional memes, state changes drive prose, and the ending depends on what
the characters do with the goop and the fold. The style is kept simple, musical,
and child-facing.
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
SENSE_MIN = 2


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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Child:
    id: str
    type: str
    trait: str
    loves: str
    shares: bool = True
    wears: str = ""
    maker: str = ""
    surprise_kind: str = ""
    foreshadow: str = ""
    meter_need: float = 0.0
    meter_splatter: float = 0.0
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
class Goop:
    id: str
    label: str
    sticky: bool = True
    messy: bool = True
    sweet: bool = False
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
class Fold:
    id: str
    label: str
    shape: str
    can_hide: bool = True
    can_open: bool = True
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
    reveal: str
    delight: str
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


def _r_splatter(world: World) -> list[str]:
    out: list[str] = []
    goo = world.get("goop")
    if goo.meters["used"] < THRESHOLD:
        return out
    for cid in ("pip", "mara"):
        child = world.get(cid)
        if child.meters["mess"] >= THRESHOLD:
            sig = ("splat", cid)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            child.memes["embarrassed"] += 1
            out.append(f"{child.id} got a little goop on {child.pronoun('possessive')} hands.")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    if world.get("goop").meters["shared"] < THRESHOLD:
        return out
    sig = ("share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("pip").memes["joy"] += 1
    world.get("mara").memes["joy"] += 1
    out.append("Both friends felt lighter, because sharing made the little table less lonely.")
    return out


def _r_open(world: World) -> list[str]:
    out: list[str] = []
    if world.get("fold").meters["opened"] < THRESHOLD:
        return out
    sig = ("open",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("surprise").meters["revealed"] += 1
    out.append("The folded thing opened wide, and a secret smile came out.")
    return out


CAUSAL_RULES = [Rule("splatter", "physical", _r_splatter), Rule("share", "social", _r_share), Rule("open", "turn", _r_open)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def goop_risk(goop: Goop, fold: Fold) -> bool:
    return goop.messy and fold.can_hide


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def is_surprising(goop: Goop, fold: Fold, surprise: Surprise) -> bool:
    return goop.sticky and fold.can_open and bool(surprise.reveal)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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


RESPONSES = {
    "wipe": Response(
        id="wipe",
        sense=3,
        power=3,
        text="wiped the goop with a soft cloth and kept the fold neat",
        fail="wiped at the goop, but the sticky patch only spread wider",
        qa_text="wiped the goop away with a soft cloth",
        tags={"clean", "share"},
    ),
    "share": Response(
        id="share",
        sense=3,
        power=2,
        text="shared the spoon, the bowl, and the best idea at the table",
        fail="tried to share, but the goop was already dripping everywhere",
        qa_text="shared the spoon and the bowl",
        tags={"share"},
    ),
    "open_gently": Response(
        id="open_gently",
        sense=2,
        power=2,
        text="opened the fold gently and found the surprise tucked inside",
        fail="opened the fold too fast and bent the paper edge",
        qa_text="opened the fold gently",
        tags={"surprise"},
    ),
    "too_hasty": Response(
        id="too_hasty",
        sense=1,
        power=1,
        text="shook the fold and made the paper rattle",
        fail="shook the fold, but that was not a wise way to do it",
        qa_text="shook the fold",
        tags={"bad"},
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for g in GOOPS:
        for f in FOLDS:
            for s in SURPRISES:
                if goop_risk(g, f) and is_surprising(g, f, s):
                    out.append((g.id, f.id, s.id))
    return out


@dataclass
class StoryParams:
    goop: str
    fold: str
    surprise: str
    response: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
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


GOOPS = {
    "jam_goop": Goop(id="jam_goop", label="jam goop", sweet=True, tags={"goop", "sweet"}),
    "paint_goop": Goop(id="paint_goop", label="paint goop", sweet=False, tags={"goop", "paint"}),
}

FOLDS = {
    "paper_fold": Fold(id="paper_fold", label="paper fold", shape="little square", tags={"fold"}),
    "gift_fold": Fold(id="gift_fold", label="gift fold", shape="small parcel", tags={"fold", "gift"}),
}

SURPRISES = {
    "song": Surprise(id="song", label="song surprise", reveal="a tiny song card", delight="a song burst", tags={"surprise"}),
    "sticker": Surprise(id="sticker", label="sticker surprise", reveal="a bright sticker", delight="a sticker shine", tags={"surprise"}),
}

GIRL_NAMES = ["Mina", "Luna", "Tia", "Nia", "Pia", "Wren"]
BOY_NAMES = ["Pip", "Ned", "Bo", "Joss", "Rex", "Cal"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme goop and fold storyworld.")
    ap.add_argument("--goop", choices=GOOPS)
    ap.add_argument("--fold", choices=FOLDS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name1")
    ap.add_argument("--gender1", choices=["girl", "boy"])
    ap.add_argument("--name2")
    ap.add_argument("--gender2", choices=["girl", "boy"])
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
    combo_pool = [c for c in valid_combos()
                  if (args.goop is None or c[0] == args.goop)
                  and (args.fold is None or c[1] == args.fold)
                  and (args.surprise is None or c[2] == args.surprise)]
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("That response is too flimsy for this little story.")
    if not combo_pool:
        raise StoryError("(No valid combination matches the given options.)")
    goop, fold, surprise = rng.choice(sorted(combo_pool))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    g1 = args.gender1 or rng.choice(["girl", "boy"])
    g2 = args.gender2 or ("boy" if g1 == "girl" else "girl")
    n1 = args.name1 or rng.choice(GIRL_NAMES if g1 == "girl" else BOY_NAMES)
    n2 = args.name2 or rng.choice([n for n in (GIRL_NAMES if g2 == "girl" else BOY_NAMES) if n != n1])
    return StoryParams(goop=goop, fold=fold, surprise=surprise, response=response,
                       child1=n1, child1_gender=g1, child2=n2, child2_gender=g2)


def tell(params: StoryParams) -> World:
    world = World()
    a = world.add(Entity(id=params.child1, kind="character", type=params.child1_gender, role="share"))
    b = world.add(Entity(id=params.child2, kind="character", type=params.child2_gender, role="share"))
    goop = world.add(Entity(id="goop", type="thing", label=GOOPS[params.goop].label))
    fold = world.add(Entity(id="fold", type="thing", label=FOLDS[params.fold].label))
    surprise = world.add(Entity(id="surprise", type="thing", label=SURPRISES[params.surprise].label))
    a.memes["curious"] += 1
    b.memes["curious"] += 1
    world.say(f"{a.id} and {b.id} were two small friends at a sunny little table.")
    world.say(f"They had {goop.label} and a {fold.label}, and a hush before the song.")
    world.say(f'"Let us share," said {a.id}. "{b.id} may have the spoon, and I may have the bowl."')
    world.para()
    a.meters["mess"] += 1
    goop.meters["used"] += 1
    propagate(world, narrate=False)
    world.say(f"The goop went round and round, and the table got just a bit sticky.")
    world.say(f"But then the {fold.label} gave a tiny wink, as if it knew a secret.")
    world.say(f'{b.id} whispered, "I think there is a surprise tucked inside."')
    world.para()
    fold.meters["opened"] += 1
    world.say(f"{a.id} opened the fold gently.")
    propagate(world, narrate=False)
    if world.get("surprise").meters["revealed"] >= THRESHOLD:
        world.say(f"Out came {surprise.reveal}, and its little delight made both children laugh.")
    response = RESPONSES[params.response]
    if response.id == "wipe":
        world.say(f"Then {a.id} {response.text}.")
    elif response.id == "share":
        world.say(f"Then {a.id} {response.text}.")
    else:
        world.say(f"Then {a.id} {response.text}.")
    world.say(f"The sticky goop was tidied, the fold was opened, and the day ended bright and neat.")
    world.facts.update(params=params, a=a, b=b, goop=GOOPS[params.goop], fold=FOLDS[params.fold],
                       surprise=SURPRISES[params.surprise], response=response,
                       shared=True, revealed=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme style story that includes the words "{f["goop"].label}", "martyr", and "fold".',
        f"Tell a small sharing story where {f['a'].id} and {f['b'].id} pass around {f['goop'].label} and then open a {f['fold'].label} for a surprise.",
        f'Write a gentle foreshadowing story: there is sticky goop, a folded secret, and a happy surprise at the end.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b = f["a"], f["b"]
    return [
        ("Who is the story about?", f"It is about {a.id} and {b.id}, two little friends at a sharing table."),
        ("What did they share?", f"They shared {f['goop'].label} and the spoon and bowl, taking turns kindly."),
        ("What happened when they opened the fold?", f"They found {f['surprise'].reveal}. That was the surprise that had been hinted at earlier in the story."),
        ("How did the story end?", "It ended happy and neat, with the sticky mess cleaned and the surprise fully revealed."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is goop?", "Goop is a sticky, messy substance that can smear onto hands and tables."),
        ("What is a fold?", "A fold is a bend in paper or cloth, and folded things can hide a secret inside."),
        ("What is a surprise?", "A surprise is something you do not expect, like a hidden note or a small gift."),
        ("What does sharing mean?", "Sharing means taking turns and letting someone else use the thing too."),
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(goop="jam_goop", fold="paper_fold", surprise="song", response="wipe",
                child1="Pip", child1_gender="boy", child2="Mina", child2_gender="girl"),
    StoryParams(goop="paint_goop", fold="gift_fold", surprise="sticker", response="open_gently",
                child1="Luna", child1_gender="girl", child2="Bo", child2_gender="boy"),
]


def explain_rejection(goop: Goop, fold: Fold) -> str:
    if not goop_risk(goop, fold):
        return "(No story: this goop and fold do not make a strong enough little problem.)"
    return "(No story: this combination does not fit the nursery-rhyme turn we want.)"


def outcome_of(params: StoryParams) -> str:
    return "shared_surprise"


ASP_RULES = r"""
goop_risk(G, F) :- goop(G), fold(F).
shared_surprise :- chosen_response(R), response(R), sense(R, S), sense_min(M), S >= M.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("sense_min", SENSE_MIN)]
    for gid in GOOPS:
        lines.append(asp.fact("goop", gid))
    for fid in FOLDS:
        lines.append(asp.fact("fold", fid))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise", sid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show shared_surprise/0."))
    return ["shared_surprise"] if asp.atoms(model, "shared_surprise") else []


def asp_verify() -> int:
    rc = 0
    if set(r.id for r in sensible_responses()) != {"wipe", "share", "open_gently"}:
        print("MISMATCH in sensible responses.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        if not sample.story:
            raise RuntimeError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.goop not in GOOPS or params.fold not in FOLDS or params.surprise not in SURPRISES or params.response not in RESPONSES:
        raise StoryError("Invalid params for this world.")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show shared_surprise/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("sensible responses:", ", ".join(sorted(r.id for r in sensible_responses())))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
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
    for i, s in enumerate(samples):
        hdr = ""
        if args.all:
            p = s.params
            hdr = f"### {p.child1} & {p.child2}: {p.goop} / {p.fold} / {p.surprise} ({outcome_of(p)})"
        elif len(samples) > 1:
            hdr = f"### variant {i + 1}"
        emit(s, trace=args.trace, qa=args.qa, header=hdr)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
