#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/bend_interpret_happy_ending_friendship_bedtime_story.py
====================================================================================================

A small standalone storyworld for a bedtime-story friendship tale.

Premise:
- Two friends get ready for bed, but a small mix-up leaves one of them worried.
- They must bend something gentle and interpret a clue to finish the night well.

The story keeps close to a bedtime-story feel: soft light, a cozy room,
friendship, a small tension, and a happy ending image that shows what changed.

The domain deliberately uses the seed words:
- bend
- interpret

and the requested features:
- Happy Ending
- Friendship
- Bedtime Story style
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: str = ""
    helper: str = ""
    made_of: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def name(self) -> str:
        return self.label or self.id
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    cozy: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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
class BedtimeItem:
    id: str
    label: str
    phrase: str
    can_bend: bool = False
    can_hint: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    place: str = "bedroom"
    item: str = "paper_moon"
    clue: str = "moon_note"
    name_a: str = "Mia"
    type_a: str = "girl"
    name_b: str = "Noah"
    type_b: str = "boy"
    caregiver: str = "mother"
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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


def _r_find_clue(world: World) -> list[str]:
    out: list[str] = []
    reader = world.get("A")
    clue = world.get("clue")
    if reader.memes.get("interpret", 0.0) < THRESHOLD:
        return out
    sig = ("find_clue",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("toy").meters["found"] = 1.0
    clue.meters["understood"] = 1.0
    out.append("The little clue made sense at last.")
    return out


CAUSAL_RULES = [Rule("find_clue", "soft", _r_find_clue)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    return [("bedroom", "paper_moon", "moon_note")]


def explain_rejection() -> str:
    return "(No story: this little bedtime world only supports the cozy moon-note setup.)"


def bedtime_setup(world: World, a: Entity, b: Entity, item: BedtimeItem, clue: BedtimeItem) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"At bedtime, {a.id} and {b.id} shared the soft glow of a nightlight in the bedroom. "
        f"They were friends who liked to whisper and listen for sleepy sounds."
    )
    world.say(
        f"On the rug, they found {item.phrase} and a small {clue.label}. "
        f"It looked like the sort of thing that needed a careful look."
    )


def worry(world: World, a: Entity, b: Entity, item: BedtimeItem, clue: BedtimeItem) -> None:
    a.memes["worry"] += 1
    world.say(
        f"{a.id} frowned a little. The {item.label} had a corner that wanted to bend, "
        f"and the {clue.label} was hard to interpret in the dim light."
    )
    world.say(
        f"{b.id} leaned closer and said they could interpret it together instead of guessing."
    )


def bend(world: World, a: Entity, item: BedtimeItem) -> None:
    a.memes["care"] += 1
    if item.can_bend:
        world.say(
            f"With gentle fingers, {a.id} chose to bend the paper corner just enough to make a tidy moon shape."
        )
        world.get("item").meters["bent"] = 1.0


def interpret(world: World, b: Entity, clue: BedtimeItem) -> None:
    b.memes["interpret"] += 1
    clue_ent = world.get("clue")
    clue_ent.meters["read"] = 1.0
    world.say(
        f"{b.id} took a breath and tried to interpret the little note. "
        f"It was a bedtime picture, not a problem."
    )
    propagate(world, narrate=True)


def resolve(world: World, a: Entity, b: Entity, item: BedtimeItem, clue: BedtimeItem) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f"Then the note made sense: it pointed to the bed, where the missing {item.label} had slipped."
    )
    world.say(
        f"{a.id} and {b.id} tucked it back in place, smiled at each other, and felt the whole room get calmer."
    )
    world.say(
        f"At last, the bedroom was snug again, with the bent little moon set right and the friends ready to sleep."
    )


