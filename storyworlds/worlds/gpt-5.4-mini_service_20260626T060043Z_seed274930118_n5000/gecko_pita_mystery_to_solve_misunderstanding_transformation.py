#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about a gecko, a pita, a misunderstanding,
a small mystery, and a gentle transformation.

Seed tale:
---
A little gecko lived near a sunny kitchen step. One morning, a warm pita that
had been on the sill was gone. The gecko thought the humming baker had taken it.
The baker thought the gecko had hidden it. They looked and looked, and at last
found the pita tucked beneath a bowl where a breeze had pushed it. Everyone
laughed. The baker warmed the pita again, and the gecko shared a crumbly bite.
---

This world keeps the scope small: one place, one missing pita, one false guess,
one discovery, and one ending image showing what changed.
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

SETTING_NAME = "sunny kitchen step"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_by: Optional[str] = None
    found_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "gecko":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type == "baker":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str = SETTING_NAME
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


@dataclass
class StoryParams:
    seed: Optional[int] = None
    place: str = SETTING_NAME
    name: str = "Gigi"
    baker_name: str = "Mara"


GECKO_NAMES = ["Gigi", "Nico", "Timo", "Lela", "Mimi", "Rafi"]
BAKER_NAMES = ["Mara", "Sana", "Pia", "Tara", "Nina"]


def reasonableness_gate(params: StoryParams) -> None:
    if not params.place:
        raise StoryError("A place is needed for the gecko and the pita to meet.")
    if "kitchen" not in params.place and "step" not in params.place and "windowsill" not in params.place:
        raise StoryError("This story needs a kitchen-like ledge where the pita can go missing.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A nursery-rhyme storyworld about a gecko, a pita, and a mystery."
    )
    ap.add_argument("--place", default=SETTING_NAME)
    ap.add_argument("--name")
    ap.add_argument("--baker-name")
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


