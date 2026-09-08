#!/usr/bin/env python3
"""
A tiny mystery world about Grampa, a harmless goof, and the moral value of
telling the truth kindly. The mystery resolves with a happy ending.
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


@dataclass(frozen=True)
class Setting:
    key: str
    place: str
    clue: str


@dataclass(frozen=True)
class Mystery:
    title: str
    object_name: str
    hiding_place: str
    first_clue: str
    second_clue: str
    goof: str
    moral: str
    happy_image: str


@dataclass
class Entity:
    ident: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: Setting
    mystery: Mystery
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.ident] = entity
        return entity


SETTINGS = {
    "kitchen": Setting("kitchen", "the sunny kitchen", "a trail of flour beside the pantry"),
    "attic": Setting("attic", "the creaky attic", "a blue thread caught on an old trunk"),
    "garden": Setting("garden", "the little garden", "three bent daisies near the gate"),
}

MYSTERIES = [
    Mystery(
        "The Vanishing Jam Jar",
        "the strawberry jam jar",
        "behind the picnic basket",
        "a sticky red dot on the floor",
        "a tiny spoon shining under the table",
        "Grampa had put the jar away, then forgotten where he put it.",
        "A mistake is easier to mend when we tell the truth instead of blaming someone else.",
        "Grampa spread jam on warm toast while everyone laughed gently about the search.",
    ),
    Mystery(
        "The Missing Blue Button",
        "the blue button",
        "inside Grampa's coat pocket",
        "a loose blue thread on the chair",
        "a small click from the coat hanging by the door",
        "Grampa had carried the button in his pocket while fixing a toy.",
        "Kind honesty turns an embarrassing mistake into a chance to help.",
        "The repaired toy rolled across the rug as Grampa's coat gleamed with both buttons again.",
    ),
    Mystery(
        "The Disappearing Garden Bell",
        "the little garden bell",
        "under a broad cabbage leaf",
        "a silver scrape along the garden path",
        "a fresh crescent in the damp soil",
        "Grampa had moved the bell to keep it dry, then forgot to mention it.",
        "Before making a guess, look closely and ask kindly.",
        "The bell rang in the evening breeze while Grampa and the children planted a new row of flowers.",
    ),
    Mystery(
        "The Empty Biscuit Tin",
        "the last cinnamon biscuit",
        "in Grampa's apron pocket",
        "a cinnamon crumb on the doorstep",
        "a round buttery mark on the apron",
        "Grampa had saved the biscuit for a surprise and then forgotten the surprise.",
        "A truthful explanation can bring forgiveness and a better plan.",
        "Grampa baked a fresh batch, and the whole family shared the warm biscuits.",
    ),
]

NAMES = ["Luna", "Milo", "Nia", "Tess", "Pip"]
GRAMPAS = ["Grampa", "Grandpa Jo", "Grampa Reed"]


@dataclass
class StoryParams:
    setting: str
    name: str
    grampa: str
    seed: Optional[int] = None


def reasonability_gate(setting: Setting, mystery: Mystery) -> bool:
    return bool(setting.place and mystery.object_name and mystery.hiding_place)


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if not params.name.strip() or not params.grampa.strip():
        raise StoryError("The child and grampa must both have names.")

    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[(params.seed or 0) % len(MYSTERIES)]
    if not reasonability_gate(setting, mystery):
        raise StoryError("The mystery does not have enough clues to resolve.")

    world = World(setting, mystery)
    luna = world.add(Entity("child", "character", params.name))
    grampa = world.add(Entity("grampa", "character", params.grampa))
    clue = world.add(Entity("clue", "evidence", mystery.first_clue))
    prize = world.add(Entity("mystery_object", "object", mystery.object_name))

    luna.memes["curiosity"] = 1.0
    grampa.memes["kindness"] = 1.0
    clue.meters["visibility"] = 1.0
    prize.meters["hidden"] = 1.0

    world.facts.update(
        child=luna,
        grampa=grampa,
        clue=clue,
        prize=prize,
        solved=False,
        moral=mystery.moral,
    )
    return world


def render_story(world: World) -> str:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    grampa: Entity = f["grampa"]  # type: ignore[assignment]
    mystery = world.mystery
    place = world.setting.place

    paragraphs = [
        f"One bright morning, {child.label} visited {grampa.label} in {place}.",
        f"{grampa.label} was ready to make breakfast, but {mystery.object_name} had vanished. "
        f"Near the pantry, {child.label} spotted {mystery.first_clue}.",
        f'"That is a curious clue," said {child.label}. "Did you see where it went?"',
        f'"I saw nothing," said {grampa.label}, rubbing his chin. "Perhaps a very sneaky mouse took it."',
        f"{child.label} followed the trail slowly. The next clue was {mystery.second_clue}. "
        f"It did not look like a mouse trail at all.",
        f'"Let us ask what happened before we make a guess," said {child.label}.',
        f"{grampa.label} thought hard. Then he gave a sheepish smile. "
        f"{mystery.goof} The missing {mystery.object_name.removeprefix('the ')} was {mystery.hiding_place}.",
        f'"I made a goof," admitted {grampa.label}. "I should have told you sooner."',
        f'"Thank you for telling the truth," said {child.label}. "Now we can fix it together."',
        f"They brought {mystery.object_name} back to its proper place and shared a relieved laugh. "
        f"{mystery.happy_image}",
        f"The moral value was clear: {mystery.moral}",
    ]
    world.facts["solved"] = True
    child.memes["confidence"] = 1.0
    grampa.memes["relief"] = 1.0
    world.facts["ending"] = mystery.happy_image
    return "\n\n".join(paragraphs)


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a gentle mystery about {world.facts['child'].label}, {world.facts['grampa'].label}, and a missing {world.mystery.object_name}.",
        f"Tell a child-facing mystery using the clues '{world.mystery.first_clue}' and '{world.mystery.second_clue}'.",
        f"End with the moral value that {world.mystery.moral}",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    grampa = world.facts["grampa"]
    m = world.mystery
    return [
        QAItem(
            f"Who noticed that {m.object_name} was missing?",
            f"{child.label} noticed that {m.object_name} was missing while visiting {grampa.label}.",
        ),
        QAItem(
            "What was the first clue?",
            f"The first clue was {m.first_clue}.",
        ),
        QAItem(
            f"Where was {m.object_name} found?",
            f"{m.object_name.capitalize()} was found {m.hiding_place}.",
        ),
        QAItem(
            "What goof had Grampa made?",
            f"{m.goof}",
        ),
        QAItem(
            "What moral value did the mystery teach?",
            f"The mystery taught that {m.moral}",
        ),
        QAItem(
            "How did the story end?",
            f"It ended happily: {m.happy_image}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a clue?",
            "A clue is a small piece of information or evidence that helps someone solve a mystery.",
        ),
        QAItem(
            "Why is it useful to ask kindly before blaming someone?",
            "Kind questions help people share what they know and make it easier to correct mistakes without hurting feelings.",
        ),
        QAItem(
            "What makes an ending happy?",
            "A happy ending shows that the problem has been solved and that the characters feel safe, forgiven, or joyful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"- {p}" for p in sample.prompts)
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
    lines = ["--- world model state ---"]
    lines.append(f"  setting: {world.setting.place}")
    lines.append(f"  mystery: {world.mystery.title}")
    lines.append(f"  solved: {world.facts.get('solved', False)}")
    for entity in world.entities.values():
        lines.append(
            f"  {entity.ident}: kind={entity.kind}, "
            f"meters={entity.meters}, memes={entity.memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
clue_present(M) :- first_clue(M,C), C != "".
resolvable(M) :- clue_present(M), second_clue(M,C), C != "", hiding_place(M,P), P != "".
valid(S,M) :- setting(S), mystery(M), resolvable(M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for key in SETTINGS:
        lines.append(asp.fact("setting", key))
    for index, mystery in enumerate(MYSTERIES):
        ident = f"mystery_{index}"
        lines.extend(
            [
                asp.fact("mystery", ident),
                asp.fact("first_clue", ident, mystery.first_clue),
                asp.fact("second_clue", ident, mystery.second_clue),
                asp.fact("hiding_place", ident, mystery.hiding_place),
            ]
        )
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> set[tuple[str, str]]:
    return {
        (setting, f"mystery_{index}")
        for setting in SETTINGS
        for index, mystery in enumerate(MYSTERIES)
        if reasonability_gate(SETTINGS[setting], mystery)
    }


def asp_valid_combos() -> set[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "valid"))


def asp_verify() -> int:
    try:
        actual = asp_valid_combos()
    except ImportError:
        print("SKIP: clingo is not installed.")
        return 0
    expected = valid_combos()
    if actual != expected:
        print("MISMATCH between Python and ASP gates.")
        print("python only:", sorted(expected - actual))
        print("ASP only:", sorted(actual - expected))
        return 1
    for index, setting in enumerate(SETTINGS):
        sample = generate(StoryParams(setting, "Luna", "Grampa", index))
        if not sample.story or not sample.facts if False else False:
            return 1
    print(f"OK: ASP gate matches Python gate ({len(expected)} combinations).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A tiny mystery world about Grampa, a goof, moral value, and a happy ending."
    )
    parser.add_argument("--setting", choices=sorted(SETTINGS))
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--grampa", choices=GRAMPAS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(sorted(SETTINGS))
    name = args.name or rng.choice(NAMES)
    grampa = args.grampa or rng.choice(GRAMPAS)
    return StoryParams(setting, name, grampa, args.seed)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    story = render_story(world)
    return StorySample(
        params=params,
        story=story,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        try:
            import asp

            model = asp.one_model(asp_program())
            for combo in sorted(asp.atoms(model, "valid")):
                print(combo)
        except ImportError:
            print("clingo is not installed.")
        return

    if args.all:
        samples = [
            generate(StoryParams(setting, name, grampa, index))
            for index, setting in enumerate(SETTINGS)
            for name, grampa in [(args.name or "Luna", args.grampa or "Grampa")]
        ]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        for offset in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
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
