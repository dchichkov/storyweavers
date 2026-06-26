#!/usr/bin/env python3
"""
A small fable-world about a piglet, a wagging tail, bravery, repetition, and dialogue.

This storyworld generates one child-friendly fable-like tale in which a timid piglet
learns bravery by trying again, listening, and speaking up. The "wag" seed word is
used both as a physical action and as the little rhythm of the piglet's tail.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    state: str = ""

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"piglet", "pig", "boar", "hog"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Scene:
    place: str = "the little barn lane"
    obstacle: str = "the low creek"
    helper: str = "the old goose"
    lesson: str = "bravery grows when a small heart tries again"


@dataclass
class StoryParams:
    place: str = "the little barn lane"
    obstacle: str = "the low creek"
    helper: str = "the old goose"
    seed: Optional[int] = None


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.scene)
        clone.entities = {
            k: Entity(
                id=v.id, kind=v.kind, label=v.label, type=v.type,
                traits=list(v.traits), owner=v.owner,
                meters=dict(v.meters), memes=dict(v.memes), state=v.state
            )
            for k, v in self.entities.items()
        }
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Parameters / registries
# ---------------------------------------------------------------------------

SCENES = {
    "lane": Scene(place="the little barn lane", obstacle="the low creek", helper="the old goose"),
    "meadow": Scene(place="the sunny meadow path", obstacle="the narrow ditch", helper="the patient cow"),
    "orchard": Scene(place="the apple orchard trail", obstacle="the muddy brook", helper="the wise hen"),
}

PIGLET_NAMES = ["Pip", "Poppy", "Milo", "Mimi", "Tilly", "Nell"]
HELPERS = {
    "the old goose": "goose",
    "the patient cow": "cow",
    "the wise hen": "hen",
}

TRAITS = ["small", "pink", "gentle", "curious"]


# ---------------------------------------------------------------------------
# Inline ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A scene is brave when the piglet tries more than once and speaks with help.
brave_scene(S) :- place(S), obstacle(S), helper(S).

% "wag" is the physical sign of hope; if the piglet's tail wags, the mood rises.
hopeful(piglet) :- tail_wags(piglet).

% Repetition: if a first try fails, a second try can happen.
tries_again(piglet) :- first_try(piglet), not stopped(piglet).

% Dialogue: a helper's words can change the piglet's mind.
listens(piglet) :- said(helper, piglet, _).

#show brave_scene/1.
#show hopeful/1.
#show tries_again/1.
#show listens/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("place", sid))
        lines.append(asp.fact("obstacle", sid))
        lines.append(asp.fact("helper", sid))
    lines.append(asp.fact("tail_wags", "piglet"))
    lines.append(asp.fact("first_try", "piglet"))
    lines.append(asp.fact("said", "helper", "piglet", "try_again"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show brave_scene/1.\n#show hopeful/1.\n#show tries_again/1.\n#show listens/1."))
    atoms = {(a.name, tuple(str(x) for x in a.arguments)) for a in model}
    expected = {
        ("brave_scene", ("lane",)),
        ("brave_scene", ("meadow",)),
        ("brave_scene", ("orchard",)),
        ("hopeful", ("piglet",)),
        ("tries_again", ("piglet",)),
        ("listens", ("piglet",)),
    }
    if atoms & expected:
        print("OK: ASP program is alive.")
        return 0
    print("ASP verification failed.")
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------


def introduce(world: World, piglet: Entity) -> None:
    world.say(
        f"Once, a little piglet named {piglet.id} lived by {world.scene.place}. "
        f"{piglet.id} was small, pink, and kind, but not yet sure of its own brave heart."
    )


def wag_tail(world: World, piglet: Entity) -> None:
    piglet.meters["wag"] = piglet.meters.get("wag", 0) + 1
    piglet.memes["hope"] = piglet.memes.get("hope", 0) + 1
    world.say(
        f"When {piglet.id} felt nervous, its tail gave a tiny wag, as if it were trying to cheer itself up."
    )


def meet_obstacle(world: World, piglet: Entity, scene: Scene) -> None:
    world.say(
        f"One morning, {piglet.id} came to {scene.obstacle} and stopped short. "
        f"The water looked deeper than a piglet could like."
    )


def first_try(world: World, piglet: Entity, scene: Scene) -> None:
    piglet.memes["fear"] = piglet.memes.get("fear", 0) + 1
    world.say(
        f"{piglet.id} looked left, then right, and tried to step across. "
        f"But the stones wobbled, so {piglet.id} stepped back."
    )


def dialogue(world: World, piglet: Entity, helper: Entity) -> None:
    piglet.memes["listening"] = piglet.memes.get("listening", 0) + 1
    helper.memes["kindness"] = helper.memes.get("kindness", 0) + 1
    world.say(
        f'"Little one," said {helper.label}, "bravery is not the same as never wobbling. '
        f'Bravery is trying again."'
    )
    world.say(
        f'{piglet.id} blinked and asked, "Try again?" '
        f'{helper.label} nodded. "Yes, and keep your eyes on the far bank."'
    )


def second_try(world: World, piglet: Entity, scene: Scene) -> None:
    piglet.memes["bravery"] = piglet.memes.get("bravery", 0) + 1
    piglet.meters["steps"] = piglet.meters.get("steps", 0) + 1
    world.say(
        f"So {piglet.id} tried again. This time it took one careful step, then another, "
        f"and then it found the firm stones one by one."
    )


def resolve(world: World, piglet: Entity, helper: Entity, scene: Scene) -> None:
    piglet.memes["joy"] = piglet.memes.get("joy", 0) + 1
    piglet.memes["bravery"] = piglet.memes.get("bravery", 0) + 1
    world.say(
        f"At last {piglet.id} crossed {scene.obstacle}. Its tail wagged so brightly that even the helper smiled."
    )
    world.say(
        f'"See?" said {helper.label}. "A brave heart can grow by repeating a good try." '
        f"And {piglet.id} went on, a little steadier, a little bolder, and very glad."
    )


def tell(scene: Scene, name: str) -> World:
    world = World(scene)
    piglet = world.add(Entity(id=name, kind="character", label="the piglet", type="piglet", traits=["small", "pink", "gentle"]))
    helper = world.add(Entity(id="Helper", kind="character", label=scene.helper, type=HELPERS[scene.helper], traits=["wise", "kind"]))
    world.facts.update(scene=scene, piglet=piglet, helper=helper)

    introduce(world, piglet)
    world.para()
    meet_obstacle(world, piglet, scene)
    first_try(world, piglet, scene)
    wag_tail(world, piglet)
    dialogue(world, piglet, helper)
    second_try(world, piglet, scene)
    resolve(world, piglet, helper, scene)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------


def generation_prompts(world: World) -> list[str]:
    scene: Scene = world.facts["scene"]  # type: ignore[assignment]
    return [
        f"Write a short fable about a piglet, a wagging tail, and a lesson learned at {scene.place}.",
        f"Tell a gentle story where a piglet faces {scene.obstacle} and learns bravery by trying again.",
        f"Write a child-friendly fable with dialogue in which a helper's words help a piglet cross {scene.obstacle}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    scene: Scene = world.facts["scene"]  # type: ignore[assignment]
    piglet: Entity = world.facts["piglet"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {piglet.id}, a little piglet who lives by {scene.place}.",
        ),
        QAItem(
            question=f"What did {piglet.id} face in the story?",
            answer=f"{piglet.id} faced {scene.obstacle}, and it looked too tricky at first.",
        ),
        QAItem(
            question=f"Who helped {piglet.id} with brave words?",
            answer=f"{helper.label} helped by speaking kindly and telling {piglet.id} to try again.",
        ),
        QAItem(
            question=f"What changed when {piglet.id} kept trying?",
            answer=f"{piglet.id} crossed the water in the end, and its tail wagged with happy bravery.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing something even when you feel a little scared.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means doing something again and again, which can help you learn.",
        ),
        QAItem(
            question="Why is dialogue useful in a fable?",
            answer="Dialogue lets the characters speak, listen, and change their minds with words.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== world qa ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.extend(f"story: {s}" for s in world.trace)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable storyworld about a piglet and bravery.")
    ap.add_argument("--place", choices=SCENES.keys())
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SCENES.keys()))
    scene = SCENES[place]
    return StoryParams(place=scene.place, obstacle=scene.obstacle, helper=scene.helper, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    scene = Scene(place=params.place, obstacle=params.obstacle, helper=params.helper)
    name = random.Random(params.seed).choice(PIGLET_NAMES) if params.seed is not None else random.choice(PIGLET_NAMES)
    world = tell(scene, name)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show brave_scene/1.\n#show hopeful/1.\n#show tries_again/1.\n#show listens/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show brave_scene/1.\n#show hopeful/1.\n#show tries_again/1.\n#show listens/1."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, scene in enumerate(SCENES.values()):
            params = StoryParams(place=scene.place, obstacle=scene.obstacle, helper=scene.helper, seed=base_seed + i)
            samples.append(generate(params))
    else:
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
