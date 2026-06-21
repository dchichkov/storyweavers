#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/baloney_secure_cat_happy_ending_flashback_curiosity.py
======================================================================================

A tiny fable-like storyworld about a curious cat, a bit of baloney, and a secure
safe place.  The world supports a flashback beat, a curiosity-driven problem,
and a happy ending where the cat ends up secure and content.

Seed words: baloney, secure, cat
Features: Happy Ending, Flashback, Curiosity
Style: Fable
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
    tags: set[str] = field(default_factory=set)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
    scene: str
    hiding_spot: str
    safe_spot: str
    lesson: str
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
class Snack:
    id: str
    label: str
    smell: str
    crumbly: bool = True
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
class SecureThing:
    id: str
    label: str
    phrase: str
    kind_word: str
    comfort: str
    safe: bool = True
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Curiosity:
    id: str
    thought: str
    question: str
    follow_up: str
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
        return c


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


def _r_interest(world: World) -> list[str]:
    out: list[str] = []
    cat = world.entities.get("cat")
    snack = world.entities.get("snack")
    if not cat or not snack:
        return out
    if cat.memes["curiosity"] < THRESHOLD or snack.meters["hidden"] < THRESHOLD:
        return out
    sig = ("interest",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cat.memes["wanting"] += 1
    out.append("__interest__")
    return out


def _r_find_secure(world: World) -> list[str]:
    out: list[str] = []
    cat = world.entities.get("cat")
    bed = world.entities.get("secure_place")
    if not cat or not bed:
        return out
    if cat.memes["relief"] < THRESHOLD or bed.meters["ready"] < THRESHOLD:
        return out
    sig = ("secure",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cat.meters["secure"] += 1
    out.append("__secure__")
    return out


CAUSAL_RULES = [
    Rule("interest", "social", _r_interest),
    Rule("secure", "physical", _r_find_secure),
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


def tell(world: World, place: Place, snack: Snack, secure_thing: SecureThing, curiosity: Curiosity,
         cat_name: str = "Milo", cat_type: str = "cat", keeper_name: str = "Nora",
         keeper_type: str = "girl", seed_memory: str = "the warm barn") -> World:
    cat = world.add(Entity(id="cat", kind="character", type=cat_type, label=cat_name, role="hero"))
    keeper = world.add(Entity(id="keeper", kind="character", type=keeper_type, label=keeper_name, role="helper"))
    snack_ent = world.add(Entity(id="snack", type="thing", label=snack.label))
    secure_ent = world.add(Entity(id="secure_place", type="thing", label=secure_thing.label))

    cat.memes["curiosity"] = 1.0
    cat.memes["trust"] = 1.0
    keeper.memes["care"] = 1.0
    snack_ent.meters["hidden"] = 1.0
    secure_ent.meters["ready"] = 0.0

    world.say(
        f"Once, in {place.scene}, {cat_name} was a little cat with bright eyes and a soft tail. "
        f"{cat_name} liked to ask why the wind shook the grass and why the hens clucked so loudly."
    )
    world.say(
        f"Near a stone wall, the smell of {snack.label} drifted by. "
        f"It was only a bit of baloney, but it smelled rich and secret, and that made {cat_name} curious."
    )
    world.para()
    world.say(
        f"Then came a flashback. Long before this day, {keeper_name} had said, "
        f'\"A curious cat should not wander into every dark hole. Some places are not secure.\"'
    )
    world.say(
        f"{cat_name} remembered that wise warning as the smell grew stronger. "
        f'\"What is under the basket?\" {cat_name} wondered. \"Could it be baloney?\"'
    )
    cat.memes["curiosity"] += 1
    keeper.memes["concern"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{keeper_name} noticed the shining eyes and smiled. "
        f'\"Let us look together,\" {keeper_name} said, \"so the answer can be safe.\"'
    )

    world.para()
    snack_ent.meters["found"] = 1.0
    secure_ent.meters["ready"] = 1.0
    cat.memes["relief"] += 1
    world.say(
        f"They lifted the basket together and found the baloney wrapped up neatly, not lost at all. "
        f"It had simply slipped behind some jars."
    )
    world.say(
        f"{keeper_name} moved the little plate to {place.safe_spot}, a secure place where the cat could smell it without trouble."
    )
    propagate(world, narrate=False)
    if cat.meters["secure"] < THRESHOLD:
        cat.meters["secure"] = 1.0
    world.say(
        f"{cat_name} sat beside the safe spot, purring. The cat still was curious, but now curiosity had a gentle path."
    )
    world.say(
        f"And so the fable ended well: the baloney stayed for later, the cat stayed secure, "
        f"and everyone learned that a wise question is best asked in a safe way."
    )

    world.facts.update(
        cat=cat,
        keeper=keeper,
        snack=snack_ent,
        secure_thing=secure_ent,
        curiosity=curiosity,
        place=place,
        ending="happy",
        seed_memory=seed_memory,
    )
    return world


PLACES = {
    "farmyard": Place(
        id="farmyard",
        scene="a sunny farmyard with apple trees and a red barn",
        hiding_spot="under a basket near the wall",
        safe_spot="the clean kitchen shelf",
        lesson="curiosity is wise when it walks with care",
    ),
    "garden": Place(
        id="garden",
        scene="a small garden with bean vines and a wooden gate",
        hiding_spot="behind a watering can",
        safe_spot="the porch table",
        lesson="questions should be answered in a calm place",
    ),
}

SNACKS = {
    "baloney": Snack(
        id="baloney",
        label="baloney",
        smell="strong and savory",
        crumbly=False,
    ),
}

SECURE_THINGS = {
    "basket": SecureThing(
        id="basket",
        label="a basket lid",
        phrase="a basket lid",
        kind_word="basket",
        comfort="closed tight",
    ),
    "tin_box": SecureThing(
        id="tin_box",
        label="a tin box",
        phrase="a tin box",
        kind_word="box",
        comfort="snapped shut",
    ),
}

CURIOSITIES = {
    "smell": Curiosity(
        id="smell",
        thought="a smell drifting on the air",
        question="What is making that smell?",
        follow_up="It would be nice to know, but only if the answer can be found safely.",
    ),
    "peek": Curiosity(
        id="peek",
        thought="a secret little peek",
        question="What is hiding under there?",
        follow_up="A brave look is best when a grown-up is near.",
    ),
}

GIRL_NAMES = ["Nora", "Mina", "Lia", "Ivy", "Tessa"]
CAT_NAMES = ["Milo", "Pip", "Toby", "Patches", "Sunny"]


@dataclass
class StoryParams:
    place: str
    snack: str
    secure_thing: str
    curiosity: str
    cat_name: str
    keeper_name: str
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


CURATED = [
    StoryParams(place="farmyard", snack="baloney", secure_thing="basket", curiosity="smell",
                cat_name="Milo", keeper_name="Nora"),
    StoryParams(place="garden", snack="baloney", secure_thing="tin_box", curiosity="peek",
                cat_name="Pip", keeper_name="Lia"),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place in PLACES:
        for snack in SNACKS:
            for secure_thing in SECURE_THINGS:
                for curiosity in CURIOSITIES:
                    out.append((place, snack, secure_thing, curiosity))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like cat storyworld with curiosity and a secure ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--secure-thing", dest="secure_thing", choices=SECURE_THINGS)
    ap.add_argument("--curiosity", choices=CURIOSITIES)
    ap.add_argument("--cat-name")
    ap.add_argument("--keeper-name")
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
              and (args.snack is None or c[1] == args.snack)
              and (args.secure_thing is None or c[2] == args.secure_thing)
              and (args.curiosity is None or c[3] == args.curiosity)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, snack, secure_thing, curiosity = rng.choice(combos)
    cat_name = args.cat_name or rng.choice(CAT_NAMES)
    keeper_name = args.keeper_name or rng.choice(GIRL_NAMES)
    return StoryParams(place=place, snack=snack, secure_thing=secure_thing,
                       curiosity=curiosity, cat_name=cat_name, keeper_name=keeper_name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for a child that includes the words "baloney", "secure", and "cat".',
        f"Tell a gentle story about a curious cat who smells baloney and learns to stay secure.",
        f"Write a happy-ending story with a flashback: a cat remembers a warning and asks a wise question.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cat = f["cat"]
    keeper = f["keeper"]
    place = f["place"]
    return [
        QAItem(
            question="Why was the cat curious?",
            answer=f"The cat was curious because the smell of baloney drifted by in the {place.scene}. The smell made the cat wonder what was hidden there."
        ),
        QAItem(
            question="What was the flashback about?",
            answer=f"The flashback remembered {keeper.label_word} warning the cat to stay out of dark, unsafe places. That memory helped the cat choose a safer way to look."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily. The baloney was found in a safe place, and the cat stayed secure while everyone learned a wise lesson."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does secure mean?",
            answer="Secure means safe, steady, and not likely to be lost or hurt."
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly remembers something that happened earlier. It helps explain why a character thinks or acts a certain way now."
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to know more. It can lead to good questions when you stay careful."
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
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
curious(cat) :- curiosity(cat, _).
happy_ending :- secure(cat), found(snack), safe_place(secure_place).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for sid in SNACKS:
        lines.append(asp.fact("snack", sid))
    for sid in SECURE_THINGS:
        lines.append(asp.fact("secure_thing", sid))
    for cid in CURIOSITIES:
        lines.append(asp.fact("curiosity", cid, "thought"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    # smoke test ordinary generation
    sample = generate(CURATED[0])
    _ = sample.story
    model = asp.one_model(asp_program("", "#show curious/1.\n#show happy_ending/0."))
    _ = model
    return 0


def _pick_name(pool: list[str], rng: random.Random) -> str:
    return rng.choice(pool)


def generate(params: StoryParams) -> StorySample:
    for field_name, table in (("place", PLACES), ("snack", SNACKS), ("secure_thing", SECURE_THINGS), ("curiosity", CURIOSITIES)):
        if getattr(params, field_name) not in table:
            raise StoryError(f"Unknown {field_name}: {getattr(params, field_name)}")
    world = World()
    place = PLACES[params.place]
    snack = SNACKS[params.snack]
    secure_thing = SECURE_THINGS[params.secure_thing]
    curiosity = CURIOSITIES[params.curiosity]
    return StorySample(
        params=params,
        story=tell(world, place, snack, secure_thing, curiosity, params.cat_name, "cat", params.keeper_name, "girl").render(),
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show curious/1.\n#show happy_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("No alternate ASP listing for this tiny world.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        if i:
            print("\n" + "=" * 70 + "\n")
        emit(sample, trace=args.trace, qa=args.qa)


if __name__ == "__main__":
    main()
