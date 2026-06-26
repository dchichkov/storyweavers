#!/usr/bin/env python3
"""
A small folk-tale storyworld about fluency, sharing, rhyme, and a lesson learned.

Premise:
A child wants to speak a rhyme fluently at the village fire, but the words keep
tumbling. A helper offers to share the rhyme cards. The child learns that
sharing and practice can make speech smooth and bright.

The world model tracks:
- physical meters: carried, scattered, gathered, warmth, distance
- emotional memes: confidence, worry, patience, joy, pride

The story is generated from a simulated sequence:
1) setup the child, elder, rhyme cards, and setting
2) the child tries to speak but stumbles
3) the elder shares the cards and teaches a pattern
4) the child practices, becomes fluent, and learns the lesson
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Person:
    id: str
    role: str
    name: str
    kind: str = "character"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "she", "object": "her", "possessive": "her"}[case]

    @property
    def short(self) -> str:
        return self.name


@dataclass
class Thing:
    id: str
    label: str
    kind: str = "thing"
    owner: Optional[str] = None
    shared_with: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str
    warmth: str
    supports_rhyme: bool = True


@dataclass
class StoryParams:
    child_name: str
    elder_name: str
    place: str
    seed: Optional[int] = None


GIRL_NAMES = ["Mira", "Lina", "Asha", "Nina", "Tala", "Rani"]
ELDER_NAMES = ["Grandmother June", "Aunt Wren", "Old Moss", "Gran Reed"]

PLACES = {
    "firepit": Place(name="the village fire", warmth="warm"),
    "porch": Place(name="the porch by the river", warmth="soft"),
    "oak": Place(name="the big oak tree", warmth="cool"),
}

RHYMES = {
    "sparrow": {
        "title": "sparrow song",
        "line": "A sparrow stitched a song in the sky",
        "lesson": "when words are shared kindly, they fly more easily",
    },
    "lantern": {
        "title": "lantern verse",
        "line": "A lantern glowed for all to see",
        "lesson": "helping with words can help a voice grow brave",
    },
    "river": {
        "title": "river chant",
        "line": "The river ran and rang all day",
        "lesson": "practice and sharing can turn stumbles into song",
    },
}


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, object] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _meter(ent, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _mem(ent, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _set(ent, key: str, val: float) -> None:
    ent.meters[key] = val


def _add_meter(ent, key: str, inc: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + inc


def _add_mem(ent, key: str, inc: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + inc


def create_story_world(params: StoryParams, rng: random.Random) -> tuple[World, Person, Person, Thing, dict]:
    place = PLACES[params.place]
    world = World(place)

    child = world.add(Person(
        id="child",
        role="child",
        name=params.child_name,
        meters={"fluent_progress": 0.0, "stumble": 0.0},
        memes={"confidence": 0.0, "worry": 1.0, "joy": 0.0, "pride": 0.0},
    ))
    elder = world.add(Person(
        id="elder",
        role="elder",
        name=params.elder_name,
        meters={"gathering": 0.0},
        memes={"patience": 1.0, "joy": 0.0},
    ))
    rhyme_key = rng.choice(sorted(RHYMES))
    rhyme = RHYMES[rhyme_key]
    cards = world.add(Thing(
        id="rhyme_cards",
        label=f"cards for the {rhyme['title']}",
        owner=elder.id,
        shared_with=[],
        meters={"scattered": 1.0, "gathered": 0.0},
    ))
    world.facts.update(rhyme_key=rhyme_key, rhyme=rhyme, child=child, elder=elder, cards=cards)
    return world, child, elder, cards, rhyme


def speak_attempt(world: World, child: Person, rhyme: dict) -> None:
    if ("stumble", child.id) in world.fired:
        return
    world.fired.add(("stumble", child.id))
    _add_mem(child, "worry", 1.0)
    _add_meter(child, "stumble", 1.0)
    world.say(
        f"{child.short} stood by {world.place.name} and tried to say the rhyme, "
        f"but the words bumped like pebbles in a pocket."
    )
    world.say(
        f"{child.short} wanted the line to sound smooth: “{rhyme['line']}”"
    )


def share_cards(world: World, elder: Person, child: Person, cards: Thing) -> None:
    if ("share", cards.id) in world.fired:
        return
    world.fired.add(("share", cards.id))
    cards.shared_with.append(child.id)
    cards.meters["gathered"] = 1.0
    cards.meters["scattered"] = 0.0
    _add_mem(elder, "joy", 1.0)
    _add_mem(child, "joy", 1.0)
    _add_mem(child, "confidence", 1.0)
    world.say(
        f"{elder.short} smiled and shared the rhyme cards with {child.short}, "
        f"so the words could be held one by one."
    )


def teach_pattern(world: World, elder: Person, child: Person, rhyme: dict) -> None:
    if ("teach", rhyme["title"]) in world.fired:
        return
    world.fired.add(("teach", rhyme["title"]))
    _add_mem(child, "confidence", 1.0)
    _add_mem(child, "worry", -0.5)
    world.say(
        f"{elder.short} tapped the cards in a soft beat and said, "
        f"“Slow feet, steady breath, clear mouth.”"
    )
    world.say(
        f"Then {elder.short} spoke the line again, and {child.short} copied the rhythm."
    )


def practice_until_fluent(world: World, child: Person, rhyme: dict) -> None:
    if ("fluent", child.id) in world.fired:
        return
    world.fired.add(("fluent", child.id))
    _add_meter(child, "fluent_progress", 1.0)
    _add_mem(child, "confidence", 2.0)
    _add_mem(child, "pride", 1.0)
    _add_mem(child, "worry", -1.0)
    world.say(
        f"{child.short} tried again, and this time the words came in order like ducks behind a mother duck."
    )
    world.say(
        f"At last, {child.short} said the whole rhyme fluently: “{rhyme['line']}”"
    )


def lesson_learned(world: World, child: Person, elder: Person, rhyme: dict) -> None:
    if ("lesson", child.id) in world.fired:
        return
    world.fired.add(("lesson", child.id))
    world.say(
        f"{child.short} grinned at {elder.short} and learned that sharing a rhyme can make speech braver, "
        f"not smaller."
    )
    world.say(
        f"The lesson stayed bright in {child.short}'s chest: when words are shared kindly, they can find their way."
    )


def tell(params: StoryParams, rng: random.Random) -> World:
    world, child, elder, cards, rhyme = create_story_world(params, rng)

    world.say(
        f"Once, by {world.place.name}, there lived {child.short}, a child who loved to speak in rhyme."
    )
    world.say(
        f"{child.short} had been practicing the {rhyme['title']}, because {child.short} wanted the words to come out with fluency."
    )
    world.para()

    speak_attempt(world, child, rhyme)
    world.say(
        f"{child.short} looked down at the dusty path and felt the worry get bigger."
    )
    world.para()

    share_cards(world, elder, child, cards)
    teach_pattern(world, elder, child, rhyme)
    practice_until_fluent(world, child, rhyme)
    lesson_learned(world, child, elder, rhyme)

    world.para()
    world.say(
        f"By dusk, the fire glowed low and kind, and {child.short} could say the rhyme without tripping."
    )
    world.say(
        f"{elder.short} kept smiling, because the best kind of lesson was the one that sounded like a song."
    )

    world.facts.update(
        child=child,
        elder=elder,
        cards=cards,
        place=world.place,
        rhyme=rhyme,
        fluent=True,
    )
    return world


def _name_pool(child_gender: str = "girl") -> list[str]:
    return GIRL_NAMES if child_gender == "girl" else GIRL_NAMES + ["Pip", "Rowan"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    place = args.place or rng.choice(list(PLACES))
    child_name = args.name or rng.choice(_name_pool())
    elder_name = args.elder or rng.choice(ELDER_NAMES)
    return StoryParams(child_name=child_name, elder_name=elder_name, place=place, seed=None)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    rhyme = f["rhyme"]
    place = f["place"].name
    return [
        f'Write a short folk tale about fluency, sharing, and rhyme at {place}.',
        f"Tell a gentle story where {child.short} stumbles over a rhyme, {elder.short} shares the cards, and the child learns a lesson.",
        f"Write a child-friendly tale that ends with the words coming out fluently after a kind act of sharing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    rhyme = f["rhyme"]
    place = f["place"].name
    return [
        QAItem(
            question=f"Who wanted to speak the rhyme fluently by {place}?",
            answer=f"{child.short} wanted to speak the {rhyme['title']} fluently by {place}.",
        ),
        QAItem(
            question=f"What did {elder.short} share with {child.short}?",
            answer=f"{elder.short} shared the rhyme cards with {child.short} so the words could be practiced one by one.",
        ),
        QAItem(
            question=f"What lesson did {child.short} learn?",
            answer=f"{child.short} learned that sharing and steady practice can help words become fluent.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does fluency mean in speaking?",
            answer="Fluency means speaking smoothly and without many stops or stumbles.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means giving another person some of what you have, or letting them use it too.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a bit of language or a song where the sounds repeat in a pleasing way.",
        ),
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
    for e in world.entities.values():
        meters = getattr(e, "meters", {})
        memes = getattr(e, "memes", {})
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if getattr(e, "label", ""):
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A rhyme is shared when a child gets access to the elder's cards.
shared(Child, Cards) :- owns(Elder, Cards), gives(Elder, Child, Cards).

% Fluency grows when a child practices after sharing and teaching.
fluent(Child) :- shared(Child, Cards), teaches(_, Child, Cards), practices(Child, Cards).

% A lesson is learned when fluent speech follows kindness.
lesson_learned(Child) :- fluent(Child), kindness(shared).

#show shared/2.
#show fluent/1.
#show lesson_learned/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("kindness", "shared"))
    for rid in RHYMES:
        lines.append(asp.fact("rhyme", rid))
    for pname, place in PLACES.items():
        lines.append(asp.fact("place", pname))
        if place.supports_rhyme:
            lines.append(asp.fact("supports_rhyme", pname))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show lesson_learned/1.\n#show fluent/1.\n#show shared/2."))
    atoms = set((sym.name, len(sym.arguments), tuple(a.name if a.type == a.type.Function else getattr(a, 'string', getattr(a, 'number', None)) for a in sym.arguments)) for sym in model)
    expected = {("shared", 2, ("Child", "Cards")), ("fluent", 1, ("Child",)), ("lesson_learned", 1, ("Child",))}
    if atoms != expected:
        print("MISMATCH between ASP and Python gate.")
        print("  ASP:", sorted(atoms))
        print("  PY :", sorted(expected))
        return 1
    print("OK: ASP twin is consistent with the storyworld gate.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about fluency, sharing, rhyme, and a lesson learned.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--name")
    ap.add_argument("--elder")
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


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed)
    world = tell(params, rng)
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
    StoryParams(child_name="Mira", elder_name="Grandmother June", place="firepit"),
    StoryParams(child_name="Asha", elder_name="Aunt Wren", place="porch"),
    StoryParams(child_name="Tala", elder_name="Old Moss", place="oak"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show shared/2.\n#show fluent/1.\n#show lesson_learned/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
