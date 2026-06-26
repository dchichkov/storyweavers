#!/usr/bin/env python3
"""
A standalone fairy-tale storyworld about a lodge, a bit of currency, and a
bottle of cologne that causes a misunderstanding before sharing heals the
conflict.

Seed premise:
- A child in a lodge notices a treasured bottle of cologne and a small pouch of
  currency.
- A misunderstanding makes two friends think the other is being selfish.
- They talk it through, share the currency and the cologne carefully, and the
  lodge feels warm again.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    room: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "fairy"}
        male = {"boy", "father", "man", "king", "elf"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str
    room: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class SharedGood:
    id: str
    label: str
    phrase: str
    type: str
    room: str
    use: str
    plural: bool = False


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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    hero: str
    companion: str
    gender: str
    seed: Optional[int] = None


PLACES = {
    "lodge": Place(name="the lodge", mood="warm", affords={"rest", "share", "talk"}),
}

HERO_NAMES = ["Mina", "Tessa", "Lina", "Pia", "Nora"]
COMPANION_NAMES = ["Bram", "Eli", "Jon", "Otto", "Finn"]

CURRENCY = Item(
    id="coins",
    label="currency",
    phrase="a small pouch of shiny currency",
    type="currency",
    room="table",
    plural=True,
)
COLOGNE = SharedGood(
    id="cologne",
    label="cologne",
    phrase="a tiny bottle of sweet cologne",
    type="cologne",
    room="mantel",
    use="make the room smell lovely",
)

ARTIFACTS = {
    "currency": CURRENCY,
    "cologne": COLOGNE,
}

TRAITS = ["kind", "curious", "gentle", "brave", "careful"]


def _canon(text: str) -> str:
    return text.strip().lower().replace(" ", "_")


def valid_story() -> bool:
    return True


def explain_invalid(msg: str) -> str:
    return f"(No story: {msg})"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld: a lodge, currency, cologne, conflict, misunderstanding, sharing."
    )
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--hero")
    ap.add_argument("--companion")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    place = args.place or "lodge"
    hero = args.hero or rng.choice(HERO_NAMES)
    companion = args.companion or rng.choice([n for n in COMPANION_NAMES if n != hero])
    gender = args.gender or rng.choice(["girl", "boy"])
    return StoryParams(place=place, hero=hero, companion=companion, gender=gender)


def tell(params: StoryParams) -> World:
    world = World(PLACES[params.place])

    hero = world.add(Entity(id=params.hero, kind="character", type=params.gender))
    companion_type = "boy" if params.gender == "girl" else "girl"
    companion = world.add(Entity(id=params.companion, kind="character", type=companion_type))

    coins = world.add(Entity(
        id="currency",
        type="currency",
        label="currency",
        phrase="a small pouch of shiny currency",
        owner=hero.id,
        caretaker=companion.id,
        room="table",
        plural=True,
    ))
    cologne = world.add(Entity(
        id="cologne",
        type="cologne",
        label="cologne",
        phrase="a tiny bottle of sweet cologne",
        owner=companion.id,
        caretaker=hero.id,
        room="mantel",
    ))

    hero.memes["love"] = 1.0
    companion.memes["love"] = 1.0

    world.say(f"In {world.place.name}, little {hero.id} lived with {companion.id}, and the lodge smelled of pine and bread.")
    world.say(f"One dusk, {hero.id} found {coins.phrase} beside {cologne.phrase}.")
    world.say(f"{hero.id} liked the bright currency, and {companion.id} liked the cologne because it made the room feel magical.")

    world.para()
    hero.memes["desire"] = 1.0
    companion.memes["desire"] = 1.0
    hero.memes["misunderstanding"] = 1.0
    companion.memes["misunderstanding"] = 1.0
    hero.memes["conflict"] = 1.0
    companion.memes["conflict"] = 1.0

    world.say(f"At supper, {hero.id} reached for the currency to buy honey cakes, but {companion.id} thought {hero.id} meant to keep it all.")
    world.say(f"Then {companion.id} picked up the cologne to help the lodge smell sweet, and {hero.id} thought {companion.id} was hiding the bottle away forever.")
    world.say("So the two friends frowned at each other, and the lodge grew quiet.")

    world.para()
    hero.memes["curiosity"] = 1.0
    companion.memes["curiosity"] = 1.0
    world.say(f"At last, {hero.id} asked a careful question, and {companion.id} did too.")
    world.say(f"They learned the truth: the currency was for sharing treats, and the cologne was for sharing the room's warm scent.")
    world.say(f"Neither had wanted to be selfish; they had only misunderstood each other.")

    world.say(f"Then they shared the currency and bought honey cakes together.")
    world.say(f"They also shared the cologne by opening the bottle for one tiny spritz near the hearth, just enough to make the lodge glow softly.")
    hero.memes["joy"] = 1.0
    companion.memes["joy"] = 1.0
    hero.memes["conflict"] = 0.0
    companion.memes["conflict"] = 0.0
    hero.memes["misunderstanding"] = 0.0
    companion.memes["misunderstanding"] = 0.0
    world.say(f"By bedtime, {hero.id} and {companion.id} were laughing side by side, and the lodge felt kind again.")

    world.facts = {
        "hero": hero,
        "companion": companion,
        "coins": coins,
        "cologne": cologne,
        "place": world.place.name,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story about a lodge, currency, and cologne where {f["hero"].id} and {f["companion"].id} misunderstand each other.',
        f'Write a gentle children\'s story set in {f["place"]} that ends with sharing and a happy ending.',
        "Tell a short fairy tale in which a small mistake about money and a perfume bottle is solved by talking kindly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    return [
        QAItem(
            question=f"Where did {hero.id} and {companion.id} live?",
            answer=f"They lived in {f['place']}, where the air smelled like pine and bread.",
        ),
        QAItem(
            question=f"What did the two friends misunderstand about the currency and the cologne?",
            answer="They each thought the other was keeping the shared things for themselves, but neither one meant to be selfish.",
        ),
        QAItem(
            question=f"How did they fix the conflict?",
            answer="They asked careful questions, learned the truth, and decided to share both the currency and the cologne.",
        ),
        QAItem(
            question=f"What happened at the end of the story?",
            answer=f"{hero.id} and {companion.id} laughed together, ate honey cakes, and the lodge felt warm and peaceful again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is currency?",
            answer="Currency is money people use to trade for things they want or need.",
        ),
        QAItem(
            question="What is cologne?",
            answer="Cologne is a light-smelling liquid people wear or use to make a room smell nice.",
        ),
        QAItem(
            question="What is a lodge?",
            answer="A lodge is a home or resting place, often a cozy house in the woods or near a camp.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use or enjoy something too.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.room:
            bits.append(f"room={e.room}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
% A story is reasonable when the lodge setting exists, both shared goods exist,
% and the ending includes conflict, misunderstanding, and sharing.
reasonably_story(lodge, currency, cologne).

has_conflict(S) :- story(S), feature(S, conflict).
has_misunderstanding(S) :- story(S), feature(S, misunderstanding).
has_sharing(S) :- story(S), feature(S, sharing).

valid_story(S) :- story(S), has_conflict(S), has_misunderstanding(S), has_sharing(S), reasonably_story(lodge, currency, cologne).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("story", "fairy_lodge_currency_cologne")]
    lines.append(asp.fact("setting", "lodge"))
    lines.append(asp.fact("feature", "fairy_lodge_currency_cologne", "conflict"))
    lines.append(asp.fact("feature", "fairy_lodge_currency_cologne", "misunderstanding"))
    lines.append(asp.fact("feature", "fairy_lodge_currency_cologne", "sharing"))
    lines.append(asp.fact("thing", "currency"))
    lines.append(asp.fact("thing", "cologne"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return bool(asp.atoms(model, "valid_story"))


def asp_verify() -> int:
    ok = asp_valid()
    py = valid_story()
    if ok == py:
        print("OK: ASP and Python reasonableness gates match.")
        return 0
    print("MISMATCH: ASP and Python reasonableness gates differ.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(place="lodge", hero="Mina", companion="Bram", gender="girl"),
    StoryParams(place="lodge", hero="Tessa", companion="Eli", gender="girl"),
    StoryParams(place="lodge", hero="Lina", companion="Jon", gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(bool(asp.atoms(model, "valid_story")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.companion} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
