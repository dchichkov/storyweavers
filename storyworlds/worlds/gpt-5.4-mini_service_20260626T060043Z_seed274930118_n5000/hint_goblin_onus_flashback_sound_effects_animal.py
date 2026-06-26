#!/usr/bin/env python3
"""
storyworlds/worlds/hint_goblin_onus_flashback_sound_effects_animal.py
=====================================================================

A small animal-story world with a hint of goblin mischief, a visible onus,
flashback beats, and sound effects woven into the simulated prose.

The seed idea:
- An animal protagonist hears a hint that something is wrong.
- A goblin's little prank creates an onus: someone must fix the mess.
- The story uses a flashback to explain why the protagonist knows what to do.
- Sound effects make the scene feel alive, but the plot still comes from world
  state changing under pressure.

This file is self-contained and follows the Storyweavers storyworld contract.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"rabbit", "fox", "cat", "dog", "bird", "squirrel", "mouse"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type == "goblin":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    outdoors: bool = True
    echoes: bool = False
    shelter: bool = False


@dataclass
class Trouble:
    id: str
    verb: str
    sound: str
    mess: str
    onus: str
    flashback: str
    hint_word: str = "hint"


@dataclass
class Fix:
    id: str
    tool: str
    verb: str
    sound: str
    prevents: set[str]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.place)
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label, "phrase": v.phrase,
            "owner": v.owner, "caretaker": v.caretaker, "plural": v.plural,
            "meters": dict(v.meters), "memes": dict(v.memes),
        }) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters.get("mischief", 0.0) < THRESHOLD:
            continue
        if world.facts.get("cleared"):
            continue
        sig = ("mess", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.facts["needs_fix"] = True
        out.append(f"The little mess spread across the path.")
    return out


def _r_onus(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("needs_fix") or world.facts.get("onus_taken"):
        return out
    sig = ("onus",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["onus_taken"] = True
    out.append("Now someone had the onus to make it right.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_mess, _r_onus):
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    goblin_name: str
    trouble: str
    fix: str
    seed: Optional[int] = None


PLACES = {
    "meadow": Place("the meadow", outdoors=True, echoes=False, shelter=False),
    "pond": Place("the pond", outdoors=True, echoes=False, shelter=False),
    "woods": Place("the woods", outdoors=True, echoes=True, shelter=True),
    "barn": Place("the barn", outdoors=False, echoes=True, shelter=True),
}

TROUBLES = {
    "sticky_trail": Trouble(
        id="sticky_trail",
        verb="stuck shiny sap on the path",
        sound="squish",
        mess="sticky",
        onus="clean the trail",
        flashback="Last spring, the little animal had seen sap ruin paws and learned to fetch leaves first.",
        hint_word="hint",
    ),
    "muddy_puddle": Trouble(
        id="muddy_puddle",
        verb="splashed muddy water everywhere",
        sound="plop",
        mess="muddy",
        onus="wash the paws",
        flashback="Once before, a muddy puddle had turned a neat coat brown, so the animal had remembered to step around it.",
        hint_word="hint",
    ),
    "noisy_berries": Trouble(
        id="noisy_berries",
        verb="cracked the berry basket open",
        sound="crack",
        mess="smeared",
        onus="gather the berries back up",
        flashback="At harvest time, the animal had watched berries bounce away and knew a basket had to be held tight.",
        hint_word="hint",
    ),
}

FIXES = {
    "leaf_rake": Fix(id="leaf_rake", tool="a leaf rake", verb="sweep", sound="swish", prevents={"sticky", "muddy"}),
    "towel": Fix(id="towel", tool="a soft towel", verb="wipe", sound="fwip", prevents={"muddy", "smeared"}),
    "basket_lid": Fix(id="basket_lid", tool="a wooden lid", verb="cover", sound="clack", prevents={"smeared"}),
}

HEROES = {
    "rabbit": ["Pip", "Milo", "Tess", "Nina"],
    "fox": ["Juno", "Rae", "Mika", "Finn"],
    "cat": ["Sage", "Mina", "Poppy", "Luna"],
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, place_obj in PLACES.items():
        for trouble_id, trouble in TROUBLES.items():
            for fix_id, fix in FIXES.items():
                if trouble.mess in fix.prevents and (place_obj.outdoors or place_obj.shelter):
                    combos.append((place, trouble_id, fix_id))
    return combos


def explain_rejection(trouble: Trouble, fix: Fix) -> str:
    return (
        f"(No story: {fix.tool} does not reasonably solve the problem of "
        f"{trouble.verb}. The fix must match the kind of mess, so this combo is rejected.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world with a hint, a goblin, an onus, flashback, and sound effects."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero-type", choices=list(HEROES))
    ap.add_argument("--hero")
    ap.add_argument("--goblin-name")
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--fix", choices=FIXES)
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
    if args.trouble and args.fix:
        tr, fx = TROUBLES[args.trouble], FIXES[args.fix]
        if tr.mess not in fx.prevents:
            raise StoryError(explain_rejection(tr, fx))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.trouble is None or c[1] == args.trouble)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, trouble, fix = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(sorted(HEROES))
    hero = args.hero or rng.choice(HEROES[hero_type])
    goblin_name = args.goblin_name or rng.choice(["Nib", "Murk", "Brim", "Wizzle"])
    return StoryParams(
        place=place,
        hero=hero,
        hero_type=hero_type,
        goblin_name=goblin_name,
        trouble=trouble,
        fix=fix,
    )


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.outdoors:
            lines.append(asp.fact("outdoors", pid))
        if p.echoes:
            lines.append(asp.fact("echoes", pid))
        if p.shelter:
            lines.append(asp.fact("shelter", pid))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("mess", tid, t.mess))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for m in sorted(f.prevents):
            lines.append(asp.fact("prevents", fid, m))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(P,T,F) :- place(P), trouble(T), fix(F), mess(T,M), prevents(F,M).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def _story_name(hero: Entity, trouble: Trouble) -> str:
    return f"{hero.id} and the {trouble.id.replace('_', ' ')}"


def build_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero))
    goblin = world.add(Entity(id="goblin", kind="character", type="goblin", label=params.goblin_name))
    trouble = TROUBLES[params.trouble]
    fix = FIXES[params.fix]
    tool = world.add(Entity(id="tool", type="tool", label=fix.tool, caretaker=hero.id))
    world.facts.update(hero=hero, goblin=goblin, trouble=trouble, fix=fix, tool=tool)

    world.say(f"{hero.label} was a small {hero.type} who liked quiet paths and bright mornings.")
    world.say(
        f"One day, {hero.label} heard a little {trouble.hint_word} from the grass: "
        f"{goblin.label} was nearby."
    )
    world.say(
        f"{trouble.flashback} That memory sat in {hero.pronoun('possessive')} head like a lantern."
    )
    world.para()

    hero.memes["attention"] = 1
    goblin.memes["mischief"] = 1
    world.say(
        f"Then came the sound: {trouble.sound}! {goblin.label} had {trouble.verb}."
    )
    propagate(world, narrate=True)
    world.say(
        f"{hero.label} looked at the path and knew the onus was on {hero.pronoun('object')} to help."
    )

    world.para()
    world.say(f"{hero.label} picked up {fix.tool} and said, \"I can {fix.verb} this.\"")
    world.say(f"{fix.sound.capitalize()}! {hero.label} worked carefully until the path looked neat again.")
    world.facts["cleared"] = True
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    trouble = f["trouble"]
    fix = f["fix"]
    return [
        f'Write a short animal story with a hint of goblin mischief, a clear onus, '
        f'a flashback, and sound effects. Include the word "{trouble.hint_word}".',
        f"Tell a gentle story about {hero.label}, {f['goblin'].label}, and a {fix.tool} "
        f"that helps after {trouble.verb}.",
        f"Write a small children's story where an animal remembers a lesson from a flashback "
        f"and fixes a goblin's mess with {fix.tool}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    goblin = f["goblin"]
    trouble = f["trouble"]
    fix = f["fix"]
    return [
        QAItem(
            question=f"Who heard the hint before the goblin caused trouble?",
            answer=f"{hero.label} heard the hint first and noticed that {goblin.label} was nearby.",
        ),
        QAItem(
            question=f"What did the flashback remind {hero.label} about?",
            answer=f"The flashback reminded {hero.label} that {trouble.flashback.lower()}",
        ),
        QAItem(
            question=f"What was the onus after {goblin.label} {trouble.verb}?",
            answer=f"The onus was on {hero.label} to use {fix.tool} and {fix.verb} the mess.",
        ),
        QAItem(
            question=f"How did the story end after the sound effect and the fix?",
            answer=f"It ended with the path clean again, and {hero.label} finishing the job with {fix.tool}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hint?",
            answer="A hint is a small clue that helps someone notice what might be happening.",
        ),
        QAItem(
            question="What is a goblin in a story?",
            answer="A goblin is a tiny fantasy creature that often causes mischief in stories.",
        ),
        QAItem(
            question="What does onus mean?",
            answer="Onus means the duty or responsibility to do something important.",
        ),
        QAItem(
            question="Why do stories use sound effects?",
            answer="Sound effects like crack or swish help the reader imagine what is happening.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is when a story briefly shows something that happened earlier.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
    StoryParams(place="meadow", hero="Pip", hero_type="rabbit", goblin_name="Nib", trouble="sticky_trail", fix="leaf_rake"),
    StoryParams(place="woods", hero="Sage", hero_type="cat", goblin_name="Brim", trouble="muddy_puddle", fix="towel"),
    StoryParams(place="barn", hero="Juno", hero_type="fox", goblin_name="Wizzle", trouble="noisy_berries", fix="basket_lid"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for p, t, f in combos:
            print(f"  {p:8} {t:16} {f:14}")
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
