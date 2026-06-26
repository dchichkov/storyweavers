#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/guess_oriental_component_flashback_myth.py
======================================================================================================================

A small mythic storyworld about a child who must guess a missing component
of an oriental relic by remembering a flashback.

Seed premise:
- A village keeps a treasured oriental lantern-chime used in a moon rite.
- The lantern has a missing component.
- A child guesses which component belongs in the relic.
- A flashback reveals where the part went.
- The story ends when the relic is restored and the rite can continue.

The world is intentionally small and constraint-checked:
- one relic with a missing component
- one child
- one elder helper
- one site of ritual use
- one plausible guess that fits the relic

The narrative shape is mythic:
- opening blessing and setting
- a warning about the broken relic
- a flashback to the loss
- a guessed fix
- a restored ending image

This script follows the Storyweavers world contract:
- stdlib only for the prose engine
- lazy import of storyworlds/asp.py in ASP helpers
- eager import of storyworlds/results.py for shared containers
- support for default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    glow: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    missing_component: str
    needed_component: str
    component_kind: str
    component_place: str
    ritual_kind: str
    flashback_hint: str


@dataclass
class StoryParams:
    place: str
    relic: str
    name: str
    gender: str
    elder: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.flashback_used: bool = False
        self.repaired: bool = False

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


RELIGIOUS_MOTIFS = {
    "moon": "the moon hung like a silver bowl above the roofs",
    "river": "the river moved like a quiet blue serpent below the reeds",
    "gate": "the gate stood carved with old flowers and tiny stars",
    "hill": "the hill watched over the village like a sleeping giant",
}


SETTINGS = {
    "moon_gate": Setting(place="the moon gate", glow="silver", affords={"repair", "remember"}),
    "river_temple": Setting(place="the river temple", glow="blue", affords={"repair", "remember"}),
    "hill_shrine": Setting(place="the hill shrine", glow="gold", affords={"repair", "remember"}),
}

RELICS = {
    "wind_chime": Relic(
        id="wind_chime",
        label="wind chime lantern",
        phrase="an old oriental wind chime lantern",
        missing_component="a jade bead",
        needed_component="jade bead",
        component_kind="bead",
        component_place="on a red string",
        ritual_kind="moon rite",
        flashback_hint="the child had untied the string during play",
    ),
    "stone_drum": Relic(
        id="stone_drum",
        label="stone drum",
        phrase="an oriental stone drum",
        missing_component="a cedar striker",
        needed_component="cedar striker",
        component_kind="striker",
        component_place="in the drum basket",
        ritual_kind="river rite",
        flashback_hint="the striker fell from the basket and rolled under a bench",
    ),
    "paper_kite": Relic(
        id="paper_kite",
        label="paper kite shrine-banner",
        phrase="an oriental paper kite shrine-banner",
        missing_component="a silk tail",
        needed_component="silk tail",
        component_kind="tail",
        component_place="at the bottom edge",
        ritual_kind="wind rite",
        flashback_hint="the tail snapped loose while the banner was being carried",
    ),
}

GENDERS = {"girl", "boy"}
BOY_NAMES = ["Jun", "Milo", "Kai", "Taro", "Noah", "Eli"]
GIRL_NAMES = ["Mei", "Lina", "Asha", "Nora", "Ivy", "Aya"]
ELDERS = ["grandmother", "grandfather", "aunt", "uncle"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, relic_id) for place in SETTINGS for relic_id in RELICS]


def explain_rejection(place: str, relic_id: str) -> str:
    return f"(No story: the relic {relic_id} cannot be used at {place} in this myth.)"


def explain_gender(relic_id: str, gender: str) -> str:
    return f"(No story: the {relic_id} tale here is not constrained by {gender}, but another option was expected.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A mythic flashback storyworld about guessing a missing component."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--gender", choices=sorted(GENDERS))
    ap.add_argument("--elder", choices=ELDERS)
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
    if args.place and args.relic:
        if (args.place, args.relic) not in valid_combos():
            raise StoryError(explain_rejection(args.place, args.relic))
    place = args.place or rng.choice(list(SETTINGS))
    relic = args.relic or rng.choice(list(RELICS))
    gender = args.gender or rng.choice(["girl", "boy"])
    elder = args.elder or rng.choice(ELDERS)
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, relic=relic, name=name, gender=gender, elder=elder)


def _name_for_gender(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def tell(setting: Setting, relic: Relic, child_name: str, child_gender: str, elder_role: str) -> World:
    world = World(setting)

    child = world.add(Entity(id=child_name, kind="character", type=child_gender, label=child_name))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_role, label=f"the {elder_role}"))
    relic_ent = world.add(Entity(
        id=relic.id,
        kind="thing",
        type=relic.component_kind,
        label=relic.label,
        phrase=relic.phrase,
        caretaker=elder.id,
        owner="village",
        location=setting.place,
    ))
    component = world.add(Entity(
        id="component",
        kind="thing",
        type=relic.component_kind,
        label=relic.needed_component,
        phrase=relic.missing_component,
        owner=child.id,
        location="memory",
    ))

    child.memes["wonder"] = 1.0
    relic_ent.meters["broken"] = 1.0
    relic_ent.meters["missing_component"] = 1.0
    relic_ent.meters["quiet"] = 1.0

    world.say(f"In {setting.place}, {RELIGIOUS_MOTIFS.get('moon' if setting.place == 'the moon gate' else 'river' if setting.place == 'the river temple' else 'hill')}.")
    world.say(
        f"There stood {relic.phrase}, and the village said it was good for the "
        f"{relic.ritual_kind} only when every piece was in place."
    )
    world.para()
    world.say(
        f"But one part was gone. {relic.label.capitalize()} missed {relic.missing_component}, "
        f"so its song stayed sleepy and thin."
    )
    world.say(
        f"{child_name} looked at the relic and tried to guess the missing component."
    )
    flashback(world, child, relic, elder, component)
    guess_and_restore(world, child, elder, relic_ent, component)
    return world