def tell(place: Place, item: BedtimeItem, clue: BedtimeItem,
         name_a: str, type_a: str, name_b: str, type_b: str, caregiver: str) -> World:
    world = World(place)
    a = world.add(Entity(id="A", kind="character", type=type_a, label=name_a, traits=["gentle"]))
    b = world.add(Entity(id="B", kind="character", type=type_b, label=name_b, traits=["kind"]))
    parent = world.add(Entity(id="Caregiver", kind="character", type=caregiver, label="the caregiver"))
    item_ent = world.add(Entity(id="item", type="thing", label=item.label, phrase=item.phrase, owner=a.id, meters={}))
    clue_ent = world.add(Entity(id="clue", type="thing", label=clue.label, phrase=clue.phrase, meters={}))
    toy = world.add(Entity(id="toy", type="thing", label="the toy", meters={}))

    world.facts.update(place=place, item=item, clue=clue, a=a, b=b, parent=parent)

    bedtime_setup(world, a, b, item, clue)
    world.para()
    worry(world, a, b, item, clue)
    bend(world, a, item)
    interpret(world, b, clue)
    world.para()
    resolve(world, a, b, item, clue)

    world.facts.update(item_ent=item_ent, clue_ent=clue_ent, toy=toy)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b, item = f["a"], f["b"], f["item"]
    return [
        f'Write a bedtime story about friendship that uses the words "bend" and "interpret".',
        f"Tell a cozy story where {a.name} and {b.name} must interpret a small clue before bed and bend one gentle paper shape.",
        f"Write a short happy ending story for children about two friends in a bedroom, a moon note, and a kind bedtime fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, item, clue = f["a"], f["b"], f["item"], f["clue"]
    return [
        QAItem(
            question=f"Who shared the bedtime moment in the bedroom?",
            answer=f"{a.name} and {b.name} shared the bedtime moment as friends. They stayed close, listened carefully, and helped each other feel safe.",
        ),
        QAItem(
            question=f"What did {a.name} need to do with the paper moon?",
            answer=f"{a.name} needed to bend the paper moon gently. The bend was small and careful, so it helped the story feel tidy instead of messy.",
        ),
        QAItem(
            question=f"Why did {b.name} try to interpret the little note?",
            answer=f"{b.name} tried to interpret the little note because it was hard to read in the dim room. Once the meaning was clear, they could solve the bedtime mix-up together.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the missing {item.label} was back where it belonged and the room felt calm again. The friends ended the night smiling, which shows the happy ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to bend something?",
            answer="To bend something means to shape it a little without breaking it. A gentle bend can make paper curve or turn.",
        ),
        QAItem(
            question="What does it mean to interpret a note?",
            answer="To interpret a note means to understand what it is trying to say. Sometimes you read slowly, look closely, and then the message becomes clear.",
        ),
        QAItem(
            question="What is a friendship story?",
            answer="A friendship story is a story about people who care about each other and help one another. Friendly stories often end with kindness and peace.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
found_clue :- interpret(B), clue(C), bend(A), bedroom.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("bedroom"),
            asp.fact("bend"),
            asp.fact("interpret"),
            asp.fact("clue"),
            asp.fact("friendship"),
            asp.fact("happy_ending"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show found_clue/0."))
    asp_ok = bool(model)
    py_ok = True
    sample = generate(resolve_params(argparse.Namespace(place=None, item=None, clue=None, name_a=None, type_a=None, name_b=None, type_b=None, caregiver=None), random.Random(1)))
    py_ok = "happy" in sample.story.lower()
    smoke = True
    try:
        emit(sample, trace=False, qa=False)
    except Exception:
        smoke = False
    if asp_ok and py_ok and smoke:
        print("OK: ASP, generation, and smoke test passed.")
        return 0
    print(f"FAIL: asp_ok={asp_ok} py_ok={py_ok} smoke={smoke}")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cozy bedtime friendship storyworld.")
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--item", choices=list(ITEMS))
    ap.add_argument("--clue", choices=list(CLUES))
    ap.add_argument("--name-a")
    ap.add_argument("--type-a", choices=["girl", "boy"])
    ap.add_argument("--name-b")
    ap.add_argument("--type-b", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=["mother", "father"])
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
    if args.place and args.place not in PLACES:
        raise StoryError("invalid place")
    if args.item and args.item not in ITEMS:
        raise StoryError("invalid item")
    if args.clue and args.clue not in CLUES:
        raise StoryError("invalid clue")
    if not combos:
        raise StoryError(explain_rejection())
    place, item, clue = rng.choice(combos)
    return StoryParams(
        place=args.place or place,
        item=args.item or item,
        clue=args.clue or clue,
        name_a=args.name_a or rng.choice(GIRL_NAMES),
        type_a=args.type_a or "girl",
        name_b=args.name_b or rng.choice(BOY_NAMES),
        type_b=args.type_b or "boy",
        caregiver=args.caregiver or rng.choice(["mother", "father"]),
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if (params.place, params.item, params.clue) not in valid_combos():
        raise StoryError(explain_rejection())
    world = tell(PLACES[params.place], ITEMS[params.item], CLUES[params.clue],
                 params.name_a, params.type_a, params.name_b, params.type_b, params.caregiver)
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
        print(asp_program("#show found_clue/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:", valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p in [StoryParams(place="bedroom", item="paper_moon", clue="moon_note")]:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)
            i += 1

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


PLACES = {"bedroom": Place(id="bedroom", label="the bedroom", cozy=True)}
ITEMS = {"paper_moon": BedtimeItem(id="paper_moon", label="paper moon", phrase="a paper moon", can_bend=True, tags={"bend"})}
CLUES = {"moon_note": BedtimeItem(id="moon_note", label="moon note", phrase="a small moon note", can_hint=True, tags={"interpret"})}
GIRL_NAMES = ["Mia", "Luna", "Ivy", "Nina", "Eden"]
BOY_NAMES = ["Noah", "Leo", "Owen", "Theo", "Finn"]


if __name__ == "__main__":
    main()
