#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/children_film_rhyme_bravery_bedtime_story.py
=============================================================================

A tiny bedtime storyworld: children want to watch a film before sleep, but the
film feels a little scary; they use a rhyme to steady their bravery, call for a
calm grown-up when needed, and finish with a softer ending image that proves
they were braver than they first felt.

The world is intentionally small and state-driven:
- typed entities with physical meters and emotional memes
- forward-chained causal rules
- a reasonableness gate over film content and rhyme/comfort responses
- three QA sets generated from world state, not by parsing rendered text
- an inline ASP twin for parity checks

This script is self-contained apart from the shared Storyweavers result API.
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
BRAVERY_START = 5.0
COMFORT_START = 4.0


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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    label: str
    cozy: str
    dark_spot: str
    supports_film: bool = True
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
class Film:
    id: str
    title: str
    clue: str
    scary: int
    whisper: str
    comfortable: bool = True
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
class Rhyme:
    id: str
    line1: str
    line2: str
    line3: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w
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


def _r_fear(world: World) -> list[str]:
    out = []
    for child in world.children():
        if child.meters["fright"] < THRESHOLD:
            continue
        sig = ("fear", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child.memes["bravery"] = max(0.0, child.memes["bravery"] - 1.0)
        out.append("__fear__")
    return out


def _r_bedtime(world: World) -> list[str]:
    out = []
    if "room" not in world.entities:
        return out
    room = world.get("room")
    if room.meters["calm"] >= THRESHOLD and room.meters["safe_light"] >= THRESHOLD:
        sig = ("bedtime",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        for child in world.children():
            child.memes["sleepy"] += 1
        out.append("The room felt soft and ready for sleep.")
    return out


CAUSAL_RULES = [Rule("fear", "emotional", _r_fear), Rule("bedtime", "emotional", _r_bedtime)]


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


def _children(self: World) -> list[Entity]:
    return [e for e in self.entities.values() if e.kind == "character" and e.role == "child"]


World.children = _children  # type: ignore[attr-defined]


def reasonable_film(film: Film, place: Place) -> bool:
    return film.comfortable and place.supports_film


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


SENSE_MIN = 2


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def predict(world: World, child_id: str, film_id: str) -> dict:
    sim = world.copy()
    child = sim.get(child_id)
    film = FILMS[film_id]
    child.meters["fright"] += film.scary
    propagate(sim, narrate=False)
    return {
        "fright": child.meters["fright"],
        "bravery": child.memes["bravery"],
    }


def watch(world: World, child: Entity, film: Film) -> None:
    child.meters["watched"] += 1
    child.meters["fright"] += film.scary
    if film.scary:
        child.memes["bravery"] += 1
    world.say(
        f"{child.id} watched {film.title}, and the flicker on the wall made a tiny shadow leap."
    )


def rhyme_line(world: World, child: Entity, rhyme: Rhyme) -> None:
    child.memes["bravery"] += 1
    child.memes["calm"] += 1
    world.get("room").meters["calm"] += 1
    world.say(
        f'{child.id} whispered, "{rhyme.line1} {rhyme.line2} {rhyme.line3}"'
    )


def warn(world: World, parent: Entity, child: Entity, film: Film) -> None:
    pred = predict(world, child.id, film.id)
    world.facts["predicted_fright"] = pred["fright"]
    world.say(
        f'{parent.label_word.capitalize()} sat beside {child.id} and said, '
        f'"We can pause if this part feels too spooky."'
    )


def calm_turn(world: World, parent: Entity, child: Entity, response: Response) -> None:
    world.get("room").meters["safe_light"] += 1
    child.memes["safe"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came with a little lamp and {response.text}."
    )


def resolve(world: World, child: Entity, parent: Entity, rhyme: Rhyme, film: Film) -> None:
    world.get("room").meters["calm"] += 1
    child.memes["joy"] += 1
    world.say(
        f"Then {child.id} took a breath and said the rhyme again, quieter this time, and the scary part grew small."
    )
    world.say(
        f"At the end, the film was only a story on a screen, {child.id} was tucked in tight, and the room glowed like a sleepy star."
    )


def tell(place: Place, film: Film, rhyme: Rhyme, response: Response,
         child_name: str = "Mia", child_type: str = "girl",
         parent_type: str = "mother") -> World:
    world = World()
    room = world.add(Entity(id="room", kind="thing", type="room", label=place.label))
    child = world.add(Entity(
        id=child_name, kind="character", type=child_type, role="child",
        traits=["small", "curious"], memes={"bravery": BRAVERY_START, "comfort": COMFORT_START}
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent"))
    world.facts["room"] = room
    world.facts["child"] = child
    world.facts["parent"] = parent
    world.facts["film"] = film
    world.facts["rhyme"] = rhyme
    world.facts["response"] = response

    world.say(
        f"After supper, {child.id} and {parent.label_word} curled up in the cozy room and picked a film for bedtime."
    )
    world.say(
        f"{place.cozy} {film.clue}"
    )
    watch(world, child, film)
    world.para()
    warn(world, parent, child, film)
    if film.scary >= 2:
        rhyme_line(world, child, rhyme)
    if response.sense >= SENSE_MIN:
        calm_turn(world, parent, child, response)
    world.para()
    resolve(world, child, parent, rhyme, film)
    propagate(world, narrate=False)
    world.facts.update(
        outcome="calm",
        brave=child.memes["bravery"] >= BRAVERY_START,
        sleepy=child.memes["sleepy"] >= THRESHOLD,
        peaceful=world.get("room").meters["calm"] >= THRESHOLD,
    )
    return world


PLACES = {
    "bedroom": Place(
        id="bedroom", label="the bedroom", cozy="The blankets were piled high, and the lamp made a warm circle.",
        dark_spot="the far corner by the curtain", supports_film=True, tags={"bedtime"}
    ),
    "livingroom": Place(
        id="livingroom", label="the living room", cozy="The couch was soft, and the curtains were shut against the night.",
        dark_spot="the shadow under the table", supports_film=True, tags={"bedtime"}
    ),
    "den": Place(
        id="den", label="the den", cozy="A quilt made the chair into a nest, and the air felt quiet.",
        dark_spot="the corner by the bookshelf", supports_film=True, tags={"bedtime"}
    ),
}

FILMS = {
    "moonboat": Film(
        id="moonboat", title="Moonboat", clue="The film showed a tiny boat sailing under a silver moon.",
        scary=1, whisper="the moon was only bright paper", comfortable=True, tags={"film"}
    ),
    "dragoncloud": Film(
        id="dragoncloud", title="Dragon in the Cloud", clue="The film had a dragon who roared, but the dragon was made of drawings.",
        scary=2, whisper="the roar was only from the speakers", comfortable=True, tags={"film", "brave"}
    ),
    "forestfox": Film(
        id="forestfox", title="Fox in the Forest", clue="The film followed a fox with bright paws and a brave little nose.",
        scary=2, whisper="the dark trees were only on the screen", comfortable=True, tags={"film", "brave"}
    ),
}

RHYMES = {
    "littlelamp": Rhyme(
        id="littlelamp", line1="Little lamp, warm and bright,", line2="Keep the shadows soft tonight,", line3="I am brave and not alone.",
        tags={"rhyme", "comfort"}
    ),
    "starryrest": Rhyme(
        id="starryrest", line1="Starry ceiling, blink and gleam,", line2="Turn the fright into a dream,", line3="Quiet heart, now home to sleep.",
        tags={"rhyme", "comfort"}
    ),
}

RESPONSES = {
    "lamp": Response(
        id="lamp", sense=3, power=3,
        text="brought a little lamp and dimmed it to a sleepy glow",
        fail="brought a little lamp, but the fear was still too big",
        qa_text="brought a little lamp and dimmed it to a sleepy glow",
        tags={"lamp", "bedtime"}
    ),
    "hug": Response(
        id="hug", sense=2, power=2,
        text="gave a long, calm hug and sat right beside them",
        fail="gave a hug, but that wasn't quite enough on its own",
        qa_text="gave a long, calm hug and sat right beside them",
        tags={"hug", "comfort"}
    ),
    "window": Response(
        id="window", sense=1, power=1,
        text="opened the window for a breeze",
        fail="opened the window, but the room stayed spookier than before",
        qa_text="opened the window for a breeze",
        tags={"window"}
    ),
}

SAMPLES = [
    # curated variety
    dict(place="bedroom", film="moonboat", rhyme="littlelamp", response="lamp", child_name="Mia"),
    dict(place="livingroom", film="dragoncloud", rhyme="starryrest", response="hug", child_name="Noah", child_type="boy"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES.values():
        for f in FILMS.values():
            for r in RHYMES.values():
                if reasonable_film(f, p):
                    combos.append((p.id, f.id, r.id))
    return combos


@dataclass
class StoryParams:
    place: str
    film: str
    rhyme: str
    response: str
    child_name: str = "Mia"
    child_type: str = "girl"
    parent_type: str = "mother"
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
    ap = argparse.ArgumentParser(description="Bedtime storyworld: children, film, rhyme, bravery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--film", choices=FILMS)
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=["mother", "father"])
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
              and (args.film is None or c[1] == args.film)
              and (args.rhyme is None or c[2] == args.rhyme)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, film, rhyme = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    if RESPONSES[response].sense < SENSE_MIN:
        raise StoryError(f"(Refusing response '{response}': too weak for bedtime bravery.)")
    return StoryParams(
        place=place,
        film=film,
        rhyme=rhyme,
        response=response,
        child_name=args.child_name or rng.choice(["Mia", "Noah", "Luna", "Eli"]),
        child_type=args.child_type or rng.choice(["girl", "boy"]),
        parent_type=args.parent_type or rng.choice(["mother", "father"]),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    film = f["film"]
    rhyme = f["rhyme"]
    return [
        f'Write a bedtime story for a child named {child.id} that includes the words "children" and "film".',
        f"Tell a gentle story where {child.id} feels a little scared by the film {film.title}, then finds bravery in a rhyme.",
        f"Write a cozy bedtime tale where rhyme helps children stay brave while watching a film together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    film = f["film"]
    rhyme = f["rhyme"]
    response = f["response"]
    return [
        QAItem(
            question="What were the children doing at bedtime?",
            answer=f"They were watching a film together in a cozy room. The story stays gentle because the film only felt a little scary, not truly dangerous."
        ),
        QAItem(
            question=f"Why did {child.id} feel braver?",
            answer=f"{child.id} whispered the rhyme and remembered the calm grown-up beside them. That helped {child.pronoun()} steady {child.pronoun('possessive')} heart and keep watching."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the room calm, the lamp glowing softly, and everyone ready for sleep. The brave part was that the fear got smaller instead of bigger."
        ),
        QAItem(
            question=f"What did {parent.label_word} do to help?",
            answer=f"{parent.label_word.capitalize()} sat close, brought a little light, and chose a response that fit bedtime best. That made the room feel safe enough for the film to become only a story."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a film?",
            answer="A film is a story shown on a screen with moving pictures. It can be funny, exciting, or a little spooky, but it is still only a picture story."
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a small bit of sound play where words can echo each other at the end. People use rhymes to remember lines and to feel calm."
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the next good thing even when you feel nervous. It does not mean you feel no fear at all."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        parts = []
        if e.meters:
            m = {k: v for k, v in e.meters.items() if v}
            if m:
                parts.append(f"meters={dict(m)}")
        if e.memes:
            mm = {k: v for k, v in e.memes.items() if v}
            if mm:
                parts.append(f"memes={dict(mm)}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_place(P) :- place(P).
valid_film(F) :- film(F), comfortable(F).
valid_combo(P,F,R) :- valid_place(P), valid_film(F), rhyme(R).
outcome(calm) :- response(R), sense(R,S), sense_min(M), S >= M.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("sense_min", SENSE_MIN)]
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for fid, film in FILMS.items():
        lines.append(asp.fact("film", fid))
        if film.comfortable:
            lines.append(asp.fact("comfortable", fid))
    for rid in RHYMES:
        lines.append(asp.fact("rhyme", rid))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, resp.sense))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP gate differs from Python gate.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            place=None, film=None, rhyme=None, response=None,
            child_name=None, child_type=None, parent_type=None
        ), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"MISMATCH: story generation smoke test failed: {exc}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return rc


def tell_story(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.film not in FILMS:
        raise StoryError("Unknown film.")
    if params.rhyme not in RHYMES:
        raise StoryError("Unknown rhyme.")
    if params.response not in RESPONSES:
        raise StoryError("Unknown response.")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError("Response too weak.")
    world = tell(PLACES[params.place], FILMS[params.film], RHYMES[params.rhyme],
                 RESPONSES[params.response], params.child_name, params.child_type, params.parent_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return tell_story(params)


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
        print(asp_program("", "#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(**d)) for d in SAMPLES]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
