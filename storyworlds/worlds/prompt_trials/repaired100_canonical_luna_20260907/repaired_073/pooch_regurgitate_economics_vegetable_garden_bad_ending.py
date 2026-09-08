#!/usr/bin/env python3
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


SETTINGS = {
    "vegetable_garden": {
        "place": "the vegetable garden",
        "detail": "Rows of carrots, beans, and pumpkins grew between damp paths and a crooked wooden fence.",
        "affords": {"gardening"},
    }
}

NAMES = ["Luna", "Milo", "Tessa", "Nora", "Pip", "Ada"]
NAME_GENDERS = {
    "Luna": "girl",
    "Milo": "boy",
    "Tessa": "girl",
    "Nora": "girl",
    "Pip": "boy",
    "Ada": "girl",
}
ADULTS = ["Grandma", "Dad", "Aunt May", "Uncle Ben"]
TRAITS = ["curious", "brave", "careful", "cheerful", "quiet", "inventive"]

INCIDENTS = [
    {
        "arrival": "Luna brought a hungry pooch named Pepper to help carry a basket of vegetables.",
        "problem": "Pepper swallowed a mouthful of old beet scraps and began to regurgitate them beside the bean row.",
        "mistake": "Luna tried to hide the mess under a cabbage leaf because she feared the garden's vegetable economics would be ruined.",
        "clue": "The sour smell reached the compost corner, where a sign explained that spoiled scraps belonged in the compost bin, not near growing food.",
        "plan": "The adult kept Pepper away from the beds, Luna fetched water and a scoop, and they moved the scraps to the compost bin.",
        "dialogue": [
            '"Is Pepper sick?" Luna asked.',
            '"Maybe, but we must not guess," Grandma said. "We will keep him safe and tell the gardener."',
        ],
        "result": "The gardener checked Pepper, found no dangerous plant in the scraps, and washed the nearby tools.",
        "ending": "But Pepper stayed ill, and the evening harvest was too small to sell at the village table.",
        "lesson": "hiding a problem can hurt both animals and people who depend on a garden",
        "object": "beet scraps",
    },
    {
        "arrival": "Milo led a friendly pooch named Button along the garden path while his family counted baskets for market.",
        "problem": "Button found a pile of wilted vegetables and tried to regurgitate a tangled wad beside the pumpkin vines.",
        "mistake": "Milo called it a funny trick and almost let the pooch wander into the planted beds.",
        "clue": "A ghostly pale shape appeared in the greenhouse glass, pointing toward the compost sign.",
        "plan": "Milo called for an adult, the adult blocked the rows, and the gardener moved the scraps while checking what Button had eaten.",
        "dialogue": [
            '"Did the ghost tell us where to go?" Milo whispered.',
            '"It told us to use our eyes," Dad replied. "The sign says compost, and the dog needs care."',
        ],
        "result": "Button received water and a quiet place, while the spoiled vegetables were safely composted.",
        "ending": "The ghostly shape faded, but the damaged pumpkin vine meant fewer pumpkins for the market.",
        "lesson": "a strange sign should lead to careful action, not a careless joke",
        "object": "wilted vegetables",
    },
    {
        "arrival": "Tessa visited the vegetable garden with a pooch named Wisp while her aunt planned the week's food budget.",
        "problem": "Wisp began to regurgitate after chewing a green stem near the pea trellis.",
        "mistake": "Tessa guessed that the pooch was only pretending and offered him another leaf.",
        "clue": "A cold breath moved through the garden, and a pale face appeared between the rows as if a ghost wanted her to stop.",
        "plan": "Tessa dropped the leaf, called Aunt May, and helped keep Wisp still while the adult identified the plant and contacted a vet.",
        "dialogue": [
            '"The ghost is warning us," Tessa said.',
            '"The warning is useful because we can check the plant," Aunt May answered. "Now we act quickly."',
        ],
        "result": "The vet treated Wisp and told them to remove the unknown stems from the path.",
        "ending": "Wisp recovered, but the garden lost a day of work and the family could not afford the extra seed order.",
        "lesson": "careful evidence matters when an animal may have eaten something harmful",
        "object": "green stems",
    },
    {
        "arrival": "Nora brought a small pooch named Clover to the garden while her family sorted vegetables by size and price.",
        "problem": "Clover regurgitated a bright red pepper near the weighing table.",
        "mistake": "Nora assumed the pepper was harmless because it looked shiny and clean.",
        "clue": "A thin ghostly whisper seemed to say, 'Ask before you sort,' and the pepper's label lay under a wet basket.",
        "plan": "Nora called the gardener, kept Clover from the table, and checked the label before deciding whether the pepper could be sold.",
        "dialogue": [
            '"Can we sell it?" Nora asked.',
            '"Not until we know where it came from," Uncle Ben said. "Economics begins with honest information."',
        ],
        "result": "The pepper came from a treated row and was discarded; Clover was watched until he felt better.",
        "ending": "The lost pepper lowered the day's earnings, and the family had to postpone buying a new watering hose.",
        "lesson": "honest labels protect both health and fair trade",
        "object": "a red pepper",
    },
]


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
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
    name: str
    gender: str
    adult: str
    trait: str
    seed: Optional[int] = None
    incident: int = 0
    cadence: int = 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A ghost story about a pooch, regurgitation, and vegetable-garden economics."
    )
    parser.add_argument("--place", choices=SETTINGS.keys())
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--adult", choices=ADULTS)
    parser.add_argument("--trait", choices=TRAITS)
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
    return StoryParams(
        place=args.place or "vegetable_garden",
        name=name,
        gender=args.gender or NAME_GENDERS[name],
        adult=args.adult or rng.choice(ADULTS),
        trait=args.trait or rng.choice(TRAITS),
        incident=rng.randrange(len(INCIDENTS)),
        cadence=rng.randrange(1000),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("This story must take place in the vegetable garden.")
    if params.gender not in {"girl", "boy"}:
        raise StoryError("The child must be identified as a girl or boy.")
    if params.incident < 0 or params.incident >= len(INCIDENTS):
        raise StoryError("The selected garden incident does not exist.")


def _build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    incident = INCIDENTS[params.incident]
    world = World(SETTINGS[params.place]["place"])

    child = world.add(Entity(
        "Child", "character", params.gender, params.name,
        meters={"curiosity": 1.0, "worry": 0.2},
        memes={"honesty": 0.4},
    ))
    adult = world.add(Entity(
        "Adult", "character", "adult", params.adult,
        meters={"care": 1.0},
        memes={"trust": 1.0},
    ))
    pooch = world.add(Entity(
        "Pooch", "animal", "dog", "pooch", "a small brown pooch",
        owner=child.id,
        meters={"health": 0.55, "hunger": 0.7},
        memes={"loyalty": 1.0},
    ))
    garden = world.add(Entity(
        "Garden", "place", "vegetable_garden", "vegetable garden",
        meters={"harvest": 0.8, "income": 0.8},
        memes={"care": 1.0},
    ))
    ghost = world.add(Entity(
        "Ghost", "spirit", "ghost", "ghost",
        meters={"visibility": 0.35},
        memes={"warning": 1.0},
    ))
    scraps = world.add(Entity(
        "Scraps", "thing", "spoiled_vegetables", incident["object"],
        meters={"safe_for_eating": 0.0},
        memes={"compostable": 1.0},
    ))

    world.say(
        f"In {world.place}, {params.name}, a {params.trait} {params.gender}, came to help {params.adult} count vegetables for the market."
    )
    world.say(SETTINGS[params.place]["detail"])
    world.say(incident["arrival"])
    world.say(
        f"The family talked about vegetable economics: healthy produce could be sold, while spoiled produce meant less money for seeds, tools, and food."
    )
    world.para()
    world.say(incident["problem"])
    world.say(incident["mistake"])
    world.say(incident["clue"])
    world.say(
        f"A pale figure stood beyond the fence. It looked like a ghost, but it did not touch the rows or make a sound."
    )
    for line in incident["dialogue"]:
        world.say(line)
    world.say(
        f"{params.name} understood that the pooch needed help, and that a garden problem could not be hidden just because it was embarrassing."
    )
    world.para()
    world.say(incident["plan"])
    world.say(
        "The ghost lifted one transparent hand toward the compost bin, then vanished behind the pumpkin leaves."
    )
    world.say(incident["result"])
    world.say(
        f"{params.adult} recorded the spoiled food honestly, because economics was not only about earning money; it was also about caring for animals, soil, and people."
    )
    world.say(incident["ending"])
    world.say(
        f"{params.name} wished the ending had been happier, but learned that a bad ending can still leave a useful warning: tell the truth early, protect the pooch, and care for the garden before a small mistake grows."
    )

    pooch.meters["health"] = 0.7
    pooch.memes["received_care"] = 1.0
    garden.meters["harvest"] = 0.55
    garden.meters["income"] = 0.4
    ghost.meters["visibility"] = 0.0
    child.memes["honesty"] = 1.0

    world.facts.update(
        params=params,
        incident=incident,
        child=child,
        adult=adult,
        pooch=pooch,
        garden=garden,
        ghost=ghost,
        scraps=scraps,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    incident = world.facts["incident"]
    return [
        f"Write a gentle ghost story about {params.name}, a pooch, and a vegetable garden.",
        f"Include a pooch that tries to regurgitate {incident['object']}, a practical warning, and vegetable economics.",
        "Write a child-facing story with dialogue and a bad ending that teaches why hiding an animal or garden problem is dangerous.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params = world.facts["params"]
    incident = world.facts["incident"]
    return [
        QAItem(
            "Who visited the vegetable garden?",
            f"{params.name} visited the vegetable garden with {params.adult} and a pooch."
        ),
        QAItem(
            "What happened to the pooch?",
            f"The pooch began to regurgitate {incident['object']} after eating something it should not have eaten."
        ),
        QAItem(
            "What did the ghost's warning help the family notice?",
            incident["clue"],
        ),
        QAItem(
            "How did the adults respond?",
            f"They kept the pooch away from the garden beds, checked what it had eaten, and moved unsafe scraps to compost or disposal. {incident['result']}"
        ),
        QAItem(
            "Why was the ending bad?",
            f"{incident['ending']} The lost harvest or extra care cost affected the family's vegetable economics."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a pooch?",
            "A pooch is an informal, friendly word for a dog."
        ),
        QAItem(
            "What does regurgitate mean?",
            "Regurgitate means to bring food back up after swallowing it."
        ),
        QAItem(
            "What is a vegetable garden?",
            "A vegetable garden is a place where people grow edible plants such as carrots, beans, and pumpkins."
        ),
        QAItem(
            "What are economics?",
            "Economics is the study of how people use, save, earn, and share limited goods and money."
        ),
        QAItem(
            "What should someone do if a dog may have eaten a harmful plant?",
            "They should keep the dog away from more plants, tell a trusted adult, and contact a veterinarian for advice."
        ),
    ]


ASP_RULES = r"""
#show compatible/1.
compatible(story) :- garden, pooch, regurgitation, warning, dialogue, bad_ending.
"""


def asp_facts() -> str:
    return "\n".join([
        "garden.",
        "pooch.",
        "regurgitation.",
        "warning.",
        "dialogue.",
        "bad_ending.",
    ])


def asp_program(show: str = "#show compatible/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        from asp import atoms, one_model
        model = one_model(asp_program())
        if ("story",) not in atoms(model, "compatible"):
            return 1
    except Exception:
        return 1
    return 0


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:8} ({entity.type:18}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


CURATED = [
    StoryParams("vegetable_garden", "Luna", "girl", "Grandma", "curious", incident=0, cadence=4),
    StoryParams("vegetable_garden", "Milo", "boy", "Dad", "brave", incident=1, cadence=9),
    StoryParams("vegetable_garden", "Tessa", "girl", "Aunt May", "careful", incident=2, cadence=15),
    StoryParams("vegetable_garden", "Nora", "girl", "Uncle Ben", "quiet", incident=3, cadence=22),
]


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            from asp import atoms, one_model
            model = one_model(asp_program())
            print("compatible:", bool(atoms(model, "compatible")))
        except Exception as exc:
            raise StoryError(f"ASP mode requires the clingo helper: {exc}") from exc
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
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
        header = ""
        if args.all:
            header = f"### {sample.params.name}: ghostly garden warning"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
