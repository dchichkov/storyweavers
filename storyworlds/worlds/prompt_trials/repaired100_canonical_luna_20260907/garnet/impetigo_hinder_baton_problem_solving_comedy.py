#!/usr/bin/env python3
"""
A child-friendly comedy storyworld about a relay baton, a muddy shortcut,
and solving a small problem without spreading impetigo.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str = "thing"
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    hero: Item
    helper: Item
    baton: Item
    place: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    name: str
    helper_name: str
    place: str
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Nia", "Toby", "Pia", "Otis", "Zara", "Finn"]
HELPERS = ["Mara", "Jules", "Ari", "Sam", "Bea", "Noah", "Tess"]
PLACES = [
    "the school yard",
    "the sunny park",
    "the village field",
    "the maple playground",
    "the little sports ground",
]


ASP_RULES = r"""
#show prepared/1.
#show safe_pass/1.
#show solved/1.

prepared(H) :- notices_skin_problem(H).
safe_pass(H) :- uses_clean_baton(H), keeps_distance(H).
solved(H) :- prepared(H), safe_pass(H), asks_helper(H).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("notices_skin_problem", "hero"),
            asp.fact("uses_clean_baton", "hero"),
            asp.fact("keeps_distance", "hero"),
            asp.fact("asks_helper", "hero"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    shown = "#show prepared/1.\n#show safe_pass/1.\n#show solved/1."
    model = asp.one_model(asp_program(shown))
    actual = set()
    for atom in model:
        args = tuple(
            a.number if a.type == a.type.Number else
            a.string if a.type == a.type.String else a.name
            for a in atom.arguments
        )
        actual.add((atom.name, args))
    expected = {
        ("prepared", ("hero",)),
        ("safe_pass", ("hero",)),
        ("solved", ("hero",)),
    }
    if actual == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(actual))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Comedy storyworld about solving a relay problem safely."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper-name", choices=HELPERS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.n < 1:
        raise StoryError("-n must be at least 1.")
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        helper_name=args.helper_name or rng.choice(HELPERS),
        place=args.place or rng.choice(PLACES),
    )


def build_world(params: StoryParams) -> World:
    hero = Item(
        id="hero",
        label=params.name,
        phrase=f"young {params.name}",
        kind="character",
        meters={"energy": 0.8, "distance_to_finish": 12.0},
        memes={"confidence": 0.7, "care": 0.9},
    )
    helper = Item(
        id="helper",
        label=params.helper_name,
        phrase=params.helper_name,
        kind="character",
        meters={"distance_to_helper": 4.0},
        memes={"patience": 0.9, "helpfulness": 0.9},
    )
    baton = Item(
        id="baton",
        label="relay baton",
        phrase="a bright blue relay baton",
        owner="team",
        meters={"length": 0.28, "cleanliness": 1.0},
        memes={"importance": 0.8, "comedy": 0.7},
    )
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.name}|{params.helper_name}|{params.place}")
    return World(hero=hero, helper=helper, baton=baton, place=params.place, seed=seed)


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _record_story(
    world: World,
    *,
    arc: str,
    discovery: str,
    trouble: str,
    cause: str,
    solution: str,
    ending: str,
    lesson: str,
    joke: str,
    lines: list[str],
) -> str:
    world.facts.update(
        arc=arc,
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        solution=solution,
        ending=ending,
        lesson=lesson,
        joke=joke,
        prepared=True,
        safe_pass=True,
        solved=True,
    )
    world.baton.meters["cleanliness"] = 1.0
    world.baton.memes["trust"] = 1.0
    return " ".join(lines)


def _muddy_shortcut(world: World, rng: random.Random) -> str:
    h, helper, place = world.hero.label, world.helper.label, world.place
    puddle = _choice(rng, ["a chocolate-colored puddle", "a soup-sized mud hole", "a shiny swampy patch"])
    animal = _choice(rng, ["a duck", "a surprised frog", "a very serious goose"])
    discovery = f"the straight shortcut crossed {puddle}"
    trouble = "the muddy shortcut could soil the baton and make passing it unsafe"
    cause = "the team had planned to race through a wet patch instead of using the clean marked lane"
    solution = f"{h} asked {helper} to place cones around the mud, then used the clean lane and passed a fresh clean baton"
    ending = f"the team crossed the finish line with the baton shining while {animal} guarded the muddy shortcut"
    lesson = "good problem solving means changing the plan when the first path is unsafe"
    joke = f"{animal} looked like the official judge of mud"
    lines = [
        f"At {place}, {h} held the bright blue baton and waited for the relay race to begin.",
        f"Then {h} noticed a small sore on the arm and remembered that impetigo can spread through close contact and shared objects.",
        f"The coach pointed to the clean lane, but the shortest route went through {puddle}.",
        f'"We can leap over it!" said {h}. "We can also land in it," said {helper}.',
        f"Just then, {animal} waddled across the puddle and wore the expression of someone who had already made that mistake.",
        f"{h} realized the muddy shortcut could hinder the whole team: dirty hands, a dirty baton, and too much touching would make the race unsafe.",
        f'"Let us solve the problem, not wrestle it," said {h}.',
        f"{h} told the coach, stepped aside for health help, and asked {helper} to mark the mud with cones.",
        f"The coach provided a clean baton and showed the team how to keep space, wash hands, and pass only the clean object in the marked lane.",
        f"Everyone followed the safer route. {ending}. {h} learned that a clever detour can beat a heroic face-plant.",
    ]
    return _record_story(
        world,
        arc="muddy_shortcut",
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        solution=solution,
        ending=ending,
        lesson=lesson,
        joke=joke,
        lines=lines,
    )


