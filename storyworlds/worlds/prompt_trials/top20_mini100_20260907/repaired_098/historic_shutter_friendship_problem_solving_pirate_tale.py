#!/usr/bin/env python3
"""A pirate tale about a historic shutter, friendship, and problem solving."""

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

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    name: str
    role: str
    species: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Problem:
    shutter: str
    risk: str
    clue: str
    cause: str
    fix: str
    ending_image: str
    lesson: str


@dataclass
class StoryParams:
    seed: Optional[int] = None
    harbor_name: str = "Blue Lantern Harbor"
    ship_name: str = "The Paper Gull"
    captain_name: str = "Mara"
    captain_species: str = "parrot"
    friend_name: str = "Pip"
    friend_species: str = "otter"
    shutter_kind: str = "historic shutter"
    route: str = "clue_first"
    problem_key: str = "stuck_shutter"


@dataclass
class World:
    harbor: Place
    ship: Place
    captain: Character
    friend: Character
    problem: Problem
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


HARBORS = [
    "Blue Lantern Harbor",
    "Old Shell Harbor",
    "Sailmaker's Bay",
]

SHIPS = [
    "The Paper Gull",
    "The Lantern Wake",
    "The Salt Petrel",
]

CAPTAINS = [
    ("Mara", "parrot"),
    ("Jory", "cat"),
    ("Nessa", "crow"),
]

FRIENDS = [
    ("Pip", "otter"),
    ("Milo", "seal"),
    ("Bree", "mouse"),
]

PROBLEMS = {
    "stuck_shutter": Problem(
        shutter="a historic shutter on the captain's chart room",
        risk="rain could soak the old maps and wet the lighthouse notes",
        clue="salt dust gathered only on one hinge",
        cause="a rope knot had wedged the shutter arm against the frame",
        fix="untied the rope, oiled the hinge, and tested the shutter open and shut",
        ending_image="the shutter swung wide while the maps stayed dry in the lamp glow",
        lesson="good friends can turn a tight problem into a safe solution by looking closely and helping together",
    ),
    "rattling_shutter": Problem(
        shutter="a historic shutter over the ship's small side window",
        risk="the rattling could wake the crew and scare the gulls from the rigging",
        clue="the sound stopped whenever the sail line went slack",
        cause="a loose sail tie was tapping the shutter frame in the wind",
        fix="retied the sail line, padded the frame with cloth, and checked the window in the breeze",
        ending_image="the shutter rested quiet while a gull perched peacefully on the rail",
        lesson="shared problem solving works best when every clue is tested one safe step at a time",
    ),
    "stained_shutter": Problem(
        shutter="a historic shutter in the harbor museum cabin",
        risk="a dark stain might mean damp was creeping into the old wood",
        clue="the stain looked brightest when the lamp moved near the latch",
        cause="polish from a lantern stand had rubbed off onto the shutter edge",
        fix="wiped the wood clean, moved the lantern stand away, and checked the cabin wall for leaks",
        ending_image="the shutter shone warm and clean beside the dry museum map",
        lesson="friends solve a problem faster when they share what they see instead of guessing alone",
    ),
}

ROUTES = (
    "clue_first",
    "dialogue_first",
    "storm_first",
    "friend_first",
    "map_first",
    "quiet_first",
    "question_first",
    "harbor_first",
)

ASP_RULES = r"""
friendship(A,B) :- crew(A), crew(B), helps(A,B), helps(B,A), A != B.
problem_solved(P) :- problem(P), cause(P,_), fix(P,_).
good_story :- friendship(_, _), problem_solved(_).
"""


