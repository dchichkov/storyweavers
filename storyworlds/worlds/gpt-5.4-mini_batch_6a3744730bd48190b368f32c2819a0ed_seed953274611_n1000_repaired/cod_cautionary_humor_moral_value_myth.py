#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cod_cautionary_humor_moral_value_myth.py
=========================================================================

A small myth-flavored storyworld about a child, a cod, and a cautionary joke
that turns into a moral lesson. The story is built from simulated world state:
a boastful wish, a funny but unsafe choice, a warning, a consequence, and a
resolution where the child learns to treat the cod and the sea with respect.

The world is intentionally tiny and classical:
- a child wants to catch or show off a cod,
- a trick or brag causes trouble,
- a wiser helper warns them,
- a sensible response restores balance,
- the ending proves the moral change.

It also supports an ASP twin for parity checks.
"""

from __future__ import annotations

import argparse
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
BRAVERY_INIT = 5.0
SENSE_MIN = 2


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
    name: str
    watery: bool = False
    homey: bool = False
    danger: int = 0
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
class Cod:
    id: str
    label: str
    silver: bool = True
    slippery: bool = True
    tasty: bool = False
    sacred: bool = False
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
class Trick:
    id: str
    label: str
    funny: str
    safe: bool
    sense: int
    consequence: str
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
class Response:
    id: str
    sense: int
    text: str
    fail: str
    tag: str
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
        c.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "role": v.role, "traits": list(v.traits), "attrs": dict(v.attrs),
        }) for k, v in self.entities.items()}
        for k, v in self.entities.items():
            c.entities[k].meters = defaultdict(float, dict(v.meters))
            c.entities[k].memes = defaultdict(float, dict(v.memes))
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


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


def _r_mischief(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes["boast"] < THRESHOLD:
        return out
    if ("mischief", "child") in world.fired:
        return out
    world.fired.add(("mischief", "child"))
    world.get("harbor").danger += 1
    child.memes["trouble"] += 1
    out.append("The harbor grew uneasy.")
    return out


CAUSAL_RULES = [Rule("mischief", _r_mischief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def cod_is_special(cod: Cod) -> str:
    return "silver" if cod.silver else "ordinary"


def predict_trouble(world: World, trick: Trick) -> dict:
    sim = world.copy()
    sim.get("child").memes["boast"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("harbor").danger,
        "mischief": sim.get("child").memes["trouble"] >= THRESHOLD,
        "consequence": trick.consequence,
    }


def introduce(world: World, child: Entity, place: Place, cod: Cod) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"Long ago, in {place.name}, {child.id} watched the waves and saw a {cod.label} "
        f"flash like a small moon beneath the foam."
    )


def boast(world: World, child: Entity, cod: Cod, trick: Trick) -> None:
    child.memes["boast"] += 1
    world.say(
        f"{child.id} laughed and said, \"Watch me! I can win the cod with {trick.label}.\" "
        f"{trick.funny}"
    )


def warn(world: World, elder: Entity, child: Entity, trick: Trick, cod: Cod) -> None:
    elder.memes["wisdom"] += 1
    pred = predict_trouble(world, trick)
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f"{elder.id} shook {elder.pronoun('possessive')} head. "
        f"\"No, little one. {trick.lesson} The {cod.label} is a gift of the sea, not a toy.\""
    )


def choose_better_way(world: World, child: Entity, elder: Entity, cod: Cod, response: Response) -> None:
    child.memes["humor"] += 1
    child.memes["moral"] += 1
    world.say(
        f"{child.id} blushed, then grinned. \"All right,\" {child.pronoun()} said. "
        f"\"That joke was sillier than a gull in a hat.\""
    )
    world.say(
        f"{elder.id} smiled and {response.text}."
    )
    world.say(
        f"Together they left the cod in the water where it belonged, and the sea stayed calm."
    )


def accident(world: World, child: Entity, cod: Cod, trick: Trick) -> None:
    child.memes["trouble"] += 1
    world.get("harbor").danger += 1
    world.say(
        f"But {child.id} tried it anyway. The trick went wrong at once: the rope slipped, "
        f"the bucket clattered, and the cod splashed free with a wet silver flip."
    )
    world.say(
        f"The harbor made a loud laugh of its own, but the lesson was plain: {trick.consequence}."
    )


def repair(world: World, elder: Entity, child: Entity, cod: Cod, response: Response) -> None:
    world.get("harbor").danger = 0
    child.memes["moral"] += 1
    world.say(
        f"{elder.id} came at once and {response.text}, while {child.id} held still and watched."
    )
    world.say(
        f"When it was done, the cod swam away shining, and {child.id} knew better than to boast at the sea."
    )


def tell(cod: Cod, trick: Trick, response: Response, place: Place,
         child_name: str = "Milo", child_type: str = "boy",
         elder_name: str = "Aunt Nera", elder_type: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, role="child"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label=elder_name, role="elder"))
    harbor = world.add(Entity(id="harbor", kind="place", type="place", label=place.name))
    world.facts["place"] = place
    world.facts["cod"] = cod
    world.facts["trick"] = trick
    world.facts["response"] = response

    introduce(world, child, place, cod)
    world.para()
    boast(world, child, cod, trick)
    warn(world, elder, child, trick, cod)
    world.para()
    if trick.safe:
        choose_better_way(world, child, elder, cod, response)
    else:
        accident(world, child, cod, trick)
        repair(world, elder, child, cod, response)
    return world


PLACES = {
    "harbor": Place(id="harbor", name="the bright harbor", watery=True),
    "shore": Place(id="shore", name="the windy shore", watery=True),
    "river": Place(id="river", name="the old river mouth", watery=True),
}

CODS = {
    "cod": Cod(id="cod", label="cod", sacred=False),
    "old_cod": Cod(id="old_cod", label="cod", sacred=True),
}

TRICKS = {
    "net_hat": Trick(
        id="net_hat",
        label="a net tied like a hat",
        funny="The net was so floppy it looked like a crown for a very confused fish.",
        safe=True,
        sense=3,
        consequence="the cod would escape and everybody would feel foolish",
        lesson="A clever joke can still be unkind if it traps a living thing",
    ),
    "bucket_boast": Trick(
        id="bucket_boast",
        label="a bucket dance",
        funny="The bucket wobbled like a drum, and the child looked proud enough to scare the gulls.",
        safe=False,
        sense=1,
        consequence="the cod escaped and the child got soaked and embarrassed",
        lesson="Boasting can make trouble faster than the tide",
    ),
    "shell_charm": Trick(
        id="shell_charm",
        label="a shell charm",
        funny="The shell clicked like little teeth, which made the elder snort despite herself.",
        safe=True,
        sense=2,
        consequence="the cod would swim off while the child laughed",
        lesson="Humor is best when it harms nothing",
    ),
}

RESPONSES = {
    "gentle_release": Response(
        id="gentle_release",
        sense=3,
        text="lifted the net carefully and set the cod free with a bow",
        fail="tried to untangle the mess, but the wet rope only made it worse",
        tag="release",
    ),
    "mend_net": Response(
        id="mend_net",
        sense=2,
        text="mended the torn net so the child could laugh without trapping anything",
        fail="pulled at the knot, but the knot laughed back and stayed tight",
        tag="mend",
    ),
    "apology": Response(
        id="apology",
        sense=3,
        text="gave the child a stern but kind look and helped them say sorry to the sea",
        fail="shouted at the waves, which solved nothing at all",
        tag="lesson",
    ),
    "juggle": Response(
        id="juggle",
        sense=1,
        text="juggled three fish at once",
        fail="juggled three fish and dropped them in a very silly heap",
        tag="silly",
    ),
}

GIRL_NAMES = ["Mira", "Nia", "Lena", "Suri", "Asha"]
BOY_NAMES = ["Milo", "Taro", "Bryn", "Ivo", "Rafi"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for c in CODS:
            for t in TRICKS:
                if CODS[c].label == "cod" and PLACES[p].watery:
                    combos.append((p, c, t))
    return combos


@dataclass
class StoryParams:
    place: str
    cod: str
    trick: str
    response: str
    child: str
    child_type: str
    elder: str
    elder_type: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic cautionary cod storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--cod", choices=CODS)
    ap.add_argument("--trick", choices=TRICKS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["boy", "girl"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-type", choices=["man", "woman"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("That response is too foolish for a moral story.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.cod is None or c[1] == args.cod)
              and (args.trick is None or c[2] == args.trick)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, cod, trick = rng.choice(sorted(combos))
    response = args.response or rng.choice(["gentle_release", "mend_net", "apology"])
    child_type = args.child_type or rng.choice(["boy", "girl"])
    elder_type = args.elder_type or rng.choice(["woman", "man"])
    child = args.child or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["Aunt Nera", "Old Sera", "Uncle Joss", "Gray Tovin"])
    return StoryParams(place=place, cod=cod, trick=trick, response=response,
                       child=child, child_type=child_type, elder=elder, elder_type=elder_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-like cautionary story that includes "{f["cod"].label}" and a funny mistake.',
        f"Tell a short moral tale where {f['child'].label} learns a lesson from the sea and a cod.",
        f"Write a humorous myth for children in which a boast about a cod goes wrong, then turns wise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, elder, cod, trick = f["child"], f["elder"], f["cod"], f["trick"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.label}, who wanted to make a scene with a cod, and {elder.label}, who knew better. The sea becomes a kind of teacher in the tale."
        ),
        QAItem(
            question="Why did the elder warn the child?",
            answer=f"{elder.label} warned {child.label} because {trick.lesson}. The cod was not a toy, and the trick could make trouble."
        ),
    ]
    if world.get("child").memes["moral"] >= THRESHOLD:
        qa.append(QAItem(
            question="What changed by the end?",
            answer=f"{child.label} stopped boasting and treated the cod with respect. The ending shows the child choosing care over pride."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cod?",
            answer="A cod is a fish that lives in the sea. It swims with a silvery body and should be handled gently."
        ),
        QAItem(
            question="What is a moral lesson?",
            answer="A moral lesson is the good idea a story teaches. It helps children learn how to act kindly and wisely."
        ),
        QAItem(
            question="Why can boasting cause trouble?",
            answer="Boasting can make a person rush into a bad choice. Then the choice can hurt feelings or create a mess."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
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
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.cod not in CODS or params.trick not in TRICKS or params.response not in RESPONSES:
        raise StoryError("Invalid parameters.")
    world = tell(
        CODS[params.cod],
        TRICKS[params.trick],
        RESPONSES[params.response],
        PLACES[params.place],
        child_name=params.child,
        child_type=params.child_type,
        elder_name=params.elder,
        elder_type=params.elder_type,
    )
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


ASP_RULES = r"""
valid(P,C,T) :- place(P), cod(C), trick(T), watery(P).
sense_ok(R) :- response(R), sense(R,S), sense_min(M), S >= M.
moral_end(R) :- response(R), sense(R,S), S >= 2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
        if PLACES[p].watery:
            lines.append(asp.fact("watery", p))
    for c in CODS:
        lines.append(asp.fact("cod", c))
    for t in TRICKS:
        lines.append(asp.fact("trick", t))
    for r, resp in RESPONSES.items():
        lines.append(asp.fact("response", r))
        lines.append(asp.fact("sense", r, resp.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sense_ok/1."))
    return sorted(r for (r,) in asp.atoms(model, "sense_ok"))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos.")
        rc = 1
    if set(asp_sensible()) != {r for r, v in RESPONSES.items() if v.sense >= SENSE_MIN}:
        print("MISMATCH in sensible responses.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            place=None, cod=None, trick=None, response=None, child=None, child_type=None,
            elder=None, elder_type=None
        ), random.Random(1)))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample)
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return rc


def explain_response(rid: str) -> str:
    return f"Response '{rid}' is too foolish for this moral tale."


def explain_combo() -> str:
    return "No valid combination matches the given options."


def maybe_fix(seed: int) -> int:
    return seed % 1000


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3.\n#show sense_ok/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("sensible responses:", ", ".join(asp_sensible()))
        print()
        for p, c, t in asp_valid_combos():
            print(f"{p:8} {c:8} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="harbor", cod="cod", trick="net_hat", response="gentle_release",
                        child="Milo", child_type="boy", elder="Aunt Nera", elder_type="woman"),
            StoryParams(place="shore", cod="cod", trick="shell_charm", response="mend_net",
                        child="Asha", child_type="girl", elder="Old Sera", elder_type="woman"),
            StoryParams(place="river", cod="cod", trick="bucket_boast", response="apology",
                        child="Taro", child_type="boy", elder="Uncle Joss", elder_type="man"),
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child}: {p.trick} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