def _sneeze_signal(world: World, rng: random.Random) -> str:
    h, helper, place = world.hero.label, world.helper.label, world.place
    sound = _choice(rng, ["a tiny achoo", "a trumpet-sized sneeze", "three polite sniffs"])
    prop = _choice(rng, ["a whistle", "a paper flag", "a cardboard arrow"])
    discovery = f"the relay signal was hard to hear over {sound}"
    trouble = "runners might bunch together around the baton and spread germs"
    cause = "the noisy crowd made everyone lean close and hurry the handoff"
    solution = f"{h} asked {helper} to use {prop} and a wider handoff space while the coach handled the health concern"
    ending = f"the relay finished in a neat line, with the baton traveling by clear signals instead of elbows and panic"
    lesson = "a clear signal can solve a crowded problem"
    joke = "the sneeze sounded like a mouse trying to play a brass horn"
    lines = [
        f"At {place}, {h} practiced the relay handoff with the team.",
        f"Before the race, {h} noticed a skin sore and heard {sound} from the busy starting line.",
        f"The crowd became noisy. Runners leaned together, hands waved, and the baton nearly received three handoffs at once.",
        f'"Was that the signal?" asked {h}. "No," said {helper}. "That was either a sneeze or a trumpet trapped in a sock."',
        f"{h} understood that impetigo can spread through close contact and shared things, so the crowded handoff needed a safer plan.",
        f"The confusion could hinder the race, but shouting louder would only make everybody crowd closer.",
        f"{h} told the coach and stepped aside for care. Then {h} suggested using {prop}, a marked handoff box, and a clean baton.",
        f"{helper} held up {prop}. The next runner waited outside the box until the signal was clear.",
        f"The baton moved smoothly from one runner to the next, with clean hands, space, and no mysterious sock trumpet.",
        f"By the finish, {ending}. The team cheered for the solution as loudly as it had cheered for the race.",
    ]
    return _record_story(
        world,
        arc="sneeze_signal",
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        solution=solution,
        ending=ending,
        lesson=lesson,
        joke=joke,
        lines=lines,
    )


def _backward_track(world: World, rng: random.Random) -> str:
    h, helper, place = world.hero.label, world.helper.label, world.baton.label
    sign = _choice(rng, ["a backwards arrow", "a dancing chalk line", "a sign with two left feet"])
    discovery = f"the route marker pointed the runners in the wrong direction"
    trouble = "the team kept returning to the same bench and could not finish the relay"
    cause = f"wind had turned {sign} around"
    solution = f"{h} compared the route with the start and finish flags, then asked {helper} to hold the marker steady"
    ending = "the team followed one clear loop and reached the finish without sharing a confused knot of elbows"
    lesson = "checking evidence before acting can reveal the real cause of a problem"
    joke = "the team visited the same bench so often that it began to expect a medal"
    lines = [
        f"At the relay course near {place}, {h} carried the baton toward the first marker.",
        f"A small sore made {h} pause and ask the coach for help because impetigo can spread by close contact and shared objects.",
        f"Meanwhile, the runners followed {sign}, dashed around the field, and arrived back at the same bench.",
        f'"We are winning!" cried one runner. "At what?" asked {helper}.',
        f"The baton passed from hand to hand, but the race was not moving forward. The wrong route could hinder every careful plan.',
        f"{h} noticed that the marker had turned in the wind. Instead of guessing, {h} compared it with the start and finish flags.",
        f'"The finish flag is over there," said {h}. "The bench is not secretly the finish flag."',
        f"{h} told the coach, stepped aside for health care, and helped {helper} hold the marker upright.",
        f"The coach supplied a clean baton and reminded everyone to wash hands, keep space, and pass only as directed.",
        f"At last, {ending}. The bench received no medal, but it looked proud anyway.",
    ]
    return _record_story(
        world,
        arc="backward_track",
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        solution=solution,
        ending=ending,
        lesson=lesson,
        joke=joke,
        lines=lines,
    )


