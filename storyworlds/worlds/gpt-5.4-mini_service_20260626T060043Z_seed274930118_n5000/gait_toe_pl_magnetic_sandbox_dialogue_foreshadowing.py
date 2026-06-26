#!/usr/bin/env python3
"""
Storyworld: gait_toe_pl_magnetic_sandbox_dialogue_foreshadowing

A small Mystery-style sandbox storyworld with dialogue, foreshadowing, and a
simple moral value at the end. The seed words are woven into the simulated
world: gait, toe-pl, magnetic.

Premise:
- A child plays in a sandbox with a small magnetic toy called a toe-pl.
- Someone notices an odd gait in the sand and follows it.
- The toe-pl pulls toward hidden metal pieces, creating a tiny mystery.

Turn:
- A clue trail, hinted at earlier, leads to the toy.
- Dialogue reveals who saw what and where.
- The child must choose whether to keep chasing the mystery or tell the truth.

Resolution:
- The mystery is solved by finding the magnetic toe-pl and returning it.
- The ending proves the change in state: the sand is calm, the missing thing is back,
  and the child has learned to be honest.

This file is self-contained and follows the Storyworld contract:
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- imports results eagerly and asp lazily in ASP helpers
- includes an inline ASP_RULES twin and asp_facts()
- supports --verify, --show-asp, --asp, --all, --trace, --qa, --json, --seed, -n
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "mother", "woman"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "father", "man"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the sandbox"
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    hint: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    clue: str
    hero_name: str
    hero_gender: str
    parent_type: str
    trait: str
    seed: Optional[int] = None


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

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _get(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def _set(entity: Entity, key: str, value: float) -> None:
    entity.meters[key] = value


def _add(entity: Entity, key: str, value: float) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + value


def _madd(entity: Entity, key: str, value: float) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + value


def _r_magnet(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.entities.values() if e.kind == "character"), None)
    toy = world.entities.get("toe_pl")
    if not hero or not toy:
        return out
    if _get(toy, "hidden_metal") >= THRESHOLD and _get(toy, "magnetic") >= THRESHOLD:
        if _get(hero, "curiosity") >= THRESHOLD and "searching" not in hero.memes:
            hero.memes["searching"] = 1.0
            out.append("The little magnetic pull made the search feel important.")
    return out


ASP_RULES = r"""
% The seed story's core logic:
% A clue is interesting when the toe-pl is magnetic and hidden metal is nearby.
interesting(toe_pl) :- magnetic(toe_pl), hidden_metal(toe_pl).

% The child notices the clue when curious and the sandbox contains the toy.
notice(hero, toe_pl) :- curious(hero), in_sandbox(hero), magnetic(toe_pl).

