#!/usr/bin/env python3
"""
A standalone storyworld for a tiny whodunit set in a craft workshop.

Premise:
- A child is making a simple craft in a workshop.
- A small remote is needed for the craft project, but it goes missing.
- The story follows clue-gathering, inner monologue suspicion, and a reveal.
- The ending proves who moved the remote and why.

This world supports:
- deterministic generation from parameters
- story QA and world QA
- inline ASP twin for parity checking
- trace output of the simulated world state
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the craft workshop"
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    object_label: str
    object_phrase: str
    use: str
    missing_question: str
    finding: str
    clue: str
    final_reveal: str


@dataclass
class StoryParams:
    mystery: str
    name: str
    gender: str
    helper: str
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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "craft_workshop": Setting(place="the craft workshop", affords={"mystery"}),
}

MYSTERIES = {
    "remote": Mystery(
        id="remote",
        object_label="remote",
        object_phrase="a small red remote",
        use="turn on the little fan for drying paint",
        missing_question="where the remote had gone",
        finding="under a basket of ribbon scraps",
        clue="a trail of glitter that pointed away from the glue table",
        final_reveal="the helper had moved it so no one would press the buttons too soon",
    ),
}

GIRL_NAMES = ["Maya", "Lina", "Nora", "Zoe", "Ivy", "Tessa"]
BOY_NAMES = ["Eli", "Noah", "Finn", "Owen", "Theo", "Sam"]
HELPERS = ["friend", "cousin", "brother", "sister", "helper", "parent"]
TRAITS = ["careful", "curious", "quiet", "thoughtful", "bright"]


def valid_combos() -> list[tuple[str, str]]:
    return [("craft_workshop", "remote")]


def reasonableness_gate(params: StoryParams) -> None:
    if params.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if params.name.strip() == "":
        raise StoryError("A child name is required.")
    if params.gender not in {"girl", "boy"}:
        raise StoryError("Gender must be girl or boy.")


def _inner_thought(world: World, hero: Entity, text: str) -> None:
    world.say(f"{hero.pronoun().capitalize()} thought, “{text}”")


def _discover_clue(world: World, hero: Entity, clue: str) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(f"Near the worktable, {hero.id} noticed {clue}.")


def _ask_helper(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    world.say(
        f"{hero.id} asked {helper.id} if {helper.pronoun('subject')} had seen the {mystery.object_label}."
    )
    _inner_thought(world, hero, f"If the remote was missing, someone must have moved it on purpose.")


def _search(world: World, hero: Entity, mystery: Mystery) -> None:
    world.say(f"{hero.id} checked the paint shelf, the ribbon bin, and the glue tray.")
    world.say(f"The {mystery.object_label} was not on the table, and that made the room feel very hush-hush.")


def _reveal(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    world.say(
        f"At last, {hero.id} found {mystery.finding}. "
        f"It was the {mystery.object_label}."
    )
    world.say(
        f"{helper.id} confessed that {helper.pronoun().capitalize()} had moved it because {mystery.final_reveal}."
    )
    world.say(
        f"{hero.id} let out a small breath and smiled, because the mystery was solved and the craft could continue."
    )


def tell(mystery: Mystery, name: str = "Maya", gender: str = "girl", helper_kind: str = "friend") -> World:
    world = World(SETTINGS["craft_workshop"])
    hero = world.add(Entity(id=name, kind="character", type=gender, traits=["little", "curious"]))
    helper = world.add(Entity(id=f"{helper_kind}", kind="character", type=helper_kind if helper_kind in {"mother", "father", "girl", "boy"} else "girl"))
    remote = world.add(Entity(
        id="remote",
        kind="thing",
        type="remote",
        label="remote",
        phrase=mystery.object_phrase,
        owner=hero.id,
    ))
    world.facts.update(hero=hero, helper=helper, remote=remote, mystery=mystery)

    world.say(f"{hero.id} was a little curious {gender} in {world.setting.place}.")
    world.say(
        f"{hero.id} was making a bright little craft, and the remote was needed to {mystery.use}."
    )
    world.say(f"Then {hero.id} looked up and noticed the remote was gone.")

    world.para()
    _search(world, hero, mystery)
    _inner_thought(world, hero, f"Who would hide a remote in a craft workshop?")
    _discover_clue(world, hero, mystery.clue)
    _ask_helper(world, hero, helper, mystery)

    world.para()
    world.say(f"{hero.id} followed the clue carefully.")
    _reveal(world, hero, helper, mystery)

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    helper = f["helper"]
    return [
        f"Write a short whodunit for a child named {hero.id} in {world.setting.place} about a missing {mystery.object_label}.",
        f"Tell a gentle mystery with inner monologue where {hero.id} wonders who moved the {mystery.object_label} and asks {helper.id} for help.",
        f"Write a tiny craft-workshop detective story that ends with the {mystery.object_label} being found and the reason explained.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mystery = f["mystery"]
    return [
        QAItem(
            question=f"What was missing from the craft workshop?",
            answer=f"The {mystery.object_label} was missing.",
        ),
        QAItem(
            question=f"Why did {hero.id} need the {mystery.object_label}?",
            answer=f"{hero.id} needed the {mystery.object_label} to {mystery.use}.",
        ),
        QAItem(
            question=f"How did {hero.id} think about the mystery?",
            answer=f"{hero.id} kept thinking to {hero.pronoun('subject')}self that someone must have moved it on purpose.",
        ),
        QAItem(
            question=f"Who explained what happened to the {mystery.object_label}?",
            answer=f"{helper.id} explained that the {mystery.object_label} had been moved for a careful reason.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a remote?",
            answer="A remote is a small controller you press to make a device do things from a little distance.",
        ),
        QAItem(
            question="What is a craft workshop?",
            answer="A craft workshop is a place where people make art, build projects, and use tools like glue, paper, and ribbon.",
        ),
        QAItem(
            question="Why do detectives look for clues?",
            answer="Detectives look for clues because clues help them figure out what happened and who did what.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        lines.append(f"{e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(X) :- helper_name(X).
missing(remote) :- mystery(remote).
needs_remote(H) :- hero(H), missing(remote).
clue_found(H) :- hero(H), clue(H).
solved(H) :- clue_found(H), helper(X), moved_for_reason(X).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy
    lines = []
    for name in MYSTERIES:
        lines.append(asp.fact("mystery", name))
        lines.append(asp.fact("missing", name))
    for name in GIRL_NAMES + BOY_NAMES:
        lines.append(asp.fact("hero_name", name))
    for helper in HELPERS:
        lines.append(asp.fact("helper_name", helper))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp  # lazy
    model = asp.one_model(asp_program("#show missing/1."))
    got = set(asp.atoms(model, "missing"))
    expected = {("remote",)}
    if got != expected:
        print("ASP mismatch")
        print("got:", sorted(got))
        print("expected:", sorted(expected))
        return 1
    print("OK: ASP parity check passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Craft-workshop whodunit storyworld with inner monologue.")
    ap.add_argument("--mystery", choices=MYSTERIES.keys(), default="remote")
    ap.add_argument("--name", choices=GIRL_NAMES + BOY_NAMES, default=None)
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--helper", choices=HELPERS, default=None)
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
    mystery = args.mystery
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    params = StoryParams(mystery=mystery, name=name, gender=gender, helper=helper)
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    mystery = MYSTERIES[params.mystery]
    world = tell(mystery, params.name, params.gender, params.helper)
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


CURATED = [
    StoryParams(mystery="remote", name="Maya", gender="girl", helper="friend"),
    StoryParams(mystery="remote", name="Eli", gender="boy", helper="sister"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show missing/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show missing/1."))
        print(sorted(asp.atoms(model, "missing")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
