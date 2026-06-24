#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/spangle_puppet_theater_reconciliation_repetition_flashback_fairy.py

A small fairy-tale storyworld set in a puppet theater.

Premise:
- A proud puppet actor loses its shine and argues with a helpful stage keeper.
- A repeated rehearsal goes wrong until a flashback reminds them why the puppet loved the stage.
- Reconciliation happens when they mend the costume together and the show can begin.

The world keeps a tiny physical/emotional model:
- meters: physical state such as shine, dust, torn, tidy
- memes: emotional state such as pride, worry, hurt, trust, joy

The story must read like a complete tale with a beginning, middle turn, and ending image.
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

TITLE = "Spangle Puppet Theater"

NAMES = ["Mira", "Toby", "Luna", "Pip", "Nell", "Jasper"]
PUPPET_NAMES = ["Sir Button", "Lady Quill", "Captain Thimble", "Rose String", "Moss Foot"]
KEEPER_NAMES = ["Old Elin", "Master Birch", "Aunt Sella", "Kind Rowan"]
PROP_NAMES = ["a tiny crown", "a velvet cape", "a painted star", "a silver bell", "a spangle sash"]


@dataclass
class StoryParams:
    name: str
    puppet: str
    keeper: str
    prop: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale puppet theater storyworld.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--puppet", choices=PUPPET_NAMES)
    ap.add_argument("--keeper", choices=KEEPER_NAMES)
    ap.add_argument("--prop", choices=PROP_NAMES)
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
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        puppet=args.puppet or rng.choice(PUPPET_NAMES),
        keeper=args.keeper or rng.choice(KEEPER_NAMES),
        prop=args.prop or rng.choice(PROP_NAMES),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if "spangle" not in params.prop and params.prop != "a painted star":
        # The seed explicitly asks for spangle; keep it in the story world.
        raise StoryError("This puppet-theater tale needs a spangled or starry prop to suit the seed word 'spangle'.")


