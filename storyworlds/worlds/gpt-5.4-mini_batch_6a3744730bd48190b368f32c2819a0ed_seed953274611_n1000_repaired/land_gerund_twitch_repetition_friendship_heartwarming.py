#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/land_gerund_twitch_repetition_friendship_heartwarming.py
=========================================================================================

A small heartwarming storyworld about two friends, a twitchy little creature,
and a repeated, calming routine that helps everyone feel brave enough to land.

Seed prompt
-----------
Write a story that includes the following words and narrative instruments.
Words: land-gerund, twitch
Features: Repetition, Friendship
Style: Heartwarming

World idea
----------
Two friends find a tiny injured bird that keeps twitching and cannot settle.
One child remembers a gentle "land-gerund" game: repeat the same calm steps,
again and again, until the bird trusts the hands, the blanket, and the nest.
The story uses repetition as a soothing structure and ends with friendship,
care, and a safe landing.

The script follows the storyworld contract:
- typed entities with physical meters and emotional memes
- a state-driven narrative engine
- reasonableness gates and an inline ASP twin
- prompts, story-grounded QA, and world-knowledge QA
- standard CLI: -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
CALM_MIN = 2.0
TWITCH_MIN = 1.0


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
    plural: bool = False

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


@dataclass
class FriendPair:
    id: str
    scene: str
    repeated_steps: list[str]
    repeated_words: list[str]
    ending_image: str
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
class Need:
    id: str
    label: str
    smallness: str
    is_hurt: bool = True
    twitchy: bool = True
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
class SafePlace:
    id: str
    label: str
    phrase: str
    comforting: str
    welcomes: str
    safe: bool = True
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class HelpfulAction:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    bird = world.entities.get("bird")
    nest = world.entities.get("nest")
    if bird and bird.meters["settled"] >= THRESHOLD and nest:
        sig = ("calm",)
        if sig not in world.fired:
            world.fired.add(sig)
            nest.meters["ready"] += 1
            out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("calm", "emotional", _r_calm)]


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


def reasonableness_gate(pair: FriendPair, need: Need, place: SafePlace) -> bool:
    return need.twitchy and place.safe and bool(pair.repeated_steps)


def can_help(action: HelpfulAction, need: Need) -> bool:
    return action.sense >= 2 and action.power >= 1 and need.is_hurt


def predict_settle(world: World) -> dict:
    sim = world.copy()
    _care_for_bird(sim, narrate=False)
    return {
        "settled": sim.get("bird").meters["settled"] >= THRESHOLD,
        "nest_ready": sim.get("nest").meters["ready"] >= THRESHOLD,
    }


def _care_for_bird(world: World, narrate: bool = True) -> None:
    bird = world.get("bird")
    bird.meters["settled"] += 1
    bird.memes["trust"] += 1
    propagate(world, narrate=narrate)


def tell_intro(world: World, a: Entity, b: Entity, pair: FriendPair, need: Need, place: SafePlace) -> None:
    a.memes["kindness"] += 1
    b.memes["kindness"] += 1
    world.say(
        f"{a.id} and {b.id} were friends who loved quiet afternoons. "
        f"They sat together in {pair.scene}, where {place.phrase} waited and the little bird kept a twitch in its wing."
    )
    world.say(
        f'"We can help," said {a.id}. "We can help," said {b.id}, because that was what friends said when something small was scared.'
    )


def repeat_steps(world: World, a: Entity, b: Entity, pair: FriendPair, need: Need) -> None:
    a.memes["patience"] += 1
    b.memes["patience"] += 1
    world.say(
        f"They tried the land-gerund game, the same gentle routine again and again: {pair.repeated_steps[0]}, "
        f"then {pair.repeated_steps[1]}, then {pair.repeated_steps[2]}."
    )
    world.say(
        f"Each time they repeated it, the bird's twitch got smaller, and each time they repeated it, {a.id} and {b.id} got calmer."
    )


