#!/usr/bin/env python3
"""
A small Storyweavers world about a rodent, a burst of bravery, a magical
mistake, and a funny reconciliation.

The story premise:
- A little rodent wants to do something brave.
- A tiny magic trick goes wrong in a comic way.
- A helper gets annoyed, then everyone fixes it together.
- The ending proves the change with a concrete new state.
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
# Domain model
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "rodent"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the pantry"
    mood: str = "quiet"
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    mishap: str
    magic_kind: str
    risk_meter: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    fixes: set[str]
    cost: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


THRESHOLD = 1.0


def _m(e: Entity, key: str, amt: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + amt


def _a(e: Entity, key: str, amt: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + amt


def bravery_line(hero: Entity) -> str:
    return f"{hero.id} took a tiny breath and tried to look as brave as a thundercloud in a cape."


def magic_line(action: Action) -> str:
    return {
        "spark": "The sparkle popped like a hiccup in a teacup.",
        "float": "The charm wobbled in the air like a spoon learning ballet.",
        "glow": "The glow blinked on and off like a sleepy firefly.",
    }[action.id]


def resolve_reaction(world: World, rodent: Entity, helper: Entity, charm: Charm, action: Action) -> None:
    if rodent.meters.get(action.risk_meter, 0.0) >= THRESHOLD:
        _a(rodent, "embarrassment", 1.0)
        _a(helper, "annoyance", 1.0)
        world.say(
            f"{magic_line(action)} It made {rodent.id}'s whiskers and paws go wild instead of doing the job."
        )
        world.say(
            f"{helper.id} stared at the mess and groaned, because {charm.label} was supposed to help, not bounce around like a circus grape."
        )


def apply_magic(world: World, rodent: Entity, helper: Entity, action: Action, charm: Charm) -> None:
    if action.id == "spark":
        _m(rodent, "sparkly", 1.0)
        _m(rodent, "noise", 1.0)
    elif action.id == "float":
        _m(rodent, "floating", 1.0)
        _m(rodent, "floor_fear", 1.0)
    elif action.id == "glow":
        _m(rodent, "glow", 1.0)
        _m(rodent, "hope", 1.0)

    _m(rodent, action.risk_meter, 1.0)
    _a(rodent, "bravery", 1.0)
    world.say(
        f"{rodent.id} wanted to {action.verb}, because being brave sounded better than staying tiny and worried forever."
    )
    world.say(bravery_line(rodent))
    world.say(
        f"{helper.id} handed over {charm.phrase} and said, \"Try it once. If it fizzles, we can laugh and clean up.\""
    )
    resolve_reaction(world, rodent, helper, charm, action)


def reconcile(world: World, rodent: Entity, helper: Entity, charm: Charm, action: Action) -> bool:
    if rodent.memes.get("embarrassment", 0.0) < THRESHOLD:
        return False
    _a(rodent, "apology", 1.0)
    _a(helper, "forgiveness", 1.0)
    _a(rodent, "bravery", 1.0)
    world.say(
        f"{rodent.id} drooped its ears and said sorry for making such a silly magical disaster."
    )
    world.say(
        f"{helper.id} snorted a laugh, then smiled, because the whole thing was too funny to stay mad about."
    )
    world.say(
        f"They tried again together, and this time {charm.label} worked just enough to be useful."
    )
    return True


def finish(world: World, rodent: Entity, helper: Entity, action: Action, charm: Charm) -> None:
    _m(rodent, action.risk_meter, 0.0)
    _m(rodent, "success", 1.0)
    _a(rodent, "joy", 1.0)
    _a(helper, "joy", 1.0)
    world.say(
        f"At the end, {rodent.id} managed to {action.verb}, and the little miracle looked less like a thunderbolt and more like a polite sneeze."
    )
    world.say(
        f"{helper.id} and {rodent.id} laughed together while {charm.label} glimmered safely in {rodent.pronoun('possessive')} paws."
    )


def tell(setting: Setting, action: Action, charm: Charm, hero_name: str = "Pip") -> World:
    world = World(setting)
    rodent = world.add(Entity(id=hero_name, kind="character", type="rodent"))
    helper = world.add(Entity(id="Mara", kind="character", type="mouse", label="friend Mara"))

    world.say(
        f"In {setting.place}, {rodent.id} was a small rodent with a big wish to be brave."
    )
    world.say(
        f"{rodent.id} liked {action.gerund}, even though the idea of magic always made {rodent.pronoun('subject')} sneeze."
    )
    world.say(
        f"{helper.label} kept a funny little charm called {charm.label}, and said it could help with {action.verb}."
    )

    world.para()
    apply_magic(world, rodent, helper, action, charm)

    world.para()
    reconciled = reconcile(world, rodent, helper, charm, action)
    if not reconciled:
        world.say("Nothing needed fixing, which was unusual and a little boring.")
    finish(world, rodent, helper, action, charm)

    world.facts.update(
        setting=setting,
        action=action,
        charm=charm,
        rodent=rodent,
        helper=helper,
        reconciled=reconciled,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "pantry": Setting(place="the pantry", mood="quiet", affords={"spark", "glow"}),
    "attic": Setting(place="the attic", mood="dusty", affords={"float", "glow"}),
    "garden_shed": Setting(place="the garden shed", mood="clattery", affords={"spark", "float"}),
}

ACTIONS = {
    "spark": Action(
        id="spark",
        verb="call up a brave spark",
        gerund="calling up brave sparks",
        mishap="sparks flew into the crackers",
        magic_kind="spark",
        risk_meter="buzz",
        tags={"magic", "comedy", "bravery"},
    ),
    "float": Action(
        id="float",
        verb="make a tiny lantern float",
        gerund="making tiny lanterns float",
        mishap="the lantern bumped the rafters",
        magic_kind="float",
        risk_meter="wobble",
        tags={"magic", "comedy", "bravery"},
    ),
    "glow": Action(
        id="glow",
        verb="light up a crumb-path",
        gerund="lighting up crumb-paths",
        mishap="the crumbs glowed too brightly",
        magic_kind="glow",
        risk_meter="shine",
        tags={"magic", "comedy", "bravery", "reconciliation"},
    ),
}

CHARMS = {
    "glitter_nut": Charm(
        id="glitter_nut",
        label="the glitter nut",
        phrase="a glitter nut on a string",
        fixes={"buzz", "shine"},
        cost="one sneeze",
    ),
    "moon_thimble": Charm(
        id="moon_thimble",
        label="the moon thimble",
        phrase="a tiny moon thimble",
        fixes={"wobble", "shine"},
        cost="three giggles",
    ),
    "copper_pebble": Charm(
        id="copper_pebble",
        label="the copper pebble",
        phrase="a copper pebble charm",
        fixes={"buzz", "wobble"},
        cost="one apology",
    ),
}

NAMES = ["Pip", "Milo", "Nib", "Tansy", "Jori", "Luma"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(pantry). setting(attic). setting(garden_shed).

action(spark). action(float). action(glow).
charm(glitter_nut). charm(moon_thimble). charm(copper_pebble).

risk(spark,buzz). risk(float,wobble). risk(glow,shine).

fixes(glitter_nut,buzz). fixes(glitter_nut,shine).
fixes(moon_thimble,wobble). fixes(moon_thimble,shine).
fixes(copper_pebble,buzz). fixes(copper_pebble,wobble).

compatible(S,A,C) :- setting(S), action(A), charm(C), risk(A,R), fixes(C,R).
#show compatible/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("risk", aid, a.risk_meter))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        for r in sorted(c.fixes):
            lines.append(asp.fact("fixes", cid, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_compatible() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid in SETTINGS:
        for aid, a in ACTIONS.items():
            for cid, c in CHARMS.items():
                if a.risk_meter in c.fixes:
                    out.append((sid, aid, cid))
    return out


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_compatible())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Params / story generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    action: str
    charm: str
    name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedic rodent bravery storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--name", choices=NAMES)
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
    combos = valid_combos()
    combos = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.action is None or c[1] == args.action)
        and (args.charm is None or c[2] == args.charm)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, action, charm = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    return StoryParams(setting=setting, action=action, charm=charm, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ACTIONS[params.action], CHARMS[params.charm], params.name)
    story = world.render()
    prompts = [
        "Write a short, funny story about a tiny rodent who gets brave with a little magic.",
        f"Tell a comedy story in {world.setting.place} where a rodent named {params.name} tries to use magic and then makes up with a friend.",
    ]
    rodent = world.facts["rodent"]
    helper = world.facts["helper"]
    action = world.facts["action"]
    charm = world.facts["charm"]
    story_qa = [
        QAItem(
            question=f"Who is the brave rodent in the story?",
            answer=f"The brave rodent is {rodent.id}, a small rodent who wanted to be brave."
        ),
        QAItem(
            question=f"What did {rodent.id} try to do with magic?",
            answer=f"{rodent.id} tried to {action.verb} using {charm.label}."
        ),
        QAItem(
            question=f"Why did {helper.label} get upset at first?",
            answer=f"{helper.label} got upset because the magic was funny but messy, and it did not work the way they hoped."
        ),
        QAItem(
            question=f"How did {rodent.id} and {helper.label} fix the problem?",
            answer=f"They apologized, laughed, and tried again together until {charm.label} worked well enough."
        ),
    ]
    world_qa = [
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something even when you feel scared."
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people make up after a disagreement and become friendly again."
        ),
        QAItem(
            question="What is magic?",
            answer="Magic is pretend or mysterious power that can make surprising things happen in stories."
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


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
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_compatible()
        print(f"{len(combos)} compatible setting/action/charm combos:\n")
        for s, a, c in combos:
            print(f"  {s:12} {a:8} {c:15}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        curated = [
            StoryParams("pantry", "glow", "glitter_nut", "Pip"),
            StoryParams("attic", "float", "moon_thimble", "Milo"),
            StoryParams("garden_shed", "spark", "copper_pebble", "Tansy"),
        ]
        samples = [generate(p) for p in curated]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.name}: {p.action} with {p.charm} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
