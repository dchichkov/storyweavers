#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/gravel_mica_nana_reconciliation_bad_ending_misunderstanding.py
==============================================================================================

A small slice-of-life story world about a child, Nana, a patch of gravel, and a
piece of mica that looks like a tiny piece of moonlight.

Seed tale used to build the world:
---
A child finds a glittery chip of mica in the gravel by Nana's steps and thinks it
must be something special. Nana thinks the child has taken a loose roof shard or
something unsafe. They talk past each other. The child feels hurt, Nana feels
worried, and the afternoon turns awkward. In the end they sit together, look at
the mica, and say sorry, but the little moment still ends with a quiet, slightly
sad feeling instead of a perfect fix.

The simulation tracks:
- physical meters: gravel in pockets, mica on the palm, tea cooling on the table
- emotional memes: curiosity, worry, hurt, apology, closeness

The story generator prefers a gentle, authored slice-of-life tone with a real
misunderstanding, a reconciliation beat, and a slightly bittersweet ending image.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"child", "girl", "daughter"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "son"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"nana", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    detail: str


@dataclass
class ObjectSpec:
    id: str
    label: str
    phrase: str
    type: str
    region: str


@dataclass
class StoryParams:
    setting: str
    name: str
    child_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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


SETTINGS = {
    "steps": Place("Nana's front steps", "The steps were lined with pale gravel and a little pot of thyme."),
    "yard": Place("Nana's yard", "The yard had a gravel strip by the gate and warm sun on the chairs."),
    "path": Place("the side path", "The path was made of small gravel stones that clicked under shoes."),
}

CHILD_NAMES = ["Mia", "Theo", "June", "Luca", "Ivy", "Owen", "Ruby", "Finn"]
CHILD_TYPES = ["girl", "boy"]

MICA = ObjectSpec(
    id="mica",
    label="mica",
    phrase="a thin shiny flake of mica",
    type="mica",
    region="palm",
)

GRAVEL = ObjectSpec(
    id="gravel",
    label="gravel",
    phrase="a handful of gravel",
    type="gravel",
    region="pocket",
)

