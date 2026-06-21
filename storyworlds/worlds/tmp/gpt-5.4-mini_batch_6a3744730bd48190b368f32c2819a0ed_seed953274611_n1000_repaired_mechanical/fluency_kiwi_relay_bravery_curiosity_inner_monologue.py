#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fluency_kiwi_relay_bravery_curiosity_inner_monologue.py
======================================================================================

A tiny folk-tale storyworld about a shy bird, a curious child, a speaking river,
and a relay that can only be won through brave, fluent passing of a kiwi-shaped
token.

The seed words are woven into the premise:
- fluency: the hero's speaking rhythm becomes clearer as courage grows
- kiwi: the small round token passed in the relay
- relay: the village race at the heart of the tale

The world uses physical meters and emotional memes, a Python reasonableness gate,
and an inline ASP twin for parity checks.
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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


@dataclass
class CharacterTemplate:
    id: str
    type: str
    label: str
    traits: set[str] = field(default_factory=set)
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
class RelayTrack:
    id: str
    label: str
    distance: int
    narrow: bool = False
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
class Token:
    id: str
    label: str
    phrase: str
    shine: str
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
        clone.facts = copy.deepcopy(self.facts)
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


def _r_fluency(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["bravery"] < THRESHOLD or e.memes["curiosity"] < THRESHOLD:
            continue
        sig = ("fluency", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["fluency"] += 1
        out.append("__fluency__")
    return out


def _r_inner_monologue(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["fluency"] < THRESHOLD or e.memes["doubt"] < THRESHOLD:
            continue
        sig = ("monologue", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["resolve"] += 1
        out.append("__monologue__")
    return out


CAUSAL_RULES = [Rule("fluency", "social", _r_fluency), Rule("inner_monologue", "social", _r_inner_monologue)]


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


def track_is_real(track: RelayTrack) -> bool:
    return track.distance > 0


def token_pairs(track: RelayTrack, token: Token) -> bool:
    return track.narrow and token.label == "kiwi"


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for tale in TALES:
        for track_id, track in TRACKS.items():
            for token_id, token in TOKENS.items():
                if track_is_real(track) and token_pairs(track, token):
                    combos.append((tale, track_id, token_id))
    return combos


def _choose_name(rng: random.Random, pool: list[str], avoid: str = "") -> str:
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def predict_relay(world: World, hero_id: str) -> dict:
    sim = world.copy()
    hero = sim.get(hero_id)
    hero.memes["bravery"] += 1
    hero.memes["curiosity"] += 1
    propagate(sim, narrate=False)
    return {"fluency": sim.get(hero_id).meters["fluency"], "resolve": sim.get(hero_id).memes["resolve"]}


def do_run(world: World, hero: Entity, friend: Entity, track: RelayTrack, token: Token, response: Response) -> None:
    hero.meters["speed"] += 1
    hero.meters["relay_pass"] += 1
    if track.narrow:
        hero.memes["focus"] += 1
    if response.power >= track.distance:
        world.say(
            f"They ran the {track.label} with the {token.phrase} in hand, and the little race held together."
        )
    else:
        world.say(
            f"They ran the {track.label}, but the race stumbled before the last bend."
        )


def opening(world: World, hero: Entity, friend: Entity, tale: str) -> None:
    hero.memes["curiosity"] += 1
    friend.memes["bravery"] += 1
    world.say(
        f"Long ago, in a village by the water, {hero.id} and {friend.id} heard a tale about {tale}."
    )
    world.say(
        f"The elders said the village would cheer only if the relay stayed smooth from start to finish."
    )


def call_to_action(world: World, hero: Entity, friend: Entity, track: RelayTrack, token: Token) -> None:
    world.say(
        f"At the green path, the children found the {track.label} and a polished {token.label} waiting on a leaf."
    )
    world.say(
        f'{hero.id} wondered, "Can I speak bravely enough to pass it?" and {friend.id} listened with bright eyes.'
    )


def inner_talk(world: World, hero: Entity) -> None:
    hero.memes["doubt"] += 1
    pred = predict_relay(world, hero.id)
    if pred["fluency"] >= THRESHOLD:
        world.facts["foreseen_fluency"] = pred["fluency"]
    world.say(
        f"{hero.id} took a breath and listened to the small voice inside: "
        f'"If you keep going, your words will come out true."'
    )


def rally(world: World, hero: Entity, friend: Entity, token: Token) -> None:
    hero.memes["bravery"] += 1
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} stood straighter, and the little voice in {hero.pronoun('possessive')} chest turned kind."
    )
    world.say(
        f'"I can do this," {hero.id} said, and the word sounded more fluent than before.'
    )


def relay_pass(world: World, hero: Entity, friend: Entity, track: RelayTrack, token: Token, response: Response) -> None:
    world.say(
        f"The {token.label} flashed like a tiny moon as {hero.id} passed it to {friend.id} in the {track.label}."
    )
    do_run(world, hero, friend, track, token, response)


def ending(world: World, hero: Entity, friend: Entity, track: RelayTrack, token: Token) -> None:
    world.say(
        f"By sunset, the {track.label} was finished, the {token.label} was safe again, and the village sang their names."
    )
    world.say(
        f"{hero.id} smiled because {hero.pronoun('possessive')} brave words had become fluent enough to carry the day."
    )


def tell(tale: str, track: RelayTrack, token: Token, response: Response, hero_name: str, friend_name: str,
         hero_type: str = "girl", friend_type: str = "boy") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="runner"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="helper"))
    world.add(Entity(id="track", type="track", label=track.label))
    world.add(Entity(id="token", type="token", label=token.label))

    hero.memes["curiosity"] = 1.0
    hero.memes["bravery"] = 0.0
    friend.memes["bravery"] = 1.0

    opening(world, hero, friend, tale)
    world.para()
    call_to_action(world, hero, friend, track, token)
    inner_talk(world, hero)
    rally(world, hero, friend, token)
    relay_pass(world, hero, friend, track, token, response)
    world.para()
    ending(world, hero, friend, track, token)

    world.facts.update(
        hero=hero,
        friend=friend,
        tale=tale,
        track=track,
        token=token,
        response=response,
        outcome="won" if response.power >= track.distance else "lost",
    )
    return world


