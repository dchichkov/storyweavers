#!/usr/bin/env python3
"""Nose, Sharing, and a Lantern for Bedtime."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
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
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str = "Nora"
    companion: str = "Pip"
    problem: str = "missing_scent"
    solution: str = "share_lantern"
    mood: str = "gentle"
    object_name: str = "moonberry"
    seed: int = 777


NAMES = ("Nora", "Milo", "Ada", "Tess", "Luca", "Ivy")
MOODS = ("gentle", "sleepy", "brave")
PROBLEMS = {
    "missing_scent": "find",
    "dark_path": "light",
    "cold_nose": "comfort",
    "secret_sniff": "share",
}
SOLUTIONS = {
    "share_lantern": "find",
    "follow_bell": "light",
    "warm_scarf": "comfort",
    "tell_secret": "share",
}
OBJECTS = {
    "moonberry": ("a moonberry", "sweet silver fruit", "the berry tree"),
    "pinecone": ("a pinecone", "warm pine scent", "the old pine"),
    "honeycake": ("a honey cake", "golden honey smell", "the kitchen window"),
}
PROMPT = (
    "Write a gentle bedtime story about a child and a small companion who share "
    "help, notice a clue about a nose, and find their way home."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity("hero", params.hero, "character", "cottage",
                           memes={"trust": 0.5, "calm": 0.6}),
            "companion": Entity("companion", params.companion, "character", "cottage",
                                memes={"trust": 0.5, "calm": 0.5}),
            "nose": Entity("nose", "the little nose", "body", "cottage",
                           meters={"warmth": 0, "scent": 0}),
            "lantern": Entity("lantern", "the blue lantern", "tool", "cottage",
                              meters={"lit": 0, "oil": 1}),
            "scarf": Entity("scarf", "the red scarf", "tool", "cottage",
                            meters={"shared": 0}),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question: str = "",
                cause: str = "", result: str = ""):
        self.history.append(Event(kind, text, question, cause, result,
                                  state=self.snapshot()))

    def say(self, speaker: str, text: str, *, question: str = ""):
        name = self.entities[speaker].label
        punctuation = "asked" if text.endswith("?") else "said"
        self.history.append(Event(
            "speech", f'"{text}" {name} {punctuation}.',
            question=question, speaker=speaker, state=self.snapshot()
        ))

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
                QAItem("What does sharing mean in this story?",
                       "It means giving another person part of the help or comfort you have."),
                QAItem("What can a nose notice?",
                       "A nose can notice scents such as berries, pine, or warm honey."),
            ],
            world=self,
        )


def validate_params(params: StoryParams):
    if params.problem not in PROBLEMS or params.solution not in SOLUTIONS:
        raise StoryError("Unknown problem or solution.")
    if PROBLEMS[params.problem] != SOLUTIONS[params.solution]:
        raise StoryError(f"{params.solution!r} cannot solve {params.problem!r}.")
    if params.hero == params.companion:
        raise StoryError("The two characters need different names.")
    if any(not name or not name[0].isupper() for name in (params.hero, params.companion)):
        raise StoryError("Names must begin with capital letters.")
    if params.mood not in MOODS or params.object_name not in OBJECTS:
        raise StoryError("Unknown mood or object.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    item, scent, place = OBJECTS[params.object_name]
    world.entities["object"] = Entity(
        "object", item, "thing", place, meters={"found": 0}
    )
    world.entities["nose"].meters["known_scent"] = 1
    world.entities["hero"].memes["scent_memory"] = 1
    return world


def find_by_scent(world: World):
    nose = world.entities["nose"]
    obj = world.entities["object"]
    if not nose.meters.get("known_scent") or not world.entities["companion"].memes.get("trust"):
        raise StoryError("The remembered scent must be shared before the search.")
    obj.location = OBJECTS[world.params.object_name][2]
    obj.meters["found"] = 1
    nose.meters["scent"] = 1


def light_path(world: World):
    lantern = world.entities["lantern"]
    if not lantern.meters["oil"]:
        raise StoryError("The lantern has no oil.")
    lantern.meters["lit"] = 1
    world.entities["hero"].location = "garden_path"
    world.entities["companion"].location = "garden_path"
    world.entities["hero"].memes["trust"] = 1


def warm_nose(world: World):
    scarf = world.entities["scarf"]
    scarf.meters["shared"] = 1
    world.entities["nose"].meters["warmth"] = 1


def share_secret(world: World):
    if not world.entities["hero"].memes.get("trust"):
        raise StoryError("The friends must trust each other before sharing the secret.")
    world.entities["companion"].memes["known_secret"] = 1
    world.entities["hero"].memes["trust"] = 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    h = world.entities["hero"].label
    c = world.entities["companion"].label
    item, scent, place = OBJECTS[params.object_name]

    world.narrate(
        "opening",
        f"{h} was getting ready for bed when {c}, a small night friend, "
        f"pressed a curious nose to the window. Outside, the garden waited under stars."
    )

    if params.problem == "missing_scent":
        world.say("companion", f"I smell {scent}, but I cannot see where it comes from.")
        world.say("hero", "Then we can remember the smell together.")
        world.narrate(
            "clue",
            f"The little nose twitched toward the dark garden, while {h} remembered "
            f"the same {scent} from the {place}.",
            question="Why could the friends begin searching for the missing treat?",
            cause=f"{h} recognized the scent that {c}'s nose had noticed.",
            result="They had a shared clue instead of a guess."
        )
        world.say("companion", "Will you carry the lantern?")
        world.say("hero", "Only if you share the scent with me. Tell me which way it pulls.")
        world.say("companion", "It pulls past the sleepy gate and toward the old stones.")
        world.entities["companion"].memes["trust"] = 1
        find_by_scent(world)
        world.narrate(
            "turn",
            f"They followed the nose's tiny turns. Near {place}, {c} sniffed once, "
            f"and {h} found {item} beneath a broad leaf.",
            question="How did the friends find the hidden object?",
            cause=f"{c} shared the direction of the scent while {h} watched the path.",
            result=f"They found {item} at {place}."
        )
        world.say("hero", f"We found it. Shall we share it before bedtime?")
        world.say("companion", "Yes. A shared treasure smells sweeter.")
        world.entities["object"].meters["shared"] = 1
        world.entities["hero"].memes["trust"] = 1
        world.entities["companion"].memes["trust"] = 1
        world.narrate(
            "ending",
            f"Back in the cottage, {h} and {c} divided {item} into two small pieces. "
            "The nose that had led them home rested happily beneath the blanket.",
            question="What changed when the friends shared the treasure?",
            cause="They treated the discovery as something for both of them.",
            result="Both friends enjoyed it, and the search ended peacefully."
        )

    elif params.problem == "dark_path":
        world.say("companion", "The path is dark, and my nose says home is the other way.")
        world.say("hero", "I thought you knew the path.")
        world.narrate(
            "uncertainty",
            f"{h} lifted the lantern, but its flame was out. A few steps ahead, "
            "the garden path disappeared into blue shadow.",
            question="Why did the friends stop on the garden path?",
            cause="The lantern was unlit, so neither friend could safely see the way.",
            result="They could not trust a guess about which turn led home."
        )
        world.say("companion", "I can hear the wind by the gate.")
        world.say("hero", "And I can share the lantern oil. We will use both clues.")
        world.entities["companion"].memes["trust"] = 1
        light_path(world)
        world.narrate(
            "turn",
            f"{h} shared the last little measure of oil with the lantern. "
            f"Its blue light showed {c}'s nose pointing toward the gate.",
            question="What helped the friends choose the safe path?",
            cause=f"{h} shared the lantern oil, while {c} used the nose's direction.",
            result="The light and the scent together revealed the gate."
        )
        world.say("hero", "Your nose found the breeze. My lantern found the stones.")
        world.say("companion", "Two small helpers are better than one big guess.")
        world.narrate(
            "ending",
            f"The gate opened with a soft click. The lantern glowed beside the bed, "
            f"and {c}'s nose no longer had to search in the dark.",
            question="How did the friends get home?",
            cause="They combined shared lantern light with the companion's sense of smell.",
            result="They followed the lit path through the gate and reached bed safely."
        )

    elif params.problem == "cold_nose":
        world.say("companion", "My nose is cold. I cannot smell the good-night garden.")
        world.say("hero", "I have a scarf, but it is only wide enough for one.")
        world.narrate(
            "worry",
            f"The red scarf lay across {h}'s knees. {c} tucked a chilly nose beneath "
            "one paw and tried not to shiver.",
            question="Why could the companion not enjoy the bedtime scent?",
            cause="The night air had made the companion's nose too cold to notice scents.",
            result="The garden smells seemed to vanish."
        )
        world.say("hero", "We can share it. One end for your nose and one end for my neck.")
        world.say("companion", "Then neither of us will be completely wrapped.")
        world.say("hero", "We only need enough warmth to try again.")
        warm_nose(world)
        world.narrate(
            "turn",
            f"They shared the red scarf in a funny little loop. Soon {c}'s nose "
            f"grew warm enough to catch the scent of {scent}.",
            question="How did the friends warm the companion's nose?",
            cause=f"{h} shared the scarf instead of keeping it around only one neck.",
            result="The scarf warmed the nose enough for the scent to return."
        )
        world.say("companion", f"I smell {scent} again!")
        world.say("hero", "Good. We can notice it together, then go to sleep.")
        world.entities["hero"].memes["trust"] = 1
        world.entities["companion"].memes["trust"] = 1
        world.narrate(
            "ending",
            f"The scarf rested between their pillows. Its red ends touched both friends, "
            "and the warm little nose breathed in one last garden scent.",
            question="What did the shared scarf change?",
            cause="Sharing the scarf gave the cold nose enough warmth to work again.",
            result="The companion could smell the garden before falling asleep."
        )

    else:
        world.say("hero", "I found a secret path under the moon.")
        world.say("companion", "Will you tell me, or keep it folded in your pocket?")
        world.narrate(
            "secret",
            f"{h} had discovered a narrow path beside the {place}, but the secret "
            f"felt heavy when {c} asked about it.",
            question="Why did the secret become a problem?",
            cause=f"{h} knew about a safe path but had not shared the information with {c}.",
            result="The companion could not choose the path or help with the journey."
        )
        world.say("hero", "I was afraid you might laugh at my little path.")
        world.say("companion", "I will listen first. A secret can become a map when shared.")
        share_secret(world)
        world.entities["companion"].memes["trust"] = 1
        world.say("hero", f"It begins where the nose can smell {scent}.")
        world.say("companion", "Then I will walk beside you, not behind you.")
        world.narrate(
            "turn",
            f"{h} shared the secret, and {c} added a careful nose to the plan. "
            "Together they reached the quiet garden without getting lost.",
            question="What happened after the secret was shared?",
            cause=f"{h} explained the path and {c} offered help instead of teasing.",
            result="The secret became a plan that both friends could follow."
        )
        world.say("hero", "Next time, I will share the map sooner.")
        world.say("companion", "Next time, I will share the walking.")
        world.narrate(
            "ending",
            f"They returned to the cottage with the moon behind them. "
            f"The little nose rested on the pillow, and the secret path belonged to both friends.",
            question="How did sharing change the journey?",
            cause="Sharing the path let both friends understand and help one another.",
            result="They walked safely together and kept the discovery as a shared memory."
        )

    check_sample(world.sample())
    return world.sample()


def check_sample(sample: StorySample):
    world = sample.world
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs at least three grounded questions.")
    speeches = [e for e in world.history if e.kind == "speech"]
    if len(speeches) < 2:
        raise StoryError("The story needs a sustained exchange of dialogue.")
    if not any(e.speaker == "hero" for e in speeches) or not any(e.speaker == "companion" for e in speeches):
        raise StoryError("Both characters must speak several times.")
    if not any("nose" in e.text.lower() for e in world.history):
        raise StoryError("The nose must matter in the story.")
    if not any("share" in e.text.lower() or "shared" in e.text.lower() for e in world.history):
        raise StoryError("Sharing must matter in the story.")
    if not world.entities["hero"].memes["trust"] >= 1:
        raise StoryError("The ending must show growing trust.")


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
    facts = [fact("problem", p, n) for p, n in PROBLEMS.items()]
    facts += [fact("solution", s, n) for s, n in SOLUTIONS.items()]
    return "\n".join(facts)


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "valid"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--companion")
    parser.add_argument("--problem", choices=tuple(PROBLEMS))
    parser.add_argument("--solution", choices=tuple(SOLUTIONS))
    parser.add_argument("--mood", choices=MOODS)
    parser.add_argument("--object-name", choices=tuple(OBJECTS))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        pair for pair in valid_combos()
        if args.problem is None or pair[0] == args.problem
        if args.solution is None or pair[1] == args.solution
    ]
    if not combos:
        raise StoryError("No compatible problem and solution.")
    problem, solution = rng.choice(combos)
    hero = args.hero or rng.choice(NAMES)
    available = [name for name in NAMES if name != hero and name != args.hero]
    companion = args.companion or rng.choice(available)
    params = StoryParams(
        hero=hero,
        companion=companion,
        problem=problem,
        solution=solution,
        mood=args.mood or rng.choice(MOODS),
        object_name=args.object_name or rng.choice(tuple(OBJECTS)),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if set(valid_combos()) != asp_combos():
        raise StoryError("Python and ASP compatibility disagree.")
    count = 0
    for problem, solution in valid_combos():
        for mood in MOODS:
            for obj in OBJECTS:
                generate(StoryParams(problem=problem, solution=solution,
                                     mood=mood, object_name=obj))
                count += 1
    print(f"OK: {count} story states; {len(valid_combos())} compatible pairs.")


def emit(sample: StorySample, *, trace: bool, qa: bool, header: str = ""):
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
            samples = []
            for problem, solution in valid_combos():
                if args.problem and args.problem != problem:
                    continue
                if args.solution and args.solution != solution:
                    continue
                fields = vars(args).copy()
                fields.update(problem=problem, solution=solution)
                samples.append(generate(resolve_params(argparse.Namespace(**fields), rng)))
        else:
            samples = [
                generate(resolve_params(args, rng))
                for _ in range(args.n)
            ]
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
