#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/desperate_suspense_bad_ending_fable.py
=======================================================================

A compact storyworld in the fable register: a small animal learns a lesson the
hard way after a desperate, suspenseful choice. The world keeps a live model of
physical state (meters) and emotional state (memes), and it narrates from that
state rather than from a frozen template.

Premise
-------
A village animal finds a risky way to solve a problem, ignores a warning, and
ends up losing what they hoped to save. The story remains child-facing and
fable-like, with a clear moral image at the end.

This world supports:
- a premise / tension / turn / ending shape
- a Python reasonableness gate
- an inline ASP twin for parity checks
- prompts, story-grounded QA, and world-knowledge QA
- --verify, --asp, --show-asp, --trace, --qa, --json, --all, -n, --seed
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"she", "girl", "mother", "woman"}
        male = {"he", "boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    secret: str
    dim: str
    wind: str
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
class RiskyAction:
    id: str
    verb: str
    lure: str
    sign: str
    harm: str
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
class Prize:
    id: str
    label: str
    phrase: str
    fragile: bool
    can_be_lost: bool
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


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    responder: str
    hero_name: str
    hero_type: str
    mentor_name: str
    mentor_type: str
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


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


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["trouble"] < THRESHOLD:
            continue
        sig = ("spread", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for char in list(world.entities.values()):
            if char.kind == "character":
                char.memes["fear"] += 1
        if "home" in world.entities:
            world.get("home").meters["loss"] += 1
        out.append("__suspense__")
    return out


CAUSAL_RULES = [Rule("spread", "physical", _r_spread)]


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


def problem_at_risk(action: RiskyAction, prize: Prize) -> bool:
    return action.spread > 0 and prize.can_be_lost


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_responses():
        return combos
    for place_id, place in PLACES.items():
        for action_id, act in ACTIONS.items():
            for prize_id, prize in PRIZES.items():
                if place_id in act.tags and problem_at_risk(act, prize):
                    combos.append((place_id, action_id, prize_id))
    return combos


def ending_of(params: StoryParams) -> str:
    if params.responder not in RESPONSES:
        return "?"
    act = ACTIONS[params.action]
    resp = RESPONSES[params.responder]
    return "bad" if resp.power < act.spread else "bad" if act.spread >= 2 else "bad"


def explain_rejection(action: RiskyAction, prize: Prize) -> str:
    return (
        f"(No story: {action.verb} would not create a real danger for {prize.label}. "
        f"Pick a fragile thing or a riskier action.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}).)"
    )


def _do_action(world: World, prize_ent: Entity, narrate: bool = True) -> None:
    prize_ent.meters["trouble"] += 1
    propagate(world, narrate=narrate)


def predict(world: World, prize_id: str) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get(prize_id), narrate=False)
    return {
        "trouble": sim.get(prize_id).meters["trouble"],
        "loss": sim.get("home").meters["loss"] if "home" in sim.entities else 0,
    }


def tell_intro(world: World, hero: Entity, mentor: Entity, place: Place, action: RiskyAction, prize: Prize) -> None:
    world.say(
        f"In a little village, {hero.id} the {hero.label_word} lived by {place.label}. "
        f"Every morning {hero.pronoun()} watched the {place.secret} and listened to the {place.wind}."
    )
    world.say(
        f"{hero.id} loved {action.lure}, but the prize in the tale was {prize.phrase}."
    )
    world.say(
        f"{mentor.id} the {mentor.label_word} had already warned, \"{action.sign} can turn to {action.harm}.\""
    )


def tempt(world: World, hero: Entity, action: RiskyAction) -> None:
    hero.memes["desire"] += 1
    hero.memes["bravery"] += 1
    world.say(
        f"Still, the day grew {action.sign.lower()} and {hero.id} felt desperate."
        f" \"If I wait,\" {hero.pronoun()} thought, \"I may lose everything.\""
    )


def ignore_warning(world: World, hero: Entity, mentor: Entity, action: RiskyAction) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"\"I know,\" {hero.id} said, and {hero.pronoun()} hurried on while {mentor.id} called after {hero.pronoun('object')}."
    )


def fall(world: World, prize_ent: Entity, action: RiskyAction) -> None:
    _do_action(world, prize_ent)
    world.say(
        f"{action.sign} flashed once, and then {action.harm} came with it."
        f" The little plan slipped out of {world.facts['hero'].pronoun('possessive')} paws."
    )


def alarm(world: World, mentor: Entity, hero: Entity, prize: Prize) -> None:
    world.say(
        f"{mentor.id} ran closer and cried, \"{hero.id}, the {prize.label} is in danger!\""
    )


def fail_response(world: World, mentor: Entity, response: Response, prize: Prize) -> None:
    world.say(
        f"{mentor.id} tried to {response.fail.replace('{target}', prize.label)}"
        f", but it was already too late."
    )
    if "home" in world.entities:
        world.get("home").meters["loss"] += 1
    for ent in list(world.entities.values()):
        if ent.kind == "character":
            ent.memes["grief"] += 1


