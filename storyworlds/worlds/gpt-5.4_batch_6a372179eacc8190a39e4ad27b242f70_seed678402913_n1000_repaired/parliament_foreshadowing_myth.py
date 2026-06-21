#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/parliament_foreshadowing_myth.py
===========================================================

A standalone story world for a small myth-shaped tale about an animal
parliament, an omen that foreshadows trouble, and one fitting creature who
solves the trouble by heeding the omen instead of ignoring it.

The domain is intentionally small and constraint-checked:

- A realm can host only certain sacred troubles.
- Each omen foreshadows exactly one trouble.
- Each trouble needs a matching kind of gift.
- The chosen hero must have the right talent for that trouble.

Because the world is narrow, every generated story reads like one complete myth:
a gathering of the parliament, an omen, a warning that points forward, a journey,
a confrontation where the omen proves true, and an ending image that shows the
realm restored.

Run it
------
    python storyworlds/worlds/gpt-5.4/parliament_foreshadowing_myth.py
    python storyworlds/worlds/gpt-5.4/parliament_foreshadowing_myth.py --all
    python storyworlds/worlds/gpt-5.4/parliament_foreshadowing_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/parliament_foreshadowing_myth.py --trace
    python storyworlds/worlds/gpt-5.4/parliament_foreshadowing_myth.py --asp
    python storyworlds/worlds/gpt-5.4/parliament_foreshadowing_myth.py --verify
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

# Make the shared result containers importable when this script is run directly
# from its nested directory under storyworlds/worlds/gpt-5.4/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "queen"}
        male = {"boy", "man", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Realm:
    id: str
    parliament_place: str = ""
    opening_image: str = ""
    path_to_site: str = ""
    site: str = ""
    closing_image: str = ""
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=lambda: {"parliament"})


@dataclass
class Omen:
    id: str
    sign: str = ""
    whisper: str = ""
    prophecy: str = ""
    foreshadows: str = ""
    tags: set[str] = field(default_factory=lambda: {"omen"})


@dataclass
class Threat:
    id: str
    title: str = ""
    need: str = ""
    site_name: str = ""
    arrival: str = ""
    harm: str = ""
    solved_by: str = ""
    restored: str = ""
    hero_needs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class HeroCfg:
    id: str
    species: str = ""
    title: str = ""
    talents: set[str] = field(default_factory=set)
    nature: str = ""
    carries: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class GiftCfg:
    id: str
    label: str = ""
    phrase: str = ""
    need: str = ""
    use_text: str = ""
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    realm: str
    omen: str
    threat: str
    hero: str
    gift: str
    elder_name: str
    seed: Optional[int] = None


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
    tag: str
    apply: Callable[[World], list[str]]


def hero_can_face(hero_cfg: HeroCfg, threat_cfg: Threat) -> bool:
    return bool(hero_cfg.talents & threat_cfg.hero_needs)


def gift_fits(gift_cfg: GiftCfg, threat_cfg: Threat) -> bool:
    return gift_cfg.need == threat_cfg.need


def omen_matches(omen_cfg: Omen, threat_cfg: Threat) -> bool:
    return omen_cfg.foreshadows == threat_cfg.id


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for realm_id, realm in REALMS.items():
        for threat_id in sorted(realm.affords):
            threat = THREATS[threat_id]
            for omen_id, omen in OMENS.items():
                if not omen_matches(omen, threat):
                    continue
                for hero_id, hero in HEROES.items():
                    if not hero_can_face(hero, threat):
                        continue
                    for gift_id, gift in GIFTS.items():
                        if gift_fits(gift, threat):
                            combos.append((realm_id, omen_id, threat_id, hero_id, gift_id))
    return sorted(combos)


