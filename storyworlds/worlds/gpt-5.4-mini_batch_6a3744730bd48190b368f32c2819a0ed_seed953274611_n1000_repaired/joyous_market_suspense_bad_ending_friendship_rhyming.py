#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/joyous_market_suspense_bad_ending_friendship_rhyming.py
=======================================================================================

A tiny storyworld set in a market: two friends share a cheerful shopping day,
worry over a missing helper, choose a risky shortcut, and sometimes end with a
bad outcome that still proves their friendship.

The world is built for rhyming, suspenseful TinyStories-style prose. It models a
small market lane, a tempting shortcut, a risky wait, and a final loss or repair
that changes the ending image.

Features:
- joyous
- Suspense
- Bad Ending
- Friendship
- Rhyming Story
- setting: market
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
class Market:
    id: str
    place: str
    lanes: list[str]
    stall: str
    scent: str
    bustle: str
    rhyme: str
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
class Trouble:
    id: str
    label: str
    bait: str
    risk: str
    delay: int
    speed: int
    suspicion: int
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
class Helper:
    id: str
    label: str
    kindness: str
    tool: str
    success: str
    fail: str
    speed: int
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
        clone.facts = copy.deepcopy(self.facts)
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


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    for eid, e in world.entities.items():
        if e.meters["waiting"] < THRESHOLD:
            continue
        sig = ("suspense", eid)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in list(world.entities.values()):
            if kid.role == "friend":
                kid.memes["worry"] += 1
        out.append("__suspense__")
    return out


