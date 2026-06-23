#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/hesitant_suspense_reconciliation_folk_tale.py
=============================================================================================================================

A small folk-tale story world about a hesitant child, a suspenseful lost-object
search, and a reconciliation with a misunderstood neighbor.

The domain is built to produce complete, state-driven stories: a simple setup,
a tense search through a dark place, a mistake or false suspicion, and a
reconciliation that changes the ending image.
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
    role: str = ""
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
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
    dark: bool = False
    supports: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    clue: str
    risk: str
    tension: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Help:
    id: str
    label: str
    method: str
    result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str = "copperwood"
    problem: str = "lantern"
    help: str = "song"
    hero_name: str = "Nina"
    hero_type: str = "girl"
    helper_name: str = "Moss"
    helper_type: str = "man"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


def _make_entity_meters(entity: Entity, keys: list[str]) -> None:
    for k in keys:
        entity.meters.setdefault(k, 0.0)
    for k in ["hope", "fear", "hesitation", "relief", "warmth", "hurt", "trust", "anger"]:
        entity.memes.setdefault(k, 0.0)


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("searched") and not world.facts.get("found"):
        if ("suspense", "fear") in world.fired:
            return []
        world.fired.add(("suspense", "fear"))
        seeker = world.get("hero")
        seeker.memes["fear"] += 1
        world.get("helper").memes["worry"] = world.get("helper").memes.get("worry", 0.0) + 1
        out.append(f"{seeker.id} felt a hush in the dark.")
    return out


def _r_reconciliation(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("resolved") and ("reconcile", "soft") not in world.fired:
        world.fired.add(("reconcile", "soft"))
        helper = world.get("helper")
        hero = world.get("hero")
        helper.memes["trust"] += 1
        hero.memes["trust"] += 1
        hero.memes["relief"] += 1
        out.append(f"Their voices softened like rain on a roof.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_suspense, _r_reconciliation):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for prob in PROBLEMS:
            for h in HELPS:
                if reasonableness(p, prob, h):
                    combos.append((p, prob, h))
    return combos


def reasonableness(place: str, problem: str, help_id: str) -> bool:
    place_cfg = PLACES[place]
    prob_cfg = PROBLEMS[problem]
    help_cfg = HELPS[help_id]
    return problem in place_cfg.supports and prob_cfg.id in help_cfg.tags


def tell(place: Place, problem: Problem, help_obj: Help, params: StoryParams) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name,
                            role="hero", tags={"seeker"}))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name,
                              role="helper", tags={"elder"}))
    object_name = world.add(Entity(id="object", kind="thing", type="thing", label=problem.label, tags={problem.id}))
    _make_entity_meters(hero, ["fear", "hope", "hesitation", "relief", "trust"])
    _make_entity_meters(helper, ["fear", "hope", "hesitation", "relief", "trust"])
    _make_entity_meters(object_name, ["lost", "found", "wet", "touched"])
    world.facts.update(
        hero=hero,
        helper=helper,
        object=object_name,
        place=place,
        problem=problem,
        help=help_obj,
        searched=False,
        found=False,
        resolved=False,
    )

    hero.memes["hesitation"] += 1
    world.say(f"In {place.label}, {hero.label} stood at the path with a hesitant heart.")
    world.say(f"They had lost {problem.label}, and {problem.clue} made the evening feel strange.")
    world.say(f"{helper.label} offered {help_obj.label}, but {hero.label} was still unsure.")

    world.para()
    world.facts["searched"] = True
    hero.memes["hope"] += 1
    hero.meters["steps"] += 1
    world.say(f"Together they searched where the lantern light thinned.")
    world.say(f"{problem.risk} lingered as they followed {problem.tension} into the quiet dark.")
    if problem.id == "lantern":
        object_name.meters["found"] += 1
        world.facts["found"] = True

    if not world.facts["found"]:
        world.say(f"Only a soft sound answered them at first, and the night grew more suspenseful.")
        world.say(f"Then {helper.label} noticed a small glint where the reeds bent low.")
        object_name.meters["found"] += 1
        world.facts["found"] = True

    world.para()
    world.facts["resolved"] = True
    hero.memes["hesitation"] = 0
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    hero.meters["holding"] += 1
    object_name.meters["touched"] += 1
    propagate(world, narrate=False)

    world.say(f"{hero.label} found {problem.label} at last, and the hard knot in their chest loosened.")
    world.say(f"{helper.label} smiled, and {help_obj.result}.")
    world.say(f"They walked home side by side, with {problem.label} warm in {hero.pronoun('possessive')} hands.")
    return world


PLACES = {
    "copperwood": Place(id="copperwood", label="Copperwood Hollow", dark=True, supports={"lantern", "cloak"}),
    "willowfen": Place(id="willowfen", label="Willowfen Lane", dark=True, supports={"bread", "lantern"}),
    "stonebridge": Place(id="stonebridge", label="Stonebridge Crossing", dark=True, supports={"key", "lantern"}),
    "hillford": Place(id="hillford", label="Hillford Meadow", dark=True, supports={"calf", "lantern"}),
}

