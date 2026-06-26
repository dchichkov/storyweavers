#!/usr/bin/env python3
"""
storyworlds/worlds/miss_squeegee_reconciliation_flashback_superhero_story.py
=============================================================================

A small superhero storyworld about a young hero, a messy rescue, a squeegee,
a flashback to earlier practice, and a reconciliation after a mistake.

Premise:
- A child hero and a helper are preparing for a simple rooftop cleanup.
- A sticky slime burst makes the hero's visor and cape messy.
- The hero blames the helper for "missing" the bucket, but the helper explains
  what happened and brings out a squeegee.

Turn:
- A flashback reminds the hero that they practiced clean-up together before.

Resolution:
- The hero and helper reconcile, use the squeegee, and finish the job with a
  bright ending image.

The world is kept small on purpose: one hero, one helper, one mess, one tool,
and one reasoned compromise.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["mess", "clean", "calm"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "blame", "trust", "conflict", "reconciliation", "flashback"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    hero_name: str = "Nova"
    hero_gender: str = "girl"
    helper_name: str = "Milo"
    helper_gender: str = "boy"
    place: str = "the rooftop"
    mess: str = "slime"
    seed: Optional[int] = None


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    guards: set[str]
    covers: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out = []
        buf = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)

    def copy(self) -> "World":
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.lines = []
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(item.protective and region in item.covers for item in self.worn_items(actor))


SETTINGS = {
    "rooftop": Setting(place="the rooftop", affords={"clean"}),
    "alley": Setting(place="the alley", affords={"clean"}),
}

TOOLS = {
    "squeegee": Tool(
        id="squeegee",
        label="squeegee",
        phrase="a bright red squeegee",
        guards={"slime"},
        covers={"hands", "torso"},
        prep="pick up the squeegee and start wiping",
        tail="worked side by side with the squeegee",
    ),
    "cloth": Tool(
        id="cloth",
        label="clean cloth",
        phrase="a soft clean cloth",
        guards={"slime"},
        covers={"hands"},
        prep="grab the clean cloth and wipe carefully",
        tail="finished with the clean cloth",
    ),
}

GIRL_NAMES = ["Nova", "Luna", "Iris", "Mina", "Zara"]
BOY_NAMES = ["Milo", "Theo", "Jace", "Arlo", "Finn"]


def mess_at_risk(mess: str, item: Entity) -> bool:
    return item.worn_by is not None and item.type in {"cape", "mask"} and mess == "slime"


def select_tool(mess: str, item: Entity) -> Optional[Tool]:
    for tool in [TOOLS["squeegee"], TOOLS["cloth"]]:
        if mess in tool.guards and item.type in {"cape", "mask"}:
            return tool
    return None


ASP_RULES = r"""
at_risk(M, I) :- mess(M), worn(I), target_part(I, P), splashes(M, P).
can_fix(T, M, I) :- tool(T), at_risk(M, I), guards(T, M), covers(T, R), needs_region(I, R).
valid_story(Place, M) :- setting(Place), affords(Place, clean), mess(M), tool(squeegee).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("setting", s) for s in SETTINGS]
    for s in SETTINGS.values():
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", s.place, a))
    for t in TOOLS.values():
        lines.append(asp.fact("tool", t.id))
        for g in sorted(t.guards):
            lines.append(asp.fact("guards", t.id, g))
        for c in sorted(t.covers):
            lines.append(asp.fact("covers", t.id, c))
    lines.append(asp.fact("mess", "slime"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        if "clean" not in setting.affords:
            continue
        for tool in TOOLS.values():
            if "slime" in tool.guards:
                combos.append((place, tool.id))
    return combos


def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} hero who loved helping people.")
    world.say(f"{hero.pronoun().capitalize()} kept a {hero.label} badge on {hero.pronoun('possessive')} chest and a brave grin on {hero.pronoun('possessive')} face.")


def setup_flashback(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["flashback"] += 1
    world.say(f"One afternoon, {hero.id} remembered a flashback from training day.")
    world.say(f"Back then, {hero.id} and {helper.id} had practiced cleaning a window until it shone like a mirror.")


def mess_event(world: World, hero: Entity, helper: Entity, cape: Entity) -> None:
    hero.meters["mess"] += 1
    hero.memes["worry"] += 1
    helper.memes["worry"] += 1
    cape.meters["mess"] += 1
    world.say(f"Then a sticky slime splash burst over {hero.id}'s cape.")
    world.say(f"{hero.id} blinked and said, \"I miss the clean sky already!\"")


def blame_beats(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["blame"] += 1
    hero.memes["conflict"] += 1
    helper.memes["conflict"] += 1
    world.say(f"{hero.id} thought {helper.id} had missed the bucket on purpose.")
    world.say(f"{helper.id} shook {helper.pronoun('possessive')} head and held up the squeegee.")


def reconciliation(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["reconciliation"] += 1
    helper.memes["reconciliation"] += 1
    hero.memes["trust"] += 1
    helper.memes["trust"] += 1
    hero.memes["conflict"] = 0.0
    helper.memes["conflict"] = 0.0
    world.say(f"Then {helper.id} said, \"I didn't miss on purpose. The wind nudged the bucket.\"")
    world.say(f"{hero.id} looked at {helper.id}, took a breath, and nodded.")
    world.say(f"They made up right away, because teams work best when they listen.")


def clean_with_tool(world: World, hero: Entity, helper: Entity, cape: Entity, tool: Tool) -> None:
    cape.meters["mess"] = 0.0
    cape.meters["clean"] = 1.0
    hero.meters["mess"] = 0.0
    helper.meters["mess"] = 0.0
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(f"{helper.id} used the {tool.label} to sweep the slime away in long shiny strokes.")
    world.say(f"{hero.id} helped, and soon the cape looked bright again.")
    world.say(f"By the end, they {tool.tail}, and the rooftop sparkled like a hero's badge.")


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_gender))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender))
    cape = world.add(Entity(id="Cape", type="cape", label="cape", phrase="a bright hero cape", owner=hero.id, caretaker=helper.id, worn_by=hero.id))
    mask = world.add(Entity(id="Mask", type="mask", label="mask", phrase="a shiny mask", owner=hero.id, caretaker=helper.id, worn_by=hero.id))

    intro(world, hero)
    world.para()
    world.say(f"That day, {hero.id} and {helper.id} were on {setting.place} to clean up after a windy rescue.")
    setup_flashback(world, hero, helper)
    mess_event(world, hero, helper, cape)
    blame_beats(world, hero, helper)
    world.para()
    world.say(f"After the argument, {helper.id} reached for the bright red squeegee.")
    world.say(f"{hero.id} saw it and remembered the flashback right away.")
    reconciliation(world, hero, helper)
    clean_with_tool(world, hero, helper, cape, TOOLS["squeegee"])

    world.facts.update(
        hero=hero,
        helper=helper,
        cape=cape,
        mask=mask,
        tool=TOOLS["squeegee"],
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    return [
        f'Write a short superhero story for a young child about {hero.id}, {helper.id}, and a squeegee.',
        f'Tell a gentle story where {hero.id} thinks {helper.id} missed the bucket, then they reconcile and clean slime together.',
        f'Write a tiny hero story that includes a flashback, a mess, and a squeegee, ending with a clean rooftop.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    cape = f["cape"]
    return [
        QAItem(
            question=f"Why did {hero.id} feel upset before they reconciled?",
            answer=f"{hero.id} felt upset because {hero.id} thought {helper.id} had missed the bucket and let slime splash the cape.",
        ),
        QAItem(
            question=f"What helped {hero.id} and {helper.id} make up?",
            answer=f"Their reconciliation happened when {helper.id} explained the wind and brought out the squeegee, so they could solve the problem together.",
        ),
        QAItem(
            question=f"What was cleaned by the end of the story?",
            answer=f"The cape was cleaned, and the rooftop looked bright again after the squeegee work.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a squeegee used for?",
            answer="A squeegee is used to push water or sticky messes off a smooth surface like glass or tile.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that briefly shows something that happened earlier, so the reader can remember it too.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop being upset with each other and make up after a disagreement.",
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
        if e.covers:
            bits.append(f"covers={sorted(e.covers)}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:6} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this superhero world expects a place where the crew can clean a slime mess with a squeegee.)"


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with a mess, a squeegee, flashback, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
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
    if place not in SETTINGS:
        raise StoryError(explain_rejection())
    hero_gender = "girl" if rng.random() < 0.5 else "boy"
    helper_gender = "boy" if hero_gender == "girl" else "girl"
    hero_name = args.name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper_name = args.helper or rng.choice(BOY_NAMES if helper_gender == "boy" else GIRL_NAMES)
    return StoryParams(hero_name=hero_name, hero_gender=hero_gender, helper_name=helper_name, helper_gender=helper_gender, place=place)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid()
        print(f"{len(triples)} compatible (place, tool) combos:\n")
        for place, tool in triples:
            print(f"  {place:10} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [
            generate(StoryParams(hero_name="Nova", hero_gender="girl", helper_name="Milo", helper_gender="boy", place="rooftop")),
            generate(StoryParams(hero_name="Iris", hero_gender="girl", helper_name="Theo", helper_gender="boy", place="alley")),
        ]
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
