#!/usr/bin/env python3
"""
storyworlds/worlds/topple_porch_magic_transformation_mystery_to_solve.py
========================================================================

A small adventure storyworld about a porch, a topple, and a magical mystery
that changes someone into something else until the problem is solved.

Premise:
- A child, a curious helper, and a porch with a strange old charm.
- A magical object can transform one thing into another.
- A bump or topple can set the mystery in motion.

Tension:
- Something treasured is changed by magic.
- The characters must figure out what happened and how to set it right.

Turn:
- The hero follows clues from the porch and notices what the magic responds to.
- A careful action reverses the wrong transformation.

Resolution:
- The transformed thing returns to its true shape.
- The porch ends calm, with one small magical clue still sparkling nearby.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the porch"
    clue_place: str = "the porch rail"
    affords: set[str] = field(default_factory=set)


@dataclass
class Spell:
    id: str
    label: str
    trigger: str
    misfire: str
    fix: str
    source: str
    result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    kind: str
    transform_to: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.weather: str = "windy"
        self.magic_residue: int = 0

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.weather = self.weather
        clone.magic_residue = self.magic_residue
        return clone


@dataclass
class StoryParams:
    place: str
    spell: str
    prize: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


PLACES = {
    "porch": Setting(place="the porch", clue_place="the porch rail", affords={"glow", "whisper", "transform"}),
    "front_porch": Setting(place="the front porch", clue_place="the step edge", affords={"glow", "whisper", "transform"}),
    "screen_porch": Setting(place="the screen porch", clue_place="the windowsill", affords={"glow", "whisper", "transform"}),
}

SPELLS = {
    "glow": Spell(
        id="glow",
        label="glow charm",
        trigger="touch the glowing stone",
        misfire="glowed too bright",
        fix="cover the stone with a cloth",
        source="glowing stone",
        result="sparkling",
        tags={"magic"},
    ),
    "whisper": Spell(
        id="whisper",
        label="whisper charm",
        trigger="listen at the old hinge",
        misfire="whispered the wrong name",
        fix="speak the true name softly",
        source="old hinge",
        result="quiet",
        tags={"mystery"},
    ),
    "transform": Spell(
        id="transform",
        label="turning charm",
        trigger="spin the little ring",
        misfire="turned the prize into something odd",
        fix="turn the ring back the other way",
        source="little ring",
        result="restored",
        tags={"transformation"},
    ),
}

PRIZES = {
    "cat": Prize("cat", "a sleepy porch cat", "cat", "animal", "cat"),
    "kettle": Prize("kettle", "a little brass kettle", "kettle", "thing", "kettle"),
    "basket": Prize("basket", "a berry basket", "basket", "thing", "basket"),
    "birdhouse": Prize("birdhouse", "a painted birdhouse", "birdhouse", "thing", "birdhouse"),
}

GIRL_NAMES = ["Ava", "Mira", "Nora", "Lina", "Poppy", "Ivy"]
BOY_NAMES = ["Theo", "Finn", "Eli", "Bram", "Noah", "Miles"]
HELPERS = ["grandmother", "grandfather", "aunt", "uncle", "sister", "brother"]
TRAITS = ["brave", "curious", "quick-eyed", "gentle", "bold"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in PLACES.items():
        for spell in setting.affords:
            for prize in PRIZES:
                out.append((place, spell, prize))
    return out


def prize_at_risk(spell: Spell, prize: Prize) -> bool:
    return True


def select_fix(spell: Spell, prize: Prize) -> str:
    return spell.fix


def explain_rejection(spell: Spell, prize: Prize) -> str:
    return f"(No story: the magic at this porch cannot reasonably transform {prize.label} with {spell.label}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: a porch, magic, and a transformation mystery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.spell and args.prize:
        if not prize_at_risk(SPELLS[args.spell], PRIZES[args.prize]):
            raise StoryError(explain_rejection(SPELLS[args.spell], PRIZES[args.prize]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.spell is None or c[1] == args.spell)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, spell, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, spell=spell, prize=prize, name=name, gender=gender, helper=helper, trait=trait)


def _do_magic(world: World, hero: Entity, spell: Spell, prize: Entity, narrate: bool = True) -> None:
    world.magic_residue += 1
    if spell.id == "transform":
        prize.memes["changed"] = 1
        prize.label = "birdhouse" if prize.type != "birdhouse" else "basket"
        prize.phrase = f"a changed {prize.label}"
    if narrate:
        world.say(f"The {spell.source} answered the magic and made the air shimmer.")


def tell(setting: Setting, spell: Spell, prize_cfg: Prize, name: str, gender: str, helper_kind: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, traits=["little", trait]))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_kind, label=f"the {helper_kind}"))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id))
    hero.memes["curiosity"] = 1
    world.say(f"{hero.id} was a little {trait} {gender} who loved adventure on {setting.place}.")
    world.say(f"Near the porch, {hero.id} found {prize.phrase} and noticed a strange {spell.label}.")
    world.para()
    world.say(f"One windy afternoon, {hero.id} stepped onto {setting.place} and heard a soft hum from {setting.clue_place}.")
    world.say(f"{hero.pronoun('possessive').capitalize()} {helper_kind} warned, \"Don't {spell.trigger}; porch magic can be tricky.\"")
    world.say(f"But when the board gave a tiny topple, the spell went off and {spell.misfire}.")
    prize.memes["mystery"] = 1
    _do_magic(world, hero, spell, prize, narrate=False)
    world.say(f"At once, the old charm left a clue behind: a single spark danced on {setting.clue_place}.")
    world.para()
    world.say(f"{hero.id} and {hero.pronoun('possessive')} {helper_kind} searched for the reason.")
    world.say(f"They watched the spark, guessed the spell's source, and tried to {spell.fix}.")
    prize.memes["safe"] = 1
    if spell.id == "transform":
        prize.label = prize_cfg.label
        prize.phrase = prize_cfg.phrase
    world.say(f"The mystery was solved, and {prize.phrase} was whole again.")
    world.say(f"By evening, {hero.id} sat safely on {setting.place}, smiling at the quiet porch and the last tiny sparkle.")
    world.facts.update(hero=hero, helper=helper, prize=prize, prize_cfg=prize_cfg, spell=spell, setting=setting)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], SPELLS[params.spell], PRIZES[params.prize], params.name, params.gender, params.helper, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short adventure story for a young child about {f['hero'].id} and a mysterious porch charm.",
        f"Tell a magical story where a topple on {f['setting'].place} changes {f['prize_cfg'].phrase} and the characters solve the mystery.",
        f"Create a child-friendly story with magic, a transformation, and a clue on {f['setting'].clue_place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, spell, setting = f["hero"], f["helper"], f["prize"], f["spell"], f["setting"]
    return [
        QAItem(
            question=f"Where did {hero.id} find the magical problem?",
            answer=f"{hero.id} found it on {setting.place}, near {setting.clue_place}, where the magic started after the topple.",
        ),
        QAItem(
            question=f"What kind of mystery did {hero.id} and {helper.label} have to solve?",
            answer=f"They had to solve a transformation mystery, because the {spell.label} changed {prize.phrase} in a strange way.",
        ),
        QAItem(
            question=f"What fixed the magic at the end?",
            answer=f"They followed the clue and used the right counter-step: {spell.fix}. That made the porch calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a porch?", answer="A porch is a small outdoor space attached to a house, often near the front or back door."),
        QAItem(question="What is magic in a story?", answer="Magic is a special kind of impossible-sounding power that can make unusual things happen in a tale."),
        QAItem(question="What is a transformation?", answer="A transformation is a change from one shape or form into another."),
        QAItem(question="What is a mystery?", answer="A mystery is something puzzling that characters must figure out by looking for clues."),
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
        bits = []
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  magic_residue={world.magic_residue}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="porch", spell="transform", prize="cat", name="Mira", gender="girl", helper="grandmother", trait="curious"),
    StoryParams(place="front_porch", spell="glow", prize="basket", name="Theo", gender="boy", helper="uncle", trait="brave"),
    StoryParams(place="screen_porch", spell="whisper", prize="kettle", name="Ava", gender="girl", helper="sister", trait="gentle"),
]


ASP_RULES = r"""
place(porch). place(front_porch). place(screen_porch).
spell(glow). spell(whisper). spell(transform).
prize(cat). prize(kettle). prize(basket). prize(birdhouse).

affords(porch,glow). affords(porch,whisper). affords(porch,transform).
affords(front_porch,glow). affords(front_porch,whisper). affords(front_porch,transform).
affords(screen_porch,glow). affords(screen_porch,whisper). affords(screen_porch,transform).

valid(P,S,R) :- affords(P,S), prize(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        for s in sorted(PLACES[pid].affords):
            lines.append(asp.fact("affords", pid, s))
    for sid in SPELLS:
        lines.append(asp.fact("spell", sid))
    for rid in PRIZES:
        lines.append(asp.fact("prize", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_story_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
