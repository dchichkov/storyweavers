#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/nip_year_flax_misunderstanding_rhyming_story.py
==============================================================================

A small standalone storyworld for a rhyming misunderstanding tale.

Premise:
- A child and a grown-up are weaving with flax.
- A tiny "nip" can mean a small bite of thread, a small pinch, or a little
  snake nip in the child's mistaken mind.
- A "year" matters because a seasonal fair is coming at year's end.
- The misunderstanding makes the child worry that the flax is hurt or that
  something has gone wrong, but the grown-up explains the harmless meaning.
- The ending proves the world changed: the flax is tied, the fear is gone, and
  the rhyme resolves in a bright final image.

This script follows the Storyweavers contract:
- stdlib only
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily inside ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports --verify, --asp, --show-asp, --qa, --json, --trace, -n, --all, --seed
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Scenario:
    id: str
    place: str
    weave_word: str
    rhyme_word: str
    setting_line: str
    dark_line: str


@dataclass
class Misunderstanding:
    id: str
    wrong_thought: str
    worry_line: str
    explanation: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Material:
    id: str
    label: str
    phrase: str
    fragile: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    sense: int
    power: int
    action_line: str
    outcome_line: str
    lesson_line: str
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_nip_fear(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child or child.meters["noticed_nip"] < THRESHOLD:
        return out
    sig = ("nip_fear",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += 1
    out.append("__fear__")
    return out


def _r_reassure(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    adult = world.entities.get("adult")
    if not child or not adult:
        return out
    if child.memes["fear"] < THRESHOLD or adult.memes["calm"] < THRESHOLD:
        return out
    sig = ("reassure",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["trust"] += 1
    adult.memes["warmth"] += 1
    out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("nip_fear", _r_nip_fear), Rule("reassure", _r_reassure)]


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


def safe_choices() -> list[Fix]:
    return [fix for fix in FIXES.values() if fix.sense >= SENSE_MIN]


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: f.sense)


def is_reasonable(scn: Scenario, mis: Misunderstanding, mat: Material, fix: Fix) -> bool:
    return bool(scn and mis and mat and fix and mat.fragile and fix.sense >= SENSE_MIN)


def predict_world(world: World) -> dict:
    sim = world.copy()
    simulate_misunderstanding(sim, narrate=False)
    return {
        "fear": sim.get("child").memes["fear"],
        "trust": sim.get("child").memes["trust"],
        "ruptured": sim.get("flax").meters["ruptured"] >= THRESHOLD,
    }


def simulate_misunderstanding(world: World, narrate: bool = True) -> None:
    child = world.get("child")
    flax = world.get("flax")
    child.meters["noticed_nip"] += 1
    flax.meters["touched"] += 1
    child.memes["confused"] += 1
    propagate(world, narrate=narrate)
    if narrate:
        world.say(
            f"{child.id} saw a little nip in the flax and thought it meant a hurtful bite."
        )
    flax.meters["knotted"] += 1
    flax.meters["ruffled"] += 1


def tell_setting(world: World, scenario: Scenario, child: Entity, adult: Entity, mat: Entity) -> None:
    child.memes["joy"] += 1
    world.say(
        f"In a bright small room by the window, {child.id} and {adult.label_word} "
        f"sat to work with {mat.label}."
    )
    world.say(scenario.setting_line)
    world.say(
        f"{child.id} smiled at the soft gold thread and hummed a little tune to see it through the day."
    )


def raise_question(world: World, child: Entity, mis: Misunderstanding, mat: Entity) -> None:
    child.memes["worry"] += 1
    world.say(
        f"But then {child.id} saw a {mis.wrong_thought} in the {mat.label}."
    )
    world.say(mis.worry_line)


def explain(world: World, adult: Entity, child: Entity, mis: Misunderstanding, mat: Entity) -> None:
    child.memes["fear"] = 0.0
    child.memes["trust"] += 1
    adult.memes["kindness"] += 1
    world.say(
        f"{adult.label_word.capitalize()} laughed softly and leaned near. "
        f'"{mis.explanation}," {adult.label_word} said. '
        f'"A nip can be tiny and harmless, not a hurt at all."'
    )
    world.say(
        f"That small explanation made the worried cloud drift from {child.id}'s mind."
    )


def repair(world: World, adult: Entity, fix: Fix, child: Entity, mat: Entity, scenario: Scenario) -> None:
    child.memes["joy"] += 1
    child.memes["worry"] = 0.0
    world.say(f"{adult.label_word.capitalize()} {fix.action_line}.")
    world.say(fix.outcome_line)
    world.say(
        f"The flax went from a tangle to a tidy braid, and the room felt ready for the {scenario.id} fair year."
    )
    world.say(
        fix.lesson_line + f" {child.id} nodded, and the little knot became a neat, bright knot."
    )


def tell(world: World, scenario: Scenario, mis: Misunderstanding, mat_name: str,
         fix: Fix, child_name: str = "Nia", child_gender: str = "girl",
         adult_name: str = "Mama", adult_gender: str = "woman") -> World:
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="adult", label="the grown-up"))
    mat = world.add(Entity(id=mat_name, kind="thing", type="material", label=mat_name))
    child.memes["joy"] = 1.0
    adult.memes["calm"] = 1.0

    tell_setting(world, scenario, child, adult, mat)
    world.para()
    raise_question(world, child, mis, mat)
    simulate_misunderstanding(world)
    explain(world, adult, child, mis, mat)
    world.para()
    repair(world, adult, fix, child, mat, scenario)

    world.facts.update(
        child=child,
        adult=adult,
        mat=mat,
        scenario=scenario,
        misunderstanding=mis,
        fix=fix,
        outcome="resolved",
    )
    return world


