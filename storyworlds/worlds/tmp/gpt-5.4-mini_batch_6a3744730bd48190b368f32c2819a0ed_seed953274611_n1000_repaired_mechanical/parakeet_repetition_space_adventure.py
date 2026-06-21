#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/parakeet_repetition_space_adventure.py
=======================================================================

A tiny space-adventure storyworld about a parakeet, repetition, and a small
crew learning that a repeated signal can guide them home.

The world is built around a simple premise:
- a parakeet repeats a useful phrase,
- a child and a grown-up follow the repeated signal through a space mishap,
- the crew reaches a bright, safe ending image.

This script follows the Storyweavers contract:
- typed entities with physical meters and emotional memes
- state-driven prose
- a reasonableness gate plus inline ASP twin
- prompts, story-grounded QA, and world-knowledge QA
- support for --verify, --asp, --show-asp, --json, --qa, --trace, -n, --all
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
    repeats: list[str] = field(default_factory=list)
    alive: bool = True

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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Ship:
    id: str
    name: str
    cabin: str
    route: str
    safe_signal: str
    distress_signal: str
    beacon: str
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


@dataclass
class Signal:
    id: str
    phrase: str
    label: str
    source: str
    repeat: int
    power: int
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
class Hazard:
    id: str
    label: str
    feature: str
    risky: bool
    severity: int
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
    ship: str
    signal: str
    hazard: str
    response: str
    child_name: str
    child_gender: str
    grownup_name: str
    grownup_gender: str
    parakeet_name: str
    parakeet_color: str
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