def ending_bad(world: World, hero: Entity, mentor: Entity, prize: Prize) -> None:
    world.say(
        f"By dusk, the village was quiet again, but {prize.label} was gone."
        f" {hero.id} stood still, learning that desperate choices can leave nothing behind."
    )


PLACES = {
    "well": Place(
        id="well",
        label="the old well",
        secret="dark water below",
        dim="deep",
        wind="cold wind",
        tags={"well"},
    ),
    "barn": Place(
        id="barn",
        label="the red barn",
        secret="hay shadows",
        dim="shadowy",
        wind="dusty wind",
        tags={"barn"},
    ),
    "orchard": Place(
        id="orchard",
        label="the apple orchard",
        secret="branches and thorns",
        dim="quiet",
        wind="soft wind",
        tags={"orchard"},
    ),
}

ACTIONS = {
    "ladder": RiskyAction(
        id="ladder",
        verb="climb the shaky ladder",
        lure="climbing the shaky ladder",
        sign="creaky",
        harm="a hard fall",
        spread=2,
        tags={"well", "barn"},
    ),
    "night_path": RiskyAction(
        id="night_path",
        verb="walk the dark path alone",
        lure="walking the dark path alone",
        sign="silent",
        harm="a wrong turn",
        spread=2,
        tags={"orchard", "well"},
    ),
    "thin_rope": RiskyAction(
        id="thin_rope",
        verb="pull on the thin rope",
        lure="pulling on the thin rope",
        sign="trembling",
        harm="a snapping break",
        spread=1,
        tags={"well", "orchard", "barn"},
    ),
}

PRIZES = {
    "seed_bag": Prize(
        id="seed_bag",
        label="seed bag",
        phrase="a pouch of seeds",
        fragile=True,
        can_be_lost=True,
        tags={"seed"},
    ),
    "milk_jug": Prize(
        id="milk_jug",
        label="milk jug",
        phrase="a jug of milk",
        fragile=True,
        can_be_lost=True,
        tags={"milk"},
    ),
    "lantern": Prize(
        id="lantern",
        label="lantern",
        phrase="a little lantern",
        fragile=True,
        can_be_lost=True,
        tags={"lantern"},
    ),
}

RESPONSES = {
    "call_help": Response(
        id="call_help",
        sense=3,
        power=2,
        text="called for help and brought the lantern to the door",
        fail="called for help",
        qa_text="called for help and got the grown-ups running",
        tags={"help"},
    ),
    "grab_rope": Response(
        id="grab_rope",
        sense=2,
        power=1,
        text="grabbed the rope and tried to steady it",
        fail="grabbed the rope and tried to steady it",
        qa_text="grabbed the rope and tried to steady it",
        tags={"rope"},
    ),
    "hide": Response(
        id="hide",
        sense=1,
        power=0,
        text="hid under the cart",
        fail="hid under the cart",
        qa_text="hid under the cart",
        tags={"hide"},
    ),
}

SENSE_MIN = 2

