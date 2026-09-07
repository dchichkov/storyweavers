#!/usr/bin/env python3
"""A bedtime tale about a nose, a shared moon-lantern, and a warning in the wind."""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

_HERE = Path(__file__).resolve()
for _parent in _HERE.parents:
    if (_parent / "results.py").exists():
        sys.path.insert(0, str(_parent))
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
    kind: str = "thing"
    location: str = ""
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
    listener: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    child: str = "Nora"
    companion: str = "Pip"
    problem: str = "sniff"
    solution: str = "share_lantern"
    clue: str = "pine"
    seed: int = 777


NAMES = ("Nora", "Milo", "Lina", "Tess", "Owen", "Pia")
CLUES = {
    "pine": {
        "scent": "the sharp smell of pine",
        "place": "the pine path",
        "warning": "The wind will bend the old branch before moonrise.",
        "ending": "pine needles whispered above the warm bed.",
    },
    "rain": {
        "scent": "the cool smell of rain",
        "place": "the rain barrel",
        "warning": "A silver drop will wake the sleeping lantern.",
        "ending": "rain tapped softly on the roof.",
    },
    "bread": {
        "scent": "the sweet smell of warm bread",
        "place": "the kitchen door",
        "warning": "The hungry little owl will visit before dawn.",
        "ending": "bread-scented dreams curled around the pillow.",
    },
}
PROBLEMS = {
    "sniff": "notice_warning",
    "dark": "light_path",
    "lonely": "share_comfort",
}
SOLUTIONS = {
    "share_lantern": "notice_warning",
    "follow_scent": "light_path",
    "tell_story": "share_comfort",
}
PROMPT = "Write a gentle bedtime story about a child whose nose notices a clue and who learns to share."

ASP_RULES = """
compatible(S,P) :- problem(P,N), solution(S,N).
#show compatible/2.
"""


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "child": Entity("child", params.child, "character", "bedroom",
                            memes={"curiosity": 1.0, "trust": 0.5}),
            "companion": Entity("companion", params.companion, "character", "bedroom",
                                memes={"curiosity": 0.5, "trust": 0.5}),
            "nose": Entity("nose", "a small nose", "body", "child",
                           meters={"scent_strength": 0.0}),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question: str = "",
                cause: str = "", result: str = ""):
        self.history.append(Event(kind, text, question, cause, result,
                                  state=self.snapshot()))

    def say(self, speaker: str, text: str, *, listener: str = ""):
        actor = self.entities[speaker]
        if text.endswith("?"):
            verb = "asked"
        else:
            verb = "said"
        self.history.append(Event(
            "speech", f'"{text}" {actor.label} {verb}.',
            speaker=speaker, listener=listener, state=self.snapshot()))

    def settle(self):
        for name in ("child", "companion"):
            self.entities[name].memes["trust"] = 1.0
            self.entities[name].memes["calm"] = 1.0

    def sample(self) -> StorySample:
        return StorySample(
            params=self.params,
            story="\n\n".join(event.text for event in self.history),
            prompts=[PROMPT],
            story_qa=[
                QAItem(event.question, f"{event.cause} {event.result}")
                for event in self.history if event.question
            ],
            world_qa=[
                QAItem("What did the nose notice?", scent_answer(self.params.clue)),
                QAItem("What did sharing change?", sharing_answer(self.params.problem)),
            ],
            world=self,
        )


def scent_answer(clue: str) -> str:
    return f"The nose noticed {CLUES[clue]['scent']}."


def sharing_answer(problem: str) -> str:
    if problem == "sniff":
        return "Sharing the clue let both friends prepare before the warning came true."
    if problem == "dark":
        return "Sharing the lantern gave both friends a safe, glowing path."
    return "Sharing a story helped both friends feel less alone."


def valid_combos() -> list[tuple[str, str]]:
    return [
        (problem, solution)
        for problem, need in PROBLEMS.items()
        for solution, gift in SOLUTIONS.items()
        if need == gift
    ]


