#!/usr/bin/env python3
"""
A folk tale about glow, a meeting, shishkebab, and a lesson learned on a canal path.
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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str = "Luna"
    companion: str = "Bram"
    seed: Optional[int] = None
    setting: str = "canal"
    encounter: int = 0
    lesson: int = 0
    reconciliation: int = 0
    glow: int = 0
    ending: int = 0


@dataclass(frozen=True)
class Tale:
    meeting: str
    trouble: str
    danger: str
    misunderstanding: str
    clue: str
    cause: str
    lesson: str
    repair: str
    resolution: str
    endings: tuple[str, ...]


TALES = (
    Tale(
        meeting="Luna met Bram beside the canal path, where a little iron brazier warmed a bundle of shishkebab",
        trouble="the brazier's soft glow vanished whenever Bram stepped near it",
        danger="the supper could grow cold before the travelers reached the village fair",
        misunderstanding="Bram thought Luna was hiding the fire from him, while Luna thought Bram had stolen her bright coal",
        clue="a trail of damp reeds clinging to Bram's wet boots",
        cause="Bram had carried canal water on his boots, and the drops were smothering the coal",
        lesson="a friend should ask before believing the worst",
        repair="Luna dried the coal while Bram fetched clean twigs and raised the brazier on a flat stone",
        resolution="the glow returned, and the shishkebab cooked evenly for both hungry travelers",
        endings=(
            "They shared the first warm skewer beneath the moon's silver path.",
            "At the village fair, their brazier glowed like a tiny sunrise.",
            "The canal water glittered while Luna and Bram carried supper side by side.",
            "From that evening onward, neither friend made a guess before asking a kind question.",
        ),
    ),
    Tale(
        meeting="Luna met Bram at the bend in the canal path, carrying a tray of shishkebab beneath a green cloth",
        trouble="a lantern meant to guide them began to glow red and flicker",
        danger="they might lose the path and drop the supper into the dark canal",
        misunderstanding="Luna believed Bram had shaken the lantern, and Bram believed Luna had forgotten its oil",
        clue="a thin line of oil shining on the tray's wooden handle",
        cause="the lantern's oil cup had loosened when the tray bumped a stone",
        lesson="a quarrel becomes smaller when both people look carefully together",
        repair="they tightened the oil cup, wiped the handle, and shielded the flame with the cloth",
        resolution="the lantern glowed gold, showing both friends the safe stones beneath their feet",
        endings=(
            "They reached the fair and offered the first shishkebab to the old canal keeper.",
            "Their golden lantern danced beside the water until every skewer was shared.",
            "The two friends laughed at the red flicker and walked home under a steady glow.",
            "The canal path seemed brighter because Luna and Bram had made peace upon it.",
        ),
    ),
    Tale(
        meeting="Luna met Bram beneath the willow by the canal path, where a row of shishkebab waited on a cooling rack",
        trouble="the rack's blue glow pointed toward the water instead of the village",
        danger="the meal might slide into the canal when they followed the false light",
        misunderstanding="each friend thought the other had turned the rack around as a joke",
        clue="a small magnet stuck to the rack's underside",
        cause="the canal keeper's compass magnet had been left beneath the rack",
        lesson="when blame pulls two hearts apart, shared patience can point them home",
        repair="Luna lifted the magnet while Bram turned the rack toward the path and tied it firmly",
        resolution="the glow pointed to the village, and the shishkebab stayed safely on the rack",
        endings=(
            "They entered the village together, carrying the glowing rack between them.",
            "The shishkebab sizzled while the willow leaves whispered that peace was good company.",
            "At supper, Luna and Bram placed the troublesome magnet far from every compass.",
            "The canal path kept their footprints, two sets walking home in one direction.",
        ),
    ),
)

SETTINGS = {
    "canal": "the canal path",
    "willow": "the willow-lined canal path",
    "moon": "the moonlit canal path",
}

ASP_RULES = r"""
friend(luna).
friend(bram).
word(glow).
word(meet).
word(shishkebab).
setting(canal_path).
feature(lesson_learned).
feature(reconciliation).
style(folk_tale).
valid_story :- friend(luna), friend(bram), word(glow), word(meet),
               word(shishkebab), setting(canal_path),
               feature(lesson_learned), feature(reconciliation),
               style(folk_tale).
