#!/usr/bin/env python3
"""A small storyworld about a zoo riverbank, a sledge, and pirate-flavored curiosity.

Seed:
    Words: sledge, riverbank
    Setting: zoo
    Features: Misunderstanding, Curiosity
    Style: Pirate Tale

Internal source tale:
    A child walking through the riverbank side of a zoo pretends to be a pirate
    captain. When a keeper pulls a low sledge past the reeds, the child
    misunderstands the cargo as pirate treasure or a boarding tool. Curiosity
    wins over grabbing or boasting, so the child asks what the load really is,
    walks with the keeper to the exhibit, and sees the sledge helping the
    animals. The ending image proves that the real story is kinder than the
    guessed pirate one.
"""

from __future__ import annotations

import argparse
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
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
    walk_line: str
    ending_image: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class CargoCase:
    key: str
    clue_phrase: str
    guess_phrase: str
    real_label: str
    need_key: str
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
    seed: int | None = None


@dataclass(frozen=True)
class Rule:
    name: str
    apply: Callable[["ZooWorld"], list[str]]


class ZooWorld:
    def __init__(self, params: StoryParams, exhibit: Exhibit, cargo: CargoCase) -> None:
        self.params = params
        self.exhibit = exhibit
        self.cargo = cargo
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.history: list[Event] = []
        self.fired: set[tuple[object, ...]] = set()
        self.fired_names: list[str] = []
        self.facts: dict[str, object] = {
            "style": "pirate tale",
            "setting": "zoo",
            "seed_words": ("sledge", "riverbank"),
            "pirate_guess": "",
            "real_cargo": "",
            "asked_keeper": False,
            "walked_to_exhibit": False,
            "misunderstanding_cleared": False,
            "need_met": False,
            "ending_proof": "",
            "lesson": "Curiosity works best when it asks before it grabs.",
        }

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, sentence: str) -> None:
        sentence = sentence.strip()
        if sentence:
            self.paragraphs[-1].append(sentence)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)

    def record(self, key: str, subject: str, detail: str, consequence: str = "") -> None:
        self.history.append(Event(key, subject, detail, consequence))

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
        bank_detail="flat wet stones and a rope float by the water",
        need_key="fish_breakfast",
        need_phrase="their breakfast fish",
        walk_line="the flat stone rail where the otters waited with their whiskers twitching",
        ending_image=(
            "Two otters popped up by the rope float, and silver drops sparkled over the riverbank stones "
            "as breakfast splashed into the water."
        ),
        tags=("riverbank", "fish"),
    ),
    "beaver_bend": Exhibit(
        key="beaver_bend",
        name="Beaver Bend",
        place_phrase="Harbor Zoo's riverbank boardwalk beside Beaver Bend",
        keeper_name="Keeper Amos",
        animal_label="the beavers",
        bank_detail="muddy reeds, chewed willow posts, and a low lodge at the bank",
        need_key="bank_patch",
        need_phrase="fresh willow branches and a steady edge to work beside",
        walk_line="the muddy edge where the beavers had nibbled the old willow posts",
        ending_image=(
            "A beaver tugged a fresh willow switch toward the lodge, and the patched riverbank edge stopped "
            "wobbling under the keepers' boots."
        ),
        tags=("riverbank", "repair"),
    ),
    "pelican_pier": Exhibit(
        key="pelican_pier",
        name="Pelican Pier",
        place_phrase="Harbor Zoo's riverbank dock by Pelican Pier",
        keeper_name="Keeper June",
        animal_label="the pelicans",
        bank_detail="shell-bright sand and a low dock above the water",
        need_key="fish_scoops",
        need_phrase="their feeding scoops and bowls",
        walk_line="the low feeding dock where the pelicans were already shuffling into line",
        ending_image=(
            "One pelican caught a glittering fish from the scoop and flapped once on the dock while the "
            "others leaned forward in a patient row."
        ),
        tags=("riverbank", "dock"),
    ),
    "capybara_lagoon": Exhibit(
        key="capybara_lagoon",
        name="Capybara Lagoon",
        place_phrase="Harbor Zoo's riverbank curve near Capybara Lagoon",
        keeper_name="Keeper Lani",
        animal_label="the capybaras",
        bank_detail="warm sand, shallow water, and reeds that bowed in the breeze",
        need_key="warm_blanket",
        need_phrase="a warm blanket after their bath",
        walk_line="the sandy curve where the capybaras liked to stand after the water dripped from their fur",
        ending_image=(
            "A capybara leaned into the striped blanket beside the water, and the damp riverbank reeds "
            "nodded softly behind it."
        ),
        tags=("riverbank", "warmth"),
    ),
}


