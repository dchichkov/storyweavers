#!/usr/bin/env python3
"""
A gentle cartoon ghost story about a misunderstanding.

Luna hears a repeated little "boo" and believes a ghost is frightening her.
By listening and speaking kindly, she learns that the ghost is trying to ask
for help soothing a lonely cartoon cloud. The story turns a spooky mistake
into care, while a small bad ending remains: the cartoon loses its happy
ending before the friends repair it together.
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
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = (
    "the old picture house at the edge of town",
    "a little cinema beneath the hill",
    "the moonlit cartoon theater by the river",
    "a quiet animation studio with dusty windows",
)

CARTOONS = (
    "a brave blue rabbit",
    "a giggling yellow star",
    "a tiny red dragon",
    "a green frog with a paper crown",
)

GHOST_NAMES = ("Pip", "Mallow", "Boo", "Wisp")
CHILD_NAMES = ("Luna", "Mira", "Tess", "Nia")

REPETITIONS = (
    "Boo from behind the curtain",
    "Tap, tap, tap from the projector booth",
    "Please, please, please from the dark aisle",
    "Hush, hush, hush beneath the seats",
)

BAD_ENDINGS = (
    "the cartoon's last scene ended with the hero alone in the rain",
    "the final picture showed the little star with no one to wave goodbye",
    "the reel stopped before the dragon found its way home",
    "the paper crown fell off just before the frog's happy dance",
)

SOOTHING_TOOLS = (
    "a soft blanket from the costume room",
    "a tinny music box from the front desk",
    "a warm lantern carried from the lobby",
    "a box of colored pencils and a clean sheet of paper",
)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    child_name: str = "Luna"
    ghost_name: str = "Pip"
    setting_place: str = SETTINGS[0]
    cartoon: str = CARTOONS[0]
    repetition: str = REPETITIONS[0]
    bad_ending: str = BAD_ENDINGS[0]
    soothing_tool: str = SOOTHING_TOOLS[0]
    samples: list = field(default_factory=list)


def _check_params(params: StoryParams) -> None:
    if not params.child_name.strip():
        raise StoryError("The child needs a name.")
    if not params.ghost_name.strip():
        raise StoryError("The ghost needs a name.")
    if params.child_name.lower() == params.ghost_name.lower():
        raise StoryError("The child and ghost must have different names.")
    if not params.cartoon or not params.repetition or not params.bad_ending:
        raise StoryError("A cartoon ghost story needs a clear cartoon, repeated sound, and bad ending.")


def tell(params: StoryParams) -> World:
    _check_params(params)
    world = World(Setting(params.setting_place))
    child = world.add(Entity("child", "character", params.child_name, memes={"curiosity": 1.0}))
    ghost = world.add(Entity("ghost", "ghost", params.ghost_name, memes={"loneliness": 1.0}))
    cartoon = world.add(Entity("cartoon", "cartoon", params.cartoon, memes={"sadness": 1.0}))
    world.facts.update(child=child, ghost=ghost, cartoon=cartoon)

    world.say(
        f"At midnight, {params.child_name} sat alone in {params.setting_place} and watched a cartoon about {params.cartoon}."
    )
    world.say(
        f"The screen flickered, and {params.bad_ending}. "
        f"{params.child_name} hugged the arm of the old theater seat."
    )

    world.para()
    world.say(f"Then came a small sound: “{params.repetition}.”")
    world.say(f"{params.child_name} looked behind the curtain, but no one was there.")
    world.say(f"The sound came again: “{params.repetition}.”")
    world.say(
        f"“That ghost is trying to scare me,” {params.child_name} whispered. "
        f"{params.child_name} pulled the blanket close and stepped toward the exit."
    )

    world.para()
    world.say(
        f"A pale little ghost drifted into the projector light. “Please wait,” said {params.ghost_name}. "
        f"“I am not trying to frighten you.”"
    )
    world.say(
        f"“But you keep saying the same spooky thing,” said {params.child_name}. "
        f"“I thought you wanted me to run away.”"
    )
    world.say(
        f"{params.ghost_name} shook a transparent head. “I repeat it because I do not know how to ask. "
        f"The cartoon is sad, and I cannot soothe it alone.”"
    )
    world.fired.add("misunderstanding_explained")

    world.para()
    world.say(
        f"{params.child_name} watched the screen again. The cartoon hero trembled beneath the unfinished ending."
    )
    world.say(
        f"“You were saying the same words to get help,” said {params.child_name}. "
        f"“You were not chasing me.”"
    )
    world.say(
        f"“Exactly,” said {params.ghost_name}. “Could we try together?”"
    )
    world.say(
        f"{params.child_name} brought {params.soothing_tool}. {params.ghost_name} hummed softly while "
        f"{params.child_name} wrapped the cartoon picture in the blanket and drew a new bright ending."
    )
    cartoon.memes["sadness"] = 0.0
    cartoon.memes["comfort"] = 1.0
    ghost.memes["loneliness"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["understanding"] = 1.0
    world.fired.add("cartoon_soothed")

    world.para()
    world.say(
        f"The projector clicked back to life. In the new scene, {params.cartoon} found a friendly lantern "
        f"and waved from a safe, sunny hill."
    )
    world.say(
        f"{params.ghost_name} smiled. “Boo,” the ghost said once."
    )
    world.say(
        f"{params.child_name} smiled back. “I know what you mean now.”"
    )
    world.say(
        f"They watched the rest of the cartoon together, though the old reel still skipped once and left "
        f"a crooked gray mark across the sky. It was not perfect, but nobody was alone."
    )
    world.fired.add("resolution")
    return world


ASP_RULES = r"""
missing_help(cartoon).
repeats(ghost).
misunderstanding(child, ghost) :- repeats(ghost), missing_help(cartoon).
soothed(cartoon) :- misunderstanding(child, ghost), listens(child), helps(child).
understood(child, ghost) :- misunderstanding(child, ghost), listens(child), helps(child).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("missing_help", "cartoon"),
            asp.fact("repeats", "ghost"),
            asp.fact("listens", "child"),
            asp.fact("helps", "child"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(
        asp_program("#show misunderstanding/2.\n#show soothed/1.\n#show understood/2.")
    )
    misunderstanding = set(asp.atoms(model, "misunderstanding"))
    soothed = set(asp.atoms(model, "soothed"))
    understood = set(asp.atoms(model, "understood"))
    expected_pair = {("child", "ghost")}
    if misunderstanding == expected_pair and soothed == {("cartoon",)} and understood == expected_pair:
        sample = generate(StoryParams(seed=0))
        if "not alone" in sample.story and "I know what you mean now" in sample.story:
            print("OK: ASP and Python agree on the ghost misunderstanding.")
            return 0
    print("MISMATCH between ASP and Python.")
    print("ASP misunderstanding:", sorted(misunderstanding))
    print("ASP soothed:", sorted(soothed))
    print("ASP understood:", sorted(understood))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    seed = int(args.seed if args.seed is not None else 0)
    index = (seed * 173 + 29) % 256
    child = CHILD_NAMES[index % len(CHILD_NAMES)]
    index //= len(CHILD_NAMES)
    ghost = GHOST_NAMES[index % len(GHOST_NAMES)]
    index //= len(GHOST_NAMES)
    return StoryParams(
        seed=seed,
        child_name=child,
        ghost_name=ghost,
        setting_place=rng.choice(SETTINGS),
        cartoon=rng.choice(CARTOONS),
        repetition=rng.choice(REPETITIONS),
        bad_ending=rng.choice(BAD_ENDINGS),
        soothing_tool=rng.choice(SOOTHING_TOOLS),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a gentle ghost story in which {f['child'].label} misunderstands a repeated spooky message.",
        f"Include a cartoon about {f['cartoon'].label} that needs someone to soothe it.",
        "End with a slightly imperfect but comforting image showing that nobody is alone.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = world.setting.place
    return [
        QAItem(
            question=f"Why did {f['child'].label} think {f['ghost'].label} was trying to scare them?",
            answer=(
                f"{f['child'].label} heard {f['ghost'].label} repeat the same spooky message in {p}, "
                "so the repeated sound seemed like a warning instead of a request for help."
            ),
        ),
        QAItem(
            question=f"What did {f['ghost'].label} really want?",
            answer=(
                f"{f['ghost'].label} wanted help soothing the sad cartoon, because its unfinished or unhappy "
                "ending left the cartoon feeling lonely."
            ),
        ),
        QAItem(
            question=f"How did {f['child'].label} soothe the cartoon?",
            answer=(
                f"{f['child'].label} listened to the ghost, brought {world.facts.get('tool', 'a soothing tool')}, "
                "wrapped the picture warmly, and drew a kinder ending."
            ),
        ),
        QAItem(
            question="What changed after the misunderstanding was cleared up?",
            answer=(
                f"{f['child'].label} stopped feeling afraid, {f['ghost'].label} no longer felt alone, and "
                "the cartoon received a bright ending even though the old reel still had one crooked mark."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a tale involving a ghost or spirit, often using mystery or spookiness to create feeling and wonder.",
        ),
        QAItem(
            question="Why can repeating a message cause a misunderstanding?",
            answer="Repeating a message without explaining its purpose can make another person guess the wrong meaning, especially when the message sounds frightening.",
        ),
        QAItem(
            question="What does it mean to soothe someone?",
            answer="To soothe someone means to help them feel calmer, safer, and less upset through gentle words, care, or comforting actions.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    world.facts["tool"] = params.soothing_tool
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A gentle cartoon ghost misunderstanding storyworld.")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show misunderstanding/2.\n#show soothed/1.\n#show understood/2."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(
            asp_program("#show misunderstanding/2.\n#show soothed/1.\n#show understood/2.")
        )
        print("misunderstanding:", sorted(asp.atoms(model, "misunderstanding")))
        print("soothed:", sorted(asp.atoms(model, "soothed")))
        print("understood:", sorted(asp.atoms(model, "understood")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = 1 if args.all else max(1, args.n)
    samples: list[StorySample] = []

    for i in range(count):
        sample_seed = base_seed + i
        params = resolve_params(
            argparse.Namespace(seed=sample_seed),
            random.Random(sample_seed),
        )
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
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
