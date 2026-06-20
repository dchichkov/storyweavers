#!/usr/bin/env python3
"""Pirate-flavored zoo storyworld about a sledge on a riverbank.

Seed:
    Words: sledge, riverbank
    Setting: zoo
    Features: Misunderstanding, Curiosity
    Style: Pirate Tale

Internal source tale:
    A child visits the riverbank side of a zoo and pretends to captain a pirate
    ship. A keeper pulls a low sledge loaded with animal supplies. Because one
    clue on the load looks pirate-ish, the child misunderstands the cargo as
    treasure, a gangplank, or sail gear. Curiosity wins over grabbing. The
    child asks what the load really is, walks with the keeper to the exhibit,
    and sees the supplies help the animals. The ending image proves that the
    real scene is kinder and more useful than the guessed pirate story.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    role: str = ""
    location: str = ""
    attrs: dict[str, str] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass(frozen=True)
class Exhibit:
    key: str
    name: str
    place_phrase: str
    keeper_name: str
    animal_label: str
    bank_detail: str
    need_key: str
    need_phrase: str
    exhibit_spot: str
    ending_image: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class CargoCase:
    key: str
    clue_phrase: str
    pirate_guess: str
    real_label: str
    need_key: str
    risk_line: str
    reveal_line: str
    use_line: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class Event:
    key: str
    subject: str
    detail: str
    consequence: str = ""


@dataclass
class StoryParams:
    exhibit: str
    cargo: str
    hero: str
    gender: str
    helper: str
    trait: str
    seed: int | None = None


@dataclass(frozen=True)
class Rule:
    name: str
    apply: Callable[["ZooRiverbankWorld"], list[str]]


class ZooRiverbankWorld:
    def __init__(self, params: StoryParams, exhibit: Exhibit, cargo: CargoCase) -> None:
        self.params = params
        self.exhibit = exhibit
        self.cargo = cargo
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.history: list[Event] = []
        self.fired: set[str] = set()
        self.fired_names: list[str] = []
        self.facts: dict[str, object] = {
            "style": "pirate tale",
            "setting": "zoo",
            "seed_words": ("sledge", "riverbank"),
            "guessed_cargo": cargo.pirate_guess,
            "real_cargo": cargo.real_label,
            "asked_keeper": False,
            "misunderstanding_cleared": False,
            "walked_with_keeper": False,
            "need_met": False,
            "risk_if_grabbed": cargo.risk_line,
            "lesson": "Curiosity helps when it asks before it grabs.",
            "ending_image": "",
        }

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, sentence: str) -> None:
        text = sentence.strip()
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(self, key: str, subject: str, detail: str, consequence: str = "") -> None:
        self.history.append(Event(key, subject, detail, consequence))

    def render(self) -> str:
        return "\n\n".join(" ".join(chunk) for chunk in self.paragraphs if chunk)

    def trace(self) -> str:
        lines = [
            f"params: {self.params}",
            f"fired_rules: {', '.join(self.fired_names) if self.fired_names else 'none'}",
        ]
        for name, value in sorted(self.facts.items()):
            lines.append(f"fact[{name}]={value}")
        for entity in self.entities.values():
            lines.append(f"{entity.id}: {entity.kind}/{entity.type} {entity.label}")
            if entity.role:
                lines.append(f"  role={entity.role}")
            if entity.location:
                lines.append(f"  location={entity.location}")
            if entity.attrs:
                lines.append(f"  attrs={entity.attrs}")
            meters = {k: v for k, v in entity.meters.items() if v}
            memes = {k: v for k, v in entity.memes.items() if v}
            if meters:
                lines.append(f"  meters={meters}")
            if memes:
                lines.append(f"  memes={memes}")
        if self.history:
            lines.append("history:")
            for event in self.history:
                tail = f" -> {event.consequence}" if event.consequence else ""
                lines.append(f"  {event.key}: {event.subject} | {event.detail}{tail}")
        return "\n".join(lines)


EXHIBITS: dict[str, Exhibit] = {
    "otter_inlet": Exhibit(
        key="otter_inlet",
        name="Otter Inlet",
        place_phrase="Harbor Zoo's riverbank path beside Otter Inlet",
        keeper_name="Keeper Rosa",
        animal_label="the otters",
        bank_detail="flat stones, reeds, and a rope float glittering by the water",
        need_key="fish_breakfast",
        need_phrase="breakfast fish and the chart for the morning feeding",
        exhibit_spot="the low feeding rail where the otters waited with whiskers twitching",
        ending_image=(
            "Two otters popped up beside the rail, and silver drops flashed over the riverbank stones as breakfast splashed into the water."
        ),
        tags=("riverbank", "feeding"),
    ),
    "beaver_bend": Exhibit(
        key="beaver_bend",
        name="Beaver Bend",
        place_phrase="Harbor Zoo's riverbank boardwalk beside Beaver Bend",
        keeper_name="Keeper Amos",
        animal_label="the beavers",
        bank_detail="muddy reeds, chewed willow posts, and a lodge tucked against the bank",
        need_key="bank_patch",
        need_phrase="fresh willow branches and a short board to patch the soft bank edge",
        exhibit_spot="the muddy edge where the beavers had worn the old bank wall loose",
        ending_image=(
            "A beaver tugged a fresh willow switch toward its lodge, and the patched riverbank edge held firm under the keeper's boots."
        ),
        tags=("riverbank", "repair"),
    ),
    "pelican_pier": Exhibit(
        key="pelican_pier",
        name="Pelican Pier",
        place_phrase="Harbor Zoo's riverbank dock beside Pelican Pier",
        keeper_name="Keeper June",
        animal_label="the pelicans",
        bank_detail="shell-bright sand and a low dock stretching over the water",
        need_key="feeding_tools",
        need_phrase="feeding scoops and bowls for the morning line-up",
        exhibit_spot="the dock where the pelicans were already shuffling into a patient row",
        ending_image=(
            "One pelican caught a glittering fish from the scoop and flapped once on the dock while the others leaned forward in a neat white row."
        ),
        tags=("riverbank", "dock"),
    ),
    "capybara_lagoon": Exhibit(
        key="capybara_lagoon",
        name="Capybara Lagoon",
        place_phrase="Harbor Zoo's riverbank curve near Capybara Lagoon",
        keeper_name="Keeper Lani",
        animal_label="the capybaras",
        bank_detail="warm sand, shallow water, and reeds bowing in the breeze",
        need_key="warm_blanket",
        need_phrase="a dry striped blanket after their bath",
        exhibit_spot="the sandy curve where the capybaras liked to stand while water dripped from their fur",
        ending_image=(
            "A capybara leaned into the striped blanket beside the water, and the damp riverbank reeds nodded softly behind it."
        ),
        tags=("riverbank", "warmth"),
    ),
}


CARGO_CASES: dict[str, CargoCase] = {
    "map_tube": CargoCase(
        key="map_tube",
        clue_phrase="a blue tube tied with red cord above a covered pail",
        pirate_guess="a rolled treasure map for pirate gold",
        real_label="a feeding chart and a pail of silver fish",
        need_key="fish_breakfast",
        risk_line="the breakfast fish could spill, and the otters would wait longer at the rail",
        reveal_line=(
            '"Not treasure, captain," {keeper} said, sliding the chart from the tube. '
            '"This tells me which fish belong to {animal} this morning."'
        ),
        use_line=(
            "{keeper} checked the chart, tipped the bright fish from the pail, and {animal} bobbed at the rail for breakfast."
        ),
        tags=("misunderstanding", "feeding"),
    ),
    "plank_bundle": CargoCase(
        key="plank_bundle",
        clue_phrase="a bundle of willow branches with one short plank lashed across the top",
        pirate_guess="a gangplank for boarding another ship",
        real_label="fresh willow branches and a patch board for the soft bank edge",
        need_key="bank_patch",
        risk_line="the patch board could slide off, and the loose bank would stay wobbly for the keepers and beavers",
        reveal_line=(
            '"This is no boarding plank," {keeper} said with a grin. '
            '"It is a patch board, and these branches are for {animal} after we steady the edge."'
        ),
        use_line=(
            "{keeper} wedged the short board into the soft edge, stacked the willow branches nearby, and {animal} went right to work with bright teeth."
        ),
        tags=("misunderstanding", "repair"),
    ),
    "hook_crate": CargoCase(
        key="hook_crate",
        clue_phrase="a crate full of long scoop handles that clinked like metal hooks",
        pirate_guess="a chest of boarding hooks and cutlasses",
        real_label="feeding scoops and bowls for the pelicans",
        need_key="feeding_tools",
        risk_line="the scoops could clatter into the water, and the feeding line would be delayed",
        reveal_line=(
            '"Hooks? Only soup-sized ones," {keeper} said, lifting a scoop from the crate. '
            '"These bowls and scoops help me feed {animal} without splashing half the fish away."'
        ),
        use_line=(
            "{keeper} filled a scoop, reached over the dock, and {animal} stepped forward in a tidy line for breakfast."
        ),
        tags=("misunderstanding", "dock"),
    ),
    "striped_roll": CargoCase(
        key="striped_roll",
        clue_phrase="a striped roll tied tight with rope like a folded sail",
        pirate_guess="a little sail for a secret riverboat",
        real_label="a warm striped blanket for drying capybaras",
        need_key="warm_blanket",
        risk_line="the blanket could drag in the wet sand, and the capybaras would stay chilly after their bath",
        reveal_line=(
            '"A sail would be hard to use on dry land," {keeper} said softly. '
            '"This blanket helps {animal} warm up after the water drips from their fur."'
        ),
        use_line=(
            "{keeper} unrolled the blanket on the warm sand, and {animal} leaned into the dry stripes one by one."
        ),
        tags=("misunderstanding", "warmth"),
    ),
}


HERO_NAMES = {
    "girl": ["Mira", "Tansy", "Nell", "Poppy"],
    "boy": ["Finn", "Otis", "Milo", "Jasper"],
}
HELPERS = ["Pip", "Rae", "Tilda", "Bram"]
TRAITS = ["curious", "bright-eyed", "careful", "eager"]


def article(phrase: str) -> str:
    return "an" if phrase[:1].lower() in {"a", "e", "i", "o", "u"} else "a"


def valid_pairs() -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for exhibit_key, exhibit in EXHIBITS.items():
        for cargo_key, cargo in CARGO_CASES.items():
            if exhibit.need_key == cargo.need_key:
                pairs.append((exhibit_key, cargo_key))
    return sorted(pairs)


def invalid_reason(exhibit_key: str, cargo_key: str) -> str:
    exhibit = EXHIBITS.get(exhibit_key)
    cargo = CARGO_CASES.get(cargo_key)
    if exhibit is None:
        return f"Unknown exhibit: {exhibit_key}."
    if cargo is None:
        return f"Unknown cargo: {cargo_key}."
    if exhibit.need_key != cargo.need_key:
        return (
            f"{cargo.real_label.capitalize()} would not honestly solve the need at {exhibit.name}. "
            f"{exhibit.name} needs {exhibit.need_phrase}."
        )
    return "The requested zoo riverbank story is reasonable."


def _r_question_opens_truth(world: ZooRiverbankWorld) -> list[str]:
    if not world.facts["asked_keeper"] or world.facts["misunderstanding_cleared"]:
        return []
    hero = world.get("hero")
    helper = world.get("helper")
    keeper = world.get("keeper")
    hero.memes["certainty"] = 0.0
    hero.memes["curiosity"] += 0.5
    helper.memes["trust"] += 0.5
    keeper.memes["warmth"] += 0.5
    world.facts["misunderstanding_cleared"] = True
    return []


def _r_delivery_meets_need(world: ZooRiverbankWorld) -> list[str]:
    if not world.facts["walked_with_keeper"] or world.facts["need_met"]:
        return []
    exhibit = world.get("exhibit")
    sledge = world.get("sledge")
    cargo = world.get("cargo")
    animals = world.get("animals")
    if exhibit.attrs["need_key"] != cargo.attrs["need_key"]:
        return []
    exhibit.meters["need"] = 0.0
    animals.meters["comfort"] += 1.0
    sledge.meters["delivered"] += 1.0
    cargo.meters["used"] += 1.0
    world.facts["need_met"] = True
    world.facts["ending_image"] = world.exhibit.ending_image
    return []


CAUSAL_RULES = [
    Rule("question_opens_truth", _r_question_opens_truth),
    Rule("delivery_meets_need", _r_delivery_meets_need),
]


def propagate(world: ZooRiverbankWorld) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            if rule.name in world.fired:
                continue
            updates = rule.apply(world)
            if rule.name == "question_opens_truth" and world.facts["misunderstanding_cleared"]:
                world.fired.add(rule.name)
                world.fired_names.append(rule.name)
                changed = True
            elif rule.name == "delivery_meets_need" and world.facts["need_met"]:
                world.fired.add(rule.name)
                world.fired_names.append(rule.name)
                changed = True
            if updates:
                changed = True


def _params_from_pair(args: argparse.Namespace, pair: tuple[str, str], index: int) -> StoryParams:
    gender = args.gender or sorted(HERO_NAMES)[index % len(HERO_NAMES)]
    names = HERO_NAMES[gender]
    hero = args.hero or names[index % len(names)]
    helper_pool = [name for name in HELPERS if name != hero]
    helper = args.helper or helper_pool[index % len(helper_pool)]
    trait = args.trait or TRAITS[index % len(TRAITS)]
    return StoryParams(
        exhibit=pair[0],
        cargo=pair[1],
        hero=hero,
        gender=gender,
        helper=helper,
        trait=trait,
        seed=args.seed,
    )


def introduce(world: ZooRiverbankWorld, hero: Entity, helper: Entity, keeper: Entity) -> None:
    exhibit = world.exhibit
    hero.memes["curiosity"] += 1.0
    hero.memes["play"] += 1.0
    helper.memes["friendship"] += 1.0
    keeper.memes["care"] += 1.0
    hero_desc = f"{article(world.params.trait)} {world.params.trait} child"
    world.say(
        f"At the zoo, {exhibit.place_phrase} felt so windy and bright that {hero.label}, {hero_desc}, called the path a pirate deck."
    )
    world.say(
        f"{helper.label} marched beside {hero.pronoun('object')} as first mate while {keeper.label} worked farther ahead near {exhibit.bank_detail}."
    )
    world.say(
        f"{hero.label} promised to keep captain eyes open for anything mysterious along the riverbank."
    )
    world.record("premise", hero.label, "pretends the zoo path is a pirate deck")


def sight_sledge(world: ZooRiverbankWorld, hero: Entity, helper: Entity, sledge: Entity, cargo: Entity) -> None:
    exhibit = world.exhibit
    sledge.meters["loaded"] += 1.0
    cargo.meters["packed"] += 1.0
    world.para()
    world.say(
        f"Then {exhibit.keeper_name} came around the bend, pulling a low sledge that hissed softly over the path."
    )
    world.say(
        f"On the sledge sat {world.cargo.clue_phrase}, and {hero.label} gasped because it looked exactly like {world.cargo.pirate_guess}."
    )
    world.say(
        f'"Treasure cargo," {hero.pronoun("subject")} whispered to {helper.label}. "A captain can tell."'
    )
    hero.memes["certainty"] += 1.0
    helper.memes["doubt"] += 0.5
    world.record("misread", hero.label, world.cargo.pirate_guess, world.cargo.real_label)


def imagine_wrong_move(world: ZooRiverbankWorld, hero: Entity, helper: Entity) -> None:
    hero.meters["reach"] += 1.0
    helper.memes["caution"] += 1.0
    world.say(
        f"{hero.label} almost reached for the load, but {helper.label} noticed how carefully the keeper held the rope."
    )
    world.say(
        f"If {hero.pronoun('subject')} grabbed it, {world.facts['risk_if_grabbed']}."
    )
    world.say(
        f"The thought made the pirate game feel smaller than the real work on the riverbank."
    )
    world.record("risk", helper.label, str(world.facts["risk_if_grabbed"]))


def ask_with_curiosity(world: ZooRiverbankWorld, hero: Entity, keeper: Entity) -> None:
    world.say(
        f"So {hero.label} chose curiosity over swagger and called, \"Captain's question, please. What is really on that sledge?\""
    )
    world.facts["asked_keeper"] = True
    hero.memes["curiosity"] += 1.0
    propagate(world)
    world.record("question", hero.label, "asks before grabbing")


def reveal_truth(world: ZooRiverbankWorld, hero: Entity, helper: Entity, keeper: Entity) -> None:
    world.say(world.cargo.reveal_line.format(keeper=keeper.label, hero=hero.label, animal=world.exhibit.animal_label))
    world.say(
        f"{helper.label} grinned, and {hero.label} felt {hero.pronoun('possessive')} pirate guess fold up as neatly as a paper hat."
    )
    hero.memes["wonder"] += 1.0
    hero.memes["embarrassment"] += 0.5
    keeper.memes["trust"] += 0.5
    world.record("reveal", keeper.label, world.cargo.real_label, "misunderstanding cleared")


def walk_and_help(world: ZooRiverbankWorld, hero: Entity, helper: Entity, keeper: Entity, sledge: Entity) -> None:
    exhibit = world.exhibit
    world.para()
    world.say(
        f"{keeper.label} invited both children to walk beside the sledge to {exhibit.exhibit_spot}."
    )
    world.facts["walked_with_keeper"] = True
    sledge.meters["pulled"] += 1.0
    hero.meters["walked"] += 1.0
    helper.meters["walked"] += 1.0
    propagate(world)
    world.say(world.cargo.use_line.format(keeper=keeper.label, animal=exhibit.animal_label))
    world.say(
        f"{hero.label} saw that the real adventure was helping {exhibit.animal_label}, not inventing treasure where there was only kind work to do."
    )
    world.record("delivery", keeper.label, exhibit.need_phrase, "animals helped")


def close_story(world: ZooRiverbankWorld, hero: Entity, helper: Entity) -> None:
    if not world.facts["need_met"]:
        raise StoryError("The sledge cargo never reached a useful ending.")
    world.say(
        f'"Best pirate captains ask first," {hero.label} said, and {helper.label} saluted because that sounded like a rule worth keeping.'
    )
    world.say(str(world.facts["ending_image"]))
    world.record("ending", hero.label, str(world.facts["ending_image"]), str(world.facts["lesson"]))


def tell(params: StoryParams) -> ZooRiverbankWorld:
    exhibit = EXHIBITS[params.exhibit]
    cargo = CARGO_CASES[params.cargo]
    world = ZooRiverbankWorld(params, exhibit, cargo)
    hero = world.add(Entity("hero", "character", params.gender, params.hero, role="captain", location=exhibit.key))
    helper = world.add(Entity("helper", "character", "child", params.helper, role="first_mate", location=exhibit.key))
    keeper = world.add(Entity("keeper", "character", "adult", exhibit.keeper_name, role="keeper", location=exhibit.key))
    world.add(Entity("sledge", "physical", "sledge", "sledge", location=exhibit.key))
    world.add(
        Entity(
            "cargo",
            "physical",
            "cargo",
            cargo.real_label,
            location=exhibit.key,
            attrs={"need_key": cargo.need_key},
        )
    )
    world.add(
        Entity(
            "exhibit",
            "place",
            "zoo_exhibit",
            exhibit.name,
            location=exhibit.key,
            attrs={"need_key": exhibit.need_key},
        )
    )
    world.add(Entity("animals", "creature", "animals", exhibit.animal_label, location=exhibit.key))
    world.get("exhibit").meters["need"] = 1.0
    world.get("animals").meters["waiting"] = 1.0
    introduce(world, hero, helper, keeper)
    sight_sledge(world, hero, helper, world.get("sledge"), world.get("cargo"))
    imagine_wrong_move(world, hero, helper)
    ask_with_curiosity(world, hero, keeper)
    reveal_truth(world, hero, helper, keeper)
    walk_and_help(world, hero, helper, keeper, world.get("sledge"))
    close_story(world, hero, helper)
    return world


def generation_prompts(world: ZooRiverbankWorld) -> list[str]:
    hero = world.get("hero")
    return [
        'Write a Pirate Tale set at a zoo that includes the words "sledge" and "riverbank."',
        f"Write a story where {hero.label} mistakes animal supplies for {world.cargo.pirate_guess}.",
        "Write a story where curiosity clears a misunderstanding and the ending image proves what changed.",
    ]


def story_qa(world: ZooRiverbankWorld) -> list[tuple[str, str]]:
    hero = world.get("hero")
    helper = world.get("helper")
    keeper = world.get("keeper")
    return [
        (
            f"Why did {hero.label} think the keeper was pulling pirate cargo?",
            f"{hero.label} thought that because the load looked like {world.cargo.pirate_guess}. "
            f"The clue was {world.cargo.clue_phrase}, so the pirate game bent the real scene into the wrong idea.",
        ),
        (
            f"What did {hero.label} do instead of grabbing the load?",
            f"{hero.label} stopped and asked {keeper.label} what was really on the sledge. "
            f"That choice let curiosity clear the misunderstanding before the zoo work was delayed.",
        ),
        (
            f"How did the real cargo help {world.exhibit.animal_label}?",
            f"The load was really {world.cargo.real_label}. "
            f"{world.cargo.use_line.format(keeper=keeper.label, animal=world.exhibit.animal_label)}",
        ),
        (
            f"Why was {helper.label}'s warning important?",
            f"{helper.label} helped {hero.label} notice that the load was important, not just exciting. "
            f"If the children had grabbed it, {world.facts['risk_if_grabbed']}.",
        ),
    ]


KNOWLEDGE = {
    "riverbank": (
        "What is a riverbank?",
        "A riverbank is the land along the edge of a river or other water. It can be stony, muddy, sandy, or covered with reeds.",
    ),
    "misunderstanding": (
        "What is a misunderstanding?",
        "A misunderstanding happens when someone explains a situation the wrong way at first. Asking questions and checking clues can replace the wrong idea with the true one.",
    ),
    "curiosity": (
        "Why can curiosity be helpful?",
        "Curiosity helps people ask careful questions before they act. That can protect other people, animals, or important work from a rushed mistake.",
    ),
    "feeding": (
        "Why might a zoo keeper use a sledge for feeding supplies?",
        "A sledge can carry supplies low and steadily along a path. That makes it easier to move fish, bowls, or charts without dropping them.",
    ),
    "repair": (
        "Why would a zoo keeper patch a riverbank edge?",
        "A soft riverbank edge can wobble or wear away. Patching it keeps the area safer for both animals and keepers.",
    ),
    "dock": (
        "Why do pelicans need careful feeding tools?",
        "Long scoops and bowls help a keeper place food where large birds can reach it cleanly. Good tools also keep fish from splashing away too fast.",
    ),
    "warmth": (
        "Why might an animal need a blanket after water time?",
        "Wet fur can stay chilly even on a mild day. A dry blanket helps an animal warm up comfortably after a bath or swim.",
    ),
}


def world_knowledge_qa(world: ZooRiverbankWorld) -> list[tuple[str, str]]:
    tags = {"curiosity", "misunderstanding"} | set(world.exhibit.tags) | set(world.cargo.tags)
    chosen: list[tuple[str, str]] = []
    for tag in sorted(tags):
        if tag in KNOWLEDGE:
            chosen.append(KNOWLEDGE[tag])
    return chosen[:4]


def generate(params: StoryParams) -> StorySample:
    if (params.exhibit, params.cargo) not in valid_pairs():
        raise StoryError(invalid_reason(params.exhibit, params.cargo))
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


ASP_RULES = r"""
valid(Exhibit,Cargo) :- exhibit(Exhibit), cargo(Cargo), exhibit_need(Exhibit,Need), cargo_need(Cargo,Need).
ok :- chosen_exhibit(Exhibit), chosen_cargo(Cargo), valid(Exhibit,Cargo).
#show valid/2.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from storyworlds import asp

    lines: list[str] = []
    for exhibit_key, exhibit in EXHIBITS.items():
        lines.append(asp.fact("exhibit", exhibit_key))
        lines.append(asp.fact("exhibit_need", exhibit_key, exhibit.need_key))
    for cargo_key, cargo in CARGO_CASES.items():
        lines.append(asp.fact("cargo", cargo_key))
        lines.append(asp.fact("cargo_need", cargo_key, cargo.need_key))
    if params is not None:
        lines.append(asp.fact("chosen_exhibit", params.exhibit))
        lines.append(asp.fact("chosen_cargo", params.cargo))
    return "\n".join(lines) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_pairs() -> list[tuple[str, str]]:
    from storyworlds import asp

    model = asp.one_model(asp_program())
    return sorted(asp.atoms(model, "valid"))


