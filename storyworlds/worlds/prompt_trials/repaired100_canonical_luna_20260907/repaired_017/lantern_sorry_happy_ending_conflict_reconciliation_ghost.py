#!/usr/bin/env python3
"""
A gentle ghost story about a lantern, a mistake, and reconciliation.

Luna carries a lantern through an old house, where a friendly ghost is upset
because a treasured bell was moved without permission. A careful apology,
honest listening, and a shared repair turn the conflict into a happy ending.
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
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
REPO_ROOT = os.path.dirname(ROOT)
for path in (REPO_ROOT, ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    location: str = ""

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Scene:
    place: str
    weather: str
    landmark: str


@dataclass
class World:
    scene: Scene
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    weather: str
    child_name: str
    child_type: str
    ghost_name: str
    ghost_type: str
    lantern_kind: str
    landmark: str
    seed: Optional[int] = None


PLACES = {
    "manor": Scene("the old manor", "a misty evening", "the round stairwell"),
    "lighthouse": Scene("the quiet lighthouse", "a windy night", "the spiral stairs"),
    "schoolhouse": Scene("the abandoned schoolhouse", "a rainy dusk", "the moonlit hallway"),
}

LANTERNS = {
    "brass lantern": {"light": "golden", "weight": "solid"},
    "blue glass lantern": {"light": "blue", "weight": "light"},
    "tin lantern": {"light": "soft", "weight": "small"},
}

CHILD_NAMES = ["Luna", "Maya", "Theo", "Nia", "Owen", "Iris"]
GHOST_NAMES = ["Milo", "Wisp", "Etta", "Bram", "Pip"]

OPENINGS = (
    "{child} carried a {lantern} through {place} on {weather}.",
    "On {weather}, {child} stepped into {place} with a {lantern} held close.",
    "The mist gathered around {place} as {child} lifted a {lantern} and began to walk.",
)

DIALOGUES = (
    '"I did not mean to frighten you," {child} said. "Then please listen," replied {ghost}.',
    '"Is something wrong?" {child} asked. "The bell was moved," said {ghost}, "and it mattered to me."',
    '"I am sorry," said {child}. The ghost answered, "A true apology begins with hearing why."',
)

ARC_TEXT = {
    "manor": {
        "object": "a silver bell",
        "problem": "The bell had been moved from the stairwell to make room for a box of old books.",
        "turn": "The ghost explained that the bell had been the last gift from a friend who had vanished long ago.",
        "action": "Luna carried the lantern while the two of them searched the dusty rooms for the bell's proper hook.",
        "ending": "When the bell rang again, its bright note sent the shadows dancing instead of hiding.",
    },
    "lighthouse": {
        "object": "a shell chime",
        "problem": "The shell chime had been taken down from the lantern room because its string was tangled.",
        "turn": "The ghost revealed that the chime's small music helped lonely sailors feel that someone was watching over them.",
        "action": "Together they untangled the string, and Luna used the lantern's steady light to guide the ghost's floating hands.",
        "ending": "The repaired chime sang above the sea, and even the ghost's pale face looked warm.",
    },
    "schoolhouse": {
        "object": "a wooden music box",
        "problem": "The music box had been placed inside a cupboard after Luna found it blocking the hallway.",
        "turn": "The ghost said the music box played the tune that had once called children in from the rain.",
        "action": "Luna opened the cupboard, dusted the music box, and set it on a safe shelf beside the lantern.",
        "ending": "The little tune filled the hallway, and the ghost invited Luna to dance across the moonlit floor.",
    },
}


def simulate(params: StoryParams) -> World:
    scene = PLACES[params.place]
    arc = ARC_TEXT[params.place]
    world = World(scene)

    child = world.add(
        Entity(
            id=params.child_name,
            kind="character",
            type=params.child_type,
            label=params.child_name,
            location=scene.place,
        )
    )
    ghost = world.add(
        Entity(
            id=params.ghost_name,
            kind="character",
            type=params.ghost_type,
            label=f"Ghost {params.ghost_name}",
            location=scene.place,
        )
    )
    lantern = world.add(
        Entity(
            id="lantern",
            kind="thing",
            type="lantern",
            label=params.lantern_kind,
            owner=child.id,
            location=scene.place,
        )
    )
    keepsake = world.add(
        Entity(
            id="keepsake",
            kind="thing",
            type="keepsake",
            label=arc["object"],
            owner=ghost.id,
            location=scene.place,
        )
    )

    world.facts.update(
        child=child,
        ghost=ghost,
        lantern=lantern,
        keepsake=keepsake,
        arc=arc,
        scene=scene,
        conflict=True,
        reconciliation=False,
        happy_ending=False,
    )

    rng = random.Random(params.seed if params.seed is not None else 0)
    world.say(
        rng.choice(OPENINGS).format(
            child=child.id,
            lantern=lantern.label,
            place=scene.place,
            weather=scene.weather,
        )
    )
    world.say(
        f"The lantern cast a {LANTERNS[params.lantern_kind]['light']} circle over "
        f"{scene.landmark}, but a cold shadow moved just beyond it."
    )
    world.para()

    world.say(arc["problem"])
    ghost.memes["hurt"] = 1.0
    ghost.meters["keepsake_missing"] = 1.0
    child.memes["worried"] = 1.0
    world.say(
        f"Ghost {ghost.id} appeared beside the {lantern.label} and frowned at "
        f"{child.id}."
    )
    world.say(rng.choice(DIALOGUES).format(child=child.id, ghost=f"Ghost {ghost.id}"))
    world.para()

    world.say(arc["turn"])
    child.memes["understanding"] = 1.0
    world.say(
        f"{child.id} lowered the {lantern.label}, so its light would not hide the "
        f"ghost's face."
    )
    world.say(
        f'"I am sorry I moved the {keepsake.label}," {child.id} said. '
        f'"I should have asked first."'
    )
    world.say(
        f'"Thank you for saying sorry," Ghost {ghost.id} replied. '
        f'"Will you help me put it right?"'
    )
    child.memes["kind"] = 1.0
    world.para()

    world.say(arc["action"])
    keepsake.location = scene.landmark
    keepsake.meters["returned"] = 1.0
    lantern.meters["guiding"] = 1.0
    child.meters["repairing"] = 1.0
    ghost.memes["trust"] = 1.0
    world.say(
        f"The {lantern.label} showed them a safe path, and the {keepsake.label} "
        f"was returned to its rightful place."
    )
    world.facts["reconciliation"] = True
    world.facts["conflict"] = False
    world.say(
        f"Ghost {ghost.id} smiled. The cold shadow shrank until it was only a "
        f"small patch of ordinary darkness."
    )
    world.para()

    world.say(arc["ending"])
    world.say(
        f"{child.id} and Ghost {ghost.id} stood together beneath the {lantern.label}, "
        f"watching the light reach every corner."
    )
    child.memes["relieved"] = 1.0
    ghost.memes["happy"] = 1.0
    world.facts["happy_ending"] = True
    world.say(
        f"Before {child.id} went home, Ghost {ghost.id} said, "
        f'"You may visit whenever you bring that honest light."'
    )
    world.say(
        f"{child.id} waved goodbye, and the {lantern.label} glowed beside the "
        f"repaired {keepsake.label} until dawn."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    ghost: Entity = f["ghost"]
    scene: Scene = f["scene"]
    return [
        f"Write a gentle ghost story about {child.id} carrying a lantern through {scene.place}.",
        f"Create a story where {child.id} has a conflict with Ghost {ghost.id}, says sorry, and reaches reconciliation.",
        f"Tell a child-friendly ghost story with a lantern, an honest apology, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    ghost: Entity = f["ghost"]
    lantern: Entity = f["lantern"]
    keepsake: Entity = f["keepsake"]
    arc = f["arc"]
    return [
        QAItem(
            question=f"Why was Ghost {ghost.id} upset with {child.id}?",
            answer=(
                f"Ghost {ghost.id} was upset because {child.id} had moved the "
                f"{keepsake.label} without asking, and the object was precious to the ghost."
            ),
        ),
        QAItem(
            question=f"How did the lantern help {child.id} and Ghost {ghost.id}?",
            answer=(
                f"The {lantern.label} gave them a steady light while they searched "
                f"together and returned the {keepsake.label} safely."
            ),
        ),
        QAItem(
            question=f"What did {child.id} say sorry for?",
            answer=(
                f"{child.id} said sorry for moving the {keepsake.label} without "
                f"asking first and promised to help repair the mistake."
            ),
        ),
        QAItem(
            question="How was the conflict resolved?",
            answer=(
                f"{child.id} listened to why the {keepsake.label} mattered, apologized, "
                f"and worked with Ghost {ghost.id} to return it to its proper place."
            ),
        ),
        QAItem(
            question="What showed that the story had a happy ending?",
            answer=(
                f"The {keepsake.label} was safely returned, Ghost {ghost.id} felt happy "
                f"again, and the lantern glowed beside it until dawn."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lantern?",
            answer=(
                "A lantern is a covered light that helps people see in dark places "
                "while protecting its flame or bulb."
            ),
        ),
        QAItem(
            question="Why is saying sorry important after a mistake?",
            answer=(
                "Saying sorry shows that someone understands the harm, accepts "
                "responsibility, and wants to help make things right."
            ),
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer=(
                "Reconciliation means repairing a disagreement so people can trust "
                "one another and continue together."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(C,G,L,K) :- child(C), ghost(G), lantern(L), keepsake(K).
conflict(C,G) :- moved_without_asking(C,K), owns(G,K).
reconciled(C,G) :- apologized(C), returned(K), owns(G,K).
happy_ending(C,G) :- reconciled(C,G), lantern(C,L), lit(L).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for lantern in LANTERNS:
        lines.append(asp.fact("lantern", lantern.replace(" ", "_")))
    lines.extend(
        [
            asp.fact("child", "luna"),
            asp.fact("ghost", "milo"),
            asp.fact("keepsake", "bell"),
            asp.fact("owns", "milo", "bell"),
            asp.fact("moved_without_asking", "luna", "bell"),
            asp.fact("apologized", "luna"),
            asp.fact("returned", "bell"),
            asp.fact("lit", "brass_lantern"),
            asp.fact("lantern", "luna", "brass_lantern"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str = "#show happy_ending/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program())
    if not model:
        print("ASP verification failed: no model.")
        return 1
    endings = asp.atoms(model, "happy_ending")
    if ("luna", "milo") not in endings:
        print("ASP verification failed: reconciliation parity missing.")
        return 1
    for seed in range(5):
        params = StoryParams(
            place="manor",
            weather="a misty evening",
            child_name="Luna",
            child_type="girl",
            ghost_name="Milo",
            ghost_type="man",
            lantern_kind="brass lantern",
            landmark="the round stairwell",
            seed=seed,
        )
        sample = generate(params)
        if not sample.world or not sample.world.facts["happy_ending"]:
            print("Python verification failed: unresolved ending.")
            return 1
    print("OK: ASP and Python reconciliation checks passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gentle lantern ghost storyworld.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--weather")
    parser.add_argument("--child-name", choices=CHILD_NAMES)
    parser.add_argument("--ghost-name", choices=GHOST_NAMES)
    parser.add_argument("--lantern-kind", choices=LANTERNS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    scene = PLACES[place]
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    if child_name == ghost_name:
        raise StoryError("The child and ghost must have different names.")
    lantern_kind = args.lantern_kind or rng.choice(list(LANTERNS))
    weather = args.weather or scene.weather
    child_type = "girl" if child_name in {"Luna", "Maya", "Nia", "Iris"} else "boy"
    ghost_type = "woman" if ghost_name in {"Etta"} else "man"
    return StoryParams(
        place=place,
        weather=weather,
        child_name=child_name,
        child_type=child_type,
        ghost_name=ghost_name,
        ghost_type=ghost_type,
        lantern_kind=lantern_kind,
        landmark=scene.landmark,
        seed=rng.randrange(2**31),
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.lantern_kind not in LANTERNS:
        raise StoryError(f"Unknown lantern kind: {params.lantern_kind}")
    world = simulate(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- trace ---")
        for entity in sample.world.entities.values():
            print(
                f"{entity.id}: type={entity.type}, location={entity.location}, "
                f"meters={entity.meters}, memes={entity.memes}"
            )
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program())
        print("\n".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    curated = [
        StoryParams(
            place="manor",
            weather="a misty evening",
            child_name="Luna",
            child_type="girl",
            ghost_name="Milo",
            ghost_type="man",
            lantern_kind="brass lantern",
            landmark="the round stairwell",
            seed=101,
        ),
        StoryParams(
            place="lighthouse",
            weather="a windy night",
            child_name="Theo",
            child_type="boy",
            ghost_name="Etta",
            ghost_type="woman",
            lantern_kind="blue glass lantern",
            landmark="the spiral stairs",
            seed=202,
        ),
        StoryParams(
            place="schoolhouse",
            weather="a rainy dusk",
            child_name="Iris",
            child_type="girl",
            ghost_name="Bram",
            ghost_type="man",
            lantern_kind="tin lantern",
            landmark="the moonlit hallway",
            seed=303,
        ),
    ]

    if args.all:
        samples = [generate(params) for params in curated]
    else:
        samples = []
        seen: set[str] = set()
        for index in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + index))
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
            header=f"### story {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
