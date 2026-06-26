#!/usr/bin/env python3
"""
A small standalone storyworld for a superhero-style tale about a creature,
peekaboo, kindness, misunderstanding, and dialogue.

A seed tale:
---
A tiny creature loved playing peekaboo in the city square. It wore a bright cape
and tried to surprise everyone with silly hiding spots. One day, the creature hid
behind a statue and popped out at a knightly hero, who thought the creature was
causing trouble. The hero spoke sternly, the creature felt scared, and for a moment
they misunderstood each other. Then the creature gently offered the hero its cape
to help cover a shivering kitten, and the hero understood that the creature was
being kind all along. They smiled, talked it out, and played peekaboo together
while keeping the kitten warm.
---
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
    kind: str = "thing"  # character | thing | creature | hero
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wears: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: {})
    memes: dict[str, float] = field(default_factory=lambda: {})

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Power:
    id: str
    label: str
    verb: str
    effect: str
    causes_misunderstanding: bool = False


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    helps: str
    region: str = ""


@dataclass
class StoryParams:
    place: str
    power: str
    gift: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "city_square": Setting(
        place="the city square",
        detail="The city square was bright, with tall steps, a fountain, and a statue that made a perfect hiding place.",
        affords={"peekaboo", "dialogue", "kindness"},
    ),
    "rooftop_garden": Setting(
        place="the rooftop garden",
        detail="The rooftop garden was high above the street, with pots, vines, and a little bench beside the railing.",
        affords={"peekaboo", "dialogue", "kindness"},
    ),
    "harbor_walk": Setting(
        place="the harbor walk",
        detail="The harbor walk smelled like salt and wind, and little boats blinked in the distance.",
        affords={"peekaboo", "dialogue", "kindness"},
    ),
}

POWERS = {
    "peekaboo": Power(
        id="peekaboo",
        label="peekaboo",
        verb="play peekaboo",
        effect="would surprise people in a playful way",
        causes_misunderstanding=True,
    ),
    "whirl": Power(
        id="whirl",
        label="whirl",
        verb="spin in a quick whirl",
        effect="would make a fast, dramatic entrance",
        causes_misunderstanding=True,
    ),
    "shadowjump": Power(
        id="shadowjump",
        label="shadowjump",
        verb="leap from shadow to shadow",
        effect="would make the hero seem mysterious",
        causes_misunderstanding=True,
    ),
}

GIFTS = {
    "cape": Gift(
        id="cape",
        label="cape",
        phrase="a bright red cape",
        helps="keep a tiny friend warm",
        region="back",
    ),
    "lantern": Gift(
        id="lantern",
        label="lantern",
        phrase="a little lantern",
        helps="light a dark corner",
        region="hand",
    ),
    "blanket": Gift(
        id="blanket",
        label="blanket",
        phrase="a soft blue blanket",
        helps="make a shivering creature feel safe",
        region="arms",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Leo", "Theo", "Ben", "Max", "Finn", "Sam"]
CREATURE_NAMES = ["Pip", "Milo", "Tiko", "Bibi", "Rumi"]
HERO_NAMES = ["Nova", "Arrow", "Comet", "Spark", "Ruby"]
TRAITS = ["brave", "gentle", "curious", "playful", "kind"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for power in POWERS:
            for gift in GIFTS:
                combos.append((place, power, gift))
    return combos


def explain_rejection(power: Power, gift: Gift) -> str:
    return (
        f"(No story: {power.label} does not lead to a helpful kind act with {gift.label}. "
        f"Try a different power or a different gift.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero-style storyworld: a creature, peekaboo, kindness, misunderstanding, and dialogue."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    if args.power and args.gift:
        if args.power == "shadowjump" and args.gift == "lantern":
            raise StoryError(explain_rejection(POWERS[args.power], GIFTS[args.gift]))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.power is None or c[1] == args.power)
              and (args.gift is None or c[2] == args.gift)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, power, gift = rng.choice(sorted(combos))
    hero_type = args.gender or rng.choice(["creature", "hero"])
    hero_name = args.name or rng.choice(CREATURE_NAMES if hero_type == "creature" else HERO_NAMES)
    friend_name = args.friend or rng.choice(["Mira", "Tess", "Jade", "Owen", "Rey"])
    friend_type = "girl" if rng.choice([True, False]) else "boy"
    return StoryParams(place=place, power=power, gift=gift, hero_name=hero_name,
                       hero_type=hero_type, friend_name=friend_name, friend_type=friend_type)


def _pulse(world: World, actor: Entity, key: str, amt: float = 1.0) -> None:
    actor.memes[key] = actor.memes.get(key, 0.0) + amt


def tell(setting: Setting, power: Power, gift: Gift, hero_name: str, hero_type: str,
         friend_name: str, friend_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type, traits=["tiny", "caped", "kind"]
    ))
    friend = world.add(Entity(
        id=friend_name, kind="character", type=friend_type, traits=["helpful"]
    ))
    kitten = world.add(Entity(
        id="kitten", kind="creature", type="creature", label="kitten", phrase="a small shivering kitten"
    ))
    item = world.add(Entity(
        id=gift.id, kind="thing", type=gift.id, label=gift.label, phrase=gift.phrase, owner=hero.id
    ))
    hero.wears.append(gift.id)
    world.facts.update(hero=hero, friend=friend, kitten=kitten, item=item, power=power, gift=gift)

    world.say(f"{hero.id} was a tiny {hero.type} hero who loved {power.verb} at {setting.place}.")
    world.say(f"{setting.detail}")
    world.say(f"One day, {hero.id} had {gift.phrase}, and {hero.id} wanted to help everyone feel happy.")

    world.para()
    world.say(f"{hero.id} hid behind a statue and popped out with a grin. It was a perfect {power.label} trick.")
    _pulse(world, hero, "joy", 1)
    _pulse(world, hero, "play", 1)
    if power.causes_misunderstanding:
        _pulse(world, friend, "worry", 1)
        world.say(f"{friend.id} saw the surprise and thought, for a moment, that {hero.id} was causing trouble.")
    world.say(f'"What are you doing?" {friend.id} asked.')
    world.say(f'"Just playing {power.label}!" {hero.id} said. "I only wanted a little peekaboo."')

    world.para()
    _pulse(world, kitten, "shiver", 1)
    world.say(f"Then {hero.id} noticed {kitten.phrase} near a bench, all curled up and chilly.")
    world.say(f"{hero.id}'s face softened. {hero.id} held out {gift.phrase} and said, " + 
              f'"You can have this. {gift.helps}."')
    _pulse(world, hero, "kindness", 1)
    _pulse(world, friend, "understanding", 1)
    world.say(f"{friend.id} looked again and understood. {friend.id} smiled and said, " +
              f'"Oh! I misunderstood you. You were being kind."')
    world.say(f'"Let’s help together," {friend.id} said.')
    world.say(f"So {hero.id}, {friend.id}, and {kitten.id} stayed close, with {gift.label} keeping the little creature warm.")
    world.say(f"After that, {hero.id} and {friend.id} played peekaboo again, but this time they laughed together.")

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    power = f["power"]
    gift = f["gift"]
    return [
        f'Write a short superhero story for a young child about a creature who loves {power.label} and learns kindness.',
        f'Tell a gentle story where {hero.id} uses peekaboo, has a misunderstanding with a friend, and then helps with {gift.phrase}.',
        'Write a simple story about a tiny hero, a surprise, a mistake in understanding, and a kind explanation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    power = f["power"]
    gift = f["gift"]
    return [
        QAItem(
            question=f"What did {hero.id} love to do at {world.setting.place}?",
            answer=f"{hero.id} loved to {power.verb}, especially as a playful peekaboo trick."
        ),
        QAItem(
            question=f"Why did {friend.id} think {hero.id} was causing trouble at first?",
            answer=f"{friend.id} had a misunderstanding. The surprise looked like trouble at first, but {hero.id} was only playing."
        ),
        QAItem(
            question=f"How did {hero.id} show kindness?",
            answer=f"{hero.id} showed kindness by offering {gift.phrase} to help the shivering kitten stay warm."
        ),
        QAItem(
            question=f"What did the friends do after they talked it out?",
            answer=f"They understood each other, smiled, and played peekaboo together."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is peekaboo?",
            answer="Peekaboo is a game where someone hides and then suddenly appears to surprise another person in a friendly way."
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means helping, sharing, or speaking gently so another person feels safe and cared for."
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when people think the wrong thing about each other before they talk it out."
        ),
        QAItem(
            question="Why do stories have dialogue?",
            answer="Dialogue is the words characters say out loud, and it helps readers hear their feelings and understand the problem."
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
    for e in world.entities.values():
        bits = []
        if e.wears:
            bits.append(f"wears={e.wears}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
story(P, Power, Gift) :- place(P), power(Power), gift(Gift).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for pid in POWERS:
        lines.append(asp.fact("power", pid))
    for gid in GIFTS:
        lines.append(asp.fact("gift", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story/3."))
    return sorted(set(asp.atoms(model, "story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_story_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(place="city_square", power="peekaboo", gift="cape", hero_name="Nova", hero_type="creature",
                friend_name="Mira", friend_type="girl"),
    StoryParams(place="rooftop_garden", power="whirl", gift="blanket", hero_name="Pip", hero_type="creature",
                friend_name="Owen", friend_type="boy"),
    StoryParams(place="harbor_walk", power="shadowjump", gift="cape", hero_name="Ruby", hero_type="hero",
                friend_name="Jade", friend_type="girl"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], POWERS[params.power], GIFTS[params.gift],
                 params.hero_name, params.hero_type, params.friend_name, params.friend_type)
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
        print(asp_program("#show story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.hero_name}: {p.power} at {p.place} (gift: {p.gift})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
