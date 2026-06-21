#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/conquer_born_happy_ending_folk_tale.py
=================================================================

A standalone storyworld for a small folk-tale domain:

A child is born under a sign, a fearsome creature blocks some village need,
and the child sets out not to conquer by force, but to conquer the trouble by
meeting the creature's true need. Every valid story ends happily, though some
endings are simple peaces and some become brighter legends.

Run it
------
python storyworlds/worlds/gpt-5.4/conquer_born_happy_ending_folk_tale.py
python storyworlds/worlds/gpt-5.4/conquer_born_happy_ending_folk_tale.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/conquer_born_happy_ending_folk_tale.py --all --qa
python storyworlds/worlds/gpt-5.4/conquer_born_happy_ending_folk_tale.py --trace --seed 11
python storyworlds/worlds/gpt-5.4/conquer_born_happy_ending_folk_tale.py --json
python storyworlds/worlds/gpt-5.4/conquer_born_happy_ending_folk_tale.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)


@dataclass
class Origin:
    id: str
    born_line: str
    title: str
    virtue: str
    prophecy: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CreatureCfg:
    id: str
    label: str
    phrase: str
    need: str
    admires: str
    allows: set[str]
    symptom: str
    roar: str
    peace_line: str
    boon: str
    tags: set[str] = field(default_factory=set)


@dataclass
class PlaceCfg:
    id: str
    label: str
    phrase: str
    want: str
    blocked_line: str
    restore_line: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class OfferingCfg:
    id: str
    label: str
    phrase: str
    comforts: str
    offer_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    label: str
    phrase: str
    advice: str
    carry_line: str
    ending_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_comfort(world: World) -> list[str]:
    creature = world.get("creature")
    offering = world.get("offering")
    need = creature.attrs.get("need")
    comforts = offering.attrs.get("comforts")
    if creature.meters["troubled"] < THRESHOLD or offering.meters["given"] < THRESHOLD:
        return []
    sig = ("comfort", need, comforts)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if need == comforts:
        creature.meters["troubled"] = 0.0
        creature.meters["soothed"] += 1
        creature.memes["trust"] += 1
        return [creature.attrs.get("soften_line", "The creature softened.")]
    creature.memes["suspicion"] += 1
    return []


