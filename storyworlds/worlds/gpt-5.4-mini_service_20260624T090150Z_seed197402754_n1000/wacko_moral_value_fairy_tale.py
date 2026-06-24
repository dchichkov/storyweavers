#!/usr/bin/env python3
"""
storyworlds/worlds/wacko_moral_value_fairy_tale.py
===================================================

A small fairy-tale story world about a wacko little problem, a moral choice,
and a gentle ending image that proves what changed.

Premise:
- A child-like hero in a fairy-tale land finds a strange, wacko wish-gift.
- The gift tempts them to use it in a selfish or unkind way.
- A wise elder warns them that the magic only works well if they choose a
  moral value: honesty, kindness, generosity, or patience.
- The hero makes a better choice, and the world responds with warmth and peace.

This world is intentionally small and classical: one main choice, one tension,
one turn, one resolution. Physical meters and emotional memes both matter.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "mother", "woman"}
        male = {"boy", "prince", "king", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    mood: str


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    temptation: str
    moral: str
    blessing: str


@dataclass
class Choice:
    id: str
    label: str
    value: str
    help_line: str
    ending_line: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    elder: str
    gift: str
    choice: str
    seed: Optional[int] = None


SETTINGS = {
    "rose_gate": Setting(place="the Rose Gate", mood="gentle"),
    "moon_well": Setting(place="the Moon Well", mood="quiet"),
    "green_hall": Setting(place="the Green Hall", mood="bright"),
}

GIFTS = {
    "feather": Gift(
        id="feather",
        label="wacko feather",
        phrase="a wacko feather from a silver bird",
        temptation="tickle the royal cat and make everyone laugh",
        moral="kindness",
        blessing="the feather warmed into a soft, useful plume",
    ),
    "berry": Gift(
        id="berry",
        label="wacko berry",
        phrase="a wacko berry in a tiny gold bowl",
        temptation="eat it alone and keep the sweetness",
        moral="generosity",
        blessing="the berry split into many sweet shares",
    ),
    "key": Gift(
        id="key",
        label="wacko key",
        phrase="a wacko key that hummed like a bee",
        temptation="hide it and pretend nobody found it",
        moral="honesty",
        blessing="the key opened a bright little door for all",
    ),
    "clock": Gift(
        id="clock",
        label="wacko clock",
        phrase="a wacko clock with painted stars",
        temptation="rush ahead and ignore the waiting line",
        moral="patience",
        blessing="the clock slowed into a calm, shining rhythm",
    ),
}

CHOICES = {
    "kind": Choice(
        id="kind",
        label="kind choice",
        value="kindness",
        help_line="share the wonder and make room for another",
        ending_line="The world felt warmer because the hero chose kindness.",
    ),
    "honest": Choice(
        id="honest",
        label="honest choice",
        value="honesty",
        help_line="tell the truth even when hiding would be easier",
        ending_line="The world felt clear because the hero chose honesty.",
    ),
    "generous": Choice(
        id="generous",
        label="generous choice",
        value="generosity",
        help_line="share the good thing instead of clutching it tight",
        ending_line="The world felt brighter because the hero chose generosity.",
    ),
    "patient": Choice(
        id="patient",
        label="patient choice",
        value="patience",
        help_line="wait a little while instead of hurrying the magic",
        ending_line="The world felt calm because the hero chose patience.",
    ),
}

GIRL_NAMES = ["Ella", "Mira", "Nora", "Lina", "Ivy", "Pippa"]
BOY_NAMES = ["Theo", "Oren", "Finn", "Bram", "Jude", "Milo"]
ELDER_NAMES = ["Grandma Reed", "Old Oak", "Aunt Willow", "Master Pine"]


def moral_gate(gift: Gift, choice: Choice) -> bool:
    return gift.moral == choice.value


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for gift in GIFTS:
            for choice in CHOICES:
                if moral_gate(GIFTS[gift], CHOICES[choice]):
                    out.append((place, gift, choice))
    return out


def explain_rejection(gift: Gift, choice: Choice) -> str:
    return (
        f"(No story: the wacko {gift.label} is about {gift.moral}, but the "
        f"chosen path is about {choice.value}. In this fairy tale, the magic only "
        f"fits a matching moral value.)"
    )


def clean_name(name: str) -> str:
    return name.strip() or "Mira"


def pick_name(rng: random.Random, hero_type: str) -> str:
    return rng.choice(GIRL_NAMES if hero_type in {"girl", "princess"} else BOY_NAMES)


def make_world(setting: Setting) -> World:
    return World(setting)


def _tempt(world: World, hero: Entity, gift: Gift) -> None:
    hero.memes["want"] = hero.memes.get("want", 0) + 1
    world.say(
        f"In {world.setting.place}, {hero.id} found {gift.phrase}. "
        f"It was so wacko that it seemed to sparkle with its own secret plan."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted to {gift.temptation}, but that idea "
        f"made {hero.pronoun('possessive')} chest feel a bit tight."
    )


def _warn(world: World, elder: Entity, hero: Entity, gift: Gift) -> None:
    hero.memes["uncertain"] = hero.memes.get("uncertain", 0) + 1
    world.say(
        f'"Careful," said {elder.id}. "That wacko gift listens to the heart. '
        f'If your heart is selfish, the gift turns small and sour."'
    )
    world.say(
        f"{elder.id} asked {hero.id} to think of a better way, one that matched "
        f"{gift.moral}."
    )


def _choose(world: World, hero: Entity, gift: Gift, choice: Choice) -> None:
    hero.memes["goodness"] = hero.memes.get("goodness", 0) + 1
    world.say(
        f"{hero.id} took a breath and made a {choice.label}. "
        f"{choice.help_line.capitalize()}."
    )
    if choice.value == "honesty":
        hero.memes["truth"] = hero.memes.get("truth", 0) + 1
    if choice.value == "kindness":
        hero.memes["care"] = hero.memes.get("care", 0) + 1
    if choice.value == "generosity":
        hero.meters["sharing"] = hero.meters.get("sharing", 0) + 1
    if choice.value == "patience":
        hero.meters["waiting"] = hero.meters.get("waiting", 0) + 1


def _resolve(world: World, hero: Entity, elder: Entity, gift: Gift, choice: Choice) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(
        f"Then the wacko gift grew warm and bright. "
        f"{gift.blessing.capitalize()}."
    )
    world.say(
        f"{elder.id} smiled, and {hero.id} smiled too, because the right moral "
        f"choice had turned the odd little magic into something good."
    )
    world.say(
        f"At the end, {hero.id} stood in {world.setting.place} with a lighter heart, "
        f"and the fairy-tale air felt gentle as a lullaby."
    )


def tell(setting: Setting, gift: Gift, choice: Choice, hero_name: str, hero_type: str,
         elder_name: str = "Grandma Reed") -> World:
    world = make_world(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    elder = world.add(Entity(id=elder_name, kind="character", type="elder"))

    world.say(
        f"Once upon a time, in {setting.place}, there lived {hero.id}, a little "
        f"{hero_type} with a curious nose for strange things."
    )
    world.say(
        f"{elder.id} was a wise old fairy-tale helper who knew that choices could "
        f"be more important than crowns."
    )
    world.para()
    _tempt(world, hero, gift)
    _warn(world, elder, hero, gift)
    world.para()
    _choose(world, hero, gift, choice)
    _resolve(world, hero, elder, gift, choice)

    world.facts.update(hero=hero, elder=elder, gift=gift, choice=choice, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    gift: Gift = f["gift"]
    choice: Choice = f["choice"]
    return [
        f'Write a short fairy tale for a child about a wacko {gift.label} and a '
        f'{choice.value} decision.',
        f"Tell a gentle story where {hero.id} finds a strange gift in {world.setting.place} "
        f"and learns to choose {choice.value}.",
        f'Write a tiny story that includes the word "wacko" and ends with a good moral choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    elder: Entity = f["elder"]
    gift: Gift = f["gift"]
    choice: Choice = f["choice"]
    return [
        QAItem(
            question=f"What did {hero.id} find in {world.setting.place}?",
            answer=f"{hero.id} found {gift.phrase}, and it was very wacko and magical.",
        ),
        QAItem(
            question=f"Who helped {hero.id} understand the choice?",
            answer=f"{elder.id} helped by warning that the gift worked best when {hero.id} chose {choice.value}.",
        ),
        QAItem(
            question=f"What good choice did {hero.id} make?",
            answer=f"{hero.id} made a {choice.label} and chose {choice.value}.",
        ),
        QAItem(
            question=f"How did the gift change at the end?",
            answer=f"It grew warm and bright, and {gift.blessing.lower()}.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "kindness": [
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring about other people.",
        )
    ],
    "honesty": [
        QAItem(
            question="What is honesty?",
            answer="Honesty means telling the truth and not pretending something false is real.",
        )
    ],
    "generosity": [
        QAItem(
            question="What is generosity?",
            answer="Generosity means sharing what you have and being glad another person can enjoy it too.",
        )
    ],
    "patience": [
        QAItem(
            question="What is patience?",
            answer="Patience means waiting calmly and not rushing when something needs a little time.",
        )
    ],
    "wacko": [
        QAItem(
            question="What does wacko mean?",
            answer="Wacko means strange, odd, or funny in a surprising way.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    choice: Choice = world.facts["choice"]
    out = [QAItem(
        question="What kind of story is this?",
        answer="It is a fairy tale about a strange magical thing and a moral choice.",
    ), QAItem(
        question="Why does the magic matter?",
        answer="Because the magic reacts to the hero's heart, so choosing well changes how the gift works.",
    ), QAItem(
        question="What does the word wacko describe here?",
        answer="It describes the odd, surprising magic of the gift.",
    )]
    out.extend(WORLD_KNOWLEDGE.get(choice.value, []))
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
gift_matches(G, C) :- gift(G), choice(C), gift_moral(G, M), choice_value(C, M).
valid_story(P, G, C) :- place(P), gift(G), choice(C), gift_matches(G, C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for gid, gift in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        lines.append(asp.fact("gift_moral", gid, gift.moral))
    for cid, choice in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        lines.append(asp.fact("choice_value", cid, choice.value))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A wacko moral-value fairy tale story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy", "princess", "prince"], default=None)
    ap.add_argument("--elder", choices=ELDER_NAMES)
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
              and (args.gift is None or c[1] == args.gift)
              and (args.choice is None or c[2] == args.choice)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, gift_id, choice_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy", "princess", "prince"])
    hero = clean_name(args.hero or pick_name(rng, hero_type))
    elder = args.elder or rng.choice(ELDER_NAMES)
    return StoryParams(place=place, hero=hero, hero_type=hero_type, elder=elder, gift=gift_id, choice=choice_id)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], GIFTS[params.gift], CHOICES[params.choice],
                 params.hero, params.hero_type, params.elder)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible story combos:\n")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("rose_gate", "Ella", "girl", "Grandma Reed", "feather", "kind"),
            StoryParams("moon_well", "Theo", "boy", "Old Oak", "key", "honest"),
            StoryParams("green_hall", "Mira", "girl", "Aunt Willow", "berry", "generous"),
            StoryParams("rose_gate", "Finn", "boy", "Master Pine", "clock", "patient"),
        ]
        samples = [generate(p) for p in curated]
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
            header = f"### {p.hero}: {p.gift} / {p.choice} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
