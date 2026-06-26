#!/usr/bin/env python3
"""
A small fairy-tale storyworld about a tiny pore, a patient worry, and a suspenseful
choice that leads to a safe ending.

The seed idea:
A child notices a little pore in a magical lantern, and a curious light keeps
leaking out. The caretaker fears the lantern may fail during the night watch.
They must decide whether to rush, mend, or wait for the right helper.

The story engine models:
- a magical object with a pore that leaks light or scent
- a child, a guardian, and a helper
- rising suspense when the leak is ignored
- a gentle repair that proves the danger was real and the fix mattered

The story style is close to a fairy tale: simple, concrete, and child-facing.
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
# World model
# ---------------------------------------------------------------------------

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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for key in ["leak", "care", "repair", "glow", "dark", "worry", "fear", "hope", "suspense", "joy"]:
            self.meters.setdefault(key, 0.0)
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "woman", "mother", "sister"}
        male = {"boy", "prince", "king", "man", "father", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the moonlit tower"
    afford: set[str] = field(default_factory=lambda: {"watch", "mend", "wait"})


@dataclass
class Cause:
    id: str
    name: str
    effect: str
    tool: str
    hint: str


@dataclass
class StoryParams:
    setting: str
    cause: str
    hero: str
    guardian: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "tower": Setting(place="the moonlit tower"),
    "forest": Setting(place="the silver forest"),
    "cottage": Setting(place="the little cottage by the hill"),
}

CAUSES = {
    "light": Cause(
        id="light",
        name="a tiny light leak",
        effect="light leaked through the pore",
        tool="wax",
        hint="a bead of wax",
    ),
    "scent": Cause(
        id="scent",
        name="a sweet scent leak",
        effect="sweet scent drifted through the pore",
        tool="spider silk",
        hint="a strand of spider silk",
    ),
    "mist": Cause(
        id="mist",
        name="a mist leak",
        effect="mist slipped through the pore",
        tool="silver moss",
        hint="silver moss",
    ),
}

HEROES = [
    ("Ayla", "girl", "curious"),
    ("Nico", "boy", "gentle"),
    ("Mira", "girl", "brave"),
    ("Tobin", "boy", "small"),
]

GUARDIANS = [
    ("the guardian", "mother"),
    ("the guardian", "father"),
    ("the стар?")  # placeholder? no, must avoid invalid. We'll override below.
]

HELPERS = [
    ("the candle-maker", "candle-maker"),
    ("the seamstress", "seamstress"),
    ("the old beetle", "beetle"),
]

# fix invalid helper list by redefining cleanly
GUARDIAN_TYPES = ["mother", "father", "queen", "king"]
HELPER_TYPES = ["candle-maker", "seamstress", "beekeeper"]


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _article(name: str) -> str:
    return "an" if name[:1].lower() in "aeiou" else "a"


def _capitalize(s: str) -> str:
    return s[:1].upper() + s[1:]


def _leak_name(cause: Cause) -> str:
    return cause.name


def valid_combo(setting: Setting, cause: Cause) -> bool:
    return "watch" in setting.afford and cause.id in CAUSES


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting_key = args.setting or rng.choice(list(SETTINGS))
    cause_key = args.cause or rng.choice(list(CAUSES))
    hero_name, hero_type, hero_trait = args.hero or rng.choice(HEROES)
    guardian_type = args.guardian or rng.choice(GUARDIAN_TYPES)
    helper_type = args.helper or rng.choice(HELPER_TYPES)

    if not valid_combo(SETTINGS[setting_key], CAUSES[cause_key]):
        raise StoryError("The chosen setting and cause do not support a suspenseful watch-and-mend story.")

    return StoryParams(
        setting=setting_key,
        cause=cause_key,
        hero=f"{hero_name}:{hero_type}:{hero_trait}",
        guardian=guardian_type,
        helper=helper_type,
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def _parse_hero(spec: str) -> tuple[str, str, str]:
    name, typ, trait = spec.split(":", 2)
    return name, typ, trait


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    cause = CAUSES[params.cause]
    hero_name, hero_type, hero_trait = _parse_hero(params.hero)

    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, traits=[hero_trait, "little"]))
    guardian = world.add(Entity(id="guardian", kind="character", type=params.guardian, label=f"the {params.guardian}"))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=f"the {params.helper}"))

    lantern = world.add(Entity(
        id="lantern",
        type="lantern",
        label="lantern",
        phrase="a lantern with a tiny pore near its glass side",
        caretaker=guardian.id,
    ))
    patch = world.add(Entity(
        id="patch",
        type="repair",
        label=cause.tool,
        phrase=f"a little patch of {cause.tool}",
        owner=helper.id,
    ))

    # Act 1: setup
    world.say(f"Once upon a time, in {setting.place}, there lived {hero_name}, a {hero_trait} little {hero_type}.")
    world.say(f"{_capitalize(hero.pronoun('subject'))} loved the night watch, because the old stones and silver windows always seemed to whisper back.")
    world.say(f"One evening, {hero_name} noticed {lantern.phrase}.")

    # Act 2: suspense builds
    world.para()
    world.say(f"At first, only a thin shimmer slipped out, but soon {cause.effect}.")
    lantern.meters["leak"] += 1.0
    hero.memes["suspense"] += 1.0
    guardian.memes["worry"] += 1.0
    world.say(f"The {params.guardian} frowned. “If that pore grows larger, the lantern may fail before midnight,” {_article(params.guardian)} {params.guardian} said.")

    # The child wants to help immediately.
    world.say(f"{hero_name} wanted to fix it right away, but the pore was smaller than a pin and trickier than it looked.")
    hero.memes["hope"] += 1.0
    hero.memes["fear"] += 0.5

    # Act 3: turn and resolution
    world.para()
    world.say(f"Then {helper.label} arrived with {patch.phrase}.")
    world.say(f"“We must mend it gently,” said {helper.label}, “or the crack will wake the whole lamp.”")
    helper.meters["repair"] += 1.0
    lantern.meters["repair"] += 1.0
    lantern.meters["leak"] = 0.0
    lantern.meters["glow"] += 1.0
    guardian.memes["worry"] = 0.0
    hero.memes["suspense"] = 0.0
    hero.memes["joy"] += 1.0
    world.say(f"They pressed the patch over the pore, and at once the lantern grew calm and bright again.")
    world.say(f"By the end, {hero_name} was smiling in the warm glow, and the night watch felt safe once more.")

    world.facts.update(
        hero=hero,
        guardian=guardian,
        helper=helper,
        lantern=lantern,
        cause=cause,
        setting=setting,
        patch=patch,
        hero_name=hero_name,
        hero_trait=hero_trait,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cause: Cause = f["cause"]
    return [
        f'Write a short fairy-tale story for a child about a tiny pore that lets {cause.effect}.',
        f'Tell a suspenseful story where a little hero notices a magical lantern with a pore and helps fix it gently.',
        f'Write a gentle fairy tale in which a caretaker worries about a leak, and a helper brings the right repair.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    guardian: Entity = f["guardian"]
    helper: Entity = f["helper"]
    lantern: Entity = f["lantern"]
    cause: Cause = f["cause"]
    hero_name = f["hero_name"]
    hero_trait = f["hero_trait"]

    return [
        QAItem(
            question=f"Who first noticed the lantern with the pore?",
            answer=f"{hero_name}, the {hero_trait} little {hero.type}, noticed it first in {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {guardian.label} worry about the lantern?",
            answer=f"{guardian.label} worried because {cause.effect}, and the lantern might fail before midnight if the pore grew larger.",
        ),
        QAItem(
            question=f"Who helped mend the pore?",
            answer=f"{helper.label} came with {f['patch'].phrase} and helped mend the pore gently.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The leak stopped, the lantern glowed again, and the night watch became safe and calm.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "pore": QAItem(
        question="What is a pore?",
        answer="A pore is a very tiny opening. In a fairy tale, a pore can be so small that it lets only a little light, scent, or mist slip through.",
    ),
    "suspense": QAItem(
        question="What is suspense in a story?",
        answer="Suspense is the feeling of waiting to see what will happen next, especially when something might go wrong.",
    ),
    "lantern": QAItem(
        question="What does a lantern do?",
        answer="A lantern gives light, so people can see in the dark.",
    ),
    "wax": QAItem(
        question="Why can wax help fix a small hole?",
        answer="Wax can be soft and sticky, so it can cover a tiny hole and help stop a leak.",
    ),
    "spider silk": QAItem(
        question="Why is spider silk special in stories?",
        answer="Spider silk is very thin and strong, so fairy tales often use it for delicate repairs.",
    ),
    "silver moss": QAItem(
        question="What is moss?",
        answer="Moss is a soft green plant that grows in damp places and can look like a little cushion.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    cause: Cause = f["cause"]
    items = [WORLD_KNOWLEDGE["pore"], WORLD_KNOWLEDGE["suspense"], WORLD_KNOWLEDGE["lantern"]]
    if cause.id == "light":
        items.append(WORLD_KNOWLEDGE["wax"])
    elif cause.id == "scent":
        items.append(WORLD_KNOWLEDGE["spider silk"])
    elif cause.id == "mist":
        items.append(WORLD_KNOWLEDGE["silver moss"])
    return items


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A pore is suspenseful when it leaks from a lantern.
suspenseful(L) :- lantern(L), pore(P), leaks(L, P).
needs_mend(L) :- suspenseful(L), guarded_by(guardian, L).
resolved(L) :- needs_mend(L), patched(L).

#show suspenseful/1.
#show needs_mend/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        lines.append(asp.fact("pore", cid))
        lines.append(asp.fact("leaks", "lantern", cid))
    lines.append(asp.fact("lantern", "lantern"))
    lines.append(asp.fact("guarded_by", "guardian", "lantern"))
    lines.append(asp.fact("patched", "lantern"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show suspenseful/1.#show needs_mend/1.#show resolved/1."))
    atoms = set((sym.name, tuple(a.name if a.type != a.type.Number and a.type != a.type.String else (a.number if a.type == a.type.Number else a.string) for a in sym.arguments)) for sym in model)
    expected = {("suspenseful", ("lantern",)), ("needs_mend", ("lantern",)), ("resolved", ("lantern",))}
    if atoms == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH:", atoms, expected)
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

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
        print("\n--- world trace ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            print(f"{e.id}: {e.type} {e.label} {' '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about a pore, suspense, and a gentle repair.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--hero", choices=[h[0] for h in HEROES])
    ap.add_argument("--guardian", choices=GUARDIAN_TYPES)
    ap.add_argument("--helper", choices=HELPER_TYPES)
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


CURATED = [
    StoryParams(setting="tower", cause="light", hero="Ayla:girl:curious", guardian="mother", helper="candle-maker"),
    StoryParams(setting="forest", cause="mist", hero="Mira:girl:brave", guardian="queen", helper="beekeeper"),
    StoryParams(setting="cottage", cause="scent", hero="Nico:boy:gentle", guardian="father", helper="seamstress"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(""))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show suspenseful/1.#show needs_mend/1.#show resolved/1."))
        for sym in model:
            print(sym)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        rng = random.Random(base_seed)
        samples = []
        seen = set()
        for i in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
            header = f"### {p.setting} / {p.cause}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
