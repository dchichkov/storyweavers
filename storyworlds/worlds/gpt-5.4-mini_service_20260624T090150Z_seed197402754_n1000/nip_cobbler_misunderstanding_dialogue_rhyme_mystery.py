#!/usr/bin/env python3
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    kind: str
    reveal: str
    meter: str


@dataclass
class StoryParams:
    place: str
    clue: str
    hero_name: str
    hero_type: str
    cobbler_name: str
    seed: Optional[int] = None


PLACES = {
    "shop": Place("shop", "the cobbler shop", True, {"find", "ask", "sort"}),
    "lane": Place("lane", "the narrow lane", False, {"find", "ask", "sort"}),
    "porch": Place("porch", "the porch", False, {"find", "ask", "sort"}),
}

CLUES = {
    "nip": Clue("nip", "a nip of cold air", "weather", "the open door had stayed cracked", "chill"),
    "mudprint": Clue("mudprint", "a muddy print", "footprint", "the print matched a little boot", "muddy"),
    "thread": Clue("thread", "a bright thread", "fiber", "the thread came from a ribbon", "bright"),
}

HEROES = ["Mina", "Toby", "Lena", "Owen", "Pip", "Nora"]
COBBLERS = ["Mr. Cobb", "Mrs. Cobb", "Cob", "Mister Lark", "Aunt Tilly"]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def tell(place: Place, clue: Clue, hero_name: str, hero_type: str, cobbler_name: str) -> World:
    w = World(place)
    hero = w.add(Entity(hero_name, kind="character", type=hero_type, label=hero_name, meters={}, memes={"curious": 1.0}))
    cobbler = w.add(Entity(cobbler_name, kind="character", type="cobbler", label=cobbler_name, meters={}, memes={"worry": 1.0}))
    shoe = w.add(Entity("shoe", type="shoe", label="shoe", phrase="the missing shoe"))
    key = w.add(Entity("key", type="key", label="key", phrase="the little brass key"))
    shop_sign = w.add(Entity("sign", type="sign", label="sign", phrase="the shop sign"))

    hero.memes["curious"] += 1
    w.say(f"{hero.id} came to {place.label} where {cobbler.label} was mending shoes.")
    w.say(f"A small mystery waited there, because {cobbler.label} could not find {shoe.phrase}.")

    w.para()
    if clue.id == "nip":
        hero.meters["chill"] = 1.0
        w.say(f"A nip of cold air slipped in when the door opened.")
        w.say(f"{hero.id} said, \"Did a fox nibble the shoe away?\"")
        w.say(f"{cobbler.label} shook {cobbler.pronoun('possessive')} head. \"No nibble, no fox. Just a draft and a missing latch.\"")
    elif clue.id == "mudprint":
        hero.meters["muddy"] = 1.0
        w.say(f"There was a muddy print by the bench.")
        w.say(f"{hero.id} whispered, \"A thief in boots!\"")
        w.say(f"{cobbler.label} pointed at the pattern. \"It is too small for a thief. I think it is from the delivery pup.\"")
    else:
        hero.meters["bright"] = 1.0
        w.say(f"A bright thread caught on a nail near the counter.")
        w.say(f"{hero.id} said, \"That looks like a clue from a dress.\"")
        w.say(f"{cobbler.label} smiled. \"Maybe. Or maybe it came from the ribbon tied around the key.\"")

    w.para()
    hero.memes["misunderstanding"] = 1.0
    cobbler.memes["misunderstanding"] = 1.0
    w.say(f"They spoke in circles for a moment, because the clue felt larger than it was.")
    w.say(f"Then {hero.id} looked under the stool and saw {key.phrase} shining where the shadow was thin.")
    w.say(f"{hero.id} said, \"So the shoe was not stolen at all?\"")
    w.say(f"{cobbler.label} laughed softly. \"No, dear one. The key had been hiding it behind the curtain.\"")

    w.para()
    hero.memes["joy"] = 1.0
    cobbler.memes["worry"] = 0.0
    w.say(f"Together they moved the curtain, and there was {shoe.phrase}, neat and safe.")
    w.say(f"{cobbler.label} slipped the shoe back into a box, and {hero.id} grinned at the tidy little answer.")
    w.say(f"The mystery ended not with a chase, but with a clear clue, a better guess, and a quiet laugh.")

    w.facts.update(
        hero=hero,
        cobbler=cobbler,
        place=place,
        clue=clue,
        shoe=shoe,
        key=key,
        sign=shop_sign,
        resolved=True,
        misunderstanding=True,
    )
    return w


