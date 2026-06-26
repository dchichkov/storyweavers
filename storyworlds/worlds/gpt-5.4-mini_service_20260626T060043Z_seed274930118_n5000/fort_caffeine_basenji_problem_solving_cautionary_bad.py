#!/usr/bin/env python3
"""
Standalone storyworld: fort, caffeine, basenji.
A tall-tale cautionary problem-solving domain with a bad ending.

Seed image:
A child builds a fort, finds grown-up coffee, and a clever basenji keeps
trying to help. The problem starts small, gets louder, and ends badly when
a careless fix makes things worse.

This world generates one story at a time, plus grounded QA and world QA.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Domain model
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    indoors: bool = False


@dataclass
class Problem:
    id: str
    title: str
    danger: str
    fix: str
    caution: str
    mess: str
    caution_tag: str


@dataclass
class StoryParams:
    place: str
    problem: str
    hero_name: str
    hero_type: str
    caretaker_type: str
    sidekick_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.history: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.history = list(self.history)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "backyard": Setting("the backyard"),
    "treehouse": Setting("the treehouse"),
    "barn": Setting("the barn"),
    "fort": Setting("the fort", indoors=True),
}

PROBLEMS = {
    "caffeine": Problem(
        id="caffeine",
        title="a mug of strong coffee",
        danger="caffeine can make a child jittery and keep a body awake too long",
        fix="pour it out and give water instead",
        caution="grown-up drinks are not for children",
        mess="spilled coffee",
        caution_tag="coffee",
    ),
    "fort": Problem(
        id="fort",
        title="a wobbly fort wall",
        danger="a shaky wall can tumble on fingers and toes",
        fix="brace the wall with a crate and slow careful hands",
        caution="a fort should be checked before anyone leans on it",
        mess="cracked sticks",
        caution_tag="fort",
    ),
    "basenji": Problem(
        id="basenji",
        title="a basenji with a hot nose and a wild idea",
        danger="a clever basenji can dart off before anyone can stop it",
        fix="clip the leash, open the gate slowly, and call it back",
        caution="dogs need calm handling near open doors",
        mess="muddy pawprints",
        caution_tag="dog",
    ),
}


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def _build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        meters={"curiosity": 1.0},
        memes={"hope": 1.0},
    ))
    caretaker = world.add(Entity(
        id="caretaker",
        kind="character",
        type=params.caretaker_type,
        label="the grown-up",
        meters={"worry": 1.0},
        memes={"caution": 1.0},
    ))
    sidekick = world.add(Entity(
        id=params.sidekick_name,
        kind="character",
        type="dog" if params.problem == "basenji" else "friend",
        label=params.sidekick_name,
        meters={"zip": 1.0},
        memes={"helpfulness": 1.0},
    ))
    problem = PROBLEMS[params.problem]
    item = world.add(Entity(
        id="problem_item",
        kind="thing",
        type=problem.id,
        label=problem.title,
        phrase=problem.title,
        owner=hero.id,
        caretaker=caretaker.id,
    ))
    world.facts.update(hero=hero, caretaker=caretaker, sidekick=sidekick, item=item, problem=problem)
    return world


def _tall_tale_opening(world: World) -> None:
    f = world.facts
    hero, sidekick, problem = f["hero"], f["sidekick"], f["problem"]
    world.say(
        f"Once, in {world.setting.place}, there was a child named {hero.id} who could build a fort "
        f"faster than a summer wind could rattle the corn."
    )
    world.say(
        f"By {hero.pronoun('possessive')} side loped {sidekick.id}, a basenji so quick and keen-eyed "
        f"it looked like the moon had taught it to think."
    )
    world.say(
        f"That day they found {problem.title}, and the trouble had a plain face but a sly grin."
    )


def _problem_builds(world: World) -> None:
    f = world.facts
    hero, caretaker, problem, item = f["hero"], f["caretaker"], f["problem"], f["item"]
    if problem.id == "caffeine":
        world.say(
            f"{hero.id} wanted to sip the coffee because it smelled rich as a thundercloud, "
            f"but the grown-up lifted a hand and said, "
            f"\"That is a caution drink, not a child drink.\""
        )
        world.say(
            f"{hero.id} stared anyway, and the basenji wagged like a metronome, as if it too could hear "
            f"the little cup calling for trouble."
        )
        item.memes["danger"] = 1.0
        hero.memes["want"] = 1.0
    elif problem.id == "fort":
        world.say(
            f"The fort wall leaned like a tired fence after a storm, and when {hero.id} pressed a palm "
            f"against it, the sticks groaned like old oxen."
        )
        world.say(
            f"{caretaker.id} warned, \"A fort needs careful solving before it gets a bad tumble.\""
        )
        item.meters["unstable"] = 1.0
        hero.memes["want"] = 1.0
    else:
        world.say(
            f"{sidekick.id} spotted an open gate and started to dance toward it, ears up, feet flying, "
            f"and the whole yard turned into a question mark."
        )
        world.say(
            f"{caretaker.id} said, \"Easy now. Dogs need calm handling near open doors.\""
        )
        item.meters["escape"] = 1.0
        hero.memes["want"] = 1.0


def _attempt_fix(world: World) -> None:
    f = world.facts
    hero, caretaker, sidekick, problem, item = f["hero"], f["caretaker"], f["sidekick"], f["problem"], f["item"]
    if problem.id == "caffeine":
        world.say(
            f"{hero.id} tried a problem-solving trick and tipped the mug toward the fort wall, thinking "
            f"the wood could catch the spill."
        )
        world.say(
            f"But the coffee splashed onto the boards, and the smell grew louder than a crow at dawn."
        )
        item.meters["spilled"] = 1.0
        world.facts["bad_choice"] = "spilled onto fort"
    elif problem.id == "fort":
        world.say(
            f"{hero.id} jammed in a stick and hoped the wall would listen, but the fix was all hurry and no sense."
        )
        world.say(
            f"The wall slumped harder, and a cloud of cracked twigs made the fort look older than a barn cat."
        )
        item.meters["worse"] = 1.0
        world.facts["bad_choice"] = "bad brace"
    else:
        world.say(
            f"{hero.id} shouted the basenji's name and opened the gate wider so it would come back quickly."
        )
        world.say(
            f"That was poor thinking, because the basenji shot through the opening like a popped cork."
        )
        item.meters["escaped"] = 1.0
        world.facts["bad_choice"] = "opened gate wider"


def _bad_ending(world: World) -> None:
    f = world.facts
    hero, caretaker, sidekick, problem, item = f["hero"], f["caretaker"], f["sidekick"], f["problem"], f["item"]
    if problem.id == "caffeine":
        world.say(
            f"The grown-up had to snatch the mug away, dump the rest into the dirt, and fetch water, "
            f"while {hero.id} got twitchy and wide-eyed."
        )
        world.say(
            f"By sunset the fort smelled like a coffee shop in a storm, the basenji was sneezing, "
            f"and nobody felt sleepy enough to laugh."
        )
        world.facts["ending"] = "jittery and spoiled"
    elif problem.id == "fort":
        world.say(
            f"The wall gave a final sigh and fell inward, leaving {hero.id} with scratched knees and a fort "
            f"that looked like a broken tooth."
        )
        world.say(
            f"{caretaker.id} had to sort the mess, and the basenji sat beside the wreckage with a nose full of dust."
        )
        world.facts["ending"] = "collapsed and broken"
    else:
        world.say(
            f"The basenji dashed out into the lane, the grown-up had to chase it, and {hero.id} stood in the yard "
            f"holding an empty leash like a bad surprise."
        )
        world.say(
            f"When the dog came back muddy and triumphant, the fort floor was tracked full of pawprints, "
            f"and the easy fix had become a caution tale."
        )
        world.facts["ending"] = "escaped and muddy"


def tell_story(params: StoryParams) -> World:
    world = _build_world(params)
    _tall_tale_opening(world)
    world.para()
    _problem_builds(world)
    world.para()
    _attempt_fix(world)
    world.para()
    _bad_ending(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.facts["problem"]
    h = world.facts["hero"]
    return [
        f"Write a tall tale for a child who finds {p.title} near a fort and must solve the problem carefully.",
        f"Tell a cautionary story about {h.id}, a basenji, and a bad fix that makes trouble worse.",
        f"Create a short story with a fort, caffeine, and a basenji, ending in a bad outcome after a mistaken solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, caretaker, sidekick, problem = f["hero"], f["caretaker"], f["sidekick"], f["problem"]
    return [
        QAItem(
            question=f"Who was the story mainly about?",
            answer=f"The story was mainly about {hero.id}, with help from {sidekick.id} the basenji and warnings from {caretaker.id}.",
        ),
        QAItem(
            question=f"What trouble did {hero.id} find?",
            answer=f"{hero.id} found {problem.title}, and it was dangerous because {problem.danger}.",
        ),
        QAItem(
            question=f"What should have been done instead of the bad fix?",
            answer=f"They should have chosen the careful fix: {problem.fix}. That would have matched the caution that {problem.caution}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    problem = f["problem"]
    return [
        QAItem(
            question="What is a fort?",
            answer="A fort is a small shelter or play space made from walls, blankets, boards, or whatever sturdy things are nearby.",
        ),
        QAItem(
            question="What is caffeine?",
            answer="Caffeine is a stimulant found in coffee and some other drinks. It can make people feel extra awake.",
        ),
        QAItem(
            question="What is a basenji?",
            answer="A basenji is a dog breed known for being quick, alert, and very clever.",
        ),
        QAItem(
            question=f"Why is {problem.caution_tag} a caution topic here?",
            answer=f"Because {problem.caution}, and this story shows what can go wrong when that warning is ignored.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
problem(caffeine).
problem(fort).
problem(basenji).

caution(caffeine).
caution(fort).
caution(basenji).

bad_end(caffeine) :- problem(caffeine).
bad_end(fort) :- problem(fort).
bad_end(basenji) :- problem(basenji).

story_feature(problem_solving).
story_feature(cautionary).
story_feature(bad_ending).

compatible_story(P) :- problem(P), caution(P), bad_end(P).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("feature", "problem_solving"),
        asp.fact("feature", "cautionary"),
        asp.fact("feature", "bad_ending"),
        asp.fact("place", pid) for pid in SETTINGS
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/1."))
    asp_set = set(asp.atoms(model, "compatible_story"))
    py_set = {("caffeine",), ("fort",), ("basenji",)}
    if asp_set != py_set:
        print("MISMATCH between ASP and Python:")
        print("ASP:", sorted(asp_set))
        print("PY :", sorted(py_set))
        return 1
    print(f"OK: ASP/Python parity ({len(py_set)} compatible story kinds).")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: fort, caffeine, basenji.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caretaker", choices=["mother", "father"])
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
    place = args.place or rng.choice(list(SETTINGS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_type = gender
    caretaker = args.caretaker or rng.choice(["mother", "father"])
    hero_name = args.name or rng.choice(
        ["Ada", "June", "Milo", "Ruby", "Hank", "Nell", "Otis", "Pippa"]
    )
    sidekick = args.sidekick or rng.choice(
        ["Dot", "Zip", "Bramble", "Scout", "Penny", "Whistle"]
    )
    return StoryParams(
        place=place,
        problem=problem,
        hero_name=hero_name,
        hero_type=hero_type,
        caretaker_type=caretaker,
        sidekick_name=sidekick,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print(asp_program("#show compatible_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("fort", "caffeine", "Ada", "girl", "mother", "Scout"),
            StoryParams("backyard", "basenji", "Milo", "boy", "father", "Zip"),
            StoryParams("treehouse", "fort", "Ruby", "girl", "mother", "Bramble"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