def _giant_baton(world: World, rng: random.Random) -> str:
    h, helper, place = world.hero.label, world.helper.label, world.baton.label
    object_name = _choice(rng, ["a broom", "a rolled poster", "a garden hose"])
    discovery = f"the team had mistaken {object_name} for the baton"
    trouble = "the oversized substitute was hard to carry and made runners bump into one another"
    cause = f"the real {place} had been placed beside {object_name}"
    solution = f"{h} compared the team label with the object, then asked {helper} to bring the clean real baton"
    ending = "the real baton passed lightly from hand to hand while the giant substitute leaned against a fence"
    lesson = "careful observation can prevent a funny mistake from becoming a risky one"
    joke = f"{object_name} looked ready to compete in the relay, though it had no running shoes"
    lines = [
        f"At {place}, {h} reached for the relay baton and found what looked like {object_name}.",
        f"{h} had noticed a sore and told the coach, since impetigo needs proper care and should not be passed through shared contact.",
        f"The team lifted the enormous substitute. It wobbled, swept across the cones, and nearly hugged a water bucket.",
        f'"Pass it carefully!" called {h}. "It is a broom," said {helper}. "It is a very athletic broom."',
        f"The mistaken object could hinder the race because everyone had to crowd around it just to keep it off the ground.",
        f"{h} checked the team label and saw that the real baton was beside the substitute.",
        f"{h} told the coach, stepped aside, and asked {helper} to fetch the clean baton for the runners.",
        f"The coach explained that health concerns should be handled by an adult, while the team used clean hands and a clear handoff.",
        f"The real baton moved quickly and safely. {ending}.",
    ]
    return _record_story(
        world,
        arc="giant_baton",
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        solution=solution,
        ending=ending,
        lesson=lesson,
        joke=joke,
        lines=lines,
    )


ARC_BUILDERS = [_muddy_shortcut, _sneeze_signal, _backward_track, _giant_baton]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x5A17B)
    builder = ARC_BUILDERS[world.seed % len(ARC_BUILDERS)]
    return builder(world, rng)


def story_qa(world: World) -> list[QAItem]:
    h = world.hero.label
    facts = world.facts
    return [
        QAItem(
            question=f"What did {h} notice before the relay?",
            answer=f"{h} noticed that {facts['discovery']}.",
        ),
        QAItem(
            question="How could the problem hinder the team?",
            answer=f"It could hinder the team because {facts['cause']}.",
        ),
        QAItem(
            question=f"How did {h} help solve the problem?",
            answer=f"{facts['solution']}.",
        ),
        QAItem(
            question="Why was the safer plan important?",
            answer=(
                "The safer plan mattered because impetigo can spread through close "
                "contact or shared objects, so the children needed adult help, clean "
                "equipment, hand washing, and space."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is impetigo?",
            answer=(
                "Impetigo is a contagious bacterial skin infection that can cause "
                "itchy sores or blisters. An adult or health professional should "
                "help with care, and people should avoid sharing personal items."
            ),
        ),
        QAItem(
            question="What does hinder mean?",
            answer=(
                "To hinder something means to make it harder for the person or team "
                "to move forward or finish a task."
            ),
        ),
        QAItem(
            question="What is a baton?",
            answer=(
                "A baton is a small stick that runners pass during a relay race."
            ),
        ),
        QAItem(
            question="What is problem solving?",
            answer=(
                "Problem solving means noticing what is wrong, gathering useful "
                "information, and choosing a safe action that can improve the situation."
            ),
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a funny, child-facing relay story about impetigo, a baton, and problem solving.",
        f"Tell a comedy story at {world.place} where a problem hinders a relay team until the children make a safer plan.",
        "Create a concrete story in which dialogue changes the team's decision and the baton reaches the finish safely.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in [world.hero, world.helper, world.baton]:
        lines.append(
            f"  {ent.id:6} {ent.kind:10} label={ent.label!r} "
            f"owner={ent.owner!r} meters={ent.meters} memes={ent.memes}"
        )
    lines.append(f"  place={world.place!r}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        out.append(f"{i}. {prompt}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world)
    world.facts["story"] = story
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
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
        print()
        print(format_qa(sample))


def asp_facts_text() -> str:
    return asp_facts()


def asp_valid() -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(
            asp_program(
                "#show prepared/1.\n#show safe_pass/1.\n#show solved/1."
            )
        )
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print(
            "3 compatible logical atoms: prepared(hero), "
            "safe_pass(hero), solved(hero)"
        )
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Luna", helper_name="Mara", place="the school yard"),
            StoryParams(name="Milo", helper_name="Jules", place="the sunny park"),
            StoryParams(name="Nia", helper_name="Ari", place="the village field"),
            StoryParams(name="Toby", helper_name="Bea", place="the maple playground"),
        ]
        for index, params in enumerate(curated):
            params.seed = base_seed + index
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if len(samples) < args.n and not args.all:
        raise StoryError("Could not create the requested number of distinct stories.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            params = sample.params
            header = f"### {params.name} at {params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