ASP_RULES = r"""
#show missing/1.
#show misunderstood/1.
#show resolved/1.
#show transformed/1.

missing(pita) :- goes_missing(pita).
misunderstood(gecko) :- false_guess(gecko).
resolved(pita) :- found(pita).
transformed(pita) :- warmed(pita).

% A missing pita leads to a misunderstanding until it is found.
false_guess(gecko) :- missing(pita).
goes_missing(pita) :- drifting(pita).
found(pita) :- under_bowl(pita).
warmed(pita) :- warmed_again(pita).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("drifting", "pita"),
            asp.fact("under_bowl", "pita"),
            asp.fact("warmed_again", "pita"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show missing/1.\n#show misunderstood/1.\n#show resolved/1.\n#show transformed/1."))
    atoms = set((sym.name, tuple(a.name if a.type != a.type.Number and a.type != a.type.String else (a.number if a.type == a.type.Number else a.string) for a in sym.arguments)) for sym in model)
    expected = {
        ("missing", ("pita",)),
        ("misunderstood", ("gecko",)),
        ("resolved", ("pita",)),
        ("transformed", ("pita",)),
    }
    if atoms == expected:
        print("OK: ASP twin matches the Python world.")
        return 0
    print("MISMATCH:")
    print("  asp:", sorted(atoms))
    print("  expected:", sorted(expected))
    return 1


def _drift_pita(world: World, gecko: Entity, pita: Entity, baker: Entity) -> None:
    gecko.memes["want"] = gecko.memes.get("want", 0) + 1
    pita.meters["missing"] = 1
    pita.hidden_by = "bowl"
    world.facts["missing"] = True
    world.say(
        f"On the {world.place}, where the warm light lay, "
        f"{gecko.id} blinked and looked at the sill."
    )
    world.say(
        f"The pita was gone from its little place, and {gecko.id} felt a prickly thrill."
    )


def _misunderstanding(world: World, gecko: Entity, pita: Entity, baker: Entity) -> None:
    gecko.memes["confused"] = 1
    baker.memes["confused"] = 1
    world.facts["misunderstanding"] = True
    world.say(
        f"{gecko.id} said, \"The baker took it! The baker took my pita!\""
    )
    world.say(
        f"But {baker.id} shook {baker.pronoun('possessive')} head and said, "
        f"\"Dear little gecko, I did not.\""
    )
    world.say(
        f"So both were puzzled in the sunny hush, with one small mystery to solve."
    )


def _solve(world: World, gecko: Entity, pita: Entity, baker: Entity) -> None:
    pita.found_by = gecko.id
    pita.hidden_by = None
    pita.meters["missing"] = 0
    world.facts["resolved"] = True
    world.say(
        f"{gecko.id} peeped and peered, then lifted the bowl with care."
    )
    world.say(
        f"Under it lay the pita, tucked by a breeze in a crumbly lair."
    )
    world.say(
        f"\"Oh!\" said {gecko.id}. \"The wind played tricks!\""
    )
    world.say(
        f"{baker.id} laughed, and the worry unknit itself quick."
    )


def _transform(world: World, gecko: Entity, pita: Entity, baker: Entity) -> None:
    pita.meters["warm"] = 1
    pita.meters["shared"] = 1
    world.facts["transformed"] = True
    world.say(
        f"{baker.id} warmed the pita once more, till it smelled like a soft, toasty tune."
    )
    world.say(
        f"{gecko.id} took one tiny bite, and the day turned bright as June."
    )
    world.say(
        f"Now the mystery was mended, and the pita was no longer lost;"
        f" it was shared, and warm, and happy, as though the wind had paid its cost."
    )


def tell(params: StoryParams) -> World:
    world = World(place=params.place)
    gecko = world.add(Entity(id=params.name, kind="character", type="gecko", label="gecko"))
    baker = world.add(Entity(id=params.baker_name, kind="character", type="baker", label="baker"))
    pita = world.add(Entity(
        id="pita",
        kind="thing",
        type="pita",
        label="pita",
        phrase="a warm pita",
        owner=baker.id,
    ))
    world.facts.update(gecko=gecko, baker=baker, pita=pita, place=params.place)

    world.say(
        f"{gecko.id} was a little gecko who lived by the {world.place}, "
        f"where the sun made every crumb look like gold."
    )
    world.say(
        f"{gecko.id} loved the smell of bread and listened to the baker's song as it rolled."
    )

    world.para()
    _drift_pita(world, gecko, pita, baker)

    world.para()
    _misunderstanding(world, gecko, pita, baker)

    world.para()
    _solve(world, gecko, pita, baker)

    world.para()
    _transform(world, gecko, pita, baker)

    return world


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short nursery-rhyme story about a gecko and a missing pita.",
        "Tell a gentle tale where a gecko has a misunderstanding about who took the pita.",
        "Write a simple story with one mystery to solve and a warm ending transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    gecko = world.facts["gecko"]
    baker = world.facts["baker"]
    return [
        QAItem(
            question=f"Who was the little gecko in the story?",
            answer=f"The little gecko was {gecko.id}, who lived by the sunny kitchen step.",
        ),
        QAItem(
            question=f"Why did {gecko.id} think the pita was missing?",
            answer=f"{gecko.id} thought the pita was missing because it had vanished from the sill, so {gecko.id} guessed someone had taken it.",
        ),
        QAItem(
            question=f"Who did {gecko.id} wrongly blame at first?",
            answer=f"At first, {gecko.id} wrongly blamed {baker.id} the baker for taking the pita.",
        ),
        QAItem(
            question="What solved the mystery?",
            answer="The mystery was solved when the gecko lifted the bowl and found the pita tucked underneath it, pushed there by a breeze.",
        ),
        QAItem(
            question="What changed at the end?",
            answer="At the end, the pita was warmed again and shared, so the missing thing became a happy snack instead of a worry.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gecko?",
            answer="A gecko is a small lizard that can climb and cling with quick little feet.",
        ),
        QAItem(
            question="What is pita?",
            answer="Pita is a soft flat bread that can be warm and tasty, and people often tear it into pieces to share.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone guesses the wrong thing about what happened, even though no one meant to trick them.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzling thing that needs careful looking and thinking before it can be solved.",
        ),
        QAItem(
            question="What does transformation mean in a story?",
            answer="Transformation means something changes in an important way, like a worried moment turning into a cheerful one.",
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden_by:
            bits.append(f"hidden_by={e.hidden_by}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(k for k, v in world.facts.items() if isinstance(v, bool) and v)}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or SETTING_NAME
    if not place:
        raise StoryError("A place is required.")
    name = args.name or rng.choice(GECKO_NAMES)
    baker_name = args.baker_name or rng.choice(BAKER_NAMES)
    params = StoryParams(seed=None, place=place, name=name, baker_name=baker_name)
    reasonableness_gate(params)
    return params


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show missing/1.\n#show misunderstood/1.\n#show resolved/1.\n#show transformed/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show missing/1.\n#show misunderstood/1.\n#show resolved/1.\n#show transformed/1."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    for i in range(args.n):
        seed = base_seed + i
        rng = random.Random(seed)
        try:
            params = resolve_params(args, rng)
        except StoryError as err:
            print(err)
            return
        params.seed = seed
        samples.append(generate(params))

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
