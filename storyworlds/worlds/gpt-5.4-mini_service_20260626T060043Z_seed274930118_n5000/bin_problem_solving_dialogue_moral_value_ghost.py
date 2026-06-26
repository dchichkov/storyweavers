#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/bin_problem_solving_dialogue_moral_value_ghost.py
====================================================================================================

A small ghost-story world about a bin, a scared child, a kind helper, and a
problem solved by talking, listening, and doing the right thing.

Premise:
- A child hears spooky noises near a bin after dusk.
- The child feels fear and wants to run away.
- A sibling or caretaker helps them look carefully and speak honestly.
- The "ghost" turns out to be a harmless animal or trick of the dark.
- The ending carries a moral value: courage, honesty, kindness, or responsibility.

This module follows the Storyweavers storyworld contract:
- standalone stdlib script under storyworlds/worlds/
- eager import of results.py; lazy import of asp.py in ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str
    indoors: bool
    after_dark: bool
    eerie: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    clue: str
    source_noise: str
    risky_action: str
    lesson: str
    moral: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Bin:
    label: str = "bin"
    phrase: str = "the bin"
    kind: str = "bin"
    can_hold: set[str] = field(default_factory=lambda: {"lost_key", "scrap_paper", "cat"})
    sounds: set[str] = field(default_factory=lambda: {"bump", "scrape", "rattle"})


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.bin_contents: list[str] = []

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


PROBLEMS = {
    "bin_noise": Problem(
        id="bin_noise",
        clue="a spooky noise near a bin",
        source_noise="the wind and a trapped little animal",
        risky_action="run away without looking",
        lesson="courage and careful listening",
        moral="It is brave to look carefully before you panic.",
        tags={"ghost", "bin", "night", "fear"},
    ),
    "bin_missing_item": Problem(
        id="bin_missing_item",
        clue="a missing item that might be in the bin",
        source_noise="something light shifting inside",
        risky_action="poke around alone in the dark",
        lesson="honesty and asking for help",
        moral="It is wise to tell the truth and ask for help.",
        tags={"bin", "lost", "help"},
    ),
    "bin_friend_help": Problem(
        id="bin_friend_help",
        clue="a strange sound that scares a friend",
        source_noise="a friendly cat hiding from rain",
        risky_action="laugh at the scared friend",
        lesson="kindness and reassurance",
        moral="Kind words can make a frightened friend feel safe.",
        tags={"bin", "friend", "kindness"},
    ),
}

SETTINGS = {
    "backyard": Setting(place="the backyard", indoors=False, after_dark=True, eerie="the moon was thin and pale", affordances={"peek", "listen", "call"}),
    "alley": Setting(place="the alley", indoors=False, after_dark=True, eerie="a lamp hummed over the fence", affordances={"peek", "listen", "call"}),
    "garage": Setting(place="the garage", indoors=True, after_dark=True, eerie="the room smelled like dust and old raincoats", affordances={"peek", "listen", "call"}),
}

BINS = {
    "trash_bin": Bin(label="trash bin", phrase="the trash bin"),
    "blue_bin": Bin(label="blue bin", phrase="the blue bin"),
    "garden_bin": Bin(label="garden bin", phrase="the garden bin"),
}

GHOST_TRUTHS = {
    "wind": ("What makes a bin rattle on a windy night?", "Wind can push light lids and loose things so they bump and rattle."),
    "cat": ("Why might a cat hide in a bin or behind one?", "A cat may hide when it feels shy, wet, or scared, and then it can make small mysterious sounds."),
    "echo": ("What is an echo?", "An echo is a sound that bounces off walls and comes back to your ears."),
    "dark": ("Why do things look scary in the dark?", "In the dark, shapes are harder to see, so ordinary things can look spooky until you check them carefully."),
    "honesty": ("Why is it good to tell the truth?", "Telling the truth helps people solve problems together and trust one another."),
    "help": ("Why ask for help when something feels hard?", "Help can make a problem safer and easier to solve."),
}

NAMES = {
    "girl": ["Mina", "Tessa", "Lila", "Nora", "Ivy", "June"],
    "boy": ["Owen", "Milo", "Eli", "Theo", "Finn", "Arlo"],
}
GENDERS = ["girl", "boy"]
RELATIVES = ["mother", "father", "grandmother", "grandfather", "big sister", "big brother"]
TRAITS = ["brave", "curious", "careful", "quiet", "sensitive"]


