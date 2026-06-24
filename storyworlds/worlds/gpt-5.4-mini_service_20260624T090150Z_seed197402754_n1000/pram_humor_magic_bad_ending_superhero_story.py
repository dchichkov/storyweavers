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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
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
    affords: set[str] = field(default_factory=set)


@dataclass
class Power:
    id: str
    label: str
    effect: str
    mess: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str = "ground"
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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


SETTINGS = {
    "city": Setting(place="the bright city square", affords={"float", "spark", "chase"}),
    "park": Setting(place="the pocket park", affords={"float", "spark", "chase"}),
}

POWERS = {
    "float": Power(
        id="float",
        label="floating spell",
        effect="lifted things into the air",
        mess="wobbly",
        tags={"magic", "humor"},
    ),
    "spark": Power(
        id="spark",
        label="spark spell",
        effect="made bright zaps and silly pops",
        mess="singed",
        tags={"magic", "humor"},
    ),
    "chase": Power(
        id="chase",
        label="speed burst",
        effect="made the hero dash very fast",
        mess="dusty",
        tags={"superhero"},
    ),
}

PRIZES = {
    "pram": Prize(
        id="pram",
        label="pram",
        phrase="a shiny red pram with a bell",
        region="ground",
    )
}

GEAR = {
    "cape": Gear(
        id="cape",
        label="a blue cape",
        prep="put on the blue cape",
        tail="flew after the pram",
        helps={"chase", "spark"},
    ),
    "blanket": Gear(
        id="blanket",
        label="a soft blanket",
        prep="wrap the baby in a soft blanket",
        tail="kept the baby snug",
        helps={"float"},
    ),
}

NAMES = ["Nova", "Max", "Tara", "Pip", "Juno", "Rex"]
HERO_TYPES = ["girl", "boy"]
PARENT_TYPES = ["mother", "father"]
TRAITS = ["brave", "funny", "curious", "quick"]


@dataclass
class StoryParams:
    place: str
    power: str
    name: str
    hero_type: str
    parent_type: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with pram, humor, magic, and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    power = args.power or rng.choice(list(POWERS))
    hero_type = args.gender or rng.choice(HERO_TYPES)
    name = args.name or rng.choice(NAMES)
    parent_type = args.parent or rng.choice(PARENT_TYPES)
    trait = rng.choice(TRAITS)
    if power not in SETTINGS[place].affords:
        raise StoryError(f"(No story: {place} does not fit the {power} scene.)")
    return StoryParams(place=place, power=power, name=name, hero_type=hero_type, parent_type=parent_type, trait=trait)


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for p in sorted(s.affords):
            lines.append(asp.fact("affords", sid, p))
    for pid, p in POWERS.items():
        lines.append(asp.fact("power", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("tags", pid, t))
    for rid, r in PRIZES.items():
        lines.append(asp.fact("prize", rid))
        lines.append(asp.fact("gender_ok", rid, "girl"))
        lines.append(asp.fact("gender_ok", rid, "boy"))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for h in sorted(g.helps):
            lines.append(asp.fact("helps", gid, h))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(S,P) :- affords(S,P), power(P).
bad_ending(P,R) :- power(P), prize(R).
show_story(S,P,R) :- compatible(S,P), bad_ending(P,R).
#show show_story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show show_story/3."))
    atoms = set(asp.atoms(model, "show_story"))
    py = {(s, p, r) for s in SETTINGS for p in SETTINGS[s].affords for r in PRIZES}
    if atoms == py:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only clingo:", sorted(atoms - py))
    print("only python:", sorted(py - atoms))
    return 1


def dump_trace(world: World) -> str:
    bits = ["--- world model state ---"]
    for e in world.entities.values():
        bits.append(f"  {e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(bits)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_type, label=params.parent_type))
    pram = world.add(Entity(id="pram", type="pram", label="pram", phrase="a shiny red pram with a bell", owner=hero.id, caretaker=parent.id))

    power = POWERS[params.power]
    hero.memes["hope"] = 1
    hero.memes["humor"] = 1
    pram.meters["gleam"] = 1

    world.say(f"{hero.id} was a {params.trait} little {hero.type} who liked being a tiny superhero.")
    world.say(f"{hero.pronoun().capitalize()} loved the {pram.label} because it looked like a magic mission cart.")
    world.para()
    world.say(f"One day at {world.setting.place}, {hero.id} tried {power.effect}.")
    world.say(f"That made the {pram.label} wobble, wobble, and then zip along with a silly bell sound.")
    world.say(f"{hero.id} laughed so hard that even {hero.pronoun('possessive')} {params.parent_type} had to smile.")

    world.para()
    villain = world.add(Entity(id="MuddleMage", kind="character", type="wizard", label="Muddle Mage"))
    villain.memes["trick"] = 1
    world.say(f"Then Muddle Mage waved a sparkly stick and shouted, \"Zoom, pram, zoom!\"")
    pram.meters["wobble"] = 2
    pram.meters["flee"] = 1
    world.say(f"The pram flew over a bench, bonked a lamppost, and landed with its wheel in a puddle.")
    hero.memes["panic"] = 1
    world.say(f"{hero.id} ran after it, but the cape snagged on a sign and made a funny flag shape.")

    world.para()
    world.say(f"{params.parent_type.capitalize()} tried to help with a blanket, but the spell had already gone wibbly.")
    pram.meters["dirty"] = 1
    pram.meters["broken"] = 1
    hero.memes["sad"] = 1
    world.say(f"In the end, the bell on the {pram.label} went tink once, then fell silent.")
    world.say(f"{hero.id} stood in the square with a muddy shoe, a crooked cape, and a broken pram.")
    world.say(f"It was a very silly superhero day, and also a bad ending, because the magic pram did not come back.")

    world.facts.update(hero=hero, parent=parent, pram=pram, power=power, setting=world.setting, villain=villain)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a short superhero story for a small child that includes a magic pram and a funny spell.',
        f"Tell a story where {hero.id} tries to be brave, but a wizard makes the pram fly away.",
        f'Write a gentle but disappointing ending with humor, magic, and the word "pram".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little superhero who loved the pram.",
        ),
        QAItem(
            question=f"What did Muddle Mage do to the pram?",
            answer=f"Muddle Mage made the pram fly and wobble until it landed in a puddle.",
        ),
        QAItem(
            question=f"Why was the ending bad?",
            answer="The pram got muddy and broken, and the magic spell did not get fixed.",
        ),
        QAItem(
            question=f"How did {parent.pronoun('subject')} try to help at the end?",
            answer=f"{parent.pronoun('subject').capitalize()} tried to help with a blanket, but it was too late.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a pram?", answer="A pram is a small carriage for a baby that a grown-up can push."),
        QAItem(question="What is a superhero?", answer="A superhero is a made-up hero who uses special powers to help others."),
        QAItem(question="What is magic?", answer="Magic is pretend power in stories that can make strange and surprising things happen."),
        QAItem(question="Why can humor make a story fun?", answer="Humor makes a story funny, which can help children enjoy the silly parts."),
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
    out.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        print(asp_program("#show show_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show show_story/3."))
        print(sorted(asp.atoms(model, "show_story")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for place in SETTINGS:
            for power in SETTINGS[place].affords:
                params = StoryParams(place=place, power=power, name="Nova", hero_type="girl", parent_type="mother", trait="brave")
                samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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