ASP_RULES = r"""
puppet(P) :- puppet_name(P).
keeper(K) :- keeper_name(K).
prop(X) :- prop_name(X).
spangled(X) :- prop_name(X), contains_spangle(X).
can_reconcile(P,K) :- puppet(P), keeper(K), prop(X), helps_mend(X), shared_show(P,K).
shared_show(P,K) :- puppet(P), keeper(K).
featured(P,K,X) :- can_reconcile(P,K), prop(X).
#show featured/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy
    lines = []
    for n in PUPPET_NAMES:
        lines.append(asp.fact("puppet_name", n))
    for n in KEEPER_NAMES:
        lines.append(asp.fact("keeper_name", n))
    for p in PROP_NAMES:
        lines.append(asp.fact("prop_name", p))
        if "spangle" in p:
            lines.append(asp.fact("contains_spangle", p))
        if p in {"a tiny crown", "a velvet cape", "a painted star", "a silver bell", "a spangle sash"}:
            lines.append(asp.fact("helps_mend", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show featured/3."))
    atoms = set(asp.atoms(model, "featured"))
    expected = {(p, k, x) for p in PUPPET_NAMES for k in KEEPER_NAMES for x in PROP_NAMES}
    if atoms == expected:
        print(f"OK: ASP shows {len(atoms)} featured combinations.")
        return 0
    print("MISMATCH between ASP and expected combinations.")
    return 1


def _flashback(world: World, puppet: Entity, keeper: Entity) -> None:
    world.say(
        f"Long ago, before the curtain was mended, {puppet.label} had danced there "
        f"with a bright heart, and {keeper.label} had promised to keep the little stage safe."
    )
    puppet.memes["nostalgia"] = puppet.memes.get("nostalgia", 0) + 1
    puppet.memes["trust"] = puppet.memes.get("trust", 0) + 1


def generate_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = World()
    puppet = world.add(Entity(id="puppet", kind="puppet", label=params.puppet,
                              meters={"shine": 1.0, "dust": 0.0, "torn": 0.0},
                              memes={"pride": 1.0, "worry": 0.0, "hurt": 0.0, "joy": 0.0}))
    keeper = world.add(Entity(id="keeper", kind="keeper", label=params.keeper,
                              meters={"tidy": 1.0},
                              memes={"patience": 1.0, "worry": 0.0, "joy": 0.0}))
    child = world.add(Entity(id="child", kind="child", label=params.name))
    world.facts.update(params=params, puppet=puppet, keeper=keeper, child=child)

    world.say(
        f"Once in the puppet theater, {child.label} came under the painted roof where {puppet.label} stood beside the curtain. "
        f"On the table waited {params.prop}, and it glittered like a small moon."
    )
    world.say(
        f"{puppet.label} loved the stage and wanted the show to begin at once. "
        f"{keeper.label} said the curtain must be brushed first, because the boards were dusty after the wind."
    )

    # repetition beat
    puppet.memes["impatience"] = 1.0
    for _ in range(2):
        world.say(
            f"{puppet.label} tried the same bow again and again, but each time the spangle on {params.prop} slipped a little more."
        )
        puppet.meters["shine"] -= 0.2
        puppet.meters["dust"] += 0.3
    puppet.memes["worry"] += 1.0
    keeper.memes["worry"] += 1.0

    world.say(
        f"Then the tiny star on {params.prop} caught on a splinter and came loose, and {puppet.label} felt the hurt of it."
    )
    puppet.meters["torn"] += 1.0
    puppet.memes["hurt"] += 1.0
    keeper.memes["hurt"] = keeper.memes.get("hurt", 0.0) + 1.0

    _flashback(world, puppet, keeper)

    world.say(
        f"Remembering that old promise, {keeper.label} brought a needle, and {puppet.label} held still by the lamp."
    )
    world.say(
        f"They worked together, loop by loop, until the spangle shone on {params.prop} again and the curtain looked ready for a royal tale."
    )
    puppet.meters["shine"] = 1.0
    puppet.meters["torn"] = 0.0
    puppet.meters["dust"] = 0.0
    puppet.memes["joy"] += 2.0
    puppet.memes["hurt"] = 0.0
    keeper.memes["joy"] += 1.0
    keeper.memes["worry"] = 0.0
    world.say(
        f"At last {puppet.label} and {keeper.label} smiled together, and {child.label} heard the first tap of the show begin at the glowing puppet theater."
    )

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a fairy tale set in a puppet theater with the word 'spangle' and a gentle reconciliation.",
        f"Tell a child-friendly story where {p.puppet} and {p.keeper} repair {p.prop} after an argument.",
        f"Create a short magical tale that uses repetition, then a flashback, then a happy ending on a puppet stage.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    puppet = world.facts["puppet"]
    keeper = world.facts["keeper"]
    return [
        QAItem(
            question=f"Who was the puppet in the story?",
            answer=f"The puppet was {puppet.label}, who stood in the puppet theater under the painted roof.",
        ),
        QAItem(
            question=f"What went wrong with {p.prop}?",
            answer=f"The spangle or little star on {p.prop} slipped loose and left {puppet.label} feeling hurt and worried.",
        ),
        QAItem(
            question=f"How did {puppet.label} and {keeper.label} make peace?",
            answer=f"They repaired {p.prop} together with a needle and thread, so they could begin the show again side by side.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a puppet theater?",
            answer="A puppet theater is a small stage where puppets act out stories for people to watch.",
        ),
        QAItem(
            question="What does a spangle look like?",
            answer="A spangle is a tiny shiny disc or star that sparkles on clothes or costumes.",
        ),
        QAItem(
            question="Why do people mend torn cloth?",
            answer="People mend torn cloth so it can be used again and so the tear does not grow bigger.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(f"{entity.id}: meters={entity.meters} memes={entity.memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
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


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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


def asp_list() -> None:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show featured/3."))
    atoms = sorted(set(asp.atoms(model, "featured")))
    for atom in atoms:
        print(atom)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show featured/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        asp_list()
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)
    samples: list[StorySample] = []

    if args.all:
        combos = [
            StoryParams(name=n, puppet=p, keeper=k, prop=x, seed=base_seed)
            for n in NAMES[:3]
            for p in PUPPET_NAMES[:2]
            for k in KEEPER_NAMES[:2]
            for x in PROP_NAMES[:2]
        ]
        for params in combos[: max(args.n, 1)]:
            samples.append(generate(params))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
