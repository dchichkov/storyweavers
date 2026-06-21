#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/success_affluent_cautionary_repetition_foreshadowing_nursery_rhyme.py
=====================================================================================================

A small standalone storyworld built from the seed words "success" and "affluent",
with cautionary repetition and foreshadowing, styled like a nursery rhyme.

The world model:
- An affluent little household with two children, a caretaker, a gate, a pond,
  a bridge, and a lantern.
- A cautionary temptation to cross a wobbly bridge to fetch a shiny prize.
- A foreshadowed warning that the bridge is loose.
- A repeated refrain that helps the story feel like a nursery rhyme.
- A successful ending image proving what changed: the children choose the safe
  way and still get the prize.

The story is state-driven, not a frozen paragraph with swapped nouns.
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mum", "father": "dad"}.get(self.type, self.type)
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
class Place:
    id: str
    name: str
    affluent: bool = False
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
class Temptation:
    id: str
    object_word: str
    phrase: str
    shine: str
    risky: str
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
class Prize:
    id: str
    label: str
    phrase: str
    safe_way: str
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
class Aid:
    id: str
    label: str
    phrase: str
    glow: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
class StoryParams:
    place: str
    temptation: str
    prize: str
    aid: str
    child1: str
    child1_type: str
    child2: str
    child2_type: str
    caretaker: str
    caretaker_type: str
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


PLACES = {
    "manor_garden": Place(id="manor_garden", name="an affluent manor garden", affluent=True, tags={"affluent"}),
    "rose_courtyard": Place(id="rose_courtyard", name="a bright rose courtyard", affluent=True, tags={"affluent"}),
    "orchard_lane": Place(id="orchard_lane", name="an affluent orchard lane", affluent=True, tags={"affluent"}),
}

TEMPTATIONS = {
    "stone_bridge": Temptation(
        id="stone_bridge",
        object_word="bridge",
        phrase="the little stone bridge by the pond",
        shine="It looked fine from far away, but one stone was loose and one rail was wobbly.",
        risky="The loose stone could make a child slip.",
        tags={"bridge", "cautionary", "foreshadowing"},
    ),
    "pond_path": Temptation(
        id="pond_path",
        object_word="path",
        phrase="the narrow path by the pond",
        shine="It looked like the quickest way, but the moss was slick as soap.",
        risky="The slick moss could make shoes slide.",
        tags={"path", "cautionary", "foreshadowing"},
    ),
}

PRIZES = {
    "pear": Prize(
        id="pear",
        label="pear",
        phrase="a ripe pear on the far side",
        safe_way="use the long ribbon pole",
        tags={"success"},
    ),
    "star_cookie": Prize(
        id="star_cookie",
        label="star cookie",
        phrase="a star cookie in the blue dish",
        safe_way="ask the caretaker to bring it",
        tags={"success"},
    ),
}

AIDS = {
    "lantern": Aid(
        id="lantern",
        label="lantern",
        phrase="a little lantern",
        glow="It glowed warm and kind, and it let everyone see the safe steps.",
        tags={"light", "foreshadowing"},
    ),
    "ribbon_pole": Aid(
        id="ribbon_pole",
        label="ribbon pole",
        phrase="a long ribbon pole",
        glow="It could reach far without stepping on the wobbly part.",
        tags={"tool", "success"},
    ),
}

GIRL_NAMES = ["Lily", "Mina", "Rose", "Elsie", "Nora", "Pippa"]
BOY_NAMES = ["Tom", "Milo", "Finn", "Owen", "Jasper", "Theo"]
CARETAKER_NAMES = ["Mum", "Dad", "Nana", "Uncle Ben"]


def _pick_name(rng: random.Random, gender: str) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice(pool)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for t in TEMPTATIONS:
            for pr in PRIZES:
                combos.append((p, t, pr))
    return combos


