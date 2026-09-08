#!/usr/bin/env python3
"""
A child-facing rhyming storyworld about a maraca, a misunderstanding, and brave,
careful listening.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)
        self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    child_name: str = "Luna"
    helper_name: str = "Milo"
    maraca_color: str = "golden"
    setting: str = "a moonlit village square"


NAMES = ["Luna", "Milo", "Pia", "Theo", "Nia", "Sol", "Mara", "Finn"]
COLORS = ["golden", "red", "blue", "striped", "green"]
SETTINGS = [
    "a moonlit village square",
    "a bright garden stage",
    "a windy hilltop festival",
    "a little seaside parade",
]

INCIDENTS = [
    {
        "place": "the lantern bridge",
        "warning": "one shake meant stop, while two meant go",
        "misunderstanding": "Luna heard two shakes in the echo and stepped toward the bridge too soon",
        "danger": "the bridge ropes began to sway above the rushing stream",
        "clue": "the lantern keeper tapped the safe beat on her wooden rail",
        "brave": "held the rail, listened to the keeper, and waited for the true two-beat signal",
        "resolution": "the lanterns glowed green and the bridge carried everyone safely across",
        "ending": "Luna shook the maraca softly, and its golden rattle sounded like a tiny star applauding",
        "lesson": "Bravery is not rushing ahead; it is stopping to understand.",
    },
    {
        "place": "the whispering orchard",
        "warning": "a quick rattle meant follow, but a long rattle meant stay",
        "misunderstanding": "Luna mistook the leaves' long rustle for a quick signal and followed the wrong path",
        "danger": "she reached a thorny thicket where the festival flags could not be seen",
        "clue": "Milo counted the pauses between the real maraca shakes",
        "brave": "called for help, counted slowly, and retraced the path beside Milo",
        "resolution": "the correct rhythm led them back to the apple-cart band",
        "ending": "red apples bobbed like drums while Luna played the safe rhythm for everyone",
        "lesson": "A brave voice can ask for help before a small mistake grows.",
    },
    {
        "place": "the dancing sand garden",
        "warning": "the rattle marked stones that were firm, not stones that looked bright",
        "misunderstanding": "Luna followed a shiny stone instead of the maraca's careful rhythm",
        "danger": "her foot sank into soft sand beside the garden pond",
        "clue": "Milo said, 'The sound is our map, not the sparkle on the ground.'",
        "brave": "stayed still, reached for Milo's branch, and followed each marked beat back to firm sand",
        "resolution": "the garden path held steady beneath their feet",
        "ending": "the maraca's seeds swished as gently as grass while the moon shone on the safe stones",
        "lesson": "Courage listens to good clues instead of chasing a tempting shine.",
    },
    {
        "place": "the bellflower meadow",
        "warning": "the maraca's quiet shake meant duck beneath the low branches",
        "misunderstanding": "Luna thought the quiet sound meant the path was empty and stood up too soon",
        "danger": "a branch brushed her hat and startled a flock of sleepy birds",
        "clue": "the birds settled when Luna copied the quiet shake and lowered her head",
        "brave": "apologized, crouched low, and led the parade by the gentle rhythm",
        "resolution": "the birds returned to their nests without a flap or fuss",
        "ending": "bellflowers nodded in time as the maraca made a soft, respectful beat",
        "lesson": "Being brave also means caring for small creatures.",
    },
]


def _setup(world: World, params: StoryParams) -> None:
    child = world.add(Entity(params.child_name, "character", "child", params.child_name))
    helper = world.add(Entity(params.helper_name, "character", "friend", params.helper_name))
    maraca = world.add(Entity("maraca", "thing", "instrument", f"{params.maraca_color} maraca"))
    path = world.add(Entity("path", "place", "route", "safe path"))
    child.meters.update(courage=1.0, danger=0.0)
    child.memes.update(confusion=0.0, bravery=0.0)
    helper.meters.update(attention=1.0)
    maraca.meters.update(volume=1.0, rhythm=1.0)
    path.meters.update(safety=1.0)
    world.facts.update(child=child, helper=helper, maraca=maraca, path=path)


def _token(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum((i + 1) * ord(c) for i, c in enumerate(
        f"{params.child_name}|{params.helper_name}|{params.maraca_color}|{params.setting}"
    ))


def tell_story(params: StoryParams) -> World:
    world = World()
    _setup(world, params)
    incident = INCIDENTS[_token(params) % len(INCIDENTS)]
    child = world.facts["child"]
    helper = world.facts["helper"]
    maraca = world.facts["maraca"]

    world.say(f"In {params.setting}, where bright ribbons flew,")
    world.say(f"{child.label} held a {maraca.label} and {helper.label} held one too.")
    world.say(f"They marched toward {incident['place']} with a tap-tap-tune,")
    world.say("Beneath the warm sun and the silver moon.")

    world.para()
    world.say(f"A sign gave a warning: {incident['warning']}.")
    world.say(f"But {child.label} {incident['misunderstanding']}.")
    world.say(f"'{incident['danger'].capitalize()}!' cried {helper.label}.")
    world.say(f"'I thought the rattle said hurry!' said {child.label}.")
    world.say(f"'Let's listen once more,' said {helper.label}. 'A brave heart can pause before it goes.'")

    child.memes["confusion"] = 1.0
    child.meters["danger"] = 1.0
    world.fired.add(("misunderstanding", incident["place"]))

    world.para()
    world.say(f"Then {incident['clue']}.")
    world.say(f"{child.label} took a breath, though the breeze made the tall grasses quiver.")
    world.say(f"'{incident['brave'].capitalize()},' said {child.label}.")
    world.say(f"'{incident['resolution'].capitalize()},' answered {helper.label}.")

    child.memes["confusion"] = 0.0
    child.memes["bravery"] = 1.0
    child.meters["danger"] = 0.0
    world.fired.add(("brave_choice", incident["place"]))

    world.para()
    world.say(f"{incident['lesson']} {incident['ending']}.")
    world.say(f"'A maraca can make music,' said {child.label}, 'but we must hear what its music means.'")
    world.say(f"'And when we listen together,' said {helper.label}, 'the safest path is clear.'")
    world.say("So the parade went on with a careful, cheerful beat,")
    world.say("And every small rattle made the journey complete.")

    world.facts.update(
        params=params,
        incident=incident,
        incident_index=_token(params) % len(INCIDENTS),
        resolved=True,
    )
    return world


def valid_story() -> bool:
    return True


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    incident = world.facts["incident"]
    return [
        f"Write a rhyming cautionary story about {p.child_name}, a maraca, and {incident['place']}.",
        f"Show how a misunderstanding of the maraca signal creates danger, then let {p.child_name} use bravery and careful listening.",
        "End with a concrete happy image proving that the characters learned to understand signals before acting.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    incident = world.facts["incident"]
    return [
        QAItem(
            f"What instrument did {p.child_name} carry?",
            f"{p.child_name} carried a {p.maraca_color} maraca.",
        ),
        QAItem(
            "What misunderstanding caused trouble?",
            f"{p.child_name} misunderstood the signal: {incident['misunderstanding'].capitalize()}.",
        ),
        QAItem(
            "What made the situation cautionary?",
            f"The warning was that {incident['warning']}, but acting on the wrong meaning led to danger: {incident['danger']}.",
        ),
        QAItem(
            "How did the child show bravery?",
            f"{p.child_name} {incident['brave']}. That was brave because it faced the problem carefully instead of rushing.",
        ),
        QAItem(
            "How did the characters solve the problem?",
            f"They used the clue that {incident['clue'].lower()} Then {incident['resolution']}.",
        ),
        QAItem(
            "What lesson did the story teach?",
            f"It taught that {incident['lesson'].lower()}",
        ),
        QAItem(
            "What final image showed that things had changed?",
            f"{incident['ending'].capitalize()}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a maraca?",
            "A maraca is a small hand instrument filled with seeds or beads that makes a shaking sound.",
        ),
        QAItem(
            "What is a misunderstanding?",
            "A misunderstanding happens when someone hears, sees, or interprets something incorrectly.",
        ),
        QAItem(
            "What is bravery?",
            "Bravery means facing a difficult or frightening situation while making a thoughtful, safe choice.",
        ),
    ]


ASP_RULES = r"""
confused(S) :- signal(S), misheard(S).
cautionary(S) :- confused(S), danger(S).
brave_choice(S) :- cautionary(S), listens(S), asks_help(S).
happy_ending(S) :- brave_choice(S), safe(S).
valid_story(S) :- cautionary(S), brave_choice(S), happy_ending(S).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("signal", "story1"),
        asp.fact("misheard", "story1"),
        asp.fact("danger", "story1"),
        asp.fact("listens", "story1"),
        asp.fact("asks_help", "story1"),
        asp.fact("safe", "story1"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    found = set(asp.atoms(model, "valid_story"))
    expected = {("story1",)} if valid_story() else set()
    if found == expected:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(found))
    print("Python:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rhyming cautionary storyworld about a maraca, misunderstanding, and bravery."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper-name", choices=NAMES)
    parser.add_argument("--maraca-color", choices=COLORS)
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    helper_choices = [n for n in NAMES if n != name]
    helper = args.helper_name or rng.choice(helper_choices)
    return StoryParams(
        seed=None,
        child_name=name,
        helper_name=helper,
        maraca_color=args.maraca_color or rng.choice(COLORS),
        setting=args.setting or rng.choice(SETTINGS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"  {entity.id:10} ({entity.kind:9}) {' '.join(details)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(child_name="Luna", helper_name="Milo", maraca_color="golden", setting=SETTINGS[0]),
    StoryParams(child_name="Pia", helper_name="Theo", maraca_color="red", setting=SETTINGS[1]),
    StoryParams(child_name="Sol", helper_name="Nia", maraca_color="blue", setting=SETTINGS[3]),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(args.n):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
