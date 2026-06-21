#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/flower_magic_sharing_rhyme_ghost_story.py
==========================================================================

A small standalone story world for a ghost-story-flavored flower tale:
a child finds a haunted flower, learns a tiny rhyme, shares magic with a ghost,
and ends with a kinder, brighter garden.

The story space is intentionally narrow:
- a flower that can be enchanted
- a ghost that is lonely, not scary-dangerous
- a sharing act that calms the ghost
- a rhyme that powers the resolution

The prose engine is world-state driven: meters and memes accumulate through
events, and the ending image proves what changed.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MAGIC_MIN = 2
SHARING_MIN = 2
RHYME_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)
    ghostly: bool = False
    blooming: bool = False
    glowing: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.ghostly:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Place:
    id: str
    label: str
    dark: str
    bright: str
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
class FlowerSpec:
    id: str
    label: str
    smell: str
    color: str
    bloom_line: str
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
class GhostSpec:
    id: str
    label: str
    spooky_line: str
    lonely_line: str
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
class MagicItem:
    id: str
    label: str
    phrase: str
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
class StoryParams:
    place: str
    flower: str
    ghost: str
    magic: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    rhyme: str
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
        self.facts: dict[str, object] = {}

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
        import copy
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: callable
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


def _r_bloom(world: World) -> list[str]:
    out: list[str] = []
    flower = world.get("flower")
    if flower.meters["magic"] >= THRESHOLD and ("bloom", flower.id) not in world.fired:
        world.fired.add(("bloom", flower.id))
        flower.blooming = True
        flower.glowing = True
        flower.meters["bloom"] += 1
        out.append("__bloom__")
    return out


