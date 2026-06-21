#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/shackle_recycle_moral_value_bad_ending_mystery.py
=============================================================================

A standalone storyworld for a small mystery about a strange sound coming from a
recycling corner. A child finds a loose metal shackle from a broken lock and is
tempted to use it to pry open a recycling container instead of asking an adult.

The domain is built to support:
- the seed words "shackle" and "recycle"
- a mystery setup and reveal
- a moral value about honesty, patience, and respecting shared places
- a bad ending when the child chooses the reckless shortcut

The world model tracks physical state (spill, mess, ruined belongings) and
emotional state (curiosity, caution, guilt, relief). The prose is driven by
that simulated state.

Run it
------
    python storyworlds/worlds/gpt-5.4/shackle_recycle_moral_value_bad_ending_mystery.py
    python storyworlds/worlds/gpt-5.4/shackle_recycle_moral_value_bad_ending_mystery.py --choice pry
    python storyworlds/worlds/gpt-5.4/shackle_recycle_moral_value_bad_ending_mystery.py --choice ask_adult
    python storyworlds/worlds/gpt-5.4/shackle_recycle_moral_value_bad_ending_mystery.py --all
    python storyworlds/worlds/gpt-5.4/shackle_recycle_moral_value_bad_ending_mystery.py --qa
    python storyworlds/worlds/gpt-5.4/shackle_recycle_moral_value_bad_ending_mystery.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "neighbor"}
        male = {"boy", "father", "man", "janitor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "janitor": "janitor",
            "neighbor": "neighbor",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    corner: str
    outdoor: bool
    adult_type: str
    adult_label: str
    afford_tags: set[str] = field(default_factory=set)


@dataclass
class ContainerCfg:
    id: str
    label: str
    phrase: str
    location: str
    contents: str
    spill_kind: str
    spill_text: str
    unstable: bool = True
    loose_lid: bool = False
    roomy: bool = False
    glassy: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    sound: str
    reveal: str
    hint: str
    need_loose_lid: bool = False
    need_roomy: bool = False
    need_glassy: bool = False
    need_outdoor: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    vulnerable: set[str] = field(default_factory=set)
    damage_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class ChoiceCfg:
    id: str
    label: str
    sense: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"hero", "friend"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spill(world: World) -> list[str]:
    box = world.get("container")
    if box.meters["jarred"] < THRESHOLD or box.meters["unstable"] < THRESHOLD:
        return []
    sig = ("spill", box.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    box.meters["spilled"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    return ["__spill__"]


def _r_soil_prize(world: World) -> list[str]:
    box = world.get("container")
    prize = world.get("prize")
    if box.meters["spilled"] < THRESHOLD:
        return []
    spill_kind = world.facts["container_cfg"].spill_kind
    if spill_kind not in prize.attrs.get("vulnerable", set()):
        return []
    sig = ("soil", prize.id, spill_kind)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    prize.meters["ruined"] += 1
    prize.meters[spill_kind] += 1
    return [prize.attrs.get("damage_text", "The mess ruined what the child was carrying.")]


def _r_workload(world: World) -> list[str]:
    prize = world.get("prize")
    adult = world.get("adult")
    if prize.meters["ruined"] < THRESHOLD:
        return []
    sig = ("work", prize.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    adult.meters["workload"] += 1
    adult.memes["concern"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="spill", tag="physical", apply=_r_spill),
    Rule(name="soil_prize", tag="physical", apply=_r_soil_prize),
    Rule(name="workload", tag="social", apply=_r_workload),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                out.extend(s for s in got if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


PLACES = {
    "schoolyard": Place(
        id="schoolyard",
        label="the schoolyard",
        corner="the recycling corner by the bike rack",
        outdoor=True,
        adult_type="janitor",
        adult_label="Mr. Bell",
        afford_tags={"outdoor", "shared_place"},
    ),
    "courtyard": Place(
        id="courtyard",
        label="the apartment courtyard",
        corner="the row of recycle bins by the brick wall",
        outdoor=True,
        adult_type="neighbor",
        adult_label="Mrs. Lane",
        afford_tags={"outdoor", "shared_place"},
    ),
    "garden": Place(
        id="garden",
        label="the community garden",
        corner="the little recycle station near the tool shed",
        outdoor=True,
        adult_type="neighbor",
        adult_label="Mr. Reed",
        afford_tags={"outdoor", "shared_place"},
    ),
}

CONTAINERS = {
    "can_cage": ContainerCfg(
        id="can_cage",
        label="can cage",
        phrase="a tall wire cage for cans",
        location="under the crooked lamp",
        contents="old cans and bottles",
        spill_kind="sticky",
        spill_text="A sour trickle from old cans splashed out with the clatter.",
        unstable=True,
        roomy=True,
        tags={"recycle", "cans"},
    ),
    "paper_bin": ContainerCfg(
        id="paper_bin",
        label="paper bin",
        phrase="a blue paper-recycle bin",
        location="beside the fence",
        contents="newspapers and cardboard",
        spill_kind="wet",
        spill_text="Rainwater hiding under the papers sloshed over the rim.",
        unstable=True,
        loose_lid=True,
        tags={"recycle", "paper"},
    ),
    "glass_crate": ContainerCfg(
        id="glass_crate",
        label="glass crate",
        phrase="a green crate for glass bottles",
        location="beside the drain",
        contents="empty jars and bottles",
        spill_kind="sharp",
        spill_text="Bottles knocked together with a bright, dangerous crash.",
        unstable=True,
        glassy=True,
        tags={"recycle", "glass"},
    ),
}

CAUSES = {
    "cat": Cause(
        id="cat",
        sound="clink... clink...",
        reveal="a thin gray cat sprang out from behind the cans with a fish wrapper in its mouth",
        hint="Something inside seemed to pause and listen back.",
        need_roomy=True,
        tags={"animal", "mystery"},
    ),
    "wind": Cause(
        id="wind",
        sound="tap... scrape... tap...",
        reveal="the loose lid was bumping the side whenever the wind slipped through",
        hint="The sound came in little breaths, as if the air itself were trying to talk.",
        need_loose_lid=True,
        need_outdoor=True,
        tags={"wind", "mystery"},
    ),
    "bottle": Cause(
        id="bottle",
        sound="tink... tink... roll...",
        reveal="one bottle inside was rocking against the others every time the crate leaned",
        hint="Whatever made the noise rolled, stopped, and rolled again.",
        need_glassy=True,
        tags={"glass", "mystery"},
    ),
}

PRIZES = {
    "library_book": Prize(
        id="library_book",
        label="library book",
        phrase="a library book with a paper fox on the cover",
        vulnerable={"wet", "sticky"},
        damage_text="The library book drank in the mess at once, and its pages puckered together.",
        tags={"book", "paper"},
    ),
    "drawing": Prize(
        id="drawing",
        label="drawing",
        phrase="a folded drawing for the wall at home",
        vulnerable={"wet", "sticky"},
        damage_text="The folded drawing sagged and blurred until the bright colors became a smear.",
        tags={"drawing", "paper"},
    ),
    "scarf": Prize(
        id="scarf",
        label="knit scarf",
        phrase="a soft knit scarf tucked through one sleeve",
        vulnerable={"sticky", "sharp"},
        damage_text="The knit scarf snagged on the tumbling edge and came away marked and torn.",
        tags={"clothes"},
    ),
}

CHOICES = {
    "ask_adult": ChoiceCfg(
        id="ask_adult",
        label="ask an adult first",
        sense=3,
        tags={"truth", "patience"},
    ),
    "pry": ChoiceCfg(
        id="pry",
        label="use the shackle to pry it open",
        sense=1,
        tags={"reckless"},
    ),
}


def cause_fits(place: Place, container: ContainerCfg, cause: Cause) -> bool:
    if cause.need_loose_lid and not container.loose_lid:
        return False
    if cause.need_roomy and not container.roomy:
        return False
    if cause.need_glassy and not container.glassy:
        return False
    if cause.need_outdoor and not place.outdoor:
        return False
    return True


def prize_at_risk(container: ContainerCfg, prize: Prize) -> bool:
    return container.spill_kind in prize.vulnerable


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for container_id, container in CONTAINERS.items():
            for cause_id, cause in CAUSES.items():
                if not cause_fits(place, container, cause):
                    continue
                for prize_id, prize in PRIZES.items():
                    if prize_at_risk(container, prize):
                        combos.append((place_id, container_id, cause_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    container: str
    cause: str
    prize: str
    choice: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    trait: str
    seed: Optional[int] = None


GIRL_NAMES = ["Lila", "Mina", "Sophie", "Nora", "Ivy", "Ella", "June", "Ruby"]
BOY_NAMES = ["Owen", "Max", "Theo", "Eli", "Ben", "Finn", "Noah", "Jack"]
TRAITS = ["curious", "brisk", "careful", "quiet", "eager", "thoughtful"]

CURATED = [
    StoryParams(
        place="schoolyard",
        container="paper_bin",
        cause="wind",
        prize="library_book",
        choice="pry",
        hero="Max",
        hero_gender="boy",
        friend="Nora",
        friend_gender="girl",
        trait="curious",
    ),
    StoryParams(
        place="courtyard",
        container="can_cage",
        cause="cat",
        prize="drawing",
        choice="pry",
        hero="Lila",
        hero_gender="girl",
        friend="Ben",
        friend_gender="boy",
        trait="eager",
    ),
    StoryParams(
        place="garden",
        container="glass_crate",
        cause="bottle",
        prize="scarf",
        choice="pry",
        hero="Theo",
        hero_gender="boy",
        friend="Ruby",
        friend_gender="girl",
        trait="quiet",
    ),
    StoryParams(
        place="schoolyard",
        container="paper_bin",
        cause="wind",
        prize="drawing",
        choice="ask_adult",
        hero="Ivy",
        hero_gender="girl",
        friend="Owen",
        friend_gender="boy",
        trait="careful",
    ),
]


def explain_combo(place: Place, container: ContainerCfg, cause: Cause, prize: Prize) -> str:
    if not cause_fits(place, container, cause):
        return (
            f"(No story: {cause.id} is not a reasonable cause for noise in {container.phrase} "
            f"at {place.label}. Pick a cause that matches the container.)"
        )
    if not prize_at_risk(container, prize):
        return (
            f"(No story: a spill from {container.phrase} would not reasonably ruin the {prize.label}, "
            f"so the bad turn would feel weak. Pick a prize that the spill could actually damage.)"
        )
    return "(No story: this combination is not reasonable.)"


def outcome_of(params: StoryParams) -> str:
    if params.choice == "ask_adult":
        return "safe"
    return "bad"


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def predict_spill(world: World) -> dict:
    sim = world.copy()
    box = sim.get("container")
    box.meters["jarred"] += 1
    propagate(sim, narrate=False)
    prize = sim.get("prize")
    return {
        "spill": box.meters["spilled"] >= THRESHOLD,
        "ruined": prize.meters["ruined"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, friend: Entity, place: Place, container: ContainerCfg,
              cause: Cause, prize: Entity) -> None:
    hero.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.say(
        f"Late that afternoon, {hero.id} and {friend.id} cut across {place.label}. "
        f"Near {place.corner} stood {container.phrase} {container.location}."
    )
    world.say(
        f"Just as they passed, it made a strange sound: {cause.sound} {cause.hint}"
    )
    world.say(
        f"{hero.id} tightened {hero.pronoun('possessive')} arm around {prize.phrase}. "
        f'"Did you hear that?" {hero.pronoun()} whispered.'
    )


def inspect(world: World, hero: Entity, friend: Entity, cause: Cause) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"They stepped closer. The whole corner felt full of small clues and shadows."
    )
    world.say(
        f'{friend.id} listened hard. "It sounds like a mystery," {friend.pronoun()} said.'
    )


def find_shackle(world: World, hero: Entity) -> None:
    shackle = world.add(Entity(
        id="shackle",
        type="thing",
        label="shackle",
        phrase="the loose shackle from a broken padlock",
        tags={"shackle", "metal"},
    ))
    world.facts["shackle"] = shackle
    world.say(
        f"By the container's wheel lay {shackle.phrase}, cold and silver in the dust."
    )
    world.say(
        f'{hero.id} picked it up. "I could hook this under the lid," {hero.pronoun()} murmured.'
    )


def warn(world: World, hero: Entity, friend: Entity, place: Place, container: ContainerCfg) -> None:
    friend.memes["caution"] += 1
    pred = predict_spill(world)
    world.facts["predicted_spill"] = pred["spill"]
    world.facts["predicted_ruined"] = pred["ruined"]
    adult = world.get("adult")
    extra = ""
    if pred["ruined"]:
        extra = f" If something spills, your {world.get('prize').label} could be ruined too."
    world.say(
        f'{friend.id} shook {friend.pronoun("possessive")} head. '
        f'"We should get {adult.id}," {friend.pronoun()} said. '
        f'"That recycle spot is not for poking at with metal.{extra}"'
    )


def choose_pry(world: World, hero: Entity, friend: Entity, container: ContainerCfg) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'But the mystery pulled harder than the warning. "{friend.id}, just one peek," '
        f'{hero.id} said.'
    )
    world.say(
        f"{hero.id} slid the shackle under the edge of the {container.label} and tugged."
    )
    box = world.get("container")
    box.meters["jarred"] += 1
    propagate(world, narrate=False)


def narrate_spill(world: World, container: ContainerCfg) -> None:
    box = world.get("container")
    if box.meters["spilled"] >= THRESHOLD:
        world.say(container.spill_text)
        propagate(world, narrate=True)


def reveal_after_pry(world: World, hero: Entity, cause: Cause) -> None:
    hero.memes["shock"] += 1
    world.say(
        f"And that was the answer to the mystery: {cause.reveal}."
    )


def adult_arrives(world: World, adult: Entity, hero: Entity, friend: Entity) -> None:
    adult.memes["concern"] += 1
    world.say(
        f'{adult.id} came hurrying over. "{hero.id}! {friend.id}! Step back," '
        f'{adult.pronoun()} said.'
    )


def bad_ending(world: World, adult: Entity, hero: Entity, friend: Entity, prize: Entity) -> None:
    hero.memes["guilt"] += 1
    friend.memes["sadness"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f"{adult.id} knelt beside the mess and looked more sad than angry."
    )
    if prize.meters["ruined"] >= THRESHOLD:
        world.say(
            f"{hero.id} stared at {hero.pronoun('possessive')} {prize.label}. "
            f"It was ruined before the sun was even down."
        )
    world.say(
        f'"Mysteries do not get better when we make a bigger problem," {adult.id} said softly. '
        f'"Shared recycle bins must be treated carefully, and when something feels strange, '
        f'you tell the truth and ask for help."'
    )
    world.say(
        f"{hero.id} helped pick up the scattered recycling in silence. "
        f"The mystery was solved, but the evening had turned heavy and unhappy."
    )
    world.say(
        f"When they finally walked home, {hero.id} carried only the lesson. "
        f"The lost bookish adventure, the torn scarf, or the blurred drawing could not be fixed that day."
    )


def choose_adult(world: World, adult: Entity, hero: Entity, friend: Entity, cause: Cause,
                 prize: Entity) -> None:
    hero.memes["restraint"] += 1
    friend.memes["relief"] += 1
    adult.memes["care"] += 1
    world.say(
        f"{hero.id} looked at the shackle, then slowly set it back on the ground."
    )
    world.say(
        f'Together the children called for {adult.id}. {adult.pronoun().capitalize()} '
        f'came over and opened the container the safe way.'
    )
    world.say(
        f"The answer to the mystery was simple after all: {cause.reveal}."
    )
    world.say(
        f'{adult.id} smiled at them. "Thank you for asking instead of guessing with your hands," '
        f'{adult.pronoun()} said.'
    )
    world.say(
        f"{hero.id} tucked {prize.phrase} safely under {hero.pronoun('possessive')} arm, and "
        f"the three of them put one stray bottle into the right place to recycle it."
    )
    world.say(
        "They left with the mystery solved, the corner tidy, and nothing spoiled."
    )


def tell(place: Place, container_cfg: ContainerCfg, cause: Cause, prize_cfg: Prize,
         choice: ChoiceCfg, hero_name: str, hero_gender: str,
         friend_name: str, friend_gender: str, trait: str) -> World:
    world = World(place=place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        traits=[trait],
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        traits=["careful"],
    ))
    adult = world.add(Entity(
        id=place.adult_label,
        kind="character",
        type=place.adult_type,
        role="adult",
        label="the adult",
    ))
    box = world.add(Entity(
        id="container",
        type="container",
        label=container_cfg.label,
        phrase=container_cfg.phrase,
        tags=set(container_cfg.tags),
    ))
    box.meters["unstable"] = 1.0 if container_cfg.unstable else 0.0
    prize = world.add(Entity(
        id="prize",
        type="prize",
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        attrs={"vulnerable": set(prize_cfg.vulnerable), "damage_text": prize_cfg.damage_text},
        tags=set(prize_cfg.tags),
    ))

    introduce(world, hero, friend, place, container_cfg, cause, prize)
    inspect(world, hero, friend, cause)

    world.para()
    find_shackle(world, hero)
    warn(world, hero, friend, place, container_cfg)

    world.para()
    if choice.id == "pry":
        choose_pry(world, hero, friend, container_cfg)
        narrate_spill(world, container_cfg)
        reveal_after_pry(world, hero, cause)
        adult_arrives(world, adult, hero, friend)
        world.para()
        bad_ending(world, adult, hero, friend, prize)
        outcome = "bad"
    else:
        choose_adult(world, adult, hero, friend, cause, prize)
        outcome = "safe"

    world.facts.update(
        place=place,
        container_cfg=container_cfg,
        cause=cause,
        prize_cfg=prize_cfg,
        choice=choice,
        hero=hero,
        friend=friend,
        adult=adult,
        prize=prize,
        outcome=outcome,
        spilled=box.meters["spilled"] >= THRESHOLD,
        ruined=prize.meters["ruined"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "shackle": [
        (
            "What is a shackle?",
            "A shackle is a curved piece of metal used as part of a lock or chain. It is hard and not a toy."
        )
    ],
    "recycle": [
        (
            "What does recycle mean?",
            "To recycle means to put used paper, metal, glass, or plastic in the right place so the material can be used again."
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is something you do not understand yet and want to figure out. A good mystery is solved by noticing clues and making careful choices."
        )
    ],
    "wind": [
        (
            "How can wind make a strange sound?",
            "Wind can push loose lids or light objects so they tap and scrape. That can sound mysterious even when nothing scary is there."
        )
    ],
    "animal": [
        (
            "Why should you not reach into a bin to look for an animal?",
            "An animal in a bin may be frightened and may scratch or jump suddenly. It is safer to get a grown-up to help."
        )
    ],
    "glass": [
        (
            "Why are glass bottles dangerous when they fall?",
            "Glass can break into sharp pieces. Sharp pieces can cut skin or tear cloth."
        )
    ],
    "paper": [
        (
            "Why do paper things get ruined by spills?",
            "Paper soaks up water and sticky mess quickly. Once it wrinkles or tears, it is hard to make it like new again."
        )
    ],
    "truth": [
        (
            "Why is it important to tell the truth when something goes wrong?",
            "Telling the truth helps grown-ups solve the problem and keep everyone safe. It also shows that you are trying to make things right."
        )
    ],
}

KNOWLEDGE_ORDER = ["shackle", "recycle", "mystery", "wind", "animal", "glass", "paper", "truth"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    container = f["container_cfg"]
    cause = f["cause"]
    choice = f["choice"]
    if choice.id == "pry":
        return [
            'Write a short mystery story for a 3-to-5-year-old that includes the words "shackle" and "recycle".',
            f"Tell a mystery where {hero.id} and {friend.id} hear a strange sound near {container.phrase}, and {hero.id} uses a shackle instead of asking an adult.",
            "Write a cautionary story with a moral value and a bad ending, where curiosity turns into trouble at a recycle bin.",
        ]
    return [
        'Write a short mystery story for a 3-to-5-year-old that includes the words "shackle" and "recycle".',
        f"Tell a gentle mystery where {hero.id} and {friend.id} hear a strange sound near {container.phrase}, but choose to ask an adult for help.",
        "Write a story about curiosity, patience, and respecting shared places, with a calm reveal at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    adult = f["adult"]
    container = f["container_cfg"]
    cause = f["cause"]
    prize = f["prize"]
    qa: list[tuple[str, str]] = [
        (
            "What was the mystery in the story?",
            f"The mystery was the strange sound coming from {container.phrase} near the recycling corner. The children did not know what was inside, so the sound felt secret and spooky."
        ),
        (
            f"What did {hero.id} find on the ground?",
            f"{hero.id} found a loose shackle from a broken padlock. {hero.pronoun().capitalize()} thought it could be used to lift or hook the container open."
        ),
        (
            f"Why did {friend.id} want to get {adult.id}?",
            f"{friend.id} knew the recycle spot was a shared place and not something to poke at with metal. {friend.pronoun().capitalize()} also understood that a spill could ruin {hero.id}'s {prize.label}."
        ),
    ]
    if f["outcome"] == "bad":
        qa.extend([
            (
                f"What happened when {hero.id} used the shackle?",
                f"{hero.id} jarred the container, and it spilled before {hero.pronoun()} could stop it. That turned the mystery into a bigger problem right away."
            ),
            (
                "What was making the strange sound?",
                f"In the end, the sound came from {cause.reveal}. The answer was ordinary, but the careless choice made the ending sad."
            ),
            (
                f"Why was the ending a bad ending?",
                f"It was a bad ending because the spill ruined the {prize.label} and left a mess for everyone. {hero.id} solved the mystery, but only after ignoring a warning and harming something important."
            ),
            (
                "What was the moral of the story?",
                "The moral was that curiosity needs patience and honesty. When something feels strange or risky, it is better to ask for help than to force an answer."
            ),
        ])
    else:
        qa.extend([
            (
                "How did they solve the mystery safely?",
                f"They put the shackle down and called {adult.id}. {adult.pronoun().capitalize()} opened the container safely, so nobody was hurt and nothing was ruined."
            ),
            (
                "What was making the strange sound?",
                f"The sound came from {cause.reveal}. It only seemed frightening because the children did not know the cause yet."
            ),
            (
                "What lesson did the children learn?",
                "They learned that patience can solve a mystery better than grabbing and prying. Asking for help kept the recycling corner tidy and their belongings safe."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"shackle", "recycle", "mystery", "truth"}
    if "wind" in f["cause"].tags:
        tags.add("wind")
    if "animal" in f["cause"].tags:
        tags.add("animal")
    if "glass" in f["cause"].tags or "glass" in f["container_cfg"].tags:
        tags.add("glass")
    if "paper" in f["prize_cfg"].tags or "paper" in f["container_cfg"].tags:
        tags.add("paper")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- compatibility gate ----------------------------------------------------
cause_fits(P, C, cat)    :- place(P), container(C), roomy(C).
cause_fits(P, C, wind)   :- place(P), container(C), outdoor(P), loose_lid(C).
cause_fits(P, C, bottle) :- place(P), container(C), glassy(C).

prize_at_risk(C, Pr) :- spill_kind(C, M), vulnerable(Pr, M).

valid(P, C, Ca, Pr) :- place(P), container(C), cause(Ca), prize(Pr),
                       cause_fits(P, C, Ca), prize_at_risk(C, Pr).

% --- outcome model ---------------------------------------------------------
outcome(safe) :- choice(ask_adult).
outcome(bad)  :- choice(pry), unstable(chosen_container).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.outdoor:
            lines.append(asp.fact("outdoor", pid))
    for cid, container in CONTAINERS.items():
        lines.append(asp.fact("container", cid))
        if container.loose_lid:
            lines.append(asp.fact("loose_lid", cid))
        if container.roomy:
            lines.append(asp.fact("roomy", cid))
        if container.glassy:
            lines.append(asp.fact("glassy", cid))
        if container.unstable:
            lines.append(asp.fact("unstable", cid))
        lines.append(asp.fact("spill_kind", cid, container.spill_kind))
    for cause_id in CAUSES:
        lines.append(asp.fact("cause", cause_id))
    for prize_id, prize in PRIZES.items():
        lines.append(asp.fact("prize", prize_id))
        for mess in sorted(prize.vulnerable):
            lines.append(asp.fact("vulnerable", prize_id, mess))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("choice", params.choice),
        asp.fact("chosen_container", params.container),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            rc = 1
            print("MISMATCH in outcome:", p, asp_outcome(p), outcome_of(p))
            break
    else:
        print(f"OK: outcome model matches on {len(cases)} curated scenarios.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("generated empty story in smoke test")
        print("OK: smoke generation passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mystery storyworld: a strange sound, a loose shackle, and a choice about the recycle bin."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.container and args.cause and args.prize:
        place = PLACES[args.place]
        container = CONTAINERS[args.container]
        cause = CAUSES[args.cause]
        prize = PRIZES[args.prize]
        if not (cause_fits(place, container, cause) and prize_at_risk(container, prize)):
            raise StoryError(explain_combo(place, container, cause, prize))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.container is None or c[1] == args.container)
        and (args.cause is None or c[2] == args.cause)
        and (args.prize is None or c[3] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, container_id, cause_id, prize_id = rng.choice(sorted(combos))
    choice = args.choice or rng.choices(["pry", "ask_adult"], weights=[4, 1], k=1)[0]
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hero_gender)
    friend = args.friend or _pick_name(rng, friend_gender, avoid=hero)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        container=container_id,
        cause=cause_id,
        prize=prize_id,
        choice=choice,
        hero=hero,
        hero_gender=hero_gender,
        friend=friend,
        friend_gender=friend_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        container = CONTAINERS[params.container]
        cause = CAUSES[params.cause]
        prize = PRIZES[params.prize]
        choice = CHOICES[params.choice]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err.args[0]})") from err

    if not (cause_fits(place, container, cause) and prize_at_risk(container, prize)):
        raise StoryError(explain_combo(place, container, cause, prize))

    world = tell(
        place=place,
        container_cfg=container,
        cause=cause,
        prize_cfg=prize,
        choice=choice,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, container, cause, prize) combos:\n")
        for place, container, cause, prize in combos:
            print(f"  {place:10} {container:11} {cause:7} {prize}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.hero} & {p.friend}: {p.container} / {p.cause} / "
                f"{p.choice} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