def _r_open(world: World) -> list[str]:
    creature = world.get("creature")
    place = world.get("place")
    village = world.get("village")
    if creature.meters["soothed"] < THRESHOLD:
        return []
    sig = ("open", place.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    place.meters["blocked"] = 0.0
    place.meters["open"] += 1
    village.memes["hope"] += 1
    return [place.attrs.get("restore_line", "The way opened again.")]


def _r_boon(world: World) -> list[str]:
    hero = world.get("hero")
    creature = world.get("creature")
    village = world.get("village")
    if world.get("place").meters["open"] < THRESHOLD:
        return []
    sig = ("boon", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if hero.attrs.get("virtue") == creature.attrs.get("admires"):
        hero.meters["boon"] += 1
        village.memes["joy"] += 1
        return [creature.attrs.get("boon_line", "The creature gave a blessing in return.")]
    return []


CAUSAL_RULES = [
    Rule(name="comfort", apply=_r_comfort),
    Rule(name="open", apply=_r_open),
    Rule(name="boon", apply=_r_boon),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def place_allows(creature: CreatureCfg, place: PlaceCfg) -> bool:
    return place.id in creature.allows


def offering_works(creature: CreatureCfg, offering: OfferingCfg) -> bool:
    return creature.need == offering.comforts


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for creature_id, creature in CREATURES.items():
            if not place_allows(creature, place):
                continue
            for offering_id, offering in OFFERINGS.items():
                if offering_works(creature, offering):
                    combos.append((place_id, creature_id, offering_id))
    return sorted(combos)


def ending_of(params: "StoryParams") -> str:
    origin = ORIGINS[params.origin]
    creature = CREATURES[params.creature]
    return "boon" if origin.virtue == creature.admires else "peace"


def predict_peace(world: World, offering_id: str) -> dict:
    sim = world.copy()
    sim_offer = sim.get("offering")
    sim_offer.attrs["comforts"] = OFFERINGS[offering_id].comforts
    sim_offer.meters["given"] += 1
    propagate(sim, narrate=False)
    return {
        "opens": sim.get("place").meters["open"] >= THRESHOLD,
        "boon": sim.get("hero").meters["boon"] >= THRESHOLD,
    }


def introduce_birth(world: World, hero: Entity, origin: Origin) -> None:
    world.say(
        f"In a valley of bells and little fields, there lived a child named {hero.id}. "
        f"{origin.born_line} The old miller said, \"This is {origin.title}. {origin.prophecy}\""
    )
    hero.memes["beloved"] += 1


def trouble_rises(world: World, hero: Entity, creature: CreatureCfg, place: PlaceCfg) -> None:
    village = world.get("village")
    place_ent = world.get("place")
    creature_ent = world.get("creature")
    village.memes["worry"] += 1
    place_ent.meters["blocked"] += 1
    creature_ent.meters["troubled"] += 1
    world.say(
        f"Years passed, and one hard season {creature.phrase} came to {place.phrase}. "
        f"{place.blocked_line}"
    )
    world.say(
        f"The grown people whispered of nets and spears, but {hero.id} listened more closely. "
        f"{creature.symptom.capitalize()}."
    )


def wise_advice(world: World, hero: Entity, helper: HelperCfg, creature: CreatureCfg) -> None:
    offering_ids = [oid for oid, off in OFFERINGS.items() if off.comforts == creature.need]
    chosen = offering_ids[0] if offering_ids else ""
    pred = predict_peace(world, chosen) if chosen else {"opens": False, "boon": False}
    world.facts["predicted_opens"] = pred["opens"]
    world.facts["predicted_boon"] = pred["boon"]
    world.say(
        f"An elder placed {helper.phrase} in {hero.id}'s hands and said, "
        f"\"{helper.advice}\""
    )


def vow_and_journey(world: World, hero: Entity, offering: OfferingCfg, helper: HelperCfg, place: PlaceCfg) -> None:
    hero.memes["resolve"] += 1
    world.say(
        f"Then {hero.id} said, \"I will not conquer this sorrow with a sword. "
        f"I will conquer it with a listening heart.\" {hero.pronoun().capitalize()} took "
        f"{offering.phrase}, {helper.carry_line}, and walked toward {place.phrase}."
    )


def encounter(world: World, hero: Entity, creature: CreatureCfg, place: PlaceCfg) -> None:
    creature_ent = world.get("creature")
    hero.memes["courage"] += 1
    creature_ent.memes["anger"] += 1
    world.say(
        f"At {place.phrase}, {hero.id} saw {creature.phrase} clearly. "
        f"{creature.roar}"
    )


def give_offering(world: World, hero: Entity, offering: OfferingCfg) -> None:
    offering_ent = world.get("offering")
    offering_ent.meters["given"] += 1
    world.say(
        f"But {hero.id} did not run. {hero.pronoun().capitalize()} stepped forward and "
        f"{offering.offer_line}"
    )
    propagate(world, narrate=True)


def peace_ending(world: World, hero: Entity, creature: CreatureCfg, place: PlaceCfg, helper: HelperCfg) -> None:
    village = world.get("village")
    village.memes["relief"] += 1
    world.say(
        f"{creature.peace_line} {place.restore_line} {helper.ending_line}"
    )
    world.say(
        f"Before sunset, {place.ending_image}. The village said that {hero.id} had been "
        f"born for courage, and had conquered fear by showing mercy first."
    )


def boon_ending(world: World, hero: Entity, creature: CreatureCfg, place: PlaceCfg, helper: HelperCfg) -> None:
    village = world.get("village")
    village.memes["relief"] += 1
    world.say(
        f"{creature.peace_line} {place.restore_line} {helper.ending_line}"
    )
    world.say(
        f"Then {creature.phrase} bowed and gave {hero.id} {creature.boon}. "
        f"Before sunset, {place.ending_image}, and the new gift shone among them like a promise."
    )
    world.say(
        f"So the tale was told for many winters: {hero.id}, once born beneath {world.facts['origin'].title.lower()}, "
        f"had learned that the kindest heart may conquer what the sharpest blade cannot."
    )


ORIGINS = {
    "dawn": Origin(
        id="dawn",
        born_line="When Mira was born, the eastern sky opened like a peach-colored flower over the roofs.",
        title="the Child of Dawn",
        virtue="gentle",
        prophecy="Where this child walks, harsh voices may soften.",
        tags={"born", "dawn"},
    ),
    "oak_moon": Origin(
        id="oak_moon",
        born_line="When Tomas was born, the round oak moon hung over the hills like a bright shield.",
        title="the Child of the Oak Moon",
        virtue="brave",
        prophecy="Where this child stands, frightened hearts may stand steady too.",
        tags={"born", "moon"},
    ),
    "first_snow": Origin(
        id="first_snow",
        born_line="When Elin was born, the first snow fell so quietly that even the dogs stopped barking.",
        title="the Child of First Snow",
        virtue="patient",
        prophecy="Where this child waits, tangled troubles may slowly loosen.",
        tags={"born", "snow"},
    ),
}

CREATURES = {
    "giant": CreatureCfg(
        id="giant",
        label="giant",
        phrase="the hill giant",
        need="hungry",
        admires="brave",
        allows={"bridge", "orchard"},
        symptom="his stomach rumbled like a mill drum, and his great eyes looked more tired than cruel",
        roar="\"Go away,\" boomed the giant, though the sound wavered like an empty kettle.",
        peace_line="The giant's shoulders sank, and the fierce look went out of his face.",
        boon="a brass horn that could call help from every hillside",
        tags={"giant", "hungry"},
    ),
    "dragon": CreatureCfg(
        id="dragon",
        label="dragon",
        phrase="the mist dragon",
        need="lonely",
        admires="gentle",
        allows={"spring", "gate"},
        symptom="the long silver body was curled in a sad ring, as if it had wrapped itself around its own loneliness",
        roar="\"No feet on this road, no buckets at this spring,\" sang the dragon in a voice like wind in jars.",
        peace_line="The dragon lifted its head, listening as if it had not heard a kind voice in a hundred years.",
        boon="a clear blue scale that glimmered like a drop of sky",
        tags={"dragon", "lonely"},
    ),
    "troll": CreatureCfg(
        id="troll",
        label="troll",
        phrase="the marsh troll",
        need="cold",
        admires="patient",
        allows={"bridge", "spring"},
        symptom="blue hands hugged its own ribs, and its teeth knocked together like pebbles in winter water",
        roar="\"Back, little one,\" grumbled the troll, though the words came between shivers.",
        peace_line="Warmth crept back into the troll's face, and it blinked in surprise at the kindness shown to it.",
        boon="a smooth river-stone that always kept the hearth coals alive",
        tags={"troll", "cold"},
    ),
}

PLACES = {
    "bridge": PlaceCfg(
        id="bridge",
        label="bridge",
        phrase="the old bridge of willow planks",
        want="the road to market",
        blocked_line="No cart could cross, and the village mill stood hungry for grain because the road to market was shut.",
        restore_line="Soon the old bridge belonged to travelers again.",
        ending_image="carts rolled across the bridge, and the lanterns on them winked like fireflies",
        tags={"bridge", "road"},
    ),
    "spring": PlaceCfg(
        id="spring",
        label="spring",
        phrase="the stone spring under the hill",
        want="fresh water",
        blocked_line="The pails came home empty, and even the parsley in the kitchen gardens drooped for want of water.",
        restore_line="Soon clear water ran singing into every waiting pail.",
        ending_image="the spring shone full again, and children laughed to see their faces in it",
        tags={"spring", "water"},
    ),
    "orchard": PlaceCfg(
        id="orchard",
        label="orchard",
        phrase="the red apple orchard",
        want="the apple harvest",
        blocked_line="No one dared gather fruit, and the red apples hung too long on the branches while the village watched from afar.",
        restore_line="Soon ladders leaned against the trees again, and baskets filled with apples.",
        ending_image="the orchard smelled of sweet peel and cider, and songs drifted between the rows",
        tags={"orchard", "apples"},
    ),
    "gate": PlaceCfg(
        id="gate",
        label="gate",
        phrase="the high gate of the mountain path",
        want="the mountain path",
        blocked_line="No shepherd could lead the sheep upward, and the high meadows waited empty behind the shut way.",
        restore_line="Soon the mountain path stood open from stone to sky.",
        ending_image="bells from the sheep came floating down the mountain path like happy rain",
        tags={"gate", "path"},
    ),
}

OFFERINGS = {
    "bread": OfferingCfg(
        id="bread",
        label="honey bread",
        phrase="a warm round of honey bread",
        comforts="hungry",
        offer_line="held up the honey bread and broke it so the sweet smell could travel ahead of her",
        tags={"bread", "food"},
    ),
    "song": OfferingCfg(
        id="song",
        label="reed song",
        phrase="a little reed flute",
        comforts="lonely",
        offer_line="raised the reed flute and played a tune simple enough for even the stones to remember",
        tags={"song", "music"},
    ),
    "cloak": OfferingCfg(
        id="cloak",
        label="wool cloak",
        phrase="a thick wool cloak",
        comforts="cold",
        offer_line="opened the wool cloak with both hands, offering its warmth before a single harsh word",
        tags={"cloak", "warmth"},
    ),
}

HELPERS = {
    "lantern": HelperCfg(
        id="lantern",
        label="lantern",
        phrase="a small brass lantern",
        advice="Carry a little light, and look for the hurt beneath the noise.",
        carry_line="a small brass lantern swinging at her side",
        ending_line="The brass lantern shone softly, not as a weapon, but as a witness to peace.",
        tags={"lantern"},
    ),
    "bell": HelperCfg(
        id="bell",
        label="bell",
        phrase="a shepherd's bell on a blue cord",
        advice="Let your steps ring true, for false hearts make the loudest clatter.",
        carry_line="a shepherd's bell tied at the wrist",
        ending_line="The little bell gave one bright note, as if the valley itself had sighed in relief.",
        tags={"bell"},
    ),
    "thread": HelperCfg(
        id="thread",
        label="red thread",
        phrase="a coil of red thread",
        advice="If the path seems tangled, remember that patience is a hand that does not tear.",
        carry_line="red thread tucked in a pocket for luck",
        ending_line="The red thread fluttered in the breeze like a tiny banner of peace.",
        tags={"thread"},
    ),
}

GIRL_NAMES = ["Mira", "Elin", "Nora", "Ava", "Lina", "Rose"]
BOY_NAMES = ["Tomas", "Ivo", "Milo", "Theo", "Finn", "Leo"]


@dataclass
class StoryParams:
    origin: str
    place: str
    creature: str
    offering: str
    helper: str
    hero_name: str
    hero_gender: str
    elder_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        origin="dawn",
        place="spring",
        creature="dragon",
        offering="song",
        helper="lantern",
        hero_name="Mira",
        hero_gender="girl",
        elder_type="mother",
    ),
    StoryParams(
        origin="oak_moon",
        place="bridge",
        creature="giant",
        offering="bread",
        helper="bell",
        hero_name="Tomas",
        hero_gender="boy",
        elder_type="father",
    ),
    StoryParams(
        origin="first_snow",
        place="spring",
        creature="troll",
        offering="cloak",
        helper="thread",
        hero_name="Elin",
        hero_gender="girl",
        elder_type="mother",
    ),
    StoryParams(
        origin="dawn",
        place="gate",
        creature="dragon",
        offering="song",
        helper="bell",
        hero_name="Nora",
        hero_gender="girl",
        elder_type="father",
    ),
    StoryParams(
        origin="oak_moon",
        place="orchard",
        creature="giant",
        offering="bread",
        helper="lantern",
        hero_name="Ivo",
        hero_gender="boy",
        elder_type="mother",
    ),
]


def explain_rejection(place: PlaceCfg, creature: CreatureCfg, offering: OfferingCfg) -> str:
    if not place_allows(creature, place):
        return (
            f"(No story: {creature.phrase} does not fit naturally at {place.phrase}. "
            f"Pick a place the creature could truly block.)"
        )
    if not offering_works(creature, offering):
        return (
            f"(No story: {offering.label} would not soothe {creature.phrase}. "
            f"This creature needs comfort for being {creature.need}, not {offering.comforts}.)"
        )
    return "(No story: that combination does not make a reasonable folk tale here.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a child born under a sign conquers trouble in folk-tale fashion."
    )
    ap.add_argument("--origin", choices=ORIGINS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--offering", choices=OFFERINGS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.creature and args.offering:
        place = PLACES[args.place]
        creature = CREATURES[args.creature]
        offering = OFFERINGS[args.offering]
        if not (place_allows(creature, place) and offering_works(creature, offering)):
            raise StoryError(explain_rejection(place, creature, offering))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.creature is None or combo[1] == args.creature)
        and (args.offering is None or combo[2] == args.offering)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, creature_id, offering_id = rng.choice(combos)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    default_names = GIRL_NAMES if hero_gender == "girl" else BOY_NAMES
    hero_name = args.hero_name or rng.choice(default_names)
    return StoryParams(
        origin=args.origin or rng.choice(sorted(ORIGINS)),
        place=place_id,
        creature=creature_id,
        offering=offering_id,
        helper=args.helper or rng.choice(sorted(HELPERS)),
        hero_name=hero_name,
        hero_gender=hero_gender,
        elder_type=args.elder or rng.choice(["mother", "father"]),
    )


