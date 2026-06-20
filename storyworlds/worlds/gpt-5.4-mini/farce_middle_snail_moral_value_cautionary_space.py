#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/farce_middle_snail_moral_value_cautionary_space.py
===================================================================================

A small standalone storyworld for a space-adventure cautionary tale:
a playful middle-of-mission farce involving a snail, a moral choice about
care, and a gentle warning that rushing can cause trouble in space.

The world is intentionally tiny:
- two children on a spaceship or moon base
- one cautious helper
- one tiny snail-like creature in a habitat
- one risky shortcut and one careful repair
- a middle beat where the mistake becomes clear
- a moral ending image that proves what changed

It supports the shared Storyweavers CLI contract:
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify,
  and --show-asp
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
CAREFUL_TRAITS = {"careful", "cautious", "thoughtful", "patient"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)
    small: bool = False
    fragile: bool = False
    snaily: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    id: str
    place: str
    view: str
    mission: str
    backdrop: str


@dataclass
class Snail:
    id: str
    label: str
    trail: str
    shell_sound: str
    care_need: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Risk:
    id: str
    label: str
    phrase: str
    warning: str
    damage: str
    risk_score: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    power: int
    kindness: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.setting)
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


def _r_scatter(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["mess"] < THRESHOLD:
            continue
        sig = ("scatter", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["embarrassment"] += 1
        out.append("__scatter__")
    return out


def _r_warn(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("risk_seen") and not world.facts.get("care_done"):
        sig = ("warn", "middle")
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("__warn__")
    return out


CAUSAL_RULES = [Rule("scatter", "social", _r_scatter), Rule("warn", "social", _r_warn)]


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


def risky_action(risk: Risk, snail: Snail) -> bool:
    return risk.risk_score >= 2 and snail.id in {"snail", "trail_snail"}


def choose_remedy(remedy: Remedy, risk: Risk) -> bool:
    return remedy.power >= risk.risk_score


def predict_farce(world: World, risk: Risk) -> dict:
    sim = world.copy()
    sim.get("crew").meters["mess"] += 1
    propagate(sim, narrate=False)
    return {
        "mess": sim.get("crew").meters["mess"] >= THRESHOLD,
        "awkward": sim.get("crew").memes["embarrassment"] >= THRESHOLD,
    }


def setup(world: World, kid1: Entity, kid2: Entity) -> None:
    kid1.memes["joy"] += 1
    kid2.memes["joy"] += 1
    world.say(
        f"On the spaceship {world.setting.place}, {kid1.id} and {kid2.id} were on a "
        f"small mission. {world.setting.backdrop}"
    )
    world.say(
        f'They wanted to finish {world.setting.mission} before the next signal blinked.'
    )


def introduce_snail(world: World, snail: Snail) -> None:
    world.say(
        f"In the middle of the bay, a tiny snail had left a shiny trail near the control mat. "
        f'Its shell made a little "{snail.shell_sound}" whenever it turned.'
    )


def farce_turn(world: World, kid1: Entity, kid2: Entity, snail: Snail, risk: Risk) -> None:
    kid1.memes["bravado"] += 1
    world.say(
        f'{kid1.id} laughed. "This is a farce," {kid1.pronoun()} said, and tried to '
        f'push the {snail.label} aside with a quick swipe.'
    )
    world.say(
        f'{kid2.id} frowned. "{risk.warning}," {kid2.pronoun()} warned. "It can make the floor slick."'
    )
    world.facts["risk_seen"] = True


def middle_mess(world: World, kid1: Entity, kid2: Entity, snail: Snail, risk: Risk) -> None:
    kid1.meters["mess"] += 1
    kid2.meters["mess"] += 1
    kid1.memes["surprise"] += 1
    kid2.memes["surprise"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The swipe backfired at the middle of the mission. The {risk.label} slid, the "
        f"{snail.label} twirled in a silly circle, and the whole bay became a clumsy little "
        f"farce."
    )
    world.say(
        f"{kid1.id} gasped. {kid2.id} pointed at the shining trail and said, "
        f'"Now it is really a slippery problem."'
    )


def moral_choice(world: World, helper: Entity, risk: Risk, remedy: Remedy) -> None:
    if choose_remedy(remedy, risk):
        world.facts["care_done"] = True
        helper.memes["kindness"] += 1
        world.say(
            f"{helper.id} came over calmly. {helper.pronoun().capitalize()} used {remedy.phrase} "
            f"and carefully wiped the floor until it was safe again."
        )
    else:
        raise StoryError("The chosen remedy is not strong enough for this space mishap.")


def closing(world: World, kid1: Entity, kid2: Entity, snail: Snail) -> None:
    for kid in (kid1, kid2):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
    world.say(
        f'After that, {kid1.id} and {kid2.id} slowed down and watched the snail instead of '
        f'rushing it. They learned that a kind choice keeps a mission on course.'
    )
    world.say(
        f"At the end, the snail rested on a clean little leaf, its trail safe in the corner, "
        f"and the spaceship looked tidy and bright again."
    )


def tell(setting: Setting, snail: Snail, risk: Risk, remedy: Remedy,
         kid1_name: str = "Mina", kid1_type: str = "girl",
         kid2_name: str = "Jai", kid2_type: str = "boy",
         helper_name: str = "Captain Noor", helper_type: str = "captain") -> World:
    world = World(setting)
    kid1 = world.add(Entity(id=kid1_name, kind="character", type=kid1_type, role="instigator"))
    kid2 = world.add(Entity(id=kid2_name, kind="character", type=kid2_type, role="cautioner"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    world.add(Entity(id="crew", kind="thing", type="room", label="the bay"))

    setup(world, kid1, kid2)
    world.para()
    introduce_snail(world, snail)
    farce_turn(world, kid1, kid2, snail, risk)
    middle_mess(world, kid1, kid2, snail, risk)
    world.para()
    moral_choice(world, helper, risk, remedy)
    closing(world, kid1, kid2, snail)

    outcome = "kind_fix"
    world.facts.update(
        kid1=kid1, kid2=kid2, helper=helper, snail=snail, risk=risk, remedy=remedy,
        setting=setting, outcome=outcome
    )
    return world


SETTINGS = {
    "orbit": Setting(
        "orbit",
        "the orbital bay",
        "a porthole view of stars",
        "the next calibration check",
        "The hallway hummed softly, and the star map glowed blue above the console.",
    ),
    "moonbase": Setting(
        "moonbase",
        "the moonbase lab",
        "a bright dust-free corridor",
        "the sample sorting task",
        "The white floor shone under the dome, and the air smelled like metal and tea.",
    ),
    "freighter": Setting(
        "freighter",
        "the cargo deck",
        "a row of stacked crates and blinking buttons",
        "the crate count",
        "The ship rocked a little, making every box feel like part of an adventure.",
    ),
}

SNAILS = {
    "snail": Snail("snail", "snail", "a silver trail", "shhrrip", "a gentle shell"),
    "trail_snail": Snail("trail_snail", "little snail", "a glossy trail", "click-clack", "a gentle shell"),
}

RISKS = {
    "slip": Risk("slip", "slippery patch", "be careful with the floor", "the floor can get slick", "a slide",
                 2, {"slip", "caution"}),
    "jam": Risk("jam", "snail trail", "watch the controls", "the trail can make a control pad tricky", "a jam",
                3, {"snail", "caution"}),
}

REMEDIES = {
    "towel": Remedy("towel", "a towel", "wipe it up with a towel", 3, "kind", {"towel", "care"}),
    "brush": Remedy("brush", "a soft brush", "gently brush it away", 2, "gentle", {"brush", "care"}),
}

KID_NAMES = ["Mina", "Jai", "Luna", "Kito", "Suri", "Nova", "Rex", "Ivy"]
TRAITS = ["careful", "curious", "thoughtful", "patient"]


@dataclass
class StoryParams:
    setting: str
    snail: str
    risk: str
    remedy: str
    kid1: str
    kid1_type: str
    kid2: str
    kid2_type: str
    helper: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for rid in RISKS:
            for mid in REMEDIES:
                combos.append((sid, rid, mid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure cautionary farce storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--snail", choices=SNAILS)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
    ap.add_argument("--name2")
    ap.add_argument("--helper")
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
              and (args.risk is None or c[1] == args.risk)
              and (args.remedy is None or c[2] == args.remedy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, risk, remedy = rng.choice(combos)
    kid1 = args.name or rng.choice(KID_NAMES)
    kid2 = args.name2 or rng.choice([n for n in KID_NAMES if n != kid1])
    helper = args.helper or rng.choice(["Captain Noor", "Engineer Tali", "Pilot Sera"])
    return StoryParams(
        setting=setting, snail=args.snail or rng.choice(list(SNAILS)),
        risk=risk, remedy=remedy,
        kid1=kid1, kid1_type="girl", kid2=kid2, kid2_type="boy",
        helper=helper, helper_type="captain", trait=rng.choice(TRAITS)
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space adventure farce for a child that includes the word "farce" and a snail.',
        f"Tell a cautionary story about {f['kid1'].id} and {f['kid2'].id} on {f['setting'].place}, where a snail trail causes trouble in the middle of the mission.",
        f"Write a moral-value story where a careful helper fixes a messy space mistake and the children learn to slow down.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid1, kid2, helper, risk = f["kid1"], f["kid2"], f["helper"], f["risk"]
    return [
        ("Who is the story about?",
         f"It is about {kid1.id}, {kid2.id}, and {helper.id} on a small space mission. The snail trouble happens around them in the middle of the story."),
        ("What went wrong?",
         f"{kid1.id} rushed at the {risk.label}, and that made the bay messy and slippery. The story turns into a farce right in the middle, before the careful fix."),
        ("How did the story end?",
         f"{helper.id} cleaned the mess and the children learned to slow down and be kind. The ending shows the mission safe again, with the snail resting quietly.")
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a snail?",
         "A snail is a small animal with a soft body and a shell. It moves slowly and can leave a shiny trail behind it."),
        ("What does cautious mean?",
         "Cautious means careful. A cautious person thinks first so they can avoid trouble."),
        ("Why is a slippery floor dangerous?",
         "A slippery floor can make someone fall or spill something. In a spaceship, that can also make tools and controls hard to use."),
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
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("orbit", "snail", "slip", "towel", "Mina", "girl", "Jai", "boy", "Captain Noor", "captain", "careful"),
    StoryParams("moonbase", "trail_snail", "jam", "brush", "Luna", "girl", "Rex", "boy", "Engineer Tali", "captain", "patient"),
]


def explain_rejection(risk: Risk, remedy: Remedy) -> str:
    return f"(No story: the remedy {remedy.label} is not enough for this cautionary space problem.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid in SNAILS:
        lines.append(asp.fact("snail", sid))
    for rid, r in RISKS.items():
        lines.append(asp.fact("risk", rid))
        lines.append(asp.fact("risk_score", rid, r.risk_score))
    for mid, m in REMEDIES.items():
        lines.append(asp.fact("remedy", mid))
        lines.append(asp.fact("power", mid, m.power))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,R,M) :- setting(S), risk(R), remedy(M).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import sys as _sys
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, snail=None, risk=None, remedy=None, name=None, name2=None, helper=None), random.Random(7)))
        _ = sample.story
    except Exception as e:
        print(f"MISMATCH: normal generation failed: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting], SNAILS[params.snail], RISKS[params.risk], REMEDIES[params.remedy],
        params.kid1, params.kid1_type, params.kid2, params.kid2_type,
        params.helper, params.helper_type
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible space combinations.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