PROBLEMS = {
    "lantern": Problem(id="lantern", label="the lantern", clue="a flicker had vanished from the path", risk="The path could not be crossed in the dark", tension="the black reeds", tags={"lantern"}),
    "bread": Problem(id="bread", label="the bread loaf", clue="the basket was empty by supper", risk="The oven would wait cold without supper bread", tension="the old bridge", tags={"bread"}),
    "key": Problem(id="key", label="the iron key", clue="the door would not open without it", risk="The chest would stay locked", tension="the mossy stones", tags={"key"}),
    "calf": Problem(id="calf", label="the calf bell", clue="the little bell had gone quiet", risk="The herd could not be called home", tension="the tall grass", tags={"calf"}),
}

HELPS = {
    "song": Help(id="song", label="a low old song", method="song", result="the song made the dark feel less sharp", tags={"lantern", "bread"}),
    "candle": Help(id="candle", label="a sheltered candle", method="candle", result="the candle glowed behind a cup of clay", tags={"lantern", "key"}),
    "lantern": Help(id="lantern", label="a bright lantern", method="lantern", result="the lantern held a small, steady sun", tags={"key", "calf", "bread", "lantern"}),
    "rope": Help(id="rope", label="a rope and careful hands", method="rope", result="the rope marked the path home", tags={"calf", "lantern"}),
}

CURATED = [
    StoryParams(place="copperwood", problem="lantern", help="lantern", hero_name="Nina", hero_type="girl", helper_name="Moss", helper_type="man"),
    StoryParams(place="willowfen", problem="bread", help="song", hero_name="Tavi", hero_type="boy", helper_name="Aunt Reed", helper_type="woman"),
    StoryParams(place="stonebridge", problem="key", help="candle", hero_name="Mira", hero_type="girl", helper_name="Old Bram", helper_type="man"),
    StoryParams(place="hillford", problem="calf", help="rope", hero_name="Pip", hero_type="boy", helper_name="Grandma June", helper_type="woman"),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale story about a hesitant child in {f["place"].label} who needs help finding {f["problem"].label}.',
        f"Tell a suspenseful but gentle story where {f['hero'].label} and {f['helper'].label} search for {f['problem'].label} and end in reconciliation.",
        f'Write a short folk tale that includes the word "hesitant" and ends with a warm reunion beside {f["problem"].label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    problem = f["problem"]
    place = f["place"]
    help_obj = f["help"]
    return [
        QAItem(
            question=f"Why was {hero.label} hesitant at {place.label}?",
            answer=f"{hero.label} was hesitant because {problem.clue}. The missing thing made the evening feel uncertain.",
        ),
        QAItem(
            question=f"What did {helper.label} offer to help with the search?",
            answer=f"{helper.label} offered {help_obj.label}. That gave the search a clear way forward in the dark.",
        ),
        QAItem(
            question=f"What changed after {hero.label} found {problem.label}?",
            answer=f"The fear eased and the two of them reconciled. They walked home together with {problem.label} safely in {hero.pronoun('possessive')} hands.",
        ),
        QAItem(
            question=f"How did the ending show that the worry was over?",
            answer=f"{hero.label} held {problem.label} warmly, and {helper.label} was smiling beside {hero.label}. The quiet path turned from tense to peaceful.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is hesitant?",
            answer="Hesitant means unsure or slow to act because something feels uncertain.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of waiting and wondering what will happen next.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people make peace after fear, blame, or misunderstanding.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.help is None or c[2] == args.help)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, help_id = rng.choice(sorted(combos))
    hero_name = args.hero_name or rng.choice(["Nina", "Tavi", "Mira", "Pip", "Oren", "Lio"])
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_name = args.helper_name or rng.choice(["Moss", "Aunt Reed", "Old Bram", "Grandma June"])
    helper_type = args.helper_type or rng.choice(["man", "woman"])
    return StoryParams(
        place=place,
        problem=problem,
        help=help_id,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.problem not in PROBLEMS or params.help not in HELPS:
        raise StoryError("Invalid story parameters.")
    if not reasonableness(params.place, params.problem, params.help):
        raise StoryError("This combination does not make a plausible folk tale.")
    world = tell(PLACES[params.place], PROBLEMS[params.problem], HELPS[params.help], params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


ASP_RULES = r"""
valid(P, O, H) :- place(P), problem(O), help(H), supports(P, O), helpful(H, O).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.dark:
            lines.append(asp.fact("dark", pid))
        for s in sorted(p.supports):
            lines.append(asp.fact("supports", pid, s))
    for oid, o in PROBLEMS.items():
        lines.append(asp.fact("problem", oid))
    for hid, h in HELPS.items():
        lines.append(asp.fact("help", hid))
        for t in sorted(h.tags):
            lines.append(asp.fact("helpful", hid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    ok = True
    if python_set != clingo_set:
        ok = False
        print("MISMATCH between Python and ASP valid_combos():")
        print("python-only:", sorted(python_set - clingo_set))
        print("asp-only:", sorted(clingo_set - python_set))
    # smoke test
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as e:
        ok = False
        print(f"SMOKE TEST FAILED: {e}")
    if ok:
        print(f"OK: verify passed ({len(python_set)} valid combos).")
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale story world of hesitation, suspense, and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--help", dest="help", choices=HELPS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["man", "woman"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.hero_name} at {p.place} ({p.problem} / {p.help})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