def asp_accepts(params: StoryParams) -> bool:
    from storyworlds import asp

    model = asp.one_model(asp_program(params))
    return bool(asp.atoms(model, "ok"))


def verify() -> str:
    python_pairs = set(valid_pairs())
    asp_pairs = set(asp_valid_pairs())
    if python_pairs != asp_pairs:
        raise StoryError(
            f"ASP/Python mismatch. only_python={sorted(python_pairs - asp_pairs)} "
            f"only_asp={sorted(asp_pairs - python_pairs)}"
        )
    for index, pair in enumerate(sorted(python_pairs), 1):
        params = StoryParams(
            exhibit=pair[0],
            cargo=pair[1],
            hero=HERO_NAMES["girl"][(index - 1) % len(HERO_NAMES["girl"])],
            gender="girl",
            helper=HELPERS[(index - 1) % len(HELPERS)],
            trait=TRAITS[(index - 1) % len(TRAITS)],
            seed=index,
        )
        if not asp_accepts(params):
            raise StoryError(f"ASP rejected valid params: {params}")
        sample = generate(params)
        lowered = sample.story.lower()
        if "sledge" not in lowered or "riverbank" not in lowered or "zoo" not in lowered:
            raise StoryError(f"Story omitted a required seed term or setting word for params={params}")
        if not sample.prompts or len(sample.story_qa) < 3 or len(sample.world_qa) < 3:
            raise StoryError(f"Prompts or QA are too thin for params={params}")
        if not sample.world.facts["asked_keeper"]:
            raise StoryError(f"Curiosity never produced a question for params={params}")
        if not sample.world.facts["misunderstanding_cleared"]:
            raise StoryError(f"Misunderstanding never cleared for params={params}")
        if not sample.world.facts["need_met"]:
            raise StoryError(f"Animal need was never met for params={params}")
        if not str(sample.world.facts["ending_image"]).strip():
            raise StoryError(f"Story lacks an ending proof image for params={params}")
        if "{" in sample.story or "}" in sample.story:
            raise StoryError(f"Story leaked template braces for params={params}")
    return f"OK: ASP parity holds and exercised {len(python_pairs)} zoo riverbank pirate stories."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate pirate-flavored zoo riverbank stories about a sledge and a misunderstanding."
    )
    parser.add_argument("--exhibit", choices=sorted(EXHIBITS))
    parser.add_argument("--cargo", choices=sorted(CARGO_CASES))
    parser.add_argument("--hero", default=None)
    parser.add_argument("--gender", choices=sorted(HERO_NAMES), default=None)
    parser.add_argument("--helper", choices=HELPERS, default=None)
    parser.add_argument("--trait", choices=TRAITS, default=None)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random | None = None) -> StoryParams:
    rng = rng or random.Random(args.seed if args.seed is not None else 1)
    pairs = valid_pairs()
    explicit = args.exhibit is not None or args.cargo is not None
    if explicit:
        pairs = [
            pair
            for pair in pairs
            if (args.exhibit is None or pair[0] == args.exhibit)
            and (args.cargo is None or pair[1] == args.cargo)
        ]
        if not pairs:
            if args.exhibit and args.cargo:
                raise StoryError(invalid_reason(args.exhibit, args.cargo))
            raise StoryError("No reasonable story matches the chosen exhibit/cargo filters.")
    pair = rng.choice(pairs)
    return _params_from_pair(args, pair, getattr(args, "_index", 0))