def tell(
    origin: Origin,
    place: PlaceCfg,
    creature: CreatureCfg,
    offering: OfferingCfg,
    helper: HelperCfg,
    hero_name: str,
    hero_gender: str,
    elder_type: str,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type=hero_gender,
            label=hero_name,
            phrase=hero_name,
            role="hero",
            attrs={"virtue": origin.virtue},
            tags={origin.virtue},
        )
    )
    elder = world.add(
        Entity(
            id="elder",
            kind="character",
            type=elder_type,
            label=elder_type,
            phrase=f"the {elder_type}",
            role="elder",
        )
    )
    village = world.add(
        Entity(
            id="village",
            kind="thing",
            type="village",
            label="village",
            phrase="the little valley village",
            role="village",
        )
    )
    place_ent = world.add(
        Entity(
            id="place",
            kind="thing",
            type="place",
            label=place.label,
            phrase=place.phrase,
            role="place",
            attrs={"restore_line": place.restore_line},
            tags=set(place.tags),
        )
    )
    creature_ent = world.add(
        Entity(
            id="creature",
            kind="character",
            type="creature",
            label=creature.label,
            phrase=creature.phrase,
            role="creature",
            attrs={
                "need": creature.need,
                "admires": creature.admires,
                "soften_line": creature.peace_line,
                "boon_line": f"Because {hero_name} had come in the spirit it most admired, {creature.phrase} offered a gift in return.",
            },
            tags=set(creature.tags),
        )
    )
    world.add(
        Entity(
            id="offering",
            kind="thing",
            type="offering",
            label=offering.label,
            phrase=offering.phrase,
            role="offering",
            attrs={"comforts": offering.comforts},
            tags=set(offering.tags),
        )
    )

    world.facts.update(
        origin=origin,
        place_cfg=place,
        creature_cfg=creature,
        offering_cfg=offering,
        helper_cfg=helper,
        hero=hero,
        elder=elder,
        village=village,
        place=place_ent,
        creature=creature_ent,
        ending=ending_of(
            StoryParams(
                origin=origin.id,
                place=place.id,
                creature=creature.id,
                offering=offering.id,
                helper=helper.id,
                hero_name=hero_name,
                hero_gender=hero_gender,
                elder_type=elder_type,
            )
        ),
    )

    introduce_birth(world, hero, origin)
    world.para()
    trouble_rises(world, hero, creature, place)
    wise_advice(world, hero, helper, creature)
    vow_and_journey(world, hero, offering, helper, place)
    world.para()
    encounter(world, hero, creature, place)
    give_offering(world, hero, offering)
    world.para()
    if world.facts["ending"] == "boon":
        boon_ending(world, hero, creature, place, helper)
    else:
        peace_ending(world, hero, creature, place, helper)

    world.facts.update(
        restored=world.get("place").meters["open"] >= THRESHOLD,
        boon=world.get("hero").meters["boon"] >= THRESHOLD,
        hero_name=hero_name,
        elder_type=elder_type,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    origin = world.facts["origin"]
    place = world.facts["place_cfg"]
    creature = world.facts["creature_cfg"]
    offering = world.facts["offering_cfg"]
    hero = world.facts["hero"]
    return [
        'Write a short folk tale for a 3-to-5-year-old that includes the words "born" and "conquer" and ends happily.',
        f"Tell a folk tale where {hero.label}, {origin.title.lower()}, goes to {place.phrase} and faces {creature.phrase} with {offering.label} instead of a weapon.",
        f"Write a gentle conquering story where the hero wins by understanding what the creature truly needs, and the ending shows the whole village changed for the better.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    origin = world.facts["origin"]
    place = world.facts["place_cfg"]
    creature = world.facts["creature_cfg"]
    offering = world.facts["offering_cfg"]
    helper = world.facts["helper_cfg"]
    elder = world.facts["elder"]
    ending = world.facts["ending"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child called {origin.title.lower()}, and the creature at {place.phrase}. "
            f"The tale also includes {hero.pronoun('possessive')} {elder.label_word}, who helps send {hero.pronoun('object')} on the journey.",
        ),
        (
            f"What happened when {hero.label} was born?",
            f"When {hero.label} was born, {origin.born_line.split('When ', 1)[1]} "
            f"That is why the village remembered {hero.pronoun('object')} as {origin.title.lower()}.",
        ),
        (
            f"What trouble came to the village?",
            f"{creature.phrase.capitalize()} blocked {place.phrase}, so the village could not enjoy {place.want} as it should. "
            f"The trouble mattered because everyday work and comfort in the village depended on that place.",
        ),
        (
            f"Why did {hero.label} bring {offering.label}?",
            f"{hero.label} brought {offering.label} because {creature.phrase} was really {creature.need}, and that offering could soothe exactly that need. "
            f"The elder's advice pointed toward kindness instead of force.",
        ),
        (
            f"How did {hero.label} conquer the trouble?",
            f"{hero.label} did not conquer by fighting. {hero.pronoun().capitalize()} offered {offering.label}, listened carefully, and the creature softened enough to open the place again.",
        ),
    ]
    if ending == "boon":
        qa.append(
            (
                "What made this ending extra special?",
                f"The ending became extra special because {hero.label}'s nature matched what {creature.phrase} most admired: {origin.virtue}. "
                f"So peace came first, and then the creature gave a gift as a blessing.",
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended happily because {place.phrase} opened again and the whole village could use it once more. "
                f"The final image shows that mercy changed fear into peace.",
            )
        )
    qa.append(
        (
            f"What did {helper.label} do in the story?",
            f"{helper.phrase.capitalize()} came from the elder as a small sign of guidance and courage. "
            f"It did not defeat the creature by itself, but it helped mark the journey as a thoughtful one.",
        )
    )
    return qa


KNOWLEDGE = {
    "giant": [
        (
            "What is a giant in a folk tale?",
            "A giant in a folk tale is a very large person-like creature. Giants are often frightening at first, but stories sometimes reveal that they have feelings and needs too.",
        )
    ],
    "dragon": [
        (
            "What is a dragon in a folk tale?",
            "A dragon in a folk tale is a great magical creature, often linked with mountains, mist, or fire. In many tales, a dragon can be wise or lonely as well as fierce.",
        )
    ],
    "troll": [
        (
            "What is a troll in a folk tale?",
            "A troll in a folk tale is a rough, magical creature often found near bridges, marshes, or stones. Trolls are usually stubborn, but they are not always evil.",
        )
    ],
    "bridge": [
        (
            "Why is a bridge important to a village?",
            "A bridge helps people cross a stream or river safely. If a bridge is blocked, people cannot easily travel, trade, or visit one another.",
        )
    ],
    "spring": [
        (
            "What is a spring?",
            "A spring is a place where fresh water comes up from the ground. People and animals may depend on it for drinking water.",
        )
    ],
    "orchard": [
        (
            "What is an orchard?",
            "An orchard is a place where fruit trees grow in rows. People gather fruit there when it is time for harvest.",
        )
    ],
    "gate": [
        (
            "What is a mountain gate in a tale?",
            "A mountain gate is a narrow opening or marked way into the hills. If it is shut, people may not be able to reach high fields or paths beyond it.",
        )
    ],
    "bread": [
        (
            "Why can sharing bread matter in a story?",
            "Sharing bread shows welcome and care. In many old tales, offering food can calm fear and begin peace.",
        )
    ],
    "song": [
        (
            "Why can music comfort someone?",
            "Music can make a lonely heart feel less alone. A gentle song can show that someone has come in friendship.",
        )
    ],
    "cloak": [
        (
            "What is a cloak for?",
            "A cloak is a warm outer covering worn over the shoulders. It helps keep a person warm in wind or cold weather.",
        )
    ],
    "kindness": [
        (
            "Can kindness conquer a problem?",
            "Sometimes kindness can conquer a problem by calming fear, hunger, or loneliness. It does not work on every problem, but in a folk tale it can change a hard heart.",
        )
    ],
}
KNOWLEDGE_ORDER = ["giant", "dragon", "troll", "bridge", "spring", "orchard", "gate", "bread", "song", "cloak", "kindness"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set(world.facts["creature_cfg"].tags) | set(world.facts["place_cfg"].tags) | set(world.facts["offering_cfg"].tags)
    tags.add("kindness")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(name for (name, *_) in world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    try:
        origin = ORIGINS[params.origin]
        place = PLACES[params.place]
        creature = CREATURES[params.creature]
        offering = OFFERINGS[params.offering]
        helper = HELPERS[params.helper]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from err

    if not place_allows(creature, place) or not offering_works(creature, offering):
        raise StoryError(explain_rejection(place, creature, offering))

    world = tell(
        origin=origin,
        place=place,
        creature=creature,
        offering=offering,
        helper=helper,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        elder_type=params.elder_type,
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


ASP_RULES = r"""
place_allows(P, C) :- place(P), creature(C), allowed(C, P).
offering_works(C, O) :- creature(C), offering(O), need(C, N), comforts(O, N).
valid(P, C, O) :- place_allows(P, C), offering_works(C, O).

ending(Origin, Creature, boon) :- origin(Origin), creature(Creature),
                                  virtue(Origin, V), admires(Creature, V).
ending(Origin, Creature, peace) :- origin(Origin), creature(Creature),
                                   not ending(Origin, Creature, boon).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for oid, origin in ORIGINS.items():
        lines.append(asp.fact("origin", oid))
        lines.append(asp.fact("virtue", oid, origin.virtue))
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid, creature in CREATURES.items():
        lines.append(asp.fact("creature", cid))
        lines.append(asp.fact("need", cid, creature.need))
        lines.append(asp.fact("admires", cid, creature.admires))
        for place_id in sorted(creature.allows):
            lines.append(asp.fact("allowed", cid, place_id))
    for oid, offering in OFFERINGS.items():
        lines.append(asp.fact("offering", oid))
        lines.append(asp.fact("comforts", oid, offering.comforts))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_ending(origin_id: str, creature_id: str) -> str:
    import asp

    extra = "\n".join([asp.fact("chosen_origin", origin_id), asp.fact("chosen_creature", creature_id)])
    show = """
ending_result(E) :- chosen_origin(O), chosen_creature(C), ending(O, C, E).
#show ending_result/1.
"""
    model = asp.one_model(asp_program(extra, show))
    atoms = asp.atoms(model, "ending_result")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    mismatch = []
    for origin_id in ORIGINS:
        for creature_id in CREATURES:
            py_end = "boon" if ORIGINS[origin_id].virtue == CREATURES[creature_id].admires else "peace"
            asp_end = asp_ending(origin_id, creature_id)
            if py_end != asp_end:
                mismatch.append((origin_id, creature_id, py_end, asp_end))
    if not mismatch:
        print("OK: ending model matches for all origin/creature pairs.")
    else:
        rc = 1
        print("MISMATCH in ending model:")
        for row in mismatch:
            print("  ", row)

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story.")
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=False, qa=True)
        if "born" not in sample.story.lower() or "conquer" not in sample.story.lower():
            raise StoryError("Smoke test story is missing required seed words.")
        print("OK: smoke test story generation and emit() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(123))
        default_sample = generate(default_params)
        if not default_sample.story.strip():
            raise StoryError("Default generation produced empty text.")
        print("OK: default random generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show ending/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, creature, offering) combos:\n")
        for place_id, creature_id, offering_id in combos:
            print(f"  {place_id:8} {creature_id:8} {offering_id}")
        print("\norigin/creature ending kinds:\n")
        for origin_id in sorted(ORIGINS):
            for creature_id in sorted(CREATURES):
                print(f"  {origin_id:10} {creature_id:8} -> {asp_ending(origin_id, creature_id)}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.hero_name}: {p.creature} at {p.place} with {p.offering} ({ending_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
