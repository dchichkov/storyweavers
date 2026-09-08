#!/usr/bin/env python3
"""
A small slice-of-life magic world about a child, a stubborn window sill,
and the quiet conflict between keeping a promise and wanting to hurry.
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
import hashlib
import json
import random
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    child: str = "Luna"
    companion: str = "Mara"
    sill: str = "the kitchen sill"
    task: str = "help a moonflower open"
    feeling: str = "patient"
    seed: Optional[int] = None


@dataclass
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(
        default_factory=lambda: {"energy": 1.0, "attention": 0.5}
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {"care": 0.0, "confidence": 0.0, "patience": 0.0}
    )


@dataclass
class World:
    child: Person
    companion: Person
    sill: str
    task: str
    conflict: str = ""
    magic: str = ""
    clue: str = ""
    first_attempt: str = ""
    resolution: str = ""
    lesson: str = ""
    ending: str = ""
    moonlight: float = 0.2
    flower_health: float = 0.5
    promise_kept: bool = False
    magic_awake: bool = False
    transformed: bool = False
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


NAMES = ["Luna", "Iris", "Milo", "Nia", "Tavi", "Sora"]
COMPANIONS = ["Mara", "Aunt Jo", "Dad", "Grandma", "Uncle Ren"]
FEELINGS = ["patient", "brave", "careful", "hopeful", "thoughtful"]

SCENES = [
    {
        "conflict": "The moonflower had wrapped one pale tendril around the curtain cord, and pulling it free might snap its new leaves.",
        "magic": "Whenever Luna placed a warm pebble beside the pot, the flower made a tiny silver chime.",
        "clue": "The chime sounded only when the pebble rested on the sill's sunniest corner.",
        "first_attempt": "reached for the cord, then pulled her hand back",
        "resolution": "Mara loosened the cord while Luna held a lamp steady, and the tendril slipped free without a tear.",
        "lesson": "a magical problem still deserves ordinary care",
        "ending": "By bedtime, the moonflower had opened one white bloom toward the glass.",
    },
    {
        "conflict": "A gust pushed the little clay star off the sill, but the flower's pot was balanced behind it.",
        "magic": "The fallen star whispered the last kind thing someone had said near the window.",
        "clue": "Its whisper grew louder whenever Luna moved the pot farther from the edge.",
        "first_attempt": "tried to catch the star quickly, nearly bumping the pot",
        "resolution": "Luna asked Mara to steady the pot first, then picked up the star and set both objects safely in the middle.",
        "lesson": "helping one precious thing should not put another at risk",
        "ending": "The clay star rested beside the flower, whispering softly as evening settled.",
    },
    {
        "conflict": "Dust had covered the sill, and the old window would not close around a bright blue moth.",
        "magic": "The moth left glowing dots wherever it touched the dusty wood.",
        "clue": "The dots formed an arrow toward a loose latch.",
        "first_attempt": "wiped at the sill in a hurry, scattering dust into the room",
        "resolution": "Luna slowed down, used a damp cloth, and showed Mara the loose latch before they closed it together.",
        "lesson": "a clear clue becomes useful when someone stops to notice it",
        "ending": "The moth flew out, and the clean sill held a fading trail of blue light.",
    },
    {
        "conflict": "A tiny rain puddle had gathered beneath the pot, making the wooden sill swell at one corner.",
        "magic": "The puddle reflected a second room where every dropped thing was waiting to be found.",
        "clue": "In the reflection, a folded cloth appeared exactly where the towel lay in the laundry basket.",
        "first_attempt": "reached for the pot without checking where the water was going",
        "resolution": "Luna fetched the cloth, dried the sill, and moved the pot onto a shallow tray with Mara's help.",
        "lesson": "wonder is safest when it leads to a useful action",
        "ending": "The real sill dried beneath the pot while the reflected room disappeared.",
    },
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Magic sill slice-of-life story world.")
    ap.add_argument("--child")
    ap.add_argument("--companion")
    ap.add_argument("--sill", default="the kitchen sill")
    ap.add_argument("--task", default="help a moonflower open")
    ap.add_argument("--feeling", choices=FEELINGS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if not args.sill.strip():
        raise StoryError("The sill must have a name.")
    if not args.task.strip():
        raise StoryError("The task must not be empty.")
    return StoryParams(
        child=args.child or rng.choice(NAMES),
        companion=args.companion or rng.choice(COMPANIONS),
        sill=args.sill,
        task=args.task,
        feeling=args.feeling or rng.choice(FEELINGS),
    )


def make_world(params: StoryParams) -> World:
    return World(
        child=Person(params.child, "child"),
        companion=Person(params.companion, "companion"),
        sill=params.sill,
        task=params.task,
    )


def generate_story(world: World, params: StoryParams) -> None:
    material = "|".join(
        [params.child, params.companion, params.sill, params.task, params.feeling]
    )
    seed = params.seed
    if seed is None:
        seed = int.from_bytes(
            hashlib.blake2b(material.encode(), digest_size=8).digest(), "big"
        )
    scene = SCENES[seed % len(SCENES)]

    world.conflict = scene["conflict"]
    world.magic = scene["magic"]
    world.clue = scene["clue"]
    world.first_attempt = scene["first_attempt"]
    world.resolution = scene["resolution"]
    world.lesson = scene["lesson"]
    world.ending = scene["ending"]

    world.say(
        f"On an ordinary evening, {world.child.name} stood beside {world.sill} "
        f"with {world.companion.name} and tried to {params.task}."
    )
    world.say(
        f'"I want to finish before the moon comes up," {world.child.name} said. '
        f"Inside, {world.child.name} thought, *If I hurry, perhaps the magic will notice me.*"
    )
    world.say(
        f'"Magic notices careful hands more often than fast ones," {world.companion.name} replied.'
    )
    world.child.memes["care"] += 0.5
    world.child.meters["energy"] -= 0.1

    world.say(world.conflict)
    world.say(world.magic)
    world.say(
        f"At first, {world.child.name} {world.first_attempt}. "
        f'"Wait," {world.child.name} whispered. "The sill is telling us something." '
        f"{world.clue}"
    )
    world.say(
        f'"Then let us listen before we act," {world.companion.name} said.'
    )
    world.say(world.resolution)
    world.promise_kept = True
    world.magic_awake = True
    world.flower_health += 0.35
    world.moonlight += 0.4
    world.child.memes["patience"] += 1.0
    world.child.memes["confidence"] += 0.4
    world.child.meters["attention"] += 0.4

    world.say(
        f"Together they finished the small task of trying to {params.task}, "
        "but they did not rush the last step."
    )
    world.say(
        f"Inside, {world.child.name} thought, *Perhaps being {params.feeling} "
        "is its own kind of magic.*"
    )
    world.say(
        f"{world.child.name} felt {params.feeling}, because {world.lesson}. "
        f"{world.ending}"
    )
    world.transformed = True


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            question=f"Where did {p.child} work on the magical task?",
            answer=f"{p.child} worked at {p.sill} with {p.companion}.",
        ),
        QAItem(
            question=f"What conflict interrupted {p.child}'s plan?",
            answer=world.conflict,
        ),
        QAItem(
            question="What magical sign helped them?",
            answer=world.magic,
        ),
        QAItem(
            question=f"Why did {p.child} stop the first attempt?",
            answer=(
                f"{p.child} stopped after noticing a clue: {world.clue} "
                "That clue showed that hurrying could cause more trouble."
            ),
        ),
        QAItem(
            question="How was the problem solved?",
            answer=world.resolution,
        ),
        QAItem(
            question=f"How did the experience change {p.child}?",
            answer=(
                f"{p.child} became more {p.feeling} by learning that {world.lesson}."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sill?",
            answer="A sill is the narrow ledge at the bottom of a window.",
        ),
        QAItem(
            question="Why should a person move a plant carefully?",
            answer="A person should move a plant carefully so its stems, leaves, and roots are not damaged.",
        ),
        QAItem(
            question="What does patience mean?",
            answer="Patience means waiting and acting carefully instead of rushing.",
        ),
    ]


def generation_prompts(params: StoryParams) -> list[str]:
    return [
        f"Write a slice-of-life story about {params.child} and a small piece of magic on {params.sill}.",
        f"Tell a child-friendly story where {params.child} tries to {params.task} and solves a conflict carefully.",
        f"Write a gentle magical story in which inner thoughts help {params.child} become more {params.feeling}.",
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Generation prompts =="]
    parts.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    parts.append("")
    parts.append("== Story Q&A ==")
    for item in sample.story_qa:
        parts.extend([f"Q: {item.question}", f"A: {item.answer}"])
    parts.append("")
    parts.append("== World Q&A ==")
    for item in sample.world_qa:
        parts.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(parts)


ASP_RULES = r"""
setting(sill).
feature(conflict).
feature(magic).
feature(inner_monologue).
style(slice_of_life).
task(T) :- chosen_task(T).
valid_story :-
    setting(sill),
    feature(conflict),
    feature(magic),
    feature(inner_monologue),
    style(slice_of_life),
    task(_).
