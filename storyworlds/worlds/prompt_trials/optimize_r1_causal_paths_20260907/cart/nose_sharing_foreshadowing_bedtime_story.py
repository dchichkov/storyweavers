#!/usr/bin/env python3
"""The Moonlit Nose: a gentle bedtime story about sharing and noticing clues."""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
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
    beliefs: dict[str, str] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    text: str
    speaker: str = ""
    listener: str = ""
    revealed: str = ""
    question: str = ""
    cause: str = ""
    result: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    child: str = "Nora"
    friend: str = "Pip"
    problem: str = "cold"
    solution: str = "share_blanket"
    clue: str = "whiskers"
    seed: int = 777


NAMES = ("Nora", "Milo", "Lina", "Owen", "Tess", "Pip")
PROBLEMS = {
    "cold": "comfort",
    "dark": "light",
    "lonely": "company",
    "lost": "search",
}
SOLUTIONS = {
    "share_blanket": "comfort",
    "share_lantern": "light",
    "share_song": "company",
    "share_clues": "search",
}
CLUES = {
    "whiskers": "a silver whisker caught on the blanket",
    "pawprints": "three tiny pawprints beside the window",
    "bell": "a faint bell sound under the porch",
}
PROMPT = (
    "Write a warm bedtime story about two friends who share something, notice an "
    "early clue, and use it to help a small animal before sleep."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "child": Entity(
                "child",
                params.child,
                "character",
                "bedroom",
                memes={"care": 0.7, "worry": 0.2},
            ),
            "friend": Entity(
                "friend",
                params.friend,
                "character",
                "bedroom",
                memes={"care": 0.6, "worry": 0.3},
            ),
            "kitten": Entity(
                "kitten",
                "the little kitten",
                "animal",
                "garden",
                memes={"trust": 0.4, "warmth": 0.1},
            ),
            "blanket": Entity(
                "blanket",
                "the moon-blue blanket",
                "object",
                "bedroom",
                meters={"warmth": 2, "shared": 0},
            ),
            "lantern": Entity(
                "lantern",
                "the small lantern",
                "object",
                "bedroom",
                meters={"light": 2, "shared": 0},
            ),
            "song": Entity(
                "song",
                "the humming song",
                "object",
                "bedroom",
                meters={"verses": 3, "shared": 0},
            ),
            "clues": Entity(
                "clues",
                "the little trail of clues",
                "object",
                "garden",
                meters={"found": 0},
            ),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(
        self,
        kind: str,
        text: str,
        *,
        question: str = "",
        cause: str = "",
        result: str = "",
    ):
        self.history.append(
            Event(
                kind=kind,
                text=text,
                question=question,
                cause=cause,
                result=result,
                state=self.snapshot(),
            )
        )

    def say(
        self,
        speaker: str,
        text: str,
        *,
        to: str = "",
        reveal: str = "",
    ):
        actor = self.entities[speaker]
        if reveal:
            if not to:
                raise StoryError("Useful information needs a listener.")
            actor.beliefs[reveal] = actor.beliefs.get(reveal, "known")
            self.entities[to].beliefs[reveal] = actor.beliefs[reveal]
        tag = "asked" if text.endswith("?") else "said"
        self.history.append(
            Event(
                kind="speech",
                text=f'"{text}" {actor.label} {tag}.',
                speaker=speaker,
                listener=to,
                revealed=reveal,
                state=self.snapshot(),
            )
        )


def validate_params(params: StoryParams):
    if params.problem not in PROBLEMS:
        raise StoryError("Unknown bedtime problem.")
    if params.solution not in SOLUTIONS:
        raise StoryError("Unknown sharing solution.")
    if PROBLEMS[params.problem] != SOLUTIONS[params.solution]:
        raise StoryError(
            f"{params.solution!r} cannot resolve {params.problem!r}; choose a fitting way to share."
        )
    if params.clue not in CLUES:
        raise StoryError("Unknown foreshadowing clue.")
    if params.child == params.friend:
        raise StoryError("The two friends must have different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", n) for n in (params.child, params.friend)):
        raise StoryError("Names must be simple capitalized words.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    if params.problem == "cold":
        world.entities["kitten"].meters["temperature"] = 1
    elif params.problem == "dark":
        world.entities["kitten"].meters["visibility"] = 1
    elif params.problem == "lonely":
        world.entities["kitten"].meters["trust"] = 1
    else:
        world.entities["kitten"].meters["distance"] = 3
    return world


def reveal_clue(world: World):
    clue = world.params.clue
    world.entities["clues"].meters["found"] = 1
    world.entities["kitten"].beliefs["nearby"] = "yes"
    world.entities["child"].beliefs["clue"] = clue
    world.entities["friend"].beliefs["clue"] = clue


def complete_action(world: World):
    p = world.params
    child = world.entities["child"]
    friend = world.entities["friend"]
    kitten = world.entities["kitten"]

    if not child.beliefs.get("plan") or not friend.beliefs.get("plan"):
        raise StoryError("Both friends must understand the shared plan.")
    if p.solution == "share_blanket":
        blanket = world.entities["blanket"]
        blanket.meters["shared"] = 1
        blanket.location = "porch"
        kitten.location = "porch"
        kitten.meters["temperature"] = 0
        kitten.memes["warmth"] = 1
    elif p.solution == "share_lantern":
        lantern = world.entities["lantern"]
        lantern.meters["shared"] = 1
        lantern.location = "garden"
        kitten.location = "garden"
        kitten.meters["visibility"] = 0
        kitten.memes["trust"] = 1
    elif p.solution == "share_song":
        song = world.entities["song"]
        song.meters["shared"] = 1
        song.location = "porch"
        kitten.location = "porch"
        kitten.memes["trust"] = 1
        kitten.memes["warmth"] = 1
    else:
        world.entities["clues"].location = "under_porch"
        kitten.location = "under_porch"
        kitten.meters["distance"] = 0
        kitten.memes["trust"] = 1


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    rng = random.Random(params.seed)
    world = build_world(params)
    h = params.child
    f = params.friend
    kitten = world.entities["kitten"]

    openings = [
        f"At bedtime, {h} and {f} listened to the rain whisper against the window.",
        f"The moon was high when {h} found {f} beside the quiet bedroom door.",
        f"Just as the house grew sleepy, {h} and {f} heard a tiny sound outside.",
    ]
    world.narrate("beginning", rng.choice(openings) + " Neither friend was ready to forget the little kitten in the garden.")

    world.say("child", "I want to help the kitten, but I do not want to go alone.")
    world.say("friend", "Then we can share the helping.")
    world.say("child", "What should we bring?")
    world.say("friend", "Something kind, and our listening ears.")

    clue_text = CLUES[params.clue]
    world.narrate(
        "foreshadowing",
        f"Before they opened the door, {h} noticed {clue_text}.",
        question="What early clue told the friends that the kitten was nearby?",
        cause=f"They noticed {clue_text}.",
        result="They searched close to the house instead of wandering into the dark garden.",
    )
    reveal_clue(world)
    world.say("child", "Look! That clue points toward the porch.", to="friend", reveal="clue")
    world.say("friend", "Then we will follow it together.")

    if params.problem == "cold":
        world.say("child", "The kitten is shivering. I thought the blanket was only for us.")
        world.say("friend", "A blanket can make room for two friends and four small paws.")
        world.say("child", "We can each hold an edge.")
        world.say("friend", "And the kitten can sleep in the middle.")
        world.narrate(
            "turn",
            f"They carried the moon-blue blanket to the porch, holding it between them like a small roof.",
            question="Why did the friends share the blanket?",
            cause="The kitten was shivering in the cool garden.",
            result="They carried the blanket together so the kitten could be warm without leaving either friend alone.",
        )
    elif params.problem == "dark":
        world.say("child", "The garden is dark. I cannot see where the kitten went.")
        world.say("friend", "We can share the lantern. You hold the handle, and I watch the path.")
        world.say("child", "Its golden circle reaches the flower pots.")
        world.say("friend", "And there—two bright eyes.")
        world.narrate(
            "turn",
            f"{h} held the small lantern while {f} guided its golden light along the garden path.",
            question="How did sharing the lantern help?",
            cause="The garden was too dark for one friend to find the kitten safely.",
            result="One friend carried the lantern while the other watched the path.",
        )
    elif params.problem == "lonely":
        world.say("child", "The kitten hides whenever I call. Maybe it thinks we will leave.")
        world.say("friend", "Then we can give it two gentle voices.")
        world.say("child", "I will hum softly.")
        world.say("friend", "I will answer from the porch.")
        world.narrate(
            "turn",
            f"They shared a quiet humming song, one verse from each friend, until the kitten crept nearer.",
            question="Why did the friends sing together?",
            cause="The kitten was lonely and afraid of a single unfamiliar voice.",
            result="Two gentle voices helped it feel safe enough to come closer.",
        )
    else:
        world.say("child", "The kitten is hidden, and the garden has many corners.")
        world.say("friend", "We can share the clues. You look for marks, and I listen for bells.")
        world.say("child", "Here are pawprints by the flower bed.")
        world.say("friend", "And I hear a bell beneath the porch.")
        world.narrate(
            "turn",
            f"They followed the clues together: {h} watched the ground while {f} listened beneath the porch.",
            question="How did sharing the search help them?",
            cause="The kitten was hidden among many garden corners.",
            result="One friend watched for marks while the other listened for the kitten's bell.",
        )

    world.entities["child"].beliefs["plan"] = params.solution
    world.entities["friend"].beliefs["plan"] = params.solution
    complete_action(world)

    if params.solution == "share_blanket":
        ending = "Under the blanket, the kitten curled into a warm comma while the two friends tucked its corners."
    elif params.solution == "share_lantern":
        ending = "The lantern made a little golden road, and the kitten followed it safely back to the porch."
    elif params.solution == "share_song":
        ending = "The kitten settled between the two voices, purring softly as the song floated into the night."
    else:
        ending = "Beneath the porch, the kitten reached the friends, guided by pawprints, a bell, and their patient voices."

    world.say("child", "It came because we noticed the clue and stayed together.")
    world.say("friend", "Sharing made the dark place feel small.")
    world.narrate(
        "ending",
        ending
        + f" Then {h} and {f} returned to bed, carrying the quiet comfort of the rescue with them.",
        question="What changed by the end of the story?",
        cause="The friends shared their useful object, voices, or search and followed the early clue.",
        result="The kitten became safe and settled, while both friends returned indoors together.",
    )

    sample = StorySample(
        params=params,
        story="\n\n".join(event.text for event in world.history),
        prompts=[PROMPT],
        story_qa=[
            QAItem(event.question, f"{event.cause} {event.result}")
            for event in world.history
            if event.question
        ],
        world_qa=[
            QAItem(
                "Why is sharing useful when someone needs help?",
                "Sharing lets friends combine what they have and makes a difficult task safer and kinder.",
            )
        ],
        world=world,
    )
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    world = sample.world
    kitten = world.entities["kitten"]
    if kitten.location not in {"porch", "garden", "under_porch"}:
        raise StoryError("The kitten must reach a safe ending place.")
    if kitten.memes["trust"] < 1 and sample.params.problem in {"dark", "lonely", "lost"}:
        raise StoryError("The kitten must become calm and trusting.")
    if not world.entities["child"].beliefs.get("plan"):
        raise StoryError("The child must carry out the shared plan.")
    speech = [e for e in world.history if e.kind == "speech"]
    if len(speech) < 10:
        raise StoryError("The bedtime story needs a sustained exchange.")
    if not any(e.speaker == "child" for e in speech) or not any(e.speaker == "friend" for e in speech):
        raise StoryError("Both friends must speak.")
    if not any(e.revealed for e in speech):
        raise StoryError("The clue must change what the friends do.")
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs grounded questions and answers.")


ASP_RULES = """
valid(P,S) :- problem(P,N), solution(S,N).
#show valid/2.
"""


def valid_combos() -> list[tuple[str, str]]:
    return [
        (problem, solution)
        for problem, need in PROBLEMS.items()
        for solution, ability in SOLUTIONS.items()
        if need == ability
    ]


def asp_facts() -> str:
    from asp import fact

    facts = [fact("problem", key, value) for key, value in PROBLEMS.items()]
    facts += [fact("solution", key, value) for key, value in SOLUTIONS.items()]
    return "\n".join(facts)


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model

    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "valid"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--child")
    parser.add_argument("--friend")
    parser.add_argument("--problem", choices=tuple(PROBLEMS))
    parser.add_argument("--solution", choices=tuple(SOLUTIONS))
    parser.add_argument("--clue", choices=tuple(CLUES))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    candidates = [
        pair
        for pair in valid_combos()
        if (args.problem is None or pair[0] == args.problem)
        and (args.solution is None or pair[1] == args.solution)
    ]
    if not candidates:
        raise StoryError("That solution does not fit the selected bedtime problem.")
    problem, solution = rng.choice(candidates)
    child = args.child or rng.choice(NAMES)
    friend_choices = [name for name in NAMES if name != child]
    friend = args.friend or rng.choice(friend_choices)
    params = StoryParams(
        child=child,
        friend=friend,
        problem=problem,
        solution=solution,
        clue=args.clue or rng.choice(tuple(CLUES)),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if set(valid_combos()) != asp_combos():
        raise StoryError("Python and ASP disagree about compatible bedtime paths.")
    count = 0
    for problem, solution in valid_combos():
        for clue in CLUES:
            sample = generate(
                StoryParams(
                    problem=problem,
                    solution=solution,
                    clue=clue,
                    seed=777 + count,
                )
            )
            check_sample(sample)
            count += 1
    print(f"OK: {count} story states; {len(valid_combos())} compatible paths.")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = ""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(
            json.dumps(
                {
                    "entities": sample.world.snapshot(),
                    "history": [asdict(event) for event in sample.world.history],
                },
                indent=2,
            )
        )


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
                if (args.problem is None or problem == args.problem)
                and (args.solution is None or solution == args.solution)
            ]
            if not selected:
                raise StoryError("No compatible bedtime paths match those options.")
            params_list = [
                StoryParams(
                    child=args.child or rng.choice(NAMES),
                    friend=args.friend or rng.choice(
                        [name for name in NAMES if name != (args.child or "")]
                    ),
                    problem=problem,
                    solution=solution,
                    clue=args.clue or rng.choice(tuple(CLUES)),
                    seed=args.seed + index,
                )
                for index, (problem, solution) in enumerate(selected)
            ]
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]

        samples = [generate(params) for params in params_list]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload, ensure_ascii=False, indent=2))
        else:
            for index, sample in enumerate(samples):
                emit(
                    sample,
                    trace=args.trace,
                    qa=args.qa,
                    header=f"\n### Story {index + 1}\n" if len(samples) > 1 else "",
                )
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