CARGO_CASES: dict[str, CargoCase] = {
    "map_tube": CargoCase(
        key="map_tube",
        clue_phrase="a blue tube tied with red cord on top of the load",
        guess_phrase="a rolled treasure map",
        real_label="a feeding chart and a bucket of silver fish",
        need_key="fish_breakfast",
        reveal_line=(
            "{keeper} loosened the cord and showed {hero} a feeding chart. "
            '"Not treasure, captain," {keeper} said. "This chart tells me which fish belong to {animal} this morning."'
        ),
        use_line=(
            "{keeper} checked the chart, tipped the bright fish from the sledge bucket, and {animal} bobbed at the rail "
            "for breakfast."
        ),
        tags=("misunderstanding", "food"),
    ),
    "plank_bundle": CargoCase(
        key="plank_bundle",
        clue_phrase="a bundle of willow branches with one short plank lashed across it",
        guess_phrase="a pirate gangplank for boarding",
        real_label="fresh willow branches and a patch board for the bank edge",
        need_key="bank_patch",
        reveal_line=(
            "{keeper} tapped the little plank and smiled. "
            '"No boarding today," {keeper} said. "The beavers need fresh willow, and this board keeps the bank path steady while we work."'
        ),
        use_line=(
            "{keeper} slid the short board against the soft edge, laid the willow branches down, and {animal} hurried over to the pile."
        ),
        tags=("misunderstanding", "repair"),
    ),
    "clink_crate": CargoCase(
        key="clink_crate",
        clue_phrase="a shiny crate that clinked each time the sledge bumped a board",
        guess_phrase="a chest of pirate coins",
        real_label="tin fish scoops and feeding bowls",
        need_key="fish_scoops",
        reveal_line=(
            "{keeper} opened the crate just enough for the metal inside to flash. "
            '"Those are feeding scoops and bowls," {keeper} said. "They only sound rich because metal sings when the sledge rattles."'
        ),
        use_line=(
            "{keeper} lifted out a scoop, filled the bowls, and {animal} lined up along the dock with bright eyes and wide beaks."
        ),
        tags=("misunderstanding", "sound"),
    ),
    "sail_roll": CargoCase(
        key="sail_roll",
        clue_phrase="a striped roll tucked under netting like a folded sail",
        guess_phrase="a hidden sail wrapped around loot",
        real_label="a warm blanket and a soft grooming brush",
        need_key="warm_blanket",
        reveal_line=(
            "{keeper} drew out the striped roll and laughed gently. "
            '"It is only a blanket and brush," {keeper} said. "After a bath, {animal} like to get warm before the breeze reaches the riverbank."'
        ),
        use_line=(
            "{keeper} spread the blanket by the sand, brushed the wet fur, and {animal} settled down with a sleepy little sigh."
        ),
        tags=("misunderstanding", "comfort"),
    ),
}


HELPERS = ("Aunt Maris", "Cousin Reed", "Grandpa Sol")

HERO_NAMES: dict[str, tuple[str, ...]] = {
    "boy": ("Pip", "Nico", "Leo"),
    "child": ("Robin", "Ash", "Wren"),
    "girl": ("Mira", "Tessa", "Lila"),
}


def _mark(world: ZooWorld, name: str, *parts: object) -> bool:
    sig = (name, *parts)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    world.fired_names.append(name)
    return True


def _r_pirate_guess(world: ZooWorld) -> list[str]:
    hero = world.get("hero")
    cargo = world.get("cargo")
    if hero.meters["saw_sledge"] < THRESHOLD or cargo.meters["visible_hint"] < THRESHOLD:
        return []
    if cargo.meters["revealed"] >= THRESHOLD:
        return []
    if not _mark(world, "pirate_guess", world.exhibit.key, world.cargo.key):
        return []
    hero.memes["misunderstanding"] += 1
    hero.memes["curiosity"] += 1
    world.facts["pirate_guess"] = world.cargo.guess_phrase
    world.record(
        "guess",
        hero.label,
        f"mistook {world.cargo.clue_phrase} for {world.cargo.guess_phrase}",
        "the first guess was wrong but vivid",
    )
    return [
        f"On the sledge lay {world.cargo.clue_phrase}. "
        f'"Matey," {hero.label} whispered, "that looks like {world.cargo.guess_phrase}."'
    ]


