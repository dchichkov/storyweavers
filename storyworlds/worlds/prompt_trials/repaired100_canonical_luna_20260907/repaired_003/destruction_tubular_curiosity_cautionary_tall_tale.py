#!/usr/bin/env python3
"""
A small cautionary tall tale about Luna, a tubular machine, and curiosity.

The machine is playful but powerful: when Luna turns its silver tube toward
something, that thing is blasted into a harmless cloud of paper confetti. Her
curiosity causes destruction until caution, listening, and a careful repair
turn the machine into a useful helper.
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
class StoryParams:
    place: str
    child_name: str = "Luna"
    helper_name: str = "Tomas"
    tube_kind: str = "moon tube"
    seed: Optional[int] = None
    style: str = "Tall Tale"
    feature: str = "Curiosity"
    warning: str = "Cautionary"


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def change_meter(self, key: str, amount: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def change_meme(self, key: str, amount: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class World:
    place: str
    child: Entity
    helper: Entity
    tube: Entity
    town: Entity
    moon: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for entity in (self.child, self.helper, self.tube, self.town, self.moon):
            meters = {k: v for k, v in entity.meters.items() if v}
            memes = {k: v for k, v in entity.memes.items() if v}
            details = []
            if meters:
                details.append(f"meters={meters}")
            if memes:
                details.append(f"memes={memes}")
            lines.append(f"  {entity.id:10} ({entity.kind:10}) {' '.join(details)}")
        lines.append(f"  place: {self.place}")
        return "\n".join(lines)


PLACES = {
    "hill": "the wind-bright hill",
    "harbor": "the old harbor",
    "market": "the noon market",
    "bridge": "the long wooden bridge",
}

NAMES = ["Luna", "Pip", "Mara", "Sol", "Nico"]
HELPERS = ["Tomas", "Aunt Bea", "Grandpa Ren", "Mina"]

OPENINGS = {
    "hill": [
        "{child} found the tubular machine beside the wind-bright hill.",
        "At the top of the hill, {child} discovered a silver tube taller than a horse.",
    ],
    "harbor": [
        "{child} spotted a long tubular machine shining beside the old harbor.",
        "Near the harbor crane, {child} found a silver tube with three brass buttons.",
    ],
    "market": [
        "At the noon market, {child} discovered a tubular machine tucked beneath a striped cart.",
        "The market bells rang when {child} rolled a shining tube out from behind a spice stall.",
    ],
    "bridge": [
        "{child} found a brass-banded tube leaning against the long wooden bridge.",
        "Under the bridge, {child} discovered a tubular machine that hummed like a sleepy whale.",
    ],
}

TARGETS = {
    "hill": ("a stack of empty crates", "a neat pile of wooden boards"),
    "harbor": ("an old sailcloth", "a heap of coiled rope"),
    "market": ("a mountain of melon boxes", "a row of cardboard stalls"),
    "bridge": ("a leaning sign", "a bundle of broken planks"),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A cautionary tall tale about curiosity and a destructive tubular machine."
    )
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def validate_params(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("Choose a place where the tubular machine can be watched safely.")
    if not params.child_name.strip():
        raise StoryError("The curious child needs a name.")
    if not params.helper_name.strip():
        raise StoryError("The careful helper needs a name.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        place=args.place or rng.choice(list(PLACES)),
        child_name=args.name or rng.choice(NAMES),
        helper_name=args.helper or rng.choice(HELPERS),
        seed=args.seed,
    )
    validate_params(params)
    return params


def make_world(params: StoryParams) -> World:
    child = Entity("child", "character", params.child_name, "curious child")
    helper = Entity("helper", "character", params.helper_name, "careful helper")
    tube = Entity("tube", "machine", params.tube_kind, "tubular launcher")
    town = Entity("town", "place", PLACES[params.place], "shared place")
    moon = Entity("moon", "thing", "moon", "paper moon")
    return World(
        place=PLACES[params.place],
        child=child,
        helper=helper,
        tube=tube,
        town=town,
        moon=moon,
    )


def build_story(world: World, params: StoryParams) -> None:
    rng = random.Random((params.seed or 0) + 9176)
    child = world.child
    helper = world.helper
    tube = world.tube
    target, repaired_target = TARGETS[params.place]

    child.memes["curiosity"] = 1.0
    child.memes["caution"] = 0.0
    tube.meters["power"] = 3.0
    tube.meters["aim"] = 0.0
    world.moon.meters["distance"] = 1.0

    world.say(rng.choice(OPENINGS[params.place]).format(child=child.label))
    world.say(
        f"The machine had a broad mouth, a narrow tail, and a tubular body "
        f"that hummed, 'Try me!' Three brass buttons glowed beside its handle."
    )
    world.say(
        f"{helper.label} hurried over and called, \"That tube is powerful. "
        f"Please wait until we know what it does.\""
    )
    world.say(
        f"\"My curiosity is bigger than this hill!\" said {child.label}. "
        f"\"I will make one tiny test.\""
    )

    world.para()
    world.say(
        f"{child.label} pressed the first button and aimed at {target}. "
        f"With a thunderous puff, the machine turned it into a whirlwind of paper flakes."
    )
    tube.change_meter("power", -1.0)
    tube.change_meter("aim", 1.0)
    child.change_meme("curiosity", 1.0)
    world.say(
        f"The destruction was harmless but enormous. Paper snow covered the ground, "
        f"and the market, harbor, hill, or bridge looked as if a cloud had fallen down."
    )
    world.say(
        f"\"That was not tiny,\" said {helper.label}. "
        f"\"A tall tale can still have a careful lesson.\""
    )

    world.para()
    world.say(
        f"Then the tube rolled toward the {world.moon.label}, which hung above the place "
        f"on a thin silver string. The brass buttons began to blink."
    )
    world.say(
        f"{child.label} reached for the handle, but {helper.label} caught it. "
        f"\"Stop, listen, and look,\" said {helper.label}. "
        f"\"Curiosity asks a question; caution checks the answer.\""
    )
    child.change_meme("caution", 1.0)
    tube.change_meter("aim", -1.0)
    world.say(
        f"Together they noticed a small arrow pointing away from the moon and toward "
        f"a cleared patch near the {world.place}. The arrow was the machine's safe mark."
    )
    world.say(
        f"\"I wanted to know everything at once,\" said {child.label}. "
        f"\"Now I will learn one safe thing at a time.\""
    )

    world.para()
    world.say(
        f"They carried the tube to the cleared patch and aimed it at {repaired_target}. "
        f"{helper.label} held a rope around the handle while {child.label} pressed the "
        f"single blue button."
    )
    tube.change_meter("power", -1.0)
    tube.change_meter("aim", 1.0)
    world.say(
        f"A gentle puff gathered the scattered paper into a sturdy little shelter. "
        f"The machine had caused destruction, but careful hands had given its power a purpose."
    )
    child.change_meme("joy", 1.0)
    child.change_meme("curiosity", -0.5)
    world.say(
        f"By sunset, {child.label} and {helper.label} had marked a safe circle around "
        f"the tube. The moon shone above the new shelter, and the tubular machine rested "
        f"quietly until someone was ready to ask it a careful question."
    )

    world.facts.update(
        target=target,
        repaired_target=repaired_target,
        destruction="the machine blasted the first target into paper flakes",
        lesson="curiosity should be guided by caution",
        safe_mark="the arrow pointed toward the cleared patch",
    )


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a Tall Tale about {world.child.label}, a tubular machine, and destruction at {world.place}.",
        "Tell a cautionary story in which curiosity causes a surprising mess but careful teamwork repairs it.",
        "Write a child-friendly tale with a powerful tube, a spoken warning, a safe test, and a changed ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question=f"What did {world.child.label}'s curiosity cause?",
            answer=f"It caused the tubular machine to blast {world.facts['target']} into a huge cloud of paper flakes.",
        ),
        QAItem(
            question=f"How did {world.helper.label} help?",
            answer=f"{world.helper.label} stopped the tube before it struck the moon, read its safe mark, and helped aim it at a cleared patch.",
        ),
        QAItem(
            question="What changed the destructive machine into a helper?",
            answer="Caution changed the result: the children used the safe mark, chose a clear target, and pressed only the blue button.",
        ),
        QAItem(
            question="What lesson did the story teach?",
            answer="Curiosity is valuable, but it should be guided by caution before a powerful machine is used.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does tubular mean?",
            answer="Tubular means shaped like a tube, with a long rounded body and an open or narrow end.",
        ),
        QAItem(
            question="Why can curiosity need caution?",
            answer="Curiosity encourages questions, but caution helps people check risks before acting.",
        ),
        QAItem(
            question="What is destruction?",
            answer="Destruction is damage that breaks, scatters, or changes something from its former state.",
        ),
        QAItem(
            question="Why was the final test safer?",
            answer="The final test happened in a cleared patch, followed the arrow, and used a single controlled button with help nearby.",
        ),
    ]


ASP_RULES = r"""
curious(C) :- child(C), curiosity(C).
careful(C) :- child(C), caution(C).
safe_test(T) :- tubular(T), marked(T), clear_place(P).
good_use(T) :- safe_test(T), careful(C).
story_good :- curious(C), careful(C), tubular(T), good_use(T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = []
    for place in PLACES:
        lines.append(asp.fact("clear_place", place))
    for name in NAMES:
        lines.append(asp.fact("child", name))
    lines.append(asp.fact("tubular", "moon_tube"))
    lines.append(asp.fact("marked", "moon_tube"))
    lines.append(asp.fact("curiosity", "Luna"))
    lines.append(asp.fact("caution", "Luna"))
    return "\n".join(lines)


def asp_program(show: str = "#show story_good/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable(params: StoryParams) -> bool:
    return (
        params.place in PLACES
        and params.style == "Tall Tale"
        and params.feature == "Curiosity"
        and params.warning == "Cautionary"
    )


def asp_verify() -> int:
    params = StoryParams(place="hill")
    if not python_reasonable(params):
        print("MISMATCH: Python reasonableness gate rejected the canonical story.")
        return 1
    try:
        import storyworlds.asp as asp

        models = asp.solve(asp_program(), models=1)
        if not models or not asp.atoms(models[0], "story_good"):
            print("MISMATCH: ASP twin did not find a good story.")
            return 1
    except ImportError:
        print("OK: Python reasonableness gate passed; clingo is unavailable.")
        return 0
    sample = generate(params)
    if "tubular" not in sample.story and "tube" not in sample.story:
        print("MISMATCH: generated story omitted its tubular instrument.")
        return 1
    if not sample.story_qa:
        print("MISMATCH: generated story omitted grounded questions.")
        return 1
    print("OK: Python and ASP gates agree, and generated story checks passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = make_world(params)
    build_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(sample.world.trace())
    if qa:
        print("\n== Generation prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== World questions ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(place="hill", child_name="Luna", helper_name="Tomas"),
    StoryParams(place="harbor", child_name="Pip", helper_name="Aunt Bea"),
    StoryParams(place="market", child_name="Mara", helper_name="Grandpa Ren"),
    StoryParams(place="bridge", child_name="Sol", helper_name="Mina"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import storyworlds.asp as asp

            models = asp.solve(asp_program(), models=1)
            print("ASP model:")
            for atom in models[0] if models else []:
                print(atom)
        except ImportError:
            print("ASP support requires clingo.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
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
