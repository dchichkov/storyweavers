#!/usr/bin/env python3
"""
A small mystery storyworld about a hidden mechanism, friendship, caution, and a twist.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


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
sys.path.insert(0, os.path.dirname(_storyworlds_dir))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    hero: str = "Luna"
    friend: str = "Mira"
    place: str = "the old clocktower"
    object_name: str = "the brass music box"
    arc: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    hero: Entity
    friend: Entity
    object_entity: Entity
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


HERO_NAMES = ["Luna", "Nell", "Iris", "Pia", "Tess", "Mara"]
FRIEND_NAMES = ["Mira", "Owen", "Juno", "Finn", "Ravi", "Bea"]
PLACES = [
    "the old clocktower",
    "the shuttered observatory",
    "the ivy-covered museum",
    "the lantern room by the river",
]
OBJECTS = [
    "the brass music box",
    "the silver puzzle clock",
    "the blue wooden cabinet",
    "the tiny glass compass",
]

ARCS = [
    {
        "premise": "A faint ticking began behind a locked display case just before sunset",
        "problem": "the tower bell was counting down to an unknown hour",
        "stake": "If they forced the case open, its delicate mechanism might break and the bell might never ring again",
        "clue": "three dust-free gear marks formed a path from the case to the winding stair",
        "mechanism": "a hidden chain of gears turned the display case into a key for the bell room",
        "twist": "the ticking was not a warning from the tower; it was a message left by the vanished clockmaker",
        "solution": "They used the marks to turn the case's small wheel one careful notch at a time",
        "ending": "the bell rang once, and a folded map slid from beneath its velvet cushion",
        "lesson": "friendship means slowing down when someone you trust notices danger",
        "question": "Why did Luna and Mira avoid forcing the display case?",
        "answer": "They avoided forcing it because the delicate mechanism could break and silence the tower bell.",
    },
    {
        "premise": "A cold blue light blinked inside the shuttered observatory",
        "problem": "the telescope had begun turning by itself toward the dark river",
        "stake": "A loose gear could crack the lens if they grabbed the telescope suddenly",
        "clue": "the light blinked whenever the brass floor plate was tapped twice",
        "mechanism": "a spring beneath the floor plate controlled the telescope's slow movement",
        "twist": "the telescope was not searching for a thief; it was following a constellation drawn by the observatory's first child visitor",
        "solution": "They tapped twice, waited for the spring to settle, and guided the telescope with its wooden handle",
        "ending": "the lens revealed a bright star shaped like a tiny key",
        "lesson": "careful friends investigate a mystery without turning fear into a reckless rush",
        "question": "What clue explained the observatory's blinking light?",
        "answer": "The light blinked whenever the brass floor plate was tapped twice, showing that the plate controlled the mechanism.",
    },
    {
        "premise": "A locked cabinet whispered whenever rain touched the museum roof",
        "problem": "the whispering latch was pulling harder against its tiny spring",
        "stake": "A sudden tug could fling the cabinet door into the oldest paintings",
        "clue": "the whisper stopped whenever Luna held Mira's red scarf near the keyhole",
        "mechanism": "a magnet hidden inside the latch responded to the scarf's small metal clasp",
        "twist": "the cabinet held no stolen treasure; it protected letters from friends who had built the museum together",
        "solution": "They used the clasp to ease the latch open instead of prying it",
        "ending": "the letters unfolded beneath a lamp, each one ending with the same promise to help a friend",
        "lesson": "a cautious pause can reveal that a frightening mystery has a gentle heart",
        "question": "How did Luna and Mira open the cabinet safely?",
        "answer": "They used the metal clasp on Mira's red scarf to guide the magnet in the latch instead of prying the door.",
    },
    {
        "premise": "The river lantern room flashed three times after midnight",
        "problem": "its turning mirror had stopped facing the boats",
        "stake": "Boats might miss the narrow channel in the morning fog",
        "clue": "a trail of wet footprints ended beside a box of spare wooden teeth",
        "mechanism": "the lantern's mirror moved through a wooden gear train",
        "twist": "the footprints belonged to an otter carrying a loose gear, not to a person sneaking through the room",
        "solution": "They replaced the missing tooth and tested the mirror with a covered lamp",
        "ending": "the repaired lantern sent a calm golden beam across the river",
        "lesson": "good friends check evidence before blaming someone they cannot see",
        "question": "Who had carried away the loose gear?",
        "answer": "An otter had carried away the loose gear, leaving the wet footprints by the box.",
    },
    {
        "premise": "A tiny glass compass spun on a table in the ivy-covered museum",
        "problem": "its needle pointed toward a sealed wall instead of north",
        "stake": "A hurried search might damage the old stones and the compass",
        "clue": "the needle steadied whenever Luna and Mira stood shoulder to shoulder",
        "mechanism": "two hidden magnets beneath the floor balanced the compass needle",
        "twist": "the sealed wall was not a secret tunnel; it was a removable panel hiding a friendship mural",
        "solution": "They stood together, marked the needle's direction, and lifted the panel from its safe hinge",
        "ending": "painted hands covered the mural, with a blank space waiting for two new names",
        "lesson": "trust can steady a mystery just as surely as a careful tool",
        "question": "What made the compass needle steady?",
        "answer": "The needle steadied when Luna and Mira stood together because hidden magnets balanced it beneath the floor.",
    },
]


OPENINGS = [
    "Moonlight silvered the windows",
    "Rain whispered along the roof",
    "A pale moon climbed above the town",
    "The last daylight faded behind the chimneys",
    "Mist curled around the silent stones",
]

DIALOGUE = [
    ("“Do you hear that?” Luna whispered.", "“Yes,” Mira replied. “But hearing a mystery is not the same as solving it.”"),
    ("“We could pull it open,” Luna said.", "“We could,” Mira answered, “but a careful friend checks the hinges first.”"),
    ("“Something is moving,” Luna murmured.", "“Then let us watch before we touch,” Mira said."),
    ("“What if someone is hiding?” Luna asked.", "“Then our questions should be kinder than our guesses,” Mira replied."),
]

CAUTION_LINES = [
    "Luna reached toward the strange device, then stopped with her fingers a handspan away.",
    "The mechanism clicked, and both friends stepped back until they could see every moving part.",
    "They placed a lamp on the floor and watched the shadows instead of poking into the darkness.",
    "Mira tied a bright ribbon to the door so they could find their way out if the room shifted.",
]

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A mystery storyworld about a mechanism, friendship, caution, and a twist."
    )
    parser.add_argument("--hero", choices=HERO_NAMES)
    parser.add_argument("--friend", choices=FRIEND_NAMES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--object-name", choices=OBJECTS)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HERO_NAMES)
    choices = [name for name in FRIEND_NAMES if name != hero]
    friend = args.friend or rng.choice(choices)
    if hero == friend:
        raise StoryError("The hero and friend must be different characters.")
    return StoryParams(
        hero=hero,
        friend=friend,
        place=args.place or rng.choice(PLACES),
        object_name=args.object_name or rng.choice(OBJECTS),
        arc=rng.randrange(len(ARCS)),
        seed=args.seed,
    )


def build_world(params: StoryParams) -> World:
    return World(
        params=params,
        hero=Entity(params.hero, "hero"),
        friend=Entity(params.friend, "friend"),
        object_entity=Entity(params.object_name, "mechanism"),
    )


def simulate(world: World) -> None:
    p = world.params
    arc = ARCS[p.arc]
    rng = random.Random(p.seed)

    world.hero.memes["curiosity"] = 1.0
    world.hero.memes["caution"] = 1.0
    world.friend.memes["trust"] = 1.0
    world.object_entity.meters["complexity"] = 3.0
    world.facts.update(
        {
            "place": p.place,
            "object": p.object_name,
            "problem": arc["problem"],
            "mechanism": arc["mechanism"],
            "clue": arc["clue"],
            "twist": arc["twist"],
            "resolved": False,
        }
    )

    world.say(
        f"{rng.choice(OPENINGS)} over {p.place}. "
        f"{p.hero} and {p.friend} had come to inspect {p.object_name}, "
        "which had been silent for many years."
    )
    world.say(f"{arc['premise']}. {arc['problem']}.")
    world.say(f"{p.hero} understood that {arc['stake']}.")
    world.para()

    first, second = rng.choice(DIALOGUE)
    world.say(first)
    world.say(second)
    world.say(rng.choice(CAUTION_LINES))
    world.say(
        f"Instead of guessing, {p.hero} and {p.friend} followed the clue: {arc['clue']}."
    )
    world.hero.memes["impulse_checked"] = 1.0
    world.friend.memes["helped_investigate"] = 1.0
    world.facts["clue_found"] = True
    world.para()

    world.say(
        f"Behind the panel they discovered the mechanism: {arc['mechanism']}."
    )
    world.say(f"Together, they chose the safe method: {arc['solution']}.")
    world.say(
        f"Then came the twist. {arc['twist']}. "
        f"{p.friend} smiled, but kept one hand near the lamp in case the old room changed again."
    )
    world.facts["twist_revealed"] = True
    world.facts["solution"] = arc["solution"]
    world.hero.memes["trust"] = 1.0
    world.friend.memes["trust"] = 1.0
    world.para()

    world.say(
        f"{arc['ending']}. {p.hero} realized that {arc['lesson']}."
    )
    world.say(
        f"{p.hero} and {p.friend} left {p.place} side by side, "
        "closing the door gently so the mystery could rest."
    )
    world.facts["resolved"] = True
    world.facts["ending_image"] = arc["ending"]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
    arc = ARCS[params.arc]
    prompts = [
        f"Write a child-friendly mystery about {params.hero} and {params.friend} investigating {params.object_name}.",
        f"Tell a cautionary friendship tale in {params.place} involving a hidden mechanism and a surprising twist.",
        f"Create a gentle mystery where careful observation solves this problem: {arc['problem']}.",
    ]
    story_qa = [
        QAItem(
            question=f"What mystery did {params.hero} and {params.friend} investigate?",
            answer=f"They investigated the strange behavior of {params.object_name} at {params.place}.",
        ),
        QAItem(
            question="What clue helped them?",
            answer=f"The clue was that {arc['clue']}.",
        ),
        QAItem(
            question="What mechanism did they discover?",
            answer=f"They discovered that {arc['mechanism']}.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {arc['twist']}.",
        ),
        QAItem(
            question=f"What did {params.hero} learn from {params.friend}?",
            answer=f"{params.hero} learned that {arc['lesson']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of connected parts that work together to make something move or function.",
        ),
        QAItem(
            question="Why is caution useful in a mystery?",
            answer="Caution is useful because it lets people study clues and avoid damaging objects or making danger worse.",
        ),
        QAItem(
            question="What is a twist?",
            answer="A twist is a surprising discovery that changes how the earlier clues are understood.",
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in [world.hero, world.friend, world.object_entity]:
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.name:24} ({entity.kind:10}) meters={meters} memes={memes}"
        )
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/1.
valid(story) :-
    domain(mechanism),
    feature(friendship),
    feature(cautionary),
    feature(twist),
    feature(mystery).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    facts = [
        asp.fact("domain", "mechanism"),
        asp.fact("feature", "friendship"),
        asp.fact("feature", "cautionary"),
        asp.fact("feature", "twist"),
        asp.fact("feature", "mystery"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "#show valid/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program())
    if asp.atoms(model, "valid") != [("story",)]:
        print("MISMATCH: ASP twin failed.")
        return 1

    for params in CURATED:
        sample = generate(params)
        if not sample.story or not sample.world.facts.get("resolved"):
            print("MISMATCH: generated story did not resolve.")
            return 1

    print("OK: ASP twin is consistent and generated stories resolve.")
    return 0


CURATED = [
    StoryParams(
        hero="Luna",
        friend="Mira",
        place="the old clocktower",
        object_name="the brass music box",
        arc=0,
        seed=101,
    ),
    StoryParams(
        hero="Iris",
        friend="Finn",
        place="the shuttered observatory",
        object_name="the tiny glass compass",
        arc=1,
        seed=202,
    ),
    StoryParams(
        hero="Nell",
        friend="Juno",
        place="the lantern room by the river",
        object_name="the blue wooden cabinet",
        arc=3,
        seed=303,
    ),
]


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program())
        print(asp.atoms(model, "valid"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1.")
        seen: set[str] = set()
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

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
