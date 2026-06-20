#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/coming_basis_suspense_inner_monologue_bravery_space.py
=======================================================================================

A small standalone storyworld about a space adventure with suspense, inner
monologue, and bravery.

Core premise:
- A child astronaut hears a strange signal that is coming from somewhere dark.
- The child must decide what the signal is based on scant clues, while fear
  grows in the silence.
- Bravery turns the guess into action, and the ending proves what changed.

This world is built to satisfy the Storyweavers storyworld contract:
- typed entities with physical meters and emotional memes
- state-driven prose
- generation prompts, story Q&A, and world knowledge Q&A
- Python reasonableness gate plus inline ASP twin
- --verify exercises both parity and normal story generation
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Ship:
    id: str
    label: str
    kind: str
    dark_zone: str
    basis: str
    suspense: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Beacon:
    id: str
    label: str
    phrase: str
    where: str
    signal_kind: str
    alarming: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["fear"] < THRESHOLD:
            continue
        sig = ("suspense", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("ship").meters["tension"] += 1
        out.append("__suspense__")
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["bravery"] < THRESHOLD:
            continue
        sig = ("bravery", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("ship").meters["hope"] += 1
        out.append("__hope__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("suspense", "social", _r_suspense),
    Rule("bravery", "social", _r_bravery),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def suspicion_at_risk(beacon: Beacon) -> bool:
    return beacon.alarming


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def fire_alert(response: Response, beacon: Beacon) -> bool:
    return response.power >= (2 if beacon.alarming else 1)


def predict_signal(world: World, beacon_id: str) -> dict:
    sim = world.copy()
    _touch_beacon(sim, sim.get(beacon_id), narrate=False)
    return {
        "tension": sim.get("ship").meters["tension"],
        "signal_kind": sim.get(beacon_id).attrs.get("signal_kind", ""),
    }


def _touch_beacon(world: World, beacon: Entity, narrate: bool = True) -> None:
    beacon.meters["seen"] += 1
    beacon.memes["mystery"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity, ship: Ship) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} floated through the corridor of {ship.label}, where the "
        f"{ship.basis} was steady and the stars were far away."
    )
    world.say(
        f"The mission was simple on paper, but {ship.suspense} made the dark "
        f"side of the ship feel wider than it was."
    )


def incoming(world: World, beacon: Beacon, hero: Entity) -> None:
    world.say(
        f"Then a tiny signal was coming from {beacon.where}. It blinked once, "
        f"then paused, as if it were waiting to be found."
    )
    hero.memes["fear"] += 1
    hero.memes["curiosity"] += 1
    world.say(
        f'In {hero.id}\'s head, a small inner voice whispered, "What if it is '
        f'broken? What if it is important?"'
    )


def guess(world: World, hero: Entity, beacon: Beacon) -> None:
    hero.memes["guessing"] += 1
    world.say(
        f"{hero.id} looked at the blinking light and tried to guess its basis. "
        f'"Maybe it is only a loose cable," {hero.pronoun()} thought. '
        f'"Maybe it is the rescue beacon coming back from the storm."'
    )


def warn(world: World, companion: Entity, hero: Entity, beacon: Beacon) -> None:
    pred = predict_signal(world, "beacon")
    companion.memes["concern"] += 1
    world.facts["predicted_tension"] = pred["tension"]
    world.say(
        f"{companion.id} swallowed hard. " 
        f'"We should not rush," {companion.pronoun()} said. "If that light is '
        f"alarming, we need to be careful."
    )


def brave_step(world: World, hero: Entity, beacon: Beacon) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f"{hero.id} took one brave breath and opened the panel anyway."
    )
    _touch_beacon(world, world.get("beacon"))


def reveal(world: World, hero: Entity, beacon: Beacon) -> None:
    world.say(
        f"The light was not a warning after all. It was a small map beacon, "
        f"showing the way to the next dock."
    )
    world.say(
        f"Inside the blinking shell, {hero.id} found a message: 'You are close.'"
    )


def calm_finish(world: World, hero: Entity, companion: Entity, beacon: Beacon) -> None:
    hero.memes["relief"] += 1
    companion.memes["relief"] += 1
    world.say(
        f"{hero.id} smiled so wide the helmet felt too small. "
        f"{companion.id} laughed, and the tense hush on the ship melted away."
    )
    world.say(
        f"Together they set the beacon on the console, and the stars outside "
        f"looked less lonely than before."
    )


def rescue_fail(world: World, hero: Entity, beacon: Beacon) -> None:
    world.say(
        f"The signal was louder than it looked, and the panel sparked. "
        f"{hero.id} jolted back, and the ship filled with a sharp warning beep."
    )