def _r_comfort(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    child = world.get("child")
    if ghost.memes["shared"] >= THRESHOLD and ghost.memes["heard_rhyme"] >= THRESHOLD:
        if ("comfort", ghost.id) not in world.fired:
            world.fired.add(("comfort", ghost.id))
            ghost.memes["sad"] = 0
            ghost.memes["home"] += 1
            child.memes["brave"] += 1
            out.append("__comfort__")
    return out


CAUSAL_RULES = [Rule("bloom", _r_bloom), Rule("comfort", _r_comfort)]


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


def reasonableness_ok(flower: FlowerSpec, ghost: GhostSpec, magic: MagicItem) -> bool:
    return bool(flower and ghost and magic and magic.power >= MAGIC_MIN)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for flower in FLOWERS:
            for ghost in GHOSTS:
                for magic in MAGIC_ITEMS:
                    if reasonableness_ok(FLOWERS[flower], GHOSTS[ghost], MAGIC_ITEMS[magic]):
                        combos.append((place, flower, ghost, magic))
    return combos


def _do_magic(world: World, magic: MagicItem, flower: Entity) -> None:
    flower.meters["magic"] += magic.power
    flower.memes["wonder"] += 1
    propagate(world, narrate=False)


def _share(world: World, child: Entity, ghost: Entity, flower: Entity) -> None:
    child.memes["sharing"] += 1
    ghost.memes["shared"] += 1
    flower.meters["magic"] += 1
    world.say(
        f"{child.id} held the {flower.label} out with a careful hand and said, "
        f'"You can have some magic too."'
    )


def _rhyme(world: World, child: Entity, helper: Entity, rhyme: str, ghost: Entity) -> None:
    child.memes["rhyme"] += 1
    helper.memes["rhyme"] += 1
    ghost.memes["heard_rhyme"] += 1
    world.say(
        f'Then {child.id} and {helper.id} whispered a little rhyme: "{rhyme}."'
    )
    world.say("The words floated through the dark like lantern light.")


def tell(place: Place, flower: FlowerSpec, ghost: GhostSpec, magic: MagicItem,
         child_name: str, child_gender: str, helper_name: str, helper_gender: str,
         rhyme: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    ghost_ent = world.add(Entity(id="ghost", kind="character", type="thing", role="ghost", ghostly=True))
    flower_ent = world.add(Entity(id="flower", type="thing", label=flower.label))
    world.facts.update(place=place, flower=flower, ghost=ghost, magic=magic, child=child, helper=helper, rhyme=rhyme)

    world.say(
        f"On a hush-dark evening, {child.id} wandered into {place.label}. "
        f"{place.dark}."
    )
    world.say(
        f"Near the path stood a {flower.color} {flower.label} that smelled like {flower.smell}. "
        f"It looked gentle, but a little strange, as if the garden were keeping a secret."
    )
    world.say(
        f"Behind it waited a ghost. {ghost.spooky_line} {ghost.lonely_line}"
    )

    world.para()
    world.say(
        f'"I know a bit of magic," said {child.id}, lifting a little hand. '
        f"{magic.phrase}."
    )
    _do_magic(world, magic, flower_ent)
    world.say(
        f"The {flower.label} answered with a soft glow, and the dark corners of {place.label} grew quieter."
    )
    _share(world, child, ghost_ent, flower_ent)
    _rhyme(world, child, helper, rhyme, ghost_ent)

    world.para()
    if ghost_ent.memes["shared"] >= THRESHOLD and ghost_ent.memes["heard_rhyme"] >= THRESHOLD:
        world.say(
            f"At once, the ghost stopped drifting in circles. It smiled, less spooky now and more shy than anything."
        )
        world.say(
            f"{flower.bloom_line} Petals opened wider, and the glow made a little silver ring on the ground."
        )
        world.say(
            f"The ghost thanked them for the magic and the sharing, then settled beside the flower as if it had found a place to stay."
        )
    else:
        world.say(
            f"The ghost still hovered sadly in the dark, and the flower's glow was not enough to change the night."
        )

    world.facts.update(
        child=child,
        helper=helper,
        ghost_ent=ghost_ent,
        flower_ent=flower_ent,
        outcome="bright" if ghost_ent.memes["shared"] >= THRESHOLD and ghost_ent.memes["heard_rhyme"] >= THRESHOLD else "dim",
    )
    return world


PLACES = {
    "garden": Place(id="garden", label="the garden", dark="The hedges made a long shadow, and the gate creaked in the wind", bright="moonlit path", tags={"garden"}),
    "yard": Place(id="yard", label="the backyard", dark="The old tree scratched the sky, and the grass looked like a dark rug", bright="patch of moonlight", tags={"yard"}),
    "greenhouse": Place(id="greenhouse", label="the greenhouse", dark="The glass panes whispered, and the shelves of pots cast tiny black squares", bright="warm glass", tags={"greenhouse"}),
}

FLOWERS = {
    "rose": FlowerSpec(id="rose", label="rose", smell="sweet rain", color="red", bloom_line="The rose turned its face toward the moon", tags={"flower"}),
    "lily": FlowerSpec(id="lily", label="lily", smell="cool water", color="white", bloom_line="The lily lifted its pale petals like little hands", tags={"flower"}),
    "violet": FlowerSpec(id="violet", label="violet", smell="soft dust", color="purple", bloom_line="The violet opened with a shy purple sigh", tags={"flower"}),
}

GHOSTS = {
    "old_ghost": GhostSpec(id="old_ghost", label="old ghost", spooky_line="Its edges wavered like torn paper.", lonely_line="It looked lonely, as if nobody had said hello in a very long time.", tags={"ghost"}),
    "pale_ghost": GhostSpec(id="pale_ghost", label="pale ghost", spooky_line="Its voice was a thin whisper that slipped between the leaves.", lonely_line="It carried a sadness as quiet as a dropped mitten.", tags={"ghost"}),
}

MAGIC_ITEMS = {
    "spark": MagicItem(id="spark", label="spark", phrase="A tiny spark danced from the child's fingers", power=2, tags={"magic"}),
    "glow_seed": MagicItem(id="glow_seed", label="glow seed", phrase="A glow seed warmed in the palm like a held star", power=3, tags={"magic"}),
    "silver_word": MagicItem(id="silver_word", label="silver word", phrase="A silver word slid from the child's lips and glittered in the air", power=2, tags={"magic", "rhyme"}),
}

RIDDLES = [
    "If a flower is lonely, share a song and watch it bloom",
    "Soft words and bright light can make a ghost feel home",
    "When night is deep, a little rhyme can turn the dark to gold",
]

GIRL_NAMES = ["Mira", "Luna", "Nora", "Ivy", "Elia", "Ada"]
BOY_NAMES = ["Theo", "Finn", "Ezra", "Milo", "Owen", "Jasper"]


@dataclass
class StoryParams:
    place: str
    flower: str
    ghost: str
    magic: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    rhyme: str
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
    ap = argparse.ArgumentParser(description="Ghost-story flower world with magic, sharing, and rhyme.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--flower", choices=FLOWERS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--magic", choices=MAGIC_ITEMS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"], dest="child_gender")
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"], dest="helper_gender")
    ap.add_argument("--rhyme")
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
    if args.magic and MAGIC_ITEMS[args.magic].power < MAGIC_MIN:
        raise StoryError("The magic is too weak to make a meaningful ghost story.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.flower is None or c[1] == args.flower)
              and (args.ghost is None or c[2] == args.ghost)
              and (args.magic is None or c[3] == args.magic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, flower, ghost, magic = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != child])
    rhyme = args.rhyme or rng.choice(RIDDLES)
    return StoryParams(place=place, flower=flower, ghost=ghost, magic=magic,
                       child=child, child_gender=child_gender,
                       helper=helper, helper_gender=helper_gender, rhyme=rhyme)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost-story for a 3-to-5-year-old that includes the word "flower" and a little magic.'
        f" Make the ghost lonely at first, then kinder by the end.",
        f"Tell a story where {f['child'].id} shares magic with a ghost beside a flower and uses a rhyme to help.",
        f'Write a gentle spooky story that ends with sharing, rhyme, and the flower glowing in the dark.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    ghost_ent: Entity = f["ghost_ent"]  # type: ignore[assignment]
    flower_ent: Entity = f["flower_ent"]  # type: ignore[assignment]
    flower: FlowerSpec = f["flower"]
    ghost: GhostSpec = f["ghost"]
    magic: MagicItem = f["magic"]
    rhyme: str = f["rhyme"]
    items = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id}, {helper.id}, and a lonely ghost near a {flower.label}. The night begins spooky, but it turns gentle by the end.",
        ),
        QAItem(
            question="What made the flower change?",
            answer=f"{child.id} used {magic.label} magic on the flower, and then the flower glowed softly. That magic helped brighten the dark garden and made the ghost less afraid.",
        ),
        QAItem(
            question="Why did the ghost get happier?",
            answer=f"The ghost got happier because {child.id} shared the magic and {helper.id} spoke the rhyme. The ghost was lonely at first, so being included made it feel welcome.",
        ),
        QAItem(
            question="What happened to the flower at the end?",
            answer=f"The {flower.label} bloomed brighter and shone like a small lamp in the dark. It became part of the friendly ending instead of staying quiet and hidden.",
        ),
    ]
    if ghost_ent.memes["heard_rhyme"] >= THRESHOLD:
        items.append(
            QAItem(
                question=f"What did {child.id} and {helper.id} say to the ghost?",
                answer=f'They whispered, "{rhyme}." The rhyme floated through the dark and helped the ghost feel safe enough to stay.',
            )
        )
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    flower: FlowerSpec = f["flower"]
    ghost: GhostSpec = f["ghost"]
    return [
        QAItem(
            question="What is a flower?",
            answer="A flower is a plant with petals. Flowers can smell sweet and can bloom open in the light.",
        ),
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost is often a spooky character from a story. In gentle stories, a ghost can be lonely, kind, and in need of a friend.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use or enjoy something too. It is a kind way to help another person feel included.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pair of words or lines that sound alike at the end. Rhymes can make a story feel musical and easy to remember.",
        ),
        QAItem(
            question="Why can magic matter in a story?",
            answer="Magic can change how a story feels and help solve a problem in a special way. It can make a dark place glow or help a lonely character feel welcome.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.ghostly:
            bits.append("ghostly=True")
        if e.blooming:
            bits.append("blooming=True")
        if e.glowing:
            bits.append("glowing=True")
        out.append(f"  {e.id:8} ({e.type}) " + " ".join(bits))
    out.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(out)


ASP_RULES = r"""
magic_boost(2). magic_boost(3).
story_ok(P,F,G,M) :- place(P), flower(F), ghost(G), magic(M), magic_power(M, Pow), Pow >= 2.
bloom(F) :- magic_power(M, Pow), Pow >= 2, flower(F), chosen_flower(F), chosen_magic(M).
shared(G) :- chosen_ghost(G), sharing_ok.
heard_rhyme(G) :- chosen_ghost(G), rhyme_ok.
happy_ending :- bloom(_), shared(_), heard_rhyme(_).
#show story_ok/4.
#show happy_ending/0.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for f_id, f in FLOWERS.items():
        lines.append(asp.fact("flower", f_id))
    for g_id, g in GHOSTS.items():
        lines.append(asp.fact("ghost", g_id))
    for m_id, m in MAGIC_ITEMS.items():
        lines.append(asp.fact("magic", m_id))
        lines.append(asp.fact("magic_power", m_id, m.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show story_ok/4."))
    return sorted(set(asp.atoms(model, "story_ok")))


def asp_verify() -> int:
    rc = 0
    try:
        import asp
        aset = set(asp_valid_combos())
        pset = set(valid_combos())
        if aset == pset:
            print(f"OK: ASP matches valid_combos() ({len(pset)} combos).")
        else:
            print("MISMATCH in ASP vs Python valid combos:")
            if aset - pset:
                print("  only in ASP:", sorted(aset - pset))
            if pset - aset:
                print("  only in Python:", sorted(pset - aset))
            rc = 1
    except Exception as e:
        print(f"ASP verification could not run cleanly: {e}")
        rc = 1

    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: default generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def valid_combo_filter(args: argparse.Namespace, combo: tuple[str, str, str, str]) -> bool:
    place, flower, ghost, magic = combo
    return ((args.place is None or place == args.place)
            and (args.flower is None or flower == args.flower)
            and (args.ghost is None or ghost == args.ghost)
            and (args.magic is None or magic == args.magic))


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.flower not in FLOWERS or params.ghost not in GHOSTS or params.magic not in MAGIC_ITEMS:
        raise StoryError("Unknown parameter value.")
    if MAGIC_ITEMS[params.magic].power < MAGIC_MIN:
        raise StoryError("Magic is too weak for this story.")
    world = tell(PLACES[params.place], FLOWERS[params.flower], GHOSTS[params.ghost], MAGIC_ITEMS[params.magic],
                 params.child, params.child_gender, params.helper, params.helper_gender, params.rhyme)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos() if valid_combo_filter(args, c)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, flower, ghost, magic = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_pool = GIRL_NAMES if helper_gender == "girl" else BOY_NAMES
    helper = args.helper or rng.choice([n for n in helper_pool if n != child] or helper_pool)
    rhyme = args.rhyme or rng.choice(RIDDLES)
    return StoryParams(place=place, flower=flower, ghost=ghost, magic=magic,
                       child=child, child_gender=child_gender, helper=helper,
                       helper_gender=helper_gender, rhyme=rhyme)


CURATED = [
    StoryParams(place="garden", flower="rose", ghost="old_ghost", magic="spark",
                child="Mira", child_gender="girl", helper="Theo", helper_gender="boy",
                rhyme=RIDDLES[0]),
    StoryParams(place="greenhouse", flower="lily", ghost="pale_ghost", magic="glow_seed",
                child="Owen", child_gender="boy", helper="Ivy", helper_gender="girl",
                rhyme=RIDDLES[1]),
    StoryParams(place="yard", flower="violet", ghost="old_ghost", magic="silver_word",
                child="Nora", child_gender="girl", helper="Finn", helper_gender="boy",
                rhyme=RIDDLES[2]),
]


def build_story_qa(sample: StorySample) -> None:
    pass


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show story_ok/4.\n#show happy_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("", "#show story_ok/4."))
        combos = asp.atoms(model, "story_ok")
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child}: {p.flower} + {p.ghost} + {p.magic}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
