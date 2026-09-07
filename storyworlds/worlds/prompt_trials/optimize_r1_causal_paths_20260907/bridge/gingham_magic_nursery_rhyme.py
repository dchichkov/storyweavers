#!/usr/bin/env python3
"""Gingham Magic Nursery Rhyme.

A small bridge of gingham, a little magic, and a rhyme that changes when
kindness and careful listening reveal the right path.
"""

from __future__ import annotations

import argparse
import json
import random
import re
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
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    beliefs: dict[str, str] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    text: str
    speaker: str = ""
    listener: str = ""
    question: str = ""
    cause: str = ""
    result: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str = "Pip"
    friend: str = "May"
    problem: str = "gap"
    solution: str = "ribbon"
    companion: str = "mouse"
    rhyme: str = "bounce"
    approach: str = "listen"
    seed: int = 777


PROBLEMS = {
    "gap": "The gingham path is too short to reach the moonlit garden.",
    "wind": "A playful wind keeps lifting the gingham bridge.",
    "spell": "A sleepy spell has made the bridge forget its way home.",
    "muddle": "The magic rhyme has mixed up the bridge's colors and direction.",
}

SOLUTIONS = {
    "ribbon": "Tie a silver ribbon to lengthen and guide the cloth.",
    "stones": "Place moon-pebbles beneath the cloth as steady stepping places.",
    "song": "Sing the missing answering line so the bridge remembers its path.",
    "sharing": "Ask the moon-mouse to share its lantern light and choose the safe way.",
}

COMPATIBLE = {
    "gap": ("ribbon",),
    "wind": ("stones",),
    "spell": ("song",),
    "muddle": ("sharing",),
}

COMPANIONS = {
    "mouse": ("a moon-mouse", "lantern"),
    "wren": ("a blue wren", "feather"),
    "frog": ("a silver frog", "bell"),
}

RHYME_LINES = {
    "bounce": ("Gingham, gingham, cross the night;", "Step by step, the stars shine bright."),
    "hush": ("Gingham, gingham, hush the breeze;", "Softly now, among the trees."),
    "twirl": ("Gingham, gingham, turn and gleam;", "Carry us across the dream."),
}

NAMES = ("Pip", "May", "Nell", "Tom", "Fay", "Bo")
APPROACHES = ("rush", "listen")
PROMPT = (
    "Write a dialogue-rich nursery-rhyme story about children using gingham "
    "and magic to repair a tiny bridge."
)