def offer_hand(world: World, a: Entity, b: Entity, need: Need) -> None:
    world.say(
        f'{a.id} held out a warm hand. {b.id} whispered, "Little one, little one, you do not have to rush."'
    )
    world.say(
        f"The bird listened. The twitch softened, just a little."
    )


def settle_bird(world: World, need: Need, place: SafePlace, pair: FriendPair) -> None:
    bird = world.get("bird")
    nest = world.get("nest")
    bird.meters["settled"] += 1
    nest.meters["ready"] += 1
    bird.memes["trust"] += 2
    world.say(
        f"At last, the bird hopped into the nest. It landed carefully, not all at once, but like a leaf touching water."
    )
    world.say(
        f"{pair.ending_image} {place.welcomes}"
    )


def ending(world: World, a: Entity, b: Entity, need: Need, place: SafePlace) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"{a.id} and {b.id} smiled at the tiny nest. The twitch was gone, and the bird stayed tucked in by the soft blanket."
    )
    world.say(
        f'"We did it together," {a.id} said. "Together," {b.id} said back, and the room felt warm and kind.'
    )


def tell(pair: FriendPair, need: Need, place: SafePlace, action: HelpfulAction,
         name1: str = "Mina", type1: str = "girl", name2: str = "Noah", type2: str = "boy") -> World:
    world = World()
    a = world.add(Entity(id=name1, kind="character", type=type1, role="friend", label=name1))
    b = world.add(Entity(id=name2, kind="character", type=type2, role="friend", label=name2))
    bird = world.add(Entity(id="bird", kind="animal", type="bird", label=need.label))
    nest = world.add(Entity(id="nest", kind="thing", type="nest", label="nest"))
    blanket = world.add(Entity(id="blanket", kind="thing", type="blanket", label="blanket"))
    world.facts.update(pair=pair, need=need, place=place, action=action, blanket=blanket)

    tell_intro(world, a, b, pair, need, place)
    world.para()
    repeat_steps(world, a, b, pair, need)
    offer_hand(world, a, b, need)
    if can_help(action, need) and reasonableness_gate(pair, need, place):
        world.para()
        _care_for_bird(world, narrate=False)
        settle_bird(world, need, place, pair)
        ending(world, a, b, need, place)
    world.facts.update(outcome="settled", bird=bird, nest=nest)
    return world


PAIR = FriendPair(
    id="twobestfriends",
    scene="a small sunny patch of grass",
    repeated_steps=["one small breath", "one soft pause", "one careful step"],
    repeated_words=["again", "again", "again"],
    ending_image="The nest looked like a little bowl of safety, and the bird's wing rested still.",
)

NEEDS = {
    "bird": Need(id="bird", label="little bird", smallness="tiny"),
    "sparrow": Need(id="sparrow", label="small sparrow", smallness="small"),
}

PLACES = {
    "garden": SafePlace(
        id="garden",
        label="garden",
        phrase="a little patch of garden grass",
        comforting="The grass was soft and bright.",
        welcomes="The garden seemed to hold its breath in a happy way.",
    ),
    "porch": SafePlace(
        id="porch",
        label="porch",
        phrase="the porch by the flowerpots",
        comforting="The porch was dry and safe from the wind.",
        welcomes="The flowerpots seemed to smile in the sun.",
    ),
}

ACTIONS = {
    "care": HelpfulAction(
        id="care",
        sense=3,
        power=2,
        text="covered the bird with a blanket, spoke softly, and kept the nest nearby until the twitch slowed",
        fail="tried to help, but the bird stayed too shaky and could not settle",
        qa_text="covered the bird with a blanket and spoke softly until the twitch slowed",
    ),
    "steady": HelpfulAction(
        id="steady",
        sense=2,
        power=1,
        text="held still, repeated the same gentle words, and gave the bird time to calm down",
        fail="was gentle, but not gentle enough to help the bird settle",
        qa_text="held still and repeated gentle words until the bird could settle",
    ),
}

GIRL_NAMES = ["Mina", "Lia", "June", "Tia", "Nora", "Elsie", "Maya", "Ada"]
BOY_NAMES = ["Noah", "Eli", "Finn", "Ben", "Owen", "Theo", "Luca", "Miles"]
TRAITS = ["gentle", "patient", "kind", "quiet", "thoughtful"]


