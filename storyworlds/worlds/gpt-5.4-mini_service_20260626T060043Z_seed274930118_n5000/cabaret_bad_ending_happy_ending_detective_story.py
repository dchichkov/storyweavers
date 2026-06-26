#!/usr/bin/env python3
"""
A tiny storyworld: a detective story at a cabaret, with a bad ending that is
turned into a happy ending by noticing the right clue.

The world is small and classical:
- a cabaret theater
- a performer
- a missing prop / broken spotlight / mistaken note
- a detective who follows clues
- a bad ending path that can be avoided
- a happy ending when the truth is found

The prose is generated from the simulated state, not from a fixed template with
swapped nouns. The core tension is whether the cabaret show ends in a flop or a
cheerful finale.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "singer"}
        male = {"boy", "man", "father", "magician", "detective"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the cabaret"
    time: str = "night"


@dataclass
class StoryParams:
    name: str
    gender: str
    detective_name: str
    clue: str
    prop: str
    seed: Optional[int] = None


@dataclass
class CabaretAct:
    id: str
    title: str
    clue: str
    prop: str
    bad_result: str
    happy_result: str
    bad_image: str
    happy_image: str


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTING = Setting()

ACTS = {
    "feather_mist": CabaretAct(
        id="feather_mist",
        title="the Feather Mist number",
        clue="a white feather",
        prop="a silver fan",
        bad_result="the song would end in a sad hush",
        happy_result="the song would end in bright applause",
        bad_image="the lights looked cold and the curtain drooped",
        happy_image="the lights warmed up and the curtain lifted like a smile",
    ),
    "moon_bow": CabaretAct(
        id="moon_bow",
        title="the Moon Bow dance",
        clue="a blue ribbon",
        prop="a red bow tie",
        bad_result="the dancer would miss the final spin",
        happy_result="the dancer would hit the final spin and grin",
        bad_image="the stage floor seemed lonely and bare",
        happy_image="the stage floor shone like a tiny moon",
    ),
    "merry_mask": CabaretAct(
        id="merry_mask",
        title="the Merry Mask trick",
        clue="a brass button",
        prop="a velvet mask",
        bad_result="the trick would look wrong and confuse the crowd",
        happy_result="the trick would look clever and delight the crowd",
        bad_image="a broken prop lay under the spotlight",
        happy_image="the props sat neatly in their box",
    ),
}

ROLES = {
    "girl": ["Mina", "Clara", "Nina", "Dora", "Lena", "Ivy"],
    "boy": ["Noel", "Hugo", "Eli", "Milo", "Theo", "Jasper"],
}

DETECTIVES = ["Inspector Plum", "Detective Reed", "Miss Lantern", "Mr. Vale"]

TRAITS = ["careful", "brave", "curious", "sharp-eyed", "patient"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
act(feather_mist).
act(moon_bow).
act(merry_mask).

clue(feather_mist, feather).
clue(moon_bow, ribbon).
clue(merry_mask, button).

prop(feather_mist, fan).
prop(moon_bow, bowtie).
prop(merry_mask, mask).

happy(A) :- act(A), clue(A, C), prop(A, P), C != P.
bad(A) :- act(A), clue(A, C), prop(A, C).
#show happy/1.
#show bad/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for aid, act in ACTS.items():
        lines.append(asp.fact("act", aid))
        lines.append(asp.fact("clue", aid, act.clue.split()[0]))
        lines.append(asp.fact("prop", aid, act.prop.split()[-1]))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> list[str]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show happy/1.\n#show bad/1."))
    return sorted(f"{sym.name}({','.join(str(a) for a in sym.arguments)})" for sym in model)


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def choose_act(rng: random.Random) -> CabaretAct:
    return ACTS[rng.choice(sorted(ACTS))]


def bad_match(act: CabaretAct) -> bool:
    return act.id in {"merry_mask"}


def world_from_params(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, role="performer"))
    detective = world.add(Entity(id="detective", kind="character", type="detective", label=params.detective_name, role="detective"))
    prop = world.add(Entity(id="prop", kind="thing", type="prop", label=params.prop, phrase=params.prop, owner=hero.id))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label=params.clue, phrase=params.clue))
    world.facts.update(hero=hero, detective=detective, prop=prop, clue=clue)
    return world


def introduce(world: World, act: CabaretAct) -> None:
    hero = world.facts["hero"]
    detective = world.facts["detective"]
    world.say(
        f"At the cabaret, {detective.label} watched {hero.id}, a little {hero.type}, "
        f"prepare for {act.title}."
    )
    world.say(
        f"The room smelled like dust, stage paint, and old velvet, and everyone hoped "
        f"the show would shine."
    )


def tension(world: World, act: CabaretAct) -> None:
    hero = world.facts["hero"]
    detective = world.facts["detective"]
    if bad_match(act):
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1
        world.say(
            f"But the prop on stage did not match the clue. "
            f"{act.bad_image.capitalize()}, and {hero.id} felt the bad ending creeping in."
        )
        world.say(
            f"{detective.label} frowned and said the wrong prop could spoil the whole number."
        )
    else:
        world.say(
            f"Still, something felt off. {detective.label} noticed the clue and the prop "
            f"did not quite line up, which meant there was a mystery to solve."
        )


def solve(world: World, act: CabaretAct) -> None:
    hero = world.facts["hero"]
    detective = world.facts["detective"]
    if bad_match(act):
        world.say(
            f"{detective.label} knelt by the stage and found {act.clue}. "
            f"It belonged with the real prop, not the one that was left out."
        )
        hero.memes["relief"] = hero.memes.get("relief", 0) + 1
        world.say(
            f"They swapped in {world.facts['prop'].label}, and the cabaret number changed at once."
        )
        world.say(
            f"{act.happy_image.capitalize()}, and {act.happy_result}."
        )
        world.say(
            f"{hero.id} bowed with a big smile while the audience clapped like rain on a roof."
        )
    else:
        world.say(
            f"{detective.label} matched the clue to {world.facts['prop'].label} at once. "
            f"The right prop was already there, so the mystery ended before trouble grew."
        )
        hero.memes["joy"] = hero.memes.get("joy", 0) + 1
        world.say(
            f"{act.happy_image.capitalize()}, and {act.happy_result}."
        )
        world.say(
            f"{hero.id} finished the dance with steady feet and a happy grin."
        )


def tell(act: CabaretAct, params: StoryParams) -> World:
    world = world_from_params(params)
    introduce(world, act)
    world.para()
    tension(world, act)
    world.para()
    solve(world, act)
    world.facts["act"] = act
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    act: CabaretAct = world.facts["act"]
    hero: Entity = world.facts["hero"]
    detective: Entity = world.facts["detective"]
    return [
        f"Write a short detective story set at a cabaret where {detective.label} helps {hero.id} avoid a bad ending.",
        f"Tell a child-friendly mystery about {act.title} and the clue {act.clue}.",
        f"Write a small cabaret story with a bad ending that is fixed into a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    act: CabaretAct = world.facts["act"]
    hero: Entity = world.facts["hero"]
    detective: Entity = world.facts["detective"]
    return [
        QAItem(
            question=f"Who helped solve the cabaret mystery?",
            answer=f"{detective.label} helped solve it by noticing the clue and the prop that did not match.",
        ),
        QAItem(
            question=f"What was the bad ending for {hero.id}'s show?",
            answer=f"The bad ending was that {act.bad_result}.",
        ),
        QAItem(
            question=f"What changed to make the ending happy?",
            answer=f"The detective found the right clue and the correct prop, so {act.happy_result}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cabaret?",
            answer="A cabaret is a small stage place where people sing, dance, or perform for an audience.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and solves mysteries.",
        ),
        QAItem(
            question="Why can a wrong prop cause trouble on stage?",
            answer="A wrong prop can make a performance look strange, confuse the crowd, or ruin the moment.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
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
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} role={e.role} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cabaret detective storyworld with bad and happy endings.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--detective-name", choices=DETECTIVES)
    ap.add_argument("--clue")
    ap.add_argument("--prop")
    ap.add_argument("--act", choices=sorted(ACTS))
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
    act = ACTS[args.act] if args.act else choose_act(rng)
    if args.clue and args.clue != act.clue:
        raise StoryError("That clue does not fit the chosen cabaret act.")
    if args.prop and args.prop != act.prop:
        raise StoryError("That prop does not fit the chosen cabaret act.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(ROLES[gender])
    detective_name = args.detective_name or rng.choice(DETECTIVES)
    return StoryParams(
        name=name,
        gender=gender,
        detective_name=detective_name,
        clue=act.clue,
        prop=act.prop,
    )


def generate(params: StoryParams) -> StorySample:
    act = next(a for a in ACTS.values() if a.clue == params.clue and a.prop == params.prop)
    world = tell(act, params)
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


# ---------------------------------------------------------------------------
# ASP verification
# ---------------------------------------------------------------------------

def asp_verify() -> int:
    import storyworlds.asp as asp
    program = asp_program("#show happy/1.\n#show bad/1.")
    model = asp.one_model(program)
    atoms = sorted(f"{s.name}({','.join(str(a) for a in s.arguments)})" for s in model)
    expected = ["happy(feather_mist)", "happy(moon_bow)", "happy(merry_mask)"]
    if atoms == expected:
        print("OK: ASP gate looks reasonable.")
        return 0
    print("ASP result:", atoms)
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy/1.\n#show bad/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, act in enumerate(ACTS.values()):
            p = StoryParams(
                name=ROLES["girl"][i % len(ROLES["girl"])],
                gender="girl" if i % 2 == 0 else "boy",
                detective_name=DETECTIVES[i % len(DETECTIVES)],
                clue=act.clue,
                prop=act.prop,
                seed=base_seed + i,
            )
            samples.append(generate(p))
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

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
