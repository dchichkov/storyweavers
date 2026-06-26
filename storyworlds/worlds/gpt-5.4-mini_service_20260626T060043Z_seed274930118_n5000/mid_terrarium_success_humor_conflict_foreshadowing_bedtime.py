#!/usr/bin/env python3
"""
A small bedtime storyworld about a child, a tiny terrarium, and a mid-task
success that is foreshadowed, funny, and conflict-tinged.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

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
    place: str = "the bedroom"
    setting_detail: str = "soft lamp light and a quiet shelf"


@dataclass
class Goal:
    verb: str
    gerund: str
    success_image: str
    mess: str = "soil"
    keyword: str = "terrarium"


@dataclass
class Item:
    label: str
    phrase: str
    type: str
    plural: bool = False


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


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    helper: str
    creature: str
    goal: str
    seed: Optional[int] = None


SETTINGS = {
    "bedroom": Setting(place="the bedroom", setting_detail="soft lamp light and a tidy shelf"),
    "nursery": Setting(place="the nursery", setting_detail="a rocking chair and a tiny night-light"),
    "sunroom": Setting(place="the sunroom", setting_detail="warm glass and sleepy curtains"),
}

GOALS = {
    "water": Goal(
        verb="water the terrarium",
        gerund="watering the terrarium",
        success_image="the moss looked glossy and happy",
        mess="spill",
        keyword="terrarium",
    ),
    "trim": Goal(
        verb="trim the terrarium plant",
        gerund="trimming the little plant",
        success_image="the little plant stood neat and bright",
        mess="snip",
        keyword="terrarium",
    ),
    "clean": Goal(
        verb="clean the terrarium glass",
        gerund="polishing the glass",
        success_image="the glass shone like a tiny window",
        mess="drip",
        keyword="terrarium",
    ),
}

ITEMS = {
    "glass": Item(label="glass jar", phrase="a round glass jar terrarium", type="jar"),
    "plant": Item(label="moss plant", phrase="a tiny moss plant", type="plant"),
    "stone": Item(label="blue pebble", phrase="a blue pebble with a moonlike shine", type="stone"),
}

HUMOR_BEATS = [
    "a sleepy spider had tied itself in a tiny bow,
",
    "the smallest snail looked like it was guarding a castle,
",
    "one pebble kept rolling into the same silly corner,
",
]

TRAITS = ["curious", "gentle", "patient", "mischievous", "brave"]
HELPERS = ["mother", "father", "grandmother", "grandfather"]
CREATURES = ["snail", "spider", "sprout", "moss"]
NAMES_GIRL = ["Mia", "Luna", "Nora", "Ivy", "Ella", "Zoe"]
NAMES_BOY = ["Theo", "Finn", "Leo", "Ben", "Noah", "Max"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime terrarium storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=HELPERS)
    ap.add_argument("--helper", choices=["cat", "teddy", "owl"])
    ap.add_argument("--creature", choices=CREATURES)
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
    if args.gender == "girl":
        name = args.name or rng.choice(NAMES_GIRL)
    elif args.gender == "boy":
        name = args.name or rng.choice(NAMES_BOY)
    else:
        gender = rng.choice(["girl", "boy"])
        name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
        args.gender = gender
    return StoryParams(
        name=name,
        gender=args.gender,
        parent=args.parent or rng.choice(HELPERS),
        helper=args.helper or rng.choice(["cat", "teddy", "owl"]),
        creature=args.creature or rng.choice(CREATURES),
        goal=args.goal or rng.choice(list(GOALS)),
    )


def _seed_word(world: World) -> str:
    return "mid terrarium success"


def tell(params: StoryParams) -> World:
    setting = SETTINGS["bedroom"]
    goal = GOALS[params.goal]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name, kind="character", type=params.gender,
        traits=["little", "sleepy", "kind"],
    ))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    helper = world.add(Entity(id="helper", kind="thing", type=params.helper, label=f"the {params.helper}"))
    terrarium = world.add(Entity(id="terrarium", type="terrarium", label="terrarium", phrase="a tiny terrarium"))
    creature = world.add(Entity(id="creature", type=params.creature, label=params.creature))

    hero.memes["hope"] = 1
    terrarium.meters["dry"] = 1
    terrarium.meters["tidy"] = 1

    world.say(
        f"At bedtime, {hero.id} sat beside {hero.pronoun('possessive')} little terrarium under {setting.setting_detail}."
    )
    world.say(
        f"{hero.id} liked the quiet work of {goal.gerund}, and {hero.pronoun('possessive')} {params.helper} helper waited nearby like a tiny audience."
    )
    world.say(
        f"Inside the glass, a {creature.label} blinked slowly, which made {hero.id} smile because it looked very serious about being small."
    )

    world.para()
    world.say(
        f"Then {parent.label} warned, \"Careful with the {goal.keyword}; if it spills, bedtime will turn into a little puddle parade.\""
    )
    hero.memes["conflict"] += 1
    hero.memes["defiance"] += 1
    world.say(
        f"{hero.id} wanted to keep going anyway, but {helper.label} had already been foreshadowing trouble by leaning exactly where the cup might tip."
    )
    world.say(
        f"For a moment, even the {creature.label} seemed to stare at the rim as if it knew a funny mistake was trying to sneak in."
    )

    world.para()
    hero.meters["carefulness"] = 1
    terrarium.meters["mess"] += 1
    world.say(
        f"Instead of rushing, {hero.id} held the cup with both hands and moved it one slow inch at a time."
    )
    world.say(
        f"The tricky part came in the middle, when the cup wobbled and everybody gasped, but {hero.id} steadied it and the water stayed put."
    )
    world.say(
        f"That was the mid-terrarium success: the plant was safe, the glass stayed clean, and the whole room let out a tiny laugh."
    )
    world.say(
        f"{goal.success_image}, and the {params.helper} sat exactly where it could not cause any more trouble."
    )

    world.para()
    hero.memes["joy"] += 1
    hero.memes["conflict"] = 0
    world.say(
        f"{hero.id} grinned, {parent.label} kissed {hero.pronoun('possessive')} forehead, and the bedtime job was done."
    )
    world.say(
        f"At the end, {hero.id} tucked the terrarium back on the shelf, where it glowed like a little night garden and promised a calmer morning."
    )

    world.facts.update(hero=hero, parent=parent, helper=helper, terrarium=terrarium, creature=creature, goal=goal, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a small child about a {f["goal"].keyword} that ends in a gentle success.',
        f"Tell a cozy story where {f['hero'].id} must {f['goal'].verb} without making a mess, even though a helper keeps causing a little conflict.",
        f'Write a short, funny bedtime tale that includes the phrase "mid terrarium success".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, goal, terrarium = f["hero"], f["parent"], f["goal"], f["terrarium"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to do at bedtime?",
            answer=f"{hero.id} was trying to {goal.verb} beside the terrarium.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the terrarium?",
            answer=f"{parent.label.capitalize()} worried because a spill could make bedtime messy and turn the terrarium work into a puddle parade.",
        ),
        QAItem(
            question=f"What showed that the story had a happy success?",
            answer=f"The terrarium stayed safe, the water stayed put, and {goal.success_image}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a terrarium?",
            answer="A terrarium is a little container garden, often made of glass, where small plants or tiny creatures can live.",
        ),
        QAItem(
            question="Why can a bedtime job be funny?",
            answer="A bedtime job can be funny when a helper, a plant, or a tiny creature makes the work feel a little silly.",
        ),
        QAItem(
            question="What does foreshadowing mean in a story?",
            answer="Foreshadowing is when a story gives a small clue that something important or surprising might happen soon.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for gid, g in GOALS.items():
        lines.append(asp.fact("goal", gid))
        lines.append(asp.fact("verb", gid, g.verb))
        lines.append(asp.fact("success", gid, g.success_image))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    for c in CREATURES:
        lines.append(asp.fact("creature", c))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S, G, H, C) :- setting(S), goal(G), helper(H), creature(C).
#show valid_story/4.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    py_set = {(s, g, h, c) for s in SETTINGS for g in GOALS for h in HELPERS for c in CREATURES}
    if clingo_set != py_set:
        print("MISMATCH between ASP and Python.")
        print("only in ASP:", sorted(clingo_set - py_set))
        print("only in Python:", sorted(py_set - clingo_set))
        return 1
    print(f"OK: ASP matches Python ({len(py_set)} combinations).")
    return 0


def explain_rejection() -> str:
    return "(No story: this bedtime terrarium world expects a calm, small story with a real conflict and a gentle success.)"


def valid_params(args: argparse.Namespace) -> bool:
    return True


def resolve_all(args: argparse.Namespace) -> list[StoryParams]:
    rng = random.Random(args.seed if args.seed is not None else 0)
    params = []
    for i, s in enumerate(SETTINGS):
        for g in GOALS:
            p = StoryParams(
                name=rng.choice(NAMES_GIRL + NAMES_BOY),
                gender=rng.choice(["girl", "boy"]),
                parent=rng.choice(HELPERS),
                helper=rng.choice(["cat", "teddy", "owl"]),
                creature=rng.choice(CREATURES),
                goal=g,
                seed=(args.seed or 0) + i,
            )
            params.append(p)
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid stories.")
        for s in stories[:20]:
            print(s)
        return

    samples: list[StorySample] = []
    if args.all:
        for p in resolve_all(args):
            samples.append(generate(p))
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
