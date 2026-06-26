#!/usr/bin/env python3
"""
storyworlds/worlds/yell_inner_monologue_comedy.py
==================================================

A small comedy storyworld about a child, a looming reason to yell, and the
inner monologue that helps them choose a funnier, kinder ending instead.

Premise:
- A character gets worked up about a noisy, surprising, or mildly embarrassing
  situation.
- Their inner monologue races ahead with dramatic thoughts.
- The world gives them a better, safer way to express themselves than yelling.

This world is intentionally tiny and constraint-driven. It models:
- a child character with physical and emotional state
- a setting with a few props
- a "yell pressure" meter that can build up
- a turn where the character notices their own inner monologue
- a resolution where they use a comic non-yelling response

The prose aims for child-facing comedy: concrete, light, and state-driven.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool
    noise_source: str
    comedy_note: str


@dataclass
class Problem:
    id: str
    trigger: str
    inner_monologue: str
    exaggeration: str
    comic_reframe: str
    safe_action: str
    shout_phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    type: str
    mood_boost: str
    tags: set[str] = field(default_factory=set)


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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        other = World(self.setting)
        other.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "traits": list(v.traits), "owner": v.owner,
            "caretaker": v.caretaker, "meters": dict(v.meters), "memes": dict(v.memes),
        }) for k, v in self.entities.items()}
        other.paragraphs = [[]]
        other.fired = set(self.fired)
        other.facts = dict(self.facts)
        return other


def _m(world: World, eid: str, key: str) -> float:
    return world.get(eid).meters.get(key, 0.0)


def _mm(world: World, eid: str, key: str) -> float:
    return world.get(eid).memes.get(key, 0.0)


def _setm(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def _setmm(ent: Entity, key: str, delta: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def _r_build_pressure(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.entities.values():
        if hero.kind != "character":
            continue
        if hero.memes.get("startled", 0.0) < THRESHOLD:
            continue
        sig = ("pressure", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _setmm(hero, "yell_pressure", 1.0)
        out.append(f"{hero.id} felt a shout climbing up like a balloon with a squeaky string.")
    return out


def _r_inner_monologue(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.entities.values():
        if hero.kind != "character":
            continue
        if hero.memes.get("yell_pressure", 0.0) < THRESHOLD:
            continue
        if hero.memes.get("self_awareness", 0.0) >= THRESHOLD:
            continue
        sig = ("monologue", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _setmm(hero, "self_awareness", 1.0)
        out.append(f"Inside {hero.id}'s head, a tiny narrator whispered, {world.facts.get('monologue', '“Maybe do not yell yet.”')}")
    return out


def _r_release_pressure(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.entities.values():
        if hero.kind != "character":
            continue
        if hero.memes.get("self_awareness", 0.0) < THRESHOLD:
            continue
        if hero.memes.get("calm_choice", 0.0) >= THRESHOLD:
            continue
        sig = ("release", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _setmm(hero, "calm_choice", 1.0)
        hero.memes["yell_pressure"] = 0.0
        out.append(f"{hero.id} took one breath, and the balloon in {hero.pronoun('possessive')} chest turned into a much less dramatic noodle.")
    return out


CAUSAL_RULES = [
    _r_build_pressure,
    _r_inner_monologue,
    _r_release_pressure,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_yell(world: World, hero_id: str) -> dict:
    sim = world.copy()
    hero = sim.get(hero_id)
    _setmm(hero, "startled", 1.0)
    propagate(sim, narrate=False)
    return {
        "yell_pressure": hero.memes.get("yell_pressure", 0.0),
        "self_awareness": hero.memes.get("self_awareness", 0.0),
        "calm_choice": hero.memes.get("calm_choice", 0.0),
    }


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t not in {"little"}), "curious")
    world.say(
        f"{hero.id} was a little {trait} {hero.type} who noticed every squeak, bump, and banana peel of life."
    )


def setup_setting(world: World, hero: Entity, prop: Entity, problem: Problem) -> None:
    world.say(
        f"One day at {world.setting.place}, {hero.id} noticed {world.setting.noise_source} and {prop.phrase} at the same time."
    )
    world.say(world.setting.comedy_note)
    world.say(
        f"{hero.id} loved {prop.label}, but {problem.trigger} made {hero.pronoun('possessive')} eyebrows climb straight toward the ceiling."
    )


def startle(world: World, hero: Entity, problem: Problem) -> None:
    _setmm(hero, "startled", 1.0)
    _setmm(hero, "annoyance", 1.0)
    world.say(
        f"{problem.trigger.capitalize()}, and {hero.id} felt the big, loud urge to yell {problem.shout_phrase}."
    )


def monologue(world: World, hero: Entity, problem: Problem) -> None:
    world.facts["monologue"] = problem.inner_monologue
    world.say(
        f"Inside {hero.id}'s head, a very serious voice announced, {problem.inner_monologue}"
    )
    world.say(f"Then the same voice immediately tripped over a sock and added, {problem.exaggeration}")


def turn(world: World, hero: Entity, problem: Problem) -> None:
    propagate(world, narrate=True)
    world.say(
        f"{hero.id} blinked, and the inner monologue got a tiny second opinion: {problem.comic_reframe}"
    )


def resolve(world: World, hero: Entity, prop: Entity, problem: Problem) -> None:
    world.say(
        f"Instead of yelling, {hero.id} tried {problem.safe_action}, which was much funnier and worked better."
    )
    world.say(
        f"{hero.id} did it, and {prop.label} looked even better afterward."
    )
    world.say(
        f"At the end, {hero.id} wore a proud little smile, and the whole room felt less like a siren and more like a giggle."
    )


SETTINGS = {
    "kitchen": Setting(
        place="the kitchen",
        indoor=True,
        noise_source="the dishwasher hummed like a sleepy robot",
        comedy_note="Even the spoon in the sink looked mildly offended by how official the noise sounded.",
    ),
    "playroom": Setting(
        place="the playroom",
        indoor=True,
        noise_source="a toy trumpet let out a tiny honk",
        comedy_note="It was not a loud trumpet. It was, in fact, the sort of trumpet that seemed apologetic about existing.",
    ),
    "backyard": Setting(
        place="the backyard",
        indoor=False,
        noise_source="the wind rattled the fence",
        comedy_note="The fence rattled so hard it looked like it was telling a joke to the grass.",
    ),
}

PROBLEMS = {
    "spill": Problem(
        id="spill",
        trigger="a cup tipped over and spilled juice across the table",
        inner_monologue="“Emergency! The juice is making a shiny lake!”",
        exaggeration="“Everything is now juice. The table. The floor. The moon.”",
        comic_reframe="It is only juice, not the end of the universe, and towels are very brave.",
        safe_action="fetching a towel and making a cleanup parade",
        shout_phrase="HEY!",
        tags={"spill", "juice", "cleanup"},
    ),
    "noise": Problem(
        id="noise",
        trigger="a toy train squealed around the track",
        inner_monologue="“Warning! That train sounds like a mouse learning opera!”",
        exaggeration="“The train will circle forever and turn the room into a concert hall for ants.”",
        comic_reframe="Tiny noises can be silly instead of scary, and ears are allowed to relax.",
        safe_action="covering one ear, laughing a little, and asking for a quieter turn",
        shout_phrase="STOP!",
        tags={"noise", "toy", "sound"},
    ),
    "teasing": Problem(
        id="teasing",
        trigger="a sibling borrowed the marker and drew a mustache on the cat picture",
        inner_monologue="“This is outrageous. The mustache has entered the house.”",
        exaggeration="“The cat picture is now a mayor, and nobody asked me for a campaign speech.”",
        comic_reframe="A marker mustache can be erased, but a funny face can also become a family joke.",
        safe_action="asking for the marker back with a dramatic but polite voice",
        shout_phrase="GIVE IT BACK!",
        tags={"marker", "drawing", "family"},
    ),
}

PROPS = {
    "juice": Prop(
        id="juice",
        label="the juice box",
        phrase="a little juice box with a straw that bent like a straw trying its best",
        type="juice_box",
        mood_boost="sticky hands and a good story",
        tags={"spill", "juice"},
    ),
    "train": Prop(
        id="train",
        label="the toy train",
        phrase="a toy train with red wheels and a very determined whistle",
        type="toy_train",
        mood_boost="tiny engine sounds and a sense of adventure",
        tags={"noise", "toy"},
    ),
    "cat_picture": Prop(
        id="cat_picture",
        label="the cat picture",
        phrase="a neat picture of a cat that looked extremely proud of its whiskers",
        type="picture",
        mood_boost="marker lines and a rescue mission",
        tags={"teasing", "drawing"},
    ),
}

HERO_NAMES = ["Mina", "Theo", "Luca", "Pia", "June", "Owen", "Nora", "Eli"]
TRAITS = ["curious", "dramatic", "cheerful", "squirmy", "thoughtful", "bouncy"]


@dataclass
class StoryParams:
    place: str
    problem: str
    prop: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for problem in PROBLEMS:
            for prop in PROPS:
                if problem in PROPS[prop].tags:
                    combos.append((place, problem, prop))
    return combos


def explain_rejection(problem: Problem, prop: Prop) -> str:
    return (
        f"(No story: the problem '{problem.id}' does not naturally pair with {prop.label}. "
        f"Try a prop that shares the same situation tags.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Comedy story world: inner monologue, yell pressure, and a gentler punchline."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    if args.problem and args.prop:
        if args.problem not in PROPS[args.prop].tags:
            raise StoryError(explain_rejection(PROBLEMS[args.problem], PROPS[args.prop]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.prop is None or c[2] == args.prop)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem_id, prop_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem_id, prop=prop_id, name=name, gender=gender, trait=trait)


def start_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero_type = "girl" if params.gender == "girl" else "boy"
    hero = world.add(Entity(
        id=params.name, kind="character", type=hero_type, traits=["little", params.trait],
        meters={}, memes={}
    ))
    prop = world.add(Entity(
        id=params.prop, kind="thing", type=PROPS[params.prop].type, label=PROPS[params.prop].label,
        phrase=PROPS[params.prop].phrase
    ))
    problem = PROBLEMS[params.problem]
    world.facts.update(hero=hero, prop=prop, problem=problem)
    introduce(world, hero)
    setup_setting(world, hero, prop, problem)
    world.para()
    startle(world, hero, problem)
    monologue(world, hero, problem)
    turn(world, hero, problem)
    world.para()
    resolve(world, hero, prop, problem)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    problem = world.facts["problem"]
    prop = world.facts["prop"]
    return [
        f'Write a short comedy story for a child where {hero.id} almost yells because {problem.trigger}, but the inner monologue helps {hero.id} calm down.',
        f"Tell a funny story set at {world.setting.place} where {hero.id} thinks very loudly inside {hero.pronoun('possessive')} head instead of yelling about {prop.label}.",
        f'Write a gentle, silly story that includes the word "yell" but ends with a calmer choice and a comic line.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    problem = world.facts["problem"]
    prop = world.facts["prop"]
    return [
        QAItem(
            question=f"Why did {hero.id} feel like yelling at {world.setting.place}?",
            answer=f"{hero.id} felt like yelling because {problem.trigger}. {problem.inner_monologue}",
        ),
        QAItem(
            question=f"What did {hero.id}'s inner monologue sound like?",
            answer=f"It sounded like a dramatic little voice that said {problem.inner_monologue} and then laughed at itself with {problem.exaggeration}",
        ),
        QAItem(
            question=f"What did {hero.id} do instead of yelling about {prop.label}?",
            answer=f"{hero.id} chose {problem.safe_action}, which turned the moment from noisy to funny.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} calmer, {prop.label} handled better, and the whole scene feeling more like a joke than a crisis.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the voice of thoughts in your head when you talk to yourself silently.",
        ),
        QAItem(
            question="Why can yelling make a problem worse?",
            answer="Yelling can make people feel upset or scared, so it often makes it harder to solve the problem nicely.",
        ),
        QAItem(
            question="What can help if you feel like yelling?",
            answer="Taking a breath, noticing your thoughts, and choosing a calm action can help you feel better.",
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
problem(P) :- problem_fact(P).
prop(X) :- prop_fact(X).

compatible(Place, Problem, Prop) :-
    setting(Place), problem(Problem), prop(Prop),
    pair(Problem, Prop).

#show compatible/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("problem_fact", pid))
    for prop_id, prop in PROPS.items():
        lines.append(asp.fact("prop", prop_id))
        lines.append(asp.fact("prop_fact", prop_id))
        for tag in prop.tags:
            lines.append(asp.fact("pair", next(p for p in PROBLEMS if p in tag or tag in p), prop_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    asp_set = set(asp.atoms(model, "compatible"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - py_set:
        print("  only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in python:", sorted(py_set - asp_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def generate(params: StoryParams) -> StorySample:
    world = start_world(params)
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
    StoryParams(place="kitchen", problem="spill", prop="juice", name="Mina", gender="girl", trait="dramatic"),
    StoryParams(place="playroom", problem="noise", prop="train", name="Theo", gender="boy", trait="thoughtful"),
    StoryParams(place="backyard", problem="teasing", prop="cat_picture", name="Nora", gender="girl", trait="bouncy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for item in combos:
            print("  ", item)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