def flashback(world: World, child: Entity, relic: Relic, elder: Entity, component: Entity) -> None:
    world.flashback_used = True
    world.para()
    world.say(
        f"Then {child.id} remembered a flashback: yesterday, {child.id} had been "
        f"playing near the shrine when {relic.flashback_hint}."
    )
    world.say(
        f"{elder.label.capitalize()} had reached out and said, "
        f"\"A small thing can travel far when the wind is curious.\""
    )
    world.say(
        f"In that old moment, {child.id} noticed {relic.missing_component} glinting where it should belong."
    )


def guess_and_restore(world: World, child: Entity, elder: Entity, relic_ent: Entity, component: Entity) -> None:
    relic = RELICS[relic_ent.id]
    world.para()
    child.memes["resolve"] = 1.0
    world.say(
        f"{child.id} made a guess: the missing piece was {relic.needed_component}."
    )
    world.say(
        f"{child.id} found it where the flashback led, and {elder.label} nodded because the guess fit the relic."
    )
    world.say(
        f"Together they tied the {relic.needed_component} back onto the {relic.label}, and the small hollow sound turned bright."
    )
    world.say(
        f"At once the {relic.ritual_kind} could begin again, and the oriental relic sang as if it had remembered its own name."
    )
    world.repaired = True
    relic_ent.meters["broken"] = 0.0
    relic_ent.meters["whole"] = 1.0
    relic_ent.meters["quiet"] = 0.0
    component.location = relic_ent.id
    world.facts.update(
        child=child,
        elder=elder,
        relic=relic_ent,
        component=component,
        rel_cfg=relic,
        flashback=True,
        repaired=True,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for a young child about a missing component and a brave guess, using the word "guess".',
        f'Write a gentle flashback story where {f["child"].id} remembers how {f["rel_cfg"].needed_component} was lost and restores an oriental relic.',
        f'Create a child-friendly myth set at {world.setting.place} where a flashback helps solve a broken component puzzle.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    elder: Entity = f["elder"]
    relic_ent: Entity = f["relic"]
    rel_cfg: Relic = f["rel_cfg"]
    return [
        QAItem(
            question=f"What did {child.id} have to guess in the story?",
            answer=f"{child.id} had to guess that the missing component was {rel_cfg.needed_component}.",
        ),
        QAItem(
            question=f"Why did the relic stay quiet at first?",
            answer=f"It stayed quiet because {relic_ent.label} was missing {rel_cfg.missing_component}.",
        ),
        QAItem(
            question=f"What did the flashback help {child.id} remember?",
            answer=f"The flashback helped {child.id} remember where {rel_cfg.missing_component} had gone and how to bring it back.",
        ),
        QAItem(
            question=f"How did {child.id} and {elder.label} fix the relic?",
            answer=f"They tied the {rel_cfg.needed_component} back onto the {relic_ent.label}, and then the {rel_cfg.ritual_kind} could begin again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    rel_cfg: Relic = world.facts["rel_cfg"]
    return [
        QAItem(
            question="What is a guess?",
            answer="A guess is an answer you think might be right when you are not sure yet.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that remembers something from before the present moment.",
        ),
        QAItem(
            question="What is a component?",
            answer="A component is one part of a bigger thing, like one piece of a toy or tool.",
        ),
        QAItem(
            question="What does oriental mean in this story world?",
            answer="Here it is a story label for an old eastern-style village relic, used as part of the mythic setting.",
        ),
        QAItem(
            question=f"Why did the {rel_cfg.ritual_kind} need every part in place?",
            answer="The rite needed every part because the relic only sang properly when it was whole.",
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
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  flashback_used={world.flashback_used}")
    lines.append(f"  repaired={world.repaired}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed)
    setting = SETTINGS[params.place]
    relic = RELICS[params.relic]
    if params.gender not in GENDERS:
        raise StoryError("invalid gender")
    name = params.name or _name_for_gender(params.gender, rng)
    world = tell(setting, relic, name, params.gender, params.elder)
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
    StoryParams(place="moon_gate", relic="wind_chime", name="Mei", gender="girl", elder="grandmother"),
    StoryParams(place="river_temple", relic="stone_drum", name="Kai", gender="boy", elder="uncle"),
    StoryParams(place="hill_shrine", relic="paper_kite", name="Lina", gender="girl", elder="aunt"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for rid, rel in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("missing", rid, rel.component_kind))
        lines.append(asp.fact("needs", rid, rel.needed_component))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, R) :- place(P), relic(R).
"""


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


def resolve_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.relic and (args.place, args.relic) not in valid_combos():
        raise StoryError(explain_rejection(args.place, args.relic))
    place = args.place or rng.choice(list(SETTINGS))
    relic = args.relic or rng.choice(list(RELICS))
    gender = args.gender or rng.choice(sorted(GENDERS))
    elder = args.elder or rng.choice(ELDERS)
    name = args.name or _name_for_gender(gender, rng)
    return StoryParams(place=place, relic=relic, name=name, gender=gender, elder=elder)


def valid_combos_story() -> list[tuple[str, str]]:
    return valid_combos()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, relic) combos:\n")
        for place, relic in combos:
            print(f"  {place:14} {relic}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_story_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.relic} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
