#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/galley_quest_folk_tale.py
==========================================================

A small folk-tale storyworld about a quest begun in a galley.

Premise:
- A child, a helper, and a wise captain prepare a tiny quest aboard a galley.
- The quest needs a missing thing to make the voyage possible.
- The child wants to hurry and do the wrong thing.
- The helper predicts the trouble, warns, and offers a better path.
- The ending proves the quest changed the world: the galley sails, the crew
  gains what they needed, and the child learns a kinder, wiser way.

The world is intentionally compact: one domain, a few constraint-checked
variants, and state-driven prose with meters and memes.
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
        female = {"girl", "mother", "mom", "woman", "queen"}
        male = {"boy", "father", "dad", "man", "king"}
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
class Ship:
    id: str
    place: str
    hold: str
    wind_word: str
    quest_word: str
    safe_way: str
    danger_word: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class MissingThing:
    id: str
    label: str
    phrase: str
    where: str
    use: str
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
class Trouble:
    id: str
    label: str
    phrase: str
    risky: bool
    makes_alarm: bool
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
class HelperTool:
    id: str
    label: str
    phrase: str
    purpose: str
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
    trouble: str
    missing: str
    helper: str
    response: str
    child: str
    child_gender: str
    helper_name: str
    helper_gender: str
    captain_name: str
    captain_gender: str
    seed: Optional[int] = None
    delay: int = 0
    child_age: int = 6
    helper_age: int = 8
    relation: str = "friends"
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
        self.ship: Optional[Ship] = None
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
        c.ship = copy.deepcopy(self.ship)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
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


