#!/usr/bin/env python3
"""
A tall-tale storyworld about a weekly swig, a sudden chickened-out moment,
and a flashback that turns a conflict into a moral lesson.

The world is small and classical:
- a boastful hero wants to lead a weekly gathering,
- a risky drink or dare causes conflict,
- a flashback reveals why the hero is afraid,
- the moral value is honesty, courage, or kindness,
- the ending proves what changed in the world state.

This script follows the Storyweavers world contract.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = False


@dataclass
class Swig:
    id: str
    label: str
    phrase: str
    moral: str
    risky: bool = False
    weekly: bool = True
    flashback_trigger: str = ""
    conflict_kind: str = "fear"


@dataclass
class StoryParams:
    place: str
    swig: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

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
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "porch": Place("porch", "the porch", indoors=False),
    "barn": Place("barn", "the old barn", indoors=True),
    "fair": Place("fair", "the county fair", indoors=False),
    "kitchen": Place("kitchen", "the kitchen", indoors=True),
}

SWIGS = {
    "lemonade": Swig(
        id="lemonade",
        label="lemonade",
        phrase="a weekly swig of tart lemonade",
        moral="honesty",
        risky=True,
        flashback_trigger="sour",
        conflict_kind="dare",
    ),
    "rootbeer": Swig(
        id="rootbeer",
        label="root beer",
        phrase="a weekly swig of frothy root beer",
        moral="courage",
        risky=False,
        flashback_trigger="foam",
        conflict_kind="worry",
    ),
    "cider": Swig(
        id="cider",
        label="apple cider",
        phrase="a weekly swig of warm apple cider",
        moral="kindness",
        risky=False,
        flashback_trigger="cinnamon",
        conflict_kind="share",
    ),
}

GIRL_NAMES = ["Mabel", "Nora", "Daisy", "June", "Clara", "Ruby", "Ivy"]
BOY_NAMES = ["Hank", "Eli", "Otis", "Wes", "Bo", "Jude", "Finn"]
TRAITS = ["bold", "curious", "stubborn", "cheerful", "lively", "tall-talking"]
ELDERS = ["grandpa", "grandma", "uncle", "aunt"]


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def hero_title(entity: Entity) -> str:
    return entity.type


def setting_sentence(place: Place) -> str:
    if place.indoors:
        return f"The {place.label.removeprefix('the ')} had creaky boards and a big echo."
    return f"The air around {place.label} was wide as a wagon road."


def opening_voice(hero: Entity, swig: Swig) -> str:
    return (
        f"{hero.id} was the sort of tall-tale {hero.type} who could spin a lasso out of a loose thread. "
        f"{hero.pronoun().capitalize()} loved {swig.phrase} and bragged that {hero.pronoun('possessive')} courage was bigger than a haystack."
    )


def flashback_line(hero: Entity, swig: Swig) -> str:
    return (
        f"But one sour flashback still lived in {hero.pronoun('possessive')} boots: "
        f"the last time {hero.id} took a swig like that, {hero.pronoun()} had laughed too hard and chickened out before the finish."
    )


def conflict_line(hero: Entity, elder: Entity, swig: Swig) -> str:
    return (
        f"At the weekly gathering, {hero.id} reached for the cup, then chickened at the very last blink. "
        f"{elder.id} frowned and said, \"A brave story means telling the truth, even when your knees rattle.\""
    )


def moral_turn_line(hero: Entity, elder: Entity, swig: Swig) -> str:
    return (
        f"{hero.id} took a breath and admitted the truth: {hero.pronoun().capitalize()} had been scared because of the old flashback, not because of the crowd. "
        f"{elder.id} nodded, and the whole place seemed to loosen its collar."
    )


def resolution_line(hero: Entity, swig: Swig) -> str:
    return (
        f"So they made the weekly swig smaller and kinder, and {hero.id} finished it without chickening out. "
        f"By the end, {hero.pronoun()} was laughing straight and tall, with the moral value of honesty shining brighter than the tin cups."
    )


# ---------------------------------------------------------------------------
# State transitions
# ---------------------------------------------------------------------------

def tell_story(world: World, hero: Entity, elder: Entity, swig: Swig) -> None:
    world.say(opening_voice(hero, swig))
    world.say(setting_sentence(world.place))
    world.say(f"Every week, the neighbors gathered for {swig.phrase}.")
    world.para()
    world.say(flashback_line(hero, swig))
    hero.memes["fear"] = 1.0
    hero.memes["shame"] = 1.0
    world.say(conflict_line(hero, elder, swig))
    hero.memes["conflict"] = 1.0
    elder.memes["concern"] = 1.0
    world.para()
    world.say(moral_turn_line(hero, elder, swig))
    hero.memes["honesty"] = 1.0
    hero.memes["fear"] = 0.0
    hero.memes["conflict"] = 0.0
    world.say(resolution_line(hero, swig))
    hero.memes["courage"] = 1.0
    hero.meters["swigs_taken"] = hero.meters.get("swigs_taken", 0.0) + 1.0


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def reasonable_combo(place: Place, swig: Swig) -> bool:
    if place.indoors and swig.label == "lemonade" and swig.risky:
        return True
    if place.label == "the county fair":
        return True
    return swig.weekly


# ---------------------------------------------------------------------------
# Sample generation / QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    swig = world.facts["swig"]
    return [
        f'Write a tall-tale story about {p.name} at {world.place.label} with a weekly swig and a moral lesson.',
        f"Tell a child-friendly story where {p.name} chickened out, remembered a flashback, and chose honesty.",
        f'Write a short story using the words "chickened", "weekly", and "swig" with a clear conflict and happy ending.',
        f"Make the ending prove how {swig.moral} changed the way the hero faced the crowd.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    swig = world.facts["swig"]
    qa = [
        QAItem(
            question=f"Who is the tall-tale story about?",
            answer=f"It is about {hero.id}, a {hero.traits[0]} {hero.type} who faces a weekly swig and a big feeling."
        ),
        QAItem(
            question=f"What made {hero.id} chickened out at first?",
            answer=f"{hero.id} chickened out because an old flashback brought back fear about the swig, so the crowd felt larger than the courage."
        ),
        QAItem(
            question=f"What did {elder.id} teach {hero.id} during the conflict?",
            answer=f"{elder.id} taught {hero.id} that honesty matters more than bragging, and that a brave story should tell the truth."
        ),
        QAItem(
            question=f"How did the story end after the weekly swig?",
            answer=f"It ended with {hero.id} finishing the swig calmly, after admitting the truth and choosing {swig.moral} instead of fear."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    swig = world.facts["swig"]
    return [
        QAItem(
            question="What does chickened out mean?",
            answer="To chickened out means to back away from something because of fear, even after you said you would do it."
        ),
        QAItem(
            question="What does weekly mean?",
            answer="Weekly means something happens once every week, like a regular Saturday habit."
        ),
        QAItem(
            question="What is a swig?",
            answer="A swig is a quick drink taken in one gulp or two."
        ),
        QAItem(
            question="What is a moral value?",
            answer=f"A moral value is a good way to live, such as honesty, courage, or kindness; this story highlights {swig.moral}."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = [f"place={world.place.label}"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
hero(H) :- hero_name(H).
elder(E) :- elder_name(E).
weekly_swig(S) :- swig(S), weekly(S).
conflict(H,S) :- fear(H), weekly_swig(S).
flashback(H) :- trigger(H,T), old_scene(H,T).
moral_turn(H,M) :- moral_of(S,M), swig(S), honesty(H).
resolved(H,S) :- conflict(H,S), honesty(H), courage(H), not fear(H).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for sid, sw in SWIGS.items():
        lines.append(asp.fact("swig", sid))
        if sw.weekly:
            lines.append(asp.fact("weekly", sid))
        lines.append(asp.fact("moral_of", sid, sw.moral))
        if sw.risky:
            lines.append(asp.fact("risky", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show moral_of/2."))
    asp_morals = set(asp.atoms(model, "moral_of"))
    py_morals = set((sid, sw.moral) for sid, sw in SWIGS.items())
    if asp_morals != py_morals:
        print("MISMATCH between ASP and python moral registry.")
        print("only in asp:", sorted(asp_morals - py_morals))
        print("only in python:", sorted(py_morals - asp_morals))
        return 1
    print(f"OK: ASP and python agree on {len(py_morals)} swigs.")
    return 0


# ---------------------------------------------------------------------------
# Story API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld with a weekly swig, conflict, flashback, and moral value.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--swig", choices=SWIGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=ELDERS)
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


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for pid, place in PLACES.items():
        for sid, sw in SWIGS.items():
            if reasonable_combo(place, sw):
                out.append((pid, sid))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.swig:
        combos = [c for c in combos if c[1] == args.swig]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place_id, swig_id = rng.choice(sorted(combos))
    swig = SWIGS[swig_id]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(ELDERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place_id, swig=swig_id, name=name, gender=gender, elder=elder, trait=trait)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    swig = SWIGS[params.swig]
    world = World(place)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=[params.trait, "stubborn"]))
    elder = world.add(Entity(id=params.elder, kind="character", type=params.elder, label=params.elder))
    world.facts.update(params=params, hero=hero, elder=elder, swig=swig)

    tell_story(world, hero, elder, swig)

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


# ---------------------------------------------------------------------------
# ASP helpers / CLI
# ---------------------------------------------------------------------------

def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show place/1.\n#show swig/1."))
    return sorted(set(asp.atoms(model, "place"))), sorted(set(asp.atoms(model, "swig")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show moral_of/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = []
        for i, (place_id, swig_id) in enumerate(sorted(valid_combos())):
            p = StoryParams(
                place=place_id,
                swig=swig_id,
                name=GIRL_NAMES[i % len(GIRL_NAMES)],
                gender="girl" if i % 2 == 0 else "boy",
                elder=ELDERS[i % len(ELDERS)],
                trait=TRAITS[i % len(TRAITS)],
                seed=base_seed + i,
            )
            samples.append(generate(p))
    else:
        samples = []
        seen = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
