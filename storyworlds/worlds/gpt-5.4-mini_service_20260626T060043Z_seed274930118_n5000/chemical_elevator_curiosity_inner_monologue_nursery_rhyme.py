#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/chemical_elevator_curiosity_inner_monologue_nursery_rhyme.py
================================================================================

A tiny standalone storyworld: a curious child in an elevator, a chemical that
should not be touched, and a nursery-rhyme style inner monologue that helps the
child choose safely.

The simulated premise:
- A child enters an elevator with a guardian and notices a chemical container.
- Curiosity grows; the child imagines what the bottle might do.
- The guardian notices the risk and warns gently.
- The child pauses, thinks, and chooses not to touch the chemical.
- The elevator ride ends safely, with the child proud of self-control.

This script follows the Storyweavers storyworld contract:
- typed entities with physical meters and emotional memes
- a Python reasonableness gate plus inline ASP twin
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    sealed: bool = False
    safe: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the elevator"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Chemical:
    id: str
    label: str
    phrase: str
    smell: str
    color: str
    risk: str
    reason: str
    can_touch: bool = False
    can_open: bool = False


@dataclass
class Safety:
    id: str
    label: str
    phrase: str
    action: str
    protects: set[str]
    payoff: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_log: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _say_nursery(*parts: str) -> str:
    return " ".join(parts)


