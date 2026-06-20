#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/wrap_gerund_mantle_surprise_fairy_tale.py
=========================================================================

A standalone fairy-tale story world about a child decorating a castle mantle,
wrapping something around it, and finding a surprise hidden in plain sight.

The world is intentionally small:
- a child helper
- a mantle in a cozy hall
- a wrapping material
- a hidden surprise
- a careful grown-up who helps reveal it

The story logic is state-driven:
- the child wants to decorate the mantle
- wrapping changes the mantle's appearance
- the act of decorating can loosen a hidden latch
- revealing the surprise changes the emotional state
- the ending image proves the surprise was found and shared

This script follows the Storyweavers contract:
- stdlib only
- imports storyworlds/results.py eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes a Python reasonableness gate and inline ASP twin
- generates three QA sets from world state
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
JOY_MIN = 1.0


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

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "princess"}
        male = {"boy", "father", "dad", "man", "king", "prince"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "queen": "queen", "king": "king"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    scene: str
    mood: str
    hall_line: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Mantle:
    id: str
    label: str
    phrase: str
    the: str
    near: str
    drape: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Wrap:
    id: str
    label: str
    phrase: str
    verb: str
    effect: str
    hidden: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Surprise:
    id: str
    label: str
    phrase: str
    reveal: str
    gift: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    mantle = world.get("mantle")
    surprise = world.get("surprise")
    if mantle.meters["draped"] < THRESHOLD or surprise.meters["hidden"] < THRESHOLD:
        return out
    if world.get("surprise").meters["revealed"] >= THRESHOLD:
        return out
    sig = ("reveal",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    surprise.meters["revealed"] += 1
    surprise.memes["delight"] += 1
    world.get("child").memes["joy"] += 1
    world.get("grownup").memes["warmth"] += 1
    out.append("__reveal__")
    return out


CAUSAL_RULES = [Rule("reveal", "social", _r_reveal)]


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


def can_wrap(setting: Setting, mantle: Mantle, wrap: Wrap, surprise: Surprise) -> bool:
    return "castle" in setting.tags and wrap.hidden == surprise.id and mantle.id == "mantle"


def avoid_reason(setting: Setting, mantle: Mantle, wrap: Wrap, surprise: Surprise) -> str:
    return (
        f"(No story: this fairy-tale scene needs a castle hall, a mantle to decorate, "
        f"a wrapping thing that can hide the surprise, and a hidden gift that can be revealed.)"
    )


@dataclass
@dataclass
class StoryParams:
    setting: str
    mantle: str
    wrap: str
    surprise: str
    child_name: str
    child_type: str
    grownup_name: str
    grownup_type: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world about wrapping a mantle and finding a surprise."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mantle", choices=MANTLES)
    ap.add_argument("--wrap", choices=WRAPS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--grownup-name")
    ap.add_argument("--grownup-type", choices=["queen", "king", "mother", "father"])
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


SETTINGS = {
    "castle_hall": Setting(
        "castle_hall",
        "the castle hall",
        "a candlelit hall with stone walls and tall windows",
        "warm",
        "A carved mantle stood above the hearth, waiting for a festival touch.",
        tags={"castle", "hall"},
    ),
    "old_keep": Setting(
        "old_keep",
        "the old keep",
        "a quiet keep with velvet shadows and polished flags",
        "gentle",
        "A wide mantle rested above the fire, looking a little plain.",
        tags={"castle", "hall"},
    ),
}

MANTLES = {
    "mantle": Mantle(
        "mantle",
        "mantle",
        "a mantle",
        "the mantle",
        "along the stone hearth",
        "dressed in gold and ash",
        tags={"mantle"},
    )
}

WRAPS = {
    "garland": Wrap(
        "garland",
        "garland",
        "a garland of ivy and ribbon",
        "wrapping",
        "the mantle bright and festive",
        "a tiny latch hidden behind the center stone",
        tags={"wrap", "garland"},
    ),
    "cloth": Wrap(
        "cloth",
        "cloth",
        "a long blue cloth",
        "wrapping",
        "the mantle soft and neat",
        "a little secret door tucked behind the wood",
        tags={"wrap", "cloth"},
    ),
}

SURPRISES = {
    "birds": Surprise(
        "birds",
        "birds",
        "a nest of three sleeping birds",
        "revealed",
        "a nest of three tiny birds, warm and safe in a feather bed",
        tags={"surprise", "birds"},
    ),
    "crown": Surprise(
        "crown",
        "crown",
        "a silver crown wrapped in silk",
        "revealed",
        "a silver crown for the gentle queen of the hall",
        tags={"surprise", "crown"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Nora", "Elsa", "Sia", "Tessa"]
BOY_NAMES = ["Owen", "Pip", "Rowan", "Theo", "Finn", "Jasper"]
GROWNUP_NAMES = ["Queen Aster", "King Rowan", "Queen Elowen", "King Cedric"]

CURATED = [
    StoryParams("castle_hall", "mantle", "garland", "birds", "Lina", "girl", "Queen Aster", "queen"),
    StoryParams("old_keep", "mantle", "cloth", "crown", "Owen", "boy", "King Cedric", "king"),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS.values():
        for m in MANTLES.values():
            for w in WRAPS.values():
                for su in SURPRISES.values():
                    if can_wrap(s, m, w, su):
                        combos.append((s.id, m.id, w.id, su.id))
    return combos


def tell(setting: Setting, mantle: Mantle, wrap: Wrap, surprise: Surprise,
         child_name: str, child_type: str, grownup_name: str, grownup_type: str) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, role="child"))
    grownup = world.add(Entity(id="grownup", kind="character", type=grownup_type, label=grownup_name, role="grownup"))
    mantle_ent = world.add(Entity(id="mantle", type="mantle", label=mantle.label))
    wrap_ent = world.add(Entity(id="wrap", type="wrap", label=wrap.label))
    surprise_ent = world.add(Entity(id="surprise", type="surprise", label=surprise.label))

    world.say(
        f"In {setting.place}, there was a {setting.scene}. {setting.hall_line}"
    )
    world.say(
        f"{child_name} loved the hall's glow and wanted to make the mantle look ready for a fairy-tale feast."
    )
    world.para()
    world.say(
        f'{child_name} found {wrap.phrase} and started {wrap.verb} the mantle.'
        f" The {wrap.label} made {wrap.effect}."
    )
    mantle_ent.meters["draped"] += 1
    surprise_ent.meters["hidden"] += 1
    child.memes["hope"] += 1
    child.memes["care"] += 1
    world.say(
        f"While {child_name} worked, {wrap.hidden} felt a little loose, like a secret trying to wake up."
    )
    propagate(world, narrate=False)
    world.para()
    world.say(
        f"Then {child_name} saw a small shine behind the mantle and called for {grownup_name}."
    )
    if surprise.id == "birds":
        world.say(
            f"{grownup_name} lifted the garland carefully and {surprise.reveal} {surprise.gift}."
        )
        world.say(
            f"The birds chirped softly, and {child_name} held still so their tiny feathers would not be frightened."
        )
    else:
        world.say(
            f"{grownup_name} opened the little secret place and {surprise.reveal} {surprise.gift}."
        )
        world.say(
            f"The crown glittered like moonlight, and {child_name} gasped at the royal surprise."
        )
    world.say(
        f"In the end, the mantle was bright, the surprise was found, and {child_name} smiled beside {grownup_name}."
    )

    world.facts.update(
        setting=setting,
        mantle=mantle,
        wrap=wrap,
        surprise=surprise,
        child=child,
        grownup=grownup,
        mantle_ent=mantle_ent,
        surprise_ent=surprise_ent,
        outcome="revealed",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story for a young child that includes the word "{f["wrap"].verb}" and the word "mantle".',
        f"Tell a gentle castle story where {f['child'].label} is {f['wrap'].verb} a mantle and discovers a surprise.",
        f'Write a short story in a fairy-tale style where a child decorates a mantle and finds something hidden behind it.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    grownup = f["grownup"]
    wrap = f["wrap"]
    surprise = f["surprise"]
    qa = [
        ("Who is the story about?", f"It is about {child.label}, who was helping in a castle hall, and {grownup.label}, who came to see the surprise."),
        ("What was the child doing?", f"{child.label} was {wrap.verb} the mantle so it would look ready for a feast. That work also loosened the hidden place where the surprise was waiting."),
        ("What was found in the end?", f"They found {surprise.gift}. The surprise had been hidden behind the mantle, and calling {grownup.label} helped reveal it safely."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["wrap"].tags) | set(f["surprise"].tags) | set(f["setting"].tags) | {"mantle"}
    qa: list[tuple[str, str]] = []
    if "mantle" in tags:
        qa.append(("What is a mantle?", "A mantle is the shelf or ledge above a fireplace where people may place decorations."))
    if "wrap" in tags:
        qa.append(("What does it mean to wrap something?", "To wrap something means to put material around it, like ribbon or cloth, so it is covered or decorated."))
    if "surprise" in tags:
        qa.append(("What is a surprise?", "A surprise is something unexpected that appears or is discovered when you are not already expecting it."))
    if "castle" in tags:
        qa.append(("What is a castle hall?", "A castle hall is a big room inside a castle where people can gather, celebrate, or wait by the fire."))
    return qa


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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
can_wrap(S, M, W, Su) :- setting(S), mantle(M), wrap(W), surprise(Su), castle(S), wrap_hidden(W, Su), mantle_ok(M).
revealed :- wrapped(mantle), hidden(surprise), wrap_hidden(_, surprise).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for tag in sorted(s.tags):
            lines.append(asp.fact(tag, sid))
    for mid in MANTLES:
        lines.append(asp.fact("mantle", mid))
    for wid, w in WRAPS.items():
        lines.append(asp.fact("wrap", wid))
        lines.append(asp.fact("wrap_hidden", wid, w.hidden))
    for suid in SURPRISES:
        lines.append(asp.fact("surprise", suid))
    lines.append(asp.fact("mantle_ok", "mantle"))
    lines.append(asp.fact("wrapped", "mantle"))
    lines.append(asp.fact("hidden", "surprise"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show can_wrap/4."))
    return sorted(set(asp.atoms(model, "can_wrap")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    else:
        print("OK: generate smoke test passed.")
    return rc


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("(No story: unknown setting.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mantle is None or c[1] == args.mantle)
              and (args.wrap is None or c[2] == args.wrap)
              and (args.surprise is None or c[3] == args.surprise)]
    if not combos:
        raise StoryError(avoid_reason(SETTINGS["castle_hall"], MANTLES["mantle"], WRAPS["garland"], SURPRISES["birds"]))
    setting, mantle, wrap, surprise = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    grownup_type = args.grownup_type or rng.choice(["queen", "king"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    grownup_name = args.grownup_name or rng.choice(GROWNUP_NAMES)
    return StoryParams(setting, mantle, wrap, surprise, child_name, child_type, grownup_name, grownup_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        MANTLES[params.mantle],
        WRAPS[params.wrap],
        SURPRISES[params.surprise],
        params.child_name,
        params.child_type,
        params.grownup_name,
        params.grownup_type,
    )
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show can_wrap/4.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:\n")
        for row in asp_valid_combos():
            print("  ", row)
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
            header = f"### {p.child_name}: {p.wrap} on the {p.mantle} ({p.surprise})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