@dataclass
class StoryParams:
    place: str
    problem: str
    bin_kind: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def _init_entity(eid: str, kind: str, type_: str, label: str = "", plural: bool = False) -> Entity:
    return Entity(id=eid, kind=kind, type=type_, label=label, plural=plural, meters={}, memes={})


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero = world.add(_init_entity(params.name, "character", params.gender))
    helper = world.add(_init_entity("Helper", "character", params.helper, label="the helper"))
    bin_obj = world.add(_init_entity("Bin", "thing", "bin", label=BINS[params.bin_kind].label))
    world.facts.update(hero=hero, helper=helper, bin=bin_obj, problem=PROBLEMS[params.problem], params=params)
    return world


def _hero_intro(world: World) -> None:
    hero: Entity = world.facts["hero"]
    trait = world.facts["params"].trait
    world.say(f"{hero.id} was a {trait} little {hero.type} who noticed every odd sound after sunset.")
    world.say(f"On nights when {world.setting.eerie}, {hero.id} liked to stay close to the light.")


def _problem_setup(world: World) -> None:
    hero: Entity = world.facts["hero"]
    problem: Problem = world.facts["problem"]
    bin_obj: Entity = world.facts["bin"]
    world.say(f"Near {bin_obj.label_word}, there was {problem.clue}.")
    world.say(f"{hero.id} heard it and felt a shiver of fear climb up {hero.pronoun('possessive')} back.")