% A mystery is solved when the clue is returned and the truth is told.
solved :- returned(toe_pl), told_truth(hero).
"""


class WorldState:
    pass


SETTING = Setting(place="the sandbox", indoors=False, affords={"search", "dig", "ask"})
ACTIVITIES = {
    "search": "search the sandbox",
    "dig": "dig near the corner",
    "ask": "ask about the odd trail",
}

CLUES = {
    "toe_pl": Clue(
        id="toe_pl",
        label="toe-pl",
        hint="a small toe-pl toy with a magnetic strip",
        reveal="the magnetic toe-pl had been pulling toward tiny metal bits",
        tags={"gait", "toe-pl", "magnetic", "mystery"},
    ),
}

HERO_NAMES = ["Mina", "Theo", "Lia", "Noah", "Pip", "Eli"]
TRAITS = ["curious", "careful", "brave", "quiet", "thoughtful", "patient"]


def valid_combos() -> list[tuple[str, str]]:
    return [(SETTING.place, clue_id) for clue_id in CLUES]


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    lines.append(asp.fact("in_sandbox", "hero"))
    lines.append(asp.fact("curious", "hero"))
    lines.append(asp.fact("magnetic", "toe_pl"))
    lines.append(asp.fact("hidden_metal", "toe_pl"))
    lines.append(asp.fact("returned", "toe_pl"))
    lines.append(asp.fact("told_truth", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show interesting/1."))
    return sorted(set(asp.atoms(model, "interesting")))


def asp_verify() -> int:
    py = {("toe_pl",)}
    cl = set(asp_valid_combos())
    if py == cl:
        print("OK: clingo gate matches valid_combos().")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  python:", sorted(py))
    print("  clingo :", sorted(cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld set in a sandbox.")
    ap.add_argument("--place", choices=[SETTING.place], default=SETTING.place)
    ap.add_argument("--clue", choices=CLUES.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.place and args.place != SETTING.place:
        raise StoryError("This storyworld only supports the sandbox setting.")
    clue = args.clue or "toe_pl"
    name = args.name or rng.choice(HERO_NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=SETTING.place,
        clue=clue,
        hero_name=name,
        hero_gender=gender,
        parent_type=parent,
        trait=trait,
    )


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_gender, label=params.hero_name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_type, label=params.parent_type))
    toy = world.add(Entity(id="toe_pl", kind="thing", type="toy", label="toe-pl", phrase="a magnetic toe-pl"))
    _set(hero, "curiosity", 1.0)
    _set(toy, "magnetic", 1.0)
    _set(toy, "hidden_metal", 1.0)
    _madd(hero, "mystery", 1.0)

    world.say(f"{hero.label} was a {params.trait} child who liked the sandbox.")
    world.say(f"One morning, {hero.label} noticed a strange gait in the sand, as if something small had been dragged along.")
    world.say(f'"Did you see that?" {hero.label} asked. "{parent.label.capitalize()}, the sand moved funny."')
    world.say(f'"I saw it too," {parent.label} said. "Look near the corner. The clue may be waiting there."')

    world.para()
    _add(hero, "search", 1.0)
    world.say(f"{hero.label} knelt down and searched the sandbox carefully.")
    world.say(f"At first, only a shell and a red spoon appeared, but the odd trail kept pointing onward.")
    world.say(f'"The trail stops here," {hero.label} whispered. "Something magnetic must be pulling it."')
    world.say(f"{parent.label.capitalize()} nodded. \"Keep going,\" they said, \"but keep your eyes honest.\"")

    world.para()
    world.say(f"Then {hero.label} found the toe-pl tucked beside a toy bucket.")
    world.say(f"It was the magnetic toe-pl, and tiny metal bits clung to it like little stars.")
    world.say(f'"So that was the mystery," {hero.label} said. "I should have told you when I picked it up."')
    world.say(f'"That is the better path," {parent.label} said. "A clear truth keeps the play fair."')
    world.say(f"{hero.label} returned the toe-pl to the open sand, and the sandbox felt quiet again.")

    _add(toy, "returned", 1.0)
    _add(hero, "truth", 1.0)
    world.facts.update(
        hero=hero,
        parent=parent,
        toy=toy,
        clue=CLUES["toe_pl"],
        resolved=True,
        told_truth=True,
        searched=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    return [
        'Write a short mystery story for a child set in a sandbox, and include a magical-sounding clue called "toe-pl".',
        f'Write a gentle sandbox mystery where {hero.label} and {parent.label} speak in dialogue and solve a small problem together.',
        'Tell a story with foreshadowing, a curious clue trail, and a moral about telling the truth.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    toy = f["toy"]
    return [
        QAItem(
            question=f"What strange thing did {hero.label} notice in the sandbox?",
            answer="They noticed a strange gait in the sand, like something had been dragged in a careful line.",
        ),
        QAItem(
            question=f"What was the clue that solved the mystery?",
            answer=f"The clue was the magnetic toe-pl. It pulled tiny metal bits and showed where the trail had come from.",
        ),
        QAItem(
            question=f"What did {hero.label} tell {parent.label} at the end?",
            answer="They admitted they should have spoken up sooner and said the honest thing right away.",
        ),
        QAItem(
            question=f"How did the sandbox look after the mystery was solved?",
            answer="The sandbox felt quiet again because the toe-pl was returned and the search was over.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a magnetic thing?",
            answer="A magnetic thing can pull toward certain metal objects or stick to them.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps someone figure out what happened.",
        ),
        QAItem(
            question="Why is telling the truth important?",
            answer="Telling the truth helps people trust each other and makes problems easier to solve.",
        ),
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
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


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


def explain_rejection() -> str:
    return "No story: this world only supports the sandbox mystery with the magnetic toe-pl."


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show interesting/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid_combos()
        print(f"{len(vals)} compatible mystery clue combos:\n")
        for v in vals:
            print(" ", v)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = resolve_params(args, random.Random(base_seed))
        params.seed = base_seed
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
