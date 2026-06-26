#!/usr/bin/env python3
"""
A small story world about an allergic spiral that ends in a happy, rhyming ending.

Seed tale:
A child loved a sweet snack at a little market, but a hidden ingredient made them
sneeze and worry. Their caregiver remembered a foreshadowed note from an earlier
flashback: check the label first. After a brief spiral of panic, they found a safe
treat with the same cheerful feel, and the day ended well.
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    allergic: bool = False
    safe: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    allergen: str
    safe_substitute: str
    rhyme_a: str
    rhyme_b: str


@dataclass
class StoryParams:
    place: str
    snack: str
    name: str
    gender: str
    caregiver: str
    seed: Optional[int] = None


PLACES = {
    "market": Place(id="market", label="the little market", indoors=True, affords={"buy_snack"}),
    "kitchen": Place(id="kitchen", label="the sunny kitchen", indoors=True, affords={"make_snack"}),
    "fair": Place(id="fair", label="the bright fair", indoors=False, affords={"buy_snack"}),
}

SNACKS = {
    "cookie": Snack(
        id="cookie",
        label="cookie",
        phrase="a crumbly honey cookie",
        allergen="nut",
        safe_substitute="oat cookie",
        rhyme_a="treat",
        rhyme_b="neat",
    ),
    "cupcake": Snack(
        id="cupcake",
        label="cupcake",
        phrase="a tiny vanilla cupcake",
        allergen="egg",
        safe_substitute="apple cake",
        rhyme_a="sweet",
        rhyme_b="treat",
    ),
    "candy": Snack(
        id="candy",
        label="candy",
        phrase="a shiny strawberry candy",
        allergen="milk",
        safe_substitute="sugar candy",
        rhyme_a="bright",
        rhyme_b="light",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Zoe", "Ruby"]
BOY_NAMES = ["Leo", "Ben", "Finn", "Max", "Noah", "Eli"]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


def rhyme_line(a: str, b: str) -> str:
    return f"{a} and {b}."


def _do_spiral(world: World, child: Entity, snack: Snack, narrate: bool = True) -> None:
    if "spiral" in world.fired:
        return
    world.fired.add("spiral")
    child.memes["panic"] = child.memes.get("panic", 0.0) + 1
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1
    if narrate:
        world.say(
            f"At first the joy got twirly and wild; {child.id} went pale, a worried little child."
        )


def _check_allergy(world: World, child: Entity, snack: Snack, narrate: bool = True) -> bool:
    if child.allergic and snack.allergen:
        if narrate:
            world.say(
                f"The label hid a tiny clue in sight: {snack.allergen} was there, tucked out of light."
            )
        return True
    return False


def _resolve(world: World, child: Entity, caregiver: Entity, snack: Snack, narrate: bool = True) -> None:
    if "resolve" in world.fired:
        return
    world.fired.add("resolve")
    child.memes["panic"] = 0.0
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    if narrate:
        world.say(
            f"{caregiver.id} said, 'Let's choose safe and right;' then found {snack.safe_substitute}, a merry, gentle bite."
        )
        world.say(
            f"{child.id} took the new snack, no sneeze, no fright; the cloudy, twisty moment turned cozy and bright."
        )


def tell(place: Place, snack: Snack, name: str, gender: str, caregiver_type: str) -> World:
    world = World(place)
    child = world.add(Entity(id=name, kind="character", type=gender, allergic=True))
    caregiver = world.add(Entity(id="Caregiver", kind="character", type=caregiver_type, label="the caregiver"))
    treat = world.add(Entity(id="Treat", type="snack", label=snack.label, phrase=snack.phrase, owner=child.id))
    safe = world.add(Entity(id="SafeTreat", type="snack", label=snack.safe_substitute, phrase=f"a safe {snack.safe_substitute}", owner=child.id, safe=True))

    world.say(
        f"{child.id} loved a sweet little bite; {snack.phrase} seemed cheery, round, and bright."
    )
    world.say(
        f"Long ago, in a flashback beam, {caregiver.id} had whispered, 'Read the label before the dream.'"
    )

    world.para()
    world.say(
        f"On a busy day at {place.label}, the snack was bought, all wrapped up neat;"
    )
    world.say(
        f"but a foreshadowing tickled the air: the bag's small print might hide a scare."
    )

    if _check_allergy(world, child, snack, narrate=True):
        _do_spiral(world, child, snack, narrate=True)
        world.say(
            f"{child.id} sniffled, then spun in a worryy whirl; the whole bright moment felt like a curl."
        )
        world.say(
            f"{caregiver.id} held {child.pronoun('object')} close and said, 'We can still share a happy ending pearl.'"
        )
        _resolve(world, child, caregiver, snack, narrate=True)
        world.say(
            f"So {child.id} ate the safe {safe.label} with a smile so wide; the sun in the window seemed to sing outside."
        )

    world.facts.update(
        child=child,
        caregiver=caregiver,
        snack=treat,
        safe=safe,
        snack_cfg=snack,
        place=place,
        allergic=True,
        resolved=True,
    )
    return world


def valid_combos() -> list[tuple[str, str]]:
    return [(p.id, s.id) for p in PLACES.values() for s in SNACKS.values()]


@dataclass
class _ParamsPack:
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="An allergic spiral with flashback, foreshadowing, and a happy ending.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--snack", choices=sorted(SNACKS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=["mother", "father"])
    ap.add_argument("--name")
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
    snack = args.snack or rng.choice(list(SNACKS))
    gender = args.gender or rng.choice(["girl", "boy"])
    caregiver = args.caregiver or rng.choice(["mother", "father"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, snack=snack, name=name, gender=gender, caregiver=caregiver)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    snack = f["snack_cfg"]
    place = f["place"]
    return [
        f'Write a rhyming story for a small child about {child.id} at {place.label} and a snack that turns out unsafe.',
        f'Tell a gentle flashback-and-foreshadowing story where a caregiver remembers to check a label before {child.id} eats {snack.phrase}.',
        f'Write a happy-ending story with a spiral of worry that ends with a safe {snack.safe_substitute}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    snack = f["snack_cfg"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {child.id}, a little {child.type} who had an allergy and went with {caregiver.label} to {place.label}.",
        ),
        QAItem(
            question=f"What made {child.id} worry?",
            answer=f"The snack had {snack.allergen} in it, so it could make {child.id} sneeze and feel unwell.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily when {child.id} ate {snack.safe_substitute} instead, and the scary moment turned into a calm smile.",
        ),
        QAItem(
            question=f"What did the caregiver remember in the flashback?",
            answer=f"{caregiver.label.capitalize()} remembered to check the label first, because that was the safe and smart way to avoid trouble.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to be allergic?",
            answer="Being allergic means a person's body can react badly to something, like food, dust, or pollen.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when the story briefly goes back to an earlier moment to remember something important.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue early in a story that hints something important may happen later.",
        ),
        QAItem(
            question="Why can checking a label help?",
            answer="Checking a label helps because it shows what is inside the food, which can keep someone safe from an allergy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"  place={world.place.label}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
snack(S) :- snack_item(S).
allergic_spiral(P,S) :- place(P), snack(S), unsafe(S).
happy_ending(P,S) :- allergic_spiral(P,S), safe_substitute(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for sid, snack in SNACKS.items():
        lines.append(asp.fact("snack_item", sid))
        lines.append(asp.fact("unsafe", sid))
        lines.append(asp.fact("safe_substitute", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_ending/2."))
    atoms = set(asp.atoms(model, "happy_ending"))
    py = {(p, s) for p, s in valid_combos()}
    if atoms == py:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos().")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], SNACKS[params.snack], params.name, params.gender, params.caregiver)
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
    StoryParams(place="market", snack="cookie", name="Mia", gender="girl", caregiver="mother"),
    StoryParams(place="kitchen", snack="cupcake", name="Leo", gender="boy", caregiver="father"),
    StoryParams(place="fair", snack="candy", name="Ruby", gender="girl", caregiver="mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show happy_ending/2."))
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
