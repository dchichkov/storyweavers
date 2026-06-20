#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/flyer_ply_galoshes_repetition_sharing_happy_ending.py
======================================================================================

A compact storyworld for a fable-like rainy-day tale built from the seed words
"flyer", "ply", and "galoshes". The world models a small village errand where a
pair of animals must deliver flyers along a muddy lane. One pair of galoshes can
help, but only if they share them and take repeated turns. The story turns on
repetition, sharing, and a happy ending.

The story is state-driven rather than frozen text: mud soaks the lane, the flyer
can be ruined by rain, the children feel worry, and the shared galoshes plus a
repeat-trip plan resolve the problem.
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    wears: str = ""
    shares_with: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "hen"}
        male = {"boy", "father", "man", "fox", "goat"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    rainy: bool
    muddy: bool
    repeated_route: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Flyer:
    id: str
    label: str
    phrase: str
    message: str
    fragile: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Galoshes:
    id: str
    label: str
    phrase: str
    shine: str
    plural: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Plan:
    id: str
    sense: int
    trips: int
    text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    flyer = world.get("flyer")
    if flyer.meters["wet"] < THRESHOLD:
        return out
    if ("worry", flyer.id) in world.fired:
        return out
    world.fired.add(("worry", flyer.id))
    for c in world.characters():
        c.memes["worry"] += 1
    out.append("The flyer curled at the wet edges, and everyone grew worried.")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("mole")
    b = world.get("mole_friend")
    if a.memes["sharing"] < THRESHOLD:
        return out
    if ("share",) in world.fired:
        return out
    if not world.get("galoshes").attrs.get("shared"):
        return out
    world.fired.add(("share",))
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    out.append("Sharing made the walk lighter.")
    return out


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    plan = world.get("plan")
    if plan.meters["completed"] < THRESHOLD:
        return out
    if ("repeat",) in world.fired:
        return out
    world.fired.add(("repeat",))
    world.get("mole").memes["pride"] += 1
    world.get("mole_friend").memes["pride"] += 1
    out.append("They had done the same kind act again and again, and each time it grew easier.")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("share", _r_share), Rule("repetition", _r_repetition)]


def flyer_risk(place: Place, flyer: Flyer) -> bool:
    return place.rainy and place.muddy and flyer.fragile


def plan_is_reasonable(place: Place, plan: Plan) -> bool:
    return plan.sense >= SENSE_MIN and flyer_risk(place, FLYERS["flyer"])


def sensible_plans() -> list[Plan]:
    return [p for p in PLANS.values() if p.sense >= SENSE_MIN]


def choose_plan() -> Plan:
    return max(PLANS.values(), key=lambda p: (p.sense, p.trips))


def make_mess(world: World, actor: Entity) -> None:
    flyer = world.get("flyer")
    flyer.meters["wet"] += 1
    actor.memes["worry"] += 1
    propagate(world, narrate=False)


