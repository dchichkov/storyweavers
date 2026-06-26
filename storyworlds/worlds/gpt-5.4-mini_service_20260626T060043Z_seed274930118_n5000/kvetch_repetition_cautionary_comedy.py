#!/usr/bin/env python3
"""
storyworlds/worlds/kvetch_repetition_cautionary_comedy.py
=========================================================

A small comedic storyworld about a child who keeps kvetching, a parent who
keeps warning, and a repeated little problem that gets funny only once the
child chooses a safer way.

Seed premise:
---
A child wants to eat warm muffins right away, but the parent says they are too
hot. The child kvetches. The complaint repeats. The parent warns again. At last,
the child follows the caution, waits, and gets a silly but safe compromise.

This world keeps the tone close to comedy:
- repeated kvetching becomes an escalating gag,
- the caution is real and concrete,
- the ending proves the child changed from impatient grumbling to patient play.

World logic:
---
    repeated kvetching -> grumble meter rises
    grumble meter high  -> parent worry rises
    too-hot snack       -> tongue-risk if eaten immediately
    safe compromise     -> waiting game + blowing on muffins + patience
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
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


@dataclass
class Setting:
    place: str = "the kitchen"
    affords: set[str] = field(default_factory=set)


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    warmth: str
    risk: str


@dataclass
class StoryParams:
    place: str
    snack: str
    name: str
    gender: str
    parent: str
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"muffins", "soup"}),
    "table": Setting(place="the dining table", affords={"muffins"}),
    "porch": Setting(place="the porch", affords={"lemonade"}),
}

SNACKS = {
    "muffins": Snack(
        id="muffins",
        label="muffins",
        phrase="a plate of warm blueberry muffins",
        warmth="too hot",
        risk="burned tongue",
    ),
    "soup": Snack(
        id="soup",
        label="soup",
        phrase="a steaming bowl of soup",
        warmth="piping hot",
        risk="scalded mouth",
    ),
    "lemonade": Snack(
        id="lemonade",
        label="lemonade",
        phrase="a cold glass of lemonade",
        warmth="nice and chilly",
        risk="brain-freeze",
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Ava", "Zoe"]
BOY_NAMES = ["Leo", "Finn", "Ben", "Max", "Theo"]
TRAITS = ["curious", "silly", "stubborn", "bouncy", "chatty"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for snack in setting.affords:
            combos.append((place, snack))
    return combos


def explain_rejection(place: str, snack: str) -> str:
    return f"(No story: {snack} does not fit naturally at {place} in this little kitchen-comedy world.)"


ASP_RULES = r"""
valid(Place, Snack) :- affords(Place, Snack).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for snack in sorted(setting.affords):
            lines.append(asp.fact("affords", place, snack))
    for sid, sn in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        lines.append(asp.fact("warmth", sid, sn.warmth))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child kvetches, a parent cautions, and a silly compromise follows."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.snack is None or c[1] == args.snack)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, snack = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, snack=snack, name=name, gender=gender, parent=parent, trait=trait)


def kvetch(world: World, child: Entity, snack: Snack, repeat: int) -> None:
    child.memes["kvetch"] += 1
    child.meters["grumble"] += 1
    if repeat == 1:
        world.say(f'{child.id} looked at the {snack.label} and kvetch, "But I want it now!"')
    elif repeat == 2:
        world.say(f'"I said I want it now," {child.id} kvetch-kvetch-kvetched, louder than before.')
    else:
        world.say(f'{child.id} kvetched again, and the tiny complaint began to sound like a trumpet in slippers.')


def warn(world: World, parent: Entity, child: Entity, snack: Snack, repeat: int) -> None:
    child.memes["warning"] += 1
    world.facts["repeated"] = repeat
    world.say(
        f'"Careful," {parent.pronoun("subject")} said. "That {snack.label} is {snack.warmth}, '
        f'and you could get a {snack.risk}."'
    )


def prediction(world: World, child: Entity, snack: Snack) -> bool:
    sim = world.copy()
    sim.get(child.id).meters["grumble"] += 1
    sim.get(snack.id).meters["heat"] += 1
    return True


def compromise(world: World, parent: Entity, child: Entity, snack: Snack) -> None:
    child.memes["joy"] += 1
    child.memes["kvetch"] = 0
    world.say(
        f'{parent.pronoun("subject").capitalize()} offered a silly deal: '
        f'"Let\'s count to ten, blow on the {snack.label}, and make the wait into a game."'
    )
    world.say(
        f'{child.id} puffed air like a sleepy dragon, counted with both fingers, '
        f'and the grumbly face turned into a grin.'
    )


