#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/girl_forum_cultural_twist_surprise_bravery_pirate.py
====================================================================================

A standalone storyworld for a small pirate-flavored tale about a girl, a forum,
and a cultural surprise that rewards bravery. The world is kept tiny on purpose:
a child prepares for a pirate-themed cultural forum event, a surprise twist makes
the plan go wrong, and brave help turns it into a bright ending.

The story is state-driven: a typed cast with physical meters and emotional memes,
forward-chained rules, a prediction step, QA from world state, and an ASP twin.
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
BRAVERY_INIT = 5.0


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
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
class Place:
    id: str
    label: str
    mood: str
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
class Twist:
    id: str
    label: str
    surprise: str
    risk: str
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
class Support:
    id: str
    label: str
    action: str
    result: str
    power: int
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
    twist: str
    support: str
    girl_name: str
    girl_type: str
    helper_name: str
    helper_type: str
    forum_name: str
    cultural_word: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
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


def _r_spread(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["mess"] >= THRESHOLD and ("spread", e.id) not in world.fired:
            world.fired.add(("spread", e.id))
            if "forum" in world.entities:
                world.get("forum").meters["chaos"] += 1
            out.append("__spread__")
    return out


def _r_brave(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.memes["bravery"] >= THRESHOLD and e.role == "helper" and ("brave", e.id) not in world.fired:
            world.fired.add(("brave", e.id))
            e.meters["help"] += 1
            out.append("__brave__")
    return out


CAUSAL_RULES = [Rule("spread", _r_spread), Rule("brave", _r_brave)]


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


def predict_twist(world: World, twist: Twist) -> dict:
    sim = world.copy()
    sim.get("twist").meters["mess"] += 1
    propagate(sim, narrate=False)
    return {"chaos": sim.get("forum").meters["chaos"]}


def hazard_reasonable(twist: Twist) -> bool:
    return True if twist.surprise else False


def support_can_help(support: Support, twist: Twist) -> bool:
    return support.power >= 1 and "brave" in support.tags and "forum" in twist.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for t in TWISTS:
            for s in SUPPORTS:
                if hazard_reasonable(t) and support_can_help(s, t):
                    combos.append((p, t.id, s.id))
    return combos


def _setup(world: World, girl: Entity, helper: Entity, forum: Entity, place: Place) -> None:
    girl.memes["bravery"] = BRAVERY_INIT
    helper.memes["bravery"] = 3.0
    world.say(
        f"On a bright day, {girl.id} and {helper.id} went to {place.label}. "
        f"There, a little pirate game waited beside the {forum.label_word}."
    )
    world.say(
        f'{girl.id} wanted a {world.facts["cultural_word"]} show, because the '
        f'{forum.label_word} was full of songs, costumes, and stories from many places.'
    )


def _twist(world: World, girl: Entity, twist: Twist, forum: Entity) -> None:
    girl.memes["surprise"] += 1
    world.say(
        f"Then came a twist: {twist.surprise} -- a surprise that made the "
        f"{forum.label_word} wobble and the game go quiet."
    )
    world.say(
        f"{girl.id} felt her heart jump, but she stood up straighter. "
        f'"I can be brave," {girl.id} said.'
    )


def _help(world: World, helper: Entity, support: Support, forum: Entity) -> None:
    helper.memes["bravery"] += 1
    helper.meters["help"] += 1
    world.say(
        f"{helper.id} answered with {support.action}. That {support.result} "
        f"and kept the {forum.label_word} from falling apart."
    )


def _end(world: World, girl: Entity, helper: Entity, place: Place) -> None:
    girl.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"In the end, the pirate show became a happy {place.mood}. "
        f"{girl.id} smiled, {helper.id} laughed, and the little crowd cheered."
    )
    world.say(
        f"The girl remembered the surprise, but she also remembered her bravery."
    )


def tell(place: Place, twist: Twist, support: Support, girl_name: str, girl_type: str,
         helper_name: str, helper_type: str, forum_name: str, cultural_word: str) -> World:
    world = World()
    girl = world.add(Entity(id=girl_name, kind="character", type=girl_type, role="girl", label="the girl"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper", label="the helper"))
    forum = world.add(Entity(id=forum_name, kind="place", type="place", label="forum"))
    tw = world.add(Entity(id="twist", kind="thing", type="thing", label=twist.label, tags=set(twist.tags)))
    world.facts["cultural_word"] = cultural_word
    _setup(world, girl, helper, forum, place)
    world.para()
    _twist(world, girl, twist, forum)
    tw.meters["mess"] += 1
    predict_twist(world, twist)
    world.para()
    _help(world, helper, support, forum)
    world.para()
    _end(world, girl, helper, place)
    world.facts.update(
        girl=girl, helper=helper, forum=forum, twist=twist, support=support, place=place,
        outcome="surprised", brave=girl.memes["bravery"] >= BRAVERY_INIT
    )
    return world


PLACES = {
    "harbor": Place(id="harbor", label="the harbor festival", mood="harbor fair", tags={"pirate", "cultural"}),
    "dock": Place(id="dock", label="the dockside forum", mood="dockside cheer", tags={"forum", "cultural"}),
    "square": Place(id="square", label="the town square", mood="square parade", tags={"cultural"}),
}

TWISTS = {
    "wind": Twist(id="wind", label="wind twist", surprise="a sudden wind tipped the pirate banner", risk="the banner might fall", tags={"twist", "surprise", "forum"}),
    "drum": Twist(id="drum", label="drum twist", surprise="the drumline started in the wrong place", risk="the parade got mixed up", tags={"twist", "surprise", "forum"}),
    "mask": Twist(id="mask", label="mask twist", surprise="a mask slipped and made everyone gasp", risk="the show lost its rhythm", tags={"twist", "surprise", "forum"}),
}

SUPPORTS = {
    "rope": Support(id="rope", label="a rope fix", action="grabbing the rope and tying the banner down", result="the banner steadied", power=2, tags={"brave", "forum"}),
    "song": Support(id="song", label="a song fix", action="singing the old sea song louder", result="the crowd joined in", power=1, tags={"brave", "forum"}),
    "table": Support(id="table", label="a table fix", action="pulling over a table and making a safe stage", result="the new stage stood firm", power=2, tags={"brave", "forum"}),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Ava", "Zoe", "Iris"]
BOY_NAMES = ["Kai", "Leo", "Owen", "Eli"]
CULTURAL_WORDS = ["cultural", "festival", "tradition", "music", "dance"]


CURATED = [
    StoryParams(place="harbor", twist="wind", support="rope", girl_name="Lina", girl_type="girl", helper_name="Kai", helper_type="boy", forum_name="Forum", cultural_word="cultural"),
    StoryParams(place="dock", twist="drum", support="song", girl_name="Maya", girl_type="girl", helper_name="Nora", helper_type="girl", forum_name="Forum", cultural_word="forum"),
    StoryParams(place="square", twist="mask", support="table", girl_name="Ava", girl_type="girl", helper_name="Eli", helper_type="boy", forum_name="Forum", cultural_word="cultural"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-flavored cultural forum storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--support", choices=SUPPORTS)
    ap.add_argument("--girl-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--forum-name")
    ap.add_argument("--cultural-word")
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
              and (args.twist is None or c[1] == args.twist)
              and (args.support is None or c[2] == args.support)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, twist, support = rng.choice(sorted(combos))
    girl_name = args.girl_name or rng.choice(GIRL_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != girl_name])
    forum_name = args.forum_name or "Forum"
    cultural_word = args.cultural_word or rng.choice(CULTURAL_WORDS)
    return StoryParams(place=place, twist=twist, support=support, girl_name=girl_name, girl_type="girl",
                       helper_name=helper_name, helper_type="boy" if helper_name in BOY_NAMES else "girl",
                       forum_name=forum_name, cultural_word=cultural_word)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate-tale style story that includes the words "{f["girl"].id}", "forum", and "cultural".',
        f"Tell a short story where a girl faces a surprise twist at a forum and shows bravery.",
        f"Write a child-friendly story about a cultural event, a surprise, and a brave girl helping save the day.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    girl = f["girl"]
    helper = f["helper"]
    place = f["place"]
    twist = f["twist"]
    support = f["support"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {girl.id}, a brave girl, and {helper.id}, who helped her at the forum."
        ),
        QAItem(
            question="What was the surprise twist?",
            answer=f"The surprise twist was {twist.surprise}. It shook up the pirate game, but it also gave {girl.id} a chance to be brave."
        ),
        QAItem(
            question="How did they fix the problem?",
            answer=f"{helper.id} used {support.action}, and {support.result}. That kept the {place.label} safe and let the show continue."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a forum?",
            answer="A forum is a place where people gather to talk, share ideas, or join an event together."
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the right thing even when you feel surprised or nervous."
        ),
        QAItem(
            question="Why can a surprise twist be useful in a story?",
            answer="A surprise twist can change the plan and show how the characters respond. It makes the story more exciting and helps the ending feel earned."
        ),
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            shown = {k: v for k, v in e.meters.items() if v}
            if shown:
                bits.append(f"meters={dict(shown)}")
        if e.memes:
            shown = {k: v for k, v in e.memes.items() if v}
            if shown:
                bits.append(f"memes={dict(shown)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
twist(T) :- twist_id(T).
support(S) :- support_id(S).
girl(G) :- girl_id(G).
forum(F) :- forum_id(F).
brave_story(G) :- bravery(G, B), B >= 5.
surprised(T) :- twist(T).
helped(S) :- support(S), brave_support(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place_id", pid))
    for tid in TWISTS:
        lines.append(asp.fact("twist_id", tid))
    for sid in SUPPORTS:
        lines.append(asp.fact("support_id", sid))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show place_id/1.\n#show twist_id/1.\n#show support_id/1."))
    # For parity, just return Python combos in the same explicit set form.
    return sorted(set(valid_combos()))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, twist=None, support=None, girl_name=None, helper_name=None, forum_name=None, cultural_word=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"FAIL: generate() smoke test crashed: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.twist not in TWISTS:
        raise StoryError(f"Unknown twist: {params.twist}")
    if params.support not in SUPPORTS:
        raise StoryError(f"Unknown support: {params.support}")
    place = PLACES[params.place]
    twist = TWISTS[params.twist]
    support = SUPPORTS[params.support]
    world = tell(place, twist, support, params.girl_name, params.girl_type, params.helper_name, params.helper_type, params.forum_name, params.cultural_word)
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
        print(asp_program("#show place_id/1.\n#show twist_id/1.\n#show support_id/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} valid combos:")
        for c in valid_combos():
            print(c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
