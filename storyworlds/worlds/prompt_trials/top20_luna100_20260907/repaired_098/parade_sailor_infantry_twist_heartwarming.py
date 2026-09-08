#!/usr/bin/env python3
"""A heartwarming parade story about a sailor, infantry friends, and a kind twist."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class ParadePlan:
    feature: str
    worry: str
    clue: str
    truth: str
    brave_action: str
    repair: str
    lesson: str
    ending: str
    solved: bool = False


@dataclass
class StoryParams:
    seed: Optional[int] = None
    parade_name: str = "the harbor parade"
    sailor_name: str = "Luna"
    sailor_species: str = "girl"
    infantry_name: str = "Mara"
    infantry_species: str = "woman"
    feature: str = "lost_signal_flag"
    route: str = "morning"


@dataclass
class World:
    parade: Place
    pier: Place
    sailor: Person
    infantry: Person
    plan: ParadePlan
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PARADES = {
    "the harbor parade": Place("the harbor parade", "parade route"),
    "the lantern parade": Place("the lantern parade", "parade route"),
    "the riverside parade": Place("the riverside parade", "parade route"),
}

FEATURES = {
    "lost_signal_flag": ParadePlan(
        feature="the blue signal flag was missing",
        worry="the sailor could not lead the boats into the safe harbor turn",
        clue="a blue thread clung to the old welcome banner",
        truth="the missing flag had been sewn into a small welcome pennant for a homesick sailor",
        brave_action="told the parade captain that the flag was gone instead of pretending everything was ready",
        repair="unpicked the blue flag from the welcome pennant and stitched its edge before raising it",
        lesson="a plan can change when kindness reveals a more important need",
        ending="the restored blue flag waved above the boats while the homesick sailor smiled from the pier",
    ),
    "quiet_drum": ParadePlan(
        feature="the infantry drum had fallen silent",
        worry="the marching group might lose its steady pace",
        clue="a tiny wooden peg lay beside the drum strap",
        truth="the peg had slipped loose when the drummer used the drum to carry a child's fallen toy",
        brave_action="paused the parade and admitted that the drum needed attention",
        repair="tightened the strap, returned the toy, and tested the beat with gentle taps",
        lesson="stopping briefly can help everyone move safely together",
        ending="the drum began a warm steady beat as the child marched beside the infantry",
    ),
    "crooked_banner": ParadePlan(
        feature="the welcome banner hung crooked",
        worry="the parade might look unready for the waiting families",
        clue="a bright ribbon was tied around one lower corner",
        truth="a young helper had tied the banner down so a gust would not strike a sleeping baby",
        brave_action="asked why the banner had changed before pulling at its knots",
        repair="kept the ribbon as a safe lower tie and straightened the banner with a second line",
        lesson="careful questions can uncover kindness hidden inside a mistake",
        ending="the banner stood straight while its lower ribbon fluttered safely beside the baby carriage",
    ),
    "empty_chair": ParadePlan(
        feature="one chair stood empty at the reviewing stand",
        worry="an honored guest might feel forgotten",
        clue="a paper shell rested on the chair seat",
        truth="the chair had been carried to the shade for an elderly sailor resting nearby",
        brave_action="left the formation to search respectfully for the missing guest",
        repair="moved the chair into the shade and made a clear place for the guest to watch",
        lesson="a parade honors people best when it notices what they need",
        ending="the old sailor watched from the cool chair and lifted a trembling hand in salute",
    ),
    "missing_ribbon": ParadePlan(
        feature="the infantry captain's red ribbon was missing",
        worry="the captain might feel unseen after years of service",
        clue="red fibers brightened the handle of a child's small wagon",
        truth="the ribbon had been given to a frightened child who needed something brave to hold",
        brave_action="searched gently instead of blaming the busy parade helpers",
        repair="returned the ribbon only after making the child a new red streamer",
        lesson="honor grows when it is shared rather than guarded",
        ending="the captain wore the ribbon again while the child waved a matching streamer",
    ),
}

ROUTES = ("morning", "before_music", "rain_cloud", "memory", "question_first")
SAILORS = (("Luna", "girl"), ("Nell", "woman"), ("Ivo", "boy"))
INFANTRY = (("Mara", "woman"), ("Jon", "man"), ("Suri", "girl"))


ASP_RULES = r"""
ready(P) :- parade(P), sailor(S), infantry(I), solved(P).
solved(P) :- parade_plan(P), kindness_found(P), safe_change(P).
valid_story(P) :- ready(P).
"""


def feature_id(value: str) -> str:
    return "feature_" + "".join(ch if ch.isalnum() else "_" for ch in value).strip("_")


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("parade", "parade"),
        asp.fact("sailor", "sailor"),
        asp.fact("infantry", "infantry"),
        asp.fact("parade_plan", "parade"),
        asp.fact("kindness_found", "parade"),
        asp.fact("safe_change", "parade"),
    ]
    for name in FEATURES:
        lines.append(asp.fact("feature", feature_id(name)))
    lines.append(asp.fact("solved", "parade"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/1."))
    found = set(asp.atoms(model, "solved"))
    expected = {("parade",)}
    if found == expected:
        print("OK: clingo gate matches python reasoning.")
        return 0
    print("MISMATCH between clingo and python reasoning.")
    print("clingo:", sorted(found))
    print("python:", sorted(expected))
    return 1


def story_rng(params: StoryParams) -> random.Random:
    raw = "|".join(
        str(x)
        for x in (
            params.seed,
            params.parade_name,
            params.sailor_name,
            params.sailor_species,
            params.infantry_name,
            params.infantry_species,
            params.feature,
            params.route,
        )
    )
    digest = hashlib.sha256(raw.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def build_world(params: StoryParams) -> World:
    if params.parade_name not in PARADES:
        raise StoryError(f"Unknown parade: {params.parade_name}")
    if params.feature not in FEATURES:
        raise StoryError(f"Unknown parade feature: {params.feature}")
    plan = FEATURES[params.feature]
    return World(
        parade=Place(params.parade_name, PARADES[params.parade_name].kind),
        pier=Place("the harbor pier", "pier"),
        sailor=Person(params.sailor_name, f"{params.sailor_species} sailor"),
        infantry=Person(params.infantry_name, f"{params.infantry_species} infantry member"),
        plan=ParadePlan(
            feature=plan.feature,
            worry=plan.worry,
            clue=plan.clue,
            truth=plan.truth,
            brave_action=plan.brave_action,
            repair=plan.repair,
            lesson=plan.lesson,
            ending=plan.ending,
        ),
    )


def tell_story(world: World, params: StoryParams) -> None:
    rng = story_rng(params)
    sailor, infantry, parade, plan = (
        world.sailor,
        world.infantry,
        world.parade,
        world.plan,
    )
    sailor.memes.update(kindness=1, courage=0)
    infantry.memes.update(patience=1, welcome=1)

    openings = {
        "morning": f"Morning light spilled over {parade.name}. {sailor.name}, a careful sailor, checked the route while {infantry.name} stood with the infantry near the pier.",
        "before_music": f"Before the parade music began, {sailor.name} looked from the harbor to {infantry.name}'s waiting group. Then they noticed that {plan.feature}.",
        "rain_cloud": f"A gray cloud floated above {parade.name}, but the families still gathered. {sailor.name} was more worried by one thing: {plan.feature}.",
        "memory": f"Years later, people would remember the warmest moment of {parade.name}. It began when {sailor.name} discovered that {plan.feature}.",
        "question_first": f'"How can we guide everyone safely if {plan.feature}?" asked {sailor.name}. {infantry.name} turned from the waiting infantry to listen.',
    }
    world.say(openings[params.route])
    world.say(f"The missing object mattered because {plan.worry}.")
    world.say(rng.choice([
        f'"Do we hide the problem until the music starts?" {infantry.name} asked.',
        f'"Tell me what you know," {infantry.name} said. "A parade is made of people, not just perfect lines."',
        f'"We can be proud and still ask for help," {sailor.name} replied.',
    ]))
    world.say(f"{infantry.name} kept the infantry group safely behind the rope while {sailor.name} checked the route.")

    world.para()
    world.say(f"First, {sailor.name} searched the signal box and the supply cart.")
    world.say(rng.choice([
        f"Nothing fit. The boxes were full, but the flag was not there; {plan.clue}.",
        f"The first search failed. Then {plan.clue}.",
        f'"This clue does not blame anyone," {sailor.name} said, pointing to the evidence that {plan.clue}.',
    ]))
    world.say(f"Together they followed the clue and learned the surprising truth: {plan.truth}.")
    world.say(f'"The parade can wait one minute," {infantry.name} said. "People should not have to wait for kindness."')

    world.para()
    world.say(f"{sailor.name} felt a flutter of worry but {plan.brave_action}.")
    sailor.memes["courage"] = 1
    world.say(rng.choice([
        f"Then the sailor and the infantry member {plan.repair}.",
        f"With the infantry standing watch, they {plan.repair}.",
        f'"Let us fix the real problem, not just the picture," {sailor.name} said, and they {plan.repair}.',
    ]))
    plan.solved = True
    world.parade.meters["route_ready"] = 1
    world.pier.meters["welcome_ready"] = 1
    world.facts.update(
        cause=plan.truth,
        repair=plan.repair,
        lesson=plan.lesson,
        ending=plan.ending,
        solved=True,
    )

    world.para()
    world.say(f'"What did we learn?" {infantry.name} asked.')
    world.say(f"{sailor.name} smiled. \"{plan.lesson.capitalize()}.\"")
    world.say(f"As the music began, {plan.ending}. The sailor and the infantry marched more slowly, so every smile could keep up.")


def generation_prompts(world: World) -> list[str]:
    p = world.plan
    return [
        f"Write a heartwarming parade story about {world.sailor.name}, a sailor, and {world.infantry.name}, an infantry member, solving this problem: {p.feature}.",
        f"Include a twist revealing that {p.truth}. Show the characters changing the parade plan with kindness.",
        f"End with this warm image: {p.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.plan
    return [
        QAItem(
            question=f"What problem did {world.sailor.name} discover at {world.parade.name}?",
            answer=f"{world.sailor.name} discovered that {p.feature}. It mattered because {p.worry}.",
        ),
        QAItem(
            question="What was the surprising twist?",
            answer=f"The twist was that {p.truth}. The missing item was connected to an act of kindness.",
        ),
        QAItem(
            question=f"How did {world.sailor.name} show courage?",
            answer=f"{world.sailor.name} {p.brave_action}. That honest choice let everyone solve the real problem safely.",
        ),
        QAItem(
            question=f"How did the sailor and infantry member repair the situation?",
            answer=f"They {p.repair}. This allowed the parade to continue while caring for the people nearby.",
        ),
        QAItem(
            question="What lesson did the characters learn?",
            answer=f"They learned that {p.lesson}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parade?",
            answer="A parade is an organized procession in which people, music, flags, or vehicles move along a route for others to watch.",
        ),
        QAItem(
            question="What does a sailor do?",
            answer="A sailor works on or around boats and helps travel safely on water.",
        ),
        QAItem(
            question="What is infantry?",
            answer="Infantry are soldiers who serve as a group on foot. In this gentle story world, they also help protect and welcome the community.",
        ),
        QAItem(
            question="Why can changing a plan be kind?",
            answer="Changing a plan can be kind when it responds to someone's real need while keeping everyone safe.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Heartwarming parade story about a sailor, infantry, and a twist."
    )
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--parade", choices=sorted(PARADES))
    parser.add_argument("--sailor-name")
    parser.add_argument("--infantry-name")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    sailor_name, sailor_species = rng.choice(SAILORS)
    infantry_name, infantry_species = rng.choice(INFANTRY)
    return StoryParams(
        seed=args.seed,
        parade_name=args.parade or rng.choice(sorted(PARADES)),
        sailor_name=args.sailor_name or sailor_name,
        sailor_species=sailor_species,
        infantry_name=args.infantry_name or infantry_name,
        infantry_species=infantry_species,
        feature=rng.choice(sorted(FEATURES)),
        route=rng.choice(ROUTES),
    )


def dump_trace(world: World) -> str:
    return "\n".join(
        [
            "--- world trace ---",
            f"parade: {world.parade.name} meters={world.parade.meters}",
            f"pier: {world.pier.name} meters={world.pier.meters}",
            f"{world.sailor.name}: meters={world.sailor.meters} memes={world.sailor.memes}",
            f"{world.infantry.name}: meters={world.infantry.meters} memes={world.infantry.memes}",
            f"plan: feature={world.plan.feature!r} solved={world.plan.solved}",
            f"cause: {world.facts.get('cause', '')!r}",
        ]
    )


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solved/1."))
        print(sorted(set(asp.atoms(model, "solved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = 3 if args.all else args.n
    samples: list[StorySample] = []
    for index in range(count):
        params = resolve_params(args, random.Random(base_seed + index))
        params.seed = base_seed + index
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