def generation_prompts(w: World) -> list[str]:
    f = w.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    cobbler: Entity = f["cobbler"]  # type: ignore[assignment]
    clue: Clue = f["clue"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    return [
        f'Write a short mystery story for a child that includes the words "nip" and "cobbler".',
        f"Tell a gentle story where {hero.id} visits {place.label} and misunderstands a clue while speaking with {cobbler.label}.",
        f"Write a simple rhyme-touched mystery about a small clue, a cobbler, and a careful ending at {place.label}.",
    ]


def story_qa(w: World) -> list[QAItem]:
    f = w.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    cobbler: Entity = f["cobbler"]  # type: ignore[assignment]
    clue: Clue = f["clue"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Where did {hero.id} go to help with the mystery?",
            answer=f"{hero.id} went to {place.label} to talk with {cobbler.label} and look for the missing shoe.",
        ),
        QAItem(
            question=f"What clue first made {hero.id} guess the wrong thing?",
            answer=f"The clue was {clue.label}. It made {hero.id} think something dramatic had happened, but it turned out to mean something small and ordinary.",
        ),
        QAItem(
            question=f"What did {hero.id} and {cobbler.label} find at the end?",
            answer=f"They found the missing shoe hiding behind the curtain, and that solved the little mystery.",
        ),
    ]


def world_knowledge_qa(w: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a cobbler do?",
            answer="A cobbler repairs shoes and helps keep them neat, sturdy, and ready to wear.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps someone solve a puzzle or mystery.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks a clue means one thing, but it really means something else.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like light and night.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(w: World) -> str:
    lines = ["--- world model state ---"]
    for e in w.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="shop", clue="nip", hero_name="Mina", hero_type="girl", cobbler_name="Mr. Cobb"),
    StoryParams(place="lane", clue="mudprint", hero_name="Toby", hero_type="boy", cobbler_name="Mrs. Cobb"),
    StoryParams(place="porch", clue="thread", hero_name="Nora", hero_type="girl", cobbler_name="Aunt Tilly"),
]


def valid_combos() -> list[tuple[str, str]]:
    return [(p.id, c.id) for p in PLACES.values() for c in CLUES.values()]


def explain_rejection(place: str, clue: str) -> str:
    return f"(No story: the combination {place!r} and {clue!r} does not make a good little mystery.)"


ASP_RULES = r"""
place(P) :- place_fact(P).
clue(C) :- clue_fact(C).
valid(P, C) :- place(P), clue(C).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place_fact", p.id))
    for c in CLUES.values():
        lines.append(asp.fact("clue_fact", c.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-sized mystery about a cobbler, a nip, and a misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--cobbler")
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
    place = args.place or rng.choice(list(PLACES))
    clue = args.clue or rng.choice(list(CLUES))
    if (place, clue) not in valid_combos():
        raise StoryError(explain_rejection(place, clue))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HEROES)
    cobbler_name = args.cobbler or rng.choice(COBBLERS)
    return StoryParams(place=place, clue=clue, hero_name=hero_name, hero_type=gender, cobbler_name=cobbler_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], CLUES[params.clue], params.hero_name, params.hero_type, params.cobbler_name)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid place/clue combos:\n")
        for p, c in combos:
            print(f"  {p:6} {c}")
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
            i += 1
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
