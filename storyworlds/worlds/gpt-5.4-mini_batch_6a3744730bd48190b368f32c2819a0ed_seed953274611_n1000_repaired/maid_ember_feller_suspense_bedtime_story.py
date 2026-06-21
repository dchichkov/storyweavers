#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/maid_ember_feller_suspense_bedtime_story.py
=============================================================================

A small bedtime-suspense storyworld about a maid, an ember, and a feller.
A sleepy child hears a soft warning, a tiny danger grows, and a calm helper
handles it before the house can wake fully.

The world is intentionally tiny: a maid keeps a house quiet and safe, a feller
works by day and returns with kind hands, and an ember may appear near a cloth
or hearth. Suspense comes from the delay between noticing the ember and acting
on it. The ending always proves what changed in the room and in the characters'
memes.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SUSPENSE_THRESHOLD = 1.0
LIGHT_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    warm: bool = False
    dry: bool = False
    flammable: bool = False
    ember_risk: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"maid", "woman", "girl", "mother", "mom"}
        male = {"feller", "man", "boy", "father", "dad"}
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
class Setting:
    id: str
    room: str
    quiet: str
    dark_spot: str
    glow_spot: str
    ending_image: str
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
class Hazard:
    id: str
    label: str
    phrase: str
    makes_ember: bool = True
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
class EmberPlace:
    id: str
    label: str
    phrase: str
    flammable: bool = True
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    ember = world.entities.get("ember")
    if not ember or ember.meters.get("glowing", 0.0) < THRESHOLD:
        return out
    if ("worry",) in world.fired:
        return out
    world.fired.add(("worry",))
    for ent in list(world.entities.values()):
        if ent.role in {"maid", "feller"}:
            ent.memes["worry"] = ent.memes.get("worry", 0.0) + 1
    room = world.entities.get("room")
    if room:
        room.meters["danger"] = room.meters.get("danger", 0.0) + 1
    out.append("__worry__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def hazard_at_risk(hazard: Hazard, place: EmberPlace) -> bool:
    return hazard.makes_ember and place.flammable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for h in HAZARDS:
        for p in PLACES:
            if hazard_at_risk(h, p):
                out.append((h.id, p.id))
    return out


def ember_severity(place: EmberPlace, delay: int) -> int:
    return 1 + delay + (1 if place.flammable else 0)


def is_contained(response: Response, place: EmberPlace, delay: int) -> bool:
    return response.power >= ember_severity(place, delay)


def predict_ember(world: World, place_id: str) -> dict:
    sim = World()
    for eid, ent in world.entities.items():
        sim.entities[eid] = Entity(
            id=ent.id, kind=ent.kind, type=ent.type, label=ent.label, role=ent.role,
            traits=list(ent.traits), attrs=dict(ent.attrs), meters=dict(ent.meters),
            memes=dict(ent.memes), warm=ent.warm, dry=ent.dry, flammable=ent.flammable,
            ember_risk=ent.ember_risk,
        )
    sim.get("ember").meters["glowing"] = 1.0
    propagate(sim, narrate=False)
    return {"danger": sim.get("room").meters.get("danger", 0.0)}


def setup(world: World, maid: Entity, feller: Entity, setting: Setting) -> None:
    world.say(
        f"At {setting.room}, the night was so quiet it seemed to hold its breath. "
        f"{setting.quiet} {setting.dark_spot} and {setting.glow_spot} waited like secrets."
    )
    world.say(
        f"{maid.id} the maid kept the room neat, and {feller.id} the feller came in "
        f"with tired shoulders and a kind face."
    )


def need_light(world: World, maid: Entity, setting: Setting) -> None:
    maid.memes["care"] = maid.memes.get("care", 0.0) + 1
    world.say(
        f"In the hush, {maid.id} noticed that {setting.dark_spot} was still too dim. "
        f"She whispered that even a bedtime room should be safe."
    )


def tempt(world: World, hazard: Hazard, place: EmberPlace) -> None:
    world.say(
        f"Then a tiny {hazard.label} shimmered near {place.phrase}, as soft as a bead "
        f"of red thread. It looked small, but it did not belong there."
    )


def warn(world: World, maid: Entity, feller: Entity, hazard: Hazard, place: EmberPlace) -> None:
    pred = predict_ember(world, "place")
    maid.memes["warning"] = maid.memes.get("warning", 0.0) + 1
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f"{maid.id} bit her lip. '{hazard.label.capitalize()} can wake a fire,' she said. "
        f"'{place.label.capitalize()} must be watched.'"
    )
    world.say(
        f"{feller.id} nodded, because bedtime is for gentle thinking and quick hands."
    )