def _r_hunger(world: World) -> list[str]:
    out: list[str] = []
    if not world.ship:
        return out
    if world.ship.meters["need"] < THRESHOLD:
        return out
    sig = ("need", world.ship.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in list(world.entities.values()):
        if e.kind == "character":
            e.memes["worry"] += 1
    out.append("__need__")
    return out


def _r_sail(world: World) -> list[str]:
    out: list[str] = []
    if not world.ship:
        return out
    if world.ship.meters["ready"] < THRESHOLD:
        return out
    sig = ("sail", world.ship.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.ship.meters["moving"] += 1
    out.append("__sail__")
    return out


CAUSAL_RULES = [Rule("need", _r_hunger), Rule("sail", _r_sail)]


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


def quest_at_risk(trouble: Trouble, missing: MissingThing) -> bool:
    return trouble.risky and missing.id in {"map", "key", "lantern"}


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def quest_severity(missing: MissingThing, delay: int) -> int:
    return 2 + delay if missing.id == "lantern" else 1 + delay


def is_resolved(response: Response, missing: MissingThing, delay: int) -> bool:
    return response.power >= quest_severity(missing, delay)


def predict(world: World, trouble_id: str) -> dict:
    sim = world.copy()
    _trigger(sim, sim.get(trouble_id), narrate=False)
    return {
        "alarm": sim.get("ship").meters["need"] >= THRESHOLD,
        "moving": sim.get("ship").meters["moving"] >= THRESHOLD,
    }


def _trigger(world: World, trouble_ent: Entity, narrate: bool = True) -> None:
    trouble_ent.meters["trouble"] += 1
    if world.ship:
        world.ship.meters["need"] += 1
    propagate(world, narrate=narrate)


def set_scene(world: World, child: Entity, helper: Entity, captain: Entity, ship: Ship) -> None:
    child.memes["hope"] += 1
    helper.memes["care"] += 1
    captain.memes["calm"] += 1
    world.ship = ship
    world.say(
        f"On a bright morning, {child.id} and {helper.id} stood in the galley, "
        f"where the old ship rocked like a cradle. {ship.hold}."
    )
    world.say(
        f'"{ship.quest_word}!" said {captain.id}, the captain. '
        f'"We must find the {ship.safe_way} before the tide turns."'
    )


def need_missing(world: World, missing: MissingThing) -> None:
    world.say(
        f"But the quest could not begin yet, because the galley had no {missing.label}. "
        f"The crew would need it to {missing.use}."
    )


def tempt(world: World, child: Entity, trouble: Trouble) -> None:
    child.memes["bold"] += 1
    world.say(
        f"{child.id}'s eyes shone. \"I know! Let's use {trouble.phrase}!\""
    )
    world.say("For one little breath, the bad idea looked easy.")


def warn(world: World, helper: Entity, child: Entity, trouble: Trouble, missing: MissingThing) -> None:
    pred = predict(world, "trouble")
    helper.memes["care"] += 1
    world.facts["pred"] = pred
    world.say(
        f"{helper.id} frowned. \"No, {child.id}. {trouble.label.capitalize()} is not for a quest. "
        f"It could bring alarm, and without a proper {missing.label}, the crew would be stuck.\""
    )


def refuse(world: World, child: Entity, helper: Entity) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"{child.id} wanted to rush ahead, but {helper.id} held up a hand and shook "
        f"{helper.pronoun('possessive')} head."
    )


def defy(world: World, child: Entity, trouble: Trouble) -> None:
    world.say(f"\"I can do it myself!\" {child.id} cried, and reached for {trouble.phrase}.")


def mishap(world: World, trouble: Trouble) -> None:
    _trigger(world, world.get("trouble"))
    world.say(
        f"Then {trouble.label} made a sudden alarm, loud enough to wake the gulls outside."
    )


def rescue(world: World, captain: Entity, response: Response, missing: MissingThing) -> None:
    body = response.text.replace("{missing}", missing.label)
    world.get("trouble").meters["trouble"] = 0.0
    if world.ship:
        world.ship.meters["need"] = 0.0
    world.say(
        f"{captain.id} came at once and {body}."
    )
    world.say(
        f"The galley grew quiet again, and the quest could breathe."
    )


def lesson(world: World, captain: Entity, child: Entity, helper: Entity, trouble: Trouble) -> None:
    for e in (child, helper):
        e.memes["relief"] += 1
        e.memes["lesson"] += 1
    world.say("For a moment, nobody spoke.")
    world.say(
        f"Then {captain.id} smiled and said, \"A wise quest is a safe quest. "
        f"{trouble.label.capitalize()} may look small, but trouble grows faster than feet can run.\""
    )
    world.say(f"{child.id} nodded, and {helper.id} nodded too.")


def end_good(world: World, child: Entity, helper: Entity, missing: MissingThing, tool: HelperTool) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    if world.ship:
        world.ship.meters["ready"] += 1
        world.ship.meters["moving"] += 1
    world.say(
        f"The next day, {helper.id} brought {tool.phrase}, and it did the very thing the quest needed."
    )
    world.say(
        f"{child.id} held the {tool.label} high, and the galley set off at last, with the {missing.label} safe aboard."
    )
    world.say("The sails filled, the oars dipped, and the little ship slipped toward the old story's promised shore.")


def end_bad(world: World, child: Entity, helper: Entity, missing: MissingThing, trouble: Trouble) -> None:
    child.memes["fear"] += 1
    helper.memes["fear"] += 1
    world.say(
        f"The wrong choice made the {trouble.label} spread its alarm, and the quest had to stop."
    )
    world.say(
        f"Still, {helper.id} gathered {child.id} close and said they would try again with a better plan."
    )
    world.say("The galley drifted home under a gray sky, carrying everyone safely back.")


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender, role="helper"))
    captain = world.add(Entity(id=params.captain_name, kind="character", type=params.captain_gender, role="captain"))
    ship = Ship(
        id="ship",
        place=params.place,
        hold="The lantern nook was empty, and the map case lay bare on the bench",
        wind_word="wind",
        quest_word="Quest!",
        safe_way="missing charm",
        danger_word="trouble",
    )
    world.add(Entity(id="trouble", kind="thing", type="trouble", label=TROUBLES[params.trouble].label))
    world.add(Entity(id="missing", kind="thing", type="missing", label=MISSING[params.missing].label))
    world.add(Entity(id="helpertool", kind="thing", type="tool", label=HELPER_TOOLS[params.helper].label))
    set_scene(world, child, helper, captain, ship)
    need_missing(world, MISSING[params.missing])
    world.para()
    tempt(world, child, TROUBLES[params.trouble])
    warn(world, helper, child, TROUBLES[params.trouble], MISSING[params.missing])
    world.para()
    refuse(world, child, helper)
    if quest_at_risk(TROUBLES[params.trouble], MISSING[params.missing]):
        defy(world, child, TROUBLES[params.trouble])
        mishap(world, TROUBLES[params.trouble])
        if is_resolved(RESPONSES[params.response], MISSING[params.missing], params.delay):
            rescue(world, captain, RESPONSES[params.response], MISSING[params.missing])
            lesson(world, captain, child, helper, TROUBLES[params.trouble])
            world.para()
            end_good(world, child, helper, MISSING[params.missing], HELPER_TOOLS[params.helper])
            outcome = "resolved"
        else:
            end_bad(world, child, helper, MISSING[params.missing], TROUBLES[params.trouble])
            outcome = "lost"
    else:
        world.say(
            f"{helper.id} smiled, because this was no true trouble after all, only a small test of patience."
        )
        world.para()
        end_good(world, child, helper, MISSING[params.missing], HELPER_TOOLS[params.helper])
        outcome = "averted"
    world.facts.update(
        child=child, helper=helper, captain=captain, ship=ship,
        missing=MISSING[params.missing], trouble=TROUBLES[params.trouble],
        tool=HELPER_TOOLS[params.helper], response=RESPONSES[params.response],
        outcome=outcome, delay=params.delay, params=params
    )
    return world


