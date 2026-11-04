#!/usr/bin/env python3
"""A small animal-story world about a misunderstanding aboard a frigate."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

# Find the shared storyworld modules even when this file is nested several
# directories below storyworlds/worlds.
_here = os.path.abspath(__file__)
for _parent in (_here, *[os.path.dirname(_here[:i]) for i in []]):
    pass
_dir = os.path.dirname(_here)
while _dir != os.path.dirname(_dir):
    if os.path.isfile(os.path.join(_dir, "results.py")):
        if _dir not in sys.path:
            sys.path.insert(0, _dir)
        break
    _dir = os.path.dirname(_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Place:
    id: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        return "\n\n".join(" ".join(paragraph) for paragraph in self.paragraphs if paragraph)


@dataclass
class StoryParams:
    place: str = "foredeck"
    hero_name: str = "Pip"
    helper_name: str = "Ollie"
    hero_animal: str = "parrot"
    helper_animal: str = "otter"
    seed: Optional[int] = None


PLACES = {
    "foredeck": Place("foredeck", "the frigate's foredeck"),
    "aftdeck": Place("aftdeck", "the frigate's aft deck"),
    "chart_deck": Place("chart_deck", "the deck beside the chart room"),
}

ANIMALS = {
    "parrot": {"names": ("Pip", "Pippa", "Rio"), "description": "bright-feathered"},
    "otter": {"names": ("Ollie", "Mina", "Finn"), "description": "whiskered"},
    "gull": {"names": ("Gus", "Skye", "Mara"), "description": "white-winged"},
    "turtle": {"names": ("Tilly", "Shelly", "Tuck"), "description": "steady-shelled"},
    "fox": {"names": ("Fenn", "Fern", "Kit"), "description": "rust-colored"},
}

CURATED = [
    StoryParams(place="foredeck", hero_name="Pip", helper_name="Ollie",
                hero_animal="parrot", helper_animal="otter", seed=11),
    StoryParams(place="aftdeck", hero_name="Skye", helper_name="Tilly",
                hero_animal="gull", helper_animal="turtle", seed=23),
    StoryParams(place="chart_deck", hero_name="Fern", helper_name="Rio",
                hero_animal="fox", helper_animal="parrot", seed=37),
]


def python_valid_combos() -> list[tuple[str, str, str]]:
    return sorted(
        (hero, helper, place)
        for hero in ANIMALS
        for helper in ANIMALS
        if hero != helper
        for place in PLACES
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"Unknown frigate location: {params.place!r}.")
    if params.hero_animal not in ANIMALS or params.helper_animal not in ANIMALS:
        raise StoryError("Choose a listed animal for each friend.")
    if params.hero_animal == params.helper_animal:
        raise StoryError("The two friends must be different kinds of animals.")
    for role, name in (("hero", params.hero_name), ("friend", params.helper_name)):
        if not isinstance(name, str) or not name.strip():
            raise StoryError(f"The {role} needs a name.")
        if len(name) > 24 or not all(ch.isalpha() or ch in " -'" for ch in name):
            raise StoryError(f"The {role}'s name must use ordinary letters, spaces, or hyphens.")
    if params.hero_name.strip().casefold() == params.helper_name.strip().casefold():
        raise StoryError("The two animal friends need different names.")


def _entity_name(name: str) -> str:
    return name.strip()


def build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    place = PLACES[params.place]
    world = World(place=place)

    hero = world.add(Entity("hero", "character", params.hero_animal,
                            _entity_name(params.hero_name), "misreader"))
    helper = world.add(Entity("helper", "character", params.helper_animal,
                              _entity_name(params.helper_name), "careful_friend"))
    captain = world.add(Entity("captain", "character", "owl", "Captain Owl", "captain"))
    case = world.add(Entity("case", "container", "wooden case", "the wooden case"))
    bottle = world.add(Entity("bottle", "cargo", "champagne bottle", "the sealed champagne bottle"))
    cloth = world.add(Entity("cloth", "gear", "sailcloth", "a folded piece of sailcloth"))
    cabinet = world.add(Entity("cabinet", "place", "dry cabinet", "the dry cabinet"))
    ship = world.add(Entity("frigate", "place", "frigate", "the frigate"))

    world.facts.update(
        hero=hero,
        helper=helper,
        captain=captain,
        case=case,
        bottle=bottle,
        cloth=cloth,
        cabinet=cabinet,
        ship=ship,
        place=place,
        misunderstood_word="champion",
        actual_word="champagne",
        destination="the harbor museum",
    )

    hero.memes["curiosity"] = 1.0
    helper.memes["carefulness"] = 1.0
    case.meters["secure"] = 1.0
    bottle.meters["sealed"] = 1.0
    bottle.meters["cargo"] = 1.0
    world.meters["cargo_safe"] = 1.0

    world.say(
        f"On {place.label}, aboard the frigate, "
        f"{hero.label}, a {ANIMALS[hero.type]['description']} {hero.type}, "
        f"helped {helper.label}, a {ANIMALS[helper.type]['description']} {helper.type}, "
        "check a wooden case bound for the harbor museum."
    )
    world.say(
        "Inside it rested a sealed bottle of champagne, wrapped for the museum's display. "
        "No one was meant to open it."
    )
    world.para()

    # Wind and a clattering sail obscure the captain's words. The mistaken
    # interpretation causes the case to be moved toward the scupper.
    captain.memes["explaining"] = 1.0
    hero.memes["uncertain"] = 1.0
    hero.memes["misunderstanding"] = 1.0
    hero.meters["heard_champion"] = 1.0
    case.meters["secure"] = 0.0
    case.meters["near_scupper"] = 1.0
    world.meters["misunderstanding"] = 1.0
    world.meters["risk"] = 1.0
    world.fired.add("misheard_cargo")

    world.say(
        f"Captain Owl called, “Keep the champagne case safe for the museum!” "
        f"But a rattling sail hid the last sound. {hero.label} heard “champion” instead."
    )
    world.say(
        f"“Is a champion hiding in there?” {hero.label} asked. "
        f"{helper.label} peered at the salt-smudged label. “I see a bottle, not a champion. "
        "Let's ask before we move it any farther.”"
    )
    world.say(
        f"The case had already slid close to an open deck scupper. "
        f"{helper.label} tucked the folded sailcloth beneath it, stopping its wooden edge."
    )
    world.para()

    # A direct answer changes what the hero knows and what both friends do.
    captain.memes["clarity"] = 1.0
    hero.memes["understanding"] = 1.0
    hero.memes["worry"] = 0.0
    hero.memes["relief"] = 1.0
    hero.meters["understands_label"] = 1.0
    helper.meters["blocks_scupper"] = 1.0
    case.meters["padded"] = 1.0
    case.meters["near_scupper"] = 0.0
    case.meters["secure"] = 1.0
    case.meters["stored"] = 1.0
    bottle.meters["safe"] = 1.0
    cabinet.meters["holds_case"] = 1.0
    world.meters["risk"] = 0.0
    world.meters["cargo_safe"] = 1.0
    world.meters["misunderstanding"] = 0.0
    world.meters["resolved"] = 1.0
    world.fired.add("word_clarified")
    world.fired.add("case_secured")

    world.say(
        "“Champagne is the name of the drink in the sealed bottle,” Captain Owl explained. "
        "“The museum asked us to carry it, not to open it.”"
    )
    world.say(
        f"“Oh! I heard ‘champion,’” {hero.label} said. “Now I know what the label means. "
        "I'll help keep the case dry.” Together, the friends lifted it onto the padded shelf "
        "inside the dry cabinet."
    )
    world.para()
    world.say(
        "When the frigate reached the harbor, the case was still snug and dry. "
        "Through the museum window, the friends saw the sealed bottle resting on its shelf, "
        "with a bright card beside it that read CHAMPAGNE."
    )

    world.facts.update(
        misunderstood=True,
        clarified=True,
        secured=True,
        safe=True,
        method="They stopped the case with sailcloth, checked the label with Captain Owl, "
               "and stowed the sealed bottle in a dry cabinet.",
        consequence="The sealed bottle reached the harbor museum safely.",
        ending="The sealed bottle rested on the museum shelf beside its bright CHAMPAGNE card.",
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a gentle animal story about a misunderstanding aboard a frigate.",
        f"Tell how {f['hero'].label} and {f['helper'].label} learn what the champagne label means.",
        "Make the animals' conversation change what they know and do, then end with a clear image of the safe cargo.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What did the animal misunderstand?",
            answer=(
                f"{f['hero'].label} heard “champion” when Captain Owl said “champagne,” "
                "so the animal thought there might be a champion hidden in the case."
            ),
        ),
        QAItem(
            question="How did the friends keep the bottle safe?",
            answer=f"{f['method']} {f['consequence']}",
        ),
        QAItem(
            question="What showed that the misunderstanding was resolved?",
            answer=f"The ending showed the change clearly: {f['ending']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a frigate?",
            answer="A frigate is a kind of ship. In this story, the animals travel aboard one.",
        ),
        QAItem(
            question="Why did the animals leave the champagne bottle sealed?",
            answer="The bottle was cargo for a museum display, so the animals kept it sealed and carried it safely instead of opening it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.extend(["", "== (2) Story questions =="])
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.extend(["", "== (3) World-knowledge questions =="])
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        state = []
        if meters:
            state.append(f"meters={meters}")
        if memes:
            state.append(f"memes={memes}")
        lines.append(f"  {entity.id:10} ({entity.type}) {' '.join(state)}")
    lines.append(f"  world      meters={dict(world.meters)}")
    lines.append(f"  events     {', '.join(sorted(world.fired))}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate an animal story about a champagne-label misunderstanding aboard a frigate."
    )
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--hero-animal", choices=sorted(ANIMALS))
    parser.add_argument("--helper-animal", choices=sorted(ANIMALS))
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
    hero_animal = args.hero_animal or rng.choice(sorted(ANIMALS))
    remaining = [animal for animal in sorted(ANIMALS) if animal != hero_animal]
    helper_animal = args.helper_animal or rng.choice(remaining)
    hero_name = args.hero or rng.choice(ANIMALS[hero_animal]["names"])
    helper_choices = [name for name in ANIMALS[helper_animal]["names"] if name.casefold() != hero_name.casefold()]
    helper_name = args.helper or rng.choice(helper_choices)
    return StoryParams(
        place=args.place or rng.choice(sorted(PLACES)),
        hero_name=hero_name,
        helper_name=helper_name,
        hero_animal=hero_animal,
        helper_animal=helper_animal,
    )


ASP_RULES = r"""
eligible(H,F,P) :- animal_species(H), animal_species(F), place(P), H != F.
cargo_safe :- cargo(champagne_case), case_padded, label_clarified, case_stored.
resolution(safe_delivery) :- cargo_safe.
#show eligible/3.
#show cargo_safe/0.
#show resolution/1.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for animal in sorted(ANIMALS):
        lines.append(asp.fact("animal_species", animal))
    for place in sorted(PLACES):
        lines.append(asp.fact("place", place))
    lines.extend(
        [
            asp.fact("cargo", "champagne_case"),
            asp.fact("case_padded"),
            asp.fact("label_clarified"),
            asp.fact("case_stored"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: Optional[str] = None) -> str:
    directives = show or ""
    return f"{asp_facts()}\n{ASP_RULES}\n{directives}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(tuple(row) for row in asp.atoms(model, "eligible")))


def asp_verify() -> int:
    try:
        import asp

        model = asp.one_model(asp_program())
        found = sorted(set(tuple(row) for row in asp.atoms(model, "eligible")))
        expected = python_valid_combos()
        if found != expected:
            print("ASP/Python registry parity failed.")
            print(f"Python: {expected}")
            print(f"ASP:    {found}")
            return 1
        if not asp.atoms(model, "cargo_safe") or not asp.atoms(model, "resolution"):
            print("ASP did not derive the safe-delivery outcome.")
            return 1
        sample = generate(StoryParams())
        if not sample.story.strip() or "champagne" not in sample.story.casefold():
            print("Story-generation smoke test failed.")
            return 1
        if not sample.story_qa or not sample.world_qa:
            print("Question-and-answer smoke test failed.")
            return 1
    except Exception as exc:
        print(f"Verification failed: {exc}")
        return 1
    print("OK: ASP/Python parity and story-generation checks passed.")
    return 0


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
    if args.n < 1 and not args.all and not args.verify and not args.asp and not args.show_asp:
        raise SystemExit("-n must be at least 1.")
    if args.show_asp:
        print(asp_program("#show eligible/3.\n#show cargo_safe/0.\n#show resolution/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            print(asp_valid_combos())
        except Exception as exc:
            raise SystemExit(f"ASP query failed: {exc}") from exc
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 50):
            seed = base_seed + attempt
            attempt += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
