#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/spruce_glop_enable_moral_value_reconciliation_problem.py
========================================================================================

A small tall-tale storyworld about a spruce tree, a troublesome glop, and a
problem that can be solved only when the characters choose moral courage and
reconciliation.

The world is built around three seed words:
- spruce
- glop
- enable

And three narrative features:
- Moral Value
- Reconciliation
- Problem Solving

The setting is intentionally small and classical: a windy village edge with a
spruce grove, a market path, and a neighborly dispute that becomes a chance to
do right, make amends, and fix what went wrong.

The prose aims for a tall-tale flavor while staying child-facing and concrete.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    id: str
    place: str
    details: str
    mood: str
    prompt: str


@dataclass
class Trouble:
    id: str
    source: str
    label: str
    mess: str
    threatens: str
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    method: str
    power: int
    virtue: str
    moral: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str = "spruce_edge"
    trouble: str = "glop"
    remedy: str = "sweep"
    hero: str = "Mabel"
    hero_gender: str = "girl"
    helper: str = "Otis"
    helper_gender: str = "boy"
    elder: str = "Aunt June"
    elder_gender: str = "woman"
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_mess_spreads(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["mess"] < THRESHOLD:
            continue
        sig = ("mess_spreads", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        path = world.entities.get("path")
        if path is not None:
            path.meters["slippery"] += 1
        for eid in ("hero", "helper"):
            if eid in world.entities:
                world.get(eid).memes["worry"] += 1
        out.append("__mess__")
    return out


def _r_reconcile(world: World) -> list[str]:
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    elder = world.entities.get("elder")
    if not hero or not helper or not elder:
        return []
    if hero.memes["apology"] < THRESHOLD or helper.memes["forgiveness"] < THRESHOLD:
        return []
    sig = ("reconcile",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["peace"] += 1
    helper.memes["peace"] += 1
    elder.memes["pride"] += 1
    return ["__reconcile__"]


CAUSAL_RULES = [Rule("mess_spreads", _r_mess_spreads), Rule("reconcile", _r_reconcile)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "spruce_edge": Setting(
        id="spruce_edge",
        place="the edge of the spruce grove",
        details="A row of spruce trees stood like green candles, and the lane bent past a little bridge.",
        mood="windy",
        prompt="the spruce grove edge",
    ),
    "market_lane": Setting(
        id="market_lane",
        place="the market lane",
        details="Stalls leaned in a long line, and the spruce boughs from a nearby yard brushed the rooflines.",
        mood="busy",
        prompt="the market lane",
    ),
    "river_ford": Setting(
        id="river_ford",
        place="the river ford",
        details="The water was shallow, the stones were round, and a spruce tree leaned over the bank like a watchman.",
        mood="muddy",
        prompt="the river ford",
    ),
}

TROUBLES = {
    "glop": Trouble(
        id="glop",
        source="a bucket of sticky glop",
        label="glop",
        mess="glop",
        threatens="the bridge boards and the wagon wheel",
        severity=2,
        tags={"glop", "mess", "slippery"},
    ),
    "pitch": Trouble(
        id="pitch",
        source="a jar of black pitch",
        label="pitch",
        mess="glop",
        threatens="the path stones",
        severity=2,
        tags={"glop", "sticky"},
    ),
    "sap": Trouble(
        id="sap",
        source="a crock of spruce sap",
        label="sap",
        mess="glop",
        threatens="the porch step",
        severity=1,
        tags={"glop", "sap", "spruce"},
    ),
}

REMEDIES = {
    "sweep": Remedy(
        id="sweep",
        label="a broom",
        method="swept the mess into a bucket",
        power=2,
        virtue="care",
        moral="it is right to help clean what you helped spill",
        tags={"problem_solving", "moral"},
    ),
    "sand": Remedy(
        id="sand",
        label="a sack of dry sand",
        method="covered the glop with dry sand and shoveled it away",
        power=3,
        virtue="helpfulness",
        moral="a calm helper can turn trouble into a tidy path",
        tags={"problem_solving", "moral"},
    ),
    "cloth": Remedy(
        id="cloth",
        label="a clean cloth",
        method="pressed the mess into the cloth and wrung it out",
        power=1,
        virtue="patience",
        moral="a small problem sometimes needs a steady hand",
        tags={"problem_solving", "moral"},
    ),
}

GIRL_NAMES = ["Mabel", "Ivy", "Nina", "Rose", "Hazel", "Clara", "Wren"]
BOY_NAMES = ["Otis", "Eli", "Hank", "Toby", "Bram", "Jude", "Milo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for tid, trouble in TROUBLES.items():
            for rid, remedy in REMEDIES.items():
                if remedy.power >= trouble.severity:
                    combos.append((sid, tid, rid))
    return combos


def explain_rejection(trouble: Trouble, remedy: Remedy) -> str:
    return (
        f"(No story: {remedy.label} is too weak for {trouble.label}. "
        f"The fix must be strong enough to solve the problem without hand-waving.)"
    )


def setting_sentence(setting: Setting) -> str:
    return f"{setting.details} It was {setting.mood} enough to make a sensible body walk a little straighter."


def _setup(world: World, hero: Entity, helper: Entity, elder: Entity, setting: Setting) -> None:
    hero.memes["curiosity"] += 1
    helper.memes["care"] += 1
    world.say(
        f"At {setting.place}, {hero.id} and {helper.id} were as lively as two sparks in a stove."
    )
    world.say(setting_sentence(setting))


def _trouble(world: World, hero: Entity, helper: Entity, trouble: Trouble) -> None:
    hero.memes["want"] += 1
    helper.memes["doubt"] += 1
    world.say(
        f"They spotted {trouble.source} by {trouble.threatens}, and the whole place went from neat to nervous."
    )
    world.say(
        f'"We can handle it," {hero.id} said, but {helper.id} saw that the {trouble.label} was a real bother.'
    )


def _spill(world: World, trouble: Trouble) -> None:
    world.get("glop").meters["mess"] += 1
    world.get("path").meters["dirty"] += 1
    propagate(world, narrate=False)


def _argument(world: World, hero: Entity, helper: Entity, trouble: Trouble) -> None:
    hero.memes["pride"] += 1
    helper.memes["frustration"] += 1
    world.say(
        f"{hero.id} tried to rush ahead, but {trouble.label} made the boards slick as fish scales."
    )
    world.say(
        f"{helper.id} warned, \"If we leave it, somebody will slip.\""
    )


def _warning(world: World, elder: Entity, hero: Entity, trouble: Trouble) -> None:
    elder.memes["wisdom"] += 1
    world.say(
        f"{elder.id} came along like a thundercloud with kindness in it and said, "
        f"\"A problem that spills for one person becomes a burden for the whole lane.\""
    )
    world.say(
        f"\"Doing the right thing now will enable a better tomorrow,\" {elder.id} said, pointing at the mess."
    )


def _apologize(world: World, hero: Entity, helper: Entity, elder: Entity) -> None:
    hero.memes["apology"] += 1
    helper.memes["forgiveness"] += 1
    world.say(
        f"{hero.id} stopped, took a breath, and said sorry for making the trouble bigger."
    )
    world.say(
        f"{helper.id} nodded, because {helper.id} had wanted peace more than a victory."
    )
    propagate(world, narrate=False)


def _fix(world: World, elder: Entity, remedy: Remedy, trouble: Trouble) -> None:
    world.get("glop").meters["mess"] = 0
    world.get("path").meters["dirty"] = 0
    world.say(
        f"Then {elder.id} grabbed {remedy.label} and {remedy.method}."
    )
    world.say(
        f"That did the trick, and the lane looked fit for a parade of geese."
    )


def _reconcile(world: World, hero: Entity, helper: Entity, elder: Entity) -> None:
    world.say(
        f"{hero.id} and {helper.id} made up, shoulder to shoulder, as if a new bridge had been built between them."
    )
    world.say(
        f"{elder.id} smiled, because the finest repair was not only the path, but the friendship too."
    )


def _ending(world: World, setting: Setting) -> None:
    world.say(
        f"By sunset, the spruce trees stood dark and proud, and the lane was clean enough to reflect the sky."
    )
    world.say(
        f"The little town remembered that day as the one when a glop of trouble was answered with honesty, help, and a good clean cure."
    )


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    trouble = TROUBLES[params.trouble]
    remedy = REMEDIES[params.remedy]

    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    elder = world.add(Entity(id=params.elder, kind="character", type=params.elder_gender, role="elder"))
    world.add(Entity(id="path", kind="thing", type="path", label="the path"))
    world.add(Entity(id="glop", kind="thing", type="mess", label=trouble.label))
    world.facts["setting"] = setting
    world.facts["trouble"] = trouble
    world.facts["remedy"] = remedy

    _setup(world, hero, helper, elder, setting)
    world.para()
    _trouble(world, hero, helper, trouble)
    _spill(world, trouble)
    _argument(world, hero, helper, trouble)
    world.para()
    _warning(world, elder, hero, trouble)
    _apologize(world, hero, helper, elder)
    _fix(world, elder, remedy, trouble)
    _reconcile(world, hero, helper, elder)
    world.para()
    _ending(world, setting)

    world.facts.update(
        hero=hero,
        helper=helper,
        elder=elder,
        resolved=True,
        mess_cleared=world.get("glop").meters["mess"] < THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story for a young child that includes the words "spruce", "glop", and "enable".',
        f"Tell a story about {f['hero'].id}, {f['helper'].id}, and a sticky problem that can only be fixed by being honest and working together.",
        f"Write a child-friendly tall tale where a bad glop causes a problem near the spruce trees, and the characters reconcile after solving it.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    elder: Entity = f["elder"]
    trouble: Trouble = f["trouble"]
    remedy: Remedy = f["remedy"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question="What problem happened in the story?",
            answer=f"A bucket of {trouble.label} got spilled near {trouble.threatens}, and it made the path messy and hard to trust.",
        ),
        QAItem(
            question="How did the grown-up help?",
            answer=f"{elder.id} brought {remedy.label} and used it to fix the mess. That turned the slippery trouble into a clean path again.",
        ),
        QAItem(
            question=f"Why did {hero.id} and {helper.id} make up?",
            answer=f"They both saw that the right thing was to solve the problem together instead of arguing. After the apology, {helper.id} forgave {hero.id}, and the two of them stood side by side again.",
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"The mess was gone, the friendship was repaired, and the spruce grove at {setting.place} felt peaceful again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a spruce tree?",
            answer="A spruce tree is a tall evergreen tree with sharp green needles. It stays green all year and often looks brave in the wind.",
        ),
        QAItem(
            question="What does glop mean?",
            answer="Glop is a thick, sticky mess that can make a place slippery or hard to clean. It is the kind of trouble that asks for careful hands.",
        ),
        QAItem(
            question="What does enable mean?",
            answer="To enable something means to make it possible or easier to happen. A helpful tool or a smart choice can enable a good result.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making up after a disagreement. It is when people choose kindness, forgive one another, and become friends again.",
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def valid_story_worlds() -> list[tuple[str, str, str]]:
    return valid_combos()


ASP_RULES = r"""
messy(M) :- trouble(M).
solve_ok(R, T) :- remedy(R), trouble(T), power(R, P), severity(T, S), P >= S.
reconcile :- apology(hero), forgiveness(helper).
outcome(clean) :- solve_ok(_, _), reconcile.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("severity", tid, t.severity))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("apology", "hero"))
    lines.append(asp.fact("forgiveness", "helper"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show solve_ok/2."))
    return sorted(set(asp.atoms(model, "solve_ok")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != {(r, t) for _, t, r in valid_combos()}:
        rc = 1
        print("MISMATCH in ASP solver gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, trouble=None, remedy=None, hero=None, hero_gender=None, helper=None, helper_gender=None, elder=None, elder_gender=None, seed=1), random.Random(1)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tall-tale story world about spruce, glop, and doing right.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["woman", "man"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    trouble = args.trouble or rng.choice(list(TROUBLES))
    remedy = args.remedy or rng.choice(list(REMEDIES))
    if trouble and remedy and REMEDIES[remedy].power < TROUBLES[trouble].severity:
        raise StoryError(explain_rejection(TROUBLES[trouble], REMEDIES[remedy]))
    return StoryParams(
        setting=setting,
        trouble=trouble,
        remedy=remedy,
        hero=args.hero or rng.choice(GIRL_NAMES),
        hero_gender=args.hero_gender or "girl",
        helper=args.helper or rng.choice(BOY_NAMES),
        helper_gender=args.helper_gender or "boy",
        elder=args.elder or "Aunt June",
        elder_gender=args.elder_gender or "woman",
    )


def generate(params: StoryParams) -> StorySample:
    for key, table in [("setting", SETTINGS), ("trouble", TROUBLES), ("remedy", REMEDIES)]:
        if getattr(params, key) not in table:
            raise StoryError(f"Unknown {key}: {getattr(params, key)}")
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
        print(asp_program("", "#show solve_ok/2.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_story_worlds())} compatible (setting, trouble, remedy) combos:")
        for row in valid_story_worlds():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [
            generate(StoryParams(setting=s, trouble=t, remedy=r, hero="Mabel", hero_gender="girl",
                                 helper="Otis", helper_gender="boy", elder="Aunt June", elder_gender="woman"))
            for s, t, r in valid_combos()
        ]
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
