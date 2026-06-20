#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/proposal_safety_twist_problem_solving_fairy_tale.py
====================================================================================

A standalone storyworld for a small fairy-tale domain about a proposal, a safety
concern, a twist, and a problem-solving ending.

Premise
-------
A young prince or princess wants to make a proposal in a fairy-tale garden.
The plan seems sweet, but the setting has a safety problem: a rickety bridge,
a slippery pond path, or a wobbly lantern can make the proposal scene unsafe.
A careful helper spots the danger, the story takes a twist, and the characters
solve the problem by changing the place or using a safer object.

The story is designed to be complete and state-driven:
- begin with the proposal setup,
- introduce a concrete safety problem,
- twist the plan through a practical fix,
- finish with a clear, safe image proving what changed.

Contract notes
--------------
- stdlib only
- imports storyworlds/results.py eagerly
- provides StoryParams, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, --show-asp
- includes Python reasonableness gate and inline ASP twin
- --verify checks ASP parity and exercises a normal generation smoke test
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

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "princess", "mother", "woman"}
        male = {"boy", "king", "prince", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"queen": "queen", "king": "king", "princess": "princess", "prince": "prince"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass(frozen=True)
class Place:
    id: str
    scene: str
    risky_thing: str
    problem: str
    safe_place: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class ProposalPlan:
    id: str
    act: str
    setting_line: str
    romantic_line: str
    finish_line: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class SafetyConcern:
    id: str
    danger: str
    risk_line: str
    warning_line: str
    fix_line: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Twist:
    id: str
    reveal: str
    turn_line: str
    solve_line: str
    ending_line: str
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
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["worry"] < THRESHOLD:
            continue
        sig = ("worry", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append("__worry__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["relief"] < THRESHOLD:
            continue
        sig = ("relief", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("relief", _r_relief)]


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


def risky(place: Place, concern: SafetyConcern) -> bool:
    return concern.id in place.tags


def sensible_fix(place: Place, concern: SafetyConcern, twist: Twist) -> bool:
    return concern.id in place.tags and twist.id in TWISTS and place.id in PLACES


def safe_choice(place: Place, concern: SafetyConcern, twist: Twist) -> bool:
    return risky(place, concern) and concern.id not in {"fire", "cliff"} and twist.id in TWISTS


def predict_problem(world: World, place: Place, concern: SafetyConcern) -> dict:
    sim = world.copy()
    _do_risky_scene(sim, place, concern, narrate=False)
    return {"worry": sim.get("hero").memes["worry"], "danger": sim.get("hero").meters["danger"]}


def _do_risky_scene(world: World, place: Place, concern: SafetyConcern, narrate: bool = True) -> None:
    hero = world.get("hero")
    hero.meters["danger"] += 1
    hero.memes["worry"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, hero: Entity, helper: Entity, place: Place, plan: ProposalPlan) -> None:
    hero.memes["hope"] += 1
    helper.memes["kindness"] += 1
    world.say(
        f"On a golden evening, {hero.id} and {helper.id} wandered to {place.scene}. "
        f"{plan.setting_line}"
    )
    world.say(
        f"{hero.id} whispered a proposal with a dreamy smile. {plan.romantic_line}"
    )


def safety_warning(world: World, helper: Entity, place: Place, concern: SafetyConcern) -> None:
    pred = predict_problem(world, place, concern)
    helper.memes["care"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f"But {place.problem}. {helper.id} pointed at the danger and said, "
        f'"{concern.warning_line}"'
    )


def twist_beats(world: World, twist: Twist, hero: Entity, helper: Entity) -> None:
    hero.memes["surprise"] += 1
    helper.memes["surprise"] += 1
    world.say(f"Then came a twist: {twist.reveal}")
    world.say(twist.turn_line)


def solve(world: World, place: Place, concern: SafetyConcern, twist: Twist, plan: ProposalPlan) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{twist.solve_line} {concern.fix_line}"
    )
    world.say(
        f"At last, {plan.finish_line} {twist.ending_line}"
    )


def tell(place: Place, plan: ProposalPlan, concern: SafetyConcern, twist: Twist,
         hero_name: str = "Luna", hero_gender: str = "girl",
         helper_name: str = "Milo", helper_gender: str = "boy") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    world.add(Entity(id="herb", type="thing", label=place.risky_thing))

    setup(world, hero, helper, place, plan)
    world.para()
    safety_warning(world, helper, place, concern)
    twist_beats(world, twist, hero, helper)
    world.para()
    _do_risky_scene(world, place, concern, narrate=False)
    solve(world, place, concern, twist, plan)

    world.facts.update(
        hero=hero,
        helper=helper,
        place=place,
        plan=plan,
        concern=concern,
        twist=twist,
        outcome="safe",
        danger=hero.meters["danger"],
        worry=hero.memes["worry"],
    )
    return world


PLACES = {
    "bridge": Place("bridge", "a moonlit bridge over the garden pond", "bridge", "The bridge boards looked loose and the rail wobbled.", "the rose arbor", tags={"bridge"}),
    "pond": Place("pond", "the lily pond by the willow tree", "water", "The stepping stones were slick with moss.", "the dry path under the lanterns", tags={"water"}),
    "tower": Place("tower", "the ivy tower beside the castle gate", "stairs", "The spiral stairs were steep and a little dark.", "the sunny courtyard", tags={"stairs"}),
}

PLANS = {
    "proposal": ProposalPlan(
        "proposal",
        "make a proposal",
        "They had brought a ribbon, a little ring of silver leaves, and a basket of berries.",
        "The plan was to ask a very important question under the stars.",
        "Their hearts felt brave and happy, as if the whole garden had been holding its breath.",
        tags={"proposal"},
    ),
    "promise": ProposalPlan(
        "promise",
        "make a promise",
        "They carried a tiny lantern, a song, and two velvet cushions.",
        "The plan was to ask for a forever promise in a soft and gentle voice.",
        "The night seemed ready for a sweet little vow.",
        tags={"proposal"},
    ),
}

CONCERNS = {
    "bridge": SafetyConcern(
        "bridge",
        "bridge",
        "The bridge boards looked loose and the rail wobbled.",
        "That bridge is not safe for a careful pause.",
        "So they moved slowly and stayed on the wider stones instead.",
        tags={"bridge"},
    ),
    "water": SafetyConcern(
        "water",
        "water",
        "The stones were slick and the edge of the pond was slippery.",
        "The pond path is too slippery for fancy steps.",
        "So they chose a dry path with steady feet and no splashing.",
        tags={"water"},
    ),
    "stairs": SafetyConcern(
        "stairs",
        "stairs",
        "The spiral stairs were steep and a little dark.",
        "Those stairs are not safe for carrying berries and lanterns together.",
        "So they used the courtyard steps where the ground was flat and bright.",
        tags={"stairs"},
    ),
}

TWISTS = {
    "owl": Twist(
        "owl",
        "a tiny owl dropped a silver feather right at their feet",
        "The feather was shaped like a little arrow pointing to the safe path.",
        "They followed the feather to a safer place for the question.",
        "The owl blinked once as if it had planned the whole thing.",
        tags={"owl"},
    ),
    "moss": Twist(
        "moss",
        "the moss on the stones spelled out a safer way in a soft green curve",
        "The green curve showed how to reach the dry path without slipping.",
        "They took the hint, and the problem became easy to solve.",
        "The moss looked like a shy little guide beneath their shoes.",
        tags={"moss"},
    ),
    "bell": Twist(
        "bell",
        "a bell in the tower rang and revealed a brighter place nearby",
        "The ringing showed them where the courtyard stayed safest and warmest.",
        "They changed course at once, and the proposal stayed sweet.",
        "The bell's echo made the ending feel festive instead of fearful.",
        tags={"bell"},
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for cid, concern in CONCERNS.items():
            if risky(place, concern):
                for plid in PLANS:
                    combos.append((pid, cid, plid))
    return combos


@dataclass
@dataclass
class StoryParams:
    place: str
    concern: str
    plan: str
    twist: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld about a proposal, safety, a twist, and problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--concern", choices=CONCERNS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
              if (args.place is None or c[0] == args.place)
              and (args.concern is None or c[1] == args.concern)
              and (args.plan is None or c[2] == args.plan)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, concern, plan = rng.choice(sorted(combos))
    twist = args.twist or rng.choice(sorted(TWISTS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(["Luna", "Ari", "Mira", "Elio", "Nia", "Tamsin"])
    helper_name = args.helper_name or rng.choice(["Milo", "Finn", "Oren", "Pippa", "Cedar", "Rowan"])
    return StoryParams(place, concern, plan, twist, hero_name, hero_gender, helper_name, helper_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story for a small child that includes the words "proposal" and "safety".',
        f"Tell a gentle story where {f['hero'].id} wants a proposal in {f['place'].scene}, but a safety problem appears and a twist helps them solve it.",
        f"Write a story with a sweet proposal, a real safety concern, and a clever twist that leads to a safe ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    place = f["place"]
    concern = f["concern"]
    twist = f["twist"]
    return [
        QAItem(
            question="What did the hero want to do?",
            answer=f"{hero.id} wanted to make a proposal, and the whole plan felt tender and important. The fairy-tale setting made it feel like a big moment."
        ),
        QAItem(
            question="What safety problem did they notice?",
            answer=f"They noticed that {place.problem.lower()} That meant the scene was not safe in the first place. The problem mattered because it could spoil the proposal and make someone stumble."
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"{helper.id} helped them use {twist.id} to find a safer spot, and they moved to {place.safe_place}. That kept the proposal sweet while protecting everyone."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does safety mean in this story?",
            answer="Safety means choosing the place and path that will not hurt anyone. It also means slowing down and solving the problem before the important moment."
        ),
        QAItem(
            question="What is a proposal?",
            answer="A proposal is a special ask, like when someone wants to begin a promise or a big new step. In fairy tales, it is often done with gentle words and a hopeful heart."
        ),
        QAItem(
            question="What is a twist?",
            answer="A twist is a surprising new clue or change that turns the story in a new direction. Here, the twist helps the characters solve the problem instead of giving up."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def tell_story(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        PLANS[params.plan],
        CONCERNS[params.concern],
        TWISTS[params.twist],
        params.hero_name,
        params.hero_gender,
        params.helper_name,
        params.helper_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return tell_story(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
risk(P,C) :- place(P), concern(C), place_tags(P,C).
safe_fix(P,C,T) :- risk(P,C), twist(T), twist_help(T), place(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for tag in sorted(p.tags):
            lines.append(asp.fact("place_tags", pid, tag))
    for cid, c in CONCERNS.items():
        lines.append(asp.fact("concern", cid))
        lines.append(asp.fact("concern_tag", cid, c.id))
    for tid, t in TWISTS.items():
        lines.append(asp.fact("twist", tid))
        lines.append(asp.fact("twist_help", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show risk/2."))
    return sorted(set(asp.atoms(model, "risk")))


def asp_verify() -> int:
    import asp
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH in risk gate:")
        print("  only in python:", sorted(py - cl))
        print("  only in clingo:", sorted(cl - py))
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print(f"OK: gate matches and generation works ({len(py)} combos).")
    return rc


def explain_rejection(place: Place, concern: SafetyConcern) -> str:
    if not risky(place, concern):
        return "(No story: this place does not create a real safety problem for this concern.)"
    return "(No story: that combination is not reasonable for this fairy-tale problem-solving story.)"


def valid_choice(twist: Twist) -> bool:
    return twist.id in TWISTS


def resolve_explicit(args: argparse.Namespace) -> None:
    pass


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show risk/2.\n#show safe_fix/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("risk combos:")
        for item in asp_valid_combos():
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("bridge", "bridge", "proposal", "owl", "Luna", "girl", "Milo", "boy"),
            StoryParams("pond", "water", "promise", "moss", "Mira", "girl", "Rowan", "boy"),
            StoryParams("tower", "stairs", "proposal", "bell", "Ari", "boy", "Pippa", "girl"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.hero_name}: {p.plan} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
