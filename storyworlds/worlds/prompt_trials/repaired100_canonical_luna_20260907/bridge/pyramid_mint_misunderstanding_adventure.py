#!/usr/bin/env python3
"""A mint, a pyramid, and a misunderstanding that becomes a careful adventure."""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
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
    hero: str = "Luna"
    guide: str = "Omar"
    misunderstanding: str = "echo"
    clue: str = "mint"
    route: str = "steps"
    seed: int = 777


NAMES = ("Luna", "Omar", "Iris", "Niko", "Tara", "Pia")
MISUNDERSTANDINGS = ("echo", "shadow", "map")
CLUES = ("mint", "feather", "bell")
ROUTES = ("steps", "tunnel")

PROMPT = (
    "Write an adventurous children's story about Luna exploring a small pyramid, "
    "misunderstanding a clue, and learning to listen carefully while finding a mint."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity(
                id="hero",
                label=params.hero,
                kind="character",
                location="camp",
                memes={"curiosity": 1.0, "worry": 0.2, "trust": 0.5},
            ),
            "guide": Entity(
                id="guide",
                label=params.guide,
                kind="character",
                location="camp",
                memes={"patience": 1.0, "trust": 0.5},
            ),
            "pyramid": Entity(
                id="pyramid",
                label="the little pyramid",
                kind="place",
                location="dune",
                meters={"steps": 12, "door_open": 0, "darkness": 1},
                memes={"mystery": 1.0},
            ),
            "mint": Entity(
                id="mint",
                label="the silver mint",
                kind="treasure",
                location="hidden_chamber",
                meters={"found": 0, "safe": 1},
                memes={"wonder": 1.0},
            ),
            "clue": Entity(
                id="clue",
                label="the painted clue",
                kind="sign",
                location="pyramid_entrance",
                beliefs={"meaning": "listen for the answer before choosing a path"},
            ),
            "lamp": Entity(
                id="lamp",
                label="the little lamp",
                kind="tool",
                location="camp",
                meters={"lit": 1, "oil": 3},
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
        tag: str = "said",
    ):
        actor = self.entities[speaker]
        if reveal:
            if not to or reveal not in actor.beliefs:
                raise StoryError("A speaker cannot share a clue they do not understand.")
            self.entities[to].beliefs[reveal] = actor.beliefs[reveal]
        if text.endswith("?") and tag == "said":
            tag = "asked"
        if text.endswith("."):
            text = text[:-1] + ","
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
                    question="What is the safe way to explore a mysterious place?",
                    answer="A careful explorer listens to clues, checks a route, and stays with a trusted helper.",
                ),
                QAItem(
                    question="Why can a misunderstanding be dangerous?",
                    answer="It can make someone choose the wrong path before they know what the clue means.",
                ),
            ],
            world=self,
        )


def validate_params(params: StoryParams):
    if params.misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError("Choose a recognized misunderstanding.")
    if params.clue not in CLUES:
        raise StoryError("Choose a recognized clue.")
    if params.route not in ROUTES:
        raise StoryError("Choose a recognized route.")
    if params.hero == params.guide:
        raise StoryError("The explorer and guide need different names.")
    for name in (params.hero, params.guide):
        if not re.fullmatch(r"[A-Z][a-z]+", name):
            raise StoryError("Use simple capitalized names, such as Luna and Omar.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    world.entities["clue"].label = {
        "mint": "the painted mint clue",
        "feather": "the painted feather clue",
        "bell": "the painted bell clue",
    }[params.clue]
    if params.route == "tunnel":
        world.entities["pyramid"].meters["steps"] = 7
    return world


def choose_route(world: World) -> str:
    hero = world.entities["hero"]
    if hero.beliefs.get("clue_meaning") != "listen":
        raise StoryError("The explorer must understand the clue before choosing a route.")
    return world.params.route


def enter_pyramid(world: World):
    pyramid = world.entities["pyramid"]
    if not pyramid.meters["door_open"]:
        raise StoryError("The pyramid door must be opened before entering.")
    pyramid.meters["darkness"] = 0
    world.entities["hero"].location = "pyramid_hall"
    world.entities["guide"].location = "pyramid_hall"


def find_mint(world: World):
    mint = world.entities["mint"]
    route = world.params.route
    if route == "steps":
        if world.entities["pyramid"].meters["steps"] != 12:
            raise StoryError("The stair route no longer matches the pyramid.")
    else:
        if world.entities["lamp"].meters["oil"] < 1:
            raise StoryError("The tunnel needs enough lamp oil.")
        world.entities["lamp"].meters["oil"] -= 1
    mint.location = "hero_hand"
    mint.meters["found"] = 1
    world.entities["hero"].memes["worry"] = 0.0


