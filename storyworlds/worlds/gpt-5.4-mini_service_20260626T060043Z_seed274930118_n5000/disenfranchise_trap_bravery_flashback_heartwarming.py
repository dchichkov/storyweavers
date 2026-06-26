#!/usr/bin/env python3
"""
storyworlds/worlds/disenfranchise_trap_bravery_flashback_heartwarming.py
========================================================================

A small heartwarming story world about fairness, a trapped choice, bravery,
and a gentle flashback that helps everyone belong.

Premise:
- A child helps a small community make a fair choice.
- A trap-like jam blocks the ballots or tokens, leaving some voices out.
- The hero shows bravery, remembers a kind lesson in a flashback, and frees
  the stuck choice so everyone can be heard.

The world is deliberately tiny and state-driven: the story changes based on
who is left out, what is trapped, where the problem happens, and how the
hero resolves it.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    verb: str
    noun: str
    trap: str
    blocked: str
    flashback: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    verb: str
    outcome: str
    helps: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    challenge: str
    fix: str
    name: str
    gender: str
    mentor: str
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


SETTINGS = {
    "classroom": Setting(
        place="the classroom",
        detail="The room was bright, with a little circle of chairs near the window.",
        affords={"vote", "share"},
    ),
    "clubhouse": Setting(
        place="the clubhouse",
        detail="The clubhouse smelled like crayons and warm tea.",
        affords={"vote", "share"},
    ),
    "garden_shed": Setting(
        place="the garden shed",
        detail="The shed was cozy, with a table for plans and a shelf for tiny things.",
        affords={"vote", "share"},
    ),
}

CHALLENGES = {
    "token_vote": Challenge(
        id="token_vote",
        verb="choose the next game with tokens",
        noun="tokens",
        trap="the token jar tipped behind a bench",
        blocked="the smallest kids could not reach the tokens",
        flashback="grandma once said a fair choice only feels warm when everyone can take part",
        risk="some voices were being left out",
        tags={"vote", "fairness", "trap"},
    ),
    "song_vote": Challenge(
        id="song_vote",
        verb="pick the song for story time",
        noun="paper slips",
        trap="the paper slips slid into a tight drawer",
        blocked="the littlest children could not slip in their choices",
        flashback="a teacher once reminded the class that brave hearts make room for shy voices",
        risk="the quiet choices were getting trapped",
        tags={"vote", "music", "trap"},
    ),
    "banner_vote": Challenge(
        id="banner_vote",
        verb="decide the color of the welcome banner",
        noun="color cards",
        trap="the color cards fell under a low crate",
        blocked="the younger children could not reach the cards",
        flashback="grandpa once showed how kindness grows when everyone gets a turn",
        risk="the choice was becoming unfair",
        tags={"vote", "colors", "trap"},
    ),
}

FIXES = {
    "lift_bench": Fix(
        id="lift_bench",
        label="a careful lift",
        verb="lift the bench",
        outcome="the hidden tokens rolled out",
        helps={"token_vote"},
    ),
    "open_drawer": Fix(
        id="open_drawer",
        label="a gentle pull",
        verb="open the drawer all the way",
        outcome="the paper slips slid free",
        helps={"song_vote"},
    ),
    "slide_crate": Fix(
        id="slide_crate",
        label="a brave slide",
        verb="slide the crate aside",
        outcome="the color cards fluttered back into view",
        helps={"banner_vote"},
    ),
}

GIRL_NAMES = ["Mia", "Lina", "Nora", "Ivy", "Maya", "Ella"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Leo", "Milo", "Ben"]
TRAITS = ["brave", "kind", "gentle", "curious", "steady"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for challenge_id in setting.affords:
            for fix_id, fix in FIXES.items():
                if challenge_id in fix.helps:
                    combos.append((place, challenge_id, fix_id))
    return combos


def prize_at_risk(challenge: Challenge) -> bool:
    return True


def select_fix(challenge: Challenge) -> Optional[Fix]:
    for fix in FIXES.values():
        if challenge.id in fix.helps:
            return fix
    return None


def explain_rejection(challenge: Challenge) -> str:
    return (
        f"(No story: the challenge '{challenge.id}' does not have a compatible fix "
        f"in this tiny world.)"
    )


def explain_gender(gender: str, name: str) -> str:
    return f"(No story: {name} is not a valid choice for gender {gender} in this world.)"


def tell(setting: Setting, challenge: Challenge, fix: Fix, hero_name: str, gender: str,
         mentor_type: str, trait: str) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=gender,
        label=hero_name,
        traits if False else "",  # pragma: no cover style placeholder not used
    ))
    mentor = world.add(Entity(id="Mentor", kind="character", type=mentor_type, label=mentor_type))
    crowd = world.add(Entity(id="Crowd", kind="character", type="group", label="the children", plural=True))

    hero.memes["bravery"] = 0.0
    hero.memes["care"] = 0.0
    hero.memes["warmth"] = 0.0

    world.say(f"{hero.id} was a {trait} child who loved fair turns and happy voices.")
    world.say(f"{hero.id} liked {challenge.verb}, because everyone smiled when choices were shared.")
    world.say(f"One day, the class gathered in {setting.place}. {setting.detail}")

    world.para()
    world.say(f"They were ready to vote, but {challenge.trap}; {challenge.blocked}.")
    world.say(f"That meant {challenge.risk}.")
    world.say(f"{hero.id} felt a small knot in {hero.pronoun('possessive')} chest, then took a deep breath.")
    hero.memes["bravery"] += 1
    world.say(
        f"{hero.id} remembered a flashback: {challenge.flashback}."
    )
    world.say(
        f"That memory made {hero.id} stand up straight. {hero.pronoun().capitalize()} said, "
        f"\"We can't leave anyone out.\""
    )

    world.para()
    world.say(
        f"With quiet bravery, {hero.id} chose {fix.label}. {hero.pronoun().capitalize()} "
        f"{fix.verb}, and soon {fix.outcome}."
    )
    hero.memes["care"] += 1
    hero.memes["warmth"] += 1
    world.say(
        f"The children cheered because now every little hand could take part."
    )
    world.say(
        f"{hero.id} smiled when {mentor_type} nodded proudly and said, "
        f"\"That was a brave way to protect a fair choice.\""
    )

    world.facts.update(
        hero=hero,
        mentor=mentor,
        crowd=crowd,
        challenge=challenge,
        fix=fix,
        setting=setting,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    challenge = f["challenge"]
    return [
        f'Write a heartwarming story about bravery, a trapped choice, and a flashback that helps {hero.id}.',
        f"Tell a gentle story where {hero.id} notices that {challenge.noun} are trapped and some children are disenfranchised.",
        f'Write a short story for a child about fairness, a trap, and a brave fix in {world.setting.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    challenge = f["challenge"]
    fix = f["fix"]
    mentor = f["mentor"]
    return [
        QAItem(
            question=f"What problem did {hero.id} notice in {world.setting.place}?",
            answer=(
                f"{hero.id} noticed that {challenge.noun} were trapped, so some children could not vote. "
                f"That made the choice unfair."
            ),
        ),
        QAItem(
            question=f"What helped {hero.id} feel brave enough to act?",
            answer=(
                f"A flashback about fairness helped {hero.id} feel brave. "
                f"{challenge.flashback}"
            ),
        ),
        QAItem(
            question=f"How did {hero.id} fix the problem?",
            answer=(
                f"{hero.id} used {fix.label} and {fix.verb}, so {fix.outcome}. "
                f"Then everyone could take part again."
            ),
        ),
        QAItem(
            question=f"Who praised {hero.id} at the end?",
            answer=f"{mentor.label.capitalize()} praised {hero.id} for protecting a fair choice.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does disenfranchise mean?",
            answer=(
                "To disenfranchise someone means to keep them from taking part in a vote "
                "or from having an equal voice."
            ),
        ),
        QAItem(
            question="What is a trap?",
            answer=(
                "A trap is something that holds something else in place or makes it hard to get free."
            ),
        ),
        QAItem(
            question="What is bravery?",
            answer=(
                "Bravery is being scared or unsure and still doing the right thing."
            ),
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer=(
                "A flashback is a moment when the story remembers something from before that helps explain now."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} memes={dict(e.memes)} meters={dict(e.meters)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, C, F) :- setting(Place), challenge(C), fix(F), helps(F, C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for cid, ch in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        for tag in sorted(ch.tags):
            lines.append(asp.fact("tags", cid, tag))
    for fid, fx in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for c in sorted(fx.helps):
            lines.append(asp.fact("helps", fid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming fairness story world with a trapped choice.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mentor", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--name")
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
    if args.challenge and args.fix:
        ch, fx = CHALLENGES[args.challenge], FIXES[args.fix]
        if args.challenge not in fx.helps:
            raise StoryError(explain_rejection(ch))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.challenge is None or c[1] == args.challenge)
        and (args.fix is None or c[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, challenge_id, fix_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    mentor = args.mentor or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, challenge=challenge_id, fix=fix_id,
                       name=name, gender=gender, mentor=mentor, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        CHALLENGES[params.challenge],
        FIXES[params.fix],
        params.name,
        params.gender,
        params.mentor,
        params.trait,
    )
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
    StoryParams(place="classroom", challenge="token_vote", fix="lift_bench",
                name="Mia", gender="girl", mentor="grandmother", trait="brave"),
    StoryParams(place="clubhouse", challenge="song_vote", fix="open_drawer",
                name="Theo", gender="boy", mentor="mother", trait="kind"),
    StoryParams(place="garden_shed", challenge="banner_vote", fix="slide_crate",
                name="Nora", gender="girl", mentor="grandfather", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print(" ", c)
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
