#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/alias_clonk_puck_quest_folk_tale.py
====================================================================

A standalone storyworld for a tiny folk-tale quest: a child gets a secret
alias, follows a clonk-sounding trail, and returns a missing puck to the right
home. The world is small on purpose: one clear quest, one turn, one ending
image proving what changed.

Seed words: alias, clonk, puck
Feature: quest
Style: folk tale
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
REASONABLE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Quest:
    id: str
    title: str
    setting: str
    guide: str
    goal: str
    trail_sound: str
    home_place: str
    return_image: str
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
class Alias:
    id: str
    title: str
    phrase: str
    reveal: str
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
class ClonkSource:
    id: str
    label: str
    phrase: str
    near: str
    makes_noise: bool = True
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
class Puck:
    id: str
    label: str
    phrase: str
    owner: str
    home: str
    round: bool = True
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
    quest: str
    alias: str
    source: str
    puck: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    keeper: str
    keeper_gender: str
    trait: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


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


def _r_lost(world: World) -> list[str]:
    out = []
    puck = world.entities.get("puck")
    if not puck or puck.meters["lost"] < THRESHOLD:
        return out
    if ("lost", "puck") in world.fired:
        return out
    world.fired.add(("lost", "puck"))
    world.get("hero").memes["worry"] += 1
    out.append("__lost__")
    return out


def _r_returned(world: World) -> list[str]:
    puck = world.entities.get("puck")
    if not puck or puck.meters["returned"] < THRESHOLD:
        return []
    if ("returned", "puck") in world.fired:
        return []
    world.fired.add(("returned", "puck"))
    world.get("keeper").memes["relief"] += 1
    return ["__returned__"]


