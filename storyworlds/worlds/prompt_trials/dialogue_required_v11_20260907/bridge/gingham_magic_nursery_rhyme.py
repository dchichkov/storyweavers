#!/usr/bin/env python3
"""Gingham's Magic Nursery-Rhyme Bridge.

A small nursery-rhyme world in which careful words, a gingham ribbon, and a
little magic help two friends mend a moonlit bridge.
"""

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
    hero: str = "Mabel"
    friend: str = "Pip"
    charm: str = "star"
    problem: str = "loose"
    seed: int = 777


NAMES = ("Mabel", "Pip", "Nell", "Bram", "Tilly", "Robin")
CHARMS = {
    "star": "a silver star button",
    "bell": "a tiny brass bell",
    "moon": "a pale moon bead",
}
PROBLEMS = {
    "loose": "a loose gingham knot",
    "dim": "a dim magic stitch",
    "slack": "a slack ribbon rail",
}

PROMPT = (
    "Write a dialogue-rich nursery-rhyme story about two friends using a magical "
    "gingham ribbon to mend a tiny moonlit bridge."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity(
                "hero", params.hero, "character", "hill_path",
                memes={"worry": 0.7, "trust": 0.5},
            ),
            "friend": Entity(
                "friend", params.friend, "character", "hill_path",
                memes={"worry": 0.5, "trust": 0.5},
            ),
            "bridge": Entity(
                "bridge", "the gingham bridge", "bridge", "ribbon_ravine",
                meters={"length": 3, "strength": 1, "magic": 1, "tested": 0},
                memes={"hope": 0.5},
            ),
            "charm": Entity(
                "charm", CHARMS[params.charm], "charm", "button_pocket",
                meters={"power": 1},
                memes={"sparkle": 1.0},
            ),
            "lamb": Entity(
                "lamb", "the little lamb", "animal", "near_side",
                meters={"crossed": 0},
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
            if not to or reveal not in actor.beliefs:
                raise StoryError("A speaker cannot share a secret they do not know.")
            self.entities[to].beliefs[reveal] = actor.beliefs[reveal]
        tag = "asked" if text.endswith("?") else "said"
        if text.endswith("."):
            text = text[:-1]
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

    def sample(self) -> StorySample:
        return StorySample(
            params=self.params,
            story="\n\n".join(event.text for event in self.history),
            prompts=[PROMPT],
            story_qa=[
                QAItem(
                    question=event.question,
                    answer=f"{event.cause} {event.result}",
                )
                for event in self.history
                if event.question
            ],
            world_qa=[
                QAItem(
                    question="What made the bridge magical?",
                    answer=(
                        f"The {self.entities['charm'].label} helped the gingham "
                        "ribbon hold when it was tied with care."
                    ),
                ),
                QAItem(
                    question="What is gingham?",
                    answer=(
                        "Gingham is a woven cloth with a simple checked pattern, "
                        "like the red-and-white ribbon in the story."
                    ),
                ),
            ],
            world=self,
        )


def validate_params(params: StoryParams):
    if params.problem not in PROBLEMS:
        raise StoryError("Choose a known bridge trouble.")
    if params.charm not in CHARMS:
        raise StoryError("Choose a known magical charm.")
    if params.hero == params.friend:
        raise StoryError("The two speakers must have different names.")
    for name in (params.hero, params.friend):
        if not re.fullmatch(r"[A-Z][a-z]+", name):
            raise StoryError("Use simple capitalized names, such as Mabel and Pip.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    bridge = world.entities["bridge"]
    if params.problem == "loose":
        bridge.meters.update(strength=1, magic=1)
    elif params.problem == "dim":
        bridge.meters.update(strength=2, magic=0)
    else:
        bridge.meters.update(strength=1, magic=1)
    return world


def inspect_problem(world: World) -> str:
    bridge = world.entities["bridge"]
    if world.params.problem == "loose":
        return "loose"
    if world.params.problem == "dim":
        return "dim"
    if bridge.meters["length"] > 2:
        return "slack"
    return ""


def repair_bridge(world: World):
    hero = world.entities["hero"]
    bridge = world.entities["bridge"]
    charm = world.entities["charm"]
    problem = inspect_problem(world)
    if hero.beliefs.get("problem") != problem:
        raise StoryError("The repair must follow the problem the friends observed.")
    if problem == "loose":
        bridge.meters["strength"] = 3
        bridge.meters["knot"] = 1
    elif problem == "dim":
        if charm.meters["power"] < 1:
            raise StoryError("The dim stitch needs a magical charm.")
        charm.meters["power"] = 0
        bridge.meters["magic"] = 1
        bridge.meters["strength"] = 3
    elif problem == "slack":
        bridge.meters["length"] = 2
        bridge.meters["strength"] = 3
        bridge.meters["taut"] = 1


def cross_bridge(world: World) -> bool:
    bridge = world.entities["bridge"]
    lamb = world.entities["lamb"]
    bridge.meters["tested"] += 1
    good = bridge.meters["strength"] >= 3 and bridge.meters["magic"] >= 1
    if good:
        lamb.location = "far_side"
        lamb.meters["crossed"] = 1
    return good


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    h = world.entities["hero"].label
    f = world.entities["friend"].label
    charm = world.entities["charm"].label

    world.narrate(
        "beginning",
        f"By the hill where the moonflowers gleamed, {h} and {f} found a "
        f"gingham bridge stretched over a silver stream. A little lamb stood "
        f"beside it, waiting to cross to the clover dream.",
    )
    world.say("hero", "Shall we lead the lamb across the bridge?")
    world.say("friend", "Yes, but let us listen before we leap.")

    world.narrate(
        "inspection",
        f"They tapped the gingham squares and watched the moonlight wink. "
        f"The bridge showed {PROBLEMS[params.problem]}.",
        question="What did the friends do before repairing the bridge?",
        cause="They listened and inspected the gingham bridge instead of rushing onto it.",
        result="They discovered the particular trouble that needed mending.",
    )
    problem = inspect_problem(world)
    world.entities["friend"].beliefs["problem"] = problem
    world.entities["hero"].beliefs["problem"] = problem

    if problem == "loose":
        world.say(
            "friend",
            "The knot is loose. A hard tug would make it slip.",
            to="hero",
            reveal="problem",
        )
        world.say("hero", "Then I will not tug. What shall I do?")
        world.say("friend", "Tie it softly, square by square, and press the knot flat.")
        world.say("hero", "Will the gingham remember the way?")
        world.say("friend", "Magic remembers careful hands.")
        repair_bridge(world)
        world.narrate(
            "repair",
            f"{h} crossed one gingham stripe over another while {f} held the "
            f"bridge still. Together they made a firm little knot.",
            question="Why did the friends tie the gingham knot softly?",
            cause="The old knot was loose and could slip under a hard tug.",
            result="They made a flat, careful knot that strengthened the bridge.",
        )
    elif problem == "dim":
        world.say(
            "friend",
            "The magic stitch is dim. The bridge needs a bright heart.",
            to="hero",
            reveal="problem",
        )
        world.say("hero", f"I have {charm}. Could it help?")
        world.say("friend", "Only if we place it where the moon can see.")
        world.say("hero", "Then tell me the right place.")
        world.say("friend", "At the center square, where every thread meets.")
        repair_bridge(world)
        world.narrate(
            "repair",
            f"{h} set {charm} in the center square while {f} whispered a "
            "small rhyme. The gingham began to glow from thread to thread.",
            question="Why did the friends place the charm in the center?",
            cause="The bridge's magic stitch had grown dim.",
            result="The center charm woke the connected gingham threads.",
        )
    else:
        world.say(
            "friend",
            "The ribbon rail is slack. The bridge droops like a sleepy cat.",
            to="hero",
            reveal="problem",
        )
        world.say("hero", "Can we pull it tight?")
        world.say("friend", "A little, but not too far. The lamb needs a short road.")
        world.say("hero", "I will fold the long end to the next gingham square.")
        world.say("friend", "Good. A snug bridge is safer than a stretched one.")
        repair_bridge(world)
        world.narrate(
            "repair",
            f"{h} folded the long gingham end to the next square, and {f} "
            "pressed the fold beneath a moonlit button.",
            question="How did the friends fix the slack ribbon rail?",
            cause="The ribbon stretched too far and made the bridge droop.",
            result="They folded it to a shorter, snug length instead of pulling it harder.",
        )

    world.say("hero", "May we test it with a tiny step?")
    world.say("friend", "Yes. One hoof, then two, and we watch together.")
    if not cross_bridge(world):
        raise StoryError("The repaired magical bridge did not support the lamb.")
    world.narrate(
        "crossing",
        f"The lamb placed one hoof on the gingham, then another. The bridge "
        f"held firm, and the little creature pattered over the silver stream.",
        question="How did they test the repaired bridge?",
        cause="They used the lamb's small, careful steps instead of a wild rush.",
        result="The bridge held while the lamb crossed to the far side.",
    )
    world.say("friend", "The lamb is safe. Your careful knot made the difference.")
    world.say("hero", "Our words made the knot, and our listening found the way.")
    world.entities["hero"].memes.update(worry=0.0, trust=1.0)
    world.entities["friend"].memes.update(worry=0.0, trust=1.0)
    world.narrate(
        "ending",
        f"On the far bank, the lamb nibbled clover beneath the stars. The "
        f"gingham bridge shimmered softly, and {h} and {f} sang together: "
        "'Tie with care, share the tune, magic mends beneath the moon.'",
    )

    sample = world.sample()
    check_sample(sample)
    return sample


ASP_RULES = """
valid(P) :- problem(P), fixes(P,R), repair(R).
#show valid/1.
"""


def asp_facts() -> str:
    from asp import fact

    return "\n".join(
        [fact("problem", "loose"), fact("problem", "dim"), fact("problem", "slack")]
        + [
            fact("repair", "knot"),
            fact("repair", "charm"),
            fact("repair", "fold"),
        ]
        + [
            fact("fixes", "loose", "knot"),
            fact("fixes", "dim", "charm"),
            fact("fixes", "slack", "fold"),
        ]
    )


def asp_pairs() -> set[tuple[str]]:
    from asp import atoms, one_model

    return set(atoms(one_model(asp_facts() + ASP_RULES), "valid"))


def check_sample(sample: StorySample):
    world = sample.world
    bridge = world.entities["bridge"]
    lamb = world.entities["lamb"]
    if lamb.meters["crossed"] != 1 or lamb.location != "far_side":
        raise StoryError("The ending must show the lamb crossing the repaired bridge.")
    if bridge.meters["tested"] != 1:
        raise StoryError("The bridge must be tested exactly once after repair.")
    speeches = [event for event in world.history if event.kind == "speech"]
    if len(speeches) < 10:
        raise StoryError("The nursery-rhyme story needs a sustained exchange.")
    if any(sum(event.speaker == key for event in speeches) < 4 for key in ("hero", "friend")):
        raise StoryError("Both friends need several spoken turns.")
    if not any(event.revealed for event in speeches):
        raise StoryError("Useful knowledge must pass through the dialogue.")
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs grounded questions and answers.")
    if any(
        world.entities[key].memes["trust"] < 1 for key in ("hero", "friend")
    ):
        raise StoryError("The friends must finish with trust restored.")
    if "gingham" not in sample.story.lower():
        raise StoryError("The story must visibly use gingham.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--charm", choices=tuple(CHARMS))
    parser.add_argument("--problem", choices=tuple(PROBLEMS))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    friend_choices = [name for name in NAMES if name != hero]
    friend = args.friend or rng.choice(friend_choices)
    params = StoryParams(
        hero=hero,
        friend=friend,
        charm=args.charm or rng.choice(tuple(CHARMS)),
        problem=args.problem or rng.choice(tuple(PROBLEMS)),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    expected = {("loose",), ("dim",), ("slack",)}
    actual = asp_pairs()
    if actual != expected:
        raise StoryError("Python and ASP disagree about valid bridge troubles.")
    tested = 0
    for problem in PROBLEMS:
        for charm in CHARMS:
            sample = generate(
                StoryParams(problem=problem, charm=charm, seed=tested)
            )
            check_sample(sample)
            tested += 1
    print(f"OK: {tested} magical nursery-rhyme states; ASP parity confirmed.")


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
            print(json.dumps(sorted(asp_pairs())))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            params_list = []
            for problem in PROBLEMS:
                for charm in CHARMS:
                    params_list.append(
                        StoryParams(
                            hero=args.hero or NAMES[len(params_list) % len(NAMES)],
                            friend=args.friend
                            or NAMES[(len(params_list) + 1) % len(NAMES)],
                            problem=problem,
                            charm=charm,
                            seed=args.seed,
                        )
                    )
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]

        samples = [generate(params) for params in params_list]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(
                json.dumps(
                    payload[0] if len(payload) == 1 else payload,
                    ensure_ascii=False,
                    indent=2,
                )
            )
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