def _r_echo(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["lost"] < THRESHOLD:
            continue
        sig = ("echo", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["fear"] += 1
        if "child" in world.entities:
            world.get("child").memes["fear"] += 1
        out.append("__echo__")
    return out


CAUSAL_RULES = [Rule("echo", "social", _r_echo)]


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


def valid_combo(ship: Ship, signal: Signal, hazard: Hazard, response: Response) -> bool:
    return ship.safe_signal == signal.label and hazard.risky and response.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, ship in SHIPS.items():
        for sig_id, sig in SIGNALS.items():
            for hid, hz in HAZARDS.items():
                for rid, resp in RESPONSES.items():
                    if valid_combo(ship, sig, hz, resp):
                        combos.append((sid, sig_id, hid))
    return combos


def reasonableness(ship: Ship, signal: Signal, hazard: Hazard) -> bool:
    return ship.safe_signal == signal.label and hazard.risky


def ship_speed(ship: Ship) -> int:
    return ship.speed


def predict_lost(world: World, hazard_id: str) -> bool:
    sim = world.copy()
    _trigger_hazard(sim, sim.get(hazard_id), narrate=False)
    return sim.get("ship").meters["lost"] >= THRESHOLD


def _trigger_hazard(world: World, hazard_ent: Entity, narrate: bool = True) -> None:
    hazard_ent.meters["lost"] += 1
    propagate(world, narrate=narrate)


def launch(world: World, child: Entity, grownup: Entity, ship: Ship, parakeet: Entity) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{child.id} and {grownup.id} rode {ship.name} into space. "
        f"The cabin was small, the stars were bright, and {parakeet.id} sat on the map board."
    )


def repeat(world: World, parakeet: Entity, signal: Signal) -> None:
    parakeet.repeats.extend([signal.phrase] * signal.repeat)
    world.say(
        f'{parakeet.id} tilted {parakeet.pronoun("possessive")} head and said, '
        f'"{signal.phrase}."'
    )
    world.say(f'"{signal.phrase}!" {parakeet.id} repeated again and again.')


def drift(world: World, ship: Ship, hazard: Hazard) -> None:
    world.say(
        f"Then the ship drifted toward {hazard.label}. {hazard.feature.capitalize()} glittered ahead."
    )


def warn(world: World, grownup: Entity, child: Entity, signal: Signal, hazard: Hazard) -> None:
    if predict_lost(world, hazard.id):
        world.say(
            f'{grownup.id} listened to the parakeet. "{signal.phrase}," {grownup.pronoun()} said, '
            f'and held tight to {child.id}.'
        )
    else:
        world.say(f"{grownup.id} smiled and listened closely to the repeated words.")


def wander(world: World, child: Entity, hazard: Entity) -> None:
    child.memes["curious"] += 1
    world.say(f"{child.id} leaned toward the window, but the repeated words kept {child.pronoun('object')} calm.")


def activate(world: World, hazard: Entity) -> None:
    _trigger_hazard(world, hazard)
    world.say(f"The ship bumped the {hazard.label}, and the lights flickered.")


def rescue(world: World, grownup: Entity, response: Response, hazard: Entity, ship: Ship) -> None:
    hazard.meters["lost"] = 0.0
    body = response.text.replace("{ship}", ship.name)
    world.say(f"{grownup.id} {body}.")
    world.say(f"The {ship.name} steadied at once, and the cabin stopped shaking.")


def lesson(world: World, grownup: Entity, child: Entity, parakeet: Entity, signal: Signal) -> None:
    child.memes["relief"] += 1
    child.memes["love"] += 1
    parakeet.memes["pride"] += 1
    world.say(
        f"Then {grownup.id} laughed softly and hugged {child.id}. "
        f'"That was a good signal," {grownup.pronoun()} said. '
        f'"When {signal.phrase} comes back again and again, we follow it."'
    )
    world.say(f"{parakeet.id} puffed up, bright and happy in the moonlight.")


def safe_finish(world: World, child: Entity, grownup: Entity, ship: Ship, parakeet: Entity) -> None:
    child.memes["joy"] += 1
    grownup.memes["joy"] += 1
    world.say(
        f"At last the {ship.name} floated into a calm blue harbor on the far side of the moon. "
        f"{parakeet.id} chirped the same brave words one more time, and the crew smiled."
    )
    world.say(f"Their tiny ship was safe, and the repeated words had guided them home.")


def tell(ship: Ship, signal: Signal, hazard: Hazard, response: Response,
         child_name: str = "Mina", child_gender: str = "girl",
         grownup_name: str = "Captain Ora", grownup_gender: str = "woman",
         parakeet_name: str = "Pip", parakeet_color: str = "green") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    grownup = world.add(Entity(id=grownup_name, kind="character", type=grownup_gender, role="grownup"))
    bird = world.add(Entity(id=parakeet_name, kind="character", type="bird", role="guide", attrs={"color": parakeet_color}))
    ship_ent = world.add(Entity(id="ship", kind="thing", type="ship", label=ship.name))
    hazard_ent = world.add(Entity(id=hazard.id, kind="thing", type="hazard", label=hazard.label))
    world.facts.update(ship=ship, signal=signal, hazard=hazard, response=response, child=child, grownup=grownup, parakeet=bird)

    launch(world, child, grownup, ship, bird)
    repeat(world, bird, signal)
    world.para()
    drift(world, ship, hazard)
    warn(world, grownup, child, signal, hazard)
    if reasonableness(ship, signal, hazard):
        world.say(f"{signal.phrase} sounded like a way back home.")
    world.para()
    activate(world, hazard_ent)
    rescue(world, grownup, response, hazard_ent, ship)
    lesson(world, grownup, child, bird, signal)
    world.para()
    safe_finish(world, child, grownup, ship, bird)
    world.facts["outcome"] = "contained"
    return world


SHIPS = {
    "moon_glider": Ship(id="moon_glider", name="the Moon Glider", cabin="small cabin", route="moon lane",
                        safe_signal="follow the bright chirp", distress_signal="lost signal", beacon="blue beacon",
                        speed=2, tags={"moon", "ship"}),
    "starlight_skiff": Ship(id="starlight_skiff", name="the Starlight Skiff", cabin="tiny cabin", route="star lane",
                            safe_signal="keep chirping", distress_signal="fading signal", beacon="silver beacon",
                            speed=2, tags={"stars", "ship"}),
    "comet_cart": Ship(id="comet_cart", name="the Comet Cart", cabin="round cabin", route="comet lane",
                       safe_signal="repeat the route", distress_signal="quiet signal", beacon="gold beacon",
                       speed=2, tags={"comet", "ship"}),
}

SIGNALS = {
    "follow_chirp": Signal(id="follow_chirp", phrase="follow the bright chirp", label="follow the bright chirp", source="parakeet", repeat=2, power=2, tags={"parakeet", "signal"}),
    "keep_chirping": Signal(id="keep_chirping", phrase="keep chirping", label="keep chirping", source="parakeet", repeat=2, power=2, tags={"parakeet", "signal"}),
    "repeat_route": Signal(id="repeat_route", phrase="repeat the route", label="repeat the route", source="parakeet", repeat=2, power=2, tags={"parakeet", "signal"}),
}

HAZARDS = {
    "meteor_glitter": Hazard(id="meteor_glitter", label="the meteor glitter", feature="a ribbon of meteors", risky=True, severity=2, tags={"meteor", "glitter"}),
    "dust_swirl": Hazard(id="dust_swirl", label="the dust swirl", feature="a cloud of silver dust", risky=True, severity=1, tags={"dust"}),
    "ring_shadow": Hazard(id="ring_shadow", label="the ring shadow", feature="a dark ring shadow", risky=True, severity=2, tags={"shadow"}),
}

RESPONSES = {
    "steady_throttle": Response(id="steady_throttle", sense=3, power=3, text="set a steady throttle and followed the repeated words until {ship} stopped wobbling", fail="tried to steer too fast and only made the wobble worse", qa_text="set a steady throttle and followed the repeated words", tags={"control"}),
    "blue_beacon": Response(id="blue_beacon", sense=3, power=3, text="switched on the blue beacon and guided {ship} by the blinking light", fail="switched on the blue beacon, but the light was too weak", qa_text="switched on the blue beacon and guided the ship by the blinking light", tags={"light"}),
    "slow_turn": Response(id="slow_turn", sense=2, power=2, text="made a slow careful turn and let the repeated signal lead {ship} forward", fail="turned too late and the ship kept drifting", qa_text="made a slow careful turn and let the repeated signal lead the ship forward", tags={"turn"}),
}

PARAKEET_COLORS = ["green", "yellow", "blue", "striped"]
CHILD_NAMES = ["Mina", "Tess", "Jun", "Pico", "Nia", "Lio"]
GROWNUP_NAMES = ["Captain Ora", "Aunt Sol", "Commander Vale", "Pilot Rina"]
TRAITS = ["curious", "careful", "bright", "patient"]


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, ship in SHIPS.items():
        lines.append(asp.fact("ship", sid))
        lines.append(asp.fact("safe_signal", sid, ship.safe_signal))
    for sig_id, sig in SIGNALS.items():
        lines.append(asp.fact("signal", sig_id))
        lines.append(asp.fact("label", sig_id, sig.label))
        lines.append(asp.fact("repeat", sig_id, sig.repeat))
    for hid, hz in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        if hz.risky:
            lines.append(asp.fact("risky", hid))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, resp.sense))
        lines.append(asp.fact("power", rid, resp.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, G, H) :- ship(S), signal(G), hazard(H), safe_signal(S, L), label(G, L), risky(H).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
outcome(ok) :- valid(_, _, _), sensible(_).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid combo gate.")
        rc = 1
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible responses match.")
    else:
        print("MISMATCH in sensible responses.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny parakeet space-adventure storyworld.")
    ap.add_argument("--ship", choices=SHIPS)
    ap.add_argument("--signal", choices=SIGNALS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child", choices=CHILD_NAMES)
    ap.add_argument("--grownup", choices=GROWNUP_NAMES)
    ap.add_argument("--parakeet", choices=["Pip", "Nova", "Peep", "Zuzu"])
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
              if (args.ship is None or c[0] == args.ship)
              and (args.signal is None or c[1] == args.signal)
              and (args.hazard is None or c[2] == args.hazard)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    ship, signal, hazard = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_name = args.child or rng.choice(CHILD_NAMES)
    grownup_name = args.grownup or rng.choice(GROWNUP_NAMES)
    parakeet_name = args.parakeet or rng.choice(["Pip", "Nova", "Peep", "Zuzu"])
    parakeet_color = rng.choice(PARAKEET_COLORS)
    return StoryParams(ship=ship, signal=signal, hazard=hazard, response=response,
                       child_name=child_name, child_gender="girl" if child_name in {"Mina", "Tess", "Nia"} else "boy",
                       grownup_name=grownup_name, grownup_gender="woman" if "Aunt" in grownup_name or grownup_name == "Captain Ora" else "man",
                       parakeet_name=parakeet_name, parakeet_color=parakeet_color)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly space adventure story that includes the word "parakeet" and the repeated phrase "{f["signal"].phrase}".',
        f"Tell a moon-ship story where {f['parakeet'].id} keeps repeating {f['signal'].phrase} until the crew follows the clue home.",
        f"Write a short space adventure where a parakeet's repeated words help a child and grown-up escape a risky drift.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    grownup = f["grownup"]
    parakeet = f["parakeet"]
    signal = f["signal"]
    hazard = f["hazard"]
    response = f["response"]
    return [
        QAItem(
            question=f"Who repeated the helpful words in the story?",
            answer=f"The parakeet {parakeet.id} repeated the helpful words. It kept saying {signal.phrase} so the crew could follow the clue."
        ),
        QAItem(
            question=f"What risk did the ship drift toward?",
            answer=f"The ship drifted toward {hazard.label}. That was risky because the story treats it like a space hazard that can shake or confuse the tiny ship."
        ),
        QAItem(
            question=f"How did {grownup.id} help after hearing the parakeet?",
            answer=f"{grownup.id} used {response.qa_text}. That kept the ship steady and helped the crew stay safe."
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt happy and relieved at the end. The repeated words led the crew home, so the scary drifting ended in a bright safe harbor."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["signal"].tags) | set(f["hazard"].tags) | set(f["response"].tags) | {"parakeet"}
    out = []
    if "parakeet" in tags:
        out.append(QAItem("What is a parakeet?", "A parakeet is a small bird with a bright voice. It can chirp and repeat sounds it hears."))
    if "signal" in tags:
        out.append(QAItem("What is a signal?", "A signal is a sign or sound that tells someone what to do. In this story, the repeated words acted like a guide."))
    if "ship" in f["ship"].tags:
        out.append(QAItem("What is a spaceship for?", "A spaceship carries people through space. It needs careful steering so it can travel safely."))
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(ship="moon_glider", signal="follow_chirp", hazard="meteor_glitter", response="steady_throttle",
                child_name="Mina", child_gender="girl", grownup_name="Captain Ora", grownup_gender="woman",
                parakeet_name="Pip", parakeet_color="green"),
    StoryParams(ship="starlight_skiff", signal="keep_chirping", hazard="dust_swirl", response="blue_beacon",
                child_name="Jun", child_gender="boy", grownup_name="Commander Vale", grownup_gender="man",
                parakeet_name="Nova", parakeet_color="yellow"),
    StoryParams(ship="comet_cart", signal="repeat_route", hazard="ring_shadow", response="slow_turn",
                child_name="Tess", child_gender="girl", grownup_name="Aunt Sol", grownup_gender="woman",
                parakeet_name="Peep", parakeet_color="blue"),
]


def generate(params: StoryParams) -> StorySample:
    try:
        ship = SHIPS[params.ship]
        signal = SIGNALS[params.signal]
        hazard = HAZARDS[params.hazard]
        response = RESPONSES[params.response]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter: {exc.args[0]})") from exc
    if not valid_combo(ship, signal, hazard, response):
        raise StoryError("(This combination is not reasonable for this storyworld.)")
    world = tell(ship, signal, hazard, response, params.child_name, params.child_gender,
                 params.grownup_name, params.grownup_gender, params.parakeet_name, params.parakeet_color)
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for combo in asp_valid_combos():
            print(combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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
    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} and {p.grownup_name}: {p.parakeet_name} in {p.ship}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
