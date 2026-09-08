#!/usr/bin/env python3
"""
A small pirate tale about humming, disinfectant, and learning to clean safely.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Voyage:
    id: str
    place: str
    mess: str
    danger: str
    clue: str
    wrong_action: str
    consequence: str
    captain_line: str
    safe_action: str
    ending: str
    moral: str


@dataclass
class World:
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
    place: str = "ship"
    activity: str = "clean_deck"
    name: str = "Luna"
    gender: str = "girl"
    friend_name: str = "Finn"
    friend_gender: str = "boy"
    trait: str = "brave"
    seed: Optional[int] = None


SETTINGS = {"ship": "the bright pirate ship Sea Comet"}
ACTIVITIES = {"clean_deck": "clean the deck safely"}
NAMES = {
    "girl": ["Luna", "Mara", "Pia", "Nell", "Tessa"],
    "boy": ["Finn", "Kai", "Rafi", "Milo", "Jonah"],
}
TRAITS = ["brave", "curious", "careful", "cheerful", "patient"]

VOYAGES = [
    Voyage(
        "stormy_deck",
        "the rain-wet deck",
        "muddy boot prints",
        "slippery boards and a sharp medicinal smell",
        "the captain's card said to ask before using disinfectant",
        "poured disinfectant straight from the bottle onto the deck",
        "a strong cloud made Luna cough, and the wet boards became even more slippery",
        '"A clean deck must also be a safe deck," Captain Bea called.',
        "opened a window, stepped back, and asked the captain to show them the correct amount and method",
        "the deck shone beneath the lanterns while the crew danced without slipping",
        "Good helpers follow safety instructions and ask an adult before using cleaning products.",
    ),
    Voyage(
        "galley_spill",
        "the little galley",
        "sticky berry juice beside the biscuit chest",
        "disinfectant could harm food and should not be sprayed near the galley table",
        "a covered food cloth lay beside the cleaning bucket",
        "hummed a sea song and sprayed disinfectant beside the biscuits",
        "the biscuits smelled strange, and the cook hurried to move them away",
        '"Do not let a shortcut sail into the food," said Cook Nessa.',
        "covered the food, carried it away, and let the grown-up clean the table properly",
        "fresh biscuits returned to the chest, and the galley smelled like cinnamon again",
        "Care means protecting people and food, not merely making a surface look shiny.",
    ),
    Voyage(
        "parrot_cabin",
        "the parrot cabin",
        "feathers and crumbs under the perches",
        "a noisy spray could frighten the parrot and irritate its lungs",
        "the parrot flapped away whenever the bottle came near",
        "hummed louder and reached for disinfectant while the parrot watched",
        "the bird fluttered into a dark corner, and Luna's smile faded",
        '"First protect the living sailor," Finn whispered.',
        "moved the parrot to a safe place with the keeper and cleaned only as instructed",
        "the parrot returned to its perch and hummed along with the happy crew",
        "A clean place matters, but kindness and safety matter first.",
    ),
    Voyage(
        "moonlit_cabin",
        "the moonlit cabin",
        "salt rings around the treasure-map table",
        "the map could be ruined by a wet cleaner",
        "a waxed cloth and a dry brush rested beside the bottle",
        "grabbed disinfectant because it seemed faster than reading the labels",
        "a droplet landed near the map, and the treasure route began to blur",
        '"Read the label before you follow the tide," Captain Bea warned.',
        "blotted the droplet, kept the bottle away, and used the approved dry tools",
        "the map dried safely, and its silver stars guided everyone to breakfast",
        "The wise choice is not always the fastest one; careful reading prevents harm.",
    ),
]

ASP_RULES = r"""
sailor(X) :- sailor_name(X).
helper(Y) :- helper_name(Y).
has_cleaning_problem(X) :- sailor(X), dirty_deck.
warned(Y) :- helper(Y), gives_warning(Y).
safe_choice(X) :- sailor(X), asks_before_cleaning(X).
happy_ending(X) :- has_cleaning_problem(X), safe_choice(X), cleaned_safely.
moral_value(X) :- happy_ending(X).
"""


def reasonable(params: StoryParams) -> bool:
    return params.place in SETTINGS and params.activity in ACTIVITIES and params.name != params.friend_name


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A cautionary pirate tale about humming and disinfectant.")
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--activity", choices=ACTIVITIES)
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--friend-gender", choices=["girl", "boy"], dest="friend_gender")
    parser.add_argument("--name")
    parser.add_argument("--friend-name", dest="friend_name")
    parser.add_argument("--seed", type=int)
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
    place = args.place or "ship"
    activity = args.activity or "clean_deck"
    gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if gender == "girl" else "girl")
    name = args.name or rng.choice(NAMES[gender])
    friend_name = args.friend_name or rng.choice(NAMES[friend_gender])
    if name == friend_name:
        raise StoryError("The two sailors must have different names.")
    return StoryParams(
        place=place,
        activity=activity,
        name=name,
        gender=gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        trait=rng.choice(TRAITS),
    )


def change(entity: Entity, category: str, key: str, amount: float = 1.0) -> None:
    target = entity.meters if category == "meters" else entity.memes
    target[key] = target.get(key, 0.0) + amount


def tell(params: StoryParams) -> World:
    if not reasonable(params):
        raise StoryError("This pirate world requires a ship and safe deck cleaning.")
    world = World()
    luna = world.add(Entity(params.name, "character", params.gender))
    friend = world.add(Entity(params.friend_name, "character", params.friend_gender))
    bottle = world.add(Entity("cleaning_bottle", "thing", "bottle", "disinfectant bottle"))
    voyage = VOYAGES[(params.seed or 0) % len(VOYAGES)]

    world.say(f"On {SETTINGS[params.place]}, {params.trait} sailor {params.name} hummed a bright tune while exploring {voyage.place}.")
    world.say(f"{params.friend_name} was coiling a rope nearby when they found {voyage.mess}.")
    world.say(f"A bottle of disinfectant stood beside a bucket, but the deck's safety card warned, '{voyage.clue}.'")
    world.say(f"{params.name} thought the quickest plan was to {voyage.wrong_action}.")
    change(luna, "memes", "confidence", 1)
    world.para()
    world.say(f"The plan went wrong: {voyage.consequence}.")
    change(luna, "memes", "worry", 1)
    change(luna, "meters", "risk", 1)
    world.say(f"{params.friend_name} stopped humming and said, {voyage.captain_line}")
    world.say(f'"But I wanted the ship to sparkle," {params.name} replied.')
    world.say(f'"Then let us make it safe before we make it shiny," answered {params.friend_name}.')
    change(friend, "memes", "care", 1)
    change(luna, "memes", "understanding", 1)
    world.para()
    world.say(f"Together, the sailors {voyage.safe_action}.")
    world.say(f"{params.name} read the instructions aloud, and {params.friend_name} stayed close while Captain Bea checked their work.")
    change(luna, "meters", "safety", 2)
    change(friend, "meters", "help", 1)
    change(luna, "memes", "worry", -1)
    change(luna, "memes", "relief", 1)
    world.say(f"At last, {voyage.ending}.")
    world.say(f"The crew cheered, and {params.name} hummed the tune more softly, remembering that {voyage.moral}")
    world.facts.update(
        sailor=luna,
        friend=friend,
        bottle=bottle,
        voyage=voyage,
        safe=True,
        cautionary=True,
        moral_value=True,
        happy_ending=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    v = world.facts["voyage"]
    c = world.facts["sailor"]
    f = world.facts["friend"]
    return [
        f"Write a child-friendly Pirate Tale in {v.place} about {c.id}, {f.id}, humming, and disinfectant.",
        f"Tell a Cautionary story where a sailor makes a risky cleaning choice and a friend gives a spoken warning.",
        f"End with a Happy Ending and a clear Moral Value: {v.moral}",
    ]


def story_qa(world: World) -> list[QAItem]:
    v = world.facts["voyage"]
    c = world.facts["sailor"]
    f = world.facts["friend"]
    return [
        QAItem(f"What problem did {c.id} find?", f"{c.id} found {v.mess} in {v.place}."),
        QAItem(f"Why was {c.id}'s first cleaning idea unsafe?", f"It was unsafe because {v.danger}."),
        QAItem(f"How did {f.id} help?", f"{f.id} gave a spoken safety warning and helped {c.id} {v.safe_action}."),
        QAItem("What happened at the Happy Ending?", v.ending.capitalize() + "."),
        QAItem("What Moral Value did the sailors learn?", v.moral),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is disinfectant?", "Disinfectant is a cleaning product used in the right way to reduce germs on suitable surfaces."),
        QAItem("Why should children ask an adult before using disinfectant?", "Some cleaning products can hurt skin, eyes, lungs, food, animals, or delicate objects, so an adult should read the label and supervise."),
        QAItem("What is a cautionary tale?", "A cautionary tale shows a risky choice and its consequence so listeners can make a safer choice."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("sailor_name", "sailor"),
        asp.fact("helper_name", "helper"),
        asp.fact("dirty_deck"),
        asp.fact("gives_warning", "helper"),
        asp.fact("asks_before_cleaning", "sailor"),
        asp.fact("cleaned_safely", "sailor"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_ending/1. #show moral_value/1."))
    good = bool(asp.atoms(model, "happy_ending")) and bool(asp.atoms(model, "moral_value"))
    print("OK: ASP and Python reasonableness agree." if good else "MISMATCH between ASP and Python reasonableness.")
    return 0 if good else 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(f"  {entity.id}: meters={entity.meters} memes={entity.memes}")
    lines.append(f"  facts: safe={world.facts.get('safe')} cautionary={world.facts.get('cautionary')} happy_ending={world.facts.get('happy_ending')}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


def valid_story_params() -> list[StoryParams]:
    return [
        StoryParams(name="Luna", gender="girl", friend_name="Finn", friend_gender="boy", trait="brave", seed=0),
        StoryParams(name="Mara", gender="girl", friend_name="Kai", friend_gender="boy", trait="careful", seed=1),
        StoryParams(name="Rafi", gender="boy", friend_name="Pia", friend_gender="girl", trait="curious", seed=2),
        StoryParams(name="Nell", gender="girl", friend_name="Jonah", friend_gender="boy", trait="cheerful", seed=3),
    ]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show happy_ending/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        print("ASP model:", asp.one_model(asp_program("#show happy_ending/1. #show moral_value/1.")))
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in valid_story_params()]
    else:
        samples = []
        for i in range(args.n):
            rng = random.Random(base + i)
            params = resolve_params(args, rng)
            params.seed = base + i
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### pirate tale {i + 1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