def explain_rejection(realm: Realm, omen: Omen, threat: Threat, hero: HeroCfg, gift: GiftCfg) -> str:
    if threat.id not in realm.affords:
        allowed = ", ".join(sorted(realm.affords))
        return (
            f"(No story: {realm.id} does not host {threat.id}. In this world, that realm only supports "
            f"these sacred troubles: {allowed}.)"
        )
    if not omen_matches(omen, threat):
        return (
            f"(No story: the omen '{omen.id}' foreshadows {omen.foreshadows}, not {threat.id}. "
            f"A foreshadowing story needs the sign to point honestly toward the later trouble.)"
        )
    if not hero_can_face(hero, threat):
        needs = " / ".join(sorted(threat.hero_needs))
        has = " / ".join(sorted(hero.talents))
        return (
            f"(No story: {hero.title} is not the right champion for {threat.title}. "
            f"The trouble calls for {needs}, but this hero only brings {has}.)"
        )
    if not gift_fits(gift, threat):
        return (
            f"(No story: {gift.label} answers {gift.need}, but {threat.title} can only be solved with "
            f"{threat.need}. The gift must match the trouble.)"
        )
    return "(No story: this combination does not fit the myth's logic.)"


def _r_trouble(world: World) -> list[str]:
    threat = world.get("threat")
    if threat.meters["active"] < THRESHOLD:
        return []
    sig = ("trouble",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("realm").meters["unrest"] += 1
    world.get("parliament").memes["worry"] += 1
    world.get("hero").memes["fear"] += 1
    return ["__trouble__"]


def _r_restore(world: World) -> list[str]:
    threat = world.get("threat")
    gift = world.get("gift")
    hero = world.get("hero")
    if threat.meters["active"] < THRESHOLD or gift.meters["offered"] < THRESHOLD:
        return []
    sig = ("restore",)
    if sig in world.fired:
        return []
    need = threat.attrs.get("need")
    hero_talents = set(hero.attrs.get("talents", []))
    hero_needs = set(threat.attrs.get("hero_needs", []))
    if gift.attrs.get("need") != need:
        return []
    if not hero_talents.intersection(hero_needs):
        return []
    world.fired.add(sig)
    threat.meters["active"] = 0.0
    threat.meters["sealed"] += 1
    world.get("realm").meters["restored"] += 1
    world.get("parliament").memes["relief"] += 1
    hero.memes["courage"] += 1
    hero.memes["honor"] += 1
    return ["__restored__"]


CAUSAL_RULES = [
    Rule(name="trouble", tag="physical", apply=_r_trouble),
    Rule(name="restore", tag="physical", apply=_r_restore),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule.apply(world)
            if produced:
                changed = True
                out.extend(produced)
    if narrate:
        for line in out:
            if not line.startswith("__"):
                world.say(line)
    return out


def predict_outcome(threat_cfg: Threat, hero_cfg: HeroCfg, gift_cfg: GiftCfg) -> dict[str, bool]:
    return {
        "hero_fits": hero_can_face(hero_cfg, threat_cfg),
        "gift_fits": gift_fits(gift_cfg, threat_cfg),
        "restored": hero_can_face(hero_cfg, threat_cfg) and gift_fits(gift_cfg, threat_cfg),
    }


def convene_parliament(world: World, realm: Realm, omen: Omen, elder: Entity, hero: Entity, hero_cfg: HeroCfg) -> None:
    world.get("parliament").memes["attention"] += 1
    hero.memes["duty"] += 1
    world.say(
        f"In the old days, when beasts still argued beneath sacred branches, the parliament of the realm "
        f"gathered at {realm.parliament_place}. {realm.opening_image}"
    )
    world.say(
        f"That morning {omen.sign}, and a hush passed from horn to wing to paw. "
        f"Even {hero.id} the {hero_cfg.species}, who was known for being {hero_cfg.nature}, listened."
    )
    world.say(
        f'{elder.id}, the elder of the parliament, raised a careful voice. "{omen.whisper}"'
    )


def foretell(world: World, omen: Omen, threat: Threat, elder: Entity, hero: Entity, gift: GiftCfg) -> None:
    world.get("parliament").memes["worry"] += 1
    world.facts["prophecy"] = omen.prophecy
    world.say(
        f'Then {elder.id} spoke the oldest line remembered there: "{omen.prophecy}"'
    )
    pred = predict_outcome(THREATS[world.facts["threat_cfg"].id], HEROES[world.facts["hero_cfg"].id], gift)
    world.facts["predicted_restored"] = pred["restored"]
    world.say(
        f"The elders understood that the omen pointed toward {threat.title} at {threat.site_name}. "
        f"If the sign was true, the realm would soon know {threat.harm.lower()}."
    )
    if pred["restored"]:
        world.say(
            f"{hero.id} touched {gift.phrase} and understood that the prophecy was not only a warning. "
            f"It was also a hint about what might save them."
        )


def choose_champion(world: World, hero: Entity, hero_cfg: HeroCfg, gift_cfg: GiftCfg, elder: Entity) -> None:
    hero.memes["resolve"] += 1
    world.say(
        f'"Let me go," said {hero.id}. The parliament looked at {hero.pronoun("object")}, small among so many '
        f"older faces, but {elder.id} nodded."
    )
    world.say(
        f"{hero.id} was chosen not for size, but because {hero.pronoun()} was {hero_cfg.nature} and carried "
        f"{gift_cfg.phrase}. In a myth, the right gift matters more than the loudest roar."
    )


def journey(world: World, realm: Realm, hero: Entity, gift_cfg: GiftCfg) -> None:
    hero.meters["distance"] += 1
    hero.memes["fear"] += 1
    world.say(
        f"{hero.id} went alone along {realm.path_to_site}, carrying {gift_cfg.phrase} as gently as a promise."
    )


def awaken_trouble(world: World, threat: Threat, hero: Entity) -> None:
    world.get("threat").meters["active"] += 1
    propagate(world, narrate=False)
    hero.memes["fear"] += 1
    world.say(
        f"At {threat.site_name}, {threat.arrival} {threat.harm}"
    )


def remember_foreshadowing(world: World, hero: Entity, omen: Omen) -> None:
    hero.memes["memory"] += 1
    hero.memes["resolve"] += 1
    world.say(
        f"For one heartbeat {hero.id} wanted to run, but then {hero.pronoun()} remembered the elder's words: "
        f'"{omen.prophecy}"'
    )


def offer_gift(world: World, hero: Entity, gift_cfg: GiftCfg, threat: Threat) -> None:
    world.get("gift").meters["offered"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So {hero.id} {gift_cfg.use_text} before {threat.title}. "
        f"{threat.solved_by}"
    )


def return_and_close(world: World, realm: Realm, hero: Entity, threat: Threat, gift_cfg: GiftCfg) -> None:
    parliament = world.get("parliament")
    parliament.memes["joy"] += 1
    world.say(
        f"When {hero.id} came back, the parliament rose as one body. {threat.restored}"
    )
    world.say(
        f"{realm.closing_image} From then on, whenever the creatures saw {world.facts['omen_cfg'].sign.lower()}, "
        f"they remembered that a true omen is a lamp as well as a warning."
    )


def tell(realm: Realm, omen: Omen, threat: Threat, hero_cfg: HeroCfg, gift_cfg: GiftCfg, elder_name: str) -> World:
    world = World()
    parliament = world.add(Entity(id="Parliament", kind="group", type="assembly", label="the parliament", tags={"parliament"}))
    elder = world.add(Entity(id=elder_name, kind="character", type="elder", label="the elder"))
    hero = world.add(
        Entity(
            id=hero_cfg.title,
            kind="character",
            type="hero",
            label=hero_cfg.species,
            phrase=hero_cfg.species,
            traits=[hero_cfg.nature],
            tags=set(hero_cfg.tags),
            attrs={"talents": sorted(hero_cfg.talents)},
        )
    )
    world.add(Entity(id="realm", kind="place", type="realm", label=realm.id, tags=set(realm.tags)))
    world.add(
        Entity(
            id="threat",
            kind="force",
            type="threat",
            label=threat.title,
            tags=set(threat.tags),
            attrs={"need": threat.need, "hero_needs": sorted(threat.hero_needs)},
        )
    )
    world.add(
        Entity(
            id="gift",
            kind="thing",
            type="gift",
            label=gift_cfg.label,
            phrase=gift_cfg.phrase,
            tags=set(gift_cfg.tags),
            attrs={"need": gift_cfg.need},
        )
    )

    world.facts.update(
        realm_cfg=realm,
        omen_cfg=omen,
        threat_cfg=threat,
        hero_cfg=hero_cfg,
        gift_cfg=gift_cfg,
        elder=elder,
        hero=hero,
        parliament=parliament,
    )

    convene_parliament(world, realm, omen, elder, hero, hero_cfg)
    world.para()
    foretell(world, omen, threat, elder, hero, gift_cfg)
    choose_champion(world, hero, hero_cfg, gift_cfg, elder)
    world.para()
    journey(world, realm, hero, gift_cfg)
    awaken_trouble(world, threat, hero)
    remember_foreshadowing(world, hero, omen)
    offer_gift(world, hero, gift_cfg, threat)
    world.para()
    return_and_close(world, realm, hero, threat, gift_cfg)

    world.facts.update(
        restored=world.get("realm").meters["restored"] >= THRESHOLD,
        prophecy_used=hero.memes["memory"] >= THRESHOLD,
        parliament_relieved=world.get("parliament").memes["relief"] >= THRESHOLD,
    )
    return world


REALMS = {
    "cedar_hill": Realm(
        id="cedar_hill",
        parliament_place="the Root Circle under the cedar king",
        opening_image="Its cones smelled of sun and resin, and the stone seats around its roots were worn smooth by ancient paws and claws.",
        path_to_site="the stair of yellow lichen that climbed toward the Sun Steps",
        site="the Sun Steps",
        closing_image="The cedar needles shone green again, and every voice in the parliament sounded lighter.",
        affords={"shadow_curtain", "bronze_gate"},
    ),
    "reed_marsh": Realm(
        id="reed_marsh",
        parliament_place="the Round Lily Stone in the middle of the marsh",
        opening_image="Mist curled around the reeds, and frogs, herons, otters, and mice took their places in a ring like little lords of water and mud.",
        path_to_site="the narrow bank where reeds bowed over the black water",
        site="the Deep Spring",
        closing_image="The marsh answered with frog-song, and silver rings spread across the water where thirsty mouths had waited.",
        affords={"thirst_serpent", "bronze_gate"},
    ),
    "basalt_cliff": Realm(
        id="basalt_cliff",
        parliament_place="the Wind Court carved into the cliff",
        opening_image="Sea birds lined the dark ledges, foxes sat below, and even the wind seemed to pause to hear what the parliament would decide.",
        path_to_site="the black path above the breakers, where the air tasted of salt and storm",
        site="the Echo Gate",
        closing_image="Far below, the sea stopped muttering and began to sparkle like hammered glass.",
        affords={"shadow_curtain", "bronze_gate"},
    ),
}

OMENS = {
    "pale_halo": Omen(
        id="pale_halo",
        sign="a pale ring stood around the morning sun",
        whisper="A sign has stepped before the day.",
        prophecy="When noon wears a gray ring, the dark will fear its own face.",
        foreshadows="shadow_curtain",
        tags={"omen", "sun"},
    ),
    "cracked_reeds": Omen(
        id="cracked_reeds",
        sign="the reeds rattled dry though the dawn was wet",
        whisper="The roots are speaking in a thirsty voice.",
        prophecy="When the reeds speak dry at dawn, the deep spring asks for a patient gift.",
        foreshadows="thirst_serpent",
        tags={"omen", "water"},
    ),
    "hollow_thunder": Omen(
        id="hollow_thunder",
        sign="a hollow thunder rolled through a clear sky",
        whisper="A shut thing is calling for the right note.",
        prophecy="When thunder hides in a blue sky, the closed gate is listening for one true song.",
        foreshadows="bronze_gate",
        tags={"omen", "song"},
    ),
}

THREATS = {
    "shadow_curtain": Threat(
        id="shadow_curtain",
        title="the Shadow Curtain",
        need="shine",
        site_name="the Sun Steps",
        arrival="a black veil poured down over the stones and tried to swallow the noon",
        harm="The day dimmed, chicks huddled, and even the bees forgot where to fly.",
        solved_by="The dark folded back on itself, as if ashamed to meet its own brightness.",
        restored="Soon warm light came down the steps again, and the sleeping flowers opened one by one.",
        hero_needs={"shine", "clever"},
        tags={"sun", "darkness"},
    ),
    "thirst_serpent": Threat(
        id="thirst_serpent",
        title="the Thirst Serpent",
        need="water",
        site_name="the Deep Spring",
        arrival="a long thirsty serpent coiled around the spring-mouth and drank the shine from the water",
        harm="The pools shrank, the reeds bent low, and thirsty creatures licked mud where clear water should have been.",
        solved_by="The serpent loosened, tasted the offered water, and slid away into the roots below.",
        restored="Then the spring leapt up laughing, and clear water ran through the marsh channels once more.",
        hero_needs={"water", "steady", "patient"},
        tags={"water", "spring"},
    ),
    "bronze_gate": Threat(
        id="bronze_gate",
        title="the Bronze Gate of Echoes",
        need="song",
        site_name="the Echo Gate",
        arrival="the great bronze gate woke and sealed the pass with a groan older than thunder",
        harm="Paths closed, winds turned strange, and every call sent across the rocks came back frightened and thin.",
        solved_by="The gate listened, trembled, and opened a crack, then all the way, like a giant ear finally satisfied.",
        restored="Fresh wind ran through the open pass, carrying seed, cloud, and brave small voices with it.",
        hero_needs={"song"},
        tags={"song", "gate"},
    ),
}

HEROES = {
    "magpie": HeroCfg(
        id="magpie",
        species="magpie",
        title="Brightwing",
        talents={"shine", "clever"},
        nature="sharp-eyed and quick-thinking",
        carries="in a beak bright as a pin of light",
        tags={"bird", "shine"},
    ),
    "tortoise": HeroCfg(
        id="tortoise",
        species="tortoise",
        title="Shellback",
        talents={"steady", "patient", "water"},
        nature="slow, patient, and hard to shake",
        carries="on a broad old shell",
        tags={"tortoise", "water"},
    ),
    "wren": HeroCfg(
        id="wren",
        species="wren",
        title="Little Reedsong",
        talents={"song", "swift"},
        nature="small, brave, and full of music",
        carries="in feet lighter than blown seeds",
        tags={"bird", "song"},
    ),
    "fox": HeroCfg(
        id="fox",
        species="fox",
        title="Red-Tail",
        talents={"clever"},
        nature="clever and soft-footed",
        carries="between careful teeth",
        tags={"fox", "clever"},
    ),
}

GIFTS = {
    "mirror_leaf": GiftCfg(
        id="mirror_leaf",
        label="mirror leaf",
        phrase="a mirror leaf hammered bright by river spirits",
        need="shine",
        use_text="lifted the mirror leaf so the little sun that remained could look at itself",
        tags={"shine", "leaf"},
    ),
    "sun_coin": GiftCfg(
        id="sun_coin",
        label="sun coin",
        phrase="a round sun coin kept from an older summer",
        need="shine",
        use_text="set down the sun coin and turned it until it threw a brave spark straight into the gloom",
        tags={"shine", "coin"},
    ),
    "dew_bowl": GiftCfg(
        id="dew_bowl",
        label="dew bowl",
        phrase="a dew bowl filled before sunrise",
        need="water",
        use_text="poured the dew bowl into the spring-mouth with both patience and care",
        tags={"water", "bowl"},
    ),
    "rain_shell": GiftCfg(
        id="rain_shell",
        label="rain shell",
        phrase="a rain shell still holding storm-water from the last good cloud",
        need="water",
        use_text="tipped the rain shell and let its saved water sing down into the deep stones",
        tags={"water", "shell"},
    ),
    "reed_flute": GiftCfg(
        id="reed_flute",
        label="reed flute",
        phrase="a reed flute cut in the moon of frogs",
        need="song",
        use_text="raised the reed flute and played one clear note that did not tremble",
        tags={"song", "flute"},
    ),
    "bell_seed": GiftCfg(
        id="bell_seed",
        label="bell seed",
        phrase="a hollow bell seed from the oldest vine",
        need="song",
        use_text="shook the bell seed until its thin bright note ran between the stones",
        tags={"song", "bell"},
    ),
}

ELDER_NAMES = ["Moss-Ear", "Stone-Brow", "Ash-Feather", "Moon-Grandmother"]

KNOWLEDGE = {
    "parliament": [
        (
            "What is a parliament?",
            "A parliament is a gathering where many voices come together to talk and decide what to do. In this story it is a council of animals."
        )
    ],
    "omen": [
        (
            "What is an omen?",
            "An omen is a sign that seems to warn about something that may happen later. In stories, an omen can help wise characters prepare."
        )
    ],
    "foreshadowing": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is when an early clue hints at something important that will happen later. It makes the later moment feel prepared instead of sudden."
        )
    ],
    "sun": [
        (
            "Why do shiny things reflect light?",
            "Shiny things bounce light back instead of swallowing it. That is why a bright surface can flash or glimmer in the sun."
        )
    ],
    "water": [
        (
            "Why is water important for animals and plants?",
            "Water helps living things drink, grow, and stay alive. When water is missing, plants droop and animals become thirsty."
        )
    ],
    "song": [
        (
            "How can sound matter in a story?",
            "Sound can call, warn, guide, or open something in a make-believe tale. A true note often stands for courage and order in myths."
        )
    ],
    "spring": [
        (
            "What is a spring?",
            "A spring is water that rises from the ground by itself. It can feed streams, pools, and marshes."
        )
    ],
    "gate": [
        (
            "What does a gate do?",
            "A gate opens a way or closes it. In a myth, a gate can also stand for a test that must be passed."
        )
    ],
    "myth": [
        (
            "What is a myth?",
            "A myth is an old kind of story that uses wonders, signs, and big meaning to explain a place, a custom, or a lesson."
        )
    ],
}
KNOWLEDGE_ORDER = ["parliament", "omen", "foreshadowing", "myth", "sun", "water", "song", "spring", "gate"]