def emit(sample: StorySample, args: argparse.Namespace, header: str | None = None) -> None:
    if args.json:
        print(sample.to_json())
        return
    if header:
        print(header)
    print(sample.story)
    if args.trace and sample.world is not None:
        print("\nTrace:")
        print(sample.world.trace())
    if args.qa:
        print("\n== Story Prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== Story QA ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== World QA ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def _emit_asp_listing(args: argparse.Namespace) -> None:
    pairs = asp_valid_pairs()
    if args.exhibit or args.cargo:
        pairs = [
            pair
            for pair in pairs
            if (args.exhibit is None or pair[0] == args.exhibit)
            and (args.cargo is None or pair[1] == args.cargo)
        ]
    for exhibit_key, cargo_key in pairs:
        print(f"{exhibit_key}\t{cargo_key}")


def _samples_from_args(args: argparse.Namespace) -> list[StorySample]:
    if args.all:
        pairs = valid_pairs()
        return [generate(_params_from_pair(args, pair, index)) for index, pair in enumerate(pairs)]
    count = max(1, args.n)
    samples: list[StorySample] = []
    for index in range(count):
        setattr(args, "_index", index)
        seed = (args.seed or 1) + index
        local_rng = random.Random(seed)
        params = resolve_params(args, local_rng)
        params.seed = seed
        samples.append(generate(params))
    return samples


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.verify:
            print(verify())
            return 0
        if args.asp:
            _emit_asp_listing(args)
            return 0
        samples = _samples_from_args(args)
        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0
        for index, sample in enumerate(samples, 1):
            header = None if len(samples) == 1 else f"### sample {index} seed={sample.params.seed}"
            emit(sample, args, header)
            if index != len(samples):
                print("\n" + "=" * 72 + "\n")
        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