def _r_lost(world: World) -> list[str]:
    out: list[str] = []
    courier = world.entities.get("courier")
    bag = world.entities.get("bag")
    if not courier or not bag:
        return out
    if courier.meters["rushed"] < THRESHOLD or bag.meters["missing"] < THRESHOLD:
        return out
    sig = ("lost",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in list(world.entities.values()):
        if kid.role == "friend":
            kid.memes["panic"] += 1
    out.append("__lost__")
    return out


def _r_bad_end(world: World) -> list[str]:
    bag = world.entities.get("bag")
    if not bag or bag.meters["missing"] < THRESHOLD:
        return []
    sig = ("bad_end",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("market").meters["sadness"] += 1
    return ["__bad__"]


CAUSAL_RULES = [
    Rule("suspense", "social", _r_suspense),
    Rule("lost", "physical", _r_lost),
    Rule("bad_end", "ending", _r_bad_end),
]


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


def rush_to_help(world: World, helper: Entity, trouble: Trouble, friend: Entity) -> None:
    helper.meters["rushed"] += 1
    friend.memes["hope"] += 1
    world.say(f"A joyous market breeze went by, and {friend.id} held {helper.id} in sight.")
    world.say(f'"Wait," {friend.id} said, "the lane looks tight, and shadows lean."')


def setup(world: World, market: Market, a: Entity, b: Entity) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"In the market bright, with apples to sell, {a.id} and {b.id} went walking "
        f"well. {market.bustle} {market.scent}, and the stalls rang chime; the day felt "
        f"joyous, like a song in rhyme."
    )
    world.say(
        f"They laughed as friends and skipped along, two small hearts beating brave and strong."
    )


def need(world: World, helper: Entity, trouble: Trouble) -> None:
    helper.meters["waiting"] += 1
    world.say(
        f"But at the far stall a small plan swayed: {trouble.bait} had not yet been laid."
    )
    world.say(
        f"{helper.id} peered ahead. \"We need {trouble.label},\" {helper.pronoun()} said, "
        f"\"but the path looks dim and the line's not fed.\""
    )


def tempt(world: World, a: Entity, trouble: Trouble) -> None:
    a.memes["bold"] += 1
    world.say(
        f"\"I'll dart through now,\" {a.id} declared, \"and grab it fast before I'm scared.\""
    )
    world.say(
        f"But {trouble.risk} waited there, and the stall was high; the little lane gave a warning sigh."
    )


def warn(world: World, b: Entity, a: Entity, trouble: Trouble) -> None:
    b.memes["care"] += 1
    world.say(
        f"{b.id} gripped {a.id}'s sleeve and frowned so tight. \"That rush could slip; let's do this right.\""
    )
    world.say(
        f"\"If we dash too near, the basket may sway, and {trouble.label} could vanish away.\""
    )


def take_risk(world: World, a: Entity, trouble: Trouble) -> None:
    a.meters["rushed"] += 1
    a.memes["defiance"] += 1
    world.say(
        f"Yet {a.id} ran on with hurried feet, chasing the prize through the crowded street."
    )
    world.say(
        f"The stall cloth fluttered, the baskets spun, and the market grew quiet under the sun."
    )


def lose_item(world: World, trouble: Trouble) -> None:
    bag = world.get("bag")
    bag.meters["missing"] += 1
    world.say(
        f"Then up went the bag, then down it flew; the string snapped loose as the ring-bell grew."
    )
    world.say(
        f"{trouble.label.capitalize()} slipped from hand and tumbled from sight, lost in the folds of the market night."
    )


def bad_ending(world: World, a: Entity, b: Entity) -> None:
    a.memes["sadness"] += 1
    b.memes["sadness"] += 1
    world.say(
        f"They searched in vain, side by side, but the crowd rolled in like a rising tide."
    )
    world.say(
        f"At last they went home with empty hands, still friends, but the market kept its plans."
    )
    world.say(
        f"Under the moon their voices stayed low; the joyous day had turned to woe."
    )


def tell(market: Market, trouble: Trouble, helper: Helper,
         a_name: str = "Mia", a_gender: str = "girl",
         b_name: str = "Noah", b_gender: str = "boy",
         seed_hint: int = 0) -> World:
    world = World()
    a = world.add(Entity(id=a_name, kind="character", type=a_gender, role="friend"))
    b = world.add(Entity(id=b_name, kind="character", type=b_gender, role="friend"))
    market_ent = world.add(Entity(id="market", type="place", label="the market"))
    bag = world.add(Entity(id="bag", type="thing", label=trouble.label))
    courier = world.add(Entity(id="courier", kind="character", type="adult", label=helper.label))
    world.facts["market"] = market
    world.facts["trouble"] = trouble
    world.facts["helper"] = helper
    world.facts["seed_hint"] = seed_hint

    setup(world, market, a, b)
    world.para()
    need(world, b, trouble)
    tempt(world, a, trouble)
    warn(world, b, a, trouble)
    take_risk(world, a, trouble)
    world.para()
    lose_item(world, trouble)
    propagate(world, narrate=False)
    bad_ending(world, a, b)

    world.facts.update(friend_a=a, friend_b=b, market_ent=market_ent, bag=bag, courier=courier)
    world.facts["outcome"] = "bad"
    return world


MARKETS = {
    "market": Market(
        id="market",
        place="the market",
        lanes=["fruit lane", "cloth lane", "bread lane"],
        stall="the sweet stall",
        scent="sweet pears and warm bread",
        bustle="Voices hummed low and lively, and bells went ding-a-ling",
        rhyme="bright"
    )
}

TROUBLES = {
    "lost_token": Trouble(
        id="lost_token",
        label="a silver token",
        bait="the silver token",
        risk="the lane was packed and the cloth hung low",
        delay=1,
        speed=1,
        suspicion=2,
        tags={"market", "token", "suspense"},
    ),
    "missing_kite": Trouble(
        id="missing_kite",
        label="a red kite",
        bait="the red kite",
        risk="the rope line curled near a cart wheel",
        delay=2,
        speed=1,
        suspicion=3,
        tags={"market", "kite", "suspense"},
    ),
}

HELPERS = {
    "stallkeeper": Helper(
        id="stallkeeper",
        label="the stallkeeper",
        kindness="kindly",
        tool="a bright lantern",
        success="found the missing thing tucked behind the apples",
        fail="could not catch it before it vanished",
        speed=2,
        tags={"help", "market"},
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Ava", "Nora", "Zoe"]
BOY_NAMES = ["Noah", "Leo", "Eli", "Owen", "Finn"]


@dataclass
class StoryParams:
    market: str
    trouble: str
    helper: str
    friend_a: str
    friend_a_gender: str
    friend_b: str
    friend_b_gender: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [("market", t, h) for t in TROUBLES for h in HELPERS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming market story with suspense and a bad ending.")
    ap.add_argument("--market", choices=MARKETS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--helper", choices=HELPERS)
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
              if (args.market is None or c[0] == args.market)
              and (args.trouble is None or c[1] == args.trouble)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    _, trouble, helper = rng.choice(combos)
    a_gender = rng.choice(["girl", "boy"])
    b_gender = "boy" if a_gender == "girl" else "girl"
    a_name = rng.choice(GIRL_NAMES if a_gender == "girl" else BOY_NAMES)
    b_name = rng.choice([n for n in (BOY_NAMES if b_gender == "boy" else GIRL_NAMES) if n != a_name])
    return StoryParams(
        market="market",
        trouble=trouble,
        helper=helper,
        friend_a=a_name,
        friend_a_gender=a_gender,
        friend_b=b_name,
        friend_b_gender=b_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.market not in MARKETS:
        raise StoryError(f"Unknown market: {params.market}")
    if params.trouble not in TROUBLES:
        raise StoryError(f"Unknown trouble: {params.trouble}")
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {params.helper}")
    world = tell(MARKETS[params.market], TROUBLES[params.trouble], HELPERS[params.helper],
                 params.friend_a, params.friend_a_gender, params.friend_b, params.friend_b_gender,
                 params.seed or 0)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming market story that includes the word "joyous" and ends badly, with friendship still shining through.',
        f"Tell a suspenseful TinyStories-style tale set in {f['market'].place} where two friends warn each other, but one takes a risky shortcut and loses the prize.",
        f'Write a short rhyming story about market stalls, a tense mistake, and a sad ending that still shows friendship.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["friend_a"]
    b = f["friend_b"]
    trouble = f["trouble"]
    return [
        ("Who are the friends in the story?",
         f"The story is about {a} and {b}, two friends walking through the market together. They care about each other, even when the day turns tense."),
        ("Why did the story feel suspenseful?",
         f"It felt suspenseful because they wanted {trouble.label}, but the path was crowded and risky. The warning made the moment feel tight, like a breath held in the air."),
        ("How did the story end?",
         f"It ended badly because the prize was lost and they went home empty-handed. Still, the two friends stayed together, which showed their friendship was real."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a market?",
         "A market is a place where people buy and sell food, cloth, and little goods. It is usually busy and full of voices."),
        ("Why can a crowded lane feel suspenseful?",
         "A crowded lane can feel suspenseful because it is hard to move fast or see what might happen next. That makes a small mistake feel bigger."),
        ("What does friendship mean?",
         "Friendship means caring about someone, listening to them, and staying kind even when things go wrong. Friends try to help each other."),
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
    out = ["--- world model state ---"]
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
        out.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(out)


ASP_RULES = r"""
friend(A) :- character(A).
suspense :- waiting(X), waiting(X) >= 1.
lost :- rushed(courier), missing(bag).
bad_end :- lost.
outcome(bad) :- bad_end.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("market", "market"))
    for t in TROUBLES:
        lines.append(asp.fact("trouble", t))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_outcomes() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show outcome/1."))
    return sorted(x[0] for x in asp.atoms(model, "outcome"))


def asp_verify() -> int:
    rc = 0
    try:
        sample = generate(resolve_params(argparse.Namespace(market=None, trouble=None, helper=None),
                                         random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    py = set(valid_combos())
    if py == {("market", t, h) for t in TROUBLES for h in HELPERS}:
        print(f"OK: Python combo gate has {len(py)} combos.")
    else:
        rc = 1
        print("MISMATCH in Python combos.")
    try:
        import asp
        asp_out = set(asp_outcomes())
        if asp_out == {"bad"}:
            print("OK: ASP twin solved with bad ending outcome.")
        else:
            rc = 1
            print(f"MISMATCH in ASP outcomes: {sorted(asp_out)}")
    except Exception as exc:
        rc = 1
        print(f"ASP CHECK FAILED: {exc}")
    return rc


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
        print(asp_program("", "#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("market story outcomes:", ", ".join(asp_outcomes() or ["bad"]))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(market="market", trouble="lost_token", helper="stallkeeper",
                        friend_a="Mia", friend_a_gender="girl", friend_b="Noah", friend_b_gender="boy"),
            StoryParams(market="market", trouble="missing_kite", helper="stallkeeper",
                        friend_a="Luna", friend_a_gender="girl", friend_b="Eli", friend_b_gender="boy"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
