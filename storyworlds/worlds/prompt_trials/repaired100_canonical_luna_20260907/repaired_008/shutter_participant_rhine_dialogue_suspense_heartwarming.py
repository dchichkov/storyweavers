#!/usr/bin/env python3
"""
A gentle suspense storyworld about a shutter, a participant, and the Rhine.

A participant helping with a riverside photo exhibit must discover why a
wooden shutter will not open before the evening visitors arrive. Dialogue turns
worry into cooperation, and the repaired shutter reveals a warm view of the
Rhine.
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
    id: str
    place: str
    river: str
    affords: set[str]


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


SETTINGS = {
    "quay": Setting(
        "quay",
        "a small riverside gallery",
        "the Rhine",
        {"river_view", "shutter"},
    ),
    "boathouse": Setting(
        "boathouse",
        "an old boathouse beside the river",
        "the Rhine",
        {"river_view", "shutter"},
    ),
    "courtyard": Setting(
        "courtyard",
        "a warm courtyard gallery near the Rhine",
        "the Rhine",
        {"river_view", "shutter"},
    ),
}

ACTIVITIES = {
    "exhibit": "prepare the evening exhibit",
    "window": "open the river window",
    "welcome": "ready the welcome display",
}

GIRL_NAMES = ["Luna", "Mara", "Nina", "Sofia"]
BOY_NAMES = ["Theo", "Eli", "Jonas", "Milo"]
HELPERS = ["Grandma Rosa", "Uncle Emil", "Aunt Clara", "Mr. Weber"]


@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    helper: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Arc:
    opening: str
    suspense: str
    clue: str
    actions: tuple[str, str, str]
    result: str
    ending: str
    cause: str


ARCS = [
    Arc(
        "Luna had placed photographs of boats, bridges, and bright riverside umbrellas along the gallery wall.",
        "Just before the first guests arrived, the wooden shutter gave a sharp click and stayed closed.",
        "A thin blue ribbon was caught in the hinge, and its end fluttered whenever the river breeze touched it.",
        (
            "held the shutter steady",
            "pulled the ribbon gently from the hinge",
            "brushed the dust from the latch",
        ),
        "The shutter opened with a soft wooden sigh, letting the last gold light spill across the photographs.",
        "Outside, the Rhine shone like a long silver welcome sign, and every participant clapped softly.",
        "A blue ribbon had slipped into the shutter hinge and blocked the latch.",
    ),
    Arc(
        "They had made a little table where visitors could write memories of the Rhine.",
        "A dark shape moved behind the shutter, and the waiting participants wondered whether a bird was trapped there.",
        "The shape was a folded sailcloth caught on the inside handle, while a loose window hook made it sway.",
        (
            "stood beside the window",
            "unhooked the sailcloth",
            "fastened the window hook",
        ),
        "The shutter swung open, and the sailcloth became a neat table cover instead of a frightening shadow.",
        "The visitors wrote kind memories while the Rhine carried the evening light past the window.",
        "A folded sailcloth had caught on the handle and moved in the breeze.",
    ),
    Arc(
        "Luna had promised that every participant could add one small drawing to the display.",
        "When the shutter jammed, a sudden thump from outside made everyone turn toward the dark glass.",
        "A delivery basket had rolled against the outside sill, and its wicker handle was touching the shutter.",
        (
            "looked through the lower gap",
            "moved the basket away from the sill",
            "tested the shutter latch",
        ),
        "The shutter opened safely, and the basket held a bundle of fresh bread for the visitors.",
        "They shared the bread beneath the open window, listening to the Rhine make a quiet, friendly hush.",
        "A delivery basket had rolled against the outside sill and blocked the shutter.",
    ),
    Arc(
        "The gallery smelled of paper, tea, and the river rain that had fallen before breakfast.",
        "A drop tapped the shutter again and again, making the quiet room feel full of hidden footsteps.",
        "Rainwater had gathered in a bent gutter above the window, and each drop struck the same loose metal clasp.",
        (
            "placed a bowl beneath the drip",
            "straightened the little gutter clasp",
            "wiped the shutter dry",
        ),
        "The tapping stopped, and the shutter opened onto a clean, pearly sky above the Rhine.",
        "Luna thanked each participant, and the bowl became a vase for one cheerful yellow flower.",
        "Rainwater from a bent gutter was striking a loose metal clasp above the shutter.",
    ),
    Arc(
        "A row of paper lanterns waited to glow when the evening walk reached the gallery.",
        "One lantern flickered behind the closed shutter, and Luna feared the display had been damaged.",
        "Its cord had slipped under the shutter edge, pulling the latch tight whenever the lantern swayed.",
        (
            "held the lantern still",
            "lifted the cord from beneath the shutter",
            "tied the cord to a small peg",
        ),
        "The shutter opened, and the lanterns glowed in a calm row along the river wall.",
        "The Rhine reflected every warm light until the whole gallery seemed to smile at the visitors.",
        "A lantern cord had slipped beneath the shutter and pulled the latch tight.",
    ),
]


DIALOGUE = [
    '"I heard that click," said {name}. "What if the shutter is stuck for good?"',
    '"Let us listen before we worry," said {helper}. "A small clue can lead to a big fix."',
    '"I see something moving," said {name}. "It is not a ghost. It is part of our display."',
    '"We can each do one safe thing," said {helper}. "Then we will know more."',
]


def valid_combos() -> list[tuple[str, str]]:
    return [
        (place, activity)
        for place, setting in SETTINGS.items()
        for activity in ACTIVITIES
        if "shutter" in setting.affords
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A heartwarming Rhine shutter storyworld.")
    parser.add_argument("--place", choices=sorted(SETTINGS))
    parser.add_argument("--activity", choices=sorted(ACTIVITIES))
    parser.add_argument("--name")
    parser.add_argument("--helper")
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
    combos = [
        combo for combo in valid_combos()
        if args.place is None or combo[0] == args.place
        if args.activity is None or combo[1] == args.activity
    ]
    if not combos:
        raise StoryError("No place and activity combination can include a shutter.")
    place, activity = rng.choice(combos)
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    if helper == name:
        raise StoryError("The helper must be different from the participant.")
    return StoryParams(place, activity, name, helper, args.seed)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    participant = world.add(Entity(params.name, "participant", params.name))
    helper = world.add(Entity("helper", "helper", params.helper))
    shutter = world.add(Entity("shutter", "object", "the wooden shutter", {"closed": 1.0}))
    river = world.add(Entity("rhine", "river", "the Rhine", {"flowing": 1.0}))
    world.facts.update(participant=participant, helper=helper, shutter=shutter, river=river)

    arc = ARCS[(params.seed or 0) % len(ARCS)]
    dialogue = DIALOGUE[((params.seed or 0) // len(ARCS)) % len(DIALOGUE)]
    name = participant.label
    helper_name = helper.label

    world.say(
        f"{name}, a participant in the evening program, helped {helper_name} "
        f"{ACTIVITIES[params.activity]} in {setting.place} beside {setting.river}."
    )
    world.say(arc.opening)
    world.say("They wanted the little gallery to feel welcoming to everyone who came in from the riverside path.")

    world.para()
    world.say(arc.suspense)
    world.say(dialogue.format(name=name, helper=helper_name))
    world.say(
        f'"We will stay together," said {helper_name}. '
        f'"The {setting.river} is outside, and our friends are waiting inside."'
    )

    world.para()
    world.say("They watched the shutter instead of guessing, and the small movement gave them a clue.")
    world.say(arc.clue)
    world.say(
        f'"Now I know what to try," said {name}. '
        f'"You can hold the shutter while I check the latch."'
    )

    world.para()
    world.say(
        f"Working as a team, {name} {arc.actions[0]}, {helper_name} {arc.actions[1]}, "
        f"and together they {arc.actions[2]}."
    )
    world.say(arc.result)
    world.say(
        f'"It was a real problem, not a scary mystery," said {helper_name}. '
        f'"And you helped us notice it."'
    )

    world.para()
    world.say(
        f"{name} smiled because every participant had a useful part in making the gallery ready."
    )
    world.say(arc.ending)

    shutter.meters["closed"] = 0.0
    shutter.meters["open"] = 1.0
    participant.memes["confidence"] = 1.0
    helper.memes["trust"] = 1.0
    world.facts.update(arc=arc, cause=arc.cause)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a heartwarming suspense story about {f['participant'].label}, a participant, solving a shutter problem beside the Rhine.",
        f"Include dialogue in which {f['participant'].label} and {f['helper'].label} turn worry into teamwork.",
        "End with a concrete image showing how the repaired shutter changes the riverside scene.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    participant = f["participant"].label
    helper = f["helper"].label
    arc = f["arc"]
    return [
        QAItem(
            "Who was helping at the riverside gallery?",
            f"{participant} was a participant helping {helper} prepare the evening activity.",
        ),
        QAItem(
            "What caused the shutter problem?",
            arc.cause,
        ),
        QAItem(
            "How did the dialogue help?",
            f"{participant} and {helper} spoke calmly, shared what they noticed, and chose safe jobs together. Their words changed worry into a plan.",
        ),
        QAItem(
            "What happened when the team solved the problem?",
            arc.result,
        ),
        QAItem(
            "How did the story end?",
            arc.ending,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a shutter?",
            "A shutter is a panel that can cover or uncover a window.",
        ),
        QAItem(
            "What is the Rhine?",
            "The Rhine is a major river in Europe.",
        ),
        QAItem(
            "What is a participant?",
            "A participant is someone who takes part in an activity.",
        ),
        QAItem(
            "Why can dialogue help solve a problem?",
            "Dialogue lets people share observations, ask questions, and make a plan together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    for item in sample.story_qa + sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: kind={entity.kind} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"setting={world.setting.place}; river={world.setting.river}")
    lines.append(f"cause={world.facts.get('cause', '')}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
activity(A) :- activity_name(A).
valid(P,A) :- affords(P,shutter), setting(P), activity_name(A).
safe_solution(P,A) :- valid(P,A), dialogue, suspense.
#show valid/2.
#show safe_solution/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for affordance in sorted(setting.affords):
            lines.append(asp.fact("affords", place, affordance))
    for activity in ACTIVITIES:
        lines.append(asp.fact("activity_name", activity))
    lines.append(asp.fact("dialogue"))
    lines.append(asp.fact("suspense"))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    python_pairs = set(valid_combos())
    try:
        import asp

        symbols = asp.one_model(asp_program("#show valid/2."))
        asp_pairs = set(asp.atoms(symbols, "valid"))
    except Exception as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1
    if python_pairs != asp_pairs:
        print(f"ASP/Python mismatch: python={python_pairs}, asp={asp_pairs}")
        return 1
    for index, params in enumerate(
        (
            StoryParams("quay", "exhibit", "Luna", "Grandma Rosa", index)
            for index in range(4)
        )
    ):
        sample = generate(params)
        if not sample.story or "shutter" not in sample.story.lower():
            print("Generated story verification failed.")
            return 1
    print(f"OK: ASP/Python parity matches ({len(python_pairs)} combinations).")
    return 0


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    if params.activity not in ACTIVITIES:
        raise StoryError(f"Unknown activity: {params.activity}")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("quay", "exhibit", "Luna", "Grandma Rosa", 0),
    StoryParams("boathouse", "window", "Theo", "Uncle Emil", 1),
    StoryParams("courtyard", "welcome", "Mara", "Aunt Clara", 2),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp

        models = asp.solve(asp_program(), models=1)
        print(json.dumps([str(symbol) for symbol in models[0]] if models else []))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        for offset in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = seed
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
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
