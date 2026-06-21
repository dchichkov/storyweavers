#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/conjunction_cautionary_transformation_suspense_pirate_tale.py
============================================================================================

A compact storyworld in a pirate-tale style with three features in the seed:
cautionary, transformation, suspense, plus the required word "conjunction".

Premise
-------
Two young pirates are exploring after dusk. They find a strange moon-ink coin
that promises a magical transformation if they speak at a conjunction of sun
and moon. One child wants to try it at once, but the other warns that strange
magic can twist the sailor who uses it. The suspense comes from waiting to see
what changes, and the cautionary turn comes from choosing a safe, kind use of
the strange object instead of reckless magic.

This file is self-contained except for the shared result containers in
storyworlds/results.py, and the optional clingo helper in storyworlds/asp.py.
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
BRAVERY_INIT = 6.0
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
    transformed: bool = False
    hidden: bool = False

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
class Island:
    id: str
    place: str
    dark_spot: str
    wind: str
    treasure_word: str
    setting_line: str
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
class Charm:
    id: str
    name: str
    label: str
    promise: str
    danger: str
    transformation: str
    strange_effect: str
    tags: set[str] = field(default_factory=set)
    makes_magic: bool = True
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
class Transformation:
    id: str
    label: str
    reveal: str
    change_line: str
    after_line: str
    risky: bool = True
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
class Safety:
    id: str
    label: str
    line: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


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


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    moon = world.entities.get("moon")
    if moon and moon.meters["glow"] >= THRESHOLD and not moon.hidden:
        sig = ("suspense", "moon")
        if sig not in world.fired:
            world.fired.add(sig)
            for e in list(world.entities.values()):
                if e.role in {"captain", "mate"}:
                    e.memes["unease"] += 1
            out.append("__wait__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    charm = world.entities.get("charm")
    if not charm or charm.meters["magic"] < THRESHOLD:
        return out
    sig = ("transform", charm.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    lantern = world.entities.get("lantern")
    if lantern:
        lantern.transformed = True
        lantern.label = "moon lantern"
        lantern.meters["glow"] += 1
        out.append("The little lamp changed into a moon lantern, and its glass shone silver.")
    return out


CAUSAL_RULES = [
    Rule("suspense", "social", _r_suspense),
    Rule("transform", "magic", _r_transform),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(line for line in lines if not line.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def safe_choice(charm: Charm, target: Transformation) -> bool:
    return charm.makes_magic and target.risky


def cautious_end(charm: Charm, target: Transformation) -> bool:
    return charm.makes_magic and target.risky and "tide" in charm.tags


def predict_transform(world: World) -> dict:
    sim = world.copy()
    sim.get("charm").meters["magic"] += 1
    propagate(sim, narrate=False)
    return {
        "transformed": sim.get("lantern").transformed,
        "unease": sum(e.memes["unease"] for e in sim.entities.values()),
    }


def tell(world: World, island: Island, charm: Charm, trans: Transformation,
         safety: Safety, captain_name: str, mate_name: str,
         captain_gender: str, mate_gender: str, delay: int = 0,
         parent: str = "father") -> World:
    cap = world.add(Entity(id=captain_name, kind="character", type=captain_gender, role="captain"))
    mate = world.add(Entity(id=mate_name, kind="character", type=mate_gender, role="mate"))
    elder = world.add(Entity(id="elder", kind="character", type=parent, role="elder", label="the old sailor"))
    ship = world.add(Entity(id="ship", type="ship", label="the ship"))
    moon = world.add(Entity(id="moon", type="thing", label="the moon"))
    lantern = world.add(Entity(id="lantern", type="thing", label="a brass lantern"))
    c = world.add(Entity(id="charm", type="charm", label=charm.label))
    cap.memes["bravery"] = BRAVERY_INIT
    mate.memes["warning"] = 5.0

    world.say(f"At the edge of the harbor, {cap.id} and {mate.id} crept along {island.place}. {island.setting_line}")
    world.say(f'The wind worried the ropes, and {island.dark_spot} looked as black as ink. "{island.treasure_word} can wait," {mate.id} whispered, but {cap.id} pointed at a strange {charm.label}.')
    world.para()
    world.say(f'"It says it will {charm.promise}," {cap.id} breathed. "At the conjunction, the sea and sky might answer."')
    world.say(f'{mate.id} bit {mate.pronoun("possessive")} lip. "{charm.danger}. If magic goes wrong, it can change more than you mean."')
    pred = predict_transform(world)
    world.facts["predicted"] = pred

    world.para()
    if delay > 0:
        moon.meters["glow"] += 1
        world.say(f"They waited while the sky slowly shifted. The moon climbed higher, and the hour of the conjunction crept closer.")
    if cautious_end(charm, trans):
        cap.memes["caution"] += 1
        world.say(f"{cap.id} looked from the charm to {mate.id}, then nodded. {mate.id} was right. Strange magic should not be rushed.")
        world.say(f"So they used the charm only to find a safe lantern spark for {elder.label_word}, not to cast a wild spell.")
        world.para()
        safety_line = safety.line
        world.say(f"{elder.label_word.capitalize()} smiled and showed them the proper way to handle it. {safety_line}")
        cap.memes["relief"] += 1
        mate.memes["relief"] += 1
    else:
        cap.meters["risk"] += 1
        charm_ent = world.get("charm")
        charm_ent.meters["magic"] += 1
        world.say(f"{cap.id} could not wait. At the conjunction, {cap.id} whispered the old words and the charm warmed like a live ember.")
        propagate(world, narrate=False)
        world.para()
        world.say(f"The lantern trembled. Its flame did not go out; instead, it changed, slow and bright, into a moon lantern.")
        if pred["unease"] >= THRESHOLD:
            world.say(f"{mate.id} stepped back, feeling the hush before trouble. Suspense filled the deck while everyone watched what the magic had become.")
        if delay >= 2:
            world.say(f"For one heart-stopping breath, it looked as if the glowing thing might pull the whole ship into the dark. Then {elder.label_word} seized the lantern and steadied it.")
        world.say(f"{elder.label_word.capitalize()} warned them that a spell can transform a tool, but it can also transform the people who trust it too quickly.")
        world.say(f"So the pirates kept the moon lantern for honest night-sailing and vowed never to speak that charm aloud without a grown sailor nearby.")

    world.facts.update(
        captain=cap,
        mate=mate,
        elder=elder,
        island=island,
        charm=charm,
        transformation=trans,
        safety=safety,
        lantern=lantern,
        outcome="cautious" if cautious_end(charm, trans) else "tense",
        transformed=world.get("lantern").transformed,
    )
    return world


ISLANDS = {
    "harbor": Island(
        id="harbor",
        place="the old harbor path",
        dark_spot="the dock under the broken awning",
        wind="salt wind",
        treasure_word="the treasure chest",
        setting_line="The harbor lanterns were low, and the tide lapped the posts like a whisper.",
    ),
    "reef": Island(
        id="reef",
        place="the reef side of the island",
        dark_spot="the cave mouth by the cliff",
        wind="sea wind",
        treasure_word="the pearl box",
        setting_line="Far out, the waves shone white, but the cave mouth stayed dark and secret.",
    ),
}

CHARMS = {
    "mooncoin": Charm(
        id="mooncoin",
        name="moon coin",
        label="moon coin",
        promise="turn any small lamp into a moon lantern",
        danger="It can twist a bright thing if you speak too greedily",
        transformation="moon lantern",
        strange_effect="its edge glimmered like a thin smile",
        tags={"tide"},
    ),
    "tidekey": Charm(
        id="tidekey",
        name="tide key",
        label="tide key",
        promise="wake a sleeping map and make it sing",
        danger="It answers only once, and a hurry can make it mislead you",
        transformation="singing map",
        strange_effect="the key hummed in a low, watery note",
        tags={"tide"},
    ),
}

TRANSFORMS = {
    "lantern": Transformation(
        id="lantern",
        label="moon lantern",
        reveal="the brass lantern flickered and shimmered",
        change_line="the glass grew pale and round as a little moon",
        after_line="Its light became steady and silver, good for a careful night watch.",
        risky=True,
        tags={"light"},
    ),
    "map": Transformation(
        id="map",
        label="singing map",
        reveal="the old chart trembled on the crate",
        change_line="the ink lines rose into bright, moving waves",
        after_line="It sang softly, but only when the sailor held it gently and listened.",
        risky=True,
        tags={"map"},
    ),
}

SAFETIES = {
    "watch": Safety(
        id="watch",
        label="night watch",
        line="They used the moon lantern only for a proper night watch, and the dock stayed calm and bright.",
        tags={"light"},
    ),
    "chart": Safety(
        id="chart",
        label="chart",
        line="They tucked the charm away and marked the route on paper instead, keeping the adventure safe.",
        tags={"map"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ivy", "Rose"]
BOY_NAMES = ["Finn", "Jace", "Owen", "Pip", "Milo"]
TRAITS = ["curious", "bold", "careful", "brave"]


@dataclass
class StoryParams:
    island: str
    charm: str
    transformation: str
    safety: str
    captain: str
    captain_gender: str
    mate: str
    mate_gender: str
    parent: str
    trait: str = "curious"
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
    StoryParams(
        island="harbor",
        charm="mooncoin",
        transformation="lantern",
        safety="watch",
        captain="Mina",
        captain_gender="girl",
        mate="Finn",
        mate_gender="boy",
        parent="father",
        trait="bold",
        delay=1,
    ),
    StoryParams(
        island="reef",
        charm="tidekey",
        transformation="map",
        safety="chart",
        captain="Pip",
        captain_gender="boy",
        mate="Nora",
        mate_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for island in ISLANDS:
        for charm_id in CHARMS:
            for trans_id in TRANSFORMS:
                if safe_choice(CHARMS[charm_id], TRANSFORMS[trans_id]):
                    combos.append((island, charm_id, trans_id))
    return combos


KNOWLEDGE = {
    "conjunction": [("What is a conjunction?", "A conjunction is a time when two things line up or come together. In stories, that moment can feel important and a little mysterious.")],
    "moon": [("Why can the moon make the night feel spooky?", "The moon makes light, but it can also leave shadows and silver glints that make quiet places feel strange.")],
    "harbor": [("What is a harbor?", "A harbor is a place near the water where boats can stop safely.")],
    "tide": [("What is a tide?", "A tide is the sea moving in and out again and again.")],
    "magic": [("Why should you be careful with magic in a story?", "Magic can change things in ways you did not plan, so careful characters use it with patience and help.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a young child that uses the word "conjunction" and has a suspenseful moment before a strange transformation.',
        f"Tell a cautionary pirate story where {f['captain'].id} wants to use a {f['charm'].label} at a conjunction, but {f['mate'].id} warns that magic can change a thing the wrong way.",
        f"Write a suspense story about a moon lantern, a wary warning, and a safe ending at {f['island'].place}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    cap, mate, elder = f["captain"], f["mate"], f["elder"]
    charm, trans, island = f["charm"], f["transformation"], f["island"]
    qa = [
        ("Who are the story about?", f"It is about {cap.id} and {mate.id}, two young pirates, and {elder.label_word}, who helps keep the evening safe."),
        ("What did they find?", f"They found a {charm.label} that promised a strange change if they used it at the conjunction. That made the deck feel both exciting and a little scary."),
        ("Why was the moment suspenseful?", f"They had to wait for the conjunction before they knew what the charm would do. The waiting made everyone listen closely to the wind and the waves."),
        ("What warning was given?", f"{mate.id} warned that {charm.danger.lower()}. That warning mattered because the charm was meant for careful use, not a greedy rush."),
    ]
    if f["outcome"] == "cautious":
        qa.append(("How did the story end?", f"They chose the safe way and kept the magic gentle. The pirates ended with a useful light instead of a risky spell, and {elder.label_word} was glad they listened."))
    else:
        qa.append(("How did the transformation turn out?", f"{trans.reveal.capitalize()} and the lantern transformed into a moon lantern. It was still beautiful, but the change showed why the pirates had been warned to be careful."))
        qa.append(("What did they learn?", f"They learned that a charm can transform a tool, but impatience can transform a fun idea into trouble. After that, they promised to ask for help before trying strange magic again."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["charm"].tags) | set(world.facts["transformation"].tags)
    if world.facts["outcome"] == "cautious":
        tags.add("magic")
    else:
        tags |= {"moon", "harbor", "magic"}
    out = []
    for key, items in KNOWLEDGE.items():
        if key in tags:
            out.extend(items)
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


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
        if e.transformed:
            bits.append("transformed=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this combination does not support a real transformation or a sensible cautionary beat.)"


def outcome_of(params: StoryParams) -> str:
    return "cautious" if params.safety in SAFETIES else "tense"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with caution, transformation, and suspense.")
    ap.add_argument("--island", choices=ISLANDS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--transformation", choices=TRANSFORMS)
    ap.add_argument("--safety", choices=SAFETIES)
    ap.add_argument("--captain")
    ap.add_argument("--mate")
    ap.add_argument("--captain-gender", choices=["girl", "boy"])
    ap.add_argument("--mate-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    combos = [c for c in valid_combos()
              if (args.island is None or c[0] == args.island)
              and (args.charm is None or c[1] == args.charm)
              and (args.transformation is None or c[2] == args.transformation)]
    if not combos:
        raise StoryError(explain_rejection())
    island, charm, trans = rng.choice(sorted(combos))
    safety = args.safety or rng.choice(sorted(SAFETIES))
    captain_gender = args.captain_gender or rng.choice(["girl", "boy"])
    mate_gender = args.mate_gender or ("boy" if captain_gender == "girl" else "girl")
    captain = args.captain or rng.choice(GIRL_NAMES if captain_gender == "girl" else BOY_NAMES)
    mate = args.mate or rng.choice([n for n in (GIRL_NAMES if mate_gender == "girl" else BOY_NAMES) if n != captain])
    parent = args.parent or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(island=island, charm=charm, transformation=trans, safety=safety,
                       captain=captain, captain_gender=captain_gender, mate=mate,
                       mate_gender=mate_gender, parent=parent, delay=delay)


def generate(params: StoryParams) -> StorySample:
    if params.island not in ISLANDS or params.charm not in CHARMS or params.transformation not in TRANSFORMS or params.safety not in SAFETIES:
        raise StoryError("Invalid params.")
    world = World()
    world = tell(world, ISLANDS[params.island], CHARMS[params.charm], TRANSFORMS[params.transformation], SAFETIES[params.safety], params.captain, params.mate, params.captain_gender, params.mate_gender, params.delay, params.parent)
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
magic_possible(C) :- charm(C), makes_magic(C).
conjunction_moment :- delay(D), D >= 1.
risky_transform(T) :- transformation(T), risky(T).
cautious_outcome :- safety(S), safe(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for island in ISLANDS:
        lines.append(asp.fact("island", island))
    for cid, charm in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        if charm.makes_magic:
            lines.append(asp.fact("makes_magic", cid))
    for tid, tr in TRANSFORMS.items():
        lines.append(asp.fact("transformation", tid))
        if tr.risky:
            lines.append(asp.fact("risky", tid))
    for sid in SAFETIES:
        lines.append(asp.fact("safety", sid))
        lines.append(asp.fact("safe", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program("#show cautious_outcome/0."))
        _ = model
    except Exception as exc:
        print(f"ASP unavailable or failed: {exc}")
        return 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        print(f"Smoke test failed: {exc}")
        return 1
    print("OK: generate() smoke test passed and ASP helper loaded.")
    return 0


def asp_valid_combos() -> list[tuple]:
    return sorted(valid_combos())


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show magic_possible/1.\n#show cautious_outcome/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {idx + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
