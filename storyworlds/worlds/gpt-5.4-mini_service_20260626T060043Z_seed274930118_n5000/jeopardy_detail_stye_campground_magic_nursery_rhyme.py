#!/usr/bin/env python3
"""
A tiny campground magic storyworld in a nursery-rhyme style.

Premise:
A child at a campground loves a little magic trick.
A tiny spark or enchanted puff can make a campfire lantern, a sleeping bag,
or a picnic basket misbehave.

Tension:
The magic can create a stye on an eye, spoil a detail of the camp setup,
or make the campsite feel in jeopardy.

Turn:
A gentle helper or simple counter-charm fixes the trouble.

Resolution:
The child learns a safer spell, and the campground ends calm and bright.
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
    place: str = "the campground"
    affords: set[str] = field(default_factory=set)


@dataclass
class Spell:
    id: str
    verb: str
    effect: str
    risk: str
    clue: str
    detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
    "campground": Setting(place="the campground", affords={"spark", "glimmer", "whisper"}),
}

SPELLS = {
    "spark": Spell(
        id="spark",
        verb="make a sparkly wish",
        effect="sparkled",
        risk="jeopardy",
        clue="a twinkling shimmer",
        detail="every little detail",
        tags={"magic", "jeopardy", "detail"},
    ),
    "glimmer": Spell(
        id="glimmer",
        verb="glimmer at the moon",
        effect="glimmered",
        risk="detail",
        clue="a silver blink",
        detail="a tiny detail",
        tags={"magic", "detail"},
    ),
    "whisper": Spell(
        id="whisper",
        verb="whisper a magic rhyme",
        effect="whispered",
        risk="stye",
        clue="a sleepy hum",
        detail="one small detail",
        tags={"magic", "stye"},
    ),
}

CHARMS = [
    Charm(
        id="patch",
        label="a soft eye patch",
        phrase="a soft eye patch",
        guards={"stye"},
        prep="put on the soft eye patch first",
        tail="followed the rhyme with careful eyes",
    ),
    Charm(
        id="shade",
        label="a little hat shade",
        phrase="a little hat shade",
        guards={"jeopardy", "detail"},
        prep="lift up a little hat shade",
        tail="stood under the little hat shade",
    ),
]

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ivy", "Ada", "June"]
BOY_NAMES = ["Pip", "Toby", "Finn", "Ollie", "Theo", "Ben"]


@dataclass
class StoryParams:
    place: str
    spell: str
    child_name: str
    gender: str
    helper_name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Campground magic nursery-rhyme storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
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


def valid_combos() -> list[tuple[str, str]]:
    return [(place, spell) for place, s in SETTINGS.items() for spell in s.affords]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.spell and args.spell not in SPELLS:
        raise StoryError("Unknown spell.")
    combos = [c for c in valid_combos()
              if args.place is None or c[0] == args.place
              and (args.spell is None or c[1] == args.spell)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, spell = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["Grandma Moss", "Uncle Reed", "Aunt Fern"])
    return StoryParams(place=place, spell=spell, child_name=name, gender=gender, helper_name=helper)


def reasonableness_gate(spell: Spell) -> bool:
    return "magic" in spell.tags and spell.risk in {"jeopardy", "detail", "stye"}


ASP_RULES = r"""
valid(Place, Spell) :- setting(Place), affords(Place, Spell), spell(Spell).
reasonable(Spell) :- magic(Spell), risk(Spell, jeopardy).
reasonable(Spell) :- magic(Spell), risk(Spell, detail).
reasonable(Spell) :- magic(Spell), risk(Spell, stye).
valid_story(Place, Spell) :- valid(Place, Spell), reasonable(Spell).
#show valid/2.
#show valid_story/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for place, s in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for spell in sorted(s.affords):
            lines.append(asp.fact("affords", place, spell))
    for sid, sp in SPELLS.items():
        lines.append(asp.fact("spell", sid))
        lines.append(asp.fact("magic", sid))
        lines.append(asp.fact("risk", sid, sp.risk))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    a, p = set(asp_valid_combos()), set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    spell = SPELLS[params.spell]
    world = World(setting)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.gender))
    helper = world.add(Entity(id=params.helper_name, kind="character", type="woman"))
    charm = world.add(Entity(id="charm", type="charm", label="eye patch", phrase="a soft eye patch", caretaker=helper.id))
    world.facts.update(child=child, helper=helper, spell=spell, charm=charm, params=params)
    return world