RULES = [Rule("lost", _r_lost), Rule("returned", _r_returned)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sensible_aliases() -> list[Alias]:
    return [a for a in ALIASES.values() if a.title in {"night name", "river name", "fox name"}]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for qid, q in QUESTS.items():
        for aid, a in ALIASES.items():
            for sid, s in CLONKS.items():
                for pid, p in PUCKS.items():
                    if q.goal in p.home and s.makes_noise and q.home_place:
                        combos.append((qid, aid, sid, pid))
    return combos


def clue_at_risk(source: ClonkSource, quest: Quest) -> bool:
    return source.makes_noise and bool(quest.goal)


def tell(quest: Quest, alias: Alias, source: ClonkSource, puck: Puck,
         hero: str = "Mira", hero_gender: str = "girl",
         helper: str = "Tobin", helper_gender: str = "boy",
         keeper: str = "Nera", keeper_gender: str = "woman",
         trait: str = "curious") -> World:
    world = World()
    h = world.add(Entity(id=hero, kind="character", type=hero_gender, role="hero",
                         traits=[trait], attrs={"quest": quest.id}))
    a = world.add(Entity(id=helper, kind="character", type=helper_gender, role="helper",
                         traits=["wise"], attrs={"quest": quest.id}))
    k = world.add(Entity(id=keeper, kind="character", type=keeper_gender, role="keeper",
                         traits=["kind"], attrs={"quest": quest.id}))
    puck_ent = world.add(Entity(id="puck", type="puck", label=puck.label, tags=set(puck.tags)))
    world.add(Entity(id="source", type="thing", label=source.label, tags=set(source.tags)))

    h.memes["hope"] = 1
    a.memes["care"] = 1

    world.say(
        f"Once in a small folk village, {h.id} set out on a quest in {quest.setting}. "
        f"{a.id} walked beside {h.id}, and {k.id} waited at the old gate."
    )
    world.say(
        f'To keep the path secret, {a.id} gave {h.id} an alias: "{alias.phrase}". '
        f"{alias.reveal} was the name the wind should never hear."
    )
    world.say(
        f"They had to find {puck.phrase}, for without it the hall was silent "
        f"and the bells would not sing."
    )

    world.para()
    world.say(
        f"{h.id} followed the trail past the moss and stones, where one step went "
        f"clonk in the quiet."
    )
    if clue_at_risk(source, quest):
        h.meters["searching"] += 1
        h.memes["need"] += 1
        world.say(
            f"{a.id} stopped and pointed to the sound. " 
            f'"Hear that clonk? The puck is near, but the wrong door could keep it lost."'
        )
    world.say(
        f"The sound led them to {source.near}, where the old road bent like a ribbon."
    )

    world.para()
    puck_ent.meters["lost"] = 1
    world.say(
        f"At last {h.id} found {puck.phrase}. It had been tucked away by the path, "
        f"cold as river-pebble and bright as a little moon."
    )
    world.say(
        f"{k.id} smiled when the puck was brought home to {puck.home}. "
        f"{quest.return_image}."
    )
    puck_ent.meters["returned"] = 1
    propagate(world, narrate=False)
    world.say(
        f"{h.id} bowed and said that the quest was complete, and the alias could "
        f"rest until another tale needed it."
    )

    world.facts.update(
        quest=quest, alias=alias, source=source, puck=puck,
        hero=h, helper=a, keeper=k, returned=True, sound="clonk",
    )
    return world


QUESTS = {
    "moon_gate": Quest(
        id="moon_gate",
        title="The Moon-Gate Quest",
        setting="a small village of lanterns and apple trees",
        guide="an old map",
        goal="the moon-gate",
        trail_sound="clonk",
        home_place="the high shelf in the hall",
        return_image="The hall at last held a bright puck on the high shelf, and the gate stood open to the moon",
        tags={"quest", "folk_tale"},
    ),
    "river_bell": Quest(
        id="river_bell",
        title="The River-Bell Quest",
        setting="a village by the river bend",
        guide="a ribbon of reeds",
        goal="the river bell",
        trail_sound="clonk",
        home_place="the bell-hook above the hearth",
        return_image="The bell-hook above the hearth held the puck again, and the water in the pail looked silver",
        tags={"quest", "folk_tale"},
    ),
}

ALIASES = {
    "night_name": Alias(
        id="night_name",
        title="night name",
        phrase="Night-Foot",
        reveal="It meant the one who walks softly under the stars",
        tags={"alias"},
    ),
    "river_name": Alias(
        id="river_name",
        title="river name",
        phrase="River-Ear",
        reveal="It meant the one who listens where the water turns",
        tags={"alias"},
    ),
    "fox_name": Alias(
        id="fox_name",
        title="fox name",
        phrase="Fox-Shadow",
        reveal="It meant the one who keeps secrets and finds paths",
        tags={"alias"},
    ),
}

CLONKS = {
    "stick": ClonkSource(
        id="stick",
        label="a root-stuck walking stick",
        phrase="a walking stick",
        near="the root of the old ash tree",
        makes_noise=True,
        tags={"clonk"},
    ),
    "gate": ClonkSource(
        id="gate",
        label="an iron gate latch",
        phrase="an iron gate latch",
        near="the gate to the garden wall",
        makes_noise=True,
        tags={"clonk"},
    ),
    "bucket": ClonkSource(
        id="bucket",
        label="a bucket on a stone step",
        phrase="a bucket",
        near="the stone step beside the well",
        makes_noise=True,
        tags={"clonk"},
    ),
}

PUCKS = {
    "moon": Puck(id="moon", label="moon puck", phrase="the moon puck", owner="keeper",
                 home="the high shelf in the hall", tags={"puck", "quest"}),
    "river": Puck(id="river", label="river puck", phrase="the river puck", owner="keeper",
                  home="the bell-hook above the hearth", tags={"puck", "quest"}),
    "ember": Puck(id="ember", label="ember puck", phrase="the ember puck", owner="keeper",
                  home="the stone niche by the hearth", tags={"puck", "quest"}),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny folk-tale quest world.")
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--alias", choices=ALIASES)
    ap.add_argument("--source", choices=CLONKS)
    ap.add_argument("--puck", choices=PUCKS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--keeper")
    ap.add_argument("--keeper-gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--trait")
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
    if args.source and args.quest and not clue_at_risk(CLONKS[args.source], QUESTS[args.quest]):
        raise StoryError("The clonk source does not meaningfully carry the quest forward.")
    combos = [c for c in valid_combos()
              if (args.quest is None or c[0] == args.quest)
              and (args.alias is None or c[1] == args.alias)
              and (args.source is None or c[2] == args.source)
              and (args.puck is None or c[3] == args.puck)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    qid, aid, sid, pid = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    keeper_gender = args.keeper_gender or rng.choice(["woman", "man"])
    return StoryParams(
        quest=qid,
        alias=aid,
        source=sid,
        puck=pid,
        hero=args.hero or rng.choice(["Mira", "Alden", "Sana", "Eli", "Wren"]),
        hero_gender=hero_gender,
        helper=args.helper or rng.choice(["Tobin", "Iris", "Perrin", "Nia"]),
        helper_gender=helper_gender,
        keeper=args.keeper or rng.choice(["Nera", "Bram", "Della"]),
        keeper_gender=keeper_gender,
        trait=args.trait or rng.choice(["curious", "brave", "patient", "gentle"]),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk-tale quest story that includes the words "{f["alias"].phrase}", '
        f'"clonk", and "{f["puck"].label}".',
        f"Tell a gentle quest in which {f['hero'].id} follows a clonk sound, uses an alias, "
        f"and brings the puck home again.",
        f"Write a child-friendly folk tale where a secret alias helps a helper guide a hero "
        f"to the missing puck.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    q = f["quest"]
    a = f["alias"]
    p = f["puck"]
    hero = f["hero"]
    helper = f["helper"]
    keeper = f["keeper"]
    return [
        QAItem(
            question="What kind of story is this?",
            answer=f"It is a folk-tale quest about {hero.id} going after {p.label}. "
                   f"The journey is small and magical, like an old village tale told by firelight.",
        ),
        QAItem(
            question="Why did the helper give the hero an alias?",
            answer=f"{helper.id} gave {hero.id} the alias {a.phrase} so the quest could stay secret. "
                   f"That way, only the right people would know who was traveling and why.",
        ),
        QAItem(
            question="What clue helped them on the path?",
            answer="A clonk sound helped them know they were on the right road. "
                   "It was a plain sound, but it pointed them toward the hidden place.",
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"The missing puck was brought back to {p.home}, and {keeper.id} was relieved. "
                   f"The hall felt ready again, because the puck was home where it belonged.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What is an alias?",
            answer="An alias is a secret or borrowed name someone uses for a while. "
                   "It can help keep a quest quiet or playful.",
        ),
        QAItem(
            question="What does clonk mean in a story?",
            answer="Clonk is a hard, round sound, like wood or metal knocking against something. "
                   "In a tale, it can be a helpful clue that someone is walking the right way.",
        ),
        QAItem(
            question="What is a puck?",
            answer="A puck is a small, round thing. In this tale it is a treasured object that needs to be carried home again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for a in ALIASES:
        lines.append(asp.fact("alias", a))
    for s in CLONKS:
        lines.append(asp.fact("source", s))
        lines.append(asp.fact("clonkish", s))
    for p in PUCKS:
        lines.append(asp.fact("puck", p))
    lines.append(asp.fact("sensible_alias", "night_name"))
    lines.append(asp.fact("sensible_alias", "river_name"))
    lines.append(asp.fact("sensible_alias", "fox_name"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Q,A,S,P) :- quest(Q), alias(A), source(S), puck(P), clonkish(S).
chosen(Q,A,S,P) :- valid(Q,A,S,P).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python gate")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        assert sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.quest not in QUESTS or params.alias not in ALIASES or params.source not in CLONKS or params.puck not in PUCKS:
        raise StoryError("Invalid parameters for this storyworld.")
    world = tell(
        QUESTS[params.quest],
        ALIASES[params.alias],
        CLONKS[params.source],
        PUCKS[params.puck],
        hero=params.hero,
        hero_gender=params.hero_gender,
        helper=params.helper,
        helper_gender=params.helper_gender,
        keeper=params.keeper,
        keeper_gender=params.keeper_gender,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


CURATED = [
    StoryParams(
        quest="moon_gate",
        alias="fox_name",
        source="stick",
        puck="moon",
        hero="Mira",
        hero_gender="girl",
        helper="Tobin",
        helper_gender="boy",
        keeper="Nera",
        keeper_gender="woman",
        trait="curious",
    ),
    StoryParams(
        quest="river_bell",
        alias="river_name",
        source="bucket",
        puck="river",
        hero="Alden",
        hero_gender="boy",
        helper="Iris",
        helper_gender="girl",
        keeper="Bram",
        keeper_gender="man",
        trait="patient",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible quest combos:\n")
        for q, a, s, p in combos:
            print(f"  {q:10} {a:10} {s:8} {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.hero} on the {p.quest} quest"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
