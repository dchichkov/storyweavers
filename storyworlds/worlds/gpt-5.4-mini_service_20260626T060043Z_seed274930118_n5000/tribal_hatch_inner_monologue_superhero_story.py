#!/usr/bin/env python3
"""
A standalone storyworld for a tiny superhero tale with an inner monologue beat.

Premise:
- A young hero in a tribal village hears a signal from a sealed hatch.
- The hatch hides something important, but opening it rashly could hurt people.
- The hero thinks through the risk, chooses a careful method, and becomes brave
  in a way that helps the whole village.

The world model uses:
- meters: physical quantities like charge, smoke, pressure, crack, safety
- memes: emotional quantities like fear, courage, duty, hope, pride

The story always has:
- beginning: hero, tribe, and the sealed hatch
- middle turn: danger rises, inner monologue weighs choices
- ending: the hero acts, the hatch opens safely, and the village changes
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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Hatch:
    id: str
    label: str
    phrase: str
    danger: str
    opens_to: str
    requires: str
    location: str
    hero_can_open: bool = True


@dataclass
class Power:
    id: str
    label: str
    phrase: str
    effect: str
    charge_use: int
    safe: bool
    use_word: str
    reveal: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "cliff": Setting(place="the wind-swept cliff village", mood="high and bright", affords={"lift", "signal"}),
    "jungle": Setting(place="the jungle clearing", mood="green and humming", affords={"lift", "signal"}),
    "island": Setting(place="the coral island dock", mood="salt-bright", affords={"lift", "signal"}),
}

HATCHES = {
    "stone_hatch": Hatch(
        id="stone_hatch",
        label="stone hatch",
        phrase="a heavy stone hatch with old symbols",
        danger="a burst of dust and hot air",
        opens_to="a hidden chamber",
        requires="steady hands and patience",
        location="under the old shrine",
    ),
    "metal_hatch": Hatch(
        id="metal_hatch",
        label="metal hatch",
        phrase="a round metal hatch with a glowing seam",
        danger="a flash of sparking power",
        opens_to="a power room",
        requires="a careful release lever",
        location="near the watchtower",
    ),
    "wooden_hatch": Hatch(
        id="wooden_hatch",
        label="wooden hatch",
        phrase="a creaking wooden hatch in the floor",
        danger="a sudden drop into a dark shaft",
        opens_to="a rescue tunnel",
        requires="two people lifting together",
        location="beneath the meeting hut",
    ),
}

POWERS = {
    "pulse": Power(
        id="pulse",
        label="pulse-blast",
        phrase="a quick pulse-blast",
        effect="pushes back danger",
        charge_use=2,
        safe=False,
        use_word="blast",
        reveal="the hatch seam glow brighter",
    ),
    "shield": Power(
        id="shield",
        label="shield-glow",
        phrase="a bright shield-glow",
        effect="holds back heat and sparks",
        charge_use=1,
        safe=True,
        use_word="shield",
        reveal="the air steady down",
    ),
    "lift": Power(
        id="lift",
        label="lift-strength",
        phrase="a steady lift-strength",
        effect="helps with heavy things",
        charge_use=1,
        safe=True,
        use_word="lift",
        reveal="the hatch edge rise without scraping",
    ),
}

TRIBES = [
    "Suntribe",
    "Shelltribe",
    "Mosstribe",
    "Windtribe",
]

HERO_NAMES = ["Kira", "Nia", "Tala", "Milo", "Rafi", "Zuri"]
PARENT_NAMES = ["Aunt Mara", "Uncle Sef", "Elder Jo", "Captain Rina"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    hatch: str
    power: str
    name: str
    tribe: str
    mentor: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
class SimState:
    def __init__(self, setting: Setting, hatch: Hatch, power: Power) -> None:
        self.setting = setting
        self.hatch = hatch
        self.power = power
        self.world = World(setting)
        self.hero = self.world.add(Entity(
            id="hero", kind="character", type="boy", label="", phrase="",
            meters={"charge": 3.0, "safety": 0.0},
            memes={"fear": 0.0, "courage": 0.0, "duty": 0.0, "hope": 0.0, "pride": 0.0},
        ))
        self.mentor = self.world.add(Entity(
            id="mentor", kind="character", type="woman", label="mentor", phrase="",
            meters={"calm": 2.0},
            memes={"worry": 1.0, "trust": 1.0},
        ))
        self.tribe = self.world.add(Entity(
            id="tribe", kind="thing", type="tribe", label="tribe", phrase="",
            plural=True, meters={"crowd": 9.0}, memes={"hope": 1.0},
        ))
        self.world.facts.update(hatch=hatch, power=power, setting=setting)

    def copy_for_prediction(self) -> "SimState":
        other = SimState(self.setting, self.hatch, self.power)
        other.world = World(self.setting)
        other.world.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "owner": v.owner, "caretaker": v.caretaker,
            "worn_by": v.worn_by, "plural": v.plural,
            "meters": dict(v.meters), "memes": dict(v.memes),
        }) for k, v in self.world.entities.items()}
        other.hero = other.world.entities["hero"]
        other.mentor = other.world.entities["mentor"]
        other.tribe = other.world.entities["tribe"]
        return other


def _inner_monologue(state: SimState) -> str:
    fear = state.hero.memes["fear"]
    duty = state.hero.memes["duty"]
    hope = state.hero.memes["hope"]
    if fear > duty:
        return "I am scared, the hero thought, but the hatch might hide help for everyone."
    if hope > fear:
        return "If I stay calm, the hero thought, I can open it without hurting anyone."
    return "A true hero does not rush, the hero thought. A true hero listens first."


def _safe_open(state: SimState) -> bool:
    return state.power.safe and state.hero.meters["charge"] >= state.power.charge_use


def _predict_risk(state: SimState) -> bool:
    return not _safe_open(state)


def _build_scene(state: SimState) -> None:
    w = state.world
    h = state.hatch
    p = state.power
    hero = state.hero
    mentor = state.mentor
    tribe = state.tribe

    hero_name = w.facts["name"]
    tribe_name = w.facts["tribe"]
    mentor_name = w.facts["mentor"]

    w.say(
        f"In {w.setting.place}, a young hero named {hero_name} guarded the {tribe_name} "
        f"while everyone watched {h.phrase}."
    )
    hero.memes["duty"] += 1
    hero.memes["hope"] += 1
    w.say(
        f"{hero_name} wore the bright badge of {tribe_name} and carried {p.phrase} at {hero.pronoun('possessive')} side."
    )
    w.say(
        f"{mentor_name} pointed at the hatch and said it was sealed for a reason, because inside waited {h.opens_to}."
    )
    w.para()

    hero.memes["fear"] += 2
    if _predict_risk(state):
        w.say(
            f"The seam of the hatch gave off a strange warning, and {hero_name}'s stomach felt tight."
        )
        w.say(_inner_monologue(state))
        w.say(
            f"{hero_name} wanted to {p.use_word} at once, but {mentor_name} shook {mentor.pronoun('possessive')} head."
        )
        hero.memes["courage"] += 1
        w.say(
            f"Then {hero_name} noticed that {h.requires} was the right way to handle it."
        )
    else:
        w.say(
            f"The hatch looked dangerous, but {hero_name} felt calm enough to use {p.label} the careful way."
        )
        w.say(_inner_monologue(state))
    w.para()

    if p.id == "shield":
        hero.meters["charge"] -= p.charge_use
        hero.memes["courage"] += 2
        w.say(
            f"{hero_name} raised {p.label} first, and the glow held back the sparks while {hero_name} worked the latch."
        )
    elif p.id == "lift":
        hero.meters["charge"] -= p.charge_use
        hero.memes["courage"] += 2
        w.say(
            f"{hero_name} used {p.label} with both hands, and the heavy hatch rose without scraping the stone."
        )
    else:
        # If unsafe, the hero must not brute-force it.
        if not _safe_open(state):
            raise StoryError("The chosen power is too risky for this hatch; the hero would not act like a careful superhero.")
        hero.meters["charge"] -= p.charge_use

    hero.meters["safety"] += 1
    hero.memes["pride"] += 1
    tribe.memes["hope"] += 2
    w.say(
        f"The hatch opened to {h.opens_to}, and instead of danger there was a rescue light that helped the {tribe_name}."
    )
    w.say(
        f"{hero_name} stood tall at the open hatch, feeling brave not because {hero_name} rushed, but because {hero_name} chose the safest way."
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    hatch = HATCHES[params.hatch]
    power = POWERS[params.power]
    state = SimState(setting, hatch, power)
    state.world.facts.update(
        name=params.name,
        tribe=params.tribe,
        mentor=params.mentor,
        power=power,
        hatch=hatch,
    )
    _build_scene(state)
    return state.world


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for h in HATCHES:
            for p in POWERS:
                if h == "metal_hatch" and p == "shield":
                    combos.append((s, h, p))
                elif h == "wooden_hatch" and p == "lift":
                    combos.append((s, h, p))
                elif h == "stone_hatch" and p == "shield":
                    combos.append((s, h, p))
    return combos


def explain_rejection(hatch: Hatch, power: Power) -> str:
    return (
        f"(No story: {power.label} is not a careful match for the {hatch.label}. "
        f"The hero's choice would not feel like a superhero solution.)"
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a child about {f["name"]} and a mysterious hatch in a {f["tribe"]} village.',
        f'Tell a story where an inner monologue helps {f["name"]} choose the safe way to open {f["hatch"].label}.',
        f'Write a gentle superhero story that uses the word "tribal" and ends with an opened hatch helping everyone.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    name = f["name"]
    tribe = f["tribe"]
    mentor = f["mentor"]
    hatch: Hatch = f["hatch"]
    power: Power = f["power"]
    return [
        QAItem(
            question=f"Who was the young hero in the {tribe} story?",
            answer=f"The young hero was {name}, who watched over the {tribe} and stayed brave.",
        ),
        QAItem(
            question=f"What was hidden behind the {hatch.label}?",
            answer=f"Behind the {hatch.label} was {hatch.opens_to}, and opening it safely helped the village.",
        ),
        QAItem(
            question=f"Why did {mentor} tell {name} not to rush?",
            answer=f"{mentor} knew the hatch could cause {hatch.danger}, so {name} had to choose the careful way.",
        ),
        QAItem(
            question=f"How did {name} act like a superhero in the end?",
            answer=f"{name} acted like a superhero by listening, thinking, and using {power.label} safely to open the hatch.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What does a hatch usually do?",
        answer="A hatch is a small door or cover that opens to something hidden underneath or inside.",
    ),
    QAItem(
        question="What is a tribe?",
        answer="A tribe is a group of people who belong together, share a home, and often help one another.",
    ),
    QAItem(
        question="Why do superheroes think before they act?",
        answer="Superheroes think before they act so they can protect people and solve problems safely.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(S) :- setting_fact(S).
hatch(H) :- hatch_fact(H).
power(P) :- power_fact(P).

valid(S,H,P) :- setting(S), hatch(H), power(P),
                 compatible(H,P).
#show valid/3.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_fact", s))
    for h in HATCHES:
        lines.append(asp.fact("hatch_fact", h))
    for p in POWERS:
        lines.append(asp.fact("power_fact", p))
    for _, h, p in valid_combos():
        lines.append(asp.fact("compatible", h, p))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


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


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero storyworld with a tribal hatch and inner monologue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hatch", choices=HATCHES)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--name")
    ap.add_argument("--tribe", choices=TRIBES)
    ap.add_argument("--mentor", choices=PARENT_NAMES)
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
    if args.hatch and args.power:
        if (args.hatch, args.power) not in {(h, p) for _, h, p in valid_combos()}:
            raise StoryError(explain_rejection(HATCHES[args.hatch], POWERS[args.power]))
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.hatch:
        combos = [c for c in combos if c[1] == args.hatch]
    if args.power:
        combos = [c for c in combos if c[2] == args.power]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, hatch, power = rng.choice(sorted(combos))
    tribe = args.tribe or rng.choice(TRIBES)
    name = args.name or rng.choice(HERO_NAMES)
    mentor = args.mentor or rng.choice(PARENT_NAMES)
    return StoryParams(setting=setting, hatch=hatch, power=power, name=name, tribe=tribe, mentor=mentor)


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes}")
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


CURATED = [
    StoryParams(setting="cliff", hatch="metal_hatch", power="shield", name="Kira", tribe="Suntribe", mentor="Aunt Mara"),
    StoryParams(setting="jungle", hatch="wooden_hatch", power="lift", name="Tala", tribe="Mosstribe", mentor="Elder Jo"),
    StoryParams(setting="island", hatch="stone_hatch", power="shield", name="Zuri", tribe="Shelltribe", mentor="Captain Rina"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        combos = sorted(set(asp.atoms(model, "valid")))
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            seed = base_seed + i
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