def validate_params(params: StoryParams) -> None:
    if params.problem not in PROBLEMS:
        raise StoryError("Unknown bridge problem.")
    if params.solution not in SOLUTIONS:
        raise StoryError("Unknown bridge solution.")
    if params.solution not in COMPATIBLE[params.problem]:
        raise StoryError(
            f"{params.solution!r} cannot solve {params.problem!r}; "
            "choose a compatible magical action."
        )
    if params.companion not in COMPANIONS or params.rhyme not in RHYME_LINES:
        raise StoryError("Unknown companion or rhyme.")
    if params.hero == params.friend:
        raise StoryError("The two speakers must have different names.")
    for name in (params.hero, params.friend):
        if not re.fullmatch(r"[A-Z][a-z]+", name):
            raise StoryError("Names must be simple capitalized words, such as Pip.")


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        companion_label, _ = COMPANIONS[params.companion]
        self.entities = {
            "hero": Entity(
                "hero", params.hero, "character", "cottage",
                memes={"courage": 0.5, "trust": 0.5},
            ),
            "friend": Entity(
                "friend", params.friend, "character", "cottage",
                memes={"courage": 0.5, "trust": 0.5},
            ),
            "bridge": Entity(
                "bridge", "the gingham bridge", "cloth_bridge", "creek_bank",
                meters={"length": 2, "gap": 3, "lift": 0, "memory": 0,
                        "direction": 0, "safe": 0},
                memes={"magic": 1, "belonging": 0.5},
            ),
            "garden": Entity(
                "garden", "the moonlit garden", "place", "far_bank",
                meters={"reachable": 0},
            ),
            "companion": Entity(
                "companion", companion_label, "helper", "hedge",
                meters={"light": 1},
                memes={"helpfulness": 1},
            ),
            "basket": Entity(
                "basket", "the berry basket", "thing", "cottage",
                meters={"delivered": 0},
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
    ) -> None:
        self.history.append(Event(
            kind=kind,
            text=text,
            question=question,
            cause=cause,
            result=result,
            state=self.snapshot(),
        ))

    def say(
        self,
        speaker: str,
        text: str,
        *,
        listener: str = "",
    ) -> None:
        label = self.entities[speaker].label
        verb = "asked" if text.endswith("?") else "said"
        self.history.append(Event(
            kind="speech",
            text=f'"{text}" {label} {verb}.',
            speaker=speaker,
            listener=listener,
            state=self.snapshot(),
        ))

    def sample(self) -> StorySample:
        return StorySample(
            params=self.params,
            story="\n\n".join(event.text for event in self.history),
            prompts=[PROMPT],
            story_qa=[
                QAItem(event.question, f"{event.cause} {event.result}")
                for event in self.history
                if event.question
            ],
            world_qa=[
                QAItem(
                    "What material is the little bridge made from?",
                    "It is made from gingham cloth.",
                ),
                QAItem(
                    "What kind of bridge is in the story?",
                    "It is a small magical bridge across a creek.",
                ),
            ],
            world=self,
        )


def build_world(params: StoryParams) -> World:
    validate_params(params)
    return World(params)


def attempt_cross(world: World) -> bool:
    bridge = world.entities["bridge"]
    bridge.meters["lift"] += 1
    problem = world.params.problem
    if problem == "gap":
        return bridge.meters["length"] >= bridge.meters["gap"]
    if problem == "wind":
        return bridge.meters["lift"] >= 2 and bridge.meters["safe"] == 1
    if problem == "spell":
        return bridge.meters["memory"] == 1
    return bridge.meters["direction"] == 1 and bridge.meters["safe"] == 1


def repair(world: World) -> None:
    params = world.params
    bridge = world.entities["bridge"]
    companion = world.entities["companion"]
    if params.solution == "ribbon":
        bridge.meters.update(length=3, direction=1, safe=1)
        bridge.memes["belonging"] = 1
    elif params.solution == "stones":
        bridge.meters.update(safe=1, lift=2)
        companion.meters["light"] = 0
    elif params.solution == "song":
        bridge.meters.update(memory=1, direction=1, safe=1)
        bridge.memes["belonging"] = 1
    elif params.solution == "sharing":
        if companion.meters["light"] < 1:
            raise StoryError("The helper has no lantern light left to share.")
        companion.meters["light"] = 0
        bridge.meters.update(direction=1, safe=1, lift=2)


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    rng = random.Random(params.seed)
    world = build_world(params)
    h = params.hero
    f = params.friend
    bridge = world.entities["bridge"].label
    companion_label, companion_item = COMPANIONS[params.companion]
    first_line, second_line = RHYME_LINES[params.rhyme]

    openings = [
        f"{h} and {f} found a gingham bridge by the creek at moonrise.",
        f"By the silver creek, {h} carried a gingham bridge while {f} carried berries.",
        f"Little {h} and {f} went tiptoe where the moon made the water shine.",
    ]
    world.narrate(
        "beginning",
        rng.choice(openings)
        + f" They wished to reach the moonlit garden by magic, where the night queen "
          f"kept a basket waiting."
    )
    world.say("hero", rng.choice([
        "Is the gingham bridge ready for our berry basket?",
        "May we cross before the moon climbs higher?",
        "Does this little bridge know the way tonight?",
    ]))
    world.say("friend", rng.choice([
        "It looks ready, but magic likes careful questions.",
        "It may be pretty, yet pretty cloth can still make a poor road.",
        "Let us look before we leap, or the berries may take a bath.",
    ]))

    if params.approach == "rush":
        world.say("hero", rng.choice([
            "I will run across before the wind can blink!",
            "A quick hop will tell us everything.",
            "The garden is waiting. I shall try it now!",
        ]))
        crossed = attempt_cross(world)
        if crossed:
            raise StoryError("The first attempt should reveal the chosen trouble.")
        failure = {
            "gap": f"The gingham bridge stopped short, and {h} hopped back from the creek.",
            "wind": f"A gust puffed beneath the gingham bridge and lifted it like a kite.",
            "spell": f"The cloth curled in a sleepy circle and pointed back to the cottage.",
            "muddle": f"Red squares pointed left while blue squares pointed right, and the path became a muddle.",
        }[params.problem]
        world.narrate("failed_attempt", failure)
        world.say("friend", rng.choice([
            "Stop, stop! A brave hop is not the same as a safe plan.",
            "That was a test, not a solution. What did the bridge show us?",
            "Come back, little jumper. The cloth has told us its trouble.",
        ]))
        world.say("hero", "I saw it now. I should listen before I leap.")
    else:
        world.say("hero", "What should we ask the bridge before we cross?")
        world.say("friend", "We should watch its edge, its lift, and the direction of its checks.")
        observations = {
            "gap": "The last gingham square dangled above empty air.",
            "wind": "The corners fluttered whenever the creek breathed.",
            "spell": "The blue checks shivered and pointed toward the cottage.",
            "muddle": "The red and blue checks pointed in opposite directions.",
        }
        world.narrate("inspection", observations[params.problem])

    if params.problem == "gap":
        world.say("friend", "The bridge is too short. Its last square cannot touch the far bank.")
        world.say("hero", "Could the moon-mouse lend us a silver ribbon?")
        world.say("friend", "A ribbon can guide the cloth, but we must tie it tightly.")
        world.narrate(
            "discovery",
            f"{companion_label} heard them and brought a silver ribbon from beneath the hedge.",
            question="Why could the children not cross the gingham bridge at first?",
            cause="The gingham bridge ended before it reached the far bank.",
            result="They learned that its length had to be changed, not merely its color admired.",
        )
        world.say("hero", "I will tie one end, and you hold the gingham straight.")
        world.say("friend", "Together, then. A bridge needs two careful hands.")
        repair(world)
        world.narrate(
            "repair",
            f"They tied the silver ribbon to the gingham edge and pulled it gently "
            f"to the far bank.",
            question="How did the ribbon help?",
            cause="The cloth bridge was too short to span the creek.",
            result="The ribbon lengthened and guided the gingham path until both banks were reached.",
        )
    elif params.problem == "wind":
        world.say("friend", "The wind is lifting the cloth. It needs weight at its corners.")
        world.say("hero", "I could hold it, but I cannot hold it and carry the basket.")
        world.say("friend", "Then we need moon-pebbles, placed where the wind can see them.")
        world.narrate(
            "discovery",
            f"The {companion_label} shook its {companion_item}, and three moon-pebbles "
            "rolled from the hedge.",
            question="What made the gingham bridge unsafe?",
            cause="The creek wind lifted the loose cloth like a kite.",
            result="The children discovered that steady moon-pebbles could hold its corners down.",
        )
        world.say("hero", "One pebble here, one there, and one beneath the middle.")
        world.say("friend", "Good. Leave a little room for our feet between the stones.")
        repair(world)
        world.narrate(
            "repair",
            "They tucked moon-pebbles beneath the gingham corners and pressed the "
            "middle flat.",
            question="Why did they place pebbles under the cloth?",
            cause="The wind kept raising the bridge from the creek bank.",
            result="The pebbles weighted the path so it stayed low and steady.",
        )
    elif params.problem == "spell":
        world.say("friend", "The bridge has forgotten its home. It keeps turning toward the cottage.")
        world.say("hero", "Can a bridge remember if we tell it a rhyme?")
        world.say("friend", "Only if we listen for the line it has lost.")
        world.narrate(
            "discovery",
            f"The {companion_label} tapped its {companion_item} twice. "
            f"The gingham whispered, “{first_line}”",
            question="What had the magical bridge forgotten?",
            cause="A sleepy spell had made the gingham point back toward the cottage.",
            result="The children learned that a missing rhyme could restore its memory.",
        )
        world.say("hero", first_line)
        world.say("friend", "That is the first half. What answer does the bridge need?")
        world.say("hero", second_line)
        repair(world)
        world.narrate(
            "repair",
            f"Together they sang, “{first_line} {second_line}” "
            "The checks brightened and faced the moonlit garden.",
            question="How did the children break the sleepy spell?",
            cause="The bridge needed the answering line of its old rhyme.",
            result="Their shared song restored its memory and turned it toward the garden.",
        )
    else:
        world.say("friend", "The checks disagree. One color points left, and the other points right.")
        world.say("hero", "Which way is safe? I cannot choose by guessing.")
        world.say("friend", f"Ask the {companion_label}. Its {companion_item} shines where the path is true.")
        world.narrate(
            "discovery",
            f"The {companion_label} held up its {companion_item}. "
            "A small glow rested on the safe edge of the creek.",
            question="Why was the path confusing?",
            cause="The magical colors pointed in two different directions.",
            result="The children learned to ask their helper instead of choosing by guesswork.",
        )
        world.say("hero", f"Will you share your light with our gingham bridge?")
        world.say("friend", "The light can show us the way, but we must follow it together.")
        repair(world)
        world.narrate(
            "repair",
            f"The {companion_label} shared its light. {h} and {f} turned each "
            "gingham square toward the glowing bank.",
            question="How did the helper resolve the muddle?",
            cause="The bridge needed a trusted guide through its mixed-up directions.",
            result="The shared lantern light marked a safe route and let the children align the cloth.",
        )

    if not attempt_cross(world):
        raise StoryError("The repaired gingham bridge did not become safe.")
    world.entities["garden"].meters["reachable"] = 1
    world.entities["basket"].location = "garden"
    world.entities["basket"].meters["delivered"] = 1
    world.narrate(
        "crossing",
        f"{h} carried the berry basket while {f} counted the gingham squares. "
        "Step by step, they crossed without a splash.",
        question="How did the children test the repaired bridge?",
        cause="They crossed slowly while counting each changed gingham square.",
        result="The bridge held, and the berry basket reached the moonlit garden.",
    )
    world.say("friend", rng.choice([
        "The berries are safe, and the bridge is singing.",
        "We crossed because we listened to what the cloth needed.",
        "A careful rhyme made a steady road.",
    ]))
    world.say("hero", rng.choice([
        "Then let us leave the ribbon, stones, song, or light ready for the next traveler.",
        "The smallest bridge can carry a very large friendship.",
        "Tomorrow we shall build another path, but tonight we shall share the berries.",
    ]))
    world.narrate(
        "ending",
        f"Under the moon, the {bridge} shimmered between the banks. "
        f"{companion_label} curled beside it, and the berry basket rested in the garden "
        "while the nursery rhyme twinkled over the creek.",
    )
    sample = world.sample()
    check_sample(sample)
    return sample


def check_sample(sample: StorySample) -> None:
    world = sample.world
    bridge = world.entities["bridge"]
    if not world.entities["garden"].meters["reachable"]:
        raise StoryError("The garden must become reachable.")
    if not world.entities["basket"].meters["delivered"]:
        raise StoryError("The berry basket must be delivered.")
    if bridge.meters["safe"] != 1:
        raise StoryError("The bridge must be safe at the ending.")
    speech = [event for event in world.history if event.kind == "speech"]
    if len(speech) < 2:
        raise StoryError("The story needs a sustained exchange of dialogue.")
    if not any(event.speaker == "hero" for event in speech):
        raise StoryError("The hero must speak.")
    if not any(event.speaker == "friend" for event in speech):
        raise StoryError("The friend must speak.")
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs at least three grounded questions.")
    if any(not item.answer.strip() for item in sample.story_qa):
        raise StoryError("Grounded answers cannot be empty.")
    if "gingham" not in sample.story.lower():
        raise StoryError("The story must visibly include gingham.")
    if "magic" not in sample.story.lower() and "magical" not in sample.story.lower():
        raise StoryError("The story must visibly include magic.")


ASP_RULES = """
valid(Problem,Solution) :- problem(Problem,Solution).
#show valid/2.
"""


def asp_facts() -> str:
    from asp import fact
    return "\n".join(
        fact("problem", problem, solution)
        for problem, solutions in COMPATIBLE.items()
        for solution in solutions
    )


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "valid"))


