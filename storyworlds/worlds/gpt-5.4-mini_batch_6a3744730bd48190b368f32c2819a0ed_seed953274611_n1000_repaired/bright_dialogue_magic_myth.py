#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bright_dialogue_magic_myth.py
==============================================================

A small myth-style storyworld about a bright spark of magic, spoken warnings,
and a child who learns to use wonder wisely.

Premise:
- A young helper receives a bright magical token.
- They are tempted to use it in a boastful way.
- A wiser voice warns them in dialogue.
- The magic either becomes a helpful gift or goes awry, depending on the world.
- The ending proves what changed: a brighter home, a calmer heart, or a mended
  shrine.

The world is intentionally small: one magical object, one bright place, one
warning helper, one elder or shrine-keeper, and a few carefully constrained
outcomes. The prose is authored from simulated state, not a frozen template.
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
MAGIC_MIN = 2
BRIGHT_MIN = 1


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
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
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
class BrightThing:
    id: str
    label: str
    phrase: str
    glows: bool = False
    wants_handled_with_care: bool = False
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
class Magic:
    id: str
    label: str
    phrase: str
    power: int
    wise_use: str
    risky_use: str
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
class Place:
    id: str
    label: str
    phrase: str
    dark_corner: str
    bright_corner: str
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


def _r_brighten(world: World) -> list[str]:
    out: list[str] = []
    shrine = world.entities.get("shrine")
    for e in list(world.entities.values()):
        if e.meters["shimmer"] < THRESHOLD:
            continue
        sig = ("brighten", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if shrine is not None:
            shrine.meters["light"] += 1
        out.append("__bright__")
    return out


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["fear"] < THRESHOLD:
            continue
        sig = ("settle", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["fear"] = max(0.0, e.memes["fear"] - 1.0)
        e.memes["reverence"] += 1
        out.append("__settle__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("brighten", _r_brighten),
    Rule("settle", _r_settle),
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


def valid_magic(magic: Magic, bright: BrightThing) -> bool:
    return magic.power >= MAGIC_MIN and bright.glows


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= BRIGHT_MIN]


def recommended_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def outcome_of(params: "StoryParams") -> str:
    if params.persists == "echo":
        return "echo"
    if params.response == "quench" and params.delay > 1:
        return "dim"
    return "gift"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': sense={r.sense} is too low for a mythic tale.)"


def _do_magic(world: World, target: Entity, magic: Magic, narrate: bool = True) -> None:
    target.meters["shimmer"] += 1
    target.memes["wonder"] += 1
    propagate(world, narrate=narrate)


def predict(world: World, magic: Magic, target_id: str) -> dict:
    sim = world.copy()
    _do_magic(sim, sim.get(target_id), magic, narrate=False)
    shrine = sim.entities.get("shrine")
    return {
        "brighter": bool(shrine and shrine.meters["light"] >= THRESHOLD),
        "fear": sum(e.memes["fear"] for e in sim.entities.values()),
    }


def opening(world: World, child: Entity, helper: Entity, place: Place, bright: BrightThing) -> None:
    child.memes["curiosity"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"At {place.phrase}, {child.id} found {bright.phrase}, and it shone bright "
        f"as a new star."
    )
    world.say(
        f'"Look," said {child.id}. "It feels like a blessing." '
        f'"It is a blessing," said {helper.id}, "but blessings must be handled well."'
    )


def warn(world: World, helper: Entity, child: Entity, bright: BrightThing, place: Place) -> None:
    pred = predict(world, MAGICS["spark"], "bright")
    helper.memes["care"] += 1
    world.facts["predicted_brighter"] = pred["brighter"]
    world.say(
        f'"Do not wave it in the {place.dark_corner}," said {helper.id}. '
        f'"A bright thing can wake old trouble."'
    )


def boast(world: World, child: Entity, bright: BrightThing, magic: Magic) -> None:
    child.memes["pride"] += 1
    world.say(
        f'"I am not afraid," said {child.id}. "If I call the {magic.label}, '
        f'it will answer me."'
    )


def invoke(world: World, child: Entity, bright: BrightThing, magic: Magic) -> None:
    _do_magic(world, world.get("bright"), magic)
    world.say(
        f'{magic.phrase.capitalize()} answered at once, and {bright.phrase} rose '
        f'into the air like a lantern caught by moonlight.'
    )


def mishap(world: World, place: Place, bright: BrightThing) -> None:
    world.get("shrine").memes["alarm"] += 1
    world.get("shrine").meters["crack"] += 1
    world.say(
        f'But the light slipped into the {place.dark_corner}, and the old shrine '
        f'shone too fiercely for a heartbeat. A small crack sang through the stone.'
    )


def rescue(world: World, elder: Entity, response: Response, bright: BrightThing) -> None:
    body = response.text.replace("{bright}", bright.label)
    world.say(
        f"{elder.id} came quickly and {body}."
    )
    world.get("shrine").meters["light"] += 1
    world.say(
        f"The shrine held steady, and the room filled with a calm, golden glow."
    )


def dim_end(world: World, elder: Entity, response: Response, bright: BrightThing) -> None:
    body = response.fail.replace("{bright}", bright.label)
    world.say(f"{elder.id} tried, but {body}.")
    world.say(
        "The glow faded to a weak ember, and the little hall went quiet."
    )


def lesson(world: World, elder: Entity, child: Entity, bright: BrightThing, magic: Magic) -> None:
    child.memes["reverence"] += 1
    child.memes["joy"] += 1
    world.say(
        f'"Remember," said {elder.id}, "magic is brightest when it is used with care."'
    )
    world.say(
        f'{child.id} bowed their head and answered, "Then I will be wise with it."'
    )


def gift_end(world: World, child: Entity, elder: Entity, bright: BrightThing) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{elder.id} smiled and placed {bright.phrase} into {child.id}'s hands, "
        f"and this time it felt warm, not wild."
    )
    world.say(
        "The hall glowed bright, and even the shadows seemed to listen."
    )


@dataclass
class StoryParams:
    place: str
    bright: str
    magic: str
    response: str
    delay: int = 0
    child: str = "Ari"
    helper: str = "Mira"
    elder: str = "Orin"
    child_gender: str = "girl"
    helper_gender: str = "girl"
    elder_gender: str = "boy"
    persists: str = "gift"
    trait: str = "curious"
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


def tale(world: World, child: Entity, helper: Entity, elder: Entity, place: Place,
         bright: BrightThing, magic: Magic, response: Response, delay: int, persists: str) -> World:
    opening(world, child, helper, place, bright)
    world.para()
    warn(world, helper, child, bright, place)
    boast(world, child, bright, magic)

    if persists == "echo":
        world.say(f'"Then I will test it," said {child.id}, "just once."')
        world.para()
        invoke(world, child, bright, magic)
        mishap(world, place, bright)
        world.para()
        rescue(world, elder, response, bright)
        lesson(world, elder, child, bright, magic)
    elif outcome_of(StoryParams(place=place.id, bright=bright.id, magic=magic.id, response=response.id, delay=delay, child=child.id, helper=helper.id, elder=elder.id, child_gender=child.type, helper_gender=helper.type, elder_gender=elder.type, persists="gift", seed=None)) == "dim":
        world.say(f'"Then I will test it," said {child.id}, "just once."')
        world.para()
        invoke(world, child, bright, magic)
        world.para()
        dim_end(world, elder, response, bright)
        lesson(world, elder, child, bright, magic)
    else:
        world.say(f'"Then I will test it," said {child.id}, "just once."')
        world.para()
        invoke(world, child, bright, magic)
        world.para()
        rescue(world, elder, response, bright)
        lesson(world, elder, child, bright, magic)
        world.para()
        gift_end(world, child, elder, bright)

    world.facts.update(
        child=child, helper=helper, elder=elder, place=place,
        bright=bright, magic=magic, response=response, delay=delay,
        persists=persists, outcome=outcome_of(StoryParams(place=place.id, bright=bright.id, magic=magic.id, response=response.id, delay=delay, child=child.id, helper=helper.id, elder=elder.id, child_gender=child.type, helper_gender=helper.type, elder_gender=elder.type, persists=persists, seed=None)),
    )
    return world


PLACES = {
    "temple": Place(id="temple", label="temple", phrase="the hill-temple", dark_corner="shadowed stair", bright_corner="sunlit gate", tags={"temple", "myth"}),
    "harbor": Place(id="harbor", label="harbor", phrase="the sea harbor", dark_corner="black water", bright_corner="silver dock", tags={"harbor", "myth"}),
    "grove": Place(id="grove", label="grove", phrase="the elder grove", dark_corner="root-cave", bright_corner="leaf-path", tags={"grove", "myth"}),
}

MAGICS = {
    "spark": Magic(id="spark", label="spark", phrase="the bright spark", power=3, wise_use="to guide a traveler home", risky_use="to show off in the dark", tags={"spark", "bright", "magic"}),
    "lamp": Magic(id="lamp", label="lamp charm", phrase="the lamp charm", power=2, wise_use="to light a path", risky_use="to summon storms", tags={"lamp", "bright", "magic"}),
    "thread": Magic(id="thread", label="golden thread", phrase="the golden thread", power=2, wise_use="to mend a torn banner", risky_use="to bind a sleeping spirit", tags={"thread", "bright", "magic"}),
}

BRIGHTS = {
    "starstone": BrightThing(id="starstone", label="starstone", phrase="a starstone on a cord", glows=True, wants_handled_with_care=True, tags={"bright", "stone"}),
    "sunbowl": BrightThing(id="sunbowl", label="sun-bowl", phrase="a sun-bowl of polished gold", glows=True, wants_handled_with_care=True, tags={"bright", "gold"}),
}

RESPONSES = {
    "pray": Response(id="pray", sense=3, power=3, text="lifted the starstone and prayed until the light steadied around the shrine", fail="lifted the starstone and prayed, but the light would not listen", qa_text="lifted the starstone and prayed until the light steadied around the shrine", tags={"prayer", "gentle"}),
    "quench": Response(id="quench", sense=2, power=2, text="covered the bright stone with a woven cloth and waited until its glow calmed down", fail="covered the bright stone with a cloth, but the glow was too fierce to calm", qa_text="covered the bright stone with a woven cloth and waited until its glow calmed down", tags={"cloth", "calm"}),
    "chant": Response(id="chant", sense=3, power=4, text="chanted the old words and drew a circle of salt around the shrine", fail="chanted the old words, but the circle broke before the light could settle", qa_text="chanted the old words and drew a circle of salt around the shrine", tags={"chant", "salt"}),
}

GIRL_NAMES = ["Ari", "Mira", "Lina", "Sela", "Tia", "Nora"]
BOY_NAMES = ["Orin", "Daro", "Kian", "Pavel", "Rian", "Tomas"]
TRAITS = ["curious", "gentle", "bold", "quiet", "clever"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for b in BRIGHTS:
            for m in MAGICS:
                if valid_magic(MAGICS[m], BRIGHTS[b]):
                    combos.append((p, b, m))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-like story for a child that includes the word "bright" and a wise warning in dialogue.',
        f"Tell a short myth where {f['child'].id} finds {f['bright'].phrase} and learns to use {f['magic'].label} carefully.",
        f'Write a gentle magical story with spoken lines, an old place, and a bright ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, elder = f["child"], f["helper"], f["elder"]
    bright, magic, place = f["bright"], f["magic"], f["place"]
    qa = [
        QAItem(
            question=f"Who found the bright thing?",
            answer=f"{child.id} found {bright.phrase} at {place.phrase}. It mattered because the light drew everyone toward the old place.",
        ),
        QAItem(
            question=f"What did {helper.id} warn {child.id} about?",
            answer=f"{helper.id} warned {child.id} not to use {magic.label} in the dark corner. The warning mattered because bright magic can wake old trouble.",
        ),
    ]
    if f["outcome"] == "gift":
        qa.append(QAItem(
            question="How did the story end?",
            answer=f"It ended with {bright.phrase} becoming a safe gift. {elder.id} placed it into {child.id}'s hands, and the hall glowed bright and calm.",
        ))
    elif f["outcome"] == "dim":
        qa.append(QAItem(
            question="How did the story end?",
            answer=f"It ended with the glow fading to a weak ember. {elder.id} and the others kept everyone safe, but the magic did not stay bright.",
        ))
    else:
        qa.append(QAItem(
            question="How did the story end?",
            answer=f"It ended with a crack in the shrine and a hard lesson. The bright magic had to be soothed and repaired before the place could rest again.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does magic do in a myth?",
            answer="Magic can make strange things happen that feel larger than an ordinary day. In myths, people often learn that magic should be used with respect.",
        ),
        QAItem(
            question="Why is bright light important in a story like this?",
            answer="Bright light can show the way, reveal a hidden path, or wake a sleeping place. It also makes the danger easier to see, which is why the characters speak carefully.",
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="temple", bright="starstone", magic="spark", response="chant", delay=0, child="Ari", helper="Mira", elder="Orin", child_gender="girl", helper_gender="girl", elder_gender="boy", persists="gift", trait="curious"),
    StoryParams(place="grove", bright="sunbowl", magic="lamp", response="pray", delay=1, child="Tomas", helper="Sela", elder="Nora", child_gender="boy", helper_gender="girl", elder_gender="girl", persists="gift", trait="bold"),
    StoryParams(place="harbor", bright="starstone", magic="thread", response="quench", delay=2, child="Lina", helper="Daro", elder="Kian", child_gender="girl", helper_gender="boy", elder_gender="boy", persists="echo", trait="gentle"),
]


def explain_rejection(magic: Magic, bright: BrightThing) -> str:
    if not valid_magic(magic, bright):
        return f"(No story: {magic.label} needs a truly bright thing to matter.)"
    return "(No story: this combination is not reasonable for the world.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for bid, b in BRIGHTS.items():
        lines.append(asp.fact("bright", bid))
        if b.glows:
            lines.append(asp.fact("glows", bid))
    for mid, m in MAGICS.items():
        lines.append(asp.fact("magic", mid))
        lines.append(asp.fact("power", mid, m.power))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", MAGIC_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,B,M) :- place(P), bright(B), magic(M), glows(B), power(M,Pow), power_min(Min), Pow >= Min.
"""


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    try:
        c = set(asp_valid_combos())
        p = set(valid_combos())
        if c != p:
            print("MISMATCH in valid combos:")
            print(" clingo-only:", sorted(c - p))
            print(" python-only:", sorted(p - c))
            return 1
        sample = generate(resolve_params(argparse.Namespace(place=None, bright=None, magic=None, response=None, seed=None, all=False, trace=False, qa=False, json=False, asp=False, verify=False, show_asp=False), random.Random(7)))
        _ = sample.story
        print("OK: ASP parity and generation smoke test passed.")
        return 0
    except Exception as e:
        print(f"VERIFY FAILED: {e}")
        return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mythic storyworld with bright magic and dialogue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--bright", choices=BRIGHTS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
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
    if args.magic and args.bright and not valid_magic(MAGICS[args.magic], BRIGHTS[args.bright]):
        raise StoryError(explain_rejection(MAGICS[args.magic], BRIGHTS[args.bright]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.bright is None or c[1] == args.bright)
              and (args.magic is None or c[2] == args.magic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, bright, magic = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    child = args.child or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = args.helper or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != child])
    elder = args.elder or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n not in {child, helper}])
    child_gender = "girl" if child in GIRL_NAMES else "boy"
    helper_gender = "girl" if helper in GIRL_NAMES else "boy"
    elder_gender = "girl" if elder in GIRL_NAMES else "boy"
    return StoryParams(place=place, bright=bright, magic=magic, response=response, child=child, helper=helper, elder=elder, child_gender=child_gender, helper_gender=helper_gender, elder_gender=elder_gender, persists=rng.choice(["gift", "dim", "echo"]), trait=rng.choice(TRAITS))


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.bright not in BRIGHTS or params.magic not in MAGICS or params.response not in RESPONSES:
        raise StoryError("Invalid parameters.")
    world = World()
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    elder = world.add(Entity(id=params.elder, kind="character", type=params.elder_gender, role="elder"))
    place = world.add(Entity(id="place", kind="place", type="place", label=PLACES[params.place].phrase))
    bright = world.add(Entity(id="bright", kind="thing", type="thing", label=BRIGHTS[params.bright].label))
    shrine = world.add(Entity(id="shrine", kind="thing", type="thing", label="shrine"))
    world.facts["place"] = PLACES[params.place]
    world.facts["bright_cfg"] = BRIGHTS[params.bright]
    world.facts["magic_cfg"] = MAGICS[params.magic]

    tale(world, child, helper, elder, PLACES[params.place], BRIGHTS[params.bright], MAGICS[params.magic], RESPONSES[params.response], params.delay, params.persists)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos:")
        for t in asp_valid_combos():
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