def problem_id(key: str) -> str:
    return "problem_" + "".join(ch if ch.isalnum() else "_" for ch in key.lower()).strip("_")


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("crew", "captain"),
        asp.fact("crew", "friend"),
        asp.fact("helps", "captain", "friend"),
        asp.fact("helps", "friend", "captain"),
    ]
    for key, prob in PROBLEMS.items():
        pid = problem_id(key)
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("cause", pid, prob.cause))
        lines.append(asp.fact("fix", pid, prob.fix))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show problem_solved/1."))
    asp_solved = set(asp.atoms(model, "problem_solved"))
    py_solved = {(problem_id(key),) for key in PROBLEMS}
    if asp_solved != py_solved:
        print("MISMATCH between clingo and python reasoning.")
        print("clingo:", sorted(asp_solved))
        print("python:", sorted(py_solved))
        return 1
    sample = generate(resolve_params(argparse.Namespace(seed=7, harbor=None, ship=None, captain=None, friend=None, problem=None, route=None), random.Random(7)))
    if not sample.story or " " not in sample.story:
        print("Generated story failed quality gate.")
        return 1
    print(f"OK: clingo gate matches python reasoning and story generation works ({len(py_solved)} problems).")
    return 0


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(str(v) for v in (
        params.seed, params.harbor_name, params.ship_name, params.captain_name,
        params.captain_species, params.friend_name, params.friend_species,
        params.shutter_kind, params.route, params.problem_key,
    ))
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def build_world(params: StoryParams) -> World:
    if params.problem_key not in PROBLEMS:
        raise StoryError(f"Unknown problem key: {params.problem_key}")
    problem = PROBLEMS[params.problem_key]
    harbor = Place(name=params.harbor_name, kind="harbor")
    ship = Place(name=params.ship_name, kind="ship")
    captain = Character(name=params.captain_name, role="captain", species=params.captain_species)
    friend = Character(name=params.friend_name, role="friend", species=params.friend_species)
    return World(harbor=harbor, ship=ship, captain=captain, friend=friend, problem=problem)