def check_ending(world: World):
    if not world.entities["mint"].meters["found"]:
        raise StoryError("The adventure must end with the mint found.")
    if world.entities["mint"].location != "hero_hand":
        raise StoryError("The mint must be safely carried by the explorer.")
    if world.entities["hero"].location != "pyramid_hall":
        raise StoryError("The explorer must remain with the guide inside the pyramid.")
    if world.entities["hero"].memes["worry"] > 0.1:
        raise StoryError("The final trace should show that the misunderstanding was resolved.")
    speech = [event for event in world.history if event.kind == "speech"]
    if len(speech) < 12:
        raise StoryError("The adventure needs a sustained exchange between the characters.")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero = world.entities["hero"].label
    guide = world.entities["guide"].label
    mint = world.entities["mint"].label
    clue = world.entities["clue"].label

    world.narrate(
        "beginning",
        f"{hero} and {guide} reached a small pyramid at the edge of the warm desert. "
        f"Inside, an old story promised a silver mint, but the doorway had no handle—only {clue}.",
    )
    world.say("hero", "The pyramid is smaller than I imagined. Can we really find the mint?")
    world.say("guide", "We can look, but we must understand the clue before we hurry inside.")
    world.say("hero", "It shows a moon, a feather, and a little ear. I think the moon means the dark tunnel.")
    world.say("guide", "Maybe. What does the ear tell us?")
    world.say("hero", "That someone heard a secret?")
    world.say("guide", "Or that we should listen before we choose.")

    world.entities["guide"].beliefs["clue_meaning"] = "listen"
    world.entities["hero"].memes["worry"] = 0.6

    if params.misunderstanding == "echo":
        world.narrate(
            "misunderstanding",
            f"{hero} tapped the stone. A hollow echo answered from the pyramid. "
            f"{hero} mistook the echo for a voice calling from the tunnel.",
            question="What did Luna misunderstand?",
            cause="An echo made by the hollow stone sounded like a voice.",
            result=f"{hero} thought the tunnel was calling and nearly chose it without checking the clue.",
        )
        world.say("hero", "There! The pyramid told us to take the tunnel.")
        world.say("guide", "It made an echo when you tapped it. A sound is not always an instruction.")
        world.say("hero", "Then how can we tell what is an instruction?")
    elif params.misunderstanding == "shadow":
        world.narrate(
            "misunderstanding",
            f"A long shadow crossed the painted doorway. {hero} thought it pointed toward the tunnel, "
            f"but the shadow came from the guide's waving scarf.",
            question="What did Luna misunderstand?",
            cause="A scarf cast a long shadow across the doorway.",
            result=f"{hero} mistook the moving shadow for an arrow toward the tunnel.",
        )
        world.say("hero", "The shadow points left. That must be the way.")
        world.say("guide", "Watch my scarf. The shadow moves when I move, so it is not a pyramid arrow.")
        world.say("hero", "Then how can we tell what is an instruction?")
    else:
        world.narrate(
            "misunderstanding",
            f"{hero} read the painted mark backward. The tiny mint picture looked like a green door, "
            f"so {hero} thought the door itself was the treasure.",
            question="What did Luna misunderstand?",
            cause="The tiny mint picture looked like a green door when read backward.",
            result=f"{hero} mistook the entrance for the treasure instead of looking for the mint inside.",
        )
        world.say("hero", "The green door must be the mint. We have already found it.")
        world.say("guide", "That is a picture of the mint, not the mint itself.")
        world.say("hero", "Then how can we tell what is an instruction?")

    world.say("guide", "We can test it. Look at the ear, then listen for the sound that follows the mark.")
    world.say("hero", "I hear a faint drip behind the wall.")
    world.say("guide", "Good. The clue says to listen, not to chase the first thing we notice.")
    world.entities["hero"].beliefs["clue_meaning"] = "listen"
    world.entities["hero"].memes["worry"] = 0.3
    world.entities["pyramid"].meters["door_open"] = 1

    world.narrate(
        "turn",
        f"{hero} pressed the ear-shaped stone. The doorway opened with a soft click. "
        f"The drip came from a safe passage behind the first wall.",
        question="How did the children correct the misunderstanding?",
        cause=f"{guide} asked {hero} to test the clue by listening instead of guessing.",
        result="They discovered that the ear-shaped mark was an instruction to listen, and the doorway opened.",
    )

    enter_pyramid(world)
    world.say("hero", "The dark is not a voice anymore. It is just a dark hallway.")
    world.say("guide", "And the lamp makes it a hallway we can inspect.")
    world.say("hero", "Should we use the stairs or follow the drip?")
    world.say("guide", "The clue gave us a choice. We can use the lit stairs, or use the lamp in the tunnel.")
    world.say("hero", "I will choose the route we can explain and check.")
    route = choose_route(world)

    if route == "steps":
        world.narrate(
            "route",
            f"They climbed the twelve broad stone steps, touching the wall at each turn. "
            f"The steps led to a small chamber above the dripping passage.",
            question="Why did they climb the steps?",
            cause="The steps were broad, visible, and easy to check as they climbed.",
            result="The pair reached the upper chamber together without rushing into the dark tunnel.",
        )
    else:
        world.narrate(
            "route",
            f"They followed the drip through the short tunnel. {guide} held the lamp low while "
            f"{hero} checked each stone before placing a foot.",
            question="How did they travel through the tunnel safely?",
            cause="The tunnel was dark, so the guide held the lamp and the explorer checked each stone.",
            result="They followed the sound carefully and reached the chamber without losing their way.",
        )

    find_mint(world)
    world.say("hero", "There it is—the silver mint beneath the moon mark.")
    world.say("guide", "Lift it slowly. A treasure is better when it arrives safely.")
    world.say("hero", "I thought the first sound, shadow, or picture told us the answer.")
    world.say("guide", "Now you know to ask what caused it, and what the clue really says.")
    world.entities["guide"].memes["trust"] = 1.0
    world.entities["hero"].memes["worry"] = 0.0

    world.narrate(
        "ending",
        f"{hero} carried {mint} back beside {guide}, while the little pyramid glowed in the evening light. "
        f"They left the doorway open for the next careful listener.",
        question="What changed by the end of the adventure?",
        cause=f"{hero} stopped treating the first impression as an answer and listened with {guide}.",
        result=f"{hero} found the silver mint safely and carried it out with the guide.",
    )

    check_ending(world)
    sample = world.sample()
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    if not sample.story.strip():
        raise StoryError("The generated story cannot be empty.")
    if "None" in sample.story or "{" in sample.story or "}" in sample.story:
        raise StoryError("The story contains an unresolved template.")
    if "meters" in sample.story or "internal" in sample.story:
        raise StoryError("Internal world terminology leaked into the story.")
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs at least three grounded questions.")
    speech = [event for event in sample.world.history if event.kind == "speech"]
    if not any(event.revealed for event in speech):
        raise StoryError("The dialogue must pass useful understanding between characters.")
    if not any(event.speaker == "hero" and event.listener == "guide" for event in speech):
        raise StoryError("The story needs back-and-forth dialogue.")
    if sample.world.entities["mint"].meters["found"] != 1:
        raise StoryError("The mint must be found in the simulated world.")