def tell(place: Place, temptation: Temptation, prize: Prize, aid: Aid,
         child1: Entity, child2: Entity, caretaker: Entity) -> World:
    world = World()
    world.add(child1)
    world.add(child2)
    world.add(caretaker)
    world.add(Entity(id=place.id, kind="place", type="place", label=place.name,
                     attrs={"affluent": place.affluent}))
    world.add(Entity(id=temptation.id, kind="thing", type="thing", label=temptation.phrase,
                     attrs={"risky": temptation.risky}))
    world.add(Entity(id=prize.id, kind="thing", type="thing", label=prize.label,
                     attrs={"safe_way": prize.safe_way}))
    world.add(Entity(id=aid.id, kind="thing", type="thing", label=aid.label,
                     attrs={"glow": aid.glow}))

    child1.memes["curiosity"] += 1
    child2.memes["care"] += 1
    caretaker.memes["watchful"] += 1

    world.say(
        f"Down in {place.name}, where the hedges were neat and the windows were bright, "
        f"{child1.id} and {child2.id} lived a very affluent day."
    )
    world.say(
        f"{child1.id} sang, \"Look there, look there,\" and {child2.id} sang, "
        f"\"Mind and beware,\" for nursery rhymes like to warn and compare."
    )
    world.say(
        f"By the pond stood {temptation.phrase}. {temptation.shine} {temptation.risky}"
    )
    world.say(
        f"{child2.id} held up {aid.phrase}. \"A lantern, a lantern, a safe little light,\" "
        f"{child2.id} said. {aid.glow}"
    )

    world.para()
    child1.memes["want"] += 1
    world.say(
        f"\"I want the {prize.label},\" said {child1.id}. \"I want the {prize.label},\" "
        f"said {child1.id} again. \"A quick little trip and a lovely little win.\""
    )
    world.say(
        f"{child2.id} nodded. \"But the bridge is wobbly, the bridge is wobbly; "
        f"slow feet are best.\""
    )
    world.say(
        f"{caretaker.id} from the gate called, \"If a thing looks shiny, dear hearts, "
        f"it may still ask you to test your luck.\""
    )

    world.para()
    child1.memes["resolve"] += 1
    child2.memes["resolve"] += 1
    caretaker.memes["pride"] += 1

    world.say(
        f"So they did not rush. They did not race. They took the lantern, and by lantern light "
        f"they chose the safe way round."
    )
    world.say(
        f"Once more they said, \"Slow feet are best, slow feet are best,\" and once more "
        f"they listened to the little warning bell in their heads."
    )
    world.say(
        f"{child2.id} used {prize.safe_way}, and soon the {prize.label} came home without a stumble."
    )
    world.say(
        f"{child1.id} clapped, {child2.id} laughed, and {caretaker.id} smiled by the gate."
    )
    world.say(
        f"So the day ended in success: the children kept safe, the prize was theirs, "
        f"and the affluent garden shone like a tidy song."
    )

    child1.memes["joy"] += 2
    child2.memes["joy"] += 2
    caretaker.memes["relief"] += 1

    world.facts.update(
        place=place,
        temptation=temptation,
        prize=prize,
        aid=aid,
        child1=child1,
        child2=child2,
        caretaker=caretaker,
        outcome="success",
        warning=temptation.risky,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme story about "{f["place"].name}" that uses the words "success" and "affluent".',
        f"Tell a cautionary rhyme where {f['child1'].id} wants to cross {f['temptation'].phrase} but {f['child2'].id} warns them and they choose the safe way.",
        f"Write a gentle story with repetition and foreshadowing where the shiny thing by the pond looks tempting, but the children succeed without getting hurt.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    c1 = f["child1"]
    c2 = f["child2"]
    car = f["caretaker"]
    temptation = f["temptation"]
    prize = f["prize"]
    aid = f["aid"]
    return [
        ("Who is the story about?",
         f"It is about {c1.id}, {c2.id}, and {car.id} in {f['place'].name}. The little group lives in an affluent home and stays together for the whole tale."),
        ("What looked tempting?",
         f"{temptation.phrase} looked tempting, but it also carried a warning. The story foreshadowed trouble by saying one stone was loose and the surface was wobbly."),
        ("How did they stay safe?",
         f"They slowed down, listened to the warning, and used {aid.phrase}. That kept them from stepping onto the risky part and let them finish in success."),
        ("What happened at the end?",
         f"The prize came home safely, and the children were happy. The ending shows that choosing the careful path can still bring success."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["temptation"].tags) | set(f["prize"].tags) | set(f["aid"].tags) | {"success", "affluent"}
    qa = []
    if "success" in tags:
        qa.append(("What does success mean?",
                   "Success means reaching a good result. It can mean finishing something well, keeping safe, or getting a goal without trouble."))
    if "affluent" in tags:
        qa.append(("What does affluent mean?",
                   "Affluent means having a lot of money or being well-off. An affluent place often looks neat, bright, and comfortable."))
    if "foreshadowing" in tags:
        qa.append(("What is foreshadowing?",
                   "Foreshadowing is a hint that something important may happen later. It helps a listener notice warning signs before the turn in the story."))
    if "cautionary" in tags:
        qa.append(("What is a cautionary story?",
                   "A cautionary story gives a warning. It shows a choice that should be made carefully so someone can avoid trouble."))
    if "light" in tags:
        qa.append(("What is a lantern for?",
                   "A lantern gives a soft light in the dark. It helps people see where they are stepping without needing to rush."))
    return qa


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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld with caution and success.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--aid", choices=AIDS)
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
    place = args.place or rng.choice(list(PLACES))
    temptation = args.temptation or rng.choice(list(TEMPTATIONS))
    prize = args.prize or rng.choice(list(PRIZES))
    aid = args.aid or rng.choice(list(AIDS))
    child1_type = rng.choice(["girl", "boy"])
    child2_type = "boy" if child1_type == "girl" else "girl"
    child1 = _pick_name(rng, child1_type)
    child2 = _pick_name(rng, child2_type)
    caretaker = rng.choice(CARETAKER_NAMES)
    caretaker_type = "mother" if caretaker == "Mum" else "father" if caretaker == "Dad" else "woman" if caretaker == "Nana" else "man"
    return StoryParams(
        place=place,
        temptation=temptation,
        prize=prize,
        aid=aid,
        child1=child1,
        child1_type=child1_type,
        child2=child2,
        child2_type=child2_type,
        caretaker=caretaker,
        caretaker_type=caretaker_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        temptation = TEMPTATIONS[params.temptation]
        prize = PRIZES[params.prize]
        aid = AIDS[params.aid]
    except KeyError as err:
        raise StoryError(f"Invalid parameter: {err.args[0]}") from None
    c1 = Entity(id=params.child1, kind="character", type=params.child1_type, role="child")
    c2 = Entity(id=params.child2, kind="character", type=params.child2_type, role="child")
    car = Entity(id=params.caretaker, kind="character", type=params.caretaker_type, role="caretaker")
    world = tell(place, temptation, prize, aid, c1, c2, car)
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


ASP_RULES = r"""
place(P) :- affluent_place(P).
temptation(T) :- risky_temptation(T).
prize(Z) :- success_prize(Z).
aid(A) :- safe_aid(A).

worry(T) :- warning(T).
resolved :- choose_safe_way.
outcome(success) :- resolved.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
        if PLACES[p].affluent:
            lines.append(asp.fact("affluent_place", p))
    for t in TEMPTATIONS:
        lines.append(asp.fact("temptation", t))
        lines.append(asp.fact("risky_temptation", t))
        lines.append(asp.fact("warning", TEMPTATIONS[t].risky))
    for z in PRIZES:
        lines.append(asp.fact("prize", z))
        lines.append(asp.fact("success_prize", z))
    for a in AIDS:
        lines.append(asp.fact("aid", a))
        lines.append(asp.fact("safe_aid", a))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show place/1."))
    return sorted(set(asp.atoms(model, "place")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != {(p,) for p in PLACES}:
        print("MISMATCH in ASP world facts")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, temptation=None, prize=None, aid=None), random.Random(777)))
        _ = sample.story
        print("OK: smoke test generated a story.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    return rc


CURATED = [
    StoryParams(
        place="manor_garden",
        temptation="stone_bridge",
        prize="pear",
        aid="lantern",
        child1="Lily",
        child1_type="girl",
        child2="Theo",
        child2_type="boy",
        caretaker="Mum",
        caretaker_type="mother",
    ),
    StoryParams(
        place="rose_courtyard",
        temptation="pond_path",
        prize="star_cookie",
        aid="ribbon_pole",
        child1="Tom",
        child1_type="boy",
        child2="Mina",
        child2_type="girl",
        caretaker="Dad",
        caretaker_type="father",
    ),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show place/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(", ".join(p for (p,) in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