def tell(place: Place, flyer: Flyer, galoshes: Galoshes, plan: Plan,
         hero_name: str = "Mole", friend_name: str = "Mouse") -> World:
    world = World(place)
    hero = world.add(Entity(id="mole", kind="character", type="mole", label=hero_name,
                            role="messenger", traits=["kind", "steady"]))
    friend = world.add(Entity(id="mole_friend", kind="character", type="mouse", label=friend_name,
                              role="helper", traits=["quick", "kind"]))
    elder = world.add(Entity(id="owl", kind="character", type="owl", label="Old Owl",
                             role="elder", traits=["wise"]))
    fl = world.add(Entity(id="flyer", label=flyer.label, attrs={"message": flyer.message}))
    gs = world.add(Entity(id="galoshes", label=galoshes.label, attrs={"shared": True}))
    pl = world.add(Entity(id="plan", label=plan.id))
    hero.memes["sharing"] = 1.0
    friend.memes["sharing"] = 1.0
    world.say(
        f"In a little village by the wet lane, {hero.label_word} found a {flyer.label} "
        f"that promised the harvest fair. {flyer.message}"
    )
    world.say(
        f"The path to the gate was muddy, and the rain kept tapping the leaves. "
        f"{friend.label_word} said the pair would have to ply the lane carefully."
    )
    world.para()
    world.say(
        f"{hero.label_word} wanted to deliver the {flyer.label} right away, but the rain "
        f"had made the paper soft."
    )
    world.say(
        f"{friend.label_word} lifted the single pair of {galoshes.label} and said, "
        f'"Let us share them and take turns."'
    )
    if plan.trips < 2:
        raise StoryError("This fable needs repetition: the plan must include more than one trip.")
    hero.memes["sharing"] += 1
    friend.memes["sharing"] += 1
    world.say(
        f"So they made a simple plan: one child would ply the lane in the {galoshes.label}, "
        f"then the other would wear them on the next trip."
    )
    world.say(
        f"Old Owl nodded and said, 'A shared good is a doubled good when a hard road repeats.'"
    )
    world.para()
    for i in range(plan.trips):
        actor = hero if i % 2 == 0 else friend
        wearer = gs
        wearer.wears = actor.id
        actor.shares_with = friend.id if actor is hero else hero.id
        actor.memes["joy"] += 1
        actor.meters["distance"] += 1
        flyer.meters["safe_carry"] += 1
        if i == 0:
            world.say(
                f"On the first trip, {actor.label_word} tucked the {flyer.label} under a chin "
                f"and stepped through the mud in the {galoshes.label}."
            )
        else:
            world.say(
                f"On the next trip, they switched the {galoshes.label} and went again, "
                f"so each one had a turn."
            )
        if flyer.meters["wet"] < THRESHOLD:
            flyer.meters["wet"] = 0.0
        world.say(
            f"The lane was still muddy, but the {flyer.label} stayed dry enough, and the fair "
            f"notice reached the gate."
        )
    plan.meters["completed"] = 1
    propagate(world, narrate=True)
    world.say(
        f"By evening, the {flyer.label} had been delivered, the {galoshes.label} were shared "
        f"between friends, and the village knew about the fair."
    )
    world.say(
        "That was the end of their little lesson: when a road is rough, kindness and "
        "turn-taking can carry the day."
    )
    world.facts.update(hero=hero, friend=friend, elder=elder, flyer=fl, galoshes=gs, plan=pl)
    return world


PLACES = {
    "lane": Place("lane", "the muddy lane", rainy=True, muddy=True, repeated_route="to the gate",
                  tags={"rain", "mud", "route"}),
    "village": Place("village", "the village road", rainy=True, muddy=True, repeated_route="to the square",
                     tags={"rain", "mud", "route"}),
}

FLYERS = {
    "flyer": Flyer("flyer", "flyer", "a bright little flyer", "It asked everyone to come to the fair."),
}

GALOSHES = {
    "galoshes": Galoshes("galoshes", "galoshes", "a single pair of galoshes",
                         "shone like two small moons", tags={"shoes", "rain"}),
}

PLANS = {
    "repeated_sharing": Plan("repeated_sharing", sense=3, trips=2, text="share the galoshes and take turns"),
    "double_round": Plan("double_round", sense=4, trips=3, text="take turns and make two or three deliveries"),
}