def _r_truth_revealed(world: ZooWorld) -> list[str]:
    hero = world.get("hero")
    helper = world.get("helper")
    keeper = world.get("keeper")
    cargo = world.get("cargo")
    animal = world.get("animal")
    if not world.facts["asked_keeper"]:
        return []
    if cargo.meters["revealed"] >= THRESHOLD:
        return []
    if not _mark(world, "truth_revealed", world.exhibit.key, world.cargo.key):
        return []
    cargo.meters["revealed"] += 1
    hero.memes["misunderstanding"] = 0.0
    hero.memes["understanding"] += 1
    helper.memes["relief"] += 1
    keeper.memes["patience"] += 1
    world.facts["misunderstanding_cleared"] = True
    world.facts["real_cargo"] = world.cargo.real_label
    world.record(
        "reveal",
        keeper.label,
        f"explained that the sledge carried {world.cargo.real_label}",
        f"{hero.label} and {helper.label} learned the real purpose",
    )
    return [
        world.cargo.reveal_line.format(
            keeper=keeper.label,
            hero=hero.label,
            helper=helper.label,
            animal=animal.label,
            exhibit=world.exhibit.name,
        )
    ]


def _r_animals_helped(world: ZooWorld) -> list[str]:
    hero = world.get("hero")
    keeper = world.get("keeper")
    cargo = world.get("cargo")
    animal = world.get("animal")
    if not world.facts["walked_to_exhibit"] or cargo.meters["revealed"] < THRESHOLD:
        return []
    if world.facts["need_met"]:
        return []
    if not _mark(world, "animals_helped", world.exhibit.key, world.cargo.key):
        return []
    animal.meters["helped"] += 1
    hero.memes["wonder"] += 1
    world.facts["need_met"] = True
    world.facts["ending_proof"] = world.exhibit.ending_image
    world.record(
        "help",
        animal.label,
        f"received {world.exhibit.need_phrase}",
        world.exhibit.ending_image,
    )
    return [
        world.cargo.use_line.format(
            keeper=keeper.label,
            hero=hero.label,
            animal=animal.label,
            exhibit=world.exhibit.name,
        )
    ]


RULES = (
    Rule("pirate_guess", _r_pirate_guess),
    Rule("truth_revealed", _r_truth_revealed),
    Rule("animals_helped", _r_animals_helped),
)


