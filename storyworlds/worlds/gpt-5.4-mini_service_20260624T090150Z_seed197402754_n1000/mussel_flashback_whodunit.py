#!/usr/bin/env python3
"""
A tiny whodunit storyworld about a mussel, a clue, and a flashback.

The seed premise:
- A child notices a mystery by the harbor.
- A mussel-shaped clue, a missing object, and a quick flashback reveal the truth.
- The ending proves what changed: the right person is found, and the missing thing is returned.

This world keeps the prose child-facing and concrete while the simulated state
tracks both physical details (meters) and feelings (memes).
"""

from __future__ import annotations

import argparse
import copy
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
    carried_by: Optional[str] = None
    hidden_in: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
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
class Clue:
    id: str
    kind: str
    phrase: str
    points_to: str
    flashback_line: str


@dataclass
class StoryParams:
    place: str
    mystery: str
    culprit: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _flashback_reveal(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    clue = world.facts["clue"]
    if hero.memes.get("thinking", 0) < THRESHOLD:
        return out
    sig = ("flashback", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["revealed"] = clue.points_to
    out.append(clue.flashback_line)
    return out


def _solve(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    culprit = world.get(world.facts["culprit_id"])
    item = world.get("missing")
    clue = world.facts["clue"]
    if world.facts.get("revealed") != culprit.id:
        return out
    sig = ("solve", culprit.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    culprit.memes["guilt"] = culprit.memes.get("guilt", 0) + 1
    item.carried_by = culprit.id
    out.append(
        f"The clue fit at last, and {hero.id} pointed to {culprit.id}. "
        f"{culprit.id} handed back the {item.label} at once."
    )
    return out


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in (_flashback_reveal, _solve):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)


SETTINGS = {
    "harbor": Setting(place="the harbor", affords={"mussel"}),
    "pier": Setting(place="the pier", affords={"mussel"}),
    "tidepool": Setting(place="the tide pool", affords={"mussel"}),
}

MYSTERIES = {
    "mussel": Clue(
        id="clue_mussel",
        kind="mussel",
        phrase="a shiny mussel shell",
        points_to="helper",
        flashback_line=(
            "Then the hero remembered a flashback: earlier, the helper had brushed past the bowl "
            "and said the shell looked like a little boat."
        ),
    ),
}

CULPRITS = {
    "helper": ("helper", "the helpful friend"),
    "sibling": ("sibling", "the little sibling"),
    "seagull": ("seagull", "the curious seagull"),
}

HERO_NAMES = ["Mina", "Leo", "Nora", "Theo", "Ava", "Eli"]
HELPER_NAMES = ["Pip", "June", "Milo", "Zara", "Finn", "Ruby"]
GENTLE_TRAITS = ["curious", "careful", "brave", "sharp-eyed", "patient"]


def reasonableness_gate(params: StoryParams) -> None:
    if params.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if params.culprit not in CULPRITS:
        raise StoryError("Unknown culprit.")


def tell(setting: Setting, clue: Clue, culprit_key: str,
         hero_name: str, hero_type: str, helper_name: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_name))
    culprit_id, culprit_label = CULPRITS[culprit_key]
    culprit = world.add(Entity(id=culprit_id, kind="character", type="child", label=culprit_label))
    missing = world.add(Entity(
        id="missing",
        kind="thing",
        type="thing",
        label="mussel",
        phrase="a little mussel in a bowl",
        carried_by=culprit.id,
    ))

    world.facts.update(culprit_id=culprit.id, clue=clue)

    world.say(
        f"{hero_name} was a {random.choice(GENTLE_TRAITS)} little {hero_type} at {setting.place}, "
        f"and {hero_name} loved solving small mysteries."
    )
    world.say(
        f"That day, a bowl by the water was missing its {missing.label}, "
        f"and everyone looked puzzled."
    )

    world.para()
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"{hero_name} checked the sand, the bucket, and the boardwalk. "
        f"{helper_name} pointed to a wet trail near the rocks."
    )
    world.say(
        f"\"Someone carried something away,\" {helper_name} whispered. "
        f"{hero_name} stared at the trail and thought hard."
    )

    world.para()
    hero.memes["thinking"] = hero.memes.get("thinking", 0) + 1
    world.say(
        f"Then came a flashback. {hero_name} remembered {clue.flashback_line.lower()}"
    )
    propagate(world, narrate=True)

    world.para()
    if missing.carried_by == culprit.id:
        world.say(
            f"{culprit_label} blinked, then smiled shyly and gave back the {missing.label}. "
            f"The little mystery was over, and the harbor felt calm again."
        )
    else:
        world.say(
            f"The clue led nowhere, but {hero_name} kept looking until the missing {missing.label} "
            f"turned up in the end."
        )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a child that includes a mussel and a flashback.',
        f"Tell a gentle mystery about {f['hero'].label if 'hero' in f else 'a child'} at {world.setting.place} "
        f"where a mussel clue helps solve who took the missing shell.",
        "Write a small detective story with a clear clue, a remembered moment, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    helper = world.get("helper")
    culprit = world.get(world.facts["culprit_id"])
    clue: Clue = world.facts["clue"]
    item = world.get("missing")
    return [
        QAItem(
            question=f"What kind of story was this?",
            answer=f"It was a small whodunit story about a missing {item.label}, a clue, and a flashback.",
        ),
        QAItem(
            question=f"What did {hero.label} remember in the flashback?",
            answer=clue.flashback_line,
        ),
        QAItem(
            question=f"Who gave back the missing {item.label}?",
            answer=f"{culprit.label} gave back the {item.label} after the clue made the truth clear.",
        ),
        QAItem(
            question=f"Who helped {hero.label} look for clues?",
            answer=f"{helper.label} helped by pointing out the wet trail near the rocks.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mussel?",
            answer="A mussel is a small shellfish that lives in water and has a hard shell.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly goes back to something that happened earlier.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues and uses careful thinking to solve a mystery.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"{e.id}: {e.type} {e.label} {' '.join(bits)}")
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
% The mystery is solved when the flashback reveals who handled the missing item.
revealed(C) :- clue(C), flashback(C), points_to(C, CULPIT).
solved(CULPIT) :- revealed(C), culprit(CULPIT).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for key in SETTINGS:
        lines.append(asp.fact("setting", key))
        for act in SETTINGS[key].affords:
            lines.append(asp.fact("affords", key, act))
    for key, clue in MYSTERIES.items():
        lines.append(asp.fact("clue", key))
        lines.append(asp.fact("flashback", key))
        lines.append(asp.fact("points_to", key, clue.points_to))
    for key in CULPRITS:
        lines.append(asp.fact("culprit", key))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld with a mussel and a flashback.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--mystery", choices=MYSTERIES.keys(), default="mussel")
    ap.add_argument("--culprit", choices=CULPRITS.keys())
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    mystery = args.mystery
    culprit = args.culprit or rng.choice(list(CULPRITS))
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    hero_type = "girl" if hero_name in {"Mina", "Nora", "Ava"} else "boy"
    helper_type = "girl" if helper_name in {"Zara", "Ruby", "June"} else "boy"
    params = StoryParams(place=place, mystery=mystery, culprit=culprit,
                         hero_name=hero_name, hero_type=hero_type,
                         helper_name=helper_name, helper_type=helper_type)
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MYSTERIES[params.mystery], params.culprit,
                 params.hero_name, params.hero_type, params.helper_name, params.helper_type)
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


def asp_verify() -> int:
    import storyworlds.asp as asp
    program = asp_program("#show solved/1.")
    model = asp.one_model(program)
    atoms = set(asp.atoms(model, "solved"))
    if atoms:
        print("OK: ASP program produces a solved answer set.")
        return 0
    print("MISMATCH: ASP program did not produce expected solved atom.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible story pattern: a mussel mystery with a flashback and a solved ending.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("harbor", "mussel", "helper", "Mina", "girl", "Pip", "boy"),
            StoryParams("pier", "mussel", "sibling", "Leo", "boy", "Ruby", "girl"),
            StoryParams("tidepool", "mussel", "seagull", "Nora", "girl", "Finn", "boy"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(max(args.n, 1)):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