def spread_ember(world: World, place_ent: Entity, hazard: Hazard, place: EmberPlace) -> None:
    place_ent.meters["glowing"] = place_ent.meters.get("glowing", 0.0) + 1
    world.get("room").meters["danger"] = world.get("room").meters.get("danger", 0.0) + 1
    propagate(world, narrate=False)
    world.say(
        f"The {hazard.label} gave a little bright blink. For one breath it seemed as if "
        f"it might climb, but it stayed near {place.phrase} and waited."
    )


def alarm(world: World, maid: Entity, feller: Entity, place: EmberPlace) -> None:
    world.say(
        f"'{feller.id}!' {maid.id} whispered, and then louder: 'The ember!'"
    )
    world.say(
        f"{feller.id} came at once, quiet as a shadow and quick as a prayer."
    )


def rescue(world: World, feller: Entity, response: Response, place_ent: Entity, place: EmberPlace) -> None:
    place_ent.meters["glowing"] = 0.0
    world.get("room").meters["danger"] = 0.0
    world.say(
        f"{feller.id} {response.text.replace('{place}', place.label)}."
    )
    world.say(
        f"The ember sighed out, leaving only a safe, sleepy smell in the air."
    )


def rescue_fail(world: World, feller: Entity, response: Response, place_ent: Entity, place: EmberPlace) -> None:
    place_ent.meters["glowing"] = 1.0
    world.get("room").meters["danger"] = 2.0
    world.say(
        f"{feller.id} tried to help, but {response.fail.replace('{place}', place.label)}."
    )
    world.say(
        f"The little light kept threatening to grow, and the house felt too thin with worry."
    )


def ending(world: World, maid: Entity, feller: Entity, setting: Setting, response: Response, place: EmberPlace, contained: bool) -> None:
    maid.memes["relief"] = maid.memes.get("relief", 0.0) + 1
    feller.memes["relief"] = feller.memes.get("relief", 0.0) + 1
    if contained:
        world.say(
            f"After that, {maid.id} tucked the blanket straighter, and {feller.id} "
            f"looked once at {setting.ending_image}. The room was quiet again, and the night "
            f"could rest."
        )
    else:
        world.say(
            f"After that, {maid.id} and {feller.id} opened the door and called for help, "
            f"because the ember had grown too bold for a sleepy room. They were safe, "
            f"though the little house would need care in the morning."
        )


def tell(setting: Setting, hazard: Hazard, place: EmberPlace, response: Response,
         maid_name: str = "Mina", feller_name: str = "Fenn", delay: int = 0) -> World:
    world = World()
    maid = world.add(Entity(id=maid_name, kind="character", type="maid", label="the maid", role="maid"))
    feller = world.add(Entity(id=feller_name, kind="character", type="feller", label="the feller", role="feller"))
    room = world.add(Entity(id="room", kind="thing", type="room", label="the room"))
    ember_ent = world.add(Entity(id="ember", kind="thing", type="ember", label="the ember", flammable=True))
    place_ent = world.add(Entity(id="place", kind="thing", type="place", label=place.label, flammable=place.flammable))

    setup(world, maid, feller, setting)
    world.para()
    need_light(world, maid, setting)
    tempt(world, hazard, place)
    warn(world, maid, feller, hazard, place)
    world.para()
    world.say(
        f"For a moment, nobody moved. That tiny pause was the scariest part of all."
    )
    spread_ember(world, place_ent, hazard, place)
    alarm(world, maid, feller, place)
    contained = is_contained(response, place, delay)
    world.para()
    if contained:
        rescue(world, feller, response, place_ent, place)
    else:
        rescue_fail(world, feller, response, place_ent, place)
    ending(world, maid, feller, setting, response, place, contained)
    world.facts.update(
        maid=maid, feller=feller, room=room, ember=ember_ent, place=place_ent,
        hazard=hazard, setting=setting, response=response, delay=delay,
        contained=contained, outcome="contained" if contained else "loomed",
    )
    return world


SETTINGS = {
    "bedroom": Setting(
        id="bedroom",
        room="a small bedroom",
        quiet="The moon made a pale square on the rug.",
        dark_spot="the corner by the toy chest",
        glow_spot="the little lamp on the shelf",
        ending_image="the moon square on the rug",
        tags={"bedtime", "bedroom"},
    ),
    "hall": Setting(
        id="hall",
        room="the narrow hall",
        quiet="The clock had almost fallen asleep itself.",
        dark_spot="the shadow under the stair",
        glow_spot="the lamp by the stairs",
        ending_image="the lamp by the stairs",
        tags={"bedtime", "hall"},
    ),
}