def tell(ship: Ship, beacon: Beacon, response: Response, hero_name: str,
         hero_gender: str, companion_name: str, companion_gender: str,
         companion_trait: str, captain_name: str = "Captain Mira") -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_gender, role="hero",
        traits=["small", "curious"], attrs={"role": "cadet"},
    ))
    companion = world.add(Entity(
        id=companion_name, kind="character", type=companion_gender, role="companion",
        traits=[companion_trait], attrs={"role": "navigator"},
    ))
    captain = world.add(Entity(
        id=captain_name, kind="character", type="woman", role="captain",
        label="the captain",
    ))
    world.add(Entity(id="ship", kind="thing", type="ship", label=ship.label))
    b = world.add(Entity(
        id="beacon", kind="thing", type="beacon", label=beacon.label,
        attrs={"signal_kind": beacon.signal_kind},
    ))

    hero.memes["bravery"] = 0.0
    companion.memes["trust"] = 1.0
    captain.memes["calm"] = 1.0

    intro(world, hero, ship)
    world.para()
    incoming(world, beacon, hero)
    guess(world, hero, beacon)
    warn(world, companion, hero, beacon)

    if not suspicion_at_risk(beacon):
        world.say("The signal was harmless, and the mystery faded before anyone had to act.")
        outcome = "quiet"
    else:
        brave_step(world, hero, beacon)
        world.para()
        if fire_alert(response, beacon):
            reveal(world, hero, beacon)
            calm_finish(world, hero, companion, beacon)
            outcome = "revealed"
        else:
            rescue_fail(world, hero, beacon)
            world.say(
                f"The captain came at once and handled the little malfunction "
                f"without panic. The ship stayed safe, but the answer had arrived "
                f"in a rough way."
            )
            outcome = "rough"

    world.facts.update(
        hero=hero, companion=companion, captain=captain, ship=ship, beacon=beacon,
        response=response, outcome=outcome, signal_kind=beacon.signal_kind,
    )
    return world


SHIP_REGISTRY = {
    "starfreighter": Ship("starfreighter", "the Starfreighter", "ship",
                          "the long hush of deep space", "a steady course",
                          "a slow, suspenseful creak"),
    "orbital": Ship("orbital", "Orbital Dawn", "station",
                    "the dark curve of the station", "a bright orbit",
                    "a soft, suspenseful hum"),
}

BEACONS = {
    "map_beacon": Beacon("map_beacon", "a tiny map beacon", "a tiny map beacon",
                         "the far panel", "map", alarming=False),
    "rescue_beacon": Beacon("rescue_beacon", "a rescue beacon", "a rescue beacon",
                            "the maintenance hatch", "rescue", alarming=True),
    "pinger": Beacon("pinger", "a deck pinger", "a deck pinger",
                     "the storage wall", "pinger", alarming=True),
}

RESPONSES = {
    "wait": Response("wait", 3, 1, "waited and listened until the signal became clear",
                     "waited, but the beep turned sharp and confusing", "waited and listened"),
    "open_carefully": Response("open_carefully", 3, 2,
                               "opened the panel carefully and looked inside",
                               "opened the panel, but the latch jammed and the signal stuttered",
                               "opened the panel carefully"),
    "call_captain": Response("call_captain", 2, 3,
                             "called the captain and followed the steps she gave them",
                             "called the captain, but the warning came too late to help",
                             "called the captain and followed the steps"),
    "slam": Response("slam", 1, 1, "slammed the panel shut",
                     "slammed it shut, but that only made the beep louder",
                     "slammed the panel shut"),
}

HERO_NAMES = ["Luna", "Milo", "Nova", "Iris", "Kai", "Ari", "Tess", "Orion"]
COMPANION_NAMES = ["Rin", "Juno", "Pax", "Sora", "Bea", "Niko", "Remy", "Zed"]
TRAITS = ["careful", "bold", "thoughtful", "steady", "brave"]