def _rule_curiosity(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts["child"]
    chem = world.facts["chemical"]
    if child.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    sig = ("curiosity_line", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["curiosity"] += 1
    out.append(_say_nursery(
        f"{child.id} peered at {chem.label} and wondered, soft and low,"
    ))
    out.append(_say_nursery(
        f"“What does that shiny bottle do?” the little thoughts did glow."
    ))
    return out


def _rule_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts["child"]
    chem = world.facts["chemical"]
    parent = world.facts["parent"]
    if child.memes.get("reach", 0.0) < THRESHOLD:
        return out
    sig = ("worry", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    parent.memes["worry"] += 1
    out.append(_say_nursery(
        f"{parent.id} saw the tiny hand reach near {chem.phrase}, and said, “Oh, no, no, no.”"
    ))
    out.append(_say_nursery(
        f"“That {chem.label} can sting or spill, so keep your fingers far below.”"
    ))
    return out


def _rule_resist(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts["child"]
    if child.memes.get("worry", 0.0) < THRESHOLD:
        return out
    sig = ("resist", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["resist"] += 1
    child.memes["curiosity"] = max(0.0, child.memes.get("curiosity", 0.0) - 0.25)
    out.append(_say_nursery(
        f"The little heart went thump-thump-thump, yet paused to think."
    ))
    out.append(_say_nursery(
        f"“If I do not touch it now, I will stay safe in the blink,”"
    ))
    return out


CAUSAL_RULES = [_rule_curiosity, _rule_worry, _rule_resist]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(chemical: Chemical, safety: Safety) -> bool:
    return chemical.can_open and chemical.reason in safety.protects


def predict_risk(world: World, child: Entity, chemical: Chemical) -> dict:
    sim = world.copy()
    sim_child = sim.get(child.id)
    sim_child.memes["curiosity"] += 1
    sim_child.memes["reach"] += 1
    propagate(sim, narrate=False)
    return {
        "curious": sim_child.memes.get("curiosity", 0.0) >= THRESHOLD,
        "worry": sim.get(world.facts["parent"].id).memes.get("worry", 0.0) >= THRESHOLD,
        "resisted": sim_child.memes.get("resist", 0.0) >= THRESHOLD,
        "risk": chemical.risk,
    }


def tell(world: World, setting: Setting, child: Entity, parent: Entity, chemical: Chemical,
         safety: Safety) -> World:
    world.facts.update(child=child, parent=parent, chemical=chemical, safety=safety)

    world.say(_say_nursery(
        f"In the elevator bright and small, {child.id} went up and down the hall."
    ))
    world.say(_say_nursery(
        f"{child.id} wore a curious look and noticed {chemical.phrase} with a shiny little hook."
    ))
    child.memes["curiosity"] += 1
    child.memes["reach"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(_say_nursery(
        f"{child.id} thought in a whisper, a private little tune,"
    ))
    world.say(_say_nursery(
        f"“I wonder if it smells like rain, or bubbles, or a moon.”"
    ))
    world.say(_say_nursery(
        f"But then {parent.id} leaned close and gave a gentle, steady view."
    ))
    world.say(_say_nursery(
        f"“That {chemical.label} is for grown-up work, and not for hands like you.”"
    ))
    parent.memes["worry"] += 1
    child.memes["worry"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(_say_nursery(
        f"{child.id} held still and listened, with the elevator going ding."
    ))
    world.say(_say_nursery(
        f"Inside the little inner voice, the safest thought took wing:"
    ))
    world.say(_say_nursery(
        f"“I can be curious and careful too; I do not have to touch that thing.”"
    ))
    child.memes["pride"] += 1
    child.memes["self_control"] += 1

    world.para()
    world.say(_say_nursery(
        f"So {child.id} kept both hands close, and waited with a grin."
    ))
    world.say(_say_nursery(
        f"The ride went to the proper floor, and the safe choice won within."
    ))
    world.say(_say_nursery(
        f"Down the doors slid open wide; the little day was sweet again."
    ))

    world.facts["resolved"] = True
    world.facts["inner_monologue"] = True
    return world


SETTINGS = {
    "elevator": Setting(place="the elevator", indoor=True, affords={"ride"}),
}

CHEMICALS = {
    "cleaner": Chemical(
        id="cleaner",
        label="blue cleaner",
        phrase="a blue cleaner bottle",
        smell="sharp",
        color="blue",
        risk="sting",
        reason="sting",
        can_touch=False,
        can_open=False,
    ),
    "soap": Chemical(
        id="soap",
        label="bubble soap",
        phrase="a bottle of bubble soap",
        smell="sweet",
        color="green",
        risk="slip",
        reason="slip",
        can_touch=False,
        can_open=False,
    ),
    "polish": Chemical(
        id="polish",
        label="silver polish",
        phrase="a silver polish tin",
        smell="strong",
        color="silver",
        risk="burn",
        reason="burn",
        can_touch=False,
        can_open=False,
    ),
}

SAFETIES = {
    "hands-off": Safety(
        id="hands-off",
        label="two hands tucked in pockets",
        phrase="keep your hands tucked in pockets",
        action="wait",
        protects={"sting", "slip", "burn"},
        payoff="the child can look without touching",
    ),
    "hold-hands": Safety(
        id="hold-hands",
        label="a warm hand to hold",
        phrase="hold hands and wait together",
        action="hold",
        protects={"sting", "slip", "burn"},
        payoff="the child can stay calm while the ride moves on",
    ),
}

NAMES_GIRL = ["Mia", "Nora", "Lily", "Ava", "Zoe"]
NAMES_BOY = ["Leo", "Finn", "Ben", "Theo", "Max"]
TRAITS = ["curious", "gentle", "small", "bright", "bouncy"]


@dataclass
class StoryParams:
    place: str
    chemical: str
    safety: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="elevator", chemical="cleaner", safety="hold-hands", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="elevator", chemical="soap", safety="hands-off", name="Leo", gender="boy", parent="father", trait="bright"),
    StoryParams(place="elevator", chemical="polish", safety="hold-hands", name="Nora", gender="girl", parent="mother", trait="gentle"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for chem_id, chem in CHEMICALS.items():
            for safety_id, safety in SAFETIES.items():
                if reasonableness_gate(chem, safety):
                    combos.append((place, chem_id, safety_id))
    return combos


def explain_rejection(chemical: Chemical, safety: Safety) -> str:
    return (
        f"(No story: {chemical.label} does not fit the safety choice "
        f"'{safety.label}'. The fix must actually protect against {chemical.risk}.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a curious child in an elevator, a chemical, and a nursery-rhyme inner monologue."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--chemical", choices=CHEMICALS)
    ap.add_argument("--safety", choices=SAFETIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.chemical and args.safety:
        chem = CHEMICALS[args.chemical]
        safety = SAFETIES[args.safety]
        if not reasonableness_gate(chem, safety):
            raise StoryError(explain_rejection(chem, safety))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.chemical is None or c[1] == args.chemical)
              and (args.safety is None or c[2] == args.safety)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, chemical, safety = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, chemical=chemical, safety=safety, name=name, gender=gender, parent=parent, trait=trait)


def _child_pronoun(gender: str) -> str:
    return "she" if gender == "girl" else "he"


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=["little", params.trait],
        meters={"curiosity": 0.0, "reach": 0.0},
        memes={"curiosity": 0.0, "worry": 0.0, "resist": 0.0, "pride": 0.0, "self_control": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        meters={"alert": 0.0},
        memes={"worry": 0.0},
    ))
    chemical = CHEMICALS[params.chemical]
    safety = SAFETIES[params.safety]

    if not reasonableness_gate(chemical, safety):
        raise StoryError(explain_rejection(chemical, safety))

    tell(world, SETTINGS[params.place], child, parent, chemical, safety)

    prompts = [
        f'Write a short nursery-rhyme story about a child named {params.name} in an elevator who notices "{chemical.label}".',
        f"Tell a gentle story where a {params.gender} named {params.name} feels curious about a chemical and chooses a safe way to ride.",
        f'Write a child-friendly story that includes an inner monologue about "{chemical.phrase}" and ends with careful hands.',
    ]

    story_qa = [
        QAItem(
            question=f"Where does {params.name} notice the {chemical.label}?",
            answer=f"{params.name} notices it in the elevator during the ride.",
        ),
        QAItem(
            question=f"What does {params.name} want to do because of curiosity?",
            answer=f"{params.name} wants to look closely and reach toward the {chemical.label}, but then chooses not to touch it.",
        ),
        QAItem(
            question=f"What did {params.name}'s {params.parent} warn about?",
            answer=f"{params.name}'s {params.parent} warned that the {chemical.label} could sting, spill, or cause trouble if touched.",
        ),
        QAItem(
            question=f"How did the inner voice help {params.name}?",
            answer=f"The inner voice helped {params.name} pause, think, and decide that being curious did not mean touching the chemical.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The elevator reached the right floor safely, and {params.name} felt proud of keeping hands to self.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is an elevator?",
            answer="An elevator is a moving box that carries people up and down in a building.",
        ),
        QAItem(
            question="Why should a child be careful around a chemical bottle?",
            answer="A chemical bottle can hold a strong liquid or powder that may sting, spill, or make a mess, so it is safer to leave it alone.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn about something new.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet talk inside your own head that helps you think things through.",
        ),
    ]

    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- world trace ---")
        for line in sample.world.trace_log:
            print(line)
        print("--- state ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            print(f"{e.id}: {e.type} {' '.join(bits)}")
    if qa:
        print()
        print("== (1) Generation prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== (2) Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== (3) World-knowledge questions ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


ASP_RULES = r"""
chemical(C) :- chemical_fact(C).
safe_choice(S) :- safety_fact(S).

reasonably_compatible(C, S) :- chemical_fact(C), safety_fact(S), protects(S, R), risk_of(C, R).
valid(place, C, S) :- place_fact(place), chemical_fact(C), safety_fact(S), reasonably_compatible(C, S).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place_fact", pid))
    for cid, chem in CHEMICALS.items():
        lines.append(asp.fact("chemical_fact", cid))
        lines.append(asp.fact("risk_of", cid, chem.risk))
    for sid, safe in SAFETIES.items():
        lines.append(asp.fact("safety_fact", sid))
        for risk in sorted(safe.protects):
            lines.append(asp.fact("protects", sid, risk))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
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


def _asp_text() -> str:
    return asp_program("#show valid/3.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(_asp_text())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, chemical, safety) combos:\n")
        for place, chem, safety in combos:
            print(f"  {place:8} {chem:10} {safety}")
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
            header = f"### {p.name}: {p.chemical} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