def _fear_and_dialogue(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    problem: Problem = world.facts["problem"]
    hero.memes["fear"] = 1.0
    hero.memes["need_help"] = 1.0
    world.say(f'"What if it is a ghost?" {hero.id} whispered.')
    world.say(f'{helper.label_word.capitalize()} listened and said, "Let\'s not guess. Let\'s look carefully and be kind about it."')
    world.say(f"{hero.id} nodded, because {problem.lesson} sounded better than running away.")


def _investigate(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    bin_obj: Entity = world.facts["bin"]
    problem: Problem = world.facts["problem"]
    hero.memes["curiosity"] = 1.0
    world.say(f"They walked slowly to {bin_obj.label_word}, keeping their voices soft.")
    world.say(f"{hero.id} held {helper.pronoun('possessive')} hand and peered closer.")
    world.say(f'From inside came a {problem.source_noise}, not a scary ghost voice at all.')


def _solve(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    problem: Problem = world.facts["problem"]
    bin_obj: Entity = world.facts["bin"]
    hero.memes["courage"] = 1.0
    helper.memes["patience"] = 1.0

    if problem.id == "bin_noise":
        world.bin_contents = ["a small cat", "a scrap of paper"]
        world.say(f'{helper.label_word.capitalize()} crouched down and gently tapped the side of {bin_obj.label_word}.')
        world.say(f"A tiny cat jumped out, shook its whiskers, and blinked in the moonlight.")
        world.say(f'"Oh!" {hero.id} said. "It was only a cat hiding from the wind."')
    elif problem.id == "bin_missing_item":
        world.bin_contents = ["a lost key", "old notes"]
        world.say(f'{helper.label_word.capitalize()} suggested they check together instead of searching alone.')
        world.say(f"{hero.id} found the missing key tucked beside a folded note at the bottom of {bin_obj.label_word}.")
        world.say(f'"I should have asked sooner," {hero.id} admitted.')
    else:
        world.bin_contents = ["a wet cat", "a fallen mitt"]
        world.say(f'{helper.label_word.capitalize()} shone a light behind {bin_obj.label_word}.')
        world.say(f"A wet cat trotted out and rubbed against {hero.id}'s shoe, safe now that it had been found.")
        world.say(f'"You were scared, but you still helped," {helper.label_word} said kindly.')
    world.say(f"{hero.id} smiled because {problem.moral}")


def _ending(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    problem: Problem = world.facts["problem"]
    bin_obj: Entity = world.facts["bin"]
    if problem.id == "bin_noise":
        ending = f"In the end, {bin_obj.label_word} was just a regular bin again, and the night felt friendly instead of frightful."
    elif problem.id == "bin_missing_item":
        ending = f"In the end, the missing thing was found, and {hero.id} was glad {helper.pronoun('subject')} had told the truth."
    else:
        ending = f"In the end, the frightened friend felt better, and {hero.id} learned that kindness can calm even a spooky moment."
    world.say(ending)


def tell(params: StoryParams) -> World:
    world = build_world(params)
    _hero_intro(world)
    world.para()
    _problem_setup(world)
    _fear_and_dialogue(world)
    world.para()
    _investigate(world)
    _solve(world)
    world.para()
    _ending(world)
    world.facts["solved"] = True
    return world


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoors:
            lines.append(asp.fact("indoors", sid))
        if setting.after_dark:
            lines.append(asp.fact("after_dark", sid))
        for a in sorted(setting.affordances):
            lines.append(asp.fact("affords", sid, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("tag", pid, t))
    for bid, b in BINS.items():
        lines.append(asp.fact("bin", bid))
        for s in sorted(b.sounds):
            lines.append(asp.fact("sound", bid, s))
    return "\n".join(lines)


ASP_RULES = r"""
% A bin-story is reasonable when the setting is after dark and the problem has a
% clue that can be investigated by peeking, listening, or calling for help.
reasonable_story(S, P, B) :- setting(S), problem(P), bin(B), after_dark(S).

% A good resolution requires the child to listen, speak, and then discover a
% harmless explanation instead of a true ghost.
solves(P) :- problem(P).
ghost_story(P) :- problem(P), tag(P, ghost).
moral_story(P, moral_value) :- problem(P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable(params: StoryParams) -> bool:
    return params.place in SETTINGS and params.problem in PROBLEMS and params.bin_kind in BINS


def asp_reasonable_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable_story/3."))
    return sorted(set(asp.atoms(model, "reasonable_story")))


def asp_verify() -> int:
    py = set((p.place, p.problem, p.bin_kind) for p in valid_combos())
    cl = set(asp_reasonable_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in SETTINGS:
        for problem in PROBLEMS:
            for bin_kind in BINS:
                combos.append((place, problem, bin_kind))
    return combos


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    prob: Problem = world.facts["problem"]
    return [
        f'Write a short ghost story for a young child that includes the word "bin" and ends with {prob.moral.lower()}',
        f"Tell a gentle spooky story where {p.name} hears a strange noise near a {p.bin_kind} and learns {prob.lesson}.",
        f"Write a simple story with dialogue about a child, a bin, and a problem that gets solved by careful listening.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    problem: Problem = world.facts["problem"]
    bin_obj: Entity = world.facts["bin"]
    return [
        QAItem(
            question=f"What did {hero.id} hear near {bin_obj.label_word}?",
            answer=f"{hero.id} heard a spooky sound near {bin_obj.label_word}, but it turned out to have a simple cause instead of a real ghost.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.label_word} solve the problem?",
            answer=f"They talked quietly, looked carefully near {bin_obj.label_word}, and found the harmless source of the sound together.",
        ),
        QAItem(
            question=f"What moral lesson did {hero.id} learn?",
            answer=problem.moral,
        ),
        QAItem(
            question=f"Why was {hero.id} afraid at first?",
            answer=f"{hero.id} was afraid because {problem.clue} sounded ghostly in the dark, even though it was not actually dangerous.",
        ),
        QAItem(
            question=f"What did the helper say to help {hero.id}?",
            answer=f'{helper.label_word.capitalize()} said, "Let\'s not guess. Let\'s look carefully and be kind about it."',
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question=q, answer=a) for q, a in GHOST_TRUTHS.values()
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  bin contents: {world.bin_contents}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="backyard", problem="bin_noise", bin_kind="trash_bin", name="Mina", gender="girl", helper="mother", trait="curious"),
    StoryParams(place="alley", problem="bin_missing_item", bin_kind="blue_bin", name="Owen", gender="boy", helper="father", trait="careful"),
    StoryParams(place="garage", problem="bin_friend_help", bin_kind="garden_bin", name="Lila", gender="girl", helper="grandmother", trait="brave"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world about a bin, dialogue, problem solving, and a moral ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--bin-kind", choices=BINS)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=RELATIVES)
    ap.add_argument("--trait", choices=TRAITS)
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
    problem = args.problem or rng.choice(list(PROBLEMS))
    bin_kind = args.bin_kind or rng.choice(list(BINS))
    gender = args.gender or rng.choice(GENDERS)
    if args.name:
        name = args.name
    else:
        name = rng.choice(NAMES[gender])
    helper = args.helper or rng.choice(RELATIVES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, bin_kind=bin_kind, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    if not python_reasonable(params):
        raise StoryError("The requested story parameters are not reasonable for this world.")
    world = tell(params)
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
        print(asp_program("#show reasonable_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show reasonable_story/3."))
        combos = sorted(set(asp.atoms(model, "reasonable_story")))
        print(f"{len(combos)} reasonable story combos:")
        for c in combos:
            print("  ", c)
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
            header = f"### {p.name}: {p.problem} at {p.place} ({p.bin_kind})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
