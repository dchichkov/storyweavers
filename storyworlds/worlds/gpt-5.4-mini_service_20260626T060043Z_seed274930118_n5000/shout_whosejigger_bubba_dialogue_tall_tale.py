#!/usr/bin/env python3
"""
A tiny tall-tale storyworld about a loud camp helper, a mystery tool called a
whosejigger, and a big-hearted bubba who hears trouble before anybody else.

The world is driven by dialogue: somebody shouts, somebody answers, and the
problem gets solved with a practical, exaggerated fix.
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
    role: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    afford: str


@dataclass
class Problem:
    id: str
    verb: str
    shout: str
    ripple: str
    risk: str
    noise: str
    effect: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    type: str
    region: str
    guards: set[str]
    covers: set[str]
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    problem: str
    thing: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        return w


SETTINGS = {
    "camp": Setting(place="the camp", afford="loud fixing"),
    "barn": Setting(place="the barn", afford="loud fixing"),
    "porch": Setting(place="the porch", afford="loud fixing"),
    "workshop": Setting(place="the workshop", afford="loud fixing"),
}

PROBLEMS = {
    "windmill": Problem(
        id="windmill",
        verb="shout at the windmill",
        shout="shout",
        ripple="the big blades could not hear anyone over the wind",
        risk="the windmill might keep wobbling and squeaking",
        noise="a mighty holler",
        effect="the whole place gets louder before it gets better",
        keyword="shout",
        tags={"shout", "wind", "noise"},
    ),
    "beehive": Problem(
        id="beehive",
        verb="shout at the beehive",
        shout="shout",
        ripple="the bees would only buzz harder",
        risk="the bees might get cross and swirl around the eaves",
        noise="a grand bark of a yell",
        effect="the air shakes like a jar lid",
        keyword="shout",
        tags={"shout", "buzz", "noise"},
    ),
    "stuckgate": Problem(
        id="stuckgate",
        verb="shout at the stuck gate",
        shout="shout",
        ripple="the hinge still would not budge",
        risk="the gate might stay stuck and make the path lonely",
        noise="a thunderous heave of a shout",
        effect="the hinges rattle before they give way",
        keyword="shout",
        tags={"shout", "gate", "noise"},
    ),
}

THINGS = {
    "whosejigger": Thing(
        id="whosejigger",
        label="whosejigger",
        phrase="a funny-looking whosejigger with a long wooden handle",
        type="tool",
        region="hands",
        guards={"noise"},
        covers={"hands"},
    ),
    "bigwhosejigger": Thing(
        id="bigwhosejigger",
        label="big whosejigger",
        phrase="a bigger whosejigger with a brass bell and a rope pull",
        type="tool",
        region="hands",
        guards={"noise"},
        covers={"hands"},
    ),
}

NAMES_GIRL = ["Maggie", "Ruby", "Lena", "June", "Nell"]
NAMES_BOY = ["Tom", "Jeb", "Otis", "Finn", "Clint"]
TRAITS = ["brave", "cheery", "curious", "stubborn", "sparkly"]


def problem_needs_fix(problem: Problem, thing: Thing) -> bool:
    return "noise" in thing.guards and problem.keyword == "shout"


def select_thing(problem: Problem) -> Optional[Thing]:
    for t in THINGS.values():
        if problem_needs_fix(problem, t):
            return t
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, pid, tid) for place in SETTINGS for pid in PROBLEMS for tid in THINGS if problem_needs_fix(PROBLEMS[pid], THINGS[tid])]


def _bold_intro(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    world.say(
        f"{hero.id} was a {next(t for t in [hero.type] if t)} little {hero.memes.get('trait', 'spunky')} {hero.type} "
        f"who liked to make the day ring like a tin pail."
    )
    world.say(
        f"{hero.id} and {helper.label} were the kind of folks who could fix a sneeze with a hammer and a storm with a wink."
    )
    world.say(
        f"They had a {problem.keyword} on their hands and a story big enough to be heard clear across a cornfield."
    )


def _introduce_dialogue(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    world.say(f'"{problem.shout.upper()}!" {hero.id} shouted. "That {problem.ripple}!"')
    world.say(f'"Well now," said {helper.label}, "that sounds like a job for the whosejigger."')


def _use_thing(world: World, hero: Entity, helper: Entity, problem: Problem, thing: Thing) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    helper.memes["pride"] = helper.memes.get("pride", 0.0) + 1
    world.say(
        f'{helper.label} fetched {thing.phrase} and held it up like a moonbeam.'
    )
    world.say(
        f'"Give it a pull," said {helper.label}. "This {thing.label} can turn a big {problem.keyword} into a little one."'
    )


def _resolve(world: World, hero: Entity, helper: Entity, problem: Problem, thing: Thing) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(
        f"{hero.id} gave the whosejigger a brave yank, and sure enough, {problem.effect}."
    )
    world.say(
        f'"Well I'll be," said {helper.label}. "That old {thing.label} works faster than a fox on a fence rail."'
    )
    world.say(
        f"Before long the trouble was tamed, the noise was all used up, and {hero.id} was grinning in the quiet that came after."
    )


def tell(setting: Setting, problem: Problem, thing: Thing, name: str, gender: str, helper: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(
        Entity(
            id=name,
            kind="character",
            type=gender,
            role="hero",
            memes={"trait": trait, "hope": 0.0, "joy": 0.0},
        )
    )
    bubba = world.add(
        Entity(
            id=helper,
            kind="character",
            type="father" if helper.lower() == "bubba" else "man",
            label=helper,
            role="helper",
            memes={"pride": 0.0},
        )
    )
    tool = world.add(
        Entity(
            id=thing.id,
            kind="thing",
            type=thing.type,
            label=thing.label,
            phrase=thing.phrase,
            caretaker=bubba.id,
            owner=hero.id,
            plural=thing.plural,
        )
    )

    world.say(f"{hero.id} and {bubba.label} were at {setting.place}.")
    _bold_intro(world, hero, bubba, problem)
    world.para()
    _introduce_dialogue(world, hero, bubba, problem)
    world.say(f'"{problem.risk}," said {bubba.label}, "so we ought to think before we go hollering at it."')
    world.say(f'"I can do it!" said {hero.id}. "I can make a {problem.keyword} turn into a plain old whisper."')
    world.para()
    _use_thing(world, hero, bubba, problem, tool)
    _resolve(world, hero, bubba, problem, tool)
    world.facts = {
        "hero": hero,
        "helper": bubba,
        "problem": problem,
        "thing": thing,
        "setting": setting,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    problem = f["problem"]
    thing = f["thing"]
    return [
        f'Write a tall tale for children that includes the word "{problem.keyword}" and a funny "{thing.label}".',
        f'Write a dialogue-heavy story where {hero.id} and {helper.label} solve a {problem.keyword} by using {thing.label}.',
        f'Write a story with a shout, a whosejigger, and a bubba who keeps calm enough to fix the mess.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    problem = f["problem"]
    thing = f["thing"]
    return [
        QAItem(
            question=f'Who shouted at {problem.id} in the story?',
            answer=f"{hero.id} shouted first, and {helper.label} answered with a plan.",
        ),
        QAItem(
            question=f'What did {helper.label} bring to fix the trouble?',
            answer=f"{helper.label} brought {thing.phrase} and called it a whosejigger.",
        ),
        QAItem(
            question=f'How did the story end after the big {problem.keyword}?',
            answer=f"It ended with the trouble tamed, the noise gone quiet, and {hero.id} smiling with {helper.label}.",
        ),
        QAItem(
            question=f'Why did {helper.label} warn {hero.id} before the fix?',
            answer=f"{helper.label} warned {hero.id} because {problem.risk}.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "shout": [
        QAItem(
            question="What does it mean to shout?",
            answer="To shout is to speak very loudly, often because something is exciting or urgent.",
        )
    ],
    "whosejigger": [
        QAItem(
            question="What is a whosejigger?",
            answer="A whosejigger is a made-up word for a gadget or tool when somebody knows what it does but not its exact name.",
        )
    ],
    "noise": [
        QAItem(
            question="What is noise?",
            answer="Noise is a loud sound or a mix of sounds that can fill up a whole place.",
        )
    ],
    "camp": [
        QAItem(
            question="What is a camp?",
            answer="A camp is a place where people stay, play, work, and tell stories outdoors or in simple buildings.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["problem"].tags)
    tags.add("whosejigger")
    out: list[QAItem] = []
    for tag in ["shout", "whosejigger", "noise", "camp"]:
        if tag in tags:
            out.extend(WORLD_KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="camp", problem="windmill", thing="whosejigger", name="Maggie", gender="girl", helper="Bubba", trait="curious"),
    StoryParams(place="barn", problem="beehive", thing="whosejigger", name="Tom", gender="boy", helper="Bubba", trait="brave"),
    StoryParams(place="workshop", problem="stuckgate", thing="bigwhosejigger", name="Ruby", gender="girl", helper="Bubba", trait="stubborn"),
]


def explain_rejection() -> str:
    return "(No story: this world only tells shout-and-whosejigger tales that can be fixed by Bubba's tools.)"


ASP_RULES = r"""
problem(P) :- problem_name(P).
thing(T) :- thing_name(T).
compatible(P,T) :- problem_name(P), thing_name(T), fixes(T,P).
story(Place,P,T) :- setting(Place), problem_name(P), thing_name(T), affords(Place,P), fixes(T,P).
#show compatible/2.
#show story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
        lines.append(asp.fact("affords", p, "shout"))
    for p in PROBLEMS:
        lines.append(asp.fact("problem_name", p))
    for t in THINGS:
        lines.append(asp.fact("thing_name", t))
        lines.append(asp.fact("fixes", t, "shout"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    if set(asp_valid_combos()) == set((p, t) for _, p, t in valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
        return 0
    print("MISMATCH between clingo and python gates.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: shout, whosejigger, bubba, dialogue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", default="Bubba")
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


def valid_names(gender: str) -> list[str]:
    return NAMES_GIRL if gender == "girl" else NAMES_BOY


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.thing:
        if not problem_needs_fix(PROBLEMS[args.problem], THINGS[args.thing]):
            raise StoryError(explain_rejection())
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.problem is None or c[1] == args.problem)
        and (args.thing is None or c[2] == args.thing)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, thing = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(valid_names(gender))
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, thing=thing, name=name, gender=gender, helper=args.helper, trait=trait)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for pid, p in PROBLEMS.items():
            for tid, t in THINGS.items():
                if problem_needs_fix(p, t):
                    out.append((place, pid, tid))
    return out


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PROBLEMS[params.problem], THINGS[params.thing], params.name, params.gender, params.helper, params.trait)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, t in combos:
            print(f"  {p[0]} / {p[1]}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