HAZARDS = {
    "ember": Hazard(
        id="ember",
        label="ember",
        phrase="the ash beside the hearth",
        makes_ember=True,
        tags={"ember"},
    ),
    "spark": Hazard(
        id="spark",
        label="spark",
        phrase="the curled wick",
        makes_ember=True,
        tags={"spark"},
    ),
}

PLACES = {
    "cloth": EmberPlace(
        id="cloth",
        label="curtain",
        phrase="the curtain",
        flammable=True,
        tags={"cloth"},
    ),
    "paper": EmberPlace(
        id="paper",
        label="paper stack",
        phrase="the paper stack",
        flammable=True,
        tags={"paper"},
    ),
    "tile": EmberPlace(
        id="tile",
        label="tile hearth",
        phrase="the cool tile hearth",
        flammable=False,
        tags={"tile"},
    ),
}

RESPONSES = {
    "smother": Response(
        id="smother",
        sense=3,
        power=3,
        text="smothered it with a heavy wool cloth until the glow was gone",
        fail="tried to smother it, but the ember hid under the cloth and kept glowing",
        tags={"smother"},
    ),
    "jar": Response(
        id="jar",
        sense=3,
        power=4,
        text="covered it with a glass jar so it could not sip any more air",
        fail="set a jar over it, but the glow was too lively and slipped out at the edge",
        tags={"jar"},
    ),
    "call_help": Response(
        id="call_help",
        sense=2,
        power=2,
        text="called for help and used a damp cloth with careful hands",
        fail="called for help, but the little glow had already grown teeth",
        tags={"help"},
    ),
    "water_cup": Response(
        id="water_cup",
        sense=1,
        power=1,
        text="poured a little water cup over it",
        fail="poured a little water cup over it, but the ember was too stubborn",
        tags={"water"},
    ),
}

SENSE_MIN = 2

MAID_NAMES = ["Mina", "Clara", "June", "Elsie", "Nora"]
FELLER_NAMES = ["Fenn", "Bram", "Otis", "Joss", "Alden"]

@dataclass
class StoryParams:
    setting: str
    hazard: str
    place: str
    response: str
    maid_name: str = "Mina"
    feller_name: str = "Fenn"
    delay: int = 0
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
    StoryParams(setting="bedroom", hazard="ember", place="cloth", response="smother", maid_name="Mina", feller_name="Fenn", delay=0),
    StoryParams(setting="hall", hazard="spark", place="paper", response="jar", maid_name="Clara", feller_name="Bram", delay=0),
    StoryParams(setting="bedroom", hazard="ember", place="paper", response="call_help", maid_name="June", feller_name="Otis", delay=1),
]