THEMES = {
    "harbor": Ship(id="ship", place="the harbor", hold="The lantern nook was empty, and the map case lay bare on the bench",
                   wind_word="wind", quest_word="Quest!", safe_way="missing charm", danger_word="trouble")
}

MISSING = {
    "map": MissingThing(id="map", label="map", phrase="an old map", where="on the bench", use="find the harbor path", tags={"map"}),
    "key": MissingThing(id="key", label="key", phrase="a little brass key", where="in the chest", use="open the sea chest", tags={"key"}),
    "lantern": MissingThing(id="lantern", label="lantern", phrase="a lantern", where="by the mast", use="light the way home", tags={"lantern"}),
}

TROUBLES = {
    "greedy_cake": Trouble(id="greedy_cake", label="greedy cake", phrase="the greedy cake", risky=True, makes_alarm=True, tags={"food"}),
    "cold_chain": Trouble(id="cold_chain", label="cold chain", phrase="the cold chain", risky=True, makes_alarm=True, tags={"metal"}),
    "dusty_bell": Trouble(id="dusty_bell", label="dusty bell", phrase="the dusty bell", risky=False, makes_alarm=False, tags={"bell"}),
}

HELPER_TOOLS = {
    "rope": HelperTool(id="rope", label="rope", phrase="a coil of rope", purpose="tie the rigging", tags={"rope"}),
    "blanket": HelperTool(id="blanket", label="blanket", phrase="a wool blanket", purpose="cover the deck", tags={"blanket"}),
    "lantern": HelperTool(id="lantern", label="lantern", phrase="a warm lantern", purpose="show the way", tags={"lantern"}),
}

RESPONSES = {
    "rope": Response(id="rope", sense=3, power=2,
                     text="tied the loose bundle down with a strong rope and steadied the deck",
                     fail="tried to tie it down, but the trouble kept wriggling free",
                     qa_text="tied the trouble down with a rope",
                     tags={"rope"}),
    "blanket": Response(id="blanket", sense=3, power=3,
                        text="covered the alarm with a thick blanket until the noise went dull",
                        fail="covered it with a blanket, but the alarm still rang too hard",
                        qa_text="smothered the alarm under a blanket",
                        tags={"blanket"}),
    "lantern": Response(id="lantern", sense=2, power=4,
                        text="lifted a lantern and led everyone toward the safe way home",
                        fail="held up a lantern, but the path stayed too dark and confused",
                        qa_text="lit the way with a lantern",
                        tags={"lantern"}),
    "bucket": Response(id="bucket", sense=1, power=1,
                       text="splashed a bucket of water where it did not help much",
                       fail="splashed a bucket of water, but the trouble only grew worse",
                       qa_text="splashed water uselessly",
                       tags={"bucket"}),
}

