#!/usr/bin/env python3
"""The Night Lantern and the Shared Nose."""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

_ROOT = Path(__file__).resolve()
for parent in _ROOT.parents:
    if (parent / "results.py").exists():
        sys.path.insert(0, str(parent))
        break
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    label: str
    kind: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    text: str
    question: str = ""
    cause: str = ""
    result: str = ""
    speaker: str = ""


@dataclass
class StoryParams:
    child: str = "Nora"
    friend: str = "Pip"
    problem: str = "dark_path"
    solution: str = "shared_lantern"
    approach: str = "listen"
    treasure: str = "moon_moth"
    seed: int = 777


NAMES = ("Nora", "Ivo", "Lina", "Milo", "Tess", "Oren")
TREASURES = {
    "moon_moth": ("a silver moth", "blue"),
    "sleepy_fox": ("a sleepy fox", "amber"),
    "star_shell": ("a tiny star shell", "pearl"),
}
APPROACHES = ("listen", "hurry")
PROBLEMS = {
    "dark_path": "share_light",
    "thorn_gate": "share_care",
    "sleepy_friend": "share_steps",
}
SOLUTIONS = {
    "shared_lantern": "share_light",
    "folded_cloak": "share_care",
    "quiet_steps": "share_steps",
}
COMPATIBLE = {
    "dark_path": ("shared_lantern",),
    "thorn_gate": ("folded_cloak",),
    "sleepy_friend": ("quiet_steps",),
}
PROMPT = (
    "Write a gentle bedtime story about two friends sharing a small night journey, "
    "with a nose noticing an important clue and a quiet foreshadowed ending."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "child": Entity("child", params.child, "character", "cottage",
                            memes={"worry": 0.6, "trust": 0.5}),
            "friend": Entity("friend", params.friend, "character", "cottage",
                             memes={"sleepiness": 0.4, "trust": 0.5}),
            "nose": Entity("nose", f"{params.child}'s nose", "sense", "cottage",
                           meters={"scent_strength": 0.0}, memes={"curiosity": 0.8}),
            "moon": Entity("moon", "the moon", "sky", "hill",
                           meters={"light": 1.0}),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(entity) for key, entity in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question: str = "",
                cause: str = "", result: str = "") -> None:
        self.history.append(Event(kind, text, question, cause, result))

    def say(self, who: str, text: str) -> None:
        label = self.entities[who].label
        verb = "asked" if text.endswith("?") else "said"
        self.history.append(Event("speech", f'"{text}" {label} {verb}.', speaker=who))