#show valid_story/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("setting", "sill"),
            asp.fact("feature", "conflict"),
            asp.fact("feature", "magic"),
            asp.fact("feature", "inner_monologue"),
            asp.fact("style", "slice_of_life"),
            asp.fact("chosen_task", "help a moonflower open"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/0."))
    if any(sym.name == "valid_story" for sym in model):
        params = StoryParams(seed=17)
        sample = generate(params)
        if sample.story and sample.story_qa:
            print("OK: ASP and Python story gates passed.")
            return 0
    print("MISMATCH: ASP or Python story gate failed.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    world.facts["params"] = params
    generate_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(params),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        print("--- world trace ---")
        print(asdict(sample.params))
        print(
            {
                "flower_health": sample.world.flower_health,
                "moonlight": sample.world.moonlight,
                "promise_kept": sample.world.promise_kept,
                "magic_awake": sample.world.magic_awake,
                "transformed": sample.world.transformed,
                "child_meters": sample.world.child.meters,
                "child_memes": sample.world.child.memes,
            }
        )
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        child="Luna",
        companion="Mara",
        sill="the kitchen sill",
        task="help a moonflower open",
        feeling="patient",
    ),
    StoryParams(
        child="Iris",
        companion="Grandma",
        sill="the bedroom sill",
        task="return a glowing button to its jar",
        feeling="careful",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.asp:
        try:
            import asp
        except Exception as exc:
            raise StoryError(f"ASP mode requires clingo: {exc}") from exc
        print("ASP model:", asp.one_model(asp_program("#show valid_story/0.")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