def tell(world: World) -> None:
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper"]
    spell: Spell = world.facts["spell"]
    charm: Entity = world.facts["charm"]

    world.say(f"{child.id} was a little one at {world.setting.place}, where the pines swayed and the lanterns gleamed.")
    world.say(f"{child.id} loved to {spell.verb}, for {spell.clue} made {spell.detail} feel bright and tame.")
    world.para()
    world.say(f"One night at the {world.setting.place}, {child.id} tried to {spell.verb} near the campfire glow.")
    world.say(f"But the magic went haywire, and a tiny {spell.risk} trouble began to grow.")
    world.say(f"{child.id} rubbed {child.pronoun('possessive')} eye and blinked and blinked; it felt sore and red like a berry in tow.")
    world.para()
    world.say(f"{helper.id} said, “Now hush, dear heart, and do not fret; let's keep this trouble small and slow.”")
    world.say(f"{helper.id} brought out {charm.phrase} and said, “We will use this and tiptoe low.”")
    world.say(f"With the soft patch on, {child.id} could rest {child.pronoun('possessive')} eye, and the spell was set to go.")
    world.para()
    world.say(f"{child.id} whispered a kinder rhyme, and the magic turned from trouble to a gentle, golden show.")
    world.say(f"The campsite stayed in no more {spell.risk}, and every little detail shone in rows and rows.")
    world.say(f"So {child.id} slept in peace by the campground fire, with a calm new charm and a moonlit glow.")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    spell: Spell = f["spell"]
    child: Entity = f["child"]
    return [
        f"Write a nursery-rhyme style story set at the campground about {child.id} and a little magic {spell.verb}.",
        f"Tell a gentle story where a campground spell causes {spell.risk} and a helper fixes it.",
        f"Write a short child-friendly tale using the words jeopardy, detail, and stye.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    spell: Spell = f["spell"]
    return [
        QAItem(
            question=f"Where was {child.id} when the magic trouble began?",
            answer=f"{child.id} was at the campground when the magic trouble began.",
        ),
        QAItem(
            question=f"What did {child.id} want to do with the magic?",
            answer=f"{child.id} wanted to {spell.verb}.",
        ),
        QAItem(
            question=f"Who helped {child.id} fix the trouble?",
            answer=f"{helper.id} helped {child.id} fix the trouble with a soft eye patch.",
        ),
        QAItem(
            question=f"What problem showed up from the spell?",
            answer=f"A tiny {spell.risk} trouble showed up, and the campsite felt shaky for a moment.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is jeopardy?",
            answer="Jeopardy means danger or the chance that something bad could happen.",
        ),
        QAItem(
            question="What is a stye?",
            answer="A stye is a small sore bump on or near the eyelid that can make an eye hurt.",
        ),
        QAItem(
            question="What is a detail?",
            answer="A detail is a tiny part of something, like one small piece of a picture or scene.",
        ),
        QAItem(
            question="What is a campground?",
            answer="A campground is a place where people can stay in tents or cabins and spend time outdoors.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic in a story is a pretend power that can make surprising things happen.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:12} ({e.kind:9}) type={e.type} label={e.label or '-'}")
    lines.append(f"  setting: {world.setting.place}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(place="campground", spell="whisper", child_name="Mina", gender="girl", helper_name="Grandma Moss"),
    StoryParams(place="campground", spell="spark", child_name="Pip", gender="boy", helper_name="Aunt Fern"),
    StoryParams(place="campground", spell="glimmer", child_name="Lila", gender="girl", helper_name="Uncle Reed"),
]


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell(world)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(combos)} compatible (place, spell) combos ({len(stories)} with reasonableness):\n")
        for place, spell in combos:
            print(f"  {place:12} {spell}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.child_name}: {p.spell} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