@dataclass
@dataclass
class StoryParams:
    ship: str
    beacon: str
    response: str
    hero: str
    hero_gender: str
    companion: str
    companion_gender: str
    companion_trait: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid in SHIP_REGISTRY:
        for bid, beacon in BEACONS.items():
            if suspicion_at_risk(beacon):
                combos.append((sid, bid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space storyworld with suspense and bravery.")
    ap.add_argument("--ship", choices=SHIP_REGISTRY)
    ap.add_argument("--beacon", choices=BEACONS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["boy", "girl"])
    ap.add_argument("--companion")
    ap.add_argument("--companion-gender", choices=["boy", "girl"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("(Refusing response: too little common sense.)")
    combos = [c for c in valid_combos()
              if (args.ship is None or c[0] == args.ship)
              and (args.beacon is None or c[1] == args.beacon)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    ship, beacon = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero_gender = args.hero_gender or rng.choice(["boy", "girl"])
    companion_gender = args.companion_gender or ("girl" if hero_gender == "boy" else "boy")
    hero = args.hero or rng.choice(HERO_NAMES)
    companion = args.companion or rng.choice([n for n in COMPANION_NAMES if n != hero])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(ship, beacon, response, hero, hero_gender, companion, companion_gender, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space adventure story for a 3-to-5-year-old that includes the word "coming" and the word "basis".',
        f"Tell a suspenseful story where {f['hero'].id} hears a signal coming from the ship and must decide its basis.",
        f"Write a brave, child-friendly space story with inner monologue, a mystery light, and a calm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    comp = f["companion"]
    beacon = f["beacon"]
    ship = f["ship"]
    outcome = f["outcome"]
    items = [
        QAItem(
            question=f"What was coming from the dark panel?",
            answer=f"A small signal was coming from {beacon.where}. It blinked and paused like it wanted to be found."
        ),
        QAItem(
            question=f"What did {hero.id} think about the signal?",
            answer=f"{hero.id} wondered what its basis was. Inside {hero.pronoun('possessive')} head, {hero.pronoun()} worried that it might be broken and hoped it might be important."
        ),
        QAItem(
            question=f"Who helped {hero.id} stay brave?",
            answer=f"{comp.id} helped by warning {hero.pronoun('object')} to go slowly. That quiet support made it easier for {hero.id} to be brave."
        ),
    ]
    if outcome == "revealed":
        items.append(QAItem(
            question="How did the story end?",
            answer=f"The mystery turned out to be a safe map beacon, so the worry faded. {hero.id} and {comp.id} felt proud because they faced the unknown and found a helpful answer."
        ))
        items.append(QAItem(
            question=f"Why was the ending peaceful?",
            answer=f"Because the beacon was not dangerous, the ship never needed an emergency rescue. Once they opened it carefully, the tension turned into relief and the stars looked friendly again."
        ))
    elif outcome == "rough":
        items.append(QAItem(
            question="What happened when the panel was opened?",
            answer=f"The panel sparked and the ship gave a sharp warning beep. The adults handled it right away, so everyone stayed safe even though the moment was scary."
        ))
    else:
        items.append(QAItem(
            question="How did the ship feel by the end?",
            answer="The mystery stayed quiet, so the ship felt calm and still. The tension never grew into a bigger problem."
        ))
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a beacon in space?", "A beacon is a light or signal that helps people find their way. In a ship, it can point the crew toward an important place."),
        QAItem("What does bravery mean?", "Bravery means doing something scary while still trying your best. It does not mean you are never afraid."),
        QAItem("Why do people listen for signals in space?", "Signals can tell crews where to go or warn them about something important. That is why a tiny blink can matter so much."),
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
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("starfreighter", "map_beacon", "open_carefully", "Luna", "girl", "Milo", "boy", "careful"),
    StoryParams("orbital", "rescue_beacon", "call_captain", "Kai", "boy", "Nova", "girl", "bold"),
]


def tell_story(params: StoryParams) -> World:
    ship = SHIP_REGISTRY[params.ship]
    beacon = BEACONS[params.beacon]
    response = RESPONSES[params.response]
    return tell(ship, beacon, response, params.hero, params.hero_gender,
                params.companion, params.companion_gender, params.companion_trait)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SHIP_REGISTRY:
        lines.append(asp.fact("ship", sid))
    for bid, b in BEACONS.items():
        lines.append(asp.fact("beacon", bid))
        if b.alarming:
            lines.append(asp.fact("alarming", bid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
suspicion_at_risk(B) :- alarming(B).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(S,B) :- ship(S), beacon(B), suspicion_at_risk(B).
"""


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


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid_combos().")
        rc = 1
    if set(asp_sensible()) != {r.id for r in sensible_responses()}:
        print("MISMATCH in sensible responses.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld.")
    ap.add_argument("--ship", choices=SHIP_REGISTRY)
    ap.add_argument("--beacon", choices=BEACONS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["boy", "girl"])
    ap.add_argument("--companion")
    ap.add_argument("--companion-gender", choices=["boy", "girl"])
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("(Refusing response: too little common sense.)")
    combos = [c for c in valid_combos()
              if (args.ship is None or c[0] == args.ship)
              and (args.beacon is None or c[1] == args.beacon)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    ship, beacon = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero_gender = args.hero_gender or rng.choice(["boy", "girl"])
    companion_gender = args.companion_gender or ("girl" if hero_gender == "boy" else "boy")
    hero = args.hero or rng.choice(HERO_NAMES)
    companion = args.companion or rng.choice([n for n in COMPANION_NAMES if n != hero])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(ship, beacon, response, hero, hero_gender, companion, companion_gender, trait)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for ship, beacon in asp_valid_combos():
            print(f"  {ship:12} {beacon}")
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} & {p.companion}: {p.ship} / {p.beacon} ({p.response})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