SCENARIOS = {
    "winter": Scenario(
        id="winter",
        place="loom room",
        weave_word="weave",
        rhyme_word="glow",
        setting_line="The flax was laid out like sunlit rope, and the window made it glow.",
        dark_line="A shadow moved over the spool, but nothing in the room was wrong.",
    ),
    "market": Scenario(
        id="market",
        place="market stall",
        weave_word="spin",
        rhyme_word="drum",
        setting_line="At the market stall, the flax lay in soft piles beside bright ribbons.",
        dark_line="The busy sounds made the little pile look strange for a moment.",
    ),
    "summer": Scenario(
        id="summer",
        place="porch",
        weave_word="twine",
        rhyme_word="sing",
        setting_line="On the porch, the flax shone pale and yellow in the summer light.",
        dark_line="A breeze made the strands dance, and the child blinked in surprise.",
    ),
}

MISUNDERSTANDINGS = {
    "nip": Misunderstanding(
        id="nip",
        wrong_thought="tiny nip",
        worry_line="The child feared the flax had been bitten by a sneaky little critter.",
        explanation="It was only a tiny twist in the thread, a harmless nip in the flax",
        tags={"nip", "misunderstanding"},
    ),
    "year": Misunderstanding(
        id="year",
        wrong_thought="new year",
        worry_line="The child feared the yarn would wait a whole year and never be ready.",
        explanation="It was only the year mark on the calendar, not a delay in the flax",
        tags={"year", "misunderstanding"},
    ),
    "flax": Misunderstanding(
        id="flax",
        wrong_thought="flax flag",
        worry_line="The child feared the pale bundle had fallen apart and lost its shape.",
        explanation="It was only the flax leaning into a small curve, not a broken thing",
        tags={"flax", "misunderstanding"},
    ),
}

MATERIALS = {
    "flax": Material(id="flax", label="flax", phrase="a bundle of flax", fragile=True, tags={"flax"}),
}

FIXES = {
    "straighten": Fix(
        id="straighten",
        sense=3,
        power=3,
        action_line="pinched the end, straightened the flax, and tied the loose bit with a soft smile",
        outcome_line="The fibers settled into a tidy line and stopped looking worried.",
        lesson_line="The grown-up said a tiny nip is just a little place where the thread bends.",
        tags={"fix", "gentle"},
    ),
    "comb": Fix(
        id="comb",
        sense=3,
        power=3,
        action_line="took a small comb and gently smoothed the flax from end to end",
        outcome_line="The strands glided into order like lines in a happy rhyme.",
        lesson_line="The grown-up said careful hands can make a little mess into a neat song.",
        tags={"fix", "gentle"},
    ),
    "ribbon": Fix(
        id="ribbon",
        sense=2,
        power=2,
        action_line="tied a bright ribbon around the bundle so it would stay neat",
        outcome_line="The ribbon held fast, and the flax looked festive for the year-end fair.",
        lesson_line="The grown-up said the worry was only a misunderstanding, not a wound.",
        tags={"fix", "gentle"},
    ),
}

CURATED = [
    StoryParams(scenario="winter", misunderstanding="nip", material="flax", fix="straighten", child_name="Nia", child_gender="girl", adult_name="Mama", adult_gender="woman"),
    StoryParams(scenario="market", misunderstanding="year", material="flax", fix="comb", child_name="Milo", child_gender="boy", adult_name="Papa", adult_gender="man"),
    StoryParams(scenario="summer", misunderstanding="flax", material="flax", fix="ribbon", child_name="Lina", child_gender="girl", adult_name="Grandma", adult_gender="woman"),
]

GIRL_NAMES = ["Nia", "Lina", "Maya", "Zoe", "Ari", "Tia"]
BOY_NAMES = ["Milo", "Oren", "Jude", "Perry", "Theo", "Finn"]


@dataclass
class StoryParams:
    scenario: str
    misunderstanding: str
    material: str
    fix: str
    child_name: str
    child_gender: str
    adult_name: str
    adult_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sc in SCENARIOS:
        for mi in MISUNDERSTANDINGS:
            for mat in MATERIALS:
                for fx in FIXES:
                    combos.append((sc, mi, mat, fx))
    return combos