def valid_combos() -> list[tuple[str, str]]:
    return [
        (problem, solution)
        for problem, solutions in COMPATIBLE.items()
        for solution in solutions
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--problem", choices=tuple(PROBLEMS))
    parser.add_argument("--solution", choices=tuple(SOLUTIONS))
    parser.add_argument("--companion", choices=tuple(COMPANIONS))
    parser.add_argument("--rhyme", choices=tuple(RHYME_LINES))
    parser.add_argument("--approach", choices=APPROACHES)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [
        pair for pair in valid_combos()
        if args.problem is None or pair[0] == args.problem
        if args.solution is None or pair[1] == args.solution
    ]
    if not choices:
        raise StoryError("No compatible problem and solution were selected.")
    problem, solution = rng.choice(choices)
    hero = args.hero or rng.choice(NAMES)
    friend_choices = [name for name in NAMES if name != hero and name != args.hero]
    friend = args.friend or rng.choice(friend_choices)
    params = StoryParams(
        hero=hero,
        friend=friend,
        problem=problem,
        solution=solution,
        companion=args.companion or rng.choice(tuple(COMPANIONS)),
        rhyme=args.rhyme or rng.choice(tuple(RHYME_LINES)),
        approach=args.approach or rng.choice(APPROACHES),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify() -> None:
    if set(valid_combos()) != asp_combos():
        raise StoryError("Python and ASP disagree about compatible paths.")
    count = 0
    for problem, solution in valid_combos():
        for companion in COMPANIONS:
            for rhyme in RHYME_LINES:
                for approach in APPROACHES:
                    generate(StoryParams(
                        problem=problem,
                        solution=solution,
                        companion=companion,
                        rhyme=rhyme,
                        approach=approach,
                        seed=19 + count,
                    ))
                    count += 1
    print(f"OK: {count} story states; {len(valid_combos())} compatible magical paths.")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps(
            {
                "entities": sample.world.snapshot(),
                "history": [asdict(event) for event in sample.world.history],
            },
            indent=2,
        ))


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
            if not selected:
                raise StoryError("No compatible combinations match these options.")
            params_list = []
            for problem, solution in selected:
                copied = argparse.Namespace(**vars(args))
                copied.problem = problem
                copied.solution = solution
                params_list.append(resolve_params(copied, rng))
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]

        samples = [generate(params) for params in params_list]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload,
                             ensure_ascii=False, indent=2))
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