TALES = {
    "river": "a river that listened to bold children",
    "orchard": "an orchard where the trees kept little secrets",
    "hill": "a hill that asked every runner for a truer breath",
}

TRACKS = {
    "riverbank": RelayTrack(id="riverbank", label="riverbank relay", distance=2, narrow=True, tags={"relay"}),
    "orchard_path": RelayTrack(id="orchard_path", label="orchard relay", distance=1, narrow=True, tags={"relay"}),
    "hill_loop": RelayTrack(id="hill_loop", label="hill relay", distance=3, narrow=True, tags={"relay"}),
}

TOKENS = {
    "kiwi": Token(id="kiwi", label="kiwi", phrase="a green kiwi", shine="glowed green", tags={"kiwi"}),
    "golden_kiwi": Token(id="golden_kiwi", label="kiwi", phrase="a golden kiwi", shine="shone like a coin", tags={"kiwi"}),
}

SENSE_MIN = 2

RESPONSES = {
    "steady_hand": Response(id="steady_hand", sense=3, power=3,
                            text="kept the relay steady and carried the token forward without dropping it",
                            fail="tried to keep the relay steady, but the path was too long",
                            qa_text="kept the relay steady and carried the token forward",
                            tags={"relay"}),
    "quick_breath": Response(id="quick_breath", sense=2, power=2,
                             text="took a quick breath and hurried the token along just in time",
                             fail="took a quick breath, but the token slipped away on the hill",
                             qa_text="took a quick breath and hurried the token along",
                             tags={"relay"}),
    "old_song": Response(id="old_song", sense=1, power=1,
                         text="sang an old song but could not keep the relay together",
                         fail="sang an old song, but it did not hold the relay",
                         qa_text="sang an old song",
                         tags={"relay"}),
}