KNOWLEDGE = {
    "nip": [("What does nip mean?",
             "A nip can mean a tiny pinch or a small bite, but it can also mean a little bend or twist in something soft.")],
    "year": [("What is a year?",
              "A year is a long stretch of time with seasons in it. It is how people count from one birthday to the next.")],
    "flax": [("What is flax?",
              "Flax is a plant. People can use its fibers to make thread and cloth.")],
    "misunderstanding": [("What is a misunderstanding?",
                          "A misunderstanding happens when someone thinks a thing means one idea, but it really means something else.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    sc = f["scenario"]
    mis = f["misunderstanding"]
    return [
        f'Write a rhyming story for a young child that includes the words "{mis.id}", "year", and "flax".',
        f"Tell a gentle misunderstanding story in a {sc.place} where a child thinks a tiny {mis.wrong_thought} in flax means trouble, but a grown-up explains it kindly.",
        f'Write a short, musical story about flax and a misunderstanding, ending with a calm fix and a bright year-end image.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    mis = f["misunderstanding"]
    mat = f["mat"]
    sc = f["scenario"]
    fix = f["fix"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {adult.label_word}. They spend the story near the flax and work through a small misunderstanding."),
        ("What did the child think at first?",
         f"{child.id} thought the little {mis.wrong_thought} meant something was wrong with the flax. That worry came from seeing a small shape and reading it the wrong way."),
        ("What did the grown-up say?",
         f"{adult.label_word.capitalize()} explained that the nip was harmless and only a tiny twist in the {mat.label}. That calm answer changed the child's worry into understanding."),
        ("How did the story end?",
         f"It ended with the flax neatly fixed, the fear gone, and the room ready for the year-end fair. The last image is bright and tidy, not scared."),
    ]
    if fix.id:
        qa.append((
            "How was the flax made neat again?",
            f"{adult.label_word.capitalize()} used a gentle fix and made the flax smooth and tidy again. That kept the bundle safe and showed the child a kinder answer.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["misunderstanding"].tags) | set(f["mat"].tags) | {"misunderstanding"}
    out: list[tuple[str, str]] = []
    for key, items in KNOWLEDGE.items():
        if key in tags:
            out.extend(items)
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this world always needs a plausible misunderstanding, a flax bundle, and a gentle fix.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sc in SCENARIOS:
        lines.append(asp.fact("scenario", sc))
    for mi in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", mi))
    for mat in MATERIALS:
        lines.append(asp.fact("material", mat))
    for fx, fix in FIXES.items():
        lines.append(asp.fact("fix", fx))
        lines.append(asp.fact("sense", fx, fix.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,M,T,F) :- scenario(S), misunderstanding(M), material(T), fix(F).
sensible(F) :- fix(F), sense(F, X), sense_min(M), X >= M.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(v for (v,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP matches Python valid_combos().")
    else:
        rc = 1
        print("MISMATCH: ASP and Python valid_combos() differ.")
    if set(asp_sensible()) == {f.id for f in safe_choices()}:
        print("OK: ASP sensible fixes match Python gate.")
    else:
        rc = 1
        print("MISMATCH: ASP sensible fixes differ.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming misunderstanding storyworld about flax and a nip.")
    ap.add_argument("--scenario", choices=SCENARIOS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--adult-name")
    ap.add_argument("--adult-gender", choices=["woman", "man", "girl", "boy"])
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
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError("This fix is too weak for the world's common sense gate.")
    sc = args.scenario or rng.choice(sorted(SCENARIOS))
    mi = args.misunderstanding or rng.choice(sorted(MISUNDERSTANDINGS))
    mat = args.material or "flax"
    fx = args.fix or rng.choice(sorted(f.id for f in safe_choices()))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    adult_gender = args.adult_gender or rng.choice(["woman", "man"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    adult_name = args.adult_name or rng.choice(["Mama", "Papa", "Grandma", "Grandpa", "Auntie", "Uncle"])
    return StoryParams(
        scenario=sc,
        misunderstanding=mi,
        material=mat,
        fix=fx,
        child_name=child_name,
        child_gender=child_gender,
        adult_name=adult_name,
        adult_gender=adult_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.scenario not in SCENARIOS or params.misunderstanding not in MISUNDERSTANDINGS or params.material not in MATERIALS or params.fix not in FIXES:
        raise StoryError("Invalid StoryParams for this world.")
    world = World()
    story_world = tell(
        world,
        SCENARIOS[params.scenario],
        MISUNDERSTANDINGS[params.misunderstanding],
        params.material,
        FIXES[params.fix],
        child_name=params.child_name,
        child_gender=params.child_gender,
        adult_name=params.adult_name,
        adult_gender=params.adult_gender,
    )
    return StorySample(
        params=params,
        story=story_world.render(),
        prompts=generation_prompts(story_world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(story_world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(story_world)],
        world=story_world,
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
        print(asp_program("#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible())}")
        print(f"combos: {len(asp_valid_combos())}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