def tell_story(world: World, params: StoryParams) -> None:
    rng = story_rng(params)
    c, f, h, s, p = world.captain, world.friend, world.harbor, world.ship, world.problem

    openings = {
        "clue_first": f"At {h.name}, the crew found that {p.shutter}. {c.name}, the {c.species} captain of {s.name}, knew a hard rain was coming.",
        "dialogue_first": f'"That shutter will not budge," said {c.name}. {f.name} the {f.species} friend frowned and pointed toward the old wood: {p.shutter}.',
        "storm_first": f"Clouds rolled over {h.name}, and the wind tugged at {s.name}. Before the storm could strike, {c.name} saw that {p.shutter}.",
        "friend_first": f"{f.name} was the sort of friend who noticed small troubles before they grew large. At {h.name}, {f.name} spotted that {p.shutter}.",
        "map_first": f"On a damp little map of {s.name}, {c.name} had marked the chart room and the old window. Then the crew saw that {p.shutter}.",
        "quiet_first": f"The harbor had gone quiet, except for one stubborn creak. It came from the place where {p.shutter}.",
        "question_first": f'"What is making the old shutter trouble us?" asked {c.name} at {h.name}. The answer seemed to hide inside {p.shutter}.',
        "harbor_first": f"{h.name} smelled of salt and tar, and {s.name} rocked in the tide. In the captain's room, {p.shutter}.",
    }
    world.say(openings[params.route])
    world.say(rng.choice([
        f"The risk was plain: {p.risk}.",
        f"Nobody wanted to leave the problem alone, because {p.risk}.",
        f"{f.name} said, \"We can fix it if we do not rush.\"",
        f"{c.name} answered, \"Then we look, then we test, then we mend.\"",
    ]))
    world.say(rng.choice([
        f'"I will hold the lantern," said {f.name}. "{c.name}, you look for the clue."',
        f'"I am brave enough for careful work," said {f.name}, and {c.name} nodded.',
        f'{c.name} smiled. "A good friend does not grab the first answer."',
        f'{f.name} tapped the frame. "Let us solve it together, captain."',
    ]))

    world.para()
    world.say(f"First, {c.name} checked the shutter by hand.")
    world.say(rng.choice([
        f"That did not solve it, because {p.clue}.",
        f"The first guess was wrong; {p.clue}.",
        f"Even after a careful push, the shutter stayed stuck, and {p.clue}.",
        f'"No storm can be blamed yet," said {c.name}, because {p.clue}.',
    ]))
    world.say(rng.choice([
        f"Then {f.name} noticed the real cause: {p.cause}.",
        f"Together they found the true answer: {p.cause}.",
        f'"Look there," said {f.name}. It was clear that {p.cause}.',
        f"The clue and the cause fit neatly once they saw that {p.cause}.",
    ]))
    world.say(f"So the old rumor of danger was only a small puzzle. The real trouble was easy to name: {p.cause}.")

    world.para()
    world.say(rng.choice([
        f"{c.name} and {f.name} worked side by side and {p.fix}.",
        f"With careful hands, the two friends {p.fix}.",
        f"{f.name} steadied the lantern while {c.name} {p.fix}.",
        f'"That is better," said {c.name}, after they {p.fix}.',
    ]))
    c.memes["relief"] = 1
    f.memes["pride"] = 1
    c.memes["friendship"] = 1
    f.memes["friendship"] = 1
    c.meters["repairs"] = 1
    world.say(rng.choice([
        f"They tested the shutter twice more, and each time it moved the way it should.",
        f"The captain and friend listened for a clean click, and at last they heard one.",
        f"They opened and closed it in the breeze until the wood answered with a smooth swing.",
        f"The repair held firm, which made both pirates grin.",
    ]))

    world.para()
    world.say(rng.choice([
        f"In the end, {p.ending_image}.",
        f"By the time the rain began, {p.ending_image}.",
        f"The night felt safer because {p.ending_image}.",
        f"When the harbor bells rang, {p.ending_image}.",
    ]))
    world.say(rng.choice([
        f"{c.name} said, \"A problem is easier with a friend beside you.\"",
        f"{f.name} laughed, \"And a careful clue is worth more than a hurried guess.\"",
        f"{c.name} added, \"That was good problem solving, mate.\"",
        f"{f.name} answered, \"Aye, and a kind crew makes the work lighter.\"",
    ]))

    world.facts.update(
        problem=p,
        harbor=h,
        ship=s,
        captain=c,
        friend=f,
        solved=True,
        lesson=p.lesson,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["problem"]
    return [
        f"Write a pirate tale about {world.facts['captain'].name} and {world.facts['friend'].name} at {world.facts['harbor'].name}, where {p.shutter} needs fixing.",
        f"Tell a child-facing story with a historic shutter, friendship, and problem solving, ending on: {p.ending_image}.",
        f"Make the crew solve the problem by discovering that {p.cause} and then {p.fix}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c, f, h, s, p = world.facts["captain"], world.facts["friend"], world.facts["harbor"], world.facts["ship"], world.facts["problem"]
    return [
        QAItem(
            question=f"What problem did {c.name} and {f.name} find at {h.name}?",
            answer=f"They found that {p.shutter}. That mattered because {p.risk}.",
        ),
        QAItem(
            question="What clue helped the crew move past their first guess?",
            answer=f"The clue was that {p.clue}. It showed they needed to look again.",
        ),
        QAItem(
            question="What was the real cause of the trouble?",
            answer=f"The real cause was that {p.cause}. That explained why the shutter would not work right.",
        ),
        QAItem(
            question="How did the friends solve the problem?",
            answer=f"They {p.fix}. They worked together and tested the shutter until it was safe.",
        ),
        QAItem(
            question="What did the ending show had changed?",
            answer=f"It showed that {p.ending_image}. The ship ended in a safer and calmer state.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a hinged cover or panel that can open and close a window or opening.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means noticing a trouble, checking clues, and choosing a fix that actually matches the cause.",
        ),
        QAItem(
            question="How can friendship help in a story?",
            answer="Friends can share the work, notice different clues, and encourage one another to keep going carefully.",
        ),
        QAItem(
            question="Why do old or historic things need gentle care?",
            answer="Historic things can be fragile, so people should test and repair them carefully to keep them from breaking.",
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
    ap = argparse.ArgumentParser(description="Pirate tale: historic shutter, friendship, and problem solving.")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--harbor")
    ap.add_argument("--ship")
    ap.add_argument("--captain")
    ap.add_argument("--friend")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    harbor_name = args.harbor or rng.choice(HARBORS)
    ship_name = args.ship or rng.choice(SHIPS)
    captain_name, captain_species = rng.choice(CAPTAINS)
    friend_name, friend_species = rng.choice(FRIENDS)
    problem_key = rng.choice(list(PROBLEMS))
    route = rng.choice(ROUTES)
    return StoryParams(
        seed=args.seed,
        harbor_name=harbor_name,
        ship_name=ship_name,
        captain_name=args.captain or captain_name,
        captain_species=captain_species,
        friend_name=args.friend or friend_name,
        friend_species=friend_species,
        shutter_kind="historic shutter",
        route=route,
        problem_key=problem_key,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in (world.harbor, world.ship, world.captain, world.friend):
        lines.append(f"{entity.name}: meters={entity.meters} memes={entity.memes}")
    lines.append(
        f"problem: shutter={world.problem.shutter!r} risk={world.problem.risk!r} "
        f"clue={world.problem.clue!r} cause={world.problem.cause!r}"
    )
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n== prompts ==")
        for i, prompt in enumerate(sample.prompts, 1):
            print(f"{i}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show problem_solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show problem_solved/1."))
        print(sorted(set(asp.atoms(model, "problem_solved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = 3 if args.all else args.n
    samples: list[StorySample] = []
    for i in range(count):
        local_args = argparse.Namespace(**vars(args))
        local_args.seed = base_seed + i
        params = resolve_params(local_args, random.Random(base_seed + i))
        params.seed = base_seed + i
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