#show valid_story/0.
"""


class World:
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A folk tale of glow, meeting, shishkebab, lesson learned, and reconciliation."
    )
    parser.add_argument("--name", default="Luna")
    parser.add_argument("--companion", default="Bram")
    parser.add_argument("--setting", choices=SETTINGS, default=None)
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
    return StoryParams(
        name=args.name.strip() or "Luna",
        companion=args.companion.strip() or "Bram",
        seed=args.seed,
        setting=args.setting or rng.choice(list(SETTINGS)),
        encounter=rng.randrange(len(TALES)),
        lesson=rng.randrange(3),
        reconciliation=rng.randrange(3),
        glow=rng.randrange(3),
        ending=rng.randrange(4),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if not params.name.strip() or not params.companion.strip():
        raise StoryError("Both travelers need names.")
    if params.name.lower() == params.companion.lower():
        raise StoryError("The two travelers need different names.")
    if params.setting not in SETTINGS:
        raise StoryError("The story must take place on a canal path.")
    if not 0 <= params.encounter < len(TALES):
        raise StoryError("Unknown canal-path encounter.")
    if not 0 <= params.lesson < 3:
        raise StoryError("Unknown lesson style.")
    if not 0 <= params.reconciliation < 3:
        raise StoryError("Unknown reconciliation style.")
    if not 0 <= params.glow < 3:
        raise StoryError("Unknown glow style.")
    if not 0 <= params.ending < 4:
        raise StoryError("Unknown ending image.")


def build_world(params: StoryParams, tale: Tale) -> World:
    place = SETTINGS[params.setting]
    world = World(place)
    luna = world.add(Entity("luna", "character", params.name, "traveler"))
    bram = world.add(Entity("bram", "character", params.companion, "traveler"))
    food = world.add(Entity("food", "object", "the shishkebab", "meal"))
    lantern = world.add(Entity("glow", "object", "the little glow", "light"))
    path = world.add(Entity("path", "place", place, "canal_path"))

    luna.memes.update({"trust": 0.4, "patience": 0.4, "relief": 0.0, "joy": 0.0})
    bram.memes.update({"trust": 0.4, "patience": 0.4, "relief": 0.0, "joy": 0.0})
    food.meters.update({"warmth": 0.8, "safety": 0.8})
    lantern.meters.update({"brightness": 0.8, "stability": 0.4})
    path.meters.update({"safety": 0.7, "visibility": 0.5})

    openings = (
        f"In a village beside the canal lived {params.name}, who carried kindness in a small basket.",
        f"Long ago, {params.name} walked the canal path with a careful step and a cheerful heart.",
        f"Each evening, {params.name} followed the canal path, listening to the water tell old stories.",
    )
    world.say(openings[params.lesson])
    world.say(f"That day, {tale.meeting}.")
    world.say(f"The meal smelled delicious, but {tale.trouble}. If nothing changed, {tale.danger}.")
    world.para()

    world.say(f'"Why did you do that?" {params.name} asked.')
    world.say(f'"I did not do what you think," {params.companion} replied. "Please let me explain."')
    if params.reconciliation == 1:
        world.say(f'{params.name} took one slow breath. "Then let us look together."')
    elif params.reconciliation == 2:
        world.say(f'{params.companion} lowered his eyes. "I was cross because I was hungry, not because I wished you harm."')
    else:
        world.say(f'"Before we quarrel, let us follow the clue," {params.name} said.')

    world.say(f"Still, {tale.misunderstanding}.")
    world.say(f"Then {params.name} noticed {tale.clue}.")
    world.say(f"The truth was plain: {tale.cause}.")
    world.para()

    glow_lines = (
        "The little glow trembled, then waited patiently for their careful hands.",
        "The glow dimmed to a bead of light, as if it too wished for peace.",
        "The glow shone along the water, revealing every wet reed and every safe stone.",
    )
    world.say(glow_lines[params.glow])
    world.say(f"They remembered that {tale.lesson}.")
    world.say(f"Together, they {tale.repair}.")
    world.say(f"As they worked, {params.name} said, \"I am sorry I blamed you.\"")
    world.say(f'{params.companion} smiled. "And I am sorry I did not speak sooner."')
    world.say(f"They forgave one another, and their reconciliation made the path feel warm.")
    world.para()

    food.meters["warmth"] = 1.0
    food.meters["safety"] = 1.0
    lantern.meters["brightness"] = 1.0
    lantern.meters["stability"] = 1.0
    path.meters["safety"] = 1.0
    path.meters["visibility"] = 1.0
    for traveler in (luna, bram):
        traveler.memes["trust"] = 1.0
        traveler.memes["patience"] = 1.0
        traveler.memes["relief"] = 1.0
        traveler.memes["joy"] = 1.0

    world.say(f"At last, {tale.resolution}.")
    world.say(tale.endings[params.ending])
    world.say(f"From then on, {params.name} and {params.companion} asked before accusing, and the canal path remembered their lesson.")

    world.facts.update(
        luna=luna,
        bram=bram,
        food=food,
        lantern=lantern,
        path=path,
        tale=tale,
        place=place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    tale: Tale = world.facts["tale"]  # type: ignore[assignment]
    return [
        "Write a child-friendly Folk Tale set on a canal path.",
        "Include a gentle glow, a meeting, and shishkebab in the story.",
        f"Show how the friends learn that {tale.lesson}, ending with reconciliation.",
    ]


def story_questions(world: World) -> list[QAItem]:
    tale: Tale = world.facts["tale"]  # type: ignore[assignment]
    luna: Entity = world.facts["luna"]  # type: ignore[assignment]
    bram: Entity = world.facts["bram"]  # type: ignore[assignment]
    return [
        QAItem(
            "Who met on the canal path?",
            f"{luna.label} met {bram.label} on the canal path while carrying shishkebab.",
        ),
        QAItem(
            "What happened to the glow?",
            f"The glow became troublesome because {tale.trouble}.",
        ),
        QAItem(
            "Why did the friends misunderstand one another?",
            f"They misunderstood one another because {tale.misunderstanding}.",
        ),
        QAItem(
            "What clue revealed the truth?",
            f"The clue was {tale.clue}, which showed that {tale.cause}.",
        ),
        QAItem(
            "What lesson did they learn?",
            f"They learned that {tale.lesson} They apologized, worked together, and reconciled.",
        ),
        QAItem(
            "How did the tale end?",
            f"It ended happily: {tale.resolution} {tale.endings[0]}",
        ),
    ]


def world_knowledge_qa(_: World) -> list[QAItem]:
    return [
        QAItem(
            "What is reconciliation?",
            "Reconciliation is making peace after a disagreement by telling the truth, apologizing, and forgiving.",
        ),
        QAItem(
            "What is a lesson learned in a tale?",
            "It is a useful idea the characters discover through what happens to them.",
        ),
        QAItem(
            "Why can a glow help travelers?",
            "A glow can make a dark path easier to see and help travelers find safe steps.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        parts = []
        if entity.meters:
            parts.append(f"meters={entity.meters}")
        if entity.memes:
            parts.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id} ({entity.type}) {' '.join(parts)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    return "\n".join(
        (
            asp.fact("friend", "luna"),
            asp.fact("friend", "bram"),
            asp.fact("word", "glow"),
            asp.fact("word", "meet"),
            asp.fact("word", "shishkebab"),
            asp.fact("setting", "canal_path"),
            asp.fact("feature", "lesson_learned"),
            asp.fact("feature", "reconciliation"),
            asp.fact("style", "folk_tale"),
        )
    )


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    found = set(asp.atoms(model, "valid_story"))
    if found == {()}:
        print("OK: ASP confirms the complete canal-path folk tale domain.")
        return 0
    print("MISMATCH")
    print("clingo:", sorted(found))
    return 1


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    tale = TALES[params.encounter]
    world = build_world(params, tale)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_questions(world),
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print(asp.atoms(model, "valid_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index in range(len(TALES)):
            rng = random.Random(base_seed + index)
            params = StoryParams(
                name=args.name,
                companion=args.companion,
                seed=base_seed + index,
                setting=rng.choice(list(SETTINGS)),
                encounter=index,
                lesson=rng.randrange(3),
                reconciliation=rng.randrange(3),
                glow=rng.randrange(3),
                ending=rng.randrange(4),
            )
            samples.append(generate(params))
    else:
        for index in range(max(1, args.n)):
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