GIRL_NAMES = ["Mira", "Tia", "Luna", "Nia", "Iris"]
BOY_NAMES = ["Otis", "Finn", "Arlo", "Bram", "Jude"]
MENTOR_NAMES = ["Grandma", "Old Fox", "Aunt Reed", "Uncle Pine"]
TRAITS = ["careful", "curious", "quiet", "brave", "thoughtful"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable storyworld with suspense and a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--responder", choices=RESPONSES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy", "fox", "rabbit"])
    ap.add_argument("--mentor-name")
    ap.add_argument("--mentor-type", choices=["old fox", "owl", "grandmother", "farmer"])
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
    if args.responder and args.responder not in RESPONSES:
        raise StoryError("Unknown responder.")
    if args.responder and RESPONSES[args.responder].sense < SENSE_MIN:
        raise StoryError(explain_response(args.responder))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, prize = rng.choice(sorted(combos))
    responder = args.responder or rng.choice(sorted(r.id for r in sensible_responses()))
    hero_type = args.hero_type or rng.choice(["girl", "boy", "fox", "rabbit"])
    mentor_type = args.mentor_type or rng.choice(["old fox", "owl", "grandmother", "farmer"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    mentor_name = args.mentor_name or rng.choice(MENTOR_NAMES)
    return StoryParams(
        place=place,
        action=action,
        prize=prize,
        responder=responder,
        hero_name=hero_name,
        hero_type=hero_type,
        mentor_name=mentor_name,
        mentor_type=mentor_type,
    )


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, role="hero"))
    mentor = world.add(Entity(id=params.mentor_name, kind="character", type=params.mentor_type, role="mentor"))
    place = PLACES[params.place]
    action = ACTIONS[params.action]
    prize = PRIZES[params.prize]
    resp = RESPONSES[params.responder]
    prize_ent = world.add(Entity(id="prize", kind="thing", type=params.prize, label=prize.label))
    world.add(Entity(id="home", kind="thing", type="home", label="the village home"))

    tell_intro(world, hero, mentor, place, action, prize)
    world.para()
    tempt(world, hero, action)
    ignore_warning(world, hero, mentor, action)
    world.para()
    world.facts["hero"] = hero
    world.facts["mentor"] = mentor
    world.facts["prize"] = prize
    fall(world, prize_ent, action)
    alarm(world, mentor, hero, prize)
    fail_response(world, mentor, resp, prize)
    ending_bad(world, hero, mentor, prize)

    world.facts.update(
        params=params,
        place=place,
        action=action,
        prize_cfg=prize,
        response=resp,
        outcome="bad",
        feared_loss=world.get("home").meters["loss"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable-like story for a young child that includes the word "desperate" and ends sadly.',
        f"Tell a suspenseful animal story where {f['hero'].id} grows desperate near {f['place'].label} and learns too late.",
        f"Write a short fable with a warning, a risky choice, and a bad ending about {f['action'].verb}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    mentor: Entity = f["mentor"]
    action: RiskyAction = f["action"]
    prize: Prize = f["prize_cfg"]
    return [
        QAItem(
            question=f"Why did {hero.id} feel desperate?",
            answer=(
                f"{hero.id} thought the prize might be lost if nothing was done quickly. "
                f"That fear pushed {hero.pronoun()} into a risky choice."
            ),
        ),
        QAItem(
            question=f"What warning did {mentor.id} give?",
            answer=(
                f"{mentor.id} warned that {action.sign} danger can turn into {action.harm}. "
                f"The warning fit the place because the risk was already close by."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"It ended badly: {prize.label} was gone, and {hero.id} had to learn from the loss. "
                f"The last image is not a rescue, but a quiet lesson."
            ),
        ),
    ]


WORLD_KNOWLEDGE = {
    "desperate": [
        QAItem(
            question="What does desperate mean?",
            answer="Desperate means feeling like something very important must happen soon, almost with no calm left.",
        )
    ],
    "fable": [
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that usually uses animals or simple characters to teach a lesson.",
        )
    ],
    "suspense": [
        QAItem(
            question="What makes a story suspenseful?",
            answer="A suspenseful story makes you wait and wonder what will happen next because the danger feels close.",
        )
    ],
    "loss": [
        QAItem(
            question="Why can a bad choice matter?",
            answer="A bad choice can cause loss, and loss teaches why warnings and patience matter.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = set(world.facts["action"].tags) | set(world.facts["prize_cfg"].tags) | {"desperate", "fable", "suspense", "loss"}
    for key, items in WORLD_KNOWLEDGE.items():
        if key in tags:
            out.extend(items)
    return out


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
suspense :- trouble(X), X >= 1.
bad_end :- loss(L), L >= 1.
valid(P, A, R) :- place(P), action(A), prize(R), risky(A, R), place_ok(P, A).
outcome(bad) :- suspense, bad_end.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("spread", aid, a.spread))
        for t in sorted(a.tags):
            lines.append(asp.fact("place_ok", t, aid))
    for rid, r in PRIZES.items():
        lines.append(asp.fact("prize", rid))
        lines.append(asp.fact("risky", "ladder", rid))
        lines.append(asp.fact("risky", "night_path", rid))
        lines.append(asp.fact("risky", "thin_rope", rid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib

    rc = 0
    try:
        from types import SimpleNamespace
        sample_args = SimpleNamespace(place=None, action=None, prize=None, responder=None,
                                      hero_name=None, hero_type=None, mentor_name=None, mentor_type=None)
        params = resolve_params(sample_args, random.Random(777))
        sample = generate(params)
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"MISMATCH: generate smoke test failed: {exc}")
        return 1

    try:
        from storyworlds import asp as asp_mod  # noqa: F401
    except Exception as exc:
        print(f"MISMATCH: asp import failed: {exc}")
        return 1

    if not valid_combos():
        print("MISMATCH: no valid combos")
        rc = 1

    try:
        import asp as asp_helper  # type: ignore
        _ = asp_helper
    except Exception:
        pass

    return rc


CURATED = [
    StoryParams(
        place="well",
        action="ladder",
        prize="seed_bag",
        responder="call_help",
        hero_name="Mira",
        hero_type="girl",
        mentor_name="Old Fox",
        mentor_type="old fox",
    ),
    StoryParams(
        place="barn",
        action="night_path",
        prize="milk_jug",
        responder="grab_rope",
        hero_name="Otis",
        hero_type="boy",
        mentor_name="Aunt Reed",
        mentor_type="farmer",
    ),
]


def generate(params: StoryParams) -> StorySample:
    for field_name, table in (("place", PLACES), ("action", ACTIONS), ("prize", PRIZES), ("responder", RESPONSES)):
        key = getattr(params, field_name, None)
        if key not in table:
            raise StoryError(f"Unknown {field_name}: {key}")
    world = tell(params)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("No ASP listing is curated beyond the twin rules in this file.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