NAMES_GIRL = ["Mara", "Lina", "Tess", "Nora", "Elsie"]
NAMES_BOY = ["Finn", "Owen", "Pip", "Rowan", "Bram"]
TRAITS = ["curious", "patient", "brave", "gentle", "clever", "hopeful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for t in TROUBLES.values():
        for m in MISSING.values():
            if quest_at_risk(t, m):
                for h in HELPER_TOOLS.values():
                    if m.id in h.tags or h.id == "lantern" or m.id in {"map", "key"}:
                        combos.append(("harbor", t.id, m.id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny folk-tale quest aboard a galley.")
    ap.add_argument("--place", choices=["harbor"])
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--missing", choices=MISSING)
    ap.add_argument("--helper", choices=HELPER_TOOLS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--captain")
    ap.add_argument("--captain-gender", choices=["woman", "man"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.trouble and args.missing and not quest_at_risk(TROUBLES[args.trouble], MISSING[args.missing]):
        raise StoryError("That trouble and missing thing do not belong in the same quest.")
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError("That response is too weak for this quest story.")

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.trouble is None or c[1] == args.trouble)
              and (args.missing is None or c[2] == args.missing)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    _, trouble, missing = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPER_TOOLS))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = NAMES_GIRL if gender == "girl" else NAMES_BOY
    name = args.name or rng.choice(name_pool)
    captain_gender = args.captain_gender or rng.choice(["woman", "man"])
    captain = args.captain or ("Captain Brine" if captain_gender == "man" else "Captain Mare")
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        place="harbor", trouble=trouble, missing=missing, helper=helper, response=response,
        child=name, child_gender=gender, helper_name=rng.choice(["Willow", "Tomas", "June", "Hugh"]),
        helper_gender=rng.choice(["girl", "boy"]), captain_name=captain, captain_gender=captain_gender,
        delay=delay, child_age=rng.randint(5, 8), helper_age=rng.randint(7, 10),
        relation="friends",
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale quest story about a galley where {f["child"].id} and {f["helper"].id} need a missing {f["missing"].label}.',
        f"Tell a gentle quest story in a galley where {f['child'].id} wants to use {f['trouble'].phrase}, but a helper warns them and the crew finds a safer answer.",
        f'Write a child-friendly quest tale that includes the word "galley" and ends with the ship ready to sail.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, captain, missing, trouble, response = f["child"], f["helper"], f["captain"], f["missing"], f["trouble"], f["response"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, {helper.id}, and {captain.id} aboard the galley. They are the small crew at the center of the quest."),
        ("What did the crew need?",
         f"They needed {missing.phrase}. The quest could not truly begin until that was found."),
        ("What did {0} want to use?".format(child.id),
         f"{child.id} wanted to use {trouble.phrase}, but {helper.id} said it was the wrong choice for a quest."),
    ]
    if f["outcome"] == "resolved":
        qa.append((
            "How did they fix the trouble?",
            f"{captain.id} came running and {response.qa_text}. That turned the story back toward the quest and kept the galley safe."
        ))
        qa.append((
            "How did the story end?",
            f"The crew set off with the missing thing safe aboard, and the galley sailed at last. The ending image proves the quest changed the world: they were ready to go."
        ))
    elif f["outcome"] == "lost":
        qa.append((
            "Why did the quest stop?",
            f"The wrong choice made the trouble worse, so the crew had to stop. They stayed safe, but they needed a better plan before trying again."
        ))
    else:
        qa.append((
            "Why did the helper smile at the warning?",
            f"Because this trouble was only a small test, not a real danger. The crew could keep the quest gentle and still reach the good ending."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["missing"].tags) | set(world.facts["trouble"].tags) | set(world.facts["response"].tags)
    out = []
    if "lantern" in tags:
        out.append(("What is a lantern?", "A lantern is a light that helps people see in the dark. In a quest, it can guide the way safely."))
    out.append(("What is a galley?", "A galley is a long ship with oars and sails. People use it for traveling over water."))
    out.append(("What is a quest?", "A quest is a journey to find something important or solve a problem. In folk tales, quests often teach courage and wisdom."))
    return out


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
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes} role={e.role}")
    if world.ship:
        lines.append(f"  ship       (ship    ) meters={dict(world.ship.meters)} memes={dict(world.ship.memes)}")
    lines.append(f"  fired rules: {sorted(set(x for x, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
quest_at_risk(T, M) :- trouble(T), missing(M), risky_trouble(T), risky_missing(M).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
resolved(M, R, D) :- severity(M, D, V), power(R, P), P >= V.
outcome(resolved) :- chosen_trouble(T), chosen_missing(M), chosen_response(R), delay(D), quest_at_risk(T, M), resolved(M, R, D).
outcome(lost) :- chosen_trouble(T), chosen_missing(M), chosen_response(R), delay(D), quest_at_risk(T, M), not resolved(M, R, D).
outcome(averted) :- chosen_trouble(T), chosen_missing(M), not quest_at_risk(T, M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for t in TROUBLES.values():
        lines.append(asp.fact("trouble", t.id))
        if t.risky:
            lines.append(asp.fact("risky_trouble", t.id))
    for m in MISSING.values():
        lines.append(asp.fact("missing", m.id))
        if m.id in {"map", "key", "lantern"}:
            lines.append(asp.fact("risky_missing", m.id))
    for r in RESPONSES.values():
        lines.append(asp.fact("response", r.id))
        lines.append(asp.fact("sense", r.id, r.sense))
        lines.append(asp.fact("power", r.id, r.power))
    lines.append(asp.fact("sense_min", 2))
    for d in [0, 1, 2]:
        lines.append(asp.fact("delay", d))
        for m in MISSING.values():
            lines.append(asp.fact("severity", m.id, d, quest_severity(m, d)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show quest_at_risk/2."))
    return sorted(set(asp.atoms(model, "quest_at_risk")))


def asp_verify() -> int:
    import asp
    ok = True
    if set(asp_valid_combos()) != set((t, m) for _, t, m in valid_combos()):
        ok = False
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        _ = sample.story
    except Exception as e:
        print(f"FAIL: smoke test crashed: {e}")
        return 1
    if ok:
        print("OK: ASP parity and smoke test passed.")
        return 0
    print("FAIL: ASP parity mismatch.")
    return 1


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it scores too low on common sense, with sense={r.sense}.)"


def explain_invalid(missing: MissingThing, trouble: Trouble) -> str:
    return f"(No story: {trouble.label} does not make sense for a quest about a missing {missing.label}.)"


CURATED = [
    StoryParams(place="harbor", trouble="greedy_cake", missing="map", helper="rope", response="rope",
                child="Mara", child_gender="girl", helper_name="Willow", helper_gender="girl",
                captain_name="Captain Mare", captain_gender="woman", delay=0),
    StoryParams(place="harbor", trouble="cold_chain", missing="key", helper="blanket", response="blanket",
                child="Finn", child_gender="boy", helper_name="Tomas", helper_gender="boy",
                captain_name="Captain Brine", captain_gender="man", delay=1),
    StoryParams(place="harbor", trouble="greedy_cake", missing="lantern", helper="lantern", response="lantern",
                child="Lina", child_gender="girl", helper_name="June", helper_gender="girl",
                captain_name="Captain Mare", captain_gender="woman", delay=2),
]


def generate(params: StoryParams) -> StorySample:
    if params.response not in RESPONSES or params.missing not in MISSING or params.trouble not in TROUBLES:
        raise StoryError("(Invalid params.)")
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
        print(asp_program("", "#show quest_at_risk/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible quest combos.")
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.child} and the galley quest ({p.trouble}, {p.missing})"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