ASP_RULES = r"""
child_curious(C) :- curious(C).
noticed_shiny(C) :- sees(C, mica).
misunderstanding(C, N) :- worried(N), took(N, mica), noticed_shiny(C).
reconcile(C, N) :- apology(C, N), apology(N, C).
bad_ending(C, N) :- misunderstanding(C, N), not reconcile(C, N).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    lines.append(asp.fact("curious", "child"))
    lines.append(asp.fact("sees", "child", "mica"))
    lines.append(asp.fact("worried", "nana"))
    lines.append(asp.fact("took", "nana", "mica"))
    lines.append(asp.fact("apology", "child", "nana"))
    lines.append(asp.fact("apology", "nana", "child"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def reasonableness_gate(setting: str) -> None:
    if setting not in SETTINGS:
        raise StoryError(f"Unknown setting '{setting}'.")
    if "gravel" not in SETTINGS[setting].detail.lower():
        raise StoryError("This story needs a gravel place so the mica can be found there.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world about gravel, mica, and Nana.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--child-type", choices=CHILD_TYPES, dest="child_type")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    reasonableness_gate(setting)
    name = args.name or rng.choice(CHILD_NAMES)
    child_type = args.child_type or rng.choice(CHILD_TYPES)
    return StoryParams(setting=setting, name=name, child_type=child_type)


def _child_pronoun(child: Entity, case: str = "subject") -> str:
    return child.pronoun(case)


def build_world(params: StoryParams) -> World:
    place = SETTINGS[params.setting]
    w = World(place)
    child = w.add(Entity(id="child", kind="character", type=params.child_type, label=params.name))
    nana = w.add(Entity(id="nana", kind="character", type="nana", label="Nana"))
    mica = w.add(Entity(id="mica", type="mica", label="mica", phrase=MICA.phrase, owner="child", caretaker="nana"))
    gravel = w.add(Entity(id="gravel", type="gravel", label="gravel", phrase=GRAVEL.phrase, plural=True))
    tea = w.add(Entity(id="tea", type="tea", label="tea", phrase="a small cup of tea", caretaker="nana"))
    w.facts.update(child=child, nana=nana, mica=mica, gravel=gravel, tea=tea, params=params)
    return w


def tell(params: StoryParams) -> World:
    w = build_world(params)
    child: Entity = w.get("child")
    nana: Entity = w.get("nana")
    mica: Entity = w.get("mica")
    gravel: Entity = w.get("gravel")
    tea: Entity = w.get("tea")

    child.memes["curiosity"] = 1
    w.say(
        f"{child.label} was visiting {w.place.name}. {w.place.detail} "
        f"{child.label} liked the tiny clicks the gravel made under each step."
    )
    w.say(
        f"Near the steps, {child.label} found {mica.phrase} tucked among the gravel. "
        f"It flashed like a little piece of bright sky."
    )
    mica.meters["in_hand"] = 1
    gravel.meters["in_shoe"] = 1
    child.memes["delight"] = 1
    w.say(
        f"{child.label} held the mica up to the light and smiled. {child.pronoun().capitalize()} "
        f"wanted to show {mica.label} to Nana right away."
    )

    w.para()
    nana.memes["worry"] = 1
    child.memes["hurt"] = 1
    w.say(
        f"Nana looked over from the chair and frowned. The shiny flake looked too much like a loose chip "
        f"from the old step, so {nana.label} thought {child.label} had taken something that should stay put."
    )
    w.say(
        f'"Put that back," Nana said, sounding sharper than {child.label} expected. '
        f"{child.label} went very still, because the mica had been a treasure in {child.pronoun('possessive')} palm."
    )

    w.para()
    child.memes["misunderstood"] = 1
    nana.memes["misunderstood"] = 1
    w.say(
        f"{child.label} said it was only a pretty stone, but Nana heard disobedience instead of excitement. "
        f"The two of them talked over each other for a moment, while the tea on the table cooled."
    )
    w.say(
        f"{child.label} set the mica on the railing. Nana checked the steps with a careful hand and saw that the gravel "
        f"was loose but harmless. She realized {child.label} had not meant any trouble at all."
    )

    w.para()
    child.memes["apology"] = 1
    nana.memes["apology"] = 1
    child.memes["closeness"] = 1
    nana.memes["closeness"] = 1
    child.memes["hurt"] *= 0.5
    nana.memes["worry"] *= 0.5
    w.say(
        f"{child.label} and Nana sat together on the bottom step. {child.label} said sorry for snatching the mica so fast, "
        f"and Nana said sorry for scolding before asking a question."
    )
    w.say(
        f"They looked at the mica again and decided it could stay in a jar on the shelf. "
        f"{child.label} slipped a little gravel from {child.pronoun('possessive')} pocket into Nana's hand, and Nana laughed softly."
    )
    w.say(
        f"By the end, the afternoon was quiet again, but not perfectly happy: the tea was cold, the gravel still needed sweeping, "
        f"and both of them remembered the misunderstanding. Still, {child.label} left with a tiny shine in {child.pronoun('possessive')} hand "
        f"and Nana walking beside {child.label} up the path."
    )

    w.facts.update(
        child=child,
        nana=nana,
        mica=mica,
        gravel=gravel,
        tea=tea,
        resolved=True,
        misunderstanding=True,
        bad_ending=True,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    return [
        f"Write a gentle slice-of-life story about {child.label}, Nana, gravel, and a tiny piece of mica.",
        "Tell a story where a child and Nana misunderstand each other and then reconcile over something small and shiny.",
        "Write a short realistic story that begins with a child finding mica in gravel and ends with a bittersweet calm.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    nana: Entity = world.facts["nana"]
    mica: Entity = world.facts["mica"]
    return [
        QAItem(
            question=f"What did {child.label} find in the gravel by Nana's steps?",
            answer=f"{child.label} found {mica.phrase} in the gravel by Nana's steps.",
        ),
        QAItem(
            question=f"Why did Nana get worried when {child.label} showed her the shiny piece?",
            answer=(
                "Nana thought the shiny piece might be something unsafe or a loose chip from the steps, "
                f"so she spoke too sharply before she understood that {child.label} only wanted to share a treasure."
            ),
        ),
        QAItem(
            question=f"How did {child.label} and Nana fix the misunderstanding?",
            answer=(
                f"They sat together, said sorry, and looked at the mica again. "
                f"After that, Nana understood that {child.label} had been excited, not naughty."
            ),
        ),
        QAItem(
            question=f"What kind of ending does the story have?",
            answer=(
                "It ends in a quiet, bittersweet way: they reconcile, but the afternoon still feels a little heavy, "
                "with cold tea and a small leftover sadness."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is mica?",
            answer="Mica is a shiny mineral that breaks into thin flakes and can sparkle in the light.",
        ),
        QAItem(
            question="What is gravel?",
            answer="Gravel is a collection of small stones that crunch underfoot and are often used on paths or by steps.",
        ),
        QAItem(
            question="Why do people sweep gravel off a step or path?",
            answer="People sweep gravel away so the walking surface stays neat and safe, and so the stones do not end up everywhere.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("\n== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(out)


def asp_verify() -> int:
    import storyworlds.asp as asp
    program = asp_program("#show reconcile/2.\n#show bad_ending/2.\n#show misunderstanding/2.")
    model = asp.one_model(program)
    atoms = set((a.name, tuple(arg.name if arg.type != 1 else arg.string for arg in a.arguments)) for a in model)
    want = {("reconcile", ("child", "nana")), ("bad_ending", ("child", "nana"))}
    if atoms == want:
        print("OK: ASP twin matches the Python story logic.")
        return 0
    print("MISMATCH:", atoms, want)
    return 1


def asp_valid() -> str:
    import storyworlds.asp as asp
    return asp_program("#show reconcile/2.\n#show bad_ending/2.\n#show misunderstanding/2.")


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
        print(asp_valid())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show reconcile/2.\n#show bad_ending/2.\n#show misunderstanding/2."))
        print("ASP atoms:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTINGS:
            params = StoryParams(setting=setting, name=CHILD_NAMES[0], child_type="child", seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