def validate_params(params: StoryParams):
    if (params.problem, params.solution) not in valid_combos():
        raise StoryError(
            f"{params.solution!r} cannot solve {params.problem!r}; choose a compatible path."
        )
    if params.clue not in CLUES:
        raise StoryError("Unknown nose clue.")
    if params.child == params.companion:
        raise StoryError("The two bedtime companions must have different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", name)
           for name in (params.child, params.companion)):
        raise StoryError("Names must be simple capitalized names.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    clue = CLUES[params.clue]
    world.entities["lantern"] = Entity(
        "lantern", "the moon-lantern", "lamp", "bedroom",
        meters={"lit": 0.0, "shared": 0.0})
    world.entities["window"] = Entity(
        "window", "the round window", "place", "bedroom",
        meters={"open": 0.0})
    world.entities["nose"].meters["scent_strength"] = 1.0
    world.entities["child"].memes["known_clue"] = clue["scent"]
    return world


def light_lantern(world: World):
    lantern = world.entities["lantern"]
    if world.entities["child"].location != "bedroom":
        raise StoryError("The lantern must be lit in the bedroom.")
    lantern.meters["lit"] = 1.0
    lantern.meters["shared"] = 1.0


def share_clue(world: World):
    if not world.entities["child"].memes.get("known_clue"):
        raise StoryError("The child must notice the nose clue first.")
    world.entities["companion"].memes["known_clue"] = (
        world.entities["child"].memes["known_clue"]
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    child = world.entities["child"].label
    companion = world.entities["companion"].label
    clue = CLUES[params.clue]
    world.narrate(
        "opening",
        f"{child} was tucked beneath a quilt when {companion} padded into the room. "
        "A round window held one sleepy star, and the moon-lantern waited on the sill.",
    )
    world.say("child", "My nose is awake, even though the rest of me is ready for bed.",
             listener="companion")
    world.say("companion", "What can it smell in the dark?", listener="child")

    if params.problem == "sniff":
        world.narrate(
            "notice",
            f"{child}'s small nose lifted. It caught {clue['scent']} drifting from {clue['place']}.",
            question="What did the nose notice?",
            cause=f"The nose caught {clue['scent']} before the friends could see anything.",
            result=f"{child} learned that something was changing near {clue['place']}.",
        )
        world.say("child", f"It smells like {clue['scent'].replace('the ', '')}.",
                 listener="companion")
        world.say("companion", "I smell only blankets. Should we look together?",
                 listener="child")
        world.say("child", "Yes. A clue is better when two people share it.",
                 listener="companion")
        share_clue(world)
        world.narrate(
            "foreshadow",
            f"{child} told {companion} the nose clue. Together they listened by the window. "
            f"Outside, the first breeze carried a quiet warning: {clue['warning']}",
            question="How did the friends learn what the warning meant?",
            cause=f"{child} shared {clue['scent']}, so {companion} knew where to listen.",
            result=f"They heard the warning before {clue['warning'].split('.')[0].lower()} happened.",
        )
        world.say("companion", "The wind is telling us to be ready.", listener="child")
        world.say("child", "Then we can get ready side by side.", listener="companion")
        light_lantern(world)
        world.narrate(
            "turn",
            f"They placed the moon-lantern near the door. When the old branch bent in the wind, "
            "its golden light showed the safe way back to bed.",
            question="What did sharing the clue help them do?",
            cause=f"{child} shared what the nose noticed, and both friends prepared for the wind.",
            result="The lantern was ready when the branch bent, so neither friend felt afraid.",
        )
        world.say("companion", "Your nose heard the night before my ears did.", listener="child")
        world.say("child", "And your ears helped my nose make sense of it.", listener="companion")

    elif params.problem == "dark":
        world.narrate(
            "dark",
            f"The room grew dim as a cloud crossed the moon. {child}'s nose caught "
            f"{clue['scent']} near {clue['place']}, but {companion} could not see the path.",
            question="Why did the friends need help finding the path?",
            cause="A cloud covered the moon while a new scent led away from the bed.",
            result="The friends needed a light they could carry together.",
        )
        world.say("companion", "I can follow your nose, but I cannot see my feet.",
                 listener="child")
        world.say("child", "We will not hurry. We will share the lantern.", listener="companion")
        light_lantern(world)
        world.narrate(
            "foreshadow",
            f"The lantern shone across the floor. Then the breeze whispered, "
            f"{clue['warning']}",
            question="What warning came before the safe journey?",
            cause="The friends paused with the lantern lit and listened to the breeze.",
            result="The whispered warning told them to move slowly and stay together.",
        )
        world.say("companion", "The wind says slow steps.", listener="child")
        world.say("child", "Slow steps can still take us home.", listener="companion")
        world.narrate(
            "turn",
            f"They followed the scent only as far as the doorway, then turned back beneath "
            "the lantern's warm circle.",
            question="How did the lantern solve the dark problem?",
            cause="The friends carried one lantern instead of walking separately.",
            result="Its shared light showed both friends the safe way back to bed.",
        )
        world.say("companion", "The light was small, but it had room for us both.", listener="child")
        world.say("child", "That is what sharing does.", listener="companion")

    else:
        world.narrate(
            "lonely",
            f"{companion} sat beside the bed feeling lonely. {child}'s nose noticed "
            f"{clue['scent']} and remembered a quiet night outside.",
            question="Why did the companion need comfort?",
            cause=f"{companion} felt lonely while the room grew quiet.",
            result=f"{child} used the nose clue to begin a gentle story.",
        )
        world.say("companion", "The night feels too large for one little listener.",
                 listener="child")
        world.say("child", "Then I will share a story with you.", listener="companion")
        world.narrate(
            "foreshadow",
            f"{child} whispered about {clue['place']}. At the window, the wind breathed, "
            f"{clue['warning']}",
            question="What detail foreshadowed the later change?",
            cause="The wind gave a warning while the friends were sharing the story.",
            result="The warning made the tale feel close to the real room.",
        )
        world.say("companion", "Did the story hear the wind too?", listener="child")
        world.say("child", "Perhaps the wind is sharing its ending with us.", listener="companion")
        light_lantern(world)
        world.narrate(
            "turn",
            "They took turns adding one sentence each until the moon-lantern glowed "
            "between them like a tiny sunrise.",
            question="How did sharing make the bedtime problem better?",
            cause="The friends took turns giving words to the same story.",
            result="The lonely companion became calm because the story belonged to both of them.",
        )
        world.say("companion", "Now the room feels small and friendly.", listener="child")
        world.say("child", "Good. Let us give the last line to the moon.", listener="companion")

    world.settle()
    world.narrate(
        "ending",
        f"{child} and {companion} climbed beneath the quilt. The moon-lantern rested between "
        f"their pillows, and {clue['ending'].capitalize()} They fell asleep knowing that "
        "a shared clue, like a shared dream, can make the night kinder.",
        question="What proved that the friends had changed by the end?",
        cause="They listened to one another and shared the clue, the light, or the story.",
        result="They settled together beneath one warm glow instead of facing the night alone.",
    )
    sample = world.sample()
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    world = sample.world
    if world.entities["lantern"].meters["lit"] != 1.0:
        raise StoryError("The ending needs a lit lantern.")
    if any(token in sample.story for token in ("{", "}", "None")):
        raise StoryError("Story contains an unresolved template.")
    turns = [event for event in world.history if event.kind == "speech"]
    if not any(event.speaker == "child" and event.listener == "companion" for event in turns):
        raise StoryError("The child must speak to the companion.")
    if not any(event.speaker == "companion" and event.listener == "child" for event in turns):
        raise StoryError("The companion must speak to the child.")
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs grounded questions and answers.")
    if any(not item.answer or item.answer.endswith(":") for item in sample.story_qa):
        raise StoryError("Story answers must be complete explanations.")
    if world.entities["child"].memes["trust"] < 1 or world.entities["companion"].memes["trust"] < 1:
        raise StoryError("The friends must settle their trust by the ending.")


def asp_facts() -> str:
    from asp import fact
    return "\n".join(fact("problem", problem, need) for problem, need in PROBLEMS.items()) + "\n" + "\n".join(
        fact("solution", solution, need)
        for solution, need in SOLUTIONS.items()
    )


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    symbols = one_model(asp_facts() + ASP_RULES)
    return {(solution, problem) for solution, problem in atoms(symbols, "compatible")}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--child")
    parser.add_argument("--companion")
    parser.add_argument("--problem", choices=tuple(PROBLEMS))
    parser.add_argument("--solution", choices=tuple(SOLUTIONS))
    parser.add_argument("--clue", choices=tuple(CLUES))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    candidates = [
        pair for pair in valid_combos()
        if args.problem is None or pair[0] == args.problem
        if args.solution is None or pair[1] == args.solution
    ]
    if not candidates:
        raise StoryError("No compatible problem and solution were selected.")
    problem, solution = rng.choice(candidates)
    child = args.child or rng.choice(NAMES)
    companion = args.companion or rng.choice([name for name in NAMES if name != child])
    params = StoryParams(
        child=child,
        companion=companion,
        problem=problem,
        solution=solution,
        clue=args.clue or rng.choice(tuple(CLUES)),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if asp_combos() != {(solution, problem) for problem, solution in valid_combos()}:
        raise StoryError("Python and ASP disagree about compatible paths.")
    tested = 0
    for problem, solution in valid_combos():
        for clue in CLUES:
            sample = generate(StoryParams(
                child="Nora", companion="Pip", problem=problem,
                solution=solution, clue=clue,
            ))
            check_sample(sample)
            tested += 1
    print(f"OK: {tested} story states; {len(valid_combos())} compatible paths.")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = ""):
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
            selected = [
                (problem, solution)
                for problem, solution in valid_combos()
                if args.problem is None or problem == args.problem
                if args.solution is None or solution == args.solution
            ]
            params_list = []
            for problem, solution in selected:
                params_list.append(resolve_params(
                    argparse.Namespace(
                        problem=problem, solution=solution, clue=args.clue,
                        child=args.child, companion=args.companion
                    ), rng))
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