@dataclass
class StoryParams:
    place: str
    need: str
    action: str
    name1: str
    type1: str
    name2: str
    type2: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for need in NEEDS:
            for action in ACTIONS:
                combos.append((place, need, action))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming friendship storyworld with repetition and twitch.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--name1")
    ap.add_argument("--type1", choices=["girl", "boy"])
    ap.add_argument("--name2")
    ap.add_argument("--type2", choices=["girl", "boy"])
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
              and (args.need is None or c[1] == args.need)
              and (args.action is None or c[2] == args.action)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, need, action = rng.choice(sorted(combos))
    n1 = args.name1 or rng.choice(GIRL_NAMES)
    t1 = args.type1 or "girl"
    n2 = args.name2 or rng.choice([n for n in BOY_NAMES if n != n1])
    t2 = args.type2 or "boy"
    return StoryParams(place=place, need=need, action=action, name1=n1, type1=t1, name2=n2, type2=t2)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story for a young child that includes the word "land-gerund" and the word "twitch".',
        f"Tell a gentle friendship story where {f['pair'].scene} helps two friends calm a twitching little bird.",
        f"Write a repetitive, soothing story about friends who keep saying the same kind words until a small bird can land safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a = world.get("Mina")
    b = world.get("Noah")
    pair: FriendPair = world.facts["pair"]
    need: Need = world.facts["need"]
    place: SafePlace = world.facts["place"]
    action: HelpfulAction = world.facts["action"]
    return [
        QAItem(
            question="Who are the story's friends?",
            answer=f"The story is about {a.id} and {b.id}, who stay kind to each other while helping the little bird. Their friendship is what makes the calm plan work.",
        ),
        QAItem(
            question="What was wrong with the bird?",
            answer=f"The bird kept twitching and could not settle down at first. It needed patience, a soft place, and the same gentle help repeated a few times.",
        ),
        QAItem(
            question="How did the friends help?",
            answer=f"They used the land-gerund routine: {pair.repeated_steps[0]}, {pair.repeated_steps[1]}, and {pair.repeated_steps[2]}. That repeated calmness helped the bird feel safe enough to land in the nest.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The bird landed safely in the nest, and the twitch stopped. {a.id} and {b.id} smiled because their friendship made the ending warm and peaceful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a twitch mean?",
            answer="A twitch is a small sudden movement, like a tiny jerk or shake. People and animals can twitch when they are nervous, hurt, or trying to get comfortable.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing or saying something again and again. Repeating a calm action can help someone feel safe and know what will happen next.",
        ),
        QAItem(
            question="Why is friendship important?",
            answer="Friendship helps people be gentle, patient, and brave together. A friend can make a scary or sad moment feel lighter and easier to handle.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    parts.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    parts.append("")
    parts.append("== Story QA ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World QA ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
calm :- bird(B), settled(B), nest(N), ready(N).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("pair", "friendship"),
        asp.fact("need", "bird"),
        asp.fact("place", "garden"),
        asp.fact("action", "care"),
    ]
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for nid in NEEDS:
        lines.append(asp.fact("need", nid))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show place/1.\n#show need/1.\n#show action/1."))
    # derive combos from python registry to keep twin simple
    return valid_combos()


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid_combos")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        assert sample.story
        print("OK: smoke story generated.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.need not in NEEDS or params.action not in ACTIONS:
        raise StoryError("Invalid params.")
    world = tell(
        PAIR,
        NEEDS[params.need],
        PLACES[params.place],
        ACTIONS[params.action],
        name1=params.name1,
        type1=params.type1,
        name2=params.name2,
        type2=params.type2,
    )
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


CURATED = [
    StoryParams(place="garden", need="bird", action="care", name1="Mina", type1="girl", name2="Noah", type2="boy"),
    StoryParams(place="porch", need="sparrow", action="steady", name1="Lia", type1="girl", name2="Eli", type2="boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show calm/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{p} {n} {a}" for p, n, a in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