def finish(world: World, child: Entity, parent: Entity, snack: Snack) -> None:
    world.say(
        f'At last, the {snack.label} was safe to eat. {child.id} took a careful bite, '
        f'smiled at the blueberry juice, and did not kvetch again.'
    )
    world.say(
        f'{parent.pronoun("subject").capitalize()} laughed, because the big drama had turned '
        f'into a very small and very funny lesson.'
    )


def tell(setting: Setting, snack_cfg: Snack, name: str, gender: str,
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(
        id=name, kind="character", type=gender,
        meters={"grumble": 0.0},
        memes={"kvetch": 0.0, "joy": 0.0, "warning": 0.0},
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    snack = world.add(Entity(id=snack_cfg.id, type=snack_cfg.id, label=snack_cfg.label, phrase=snack_cfg.phrase))

    trait = (hero_traits or ["silly"])[0]
    world.say(f"{child.id} was a {trait} {gender} who loved snacks and hated waiting.")
    world.say(f"One afternoon, {child.id} found {snack_cfg.phrase} cooling on the counter.")
    world.para()

    world.say(f"{child.id} wanted to grab {snack_cfg.label} right away, but {parent.pronoun('subject')} held up a hand.")
    warn(world, parent, child, snack_cfg, 1)
    kvetch(world, child, snack_cfg, 1)
    world.say(f'The kitchen went quiet except for the oven tick-tick-ticking in the background.')

    world.para()
    warn(world, parent, child, snack_cfg, 2)
    kvetch(world, child, snack_cfg, 2)
    world.say(f"The second kvetch was so round and serious that even the spoon seemed to listen.")

    world.para()
    warn(world, parent, child, snack_cfg, 3)
    kvetch(world, child, snack_cfg, 3)
    world.say(f"By the third kvetch, the complaint had become a full parade marching across the tiles.")
    compromise(world, parent, child, snack_cfg)

    world.para()
    finish(world, child, parent, snack_cfg)

    world.facts.update(
        child=child,
        parent=parent,
        snack=snack_cfg,
        setting=setting,
        trait=trait,
        resolved=True,
        repeated=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, snack = f["child"], f["snack"]
    return [
        f"Write a short comedy for a small child who keeps kvetching about waiting for {snack.label}.",
        f"Tell a cautionary story where {child.id} wants {snack.phrase} but must wait because it is too hot.",
        f"Write a funny little story that repeats the word kvetch and ends with a safe compromise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, snack = f["child"], f["parent"], f["snack"]
    return [
        QAItem(
            question=f"Why did {child.id} kvetch about the {snack.label}?",
            answer=f"{child.id} kvetched because {snack.phrase} looked delicious and {child.pronoun('subject')} wanted it right away, but {parent.pronoun('subject')} said it was still too hot.",
        ),
        QAItem(
            question=f"What warning did {parent.pronoun('subject')} give about the {snack.label}?",
            answer=f"{parent.pronoun('subject').capitalize()} warned that the {snack.label} was {snack.warmth} and that grabbing it too soon could cause a {snack.risk}.",
        ),
        QAItem(
            question=f"How did the story end after all the kvetching?",
            answer=f"After the repeated kvetching, {child.id} waited, blew on the {snack.label}, and finally ate it safely while everyone laughed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does kvetch mean?",
            answer="Kvetch means to complain a lot, usually in a grumbly or fussy way.",
        ),
        QAItem(
            question="Why should hot food be waited on before eating?",
            answer="Hot food should cool first so it does not burn your tongue or mouth.",
        ),
        QAItem(
            question="Why can waiting turn into a game?",
            answer="Waiting can turn into a game when someone counts, sings, or does a silly challenge to pass the time more happily.",
        ),
    ]


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
    lines.append("== (3) World questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", snack="muffins", name="Mia", gender="girl", parent="mother", trait="stubborn"),
    StoryParams(place="kitchen", snack="soup", name="Ben", gender="boy", parent="father", trait="chatty"),
    StoryParams(place="table", snack="muffins", name="Zoe", gender="girl", parent="mother", trait="bouncy"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], SNACKS[params.snack], params.name, params.gender, [params.trait], params.parent)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, snack) combos:\n")
        for place, snack in combos:
            print(f"  {place:10} {snack}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.snack} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