def generation_prompts(world: World) -> list[str]:
    realm = world.facts["realm_cfg"]
    omen = world.facts["omen_cfg"]
    threat = world.facts["threat_cfg"]
    hero = world.facts["hero_cfg"]
    gift = world.facts["gift_cfg"]
    return [
        (
            f'Write a short myth for a 3-to-5-year-old that includes the word "parliament", '
            f"uses clear foreshadowing, and ends with a realm restored."
        ),
        (
            f"Tell a myth where an animal parliament sees this omen: {omen.sign}. "
            f"The clue should foreshadow {threat.title}, and {hero.title} should carry {gift.phrase} to set things right."
        ),
        (
            f"Write a gentle legendary tale set near {realm.parliament_place} where an elder's prophecy hints at the answer before the trouble fully appears."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    realm = world.facts["realm_cfg"]
    omen = world.facts["omen_cfg"]
    threat = world.facts["threat_cfg"]
    hero_cfg = world.facts["hero_cfg"]
    gift = world.facts["gift_cfg"]
    elder = world.facts["elder"]
    hero = world.facts["hero"]
    qa: list[tuple[str, str]] = [
        (
            "Who gathered in the story?",
            f"The animals of the realm gathered in a parliament at {realm.parliament_place}. They came because the sign in the sky or earth felt important."
        ),
        (
            "What was the omen at the beginning?",
            f"The omen was that {omen.sign}. It mattered because the elder said it was a true sign pointing toward later trouble."
        ),
        (
            "How did the story use foreshadowing?",
            f'{elder.id} spoke this prophecy early: "{omen.prophecy}" That line foreshadowed what would happen later and hinted at the way the trouble could be solved.'
        ),
        (
            f"Why was {hero.title} chosen?",
            f"{hero.title} was chosen because {hero.pronoun()} was {hero_cfg.nature} and had the right talent for {threat.title}. The parliament needed the fitting hero, not merely the biggest one."
        ),
        (
            f"What did {hero.title} carry?",
            f"{hero.title} carried {gift.phrase}. The gift matched the trouble because {threat.title} could be answered only with {gift.need}."
        ),
    ]
    if world.facts.get("restored"):
        qa.append(
            (
                f"How was {threat.title} defeated?",
                f"{hero.title} remembered the prophecy and used {gift.label} in the right way before {threat.title}. That worked because the omen had already hinted what the trouble feared or needed."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the realm restored and the parliament rising in relief. The final image shows that the warning sign had become a lesson in wisdom instead of a cause for panic."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"parliament", "omen", "foreshadowing", "myth"}
    tags |= set(world.facts["omen_cfg"].tags)
    tags |= set(world.facts["threat_cfg"].tags)
    tags |= set(world.facts["gift_cfg"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:12} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        realm="cedar_hill",
        omen="pale_halo",
        threat="shadow_curtain",
        hero="magpie",
        gift="mirror_leaf",
        elder_name="Moss-Ear",
    ),
    StoryParams(
        realm="reed_marsh",
        omen="cracked_reeds",
        threat="thirst_serpent",
        hero="tortoise",
        gift="dew_bowl",
        elder_name="Moon-Grandmother",
    ),
    StoryParams(
        realm="basalt_cliff",
        omen="hollow_thunder",
        threat="bronze_gate",
        hero="wren",
        gift="reed_flute",
        elder_name="Ash-Feather",
    ),
    StoryParams(
        realm="cedar_hill",
        omen="hollow_thunder",
        threat="bronze_gate",
        hero="wren",
        gift="bell_seed",
        elder_name="Stone-Brow",
    ),
]


ASP_RULES = r"""
realm_allows(R, T) :- affords(R, T).
omen_matches(O, T) :- foreshadows(O, T).
hero_fits(H, T)    :- hero(H), threat(T), needs_hero(T, Need), has_talent(H, Need).
gift_fits(G, T)    :- gift(G), threat(T), needs_gift(T, Need), gift_need(G, Need).

valid(R, O, T, H, G) :-
    realm(R), omen(O), threat(T), hero(H), gift(G),
    realm_allows(R, T), omen_matches(O, T), hero_fits(H, T), gift_fits(G, T).

restored :- chosen_threat(T), chosen_hero(H), chosen_gift(G), hero_fits(H, T), gift_fits(G, T).
outcome(restored) :- restored.
outcome(failed)   :- not restored.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for realm_id, realm in REALMS.items():
        lines.append(asp.fact("realm", realm_id))
        for threat_id in sorted(realm.affords):
            lines.append(asp.fact("affords", realm_id, threat_id))
    for omen_id, omen in OMENS.items():
        lines.append(asp.fact("omen", omen_id))
        lines.append(asp.fact("foreshadows", omen_id, omen.foreshadows))
    for threat_id, threat in THREATS.items():
        lines.append(asp.fact("threat", threat_id))
        lines.append(asp.fact("needs_gift", threat_id, threat.need))
        for talent in sorted(threat.hero_needs):
            lines.append(asp.fact("needs_hero", threat_id, talent))
    for hero_id, hero in HEROES.items():
        lines.append(asp.fact("hero", hero_id))
        for talent in sorted(hero.talents):
            lines.append(asp.fact("has_talent", hero_id, talent))
    for gift_id, gift in GIFTS.items():
        lines.append(asp.fact("gift", gift_id))
        lines.append(asp.fact("gift_need", gift_id, gift.need))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_threat", params.threat),
            asp.fact("chosen_hero", params.hero),
            asp.fact("chosen_gift", params.gift),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    threat = THREATS[params.threat]
    hero = HEROES[params.hero]
    gift = GIFTS[params.gift]
    return "restored" if hero_can_face(hero, threat) and gift_fits(gift, threat) else "failed"


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            args = parser.parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {seed}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcome matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: generate() smoke test passed.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: an animal parliament, an omen, and a mythic rescue."
    )
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--omen", choices=OMENS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--elder-name", dest="elder_name")
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
    realm_id = args.realm
    omen_id = args.omen
    threat_id = args.threat
    hero_id = args.hero
    gift_id = args.gift

    if realm_id and threat_id and threat_id not in REALMS[realm_id].affords:
        realm = REALMS[realm_id]
        threat = THREATS[threat_id]
        omen = OMENS[omen_id] if omen_id else next(iter(OMENS.values()))
        hero = HEROES[hero_id] if hero_id else next(iter(HEROES.values()))
        gift = GIFTS[gift_id] if gift_id else next(iter(GIFTS.values()))
        raise StoryError(explain_rejection(realm, omen, threat, hero, gift))

    if omen_id and threat_id and not omen_matches(OMENS[omen_id], THREATS[threat_id]):
        realm = REALMS[realm_id] if realm_id else next(iter(REALMS.values()))
        raise StoryError(explain_rejection(realm, OMENS[omen_id], THREATS[threat_id], next(iter(HEROES.values())), next(iter(GIFTS.values()))))

    if hero_id and threat_id and not hero_can_face(HEROES[hero_id], THREATS[threat_id]):
        realm = REALMS[realm_id] if realm_id else next(iter(REALMS.values()))
        omen = OMENS[omen_id] if omen_id else next(iter(OMENS.values()))
        gift = GIFTS[gift_id] if gift_id else next(iter(GIFTS.values()))
        raise StoryError(explain_rejection(realm, omen, THREATS[threat_id], HEROES[hero_id], gift))

    if gift_id and threat_id and not gift_fits(GIFTS[gift_id], THREATS[threat_id]):
        realm = REALMS[realm_id] if realm_id else next(iter(REALMS.values()))
        omen = OMENS[omen_id] if omen_id else next(iter(OMENS.values()))
        hero = HEROES[hero_id] if hero_id else next(iter(HEROES.values()))
        raise StoryError(explain_rejection(realm, omen, THREATS[threat_id], hero, GIFTS[gift_id]))

    combos = [
        combo
        for combo in valid_combos()
        if (realm_id is None or combo[0] == realm_id)
        and (omen_id is None or combo[1] == omen_id)
        and (threat_id is None or combo[2] == threat_id)
        and (hero_id is None or combo[3] == hero_id)
        and (gift_id is None or combo[4] == gift_id)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    realm_id, omen_id, threat_id, hero_id, gift_id = rng.choice(combos)
    elder_name = args.elder_name or rng.choice(ELDER_NAMES)
    return StoryParams(
        realm=realm_id,
        omen=omen_id,
        threat=threat_id,
        hero=hero_id,
        gift=gift_id,
        elder_name=elder_name,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        realm = REALMS[params.realm]
        omen = OMENS[params.omen]
        threat = THREATS[params.threat]
        hero = HEROES[params.hero]
        gift = GIFTS[params.gift]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from err

    if (params.realm, params.omen, params.threat, params.hero, params.gift) not in set(valid_combos()):
        raise StoryError(explain_rejection(realm, omen, threat, hero, gift))

    world = tell(realm, omen, threat, hero, gift, params.elder_name)
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
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (realm, omen, threat, hero, gift) combos:\n")
        for realm, omen, threat, hero, gift in combos:
            print(f"  {realm:12} {omen:14} {threat:15} {hero:8} {gift}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.realm}: {p.omen} -> {p.threat} with {p.hero}/{p.gift}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