def propagate(world: ZooWorld, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def valid_pairs() -> list[tuple[str, str]]:
    pairs = [
        (exhibit.key, cargo.key)
        for exhibit in EXHIBITS.values()
        for cargo in CARGO_CASES.values()
        if exhibit.need_key == cargo.need_key
    ]
    return sorted(pairs)


def invalid_reason(exhibit: str, cargo: str) -> str:
    if exhibit not in EXHIBITS:
        return f"Unknown exhibit {exhibit!r}. Choose one of: {', '.join(sorted(EXHIBITS))}."
    if cargo not in CARGO_CASES:
        return f"Unknown cargo {cargo!r}. Choose one of: {', '.join(sorted(CARGO_CASES))}."
    exhibit_obj = EXHIBITS[exhibit]
    cargo_obj = CARGO_CASES[cargo]
    return (
        f"No story: {exhibit_obj.name} needs {exhibit_obj.need_phrase}, but {cargo_obj.key} solves "
        f"{cargo_obj.need_key} instead."
    )


def valid_params(params: StoryParams) -> tuple[bool, str]:
    if params.exhibit not in EXHIBITS:
        return False, f"Unknown exhibit {params.exhibit!r}."
    if params.cargo not in CARGO_CASES:
        return False, f"Unknown cargo {params.cargo!r}."
    if params.gender not in HERO_NAMES:
        return False, f"Unknown gender bucket {params.gender!r}."
    if params.helper not in HELPERS:
        return False, f"Unknown helper {params.helper!r}. Choose one of: {', '.join(HELPERS)}."
    if params.hero.strip().lower() == params.helper.strip().lower():
        return False, "Hero and helper must be different people."
    exhibit = EXHIBITS[params.exhibit]
    cargo = CARGO_CASES[params.cargo]
    if exhibit.need_key != cargo.need_key:
        return False, invalid_reason(params.exhibit, params.cargo)
    return True, ""


def _params_from_pair(
    args: argparse.Namespace,
    pair: tuple[str, str],
    index: int,
) -> StoryParams:
    base_seed = args.seed if args.seed is not None else 1
    rng = random.Random(base_seed + index * 7919)
    gender = args.gender or rng.choice(sorted(HERO_NAMES))
    hero = args.hero or rng.choice(HERO_NAMES[gender])
    helper = args.helper or rng.choice(HELPERS)
    params = StoryParams(
        exhibit=pair[0],
        cargo=pair[1],
        hero=hero,
        gender=gender,
        helper=helper,
        seed=base_seed + index,
    )
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    return params


def build_world(params: StoryParams) -> ZooWorld:
    exhibit = EXHIBITS[params.exhibit]
    cargo = CARGO_CASES[params.cargo]
    world = ZooWorld(params, exhibit, cargo)
    world.add(
        Entity(
            id="hero",
            kind="character",
            type=params.gender,
            label=params.hero,
            role="child pirate captain",
            location=exhibit.name,
        )
    )
    world.add(
        Entity(
            id="helper",
            kind="character",
            type="adult",
            label=params.helper,
            role="trusted deck mate",
            location=exhibit.name,
        )
    )
    world.add(
        Entity(
            id="keeper",
            kind="character",
            type="adult",
            label=exhibit.keeper_name,
            role="zoo keeper",
            location=exhibit.name,
        )
    )
    world.add(
        Entity(
            id="sledge",
            kind="thing",
            type="sledge",
            label="the little sledge",
            role="keeper's supply sled",
            location="riverbank path",
        )
    )
    world.add(
        Entity(
            id="cargo",
            kind="thing",
            type="cargo",
            label=cargo.real_label,
            role="hidden zoo supply",
            location="on the sledge",
            attrs={"clue_phrase": cargo.clue_phrase},
        )
    )
    world.add(
        Entity(
            id="animal",
            kind="group",
            type="animals",
            label=exhibit.animal_label,
            role=f"residents of {exhibit.name}",
            location=exhibit.name,
        )
    )
    world.facts["place_phrase"] = exhibit.place_phrase
    world.facts["bank_detail"] = exhibit.bank_detail
    return world


def introduce(world: ZooWorld) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    hero.memes["pirate_play"] += 1
    hero.memes["curiosity"] += 1
    helper.meters["beside_hero"] += 1
    world.say(
        f"Once upon a bright morning at {world.exhibit.place_phrase}, {hero.label} walked with {helper.label} "
        f"and pretended the path was the deck of a small pirate ship. "
        f"{hero.pronoun('subject').capitalize()} kept one hand on the rail and watched {world.exhibit.bank_detail} "
        f"as if hidden islands might appear there."
    )
    world.record(
        "opening",
        hero.label,
        f"arrived at {world.exhibit.place_phrase} with {helper.label}",
        "pirate play made the zoo feel like a harbor",
    )
    world.para()


def sight_sledge(world: ZooWorld) -> None:
    hero = world.get("hero")
    sledge = world.get("sledge")
    cargo = world.get("cargo")
    sledge.meters["loaded"] += 1
    hero.meters["saw_sledge"] += 1
    cargo.meters["visible_hint"] += 1
    world.say(
        f"Then {world.exhibit.keeper_name} came along the riverbank boards, pulling a little sledge behind the keeper. "
        "Its runners made a hush-hush sound over the damp wood."
    )
    world.record(
        "sighting",
        hero.label,
        "noticed a keeper pulling a sledge along the riverbank",
        f"the clue was {world.cargo.clue_phrase}",
    )
    propagate(world)
    world.para()


def ask_carefully(world: ZooWorld) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    world.say(
        f"{helper.label} felt {hero.pronoun('possessive')} shoulder go tight and rested a calm hand there. "
        f"Instead of grabbing the rope or boasting about treasure, {hero.label} let curiosity steer the moment and asked, "
        '"Please, what is really on that sledge?"'
    )
    world.facts["asked_keeper"] = True
    hero.meters["asked_question"] += 1
    world.record(
        "question",
        hero.label,
        "asked a careful question instead of chasing the sledge",
        "curiosity took command of the pirate game",
    )
    propagate(world)
    world.para()


def follow_to_exhibit(world: ZooWorld) -> None:
    keeper = world.get("keeper")
    world.say(
        f"{keeper.label} smiled and beckoned them onward. "
        f"Together they followed the sledge to {world.exhibit.walk_line}."
    )
    world.facts["walked_to_exhibit"] = True
    world.record(
        "walk",
        keeper.label,
        f"led the pair toward {world.exhibit.name}",
        "the real work of the sledge came into view",
    )
    propagate(world)
    world.para()


def close_story(world: ZooWorld) -> None:
    hero = world.get("hero")
    if not world.facts["misunderstanding_cleared"]:
        raise StoryError("No story: the misunderstanding never clears.")
    if not world.facts["need_met"]:
        raise StoryError("No story: the cargo never helps the animals.")
    hero.memes["relief"] += 1
    world.say(
        f'{hero.label} gave a sheepish grin. "So the truest treasure was help," {hero.pronoun()} said. '
        "That made the pirate game feel bigger, not smaller, because the best captains noticed what was real. "
        f"{world.exhibit.ending_image}"
    )
    world.record(
        "ending",
        hero.label,
        "understood the sledge's real purpose",
        world.exhibit.ending_image,
    )


def tell(params: StoryParams) -> ZooWorld:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    world = build_world(params)
    introduce(world)
    sight_sledge(world)
    ask_carefully(world)
    follow_to_exhibit(world)
    close_story(world)
    return world


def _prompts(world: ZooWorld) -> list[str]:
    hero = world.get("hero")
    keeper = world.get("keeper")
    return [
        (
            f"Tell a child-facing pirate tale set at a zoo riverbank where {hero.label} sees a keeper's sledge "
            f"and mistakes {world.cargo.clue_phrase} for {world.cargo.guess_phrase}."
        ),
        (
            f"Make curiosity the turning point: {hero.label} should ask {keeper.label} a careful question "
            "instead of grabbing the load."
        ),
        (
            f"End with a concrete image showing how the real cargo helps {world.exhibit.animal_label} at {world.exhibit.name}."
        ),
    ]


def _story_qa(world: ZooWorld) -> list[QAItem]:
    hero = world.get("hero")
    helper = world.get("helper")
    keeper = world.get("keeper")
    return [
        QAItem(
            "What misunderstanding did the child have when the sledge first appeared?",
            (
                f"{hero.label} thought the load might be {world.facts['pirate_guess']}. "
                f"The clue was {world.cargo.clue_phrase}, so the pirate guess felt exciting before the truth was known."
            ),
        ),
        QAItem(
            "How did curiosity change what happened next?",
            (
                f"Curiosity made {hero.label} ask {keeper.label} what was really on the sledge instead of grabbing it or making a loud claim. "
                f"{helper.label} stayed close, so the question opened the way to the true answer."
            ),
        ),
        QAItem(
            "What was really on the sledge?",
            (
                f"The sledge was carrying {world.facts['real_cargo']}. "
                f"That load was meant to bring {world.exhibit.need_phrase} to {world.exhibit.animal_label}, not pirate treasure to anyone."
            ),
        ),
        QAItem(
            "What ending image proved that the misunderstanding was over?",
            (
                f"The final proof was simple and physical: {world.facts['ending_proof']} "
                "Once the animals used the keeper's supplies, the guessed pirate story could not stay true."
            ),
        ),
    ]


def _world_qa(world: ZooWorld) -> list[QAItem]:
    keeper = world.get("keeper")
    return [
        QAItem(
            "Where does this story happen?",
            (
                f"It happens at {world.exhibit.place_phrase}. "
                f"The riverbank setting matters because the sledge moves beside {world.exhibit.bank_detail} and reaches the exhibit from there."
            ),
        ),
        QAItem(
            "Who explained the truth about the sledge?",
            (
                f"{keeper.label} explained it. "
                "The keeper knew the job of the cargo and could connect the clue on the sledge to the animals' real needs."
            ),
        ),
        QAItem(
            "What lesson does this story support?",
            (
                f"The lesson is that {world.facts['lesson'].lower()} "
                "In this riverbank story, asking first leads to care for the animals, while guessing alone leads to a misunderstanding."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=_prompts(world),
        story_qa=_story_qa(world),
        world_qa=_world_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(E,C) :- exhibit(E), cargo(C), need(E,N), solves(C,N).
ok :- chosen(E,C), valid(E,C).

#show valid/2.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from storyworlds.asp import fact

    rows: list[str] = []
    for exhibit in sorted(EXHIBITS.values(), key=lambda item: item.key):
        rows.append(fact("exhibit", exhibit.key))
        rows.append(fact("need", exhibit.key, exhibit.need_key))
    for cargo in sorted(CARGO_CASES.values(), key=lambda item: item.key):
        rows.append(fact("cargo", cargo.key))
        rows.append(fact("solves", cargo.key, cargo.need_key))
    if params is not None:
        rows.append(fact("chosen", params.exhibit, params.cargo))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_pairs() -> set[tuple[str, str]]:
    from storyworlds.asp import atoms, solve

    pairs: set[tuple[str, str]] = set()
    for model in solve(asp_program(), models=0):
        pairs.update(atoms(model, "valid"))
    return pairs


def asp_accepts(params: StoryParams) -> bool:
    from storyworlds.asp import atoms, one_model

    return bool(atoms(one_model(asp_program(params)), "ok"))


def verify() -> str:
    python_pairs = set(valid_pairs())
    asp_pairs = asp_valid_pairs()
    if python_pairs != asp_pairs:
        only_python = sorted(python_pairs - asp_pairs)
        only_asp = sorted(asp_pairs - python_pairs)
        raise StoryError(f"ASP/Python mismatch. only_python={only_python} only_asp={only_asp}")
    for index, pair in enumerate(sorted(python_pairs), 1):
        params = StoryParams(
            exhibit=pair[0],
            cargo=pair[1],
            hero="Mira",
            gender="girl",
            helper=HELPERS[(index - 1) % len(HELPERS)],
            seed=index,
        )
        if not asp_accepts(params):
            raise StoryError(f"ASP rejected valid params: {params}")
        sample = generate(params)
        lowered = sample.story.lower()
        if "sledge" not in lowered:
            raise StoryError(f"Generated story omitted seed word 'sledge' for params={params}")
        if "riverbank" not in lowered or "zoo" not in lowered:
            raise StoryError(f"Generated story omitted setting language for params={params}")
        if not sample.prompts or len(sample.story_qa) < 3 or len(sample.world_qa) < 3:
            raise StoryError(f"QA or prompts too thin for params={params}")
        if not sample.world.facts["misunderstanding_cleared"]:
            raise StoryError(f"Misunderstanding did not clear for params={params}")
        if not sample.world.facts["need_met"]:
            raise StoryError(f"Cargo never helped the animals for params={params}")
        if "{" in sample.story or "}" in sample.story:
            raise StoryError(f"Story leaked template braces for params={params}")
    return f"OK: clingo gate matches valid_pairs() and exercised {len(python_pairs)} stories."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate pirate-flavored zoo riverbank storyworld samples."
    )
    parser.add_argument("--exhibit", choices=sorted(EXHIBITS))
    parser.add_argument("--cargo", choices=sorted(CARGO_CASES))
    parser.add_argument("--hero", default=None)
    parser.add_argument("--gender", choices=sorted(HERO_NAMES), default=None)
    parser.add_argument("--helper", choices=HELPERS, default=None)
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
            raise StoryError("No story: the chosen filters do not overlap in a reasonable zoo riverbank scenario.")
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
        for qa in sample.story_qa:
            print(f"Q: {qa.question}")
            print(f"A: {qa.answer}")
        print("\n== World QA ==")
        for qa in sample.world_qa:
            print(f"Q: {qa.question}")
            print(f"A: {qa.answer}")


def _emit_asp_listing() -> None:
    for exhibit, cargo in sorted(asp_valid_pairs()):
        print(f"{exhibit}\t{cargo}")


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
            _emit_asp_listing()
            return 0
        if args.all:
            pairs = valid_pairs()
            for index, pair in enumerate(pairs, 1):
                sample = generate(_params_from_pair(args, pair, index))
                header = None if args.json else f"### {pair[0]} / {pair[1]}"
                emit(sample, args, header)
                if index != len(pairs) and not args.json:
                    print("\n" + "=" * 72 + "\n")
            return 0
        count = max(1, args.n)
        for index in range(count):
            setattr(args, "_index", index)
            sample = generate(resolve_params(args, random.Random((args.seed or 1) + index)))
            header = None if args.json or count == 1 else f"### variant {index + 1}"
            emit(sample, args, header)
            if index != count - 1 and not args.json:
                print("\n" + "=" * 72 + "\n")
        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
