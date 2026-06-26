#!/usr/bin/env python3
"""
storyworlds/worlds/fantasy_kosher_problem_solving_conflict_animal_story.py
=========================================================================

A small animal-fantasy story world about a gentle conflict and a kosher
problem-solving turn.

Premise:
- A small animal protagonist wants to share a magical treat in a fantasy setting.
- The treat must be kosher, and the characters must solve a conflict about what
  can be eaten and how to help everyone join in.
- The ending proves a concrete change in the world: the shared meal becomes
  kosher, safe, and happily shared.

This world keeps the prose child-facing and concrete, with physical meters and
emotional memes driving the story events.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "mouse": {"subject": "they", "object": "them", "possessive": "their"},
            "rabbit": {"subject": "they", "object": "them", "possessive": "their"},
            "fox": {"subject": "they", "object": "them", "possessive": "their"},
            "bear": {"subject": "they", "object": "them", "possessive": "their"},
            "owl": {"subject": "they", "object": "them", "possessive": "their"},
            "cat": {"subject": "they", "object": "them", "possessive": "their"},
        }
        return mapping.get(self.type, {"subject": "it", "object": "it", "possessive": "its"})[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = False
    magic: str = ""


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    kosher: bool
    allowed: set[str]
    risky: set[str]


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    protects: set[str]
    method: str
    result: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _ensure(m: dict[str, float], key: str) -> float:
    if key not in m:
        m[key] = 0.0
    return m[key]


def trigger_conflict(world: World, hero: Entity) -> None:
    hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1.0


def _r_temptation(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.characters() if e.type == "mouse"), None)
    snack = world.entities.get("snack")
    if not hero or not snack:
        return out
    if hero.meters.get("hunger", 0.0) < THRESHOLD:
        return out
    sig = ("temptation", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1.0
    out.append(f"{hero.label or hero.id} stared at the treat and really wanted a bite.")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.memes.get("warning", 0.0) < THRESHOLD or hero.memes.get("desire", 0.0) < THRESHOLD:
        return out
    sig = ("conflict", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1.0
    out.append("__conflict__")
    return out


def _r_plan(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    snack = world.entities.get("snack")
    fix = world.entities.get("fix")
    if not hero or not helper or not snack or not fix:
        return out
    if hero.memes.get("conflict", 0.0) < THRESHOLD:
        return out
    sig = ("plan", fix.id)
    if sig in world.fired:
        return out
    if snack.label not in fix.protects:
        return out
    world.fired.add(sig)
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1.0
    helper.memes["kindness"] = helper.memes.get("kindness", 0.0) + 1.0
    out.append(f"They thought of a careful way that would keep the snack kosher and safe.")
    return out


CAUSAL_RULES = [
    _r_temptation,
    _r_conflict,
    _r_plan,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(x for x in lines if x != "__conflict__")
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def kosher_reason(snack: Snack) -> str:
    return f"{snack.label} is kosher because it stays within the simple food rules of this world."


def select_fix(snack: Snack) -> Optional[Fix]:
    for fix in FIXES:
        if snack.label in fix.protects:
            return fix
    return None


def predict_resolution(world: World, hero: Entity, snack: Snack) -> bool:
    sim = world.copy()
    h = sim.get(hero.id)
    h.memes["warning"] = 1.0
    h.memes["desire"] = 1.0
    propagate(sim, narrate=False)
    return any(e.id == "fix" for e in sim.entities.values()) and snack.label in FIXES[0].protects


SETTINGS = {
    "moon_garden": Setting(place="the moonlit garden", indoors=False, magic="silver light"),
    "pine_hall": Setting(place="the pine hall", indoors=True, magic="soft lantern glow"),
    "river_wood": Setting(place="the river wood", indoors=False, magic="singing reeds"),
}

SNACKS = {
    "apple_cakes": Snack(
        id="apple_cakes",
        label="apple cakes",
        phrase="small apple cakes with honey",
        kosher=True,
        allowed={"garden", "hall", "wood"},
        risky={"spoil", "share"},
    ),
    "berry_bread": Snack(
        id="berry_bread",
        label="berry bread",
        phrase="a berry bread loaf",
        kosher=True,
        allowed={"garden", "hall", "wood"},
        risky={"crush"},
    ),
    "moon_pie": Snack(
        id="moon_pie",
        label="moon pie",
        phrase="a moon pie made with bright crust",
        kosher=False,
        allowed={"garden", "hall", "wood"},
        risky={"spill"},
    ),
}

FIXES = [
    Fix(
        id="tea_tray",
        label="a clean tea tray",
        phrase="a clean tea tray for sharing",
        protects={"apple cakes", "berry bread"},
        method="placed it on a tray with napkins",
        result="the treat stayed neat and kosher",
    ),
    Fix(
        id="covered_basket",
        label="a covered basket",
        phrase="a covered basket with a snug cloth",
        protects={"apple cakes", "berry bread"},
        method="covered it carefully",
        result="nothing dusty touched the snack",
    ),
]

NAMES = {
    "mouse": ["Mina", "Milo", "Mossy", "Nib", "Pip"],
    "rabbit": ["Tala", "Bunny", "Rin", "Lula", "Poppy"],
    "fox": ["Fenn", "Tavi", "Sly", "Roo", "Clover"],
    "bear": ["Bran", "Hugo", "Nori", "Mallow", "Tiko"],
    "owl": ["Orin", "Wren", "Luma", "Sage", "Pella"],
    "cat": ["Kiki", "Lio", "Nina", "Mika", "Zuri"],
}

TRAITS = ["brave", "curious", "gentle", "careful", "bright", "quick"]


@dataclass
class StoryParams:
    setting: str
    hero_type: str
    helper_type: str
    snack: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fantasy kosher animal story with conflict and problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero-type", choices=list(NAMES))
    ap.add_argument("--helper-type", choices=list(NAMES))
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--trait", choices=TRAITS)
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
    hero_type = args.hero_type or rng.choice(list(NAMES))
    helper_type = args.helper_type or rng.choice([k for k in NAMES if k != hero_type])
    snack = args.snack or rng.choice(list(SNACKS))
    trait = args.trait or rng.choice(TRAITS)
    sn = SNACKS[snack]
    if not sn.kosher:
        raise StoryError("This world only tells stories about kosher snacks.")
    if hero_type == helper_type:
        raise StoryError("The helper animal should be different from the hero animal.")
    return StoryParams(setting=setting, hero_type=hero_type, helper_type=helper_type, snack=snack, trait=trait)


def _make_name(kind: str, rng: random.Random) -> str:
    return rng.choice(NAMES[kind])


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    rng = random.Random(params.seed or 0)

    hero_name = _make_name(params.hero_type, rng)
    helper_name = _make_name(params.helper_type, rng)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.hero_type,
        label=hero_name,
        traits=[params.trait, "animal"],
        meters={"hunger": 1.0},
        memes={"desire": 0.0, "warning": 0.0, "conflict": 0.0, "hope": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper_type,
        label=helper_name,
        traits=["kind", "animal"],
        meters={},
        memes={"kindness": 0.0},
    ))
    snack = world.add(Entity(
        id="snack",
        type="snack",
        label=SNACKS[params.snack].label,
        phrase=SNACKS[params.snack].phrase,
        owner=helper.id,
    ))
    fix = world.add(Entity(
        id="fix",
        type="fix",
        label=FIXES[0].label,
        phrase=FIXES[0].phrase,
        owner=helper.id,
    ))

    # Act 1
    world.say(f"In {world.setting.place}, a {params.trait} little {params.hero_type} named {hero_name} found {snack.phrase}.")
    world.say(f"{helper_name}, a gentle {params.helper_type}, said it was kosher and ready to share.")
    world.para()

    # Act 2
    world.say(f"The air glowed with {world.setting.magic}, and the snack smelled sweet.")
    world.say(f"But {hero_name} wanted to grab a piece at once, while {helper_name} worried the sharing dish was not ready.")
    hero.memes["warning"] += 1.0
    propagate(world, narrate=True)
    world.say(f"{hero_name} pouted, because the idea of waiting felt hard.")
    world.para()

    # Act 3
    hero.memes["warning"] += 0.0
    hero.memes["desire"] += 1.0
    hero.memes["conflict"] += 1.0
    prop_lines = []
    fix_def = select_fix(SNACKS[params.snack])
    if fix_def is None:
        raise StoryError("No fair fix exists for that snack.")
    world.say(f"{helper_name} thought for a moment, then found {fix_def.label}.")
    world.say(f"Together they {fix_def.method}, and the snack stayed kosher and neat.")
    world.say(f"{hero_name} took a small bite, then smiled at {helper_name}.")
    world.say(f"In the end, they shared {snack.label} with calm paws and happy faces.")
    hero.memes["conflict"] = 0.0
    hero.memes["hope"] += 1.0
    helper.memes["kindness"] += 1.0

    world.facts.update(
        hero=hero,
        helper=helper,
        snack=snack,
        fix=fix_def,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    snack = f["snack"]
    return [
        f"Write a short fantasy animal story about {hero.label} the {hero.type} and a kosher snack.",
        f"Tell a gentle story where {hero.label} wants to share {snack.label} but there is a conflict, and {helper.label} helps solve the problem.",
        f"Write a child-friendly animal story set in {world.setting.place} with a kosher treat and a happy solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    snack = f["snack"]
    fix = f["fix"]
    return [
        QAItem(
            question=f"Who wanted to eat the snack too quickly in {world.setting.place}?",
            answer=f"{hero.label}, the little {hero.type}, wanted to eat it right away.",
        ),
        QAItem(
            question=f"Who helped solve the conflict about {snack.label}?",
            answer=f"{helper.label}, the gentle {helper.type}, helped think of a safe and kosher way to share.",
        ),
        QAItem(
            question=f"What did they use so the snack would stay tidy?",
            answer=f"They used {fix.label} and placed the snack carefully so it stayed kosher and neat.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.label} and {helper.label} sharing {snack.label} happily in {world.setting.place}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does kosher mean?",
            answer="Kosher means food follows the food rules used in this story world, so it is okay to eat.",
        ),
        QAItem(
            question="What is a conflict?",
            answer="A conflict is when two wishes bump into each other, like wanting a snack now but also wanting to do it the safe way.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking carefully and finding a good way to fix a hard situation.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {e.label} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- entity(H), kind(H,character), type(H,mouse).
helper(K) :- entity(K), kind(K,character), type(K,cat).
kosher_snack(S) :- snack(S), kosher(S).

problem(H,S) :- hero(H), snack(S), desire(H), warning(H), kosher_snack(S).
conflict(H) :- problem(H,_).
solution(H,F) :- conflict(H), fix(F), protects(F,S), snack(S).
shared(H,S) :- solution(H,_), snack(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        lines.append(asp.fact("magic", sid, s.magic))
    for sid, s in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        if s.kosher:
            lines.append(asp.fact("kosher", sid))
        for a in sorted(s.allowed):
            lines.append(asp.fact("allowed", sid, a))
    for fid, f in enumerate(FIXES):
        lines.append(asp.fact("fix", f.id))
        for p in sorted(f.protects):
            lines.append(asp.fact("protects", f.id, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show kosher_snack/1. #show conflict/1."))
    if model is None:
        print("No ASP model.")
        return 1
    print("OK: ASP rules loaded.")
    return 0


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for hero_type in NAMES:
            for helper_type in NAMES:
                if helper_type == hero_type:
                    continue
                for snack_id, snack in SNACKS.items():
                    if snack.kosher:
                        combos.append((setting, hero_type, snack_id))
    return combos


CURATED = [
    StoryParams(setting="moon_garden", hero_type="mouse", helper_type="cat", snack="apple_cakes", trait="curious"),
    StoryParams(setting="pine_hall", hero_type="rabbit", helper_type="owl", snack="berry_bread", trait="gentle"),
    StoryParams(setting="river_wood", hero_type="fox", helper_type="bear", snack="apple_cakes", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show kosher_snack/1.\n#show conflict/1.\n#show solution/2.\n#show shared/2."))
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
            header = f"### {p.setting} / {p.hero_type} / {p.snack}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
