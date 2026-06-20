#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/silver_dummy_surprise_repetition_space_adventure.py
===================================================================================

A standalone story world for a tiny Space Adventure style tale with the seed
words "silver" and "dummy", and the narrative instruments Surprise + Repetition.

Base premise
------------
A child astronaut and a tiny robot are on a practice ship. A silver dummy drifts
loose in the cargo bay and keeps surprising them by appearing in new places as
the ship changes direction. The crew repeats the same calm safety steps, learns
what is really happening, and finishes the mission with a safe fix.

The world is built around a small simulated domain:
- typed entities with physical meters and emotional memes
- a surprise event that is grounded in world state, not a frozen paragraph
- repeated checking / repeating a safety phrase as a story instrument
- a gentle turn from confusion to understanding and a concrete ending image

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/silver_dummy_surprise_repetition_space_adventure.py
    python storyworlds/worlds/gpt-5.4-mini/silver_dummy_surprise_repetition_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4-mini/silver_dummy_surprise_repetition_space_adventure.py --qa
    python storyworlds/worlds/gpt-5.4-mini/silver_dummy_surprise_repetition_space_adventure.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    vibe: str
    detail: str
    repeat_line: str


@dataclass
class Surprise:
    id: str
    label: str
    phrase: str
    drift: str
    appear: str
    secret: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_bump_attention(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["surprise"] < THRESHOLD:
            continue
        sig = ("attention", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["alert"] += 1
        out.append("__surprise__")
    return out


def _r_reassure(world: World) -> list[str]:
    out: list[str] = []
    if "crew" not in world.entities:
        return out
    crew = world.get("crew")
    if crew.memes["reassurance"] < THRESHOLD:
        return out
    sig = ("reassure", crew.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    crew.memes["calm"] += 1
    out.append("__calm__")
    return out


CAUSAL_RULES = [
    Rule("attention", "social", _r_bump_attention),
    Rule("reassure", "social", _r_reassure),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def lift_surprise(world: World, dummy: Entity, narrator: Entity, surprise: Surprise) -> None:
    dummy.meters["surprise"] += 1
    narrator.memes["surprised"] += 1
    propagate(world, narrate=False)


def scan(world: World, narrator: Entity, setting: Setting) -> None:
    world.say(
        f"On the {setting.place}, {narrator.id} watched the silver stars through the window. "
        f"{setting.detail}"
    )
    world.say(
        f'{narrator.id} said the same check twice, just to be sure: "{setting.repeat_line}"'
    )
    world.say(f'The tiny ship felt quiet, bright, and ready for a space adventure.')


def discover(world: World, child: Entity, bot: Entity, surprise: Surprise) -> None:
    world.say(
        f"Then came a surprise. A {surprise.label} drifted from the cargo hatch, its {surprise.drift}."
    )
    world.say(
        f'{bot.id} blinked. "{surprise.appear}" {bot.id} asked, looking again and again.'
    )
    child.memes["curious"] += 1


def repeat_check(world: World, child: Entity, bot: Entity, setting: Setting) -> None:
    world.say(
        f'{child.id} pointed and repeated the check: "{setting.repeat_line}"'
    )
    world.say(
        f'{bot.id} repeated it too, because on a ship, saying the plan twice helps the mind stay steady.'
    )


def explain(world: World, child: Entity, bot: Entity, surprise: Surprise) -> None:
    world.say(
        f"At last they saw the truth: the {surprise.label} was not alive at all. "
        f"It had been a practice dummy, silver and round, left loose from training."
    )
    world.say(
        f'{child.id} laughed with relief. "{surprise.secret}"'
    )
    child.memes["relief"] += 1
    bot.memes["relief"] += 1


def fix_dummy(world: World, child: Entity, bot: Entity, fix: Fix) -> None:
    child.memes["joy"] += 1
    bot.memes["joy"] += 1
    world.say(
        f"Together they used the ship's {fix.label}. {fix.text}."
    )
    world.say(
        f"The silver dummy rolled into its cradle, and the cargo bay felt safe again."
    )


def failed_fix(world: World, child: Entity, bot: Entity, fix: Fix) -> None:
    world.say(
        f"Together they tried the {fix.label}, but {fix.fail}."
    )
    world.say(
        f"The dummy kept drifting, so they had to call for a grown-up to secure it."
    )


def tell(setting: Setting, surprise: Surprise, fix: Fix,
         child_name: str = "Nova", child_type: str = "girl",
         bot_name: str = "Pip", bot_type: str = "robot",
         captain_name: str = "Captain Ray") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    bot = world.add(Entity(id=bot_name, kind="character", type=bot_type, role="helper"))
    crew = world.add(Entity(id="crew", kind="character", type="crew", role="crew"))
    captain = world.add(Entity(id=captain_name, kind="character", type="captain", role="adult"))

    world.facts["setting"] = setting
    world.facts["surprise"] = surprise
    world.facts["fix"] = fix

    scan(world, child, setting)
    world.para()
    discover(world, child, bot, surprise)
    repeat_check(world, child, bot, setting)
    lift_surprise(world, bot, child, surprise)
    world.para()
    explain(world, child, bot, surprise)

    if fix.power >= 2:
        crew.memes["reassurance"] += 1
        world.say(
            f'{captain.id} came in and nodded. "{fix.label.capitalize()} first, then steady hands."'
        )
        fix_dummy(world, child, bot, fix)
        outcome = "fixed"
    else:
        failed_fix(world, child, bot, fix)
        outcome = "called_help"

    world.facts.update(child=child, bot=bot, crew=crew, captain=captain, outcome=outcome)
    return world


SETTINGS = {
    "orbital": Setting(
        "orbital", "orbital window", "silver light",
        "Outside the glass, the moon made a bright trail across the hull.",
        "Check the hatch, check the latch, check the hatch again.",
    ),
    "dock": Setting(
        "dock", "dock window", "silver sparks",
        "Dock lights glittered on the metal walls like tiny frozen fireworks.",
        "Check the straps, check the straps, then check them once more.",
    ),
    "moonbase": Setting(
        "moonbase", "moon bay", "silver dust",
        "Moon dust clung to boots and floated in soft little clouds.",
        "Check the boots, check the boots, then check the boots again.",
    ),
}

SURPRISES = {
    "dummy": Surprise(
        "dummy", "dummy", "silver and round",
        "drifting like a sleepy moon", "Is that a moon rock?", "It was only a practice dummy.",
        tags={"dummy", "silver", "surprise"},
    ),
    "pod": Surprise(
        "pod", "pod", "silver-striped",
        "wobbling in a slow spin", "Is that an empty pod?", "It was a training pod with no one inside.",
        tags={"surprise"},
    ),
    "parcel": Surprise(
        "parcel", "parcel", "silver-taped",
        "bouncing in the air pump", "Did the mail float in?", "It was only a sealed parcel for the base.",
        tags={"surprise"},
    ),
}

FIXES = {
    "strap": Fix("strap", "strap clamp", 3, 3,
                 "they tightened the strap clamp around the dummy and clipped it to the wall",
                 "the clamp slipped on the smooth metal",
                 "secured the silver dummy with a strap clamp",
                 tags={"fix"}),
    "net": Fix("net", "net launcher", 2, 2,
               "they fired a soft net and tucked the dummy inside a storage bin",
               "the net missed and only bounced off the hatch",
               "caught the silver dummy in a soft net",
               tags={"fix"}),
    "call": Fix("call", "radio call", 1, 1,
                "they sent a calm radio call and waited for help",
                "the call went through, but it was too small to solve the drifting",
                "asked for help with a calm radio call",
                tags={"help"}),
}

GIRL_NAMES = ["Nova", "Mira", "Luna", "Zia", "Aria"]
BOY_NAMES = ["Kai", "Jett", "Rune", "Pax", "Theo"]


@dataclass
class StoryParams:
    setting: str
    surprise: str
    fix: str
    name: str
    gender: str
    bot: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for sur_id in SURPRISES:
            for fix_id in FIXES:
                combos.append((sid, sur_id, fix_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld with silver surprise repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--bot")
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
              if (args.setting is None or c[0] == args.setting)
              and (args.surprise is None or c[1] == args.surprise)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, surprise, fix = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    bot = args.bot or rng.choice(["Pip", "Bex", "Dot"])
    return StoryParams(setting, surprise, fix, name, gender, bot)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    s = f["setting"]
    sp = f["surprise"]
    fx = f["fix"]
    return [
        f'Write a space adventure story for a young child that includes "silver" and "dummy".',
        f'Tell a story where {f["child"].id} and {f["bot"].id} meet a surprise in the {s.place} and keep checking the plan twice.',
        f'Write a gentle spaceship story with repetition, a surprise, and a safe fix using a {fx.label}.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    bot = f["bot"]
    setting = f["setting"]
    surprise = f["surprise"]
    fix = f["fix"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {bot.id} on a little space adventure. They are the ones who notice the surprise and work together."),
        ("What surprising thing did they find?",
         f"They found a {surprise.label}, and it was {surprise.phrase}. At first it looked strange, so they had to look again to understand it."),
        ("What did they repeat?",
         f'They repeated "{setting.repeat_line}" more than once. Repeating the check helped them stay calm and careful.'),
    ]
    if f["outcome"] == "fixed":
        qa.append((
            "How did they solve the problem?",
            f"They used the {fix.label} and secured the silver dummy safely. That changed the drifting problem into a tidy, safe ending."
        ))
    else:
        qa.append((
            "What happened when the fix was not enough?",
            f"They called for help, because the {fix.label} was too weak to hold the dummy. The grown-up had to finish the job."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with the cargo bay safe again and the silver dummy put away where it belonged. The repeated checks led to a calm finish."
    ))
    return qa


KNOWLEDGE = {
    "silver": [("What is silver?",
                "Silver is a shiny metal color. It often looks bright and cool, like moonlight.")],
    "dummy": [("What is a dummy?",
               "A dummy can be a practice model or stand-in used for training. It is not a real person.")],
    "space": [("Why do astronauts check things twice?",
              "Astronauts check things twice because in space they must be extra careful. A small mistake can become a big problem.")],
    "repetition": [("What is repetition in a story?",
                     "Repetition means saying or doing something again. In a story, it can help show a habit or make a moment feel important.")],
    "surprise": [("What is a surprise?",
                  "A surprise is something unexpected. It can make a character stop, look, and think again.")],
}
KNOWLEDGE_ORDER = ["silver", "dummy", "space", "repetition", "surprise"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["surprise"].tags) | {"silver", "repetition", "space"}
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(_: Surprise, __: Fix) -> str:
    return "(No story: this combination cannot make a coherent surprise-and-fix space adventure.)"


ASP_RULES = r"""
valid(S, U, F) :- setting(S), surprise(U), fix(F).
surprise_event(U) :- surprise(U).
repeat_story(S) :- setting(S).
outcome(fixed) :- chosen_fix(F), power(F, P), P >= 2.
outcome(called_help) :- chosen_fix(F), power(F, P), P < 2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for u in SURPRISES:
        lines.append(asp.fact("surprise", u))
    for f in FIXES:
        lines.append(asp.fact("fix", f))
        lines.append(asp.fact("power", f, FIXES[f].power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("chosen_fix", params.fix)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    sample = generate(resolve_params(argparse.Namespace(setting=None, surprise=None, fix=None, name=None, gender=None, bot=None), random.Random(7)))
    if not sample.story:
        rc = 1
    print("OK: smoke test generated a story." if sample.story else "FAIL: no story.")
    if asp_outcome(sample.params) not in {"fixed", "called_help"}:
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SURPRISES[params.surprise], FIXES[params.fix],
                 params.name, params.gender, params.bot)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
    StoryParams("orbital", "dummy", "strap", "Nova", "girl", "Pip"),
    StoryParams("dock", "parcel", "net", "Kai", "boy", "Dot"),
    StoryParams("moonbase", "pod", "call", "Mira", "girl", "Bex"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not samples:
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