def validate_params(params: StoryParams) -> None:
    if params.problem not in PROBLEMS:
        raise StoryError("Unknown night problem.")
    if params.solution not in SOLUTIONS:
        raise StoryError("Unknown solution.")
    if params.solution not in COMPATIBLE[params.problem]:
        raise StoryError(
            f"{params.solution!r} cannot solve {params.problem!r}; choose a compatible path."
        )
    if params.approach not in APPROACHES or params.treasure not in TREASURES:
        raise StoryError("Unknown approach or treasure.")
    if params.child == params.friend:
        raise StoryError("The two bedtime friends need different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", n) for n in (params.child, params.friend)):
        raise StoryError("Names must be simple capitalized names.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    if params.problem == "dark_path":
        world.entities["lantern"] = Entity(
            "lantern", "the little lantern", "tool", "cottage",
            meters={"fuel": 1.0, "light": 0.0}, memes={"belonging": 1.0})
    elif params.problem == "thorn_gate":
        world.entities["cloak"] = Entity(
            "cloak", "the soft blue cloak", "tool", "cottage",
            meters={"length": 2.0, "cover": 0.0}, memes={"warmth": 1.0})
    else:
        world.entities["path"] = Entity(
            "path", "the moonlit path", "place", "hill",
            meters={"stones": 4.0, "crossed": 0.0}, memes={"quiet": 0.5})
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    child = params.child
    friend = params.friend
    treasure, color = TREASURES[params.treasure]

    world.narrate(
        "opening",
        f"At bedtime, {child} and {friend} carried a small wish to the hill: "
        f"they hoped to see {treasure} before the moon climbed high. "
        f"{child}'s nose twitched at the cool night air, as if it already knew the way."
    )
    world.say("child", "Will you come with me?")
    world.say("friend", "I will, but I want us both to get home cozy.")
    world.narrate(
        "foreshadow",
        f"Far above the hill, one {color} star blinked twice and hid behind a cloud. "
        "Neither friend noticed, but the night was quietly preparing a turn."
    )

    if params.problem == "dark_path":
        if params.approach == "hurry":
            world.say("child", "The path is dark. Let's hurry before it gets darker.")
            world.narrate(
                "mistake",
                f"{child} stepped ahead, but {child}'s nose caught a sharp smell of wet pine. "
                "The familiar path bent somewhere it had not bent before."
            )
        else:
            world.say("child", "The path is dark. What does your careful listening hear?")
            world.say("friend", "I hear the creek to our left. We should not guess.")
            world.narrate(
                "clue",
                f"{child}'s nose caught wet pine and cool water. The smell told them "
                "the creek was close, even though the dark hid its silver stones."
            )
        world.say("child", "The lantern can help us both if we hold it between us.")
        world.say("friend", "Then neither of us has to walk alone.")
        world.entities["lantern"].location = "shared"
        world.entities["lantern"].meters["light"] = 1.0
        world.entities["child"].memes["trust"] = 1.0
        world.entities["friend"].memes["trust"] = 1.0
        world.narrate(
            "solution",
            f"They shared the little lantern, keeping its warm circle between their hands. "
            f"{friend} watched the stones while {child} followed the pine-scented breeze.",
            question="Why did the friends share the lantern?",
            cause="The dark hid the creek and made guessing unsafe.",
            result="The lantern lit the space between them, so both friends could walk carefully."
        )
        world.say("friend", "Look! Something pale is fluttering by the moon flower.")
        world.say("child", "My nose smells sweet flowers. We must be near the hilltop.")
        world.narrate(
            "ending",
            f"Together they found {treasure} resting on a moon flower. "
            f"They watched it beneath the {color} moonlight, then carried the lantern home "
            "with their shoulders touching.",
            question="How did they find the treasure safely?",
            cause="They used the lantern together and followed the flower scent their noses noticed.",
            result=f"They reached the moon flower and saw {treasure} without leaving either friend behind."
        )

    elif params.problem == "thorn_gate":
        if params.approach == "hurry":
            world.say("child", "I can squeeze through first.")
            world.narrate(
                "warning",
                f"{child} reached for the gate, but {child}'s nose felt the dry, dusty "
                "air trapped among the thorns. The smallest gap was not safe."
            )
        else:
            world.say("child", "My nose says the thorns are close. Should we look before touching?")
            world.say("friend", "Yes. The moon makes the sharp branches easier to see.")
        world.say("child", "We can share the cloak and cover our arms.")
        world.say("friend", "And we can take turns holding the edge away.")
        world.entities["cloak"].location = "thorn_gate"
        world.entities["cloak"].meters["cover"] = 1.0
        world.entities["child"].memes["trust"] = 1.0
        world.entities["friend"].memes["trust"] = 1.0
        world.narrate(
            "solution",
            f"They spread the soft blue cloak over the low thorns and shared its two corners. "
            "Slowly, they stepped through without pulling the branches.",
            question="Why did the friends use the cloak together?",
            cause="The narrow gate was filled with sharp thorns.",
            result="The shared cloak covered their arms while they took turns making a safe space."
        )
        world.say("friend", "There is a flutter near the moon flower.")
        world.say("child", "And my nose smells honey. The hilltop is close.")
        world.narrate(
            "ending",
            f"On the other side of the gate, {treasure} rested in the flower's pale cup. "
            f"They shared the {color} cloak on the walk home, warm as a small quiet promise.",
            question="What let them pass the thorn gate?",
            cause="They covered the thorns with the cloak and held it together.",
            result=f"They reached the flower safely and found {treasure} waiting there."
        )

    else:
        if params.approach == "hurry":
            world.say("child", "We can walk quickly, even if you are sleepy.")
            world.narrate(
                "warning",
                f"{friend} yawned, and {child}'s nose noticed the warm scent of wool. "
                "The smell reminded them that tired feet could stumble on the stones."
            )
        else:
            world.say("child", "Your eyes are drooping. What would help?")
            world.say("friend", "A slow path, and a friend who walks beside me.")
        world.say("child", "We will share the steps. One stone, then one breath.")
        world.say("friend", "You may count. I will listen.")
        world.entities["path"].meters["crossed"] = 4.0
        world.entities["child"].memes["trust"] = 1.0
        world.entities["friend"].memes["trust"] = 1.0
        world.narrate(
            "solution",
            f"They shared the journey in quiet steps. {child} counted each stone, "
            f"and {friend} rested whenever {child}'s nose found the warm wool scent.",
            question="Why did the friends slow down?",
            cause=f"{friend} was sleepy, and {child}'s nose noticed the comforting wool scent.",
            result="They crossed each stone together instead of letting tiredness make them stumble."
        )
        world.say("friend", "I see a silver flutter by the flower.")
        world.say("child", "Then we are close. Breathe in, and take one more step.")
        world.narrate(
            "ending",
            f"At the top, they found {treasure} curled beside the moon flower. "
            f"They sat together until the {color} light softened, then walked home "
            "one gentle step at a time.",
            question="How did they reach the hilltop?",
            cause="They counted the stones and rested whenever sleepiness made the path difficult.",
            result=f"They arrived together and saw {treasure} beside the moon flower."
        )

    sample = WorldSample(world, params).sample()
    check_sample(sample)
    return sample


class WorldSample:
    def __init__(self, world: World, params: StoryParams):
        self.world = world
        self.params = params

    def sample(self) -> StorySample:
        events = self.world.history
        return StorySample(
            params=self.params,
            story="\n\n".join(event.text for event in events),
            prompts=[PROMPT],
            story_qa=[
                QAItem(event.question, f"{event.cause} {event.result}")
                for event in events if event.question
            ],
            world_qa=[
                QAItem(
                    "What should friends do when a night path feels unsafe?",
                    "They should share information, choose a careful plan, and stay together."
                )
            ],
            world=self.world,
        )


def check_sample(sample: StorySample) -> None:
    world = sample.world
    speech = [e for e in world.history if e.kind == "speech"]
    if len(speech) < 2 or not all(
        any(event.speaker == actor for event in speech) for actor in ("child", "friend")
    ):
        raise StoryError("The story needs a sustained spoken exchange.")
    text = sample.story
    if "{" in text or "}" in text or "  " in text:
        raise StoryError("The story contains unresolved or doubled template text.")
    if world.entities["child"].memes["trust"] < 1 or world.entities["friend"].memes["trust"] < 1:
        raise StoryError("The friends did not complete their shared plan.")
    if not any("nose" in e.text for e in world.history):
        raise StoryError("The nose must notice a story-grounded clue.")
    if len(sample.story_qa) < 2:
        raise StoryError("The story needs grounded questions and answers.")


ASP_RULES = """
compatible(P,S) :- problem(P,N), solution(S,N).
#show compatible/2.
"""


def asp_facts() -> str:
    from asp import fact
    facts = []
    for problem, need in PROBLEMS.items():
        facts.append(fact("problem", problem, need))
    for solution, ability in SOLUTIONS.items():
        facts.append(fact("solution", solution, ability))
    return "\n".join(facts)


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "compatible"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--child")
    parser.add_argument("--friend")
    parser.add_argument("--problem", choices=tuple(PROBLEMS))
    parser.add_argument("--solution", choices=tuple(SOLUTIONS))
    parser.add_argument("--approach", choices=APPROACHES)
    parser.add_argument("--treasure", choices=tuple(TREASURES))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [
        (problem, solution)
        for problem, solutions in COMPATIBLE.items()
        for solution in solutions
        if args.problem is None or problem == args.problem
        if args.solution is None or solution == args.solution
    ]
    if not choices:
        raise StoryError("No compatible problem and solution match those options.")
    problem, solution = rng.choice(choices)
    child = args.child or rng.choice(NAMES)
    friend = args.friend or rng.choice([name for name in NAMES if name != child])
    return StoryParams(
        child=child,
        friend=friend,
        problem=problem,
        solution=solution,
        approach=args.approach or rng.choice(APPROACHES),
        treasure=args.treasure or rng.choice(tuple(TREASURES)),
        seed=args.seed,
    )


def verify() -> None:
    expected = {(p, s) for p, ss in COMPATIBLE.items() for s in ss}
    if expected != asp_combos():
        raise StoryError("Python and ASP compatibility differ.")
    count = 0
    for problem, solutions in COMPATIBLE.items():
        for solution in solutions:
            for approach in APPROACHES:
                for treasure in TREASURES:
                    sample = generate(StoryParams(
                        problem=problem, solution=solution,
                        approach=approach, treasure=treasure
                    ))
                    check_sample(sample)
                    count += 1
    print(f"OK: {count} story states; {len(expected)} compatible paths.")


def emit(sample: StorySample, *, trace: bool, qa: bool, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps({
            "entities": sample.world.snapshot(),
            "history": [asdict(event) for event in sample.world.history],
        }, indent=2))


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.n < 1:
            raise StoryError("-n must be positive.")
        if args.show_asp:
            print(asp_facts() + "\n" + ASP_RULES)
            return 0
        if args.verify:
            verify()
            return 0
        if args.asp:
            print(json.dumps(sorted(asp_combos())))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            paths = [
                (problem, solution)
                for problem, solutions in COMPATIBLE.items()
                for solution in solutions
                if args.problem is None or problem == args.problem
                if args.solution is None or solution == args.solution
            ]
            if not paths:
                raise StoryError("No compatible paths match those options.")
            params_list = []
            for problem, solution in paths:
                params_list.append(StoryParams(
                    child=args.child or rng.choice(NAMES),
                    friend=args.friend or rng.choice(NAMES),
                    problem=problem,
                    solution=solution,
                    approach=args.approach or rng.choice(APPROACHES),
                    treasure=args.treasure or rng.choice(tuple(TREASURES)),
                    seed=args.seed,
                ))
                if params_list[-1].child == params_list[-1].friend:
                    params_list[-1].friend = next(
                        n for n in NAMES if n != params_list[-1].child
                    )
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]

        samples = [generate(params) for params in params_list]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload,
                             ensure_ascii=False, indent=2))
        else:
            for index, sample in enumerate(samples):
                emit(sample, trace=args.trace, qa=args.qa,
                     header=f"\n### Story {index + 1}\n" if len(samples) > 1 else "")
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
