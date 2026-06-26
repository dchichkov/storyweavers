#!/usr/bin/env python3
"""
storyworlds/worlds/conditioner_hypothesize_click_twist_folk_tale.py
===================================================================

A standalone folk-tale story world about a child, a stubborn tangle, a
careful guess, and a small click that changes the day.

Seed inspiration:
- conditioner
- hypothesize
- click
- Twist
- Folk Tale style

The domain is intentionally small: a village child faces a tangled problem,
the grown-up makes a reasoned guess about the cause, and a humble bottle of
conditioner helps turn the trouble into a neat ending.
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
TANGLES = {"snarl", "knot", "tangle"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
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
        female = {"girl", "mother", "woman", "grandmother"}
        male = {"boy", "father", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    feature: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    target_part: str
    tag: str
    keyword: str


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trail_twist: bool = False

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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.trail_twist = self.trail_twist
        return w


def _messy(world: World, actor: Entity, prob: Problem, narrate: bool = True) -> list[str]:
    out: list[str] = []
    if actor.meters.get(prob.mess, 0.0) < THRESHOLD:
        return out
    for ent in world.entities.values():
        if ent.owner != actor.id or ent.kind != "thing":
            continue
        if ent.label == "conditioner bottle":
            continue
        if ent.type != prob.target_part:
            continue
        sig = ("messy", ent.id, prob.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters[prob.mess] = ent.meters.get(prob.mess, 0.0) + 1.0
        ent.meters["dirty"] = ent.meters.get("dirty", 0.0) + 1.0
        out.append(f"{actor.pronoun('possessive').capitalize()} {ent.label} got {prob.soil}.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        for actor in [e for e in world.entities.values() if e.kind == "character"]:
            prob: Problem = world.facts["problem"]
            before = len(world.fired)
            _messy(world, actor, prob, narrate=narrate)
            if len(world.fired) != before:
                changed = True


def reasonableness_gate(problem: Problem, remedy: Remedy, setting: Setting) -> bool:
    return problem.tag in remedy.helps and problem.id in setting.affords


@dataclass
class StoryParams:
    place: str
    problem: str
    remedy: str
    name: str
    gender: str
    kin: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "village": Setting(place="the village green", feature="a twisty lane", affords={"hair", "wool"}),
    "cottage": Setting(place="the old cottage", feature="a little blue chair", affords={"hair"}),
    "barn": Setting(place="the warm barn", feature="a hay cart", affords={"wool"}),
}

PROBLEMS = {
    "hair": Problem(
        id="hair",
        verb="untangle her hair",
        gerund="untangling hair",
        rush="run to the mirror",
        mess="snarl",
        soil="full of knots",
        target_part="hair",
        tag="tangle",
        keyword="hair",
    ),
    "wool": Problem(
        id="wool",
        verb="smooth the lamb's wool",
        gerund="smoothing wool",
        rush="dash to the stall",
        mess="knot",
        soil="all knotted up",
        target_part="wool",
        tag="tangle",
        keyword="wool",
    ),
}

REMEDIES = {
    "conditioner": Remedy(
        id="conditioner",
        label="conditioner",
        phrase="a small bottle of conditioner",
        prep="twist open the conditioner and pour a little into a bowl",
        tail="took the softened strands gently apart",
        helps={"tangle"},
    )
}

GIRL_NAMES = ["Mira", "Anya", "Lina", "Tessa", "Nora", "Elsa"]
BOY_NAMES = ["Pip", "Otto", "Ruben", "Milo", "Jory", "Theo"]
TRAITS = ["gentle", "curious", "brave", "patient", "cheerful", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for pid, prob in PROBLEMS.items():
            if pid not in setting.affords:
                continue
            for rid, rem in REMEDIES.items():
                if reasonableness_gate(prob, rem, setting):
                    out.append((place, pid, rid))
    return out


def explain_rejection(problem: Problem, remedy: Remedy, setting: Setting) -> str:
    return (
        f"(No story: {remedy.label} can help with a tangle, but this setting "
        f"does not fit {problem.keyword} work well enough for a folk-tale turn.)"
    )


def explain_gender(problem_id: str, gender: str) -> str:
    return f"(No story: this world's {problem_id} tale is not set up for {gender}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale story world: conditioner, a guess, and a click."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--kin", choices=["mother", "father", "grandmother", "grandfather"])
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
    if args.problem and args.remedy:
        prob = PROBLEMS[args.problem]
        rem = REMEDIES[args.remedy]
        setting = SETTINGS[args.place] if args.place else next(iter(SETTINGS.values()))
        if not reasonableness_gate(prob, rem, setting):
            raise StoryError(explain_rejection(prob, rem, setting))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.remedy is None or c[2] == args.remedy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, remedy = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    kin = args.kin or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, remedy=remedy, name=name, gender=gender, kin=kin, trait=trait)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    problem = PROBLEMS[params.problem]
    remedy = REMEDIES[params.remedy]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    kin = world.add(Entity(id="Kin", kind="character", type=params.kin, label=f"the {params.kin}"))
    target = world.add(Entity(
        id="Target",
        kind="thing",
        type=problem.target_part,
        label=problem.target_part,
        phrase=problem.keyword,
        owner=hero.id,
        caretaker=kin.id,
    ))
    bottle = world.add(Entity(
        id="Bottle",
        kind="thing",
        type="bottle",
        label="conditioner bottle",
        phrase=remedy.phrase,
        owner=kin.id,
    ))

    world.facts.update(hero=hero, kin=kin, target=target, bottle=bottle,
                       problem=problem, remedy=remedy, setting=setting)
    hero.meters[problem.mess] = 1.0
    hero.memes["worry"] = 1.0

    world.say(
        f"Once in {setting.place}, there lived a {params.trait} {params.gender} named {params.name}."
    )
    world.say(
        f"{params.name} loved {problem.gerund}, but {setting.feature} hid a stubborn little twist in the day."
    )
    world.say(
        f"{'Her' if params.gender == 'girl' else 'His'} {problem.keyword} was lovely until the wind and play turned it {problem.soil}."
    )

    world.para()
    world.say(
        f"At the gate, {params.name} wanted to {problem.verb}, but {params.kin} could see the trouble at once."
    )
    world.say(
        f"{params.kin.capitalize()} stopped, looked, and said, "
        f"\"I hypothesize the snarl came from the {setting.feature}.\""
    )
    world.say(
        f"Then came a small click as {params.kin} opened the {bottle.label}."
    )

    world.para()
    world.say(
        f"{params.kin.capitalize()} used the {bottle.label} with a slow, careful hand."
    )
    world.say(
        f"{params.name} counted the breaths, and the soft cream smoothed the knots little by little."
    )
    world.say(
        f"At last, {params.kin} {remedy.tail}, and the whole tangle gave way."
    )

    if problem.id == "hair":
        target.meters["snarl"] = 0.0
        target.meters["clean"] = 1.0
    else:
        target.meters["knot"] = 0.0
        target.meters["clean"] = 1.0
    hero.memes["worry"] = 0.0
    hero.memes["joy"] = 1.0
    world.trail_twist = True
    world.say(
        f"In the end, {params.name} laughed, and the {problem.keyword} shone neat as a ribbon in spring."
    )

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prob: Problem = f["problem"]
    rem: Remedy = f["remedy"]
    kin = f["kin"]
    return [
        f'Write a gentle folk tale for a small child that includes the word "{prob.keyword}".',
        f"Tell a short story where {hero.id} wants to {prob.verb}, but {kin.label} makes a careful guess and uses {rem.label}.",
        f'Write a simple folk tale with a tiny twist, a soft click, and a bottle of "{rem.label}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    kin = f["kin"]
    prob: Problem = f["problem"]
    rem: Remedy = f["remedy"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who was the story about in {setting.place}?",
            answer=f"It was about {hero.id}, who faced a {prob.keyword} problem in {setting.place}.",
        ),
        QAItem(
            question=f"What did {kin.label} hypothesize about the trouble?",
            answer=f"{kin.label.capitalize()} hypothesized that the snarl came from the twisty place and the day’s rough play.",
        ),
        QAItem(
            question=f"What made the soft change happen?",
            answer=f"The {rem.label} helped smooth the {prob.keyword}, and the click of the bottle opened the fix.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the tangle gone, {hero.id} smiling, and the hair or wool neat again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is conditioner for?",
            answer="Conditioner is a creamy hair product that helps make tangles softer and easier to comb apart.",
        ),
        QAItem(
            question="What does hypothesize mean?",
            answer="To hypothesize means to make a careful guess about why something happened.",
        ),
        QAItem(
            question="What does click usually sound like?",
            answer="A click is a small, sharp sound, like when a bottle cap or latch opens or shuts.",
        ),
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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  twist trail: {world.trail_twist}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="cottage", problem="hair", remedy="conditioner", name="Mira", gender="girl", kin="mother", trait="gentle"),
    StoryParams(place="barn", problem="wool", remedy="conditioner", name="Pip", gender="boy", kin="grandmother", trait="curious"),
    StoryParams(place="village", problem="hair", remedy="conditioner", name="Lina", gender="girl", kin="father", trait="bright"),
]


ASP_RULES = r"""
% A story is valid when the setting affords the problem and the remedy helps it.
valid(Place, Problem, Remedy) :- setting(Place), problem(Problem), remedy(Remedy),
    affords(Place, Problem), helps(Remedy, Problem).

valid_story(Place, Problem, Remedy, Gender) :- valid(Place, Problem, Remedy), gender_ok(Problem, Gender).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("keyword", pid, p.keyword))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        for h in sorted(r.helps):
            lines.append(asp.fact("helps", rid, h))
    for g in ["girl", "boy"]:
        lines.append(asp.fact("gender_ok", "hair", g))
        lines.append(asp.fact("gender_ok", "wool", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_sample(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_sample(params)


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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.problem} at {p.place} (remedy: {p.remedy})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