KNOWLEDGE = {
    "maid": [("What is a maid?",
              "A maid is a person who helps keep a home tidy, clean, and ready for daily life.")],
    "feller": [("What is a feller?",
                "A feller is a person who cuts down trees or wood. In a story, a feller can be a careful helper with strong hands.")],
    "ember": [("What is an ember?",
               "An ember is a small, glowing bit left after a fire. It can stay hot and can start a bigger fire if it reaches something dry.")],
    "bedtime": [("Why are bedtime stories calm?",
                  "Bedtime stories are calm because they help children settle down, breathe slowly, and feel safe before sleep.")],
    "smother": [("How can smothering help with a small ember?",
                 "Smothering takes away the air an ember needs. Without air, the glow fades and the little danger goes out.")],
    "jar": [("Why can a glass jar help with an ember?",
              "A glass jar can cover a small ember and block air. That can help stop the glow from spreading.")],
    "help": [("What should you do if a fire starts?",
              "You should get away and call a grown-up or emergency helpers right away. Fast help is the safest choice.")],
    "tile": [("Can tile burn?",
              "No. Tile does not burn, so it is safer near heat than cloth or paper.")],
    "cloth": [("Why is cloth risky near fire?",
               "Dry cloth can catch fire easily, and once it starts burning it can spread fast.")],
    "paper": [("Why is paper risky near fire?",
               "Paper is thin and dry, so it can light quickly and let a small flame grow.")],
}
KNOWLEDGE_ORDER = ["maid", "feller", "ember", "bedtime", "smother", "jar", "help", "tile", "cloth", "paper"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime-suspense storyworld about a maid, an ember, and a feller.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--maid-name", choices=MAID_NAMES)
    ap.add_argument("--feller-name", choices=FELLER_NAMES)
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


def explain_rejection(hazard: Hazard, place: EmberPlace) -> str:
    if not hazard_at_risk(hazard, place):
        return f"(No story: {place.label} will not catch an ember, so the suspense would have no real risk.)"
    return "(No story: this combination is not reasonable.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    good = ", ".join(sorted(x.id for x in sensible_responses()))
    return f"(Refusing response '{rid}': sense={r.sense} is too low. Try one of: {good}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.hazard is None or c[0] == args.hazard)
              and (args.place is None or c[1] == args.place)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    hazard, place = rng.choice(sorted(combos))
    setting = args.setting or rng.choice(sorted(SETTINGS))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    maid_name = args.maid_name or rng.choice(MAID_NAMES)
    feller_name = args.feller_name or rng.choice([n for n in FELLER_NAMES if n != maid_name])
    return StoryParams(setting=setting, hazard=hazard, place=place, response=response, maid_name=maid_name, feller_name=feller_name, delay=rng.randint(0, 1))


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.hazard not in HAZARDS or params.place not in PLACES or params.response not in RESPONSES:
        raise StoryError("Invalid params.")
    world = tell(SETTINGS[params.setting], HAZARDS[params.hazard], PLACES[params.place], RESPONSES[params.response], params.maid_name, params.feller_name, params.delay)
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
        f'Write a bedtime-suspense story that includes the words "{f["maid"].role}", "{f["hazard"].label}", and "{f["feller"].role}".',
        f"Tell a calm story where {f['maid'].id} notices a small {f['hazard'].label} near {f['place'].label} and {f['feller'].id} helps before it becomes a bigger worry.",
        f"Write a sleepy, child-friendly suspense story about a {f['maid'].role} and a {f['feller'].role} who keep the room safe from a tiny ember.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    maid, feller, hazard, place, resp = f["maid"], f["feller"], f["hazard"], f["place"], f["response"]
    ans = []
    ans.append(("Who is the story about?", f"It is about {maid.id} the maid and {feller.id} the feller. They are the ones who notice the danger and keep the room safe."))
    ans.append(("What made the room feel suspenseful?", f"A tiny {hazard.label} near {place.label} made the room feel suspenseful. It was small, but it could have grown into something bigger if nobody acted."))
    if f["contained"]:
        ans.append((f"How did {feller.id} stop the ember?", f"{feller.id} {resp.text.replace('{place}', place.label)}. That covered the danger quickly, so the ember went out before it could spread."))
        ans.append(("How did the story end?", f"It ended quietly and safely. The room settled down, and the ending image showed {world.facts['setting'].ending_image}, which means the night was calm again."))
    else:
        ans.append((f"How did {feller.id} try to help?", f"{feller.id} {resp.fail.replace('{place}', place.label)}. The ember was too stubborn, so they had to call for more help and move away safely."))
        ans.append(("How did the story end?", "It ended with everyone safe, but with more worry than before. The little room needed careful help in the morning."))
    return ans


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {world.facts["hazard"].id, world.facts["place"].id, "bedtime"}
    tags |= set(world.facts["response"].tags)
    out = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({x[0] for x in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(F,P) :- makes_ember(F), flammable(P).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(H,P) :- hazard(H,P).
outcome(contained) :- chosen_response(R), chosen_place(P), power(R,Po), delay(D), needed(P,N), Po >= N + D.
outcome(loomed) :- chosen_response(R), chosen_place(P), power(R,Po), delay(D), needed(P,N), Po < N + D.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        if h.makes_ember:
            lines.append(asp.fact("makes_ember", hid))
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.flammable:
            lines.append(asp.fact("flammable", pid))
        lines.append(asp.fact("needed", pid, 1 if p.flammable else 0))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_response", params.response),
        asp.fact("chosen_place", params.place),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos.")
    if set(asp_sensible()) != {r.id for r in sensible_responses()}:
        rc = 1
        print("MISMATCH in sensible responses.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    for p in CURATED:
        if asp_outcome(p) != ("contained" if is_contained(RESPONSES[p.response], PLACES[p.place], p.delay) else "loomed"):
            rc = 1
            print("MISMATCH in outcome for", p)
            break
    if rc == 0:
        print("OK: ASP parity and smoke test passed.")
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
        print(asp_program("", "#show valid/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("sensible responses:", ", ".join(asp_sensible()))
        print()
        for h, p in asp_valid_combos():
            print(h, p)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def tell_for_world(params: StoryParams) -> StorySample:
    return generate(params)


if __name__ == "__main__":
    main()
