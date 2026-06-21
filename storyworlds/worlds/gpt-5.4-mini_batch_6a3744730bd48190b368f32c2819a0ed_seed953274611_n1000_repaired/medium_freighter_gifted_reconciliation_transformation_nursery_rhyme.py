#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/medium_freighter_gifted_reconciliation_transformation_nursery_rhyme.py
=====================================================================================================

A tiny, nursery-rhyme-style storyworld about a medium freighter in a harbor, a
gift that feels a bit too small or too big, and a reconciliation that changes
how everyone sees the day.

The domain is deliberately small and state-driven:
- a child gives a gift to a dock worker after a quarrel,
- the gift transforms the medium freighter in a gentle, magical-but-concrete way,
- the quarrel mends, and the ending proves what changed.

Seed words: medium, freighter, gifted
Features: Reconciliation, Transformation
Style: Nursery Rhyme
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
MEME_GOAL = 2.0


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
    plural: bool = False

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
    harbor: str
    child: str
    child_gender: str
    keeper: str
    keeper_gender: str
    ship: str
    gift: str
    gift_kind: str
    mood: str
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
class Harbor:
    id: str
    name: str
    sound: str
    features: list[str]
    breeze: str
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
class Freighter:
    id: str
    label: str
    size: str
    cargo: str
    hull_color: str
    lantern_word: str
    lane: str
    can_transform: bool = True
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
class Gift:
    id: str
    label: str
    kind: str
    shine: str
    transformation: str
    fits: str
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
    harbor: Harbor
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
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
        clone = World(self.harbor)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone
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


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    keeper = world.get("keeper")
    if child.memes["apology"] >= THRESHOLD and keeper.memes["softening"] >= THRESHOLD:
        sig = ("reconcile",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.memes["peace"] += 1
        keeper.memes["peace"] += 1
        keeper.memes["grudge"] = 0.0
        out.append("__reconcile__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    ship = world.get("ship")
    gift = world.get("gift")
    if gift.meters["given"] >= THRESHOLD and ship.memes["hope"] >= THRESHOLD:
        sig = ("transform",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        ship.meters["changed"] += 1
        ship.meters["glow"] += 1
        ship.memes["pride"] += 1
        out.append("__transform__")
    return out


CAUSAL_RULES = [
    Rule("reconcile", _r_reconcile),
    Rule("transform", _r_transform),
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


def rhyme(lines: list[str]) -> str:
    return " ".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for harbor_id, h in HARBORS.items():
        for ship_id, ship in FREIGHTERS.items():
            for gift_id, gift in GIFTS.items():
                if ship.can_transform and "gift" in gift.tags:
                    combos.append((harbor_id, ship_id, gift_id))
    return combos


def explain_rejection(ship: Freighter, gift: Gift) -> str:
    return (
        f"(No story: the gift '{gift.id}' does not belong in this little rhyme, "
        f"or the ship cannot be transformed by it. Choose a gift with a real gentle change.)"
    )


def _setup_names(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def build_world(harbor: Harbor, child_name: str, child_gender: str, keeper_name: str, keeper_gender: str,
                ship: Freighter, gift: Gift, mood: str) -> World:
    world = World(harbor)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", label=child_name))
    keeper = world.add(Entity(id=keeper_name, kind="character", type=keeper_gender, role="keeper", label=keeper_name))
    vessel = world.add(Entity(id="ship", kind="thing", type="ship", label=ship.label, meters=defaultdict(float), memes=defaultdict(float)))
    present = world.add(Entity(id="gift", kind="thing", type="gift", label=gift.label, meters=defaultdict(float), memes=defaultdict(float)))
    world.facts.update(child=child, keeper=keeper, ship=vessel, gift=present, harbor=harbor, ship_cfg=ship, gift_cfg=gift, mood=mood)
    return world


def opening(world: World) -> None:
    h = world.harbor
    ship = world.facts["ship_cfg"]
    child = world.facts["child"]
    keeper = world.facts["keeper"]
    child.memes["curiosity"] += 1
    keeper.memes["duty"] += 1
    world.say(
        rhyme([
            f"By the harbor soft and gray, {child.id} came out to play,",
            f"where {h.name} sang low and sweet in the whisper of the bay.",
            f"There rocked a medium freighter, {ship.label}, with a patient painted side,",
            f"and {keeper.id} watched the mooring rope while gulls went swoop and glide.",
        ])
    )
    world.say(
        f"{child.id} had a gifted little gift, {world.facts['gift_cfg'].label}, "
        f"small as a shell but bright as a star."
    )


def quarrel(world: World) -> None:
    child = world.facts["child"]
    keeper = world.facts["keeper"]
    gift = world.facts["gift_cfg"]
    child.memes["hurt"] += 1
    keeper.memes["grudge"] += 1
    world.say(
        f"But {keeper.id} said the day was busy, and the gift must wait a while; "
        f"{child.id} frowned and folded arms, and lost the sunny smile."
    )
    world.say(
        f'"If I cannot give it now," said {child.id}, "then I shall not stay." '
        f"But the little gift still glimmered, as if it had a kinder way."
    )
    world.facts["gift_label"] = gift.label


def ask_pardon(world: World) -> None:
    child = world.facts["child"]
    keeper = world.facts["keeper"]
    child.memes["apology"] += 1
    keeper.memes["softening"] += 1
    world.say(
        f"Then {child.id} went close and spoke it true: "
        f'"I meant to share my gift with you."'
    )
    world.say(
        f"{keeper.id} blinked and sighed, then knelt right down; the grudge grew small, then smaller still."
    )
    propagate(world, narrate=False)


def give_gift(world: World) -> None:
    child = world.facts["child"]
    keeper = world.facts["keeper"]
    gift = world.facts["gift_cfg"]
    ship = world.facts["ship_cfg"]
    present = world.get("gift")
    present.meters["given"] += 1
    ship.memes["hope"] += 1
    child.memes["joy"] += 1
    keeper.memes["joy"] += 1
    world.say(
        f"{child.id} placed the {gift.label} into {keeper.id}'s hand; it shone "
        f"{gift.shine}, and the old quarrel shook and sank."
    )
    propagate(world, narrate=False)


def transform_ship(world: World) -> None:
    ship = world.facts["ship_cfg"]
    gift = world.facts["gift_cfg"]
    vessel = world.get("ship")
    vessel.meters["changed"] += 1
    vessel.meters["glow"] += 1
    vessel.memes["hope"] += 1
    world.say(
        f"At once the {ship.label} took {gift.transformation}, "
        f"and changed from dull to dazzle in the harbor light."
    )
    world.say(
        f"Her rope ran straight, her lantern word was warm, and every porthole seemed to smile."
    )


def ending(world: World) -> None:
    child = world.facts["child"]
    keeper = world.facts["keeper"]
    ship = world.facts["ship_cfg"]
    world.say(
        f"Now {child.id} and {keeper.id} stood side by side, the peace between them new and bright."
    )
    world.say(
        f"The medium freighter, {ship.label}, shone with a little change, and the harbor hummed that night."
    )


def tell(params: StoryParams) -> World:
    harbor = HARBORS[params.harbor]
    ship = FREIGHTERS[params.ship]
    gift = GIFTS[params.gift]
    world = build_world(harbor, params.child, params.child_gender, params.keeper, params.keeper_gender, ship, gift, params.mood)
    opening(world)
    world.para()
    quarrel(world)
    ask_pardon(world)
    give_gift(world)
    transform_ship(world)
    world.para()
    ending(world)
    world.facts["outcome"] = "reconciled" if world.get("keeper").memes["peace"] >= THRESHOLD else "unresolved"
    world.facts["transformed"] = world.get("ship").meters["changed"] >= THRESHOLD
    return world


HARBORS = {
    "medium": Harbor(
        id="medium",
        name="a medium harbor",
        sound="soft bells",
        features=["boats", "ropes", "gulls"],
        breeze="gentle",
    ),
    "moon": Harbor(
        id="moon",
        name="the moonlit harbor",
        sound="silver bells",
        features=["lanterns", "water", "gulls"],
        breeze="cool",
    ),
}

FREIGHTERS = {
    "freighter": Freighter(
        id="freighter",
        label="medium freighter",
        size="medium",
        cargo="tea crates",
        hull_color="blue",
        lantern_word="lantern",
        lane="quiet lane",
        can_transform=True,
    ),
    "barge": Freighter(
        id="barge",
        label="old barge",
        size="large",
        cargo="apple sacks",
        hull_color="green",
        lantern_word="lamp",
        lane="slow lane",
        can_transform=True,
    ),
}

GIFTS = {
    "gifted_song": Gift(
        id="gifted",
        label="gifted song",
        kind="song",
        shine="like a silver ribbon",
        transformation="a bright new hum",
        fits="heart",
        tags={"gift"},
    ),
    "gifted_flag": Gift(
        id="gifted_flag",
        label="gifted flag",
        kind="flag",
        shine="like a little sunrise",
        transformation="a fresh flag of cheer",
        fits="mast",
        tags={"gift"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Tom", "Finn", "Leo", "Sam", "Noah"]

TRAITS = ["gentle", "brave", "curious", "careful"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme story about a medium freighter and a gifted present, using the word "medium".',
        f"Tell a soft harbor story where {f['child'].id} and {f['keeper'].id} make up after a quarrel, and the freighter changes too.",
        f'Write a tiny rhyme where a gift helps a harbor argument turn into friendship and a ship transformation.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    keeper = f["keeper"]
    ship = f["ship_cfg"]
    gift = f["gift_cfg"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, {keeper.id}, and the medium freighter called {ship.label}. The harbor and the gift matter because they drive the change in the story."),
        ("Why did the quarrel end?",
         f"{child.id} spoke kindly and offered the gift instead of holding on to the hurt. That softened {keeper.id}, and the two of them mended their mood together."),
        ("What changed on the freighter?",
         f"The freighter took {gift.transformation} and began to glow with hope. That shows the gift did more than sit in a hand; it changed the ship in the ending image."),
    ]
    if f.get("outcome") == "reconciled":
        qa.append(
            ("How did the story end?",
             f"It ended with {child.id} and {keeper.id} standing side by side in peace. The medium freighter still floated there, but now it shone like it had been blessed by the gift.")
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a freighter?",
         "A freighter is a ship that carries cargo from one place to another. It is built to travel on water and hold useful things."),
        ("What does reconciliation mean?",
         "Reconciliation means making up after a quarrel. The hurt feelings soften, and people can stand together again."),
        ("What does transformation mean?",
         "Transformation means something changes into a new form or becomes very different. In stories, it can be a small magic change or a big real one."),
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
    return "\n".join(lines)


ASP_RULES = r"""
reconciled :- child_apology, keeper_softens.
transformed :- gift_given, ship_hope.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("world", "harbor"),
    ]
    for hid in HARBORS:
        lines.append(asp.fact("harbor", hid))
    for sid in FREIGHTERS:
        lines.append(asp.fact("freighter", sid))
    for gid in GIFTS:
        lines.append(asp.fact("gift", gid))
        lines.append(asp.fact("gift_tag", gid, "gift"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show reconciled/0.\n#show transformed/0."))
    atoms = {sym.name for sym in model}
    if "reconciled" not in atoms and "transformed" not in atoms:
        print("OK: ASP twin loads.")
    sample = generate(resolve_params(argparse.Namespace(harbor=None, child=None, child_gender=None, keeper=None, keeper_gender=None, ship=None, gift=None, mood=None), random.Random(7)))
    try:
        _ = sample.story
    except Exception as exc:
        print(f"Story generation failed: {exc}")
        return 1
    print("OK: story generation smoke test passed.")
    print("OK: verify completed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about a medium freighter, a gifted present, reconciliation, and transformation.")
    ap.add_argument("--harbor", choices=HARBORS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", dest="child_gender", choices=["girl", "boy"])
    ap.add_argument("--keeper")
    ap.add_argument("--keeper-gender", dest="keeper_gender", choices=["mother", "father", "girl", "boy", "woman", "man"])
    ap.add_argument("--ship", choices=FREIGHTERS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--mood", choices=["sad", "soft", "bright"])
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


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid story combinations exist.")
    filtered = [
        c for c in combos
        if (args.harbor is None or c[0] == args.harbor)
        and (args.ship is None or c[1] == args.ship)
        and (args.gift is None or c[2] == args.gift)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    harbor, ship, gift = rng.choice(sorted(filtered))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    keeper_gender = args.keeper_gender or rng.choice(["mother", "father"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    keeper = args.keeper or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != child])
    mood = args.mood or rng.choice(["sad", "soft", "bright"])
    return StoryParams(
        harbor=harbor,
        child=child,
        child_gender=child_gender,
        keeper=keeper,
        keeper_gender=keeper_gender,
        ship=ship,
        gift=gift,
        gift_kind=GIFTS[gift].kind,
        mood=mood,
    )


def generate(params: StoryParams) -> StorySample:
    if params.harbor not in HARBORS:
        raise StoryError(f"Unknown harbor: {params.harbor}")
    if params.ship not in FREIGHTERS:
        raise StoryError(f"Unknown ship: {params.ship}")
    if params.gift not in GIFTS:
        raise StoryError(f"Unknown gift: {params.gift}")
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


CURATED = [
    StoryParams(harbor="medium", child="Mia", child_gender="girl", keeper="Tom", keeper_gender="boy", ship="freighter", gift="gifted_song", gift_kind="song", mood="soft"),
    StoryParams(harbor="moon", child="Leo", child_gender="boy", keeper="Nora", keeper_gender="girl", ship="barge", gift="gifted_flag", gift_kind="flag", mood="bright"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reconciled/0.\n#show transformed/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("This tiny world keeps its ASP twin simple.")
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
            header = f"### {p.child} and {p.keeper}: {p.ship} with {p.gift}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