GIRL_NAMES = ["Mina", "Lila", "Sora", "Anya", "Talia", "Nina"]
BOY_NAMES = ["Ravi", "Oren", "Pico", "Eli", "Jaro", "Tobin"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale story for a young child that includes the words "{f["tale"]}", "fluency", "kiwi", and "relay".',
        f"Tell a brave little story about {f['hero'].id} learning fluency during a relay with a kiwi token.",
        f"Write a story where curiosity and inner monologue help a child finish a relay and carry a kiwi safely home.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend = f["hero"], f["friend"]
    track, token, response = f["track"], f["token"], f["response"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id} and {friend.id}, who took part in the {track.label}."),
        ("What did the children find on the leaf?",
         f"They found {token.phrase} waiting at the start of the relay."),
        ("What did the child think inside?",
         f"{hero.id} listened to a small inner voice that told {hero.pronoun('object')} to keep going with courage."),
        ("How did the story end?",
         f"It ended with the {track.label} finished, the {token.label} safe, and the village singing because the relay stayed true."),
    ]
    if f.get("outcome") == "won":
        qa.append(
            ("How did fluency change the hero?",
             f"{hero.id} spoke more fluently after listening to inner monologue and choosing bravery. The clearer words helped {hero.pronoun('object')} pass the {token.label} smoothly.")
        )
    else:
        qa.append(
            ("What went wrong?",
             f"{response.fail}. The relay needed a stronger, steadier finish than that.")
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is fluency?",
         "Fluency means speaking or doing something smoothly and without too many stops."),
        ("What is a relay?",
         "A relay is a race where runners pass something along in turns."),
        ("What is a kiwi?",
         "A kiwi is a small, round fruit with green flesh and tiny seeds."),
        ("What is an inner monologue?",
         "An inner monologue is the quiet talking a person does inside their own mind."),
        ("What is curiosity?",
         "Curiosity is the wish to know more and look closely at new things."),
        ("What is bravery?",
         "Bravery is the courage to do something even when you feel nervous."),
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
fluency(E) :- bravery(E), curiosity(E).
resolve(E) :- fluency(E), doubt(E).
won :- chosen_response(R), power(R,P), chosen_track(T), distance(T,D), P >= D.
outcome(won) :- won.
outcome(lost) :- not won.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in TALES:
        lines.append(asp.fact("tale", tid))
    for tid, t in TRACKS.items():
        lines.append(asp.fact("track", tid))
        lines.append(asp.fact("distance", tid, t.distance))
        if t.narrow:
            lines.append(asp.fact("narrow", tid))
    for kid in TOKENS:
        lines.append(asp.fact("token", kid))
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
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: "StoryParams") -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_response", params.response),
        asp.fact("chosen_track", params.track),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP gate differs from Python valid_combos().")
    else:
        print(f"OK: ASP gate matches Python valid_combos() ({len(valid_combos())} combos).")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as exc:
        print(f"FAILED: generation smoke test crashed: {exc}")
        return 1
    cases = [CURATED[0], CURATED[-1]]
    if any(asp_outcome(p) != outcome_of(p) for p in cases):
        rc = 1
        print("MISMATCH: ASP outcome differs from Python outcome.")
    else:
        print("OK: ASP outcome matches Python outcome on smoke cases.")
    return rc


def outcome_of(params: "StoryParams") -> str:
    return "won" if RESPONSES[params.response].power >= TRACKS[params.track].distance else "lost"


@dataclass
class StoryParams:
    tale: str
    track: str
    token: str
    response: str
    hero: str
    hero_type: str
    friend: str
    friend_type: str
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
    StoryParams(tale="river", track="orchard_path", token="kiwi", response="steady_hand",
                hero="Mina", hero_type="girl", friend="Ravi", friend_type="boy"),
    StoryParams(tale="orchard", track="riverbank", token="golden_kiwi", response="quick_breath",
                hero="Lila", hero_type="girl", friend="Oren", friend_type="boy"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld about fluency, kiwi, and relay.")
    ap.add_argument("--tale", choices=TALES)
    ap.add_argument("--track", choices=TRACKS)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-type", choices=["girl", "boy"])
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
    combos = valid_combos()
    if args.track and args.token and not token_pairs(TRACKS[args.track], TOKENS[args.token]):
        raise StoryError("No story: that token does not fit that relay track.")
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("No story: that response is too weak for this folk tale.")
    combos = [c for c in combos if (args.tale is None or c[0] == args.tale)
              and (args.track is None or c[1] == args.track)
              and (args.token is None or c[2] == args.token)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    tale, track, token = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or ("boy" if hero_type == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    friend = args.friend or _choose_name(rng, GIRL_NAMES + BOY_NAMES, avoid=hero)
    return StoryParams(tale=tale, track=track, token=token, response=response,
                       hero=hero, hero_type=hero_type, friend=friend, friend_type=friend_type)


def generate(params: StoryParams) -> StorySample:
    if params.tale not in TALES or params.track not in TRACKS or params.token not in TOKENS or params.response not in RESPONSES:
        raise StoryError("Invalid params for this storyworld.")
    world = tell(TALES[params.tale], TRACKS[params.track], TOKENS[params.token], RESPONSES[params.response],
                 params.hero, params.friend, params.hero_type, params.friend_type)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("", "#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
        for item in combos:
            print(" ", item)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
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