ASP_RULES = """
valid_misunderstanding(echo).
valid_misunderstanding(shadow).
valid_misunderstanding(map).
valid_clue(mint).
valid_clue(feather).
valid_clue(bell).
valid_route(steps).
valid_route(tunnel).
compatible(M,C,R) :- valid_misunderstanding(M), valid_clue(C), valid_route(R).
#show compatible/3.
"""


def asp_facts() -> str:
    from asp import fact

    facts = []
    for value in MISUNDERSTANDINGS:
        facts.append(fact("valid_misunderstanding", value))
    for value in CLUES:
        facts.append(fact("valid_clue", value))
    for value in ROUTES:
        facts.append(fact("valid_route", value))
    return "\n".join(facts)


def asp_combos() -> set[tuple[str, str, str]]:
    from asp import atoms, one_model

    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "compatible"))


def valid_combos() -> set[tuple[str, str, str]]:
    return {
        (misunderstanding, clue, route)
        for misunderstanding in MISUNDERSTANDINGS
        for clue in CLUES
        for route in ROUTES
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--guide")
    parser.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    parser.add_argument("--clue", choices=CLUES)
    parser.add_argument("--route", choices=ROUTES)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    possibilities = [
        combo
        for combo in sorted(valid_combos())
        if (args.misunderstanding is None or combo[0] == args.misunderstanding)
        and (args.clue is None or combo[1] == args.clue)
        and (args.route is None or combo[2] == args.route)
    ]
    if not possibilities:
        raise StoryError("No compatible story choices match these options.")
    misunderstanding, clue, route = rng.choice(possibilities)
    hero = args.hero or rng.choice(
        [name for name in NAMES if name != args.guide]
    )
    guide = args.guide or rng.choice([name for name in NAMES if name != hero])
    params = StoryParams(
        hero=hero,
        guide=guide,
        misunderstanding=misunderstanding,
        clue=clue,
        route=route,
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if valid_combos() != asp_combos():
        raise StoryError("Python and ASP disagree about valid story combinations.")
    count = 0
    for misunderstanding, clue, route in sorted(valid_combos()):
        for hero, guide in (("Luna", "Omar"), ("Iris", "Niko")):
            sample = generate(
                StoryParams(
                    hero=hero,
                    guide=guide,
                    misunderstanding=misunderstanding,
                    clue=clue,
                    route=route,
                )
            )
            check_sample(sample)
            count += 1
    print(f"OK: {count} story states; {len(valid_combos())} ASP-compatible combinations.")


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
                ensure_ascii=False,
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
            print(json.dumps(sorted(asp_combos()), ensure_ascii=False))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            combos = [
                combo
                for combo in sorted(valid_combos())
                if (args.misunderstanding is None or combo[0] == args.misunderstanding)
                and (args.clue is None or combo[1] == args.clue)
                and (args.route is None or combo[2] == args.route)
            ]
            if not combos:
                raise StoryError("No combinations match the selected options.")
            params_list = [
                StoryParams(
                    hero=args.hero or "Luna",
                    guide=args.guide or "Omar",
                    misunderstanding=misunderstanding,
                    clue=clue,
                    route=route,
                    seed=args.seed,
                )
                for misunderstanding, clue, route in combos
            ]
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
                    header=f"\n### Story {index + 1}\n"
                    if len(samples) > 1
                    else "",
                )
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
