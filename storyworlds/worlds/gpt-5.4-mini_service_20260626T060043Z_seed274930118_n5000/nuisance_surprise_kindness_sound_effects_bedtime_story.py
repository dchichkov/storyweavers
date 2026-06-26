#!/usr/bin/env python3
"""
storyworlds/worlds/nuisance_surprise_kindness_sound_effects_bedtime_story.py
============================================================================

A small bedtime-story world about a child, a nuisance, a surprise, and a kind
fix. The narrative is driven by a simple world model with physical meters and
emotional memes.

Seed tale premise:
- It is bedtime.
- A small nuisance keeps making an annoying sound.
- The child feels uneasy, then gets a surprise.
- Someone shows kindness and the nuisance is resolved.
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
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the bedroom"
    bedtime: bool = True
    cozy: bool = True


@dataclass
class Nuisance:
    id: str
    label: str
    phrase: str
    sound: str
    surprise: str
    kindness_fix: str
    resolves_with: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    nuisance: str
    name: str
    gender: str
    helper: str
    trait: str
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

NAMES_GIRL = ["Mia", "Luna", "Nora", "Ivy", "Ella", "Zoe"]
NAMES_BOY = ["Leo", "Finn", "Theo", "Noah", "Ben", "Max"]
HELPERS = ["mother", "father", "grandmother", "grandfather"]
TRAITS = ["sleepy", "gentle", "curious", "brave", "soft-hearted", "patient"]

SETTINGS = {
    "bedroom": Setting(place="the bedroom", bedtime=True, cozy=True),
    "nursery": Setting(place="the nursery", bedtime=True, cozy=True),
    "attic-room": Setting(place="the little attic room", bedtime=True, cozy=True),
}

NUISANCES = {
    "squeaky-toy": Nuisance(
        id="squeaky-toy",
        label="a squeaky toy",
        phrase="a little toy with a squeaker inside",
        sound="squeeeak",
        surprise="a tiny ribbon tied around the toy",
        kindness_fix="wrap it in a soft cloth",
        resolves_with="a soft cloth",
        tags={"sound", "toy", "squeak"},
    ),
    "dripping-faucet": Nuisance(
        id="dripping-faucet",
        label="a dripping faucet",
        phrase="a faucet that dripped one slow drop at a time",
        sound="plink",
        surprise="a shiny cup catching the drops",
        kindness_fix="turn the handle gently and set a cup underneath",
        resolves_with="a cup",
        tags={"sound", "water", "drip"},
    ),
    "rustly-blanket": Nuisance(
        id="rustly-blanket",
        label="a rustly blanket",
        phrase="a blanket that rustled like paper leaves",
        sound="rustle-rustle",
        surprise="a hidden moon-and-star patch",
        kindness_fix="smooth it flat and tuck it in carefully",
        resolves_with="a tidy tuck-in",
        tags={"sound", "fabric", "rustle"},
    ),
    "creaky-chair": Nuisance(
        id="creaky-chair",
        label="a creaky chair",
        phrase="a chair that creaked whenever someone leaned on it",
        sound="creeeak",
        surprise="a tiny sticker shaped like a sleepy fox",
        kindness_fix="place a folded towel on the seat",
        resolves_with="a folded towel",
        tags={"sound", "wood", "creak"},
    ),
}

VALID_COMBOS = [
    ("bedroom", "squeaky-toy"),
    ("bedroom", "rustly-blanket"),
    ("nursery", "dripping-faucet"),
    ("nursery", "squeaky-toy"),
    ("attic-room", "creaky-chair"),
    ("attic-room", "rustly-blanket"),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
nuisance(N) :- nuisance_id(N).
place(P) :- place_id(P).

compatible(P, N) :- supports(P, N).
story(P, N) :- compatible(P, N).

#show compatible/2.
#show story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place_id", pid))
    for nid in NUISANCES:
        lines.append(asp.fact("nuisance_id", nid))
    for place, nuis in VALID_COMBOS:
        lines.append(asp.fact("supports", place, nuis))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Helpers / reasonableness
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    return list(VALID_COMBOS)


def explain_rejection(place: str, nuisance: str) -> str:
    return (
        f"(No story: {nuisance} does not fit a gentle bedtime scene in {place}. "
        f"Try one of: {', '.join(f'{p} + {n}' for p, n in VALID_COMBOS)}.)"
    )


def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)


def articleize(text: str) -> str:
    return text if text.startswith(("a ", "an ", "the ")) else f"a {text}"


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def tell(setting: Setting, nuisance: Nuisance, hero: Entity, helper: Entity) -> World:
    w = World(setting)
    child = w.add(hero)
    adult = w.add(helper)
    noise = w.add(Entity(
        id="nuisance",
        kind="thing",
        type="thing",
        label=nuisance.label,
        phrase=nuisance.phrase,
        owner=adult.id,
        meters={"noisy": 1.0},
        memes={"annoying": 1.0},
    ))
    w.facts.update(hero=child, helper=adult, nuisance=noise, nuisance_def=nuisance)

    child.memes["sleepy"] = 1.0
    child.memes["uneasy"] = 1.0

    w.say(
        f"At bedtime in {setting.place}, {child.id} was a little {hero.traits[0]} {child.type} "
        f"who was ready to snuggle down."
    )
    w.say(
        f"But there was {nuisance.label} nearby, and it kept making a {nuisance.sound} sound "
        f"that filled the quiet room."
    )

    w.para()
    child.memes["frustration"] = 1.0
    w.say(
        f"{child.id} wrinkled {child.pronoun('possessive')} nose and whispered, "
        f'"That noise is such a nuisance."'
    )
    w.say(
        f"The little sound made {child.id} tug {child.pronoun('possessive')} blanket closer, "
        f"but it still went {nuisance.sound}."
    )

    w.para()
    child.memes["surprise"] = 1.0
    w.say(
        f"Then came a small surprise: {helper.id} smiled and showed {child.id} "
        f"{nuisance.surprise}."
    )
    w.say(
        f"{helper.id} said, \"We can be kind to it.\""
    )
    w.say(
        f"So {helper.id} helped {nuisance.kindness_fix}, and the room sounded much softer."
    )
    noise.meters["noisy"] = 0.0
    noise.memes["annoying"] = 0.0
    child.memes["comfort"] = 1.0
    child.memes["kindness"] = 1.0

    w.para()
    w.say(
        f"Soon the nuisance was calm, and the bedtime room was quiet again."
    )
    w.say(
        f"{child.id} curled up, feeling safe and sleepy, while {helper.id} tucked the blanket in "
        f"with a gentle smile."
    )
    w.say(
        f"In the soft dark, the last little sound was only the peaceful hush of sleep."
    )
    return w


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, nuisance = f["hero"], f["helper"], f["nuisance_def"]
    return [
        f'Write a bedtime story for a young child that includes the word "nuisance" and a gentle surprise.',
        f"Tell a short story where {hero.id} notices {nuisance.label} at {world.setting.place} and {helper.id} responds with kindness.",
        f"Write a cozy bedtime tale with sound effects like {nuisance.sound} and an ending that feels calm.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    nuis: Nuisance = f["nuisance_def"]
    place = world.setting.place
    qa = [
        QAItem(
            question=f"Why did {hero.id} think {nuis.label} was a nuisance?",
            answer=(
                f"{hero.id} thought it was a nuisance because it kept making a {nuis.sound} sound "
                f"while the room was supposed to be quiet for bedtime."
            ),
        ),
        QAItem(
            question=f"What surprise did {helper.id} show {hero.id}?",
            answer=(
                f"{helper.id} showed {hero.id} {nuis.surprise}, which made the bedtime moment feel special "
                f"in {place}."
            ),
        ),
        QAItem(
            question=f"How did {helper.id} use kindness to fix the problem?",
            answer=(
                f"{helper.id} used kindness by helping {nuis.kindness_fix}, so the noise became soft and the room grew calm."
            ),
        ),
        QAItem(
            question=f"What did the room sound like at the end?",
            answer=(
                f"At the end the room was quiet again, with only the peaceful hush of sleep after the nuisance was soothed."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    nuis: Nuisance = f["nuisance_def"]
    out: list[QAItem] = [
        QAItem(
            question="What is a nuisance?",
            answer="A nuisance is something annoying or troublesome that makes it hard to relax or enjoy a quiet moment.",
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a word that helps you imagine a sound, like squeak, plink, rustle, or creak.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring toward someone or something.",
        ),
        QAItem(
            question="What is bedtime for?",
            answer="Bedtime is when children get ready to rest, settle down, and fall asleep.",
        ),
    ]
    if "sound" in nuis.tags:
        out.append(QAItem(
            question=f"Why do stories sometimes use the word {nuis.sound}?",
            answer=f"Stories use a word like {nuis.sound} because it helps readers hear the noisy part in their imagination.",
        ))
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:6}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A bedtime story world about a nuisance, a surprise, and kindness."
    )
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--nuisance", choices=sorted(NUISANCES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=sorted(set(HELPERS)))
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=sorted(TRAITS))
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
    if args.place and args.nuisance and (args.place, args.nuisance) not in valid_combos():
        raise StoryError(explain_rejection(args.place, args.nuisance))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.nuisance is None or c[1] == args.nuisance)
    ]
    if not combos:
        raise StoryError("(No valid bedtime-story combination matches the given options.)")

    place, nuisance = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or choose_name(gender, rng)
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        nuisance=nuisance,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS["bedroom"]
    # Keep the domain small but allow the parameter to vary the scene via combo.
    if params.nuisance == "dripping-faucet":
        setting = SETTINGS["nursery"]
    elif params.nuisance == "creaky-chair":
        setting = SETTINGS["attic-room"]

    hero = Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=[params.trait, "sleepy"],
        meters={"sleepiness": 1.0},
        memes={"comfort": 0.0},
    )
    helper = Entity(
        id=params.helper,
        kind="character",
        type=params.helper if params.helper in {"mother", "father"} else "adult",
        traits=["gentle"],
        meters={"calm": 1.0},
        memes={"kindness": 1.0},
    )
    world = tell(setting, NUISANCES[params.nuisance], hero, helper)
    world.facts["params"] = params
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


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/2."))
        combos = sorted(set(asp.atoms(model, "compatible")))
        print(f"{len(combos)} compatible bedtime-story combos:")
        for place, nuis in combos:
            print(f"  {place:12} {nuis}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place, nuis in valid_combos():
            p = StoryParams(
                nuisance=nuis,
                name="Mia",
                gender="girl",
                helper="mother",
                trait="gentle",
                seed=base_seed,
            )
            if nuis == "creaky-chair":
                p.name = "Leo"
                p.gender = "boy"
                p.helper = "father"
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
