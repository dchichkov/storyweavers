#!/usr/bin/env python3
"""
A nursery-rhyme storyworld about a dingo, a lesson learned, and a bad ending
made safer by telling the truth and asking for help.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
REPO_ROOT = os.path.dirname(ROOT)
for path in (REPO_ROOT, ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

from storyworlds.results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Scene:
    place: str
    object_name: str
    lesson: str
    bad_ending: str


@dataclass
class World:
    scene: Scene
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    dingo_name: str
    object_name: str
    seed: Optional[int] = None


PLACES = {
    "moonlit meadow": Scene(
        place="the moonlit meadow",
        object_name="a silver bell",
        lesson="ask before taking what is not yours",
        bad_ending="the bell was lost in the tall grass",
    ),
    "gum-tree path": Scene(
        place="the gum-tree path",
        object_name="a red ribbon",
        lesson="tell the truth when a mistake is made",
        bad_ending="the ribbon tore on a thorn",
    ),
    "quiet creek": Scene(
        place="the quiet creek",
        object_name="a blue cup",
        lesson="use a safe path instead of rushing",
        bad_ending="the cup slipped into the creek",
    ),
}

CHILD_NAMES = ["Luna", "Milo", "Nell", "Pip", "Tara"]
DINGO_NAMES = ["Dingo", "Rusty", "Sunny", "Goldie"]
CHILD_TYPES = {"Luna": "girl", "Nell": "girl", "Tara": "girl", "Milo": "boy", "Pip": "boy"}


@dataclass(frozen=True)
class RhymeArc:
    id: str
    opening: str
    problem: str
    turn: str
    action: str
    lesson: str
    ending: str


ARCS = (
    RhymeArc(
        id="silver_bell",
        opening="{child} and {dingo} went skipping through {place}, where a bright bell shone.",
        problem="{dingo} grabbed it with a clink and ran, though it belonged to the shepherd's stone.",
        turn="The bell fell deep in grass, and {child} cried, 'We must not hide this wrong!'",
        action="They stopped their feet, called for the shepherd, and searched by singing a steady song.",
        lesson="They learned that asking first keeps trust as bright as bells in the dawn.",
        ending="The bell was found, the shepherd smiled, and they walked home side by side.",
    ),
    RhymeArc(
        id="red_ribbon",
        opening="By {place}, {child} found a red ribbon dancing where the gum leaves swayed.",
        problem="{dingo} tugged it hard to make a flag, and a thorn caught the braid.",
        turn="{child} said, 'We made a bad ending, friend; pretending will not mend the thread.'",
        action="They told the owner, fetched a needle, and stitched the ribbon red.",
        lesson="They learned that truth and careful hands can mend a trouble made.",
        ending="The ribbon waved above the path, a sign of honesty in the shade.",
    ),
    RhymeArc(
        id="blue_cup",
        opening="At {place}, {child} and {dingo} saw a blue cup gleaming in the sun.",
        problem="{dingo} raced along a slippery bank, and down the creek the cup did run.",
        turn="{child} called, 'Slow down! A hurried paw can make a bad ending come.'",
        action="They fetched a long safe branch and asked the creek keeper for a hand.",
        lesson="They learned that safe steps and helping words are wiser than a dash.",
        ending="The cup came home, and careful paws made ripples in the sand.",
    ),
)


def _rhyme(text: str, world: World, child: Entity, dingo: Entity) -> str:
    return text.format(
        child=child.id,
        dingo=dingo.id,
        place=world.scene.place,
    )


def simulate(params: StoryParams) -> World:
    if params.child_name == params.dingo_name:
        raise StoryError("The child and dingo must have different names.")
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}.")
    if params.object_name != PLACES[params.place].object_name:
        raise StoryError("The chosen object does not belong to that place.")

    rng = random.Random(params.seed if params.seed is not None else 0)
    scene = PLACES[params.place]
    world = World(scene)
    child = world.add(
        Entity(
            id=params.child_name,
            kind="character",
            type=params.child_type,
            label=params.child_name,
        )
    )
    dingo = world.add(
        Entity(
            id=params.dingo_name,
            kind="character",
            type="dingo",
            label="dingo",
        )
    )
    object_entity = world.add(
        Entity(
            id="found_object",
            kind="thing",
            type="object",
            label=params.object_name,
        )
    )
    arc = rng.choice(ARCS)

    world.facts.update(child=child, dingo=dingo, object=object_entity, arc=arc)

    child.memes["curious"] = 1.0
    dingo.memes["eager"] = 1.0
    world.say(_rhyme(arc.opening, world, child, dingo))
    world.say("The dingo's quick paws made a bright beginning, but a poor choice was near.")
    world.para()

    object_entity.meters["taken"] = 1.0
    dingo.memes["hasty"] = 1.0
    world.say(_rhyme(arc.problem, world, child, dingo))
    world.say(_rhyme(arc.turn, world, child, dingo))
    world.para()

    child.memes["brave"] = 1.0
    world.say(f'"What shall we do?" {child.id} asked. "{arc.lesson.capitalize()}," said {dingo.id}.')
    world.say(_rhyme(arc.action, world, child, dingo))
    object_entity.meters["repaired"] = 1.0
    dingo.memes["honest"] = 1.0
    world.para()

    world.say(_rhyme(arc.lesson, world, child, dingo))
    world.say(_rhyme(arc.ending, world, child, dingo))
    child.memes["wise"] = 1.0
    dingo.memes["grateful"] = 1.0
    object_entity.meters["safe"] = 1.0
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    child: Entity = world.facts["child"]
    dingo: Entity = world.facts["dingo"]
    arc: RhymeArc = world.facts["arc"]
    return [
        f"Write a nursery rhyme about {child.id} and {dingo.id} learning to {world.scene.lesson}.",
        f"Tell a rhyming story in {world.scene.place} where a bad ending follows a hasty choice.",
        f"Write a gentle lesson-learned tale with {dingo.id}, a mistake, an honest repair, and a safe ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    dingo: Entity = world.facts["dingo"]
    arc: RhymeArc = world.facts["arc"]
    return [
        QAItem(
            question=f"What bad choice did {dingo.id} make?",
            answer=_rhyme(arc.problem, world, child, dingo),
        ),
        QAItem(
            question=f"Why did {child.id} say they should not hide the mistake?",
            answer=f"{child.id} knew that hiding the mistake would leave the {world.scene.bad_ending}; telling the truth made repair possible.",
        ),
        QAItem(
            question=f"How did {child.id} and {dingo.id} fix the trouble?",
            answer=_rhyme(arc.action, world, child, dingo),
        ),
        QAItem(
            question="What lesson did they learn?",
            answer=_rhyme(arc.lesson, world, child, dingo),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dingo?",
            answer="A dingo is a wild dog native to Australia, with a keen nose, quick feet, and a strong sense of curiosity.",
        ),
        QAItem(
            question="Why is it important to tell the truth after a mistake?",
            answer="Truth helps other people understand what happened so everyone can make the situation safer and repair what was harmed.",
        ),
        QAItem(
            question="Why should someone ask before taking an object?",
            answer="Asking first respects the object's owner and prevents a playful choice from becoming a harmful or unfair one.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(C, D, O) :- child(C), dingo(D), object(O), companion(C, D), found(D, O).
lesson_learned(C, D) :- child(C), dingo(D), honest(D), helped(C, D).
safe_ending(O) :- object(O), repaired(O), safe(O).
bad_ending_avoided(C, D, O) :- child(C), dingo(D), object(O), lesson_learned(C, D), safe_ending(O).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = []
    for place, scene in PLACES.items():
        lines.append(asp.fact("place", place.replace(" ", "_")))
        lines.append(asp.fact("object", scene.object_name.replace(" ", "_")))
    lines.extend(
        [
            asp.fact("child", "child"),
            asp.fact("dingo", "dingo"),
            asp.fact("companion", "child", "dingo"),
            asp.fact("found", "dingo", "object"),
            asp.fact("helped", "child", "dingo"),
            asp.fact("honest", "dingo"),
            asp.fact("repaired", "object"),
            asp.fact("safe", "object"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str = "#show bad_ending_avoided/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program())
        found = asp.atoms(model, "bad_ending_avoided")
        if not found:
            print("ASP verification failed: expected a safe resolution.")
            return 1
        print(f"OK: ASP program solved with {len(model)} shown atoms.")
        return 0
    except Exception as exc:
        print(f"ASP verification failed: {exc}")
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Nursery-rhyme dingo storyworld about a lesson learned after a bad ending."
    )
    parser.add_argument("--place", choices=list(PLACES))
    parser.add_argument("--child-name", choices=CHILD_NAMES)
    parser.add_argument("--dingo-name", choices=DINGO_NAMES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    dingo_name = args.dingo_name or rng.choice(DINGO_NAMES)
    if child_name == dingo_name:
        raise StoryError("The child and dingo must have different names.")
    return StoryParams(
        place=place,
        child_name=child_name,
        child_type=CHILD_TYPES.get(child_name, "child"),
        dingo_name=dingo_name,
        object_name=PLACES[place].object_name,
        seed=rng.randrange(2**31),
    )


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
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
        print("\n--- trace ---")
        for entity in sample.world.entities.values():
            print(entity.id, entity.type, dict(entity.meters), dict(entity.memes))
    if qa:
        print("\n" + format_qa(sample))


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
        print("\n".join(str(atom) for atom in model))
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams(
                place=place,
                child_name=CHILD_NAMES[i % len(CHILD_NAMES)],
                child_type=CHILD_TYPES[CHILD_NAMES[i % len(CHILD_NAMES)]],
                dingo_name=DINGO_NAMES[i % len(DINGO_NAMES)],
                object_name=scene.object_name,
                seed=100 + i,
            )
            for i, (place, scene) in enumerate(PLACES.items())
        ]
    else:
        params_list = [
            resolve_params(args, random.Random(seed + i))
            for i in range(max(1, args.n))
        ]

    samples = [generate(params) for params in params_list]
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
            header=f"### story {index + 1}" if len(samples) > 1 else "",
        )
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