@dataclass
class StoryParams:
    place: str
    flyer: str
    galoshes: str
    plan: str
    hero_name: str
    friend_name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [("lane", "flyer", "galoshes"), ("village", "flyer", "galoshes")]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-like rainy lane storyworld with a flyer, ply, and galoshes.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--flyer", choices=FLYERS)
    ap.add_argument("--galoshes", choices=GALOSHES)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    combos = valid_combos()
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    if args.flyer and args.flyer not in FLYERS:
        raise StoryError("Unknown flyer.")
    if args.galoshes and args.galoshes not in GALOSHES:
        raise StoryError("Unknown galoshes.")
    place = args.place or rng.choice(sorted(PLACES))
    flyer = args.flyer or "flyer"
    galoshes = args.galoshes or "galoshes"
    plan = args.plan or rng.choice(sorted(PLANS))
    if plan not in PLANS or PLANS[plan].sense < SENSE_MIN:
        raise StoryError("The chosen plan is not sensible enough for this story.")
    if (place, flyer, galoshes) not in combos:
        raise StoryError("No valid combination matches the given options.")
    hero = args.name or rng.choice(["Mole", "Hare", "Otter"])
    friend = args.friend or rng.choice(["Mouse", "Robin", "Newt"])
    return StoryParams(place, flyer, galoshes, plan, hero, friend)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable for a child that includes the words "flyer", "ply", and "galoshes".',
        f"Tell a short story where {f['hero'].label_word} and {f['friend'].label_word} share {f['galoshes'].label} to ply a muddy lane and deliver a flyer.",
        "Write a gentle fable about repeated turn-taking, sharing, and a happy ending on a rainy road.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    flyer = f["flyer"]
    galoshes = f["galoshes"]
    return [
        QAItem(
            question="What problem did they face?",
            answer=f"The rain made the lane muddy, and the {flyer.label} could have gotten wet. They needed a way to ply the road without ruining the notice."
        ),
        QAItem(
            question="How did they solve it?",
            answer=f"They shared the {galoshes.label} and took turns wearing them on repeated trips. That way the work was divided, and the {flyer.label} stayed safe."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily: the {flyer.label} reached the gate, the village heard the news, and the friends felt proud because they had shared and helped one another."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are galoshes?",
            answer="Galoshes are waterproof shoes worn over other shoes to keep feet dry in rain and mud."
        ),
        QAItem(
            question="What is a flyer?",
            answer="A flyer is a small paper notice that tells people about an event or message."
        ),
        QAItem(
            question="What does 'ply' mean in this story?",
            answer="Here, 'ply' means to travel back and forth along a route again and again."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.wears:
            bits.append(f"wears={e.wears}")
        if e.shares_with:
            bits.append(f"shares_with={e.shares_with}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, F, G) :- place(P), flyer(F), galoshes(G).
sensible_plan(R) :- plan(R), sense(R, S), sense_min(M), S >= M.
shared_help :- galoshes(galoshes), plan(repeated_sharing).
happy_end :- valid(P, F, G), sensible_plan(R), shared_help.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for f in FLYERS:
        lines.append(asp.fact("flyer", f))
    for g in GALOSHES:
        lines.append(asp.fact("galoshes", g))
    for pid, p in PLANS.items():
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("sense", pid, p.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    rc = 0
    model = asp.one_model(asp_program("#show valid/3.\n#show sensible_plan/1.\n#show happy_end/0."))
    clingo_valid = set(asp.atoms(model, "valid"))
    python_valid = set(valid_combos())
    if clingo_valid != python_valid:
        print("MISMATCH in valid combos.")
        rc = 1
    if not any(p.sense >= SENSE_MIN for p in PLANS.values()):
        print("No sensible plans found.")
        rc = 1
    try:
        params = resolve_params(argparse.Namespace(place=None, flyer=None, galoshes=None, plan=None, name=None, friend=None), random.Random(7))
        sample = generate(params)
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"Smoke test failed: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], FLYERS[params.flyer], GALOSHES[params.galoshes], PLANS[params.plan], params.hero_name, params.friend_name)
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


CURATED = [
    StoryParams("lane", "flyer", "galoshes", "repeated_sharing", "Mole", "Mouse"),
    StoryParams("village", "flyer", "galoshes", "double_round", "Hare", "Robin"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3.\n#show sensible_plan/1.\n#show happy_end/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3.\n#show sensible_plan/1.\n#show happy_end/0."))
        print(f"valid combos: {sorted(set(asp.atoms(model, 'valid')))}")
        print(f"sensible plans: {sorted(set(asp.atoms(model, 'sensible_plan')))}")
        print(f"happy_end: {sorted(set(asp.atoms(model, 'happy_end')))}")
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
            header = f"### {p.hero_name} and {p.friend_name}: {p.plan}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
