#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/emergency_clamp_starfish_friendship_quest_transformation_animal.py
======================================================================================================

A small animal-story world about an emergency, a clamp, a starfish, and the
friendship that turns a scary quest into a gentle transformation.

Premise:
- A young sea animal friend sees an emergency at the tidepool reef.
- A starfish is stuck under a clamp.
- The friends go on a short quest to free it.
- The hero changes from worried to brave, and the starfish changes from stuck
  to safe and smiling.

The world is deliberately compact and classical: a few typed entities, physical
meters, emotional memes, and a tiny forward simulation that drives the prose.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT) and not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    stuck: bool = False
    transformable: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"octopus", "seal", "otter", "crab", "fish", "starfish", "turtle"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str = "the tidepool reef"
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    danger: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    used_for: set[str]
    prep: str
    tail: str


@dataclass(frozen=True)
class NarrativeArc:
    id: str
    opening: str
    emergency: str
    obstacle: str
    clue: str
    friend_choice: str
    hero_action: str
    release: str
    transformation: str
    ending: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.facts = dict(self.facts)
        return clone


def _r_clamp_hurts(world: World) -> list[str]:
    out: list[str] = []
    clamp = world.entities.get("clamp")
    if not clamp or clamp.carried_by is None:
        return out
    carrier = world.get(clamp.carried_by)
    if carrier.memes.get("worry", 0) < THRESHOLD:
        return out
    sig = ("clamp_hurts", carrier.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    carrier.memes["stress"] = carrier.memes.get("stress", 0) + 1
    out.append(f"For one breath the clamp resisted, and {carrier.id} felt the worry pinch harder.")
    return out


def _r_free_starfish(world: World) -> list[str]:
    out: list[str] = []
    star = world.entities.get("starfish")
    clamp = world.entities.get("clamp")
    if not star or not clamp:
        return out
    if not star.stuck:
        return out
    helper = world.facts.get("hero")
    if not helper:
        return out
    if helper.memes.get("brave", 0) < THRESHOLD:
        return out
    if helper.meters.get("tool_use", 0) < THRESHOLD:
        return out
    sig = ("free_starfish",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    star.stuck = False
    star.meters["safe"] = star.meters.get("safe", 0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0) + 1
    arc = world.facts["arc"]
    out.append(arc.release)
    return out


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    star = world.facts.get("star")
    if not hero or not star:
        return out
    if hero.memes.get("brave", 0) < THRESHOLD or star.meters.get("safe", 0) < THRESHOLD:
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["confidence"] = hero.memes.get("confidence", 0) + 1
    star.meters["glow"] = star.meters.get("glow", 0) + 1
    out.append(world.facts["arc"].transformation.format(hero=hero.id))
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    all_sents: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_clamp_hurts, _r_free_starfish, _r_transformation):
            sents = rule(world)
            if sents:
                changed = True
                all_sents.extend(sents)
    if narrate:
        for s in all_sents:
            world.say(s)
    return all_sents


SETTING = Setting(place="the tidepool reef", affords={"quest", "emergency", "transformation"})

QUESTS = {
    "rescue": Quest(
        id="rescue",
        verb="help the starfish",
        gerund="helping the starfish",
        rush="rush to the reef",
        danger="the clamp might hurt the starfish",
        keyword="starfish",
        tags={"emergency", "starfish", "clamp", "quest", "friendship", "transformation"},
    )
}

TOOLS = {
    "shell_wedge": Tool(
        id="shell_wedge",
        label="a smooth shell wedge",
        phrase="a smooth shell wedge",
        helps={"clamp"},
        used_for={"freeing"},
        prep="pick up a smooth shell wedge",
        tail="used the shell wedge to pry the clamp open",
    )
}


ARCS = [
    NarrativeArc(
        "nursery_gate",
        "A spring tide had filled the reef nursery with silver bubbles.",
        "A loose research clamp had snapped around one arm of a young starfish beside the nursery gate.",
        "Every wave rocked the gate and tightened the clamp another click.",
        "A trail of scraped algae showed that the gate must be held still before anyone touched the fastener.",
        "offered to brace the swaying gate, although the deeper water frightened them",
        "slid the shell wedge beneath the clamp and waited for the wave to draw back",
        "With the gate steady, the clamp sprang open and the starfish crept into the quiet nursery.",
        "That patient rescue was a transformation for {hero}: worry became careful courage, not reckless speed.",
        "At sunset, the freed starfish rested among the bubbles while two friends watched the gate swing safely above it.",
    ),
    NarrativeArc(
        "storm_marker",
        "After a night storm, broken marker ropes lay across the tidepool.",
        "A clamp from a marker line had pinned a starfish beneath a flat red float.",
        "Foam hid the clamp each time the friends leaned close.",
        "The float rose on every third wave, leaving one calm breath in which to work.",
        "counted the waves aloud so the rescue would follow a safe rhythm",
        "used the shell wedge only when the third wave lifted the float",
        "On the next count, the clamp released and the starfish paddled clear of the storm rope.",
        "The quest caused a quiet transformation in {hero}, who learned that bravery can listen and time its move.",
        "Three tiny arm prints remained in the wet sand beside the neatly coiled marker rope.",
    ),
    NarrativeArc(
        "telescope_stand",
        "The friends came to chart moon pools for the reef animals.",
        "The clamp on an old tide telescope had fallen and trapped a starfish against its wooden stand.",
        "The stand tilted whenever either animal pulled at the clamp.",
        "A dry barnacle patch marked the one leg that needed a counterweight.",
        "dragged a round stone into place and promised not to let the telescope tip",
        "wedged the clamp apart while keeping one paw against the balanced stand",
        "The balanced stand held; the clamp opened, and the starfish slid down a ribbon of water.",
        "For {hero}, the transformation was from guessing alone to trusting a friend's practical idea.",
        "That night the telescope pointed at the moon, with the starfish safe in the pool below its reflection.",
    ),
    NarrativeArc(
        "rescue_basket",
        "A floating rescue basket bumped against the reef after drifting from the harbor.",
        "Its metal clamp had caught a starfish together with a twist of fishing line.",
        "Pulling the line made the starfish slide toward a sharp shell edge.",
        "The line went slack whenever the basket was turned toward shore.",
        "turned the heavy basket while calling clear directions to the hero",
        "kept the line loose and worked the wedge into the clamp from the safe side",
        "The clamp clicked free, and the starfish dropped gently into a cup of clear water.",
        "The shared work brought a transformation: {hero} stopped treating help as a weakness and began using it as strength.",
        "They carried the empty basket home while the starfish vanished beneath a waving green frond.",
    ),
    NarrativeArc(
        "festival_lantern",
        "The reef animals were hanging shell lanterns for the first low-tide festival.",
        "One lantern clamp slipped from its cord and closed over a starfish near the dance pool.",
        "The lantern kept spinning, putting the trapped arm under strain.",
        "Its shadow paused whenever the cord was caught against a forked rock.",
        "caught the cord and gave up a place in the parade to keep it from twisting",
        "crawled beneath the quiet lantern and eased the clamp open with the wedge",
        "Once the cord stopped turning, the clamp loosened and the starfish unfurled all five arms.",
        "Kindness made the transformation in {hero}: being the festival's rescuer mattered more than leading its parade.",
        "The last lantern cast a five-pointed glow around the starfish as the friends danced on opposite sides of the pool.",
    ),
    NarrativeArc(
        "kelp_bridge",
        "The pair set out to repair a kelp bridge used by the smallest shore animals.",
        "Beneath the kelp bridge, a fastening clamp had fallen onto a starfish and tangled itself in two strands.",
        "Cutting either strand would drop the bridge into the channel.",
        "The crossed strands formed a loop that could carry the weight if both ends stayed taut.",
        "held both kelp ends, choosing a sore grip over abandoning the bridge",
        "followed the loop to the clamp and pried its hinge instead of cutting the living kelp",
        "The hinge opened; the starfish floated free, and the woven bridge stayed whole.",
        "The transformation taught {hero} to protect the whole reef while saving one animal in danger.",
        "By evening, the starfish sheltered under the bridge and tiny crabs crossed safely overhead.",
    ),
    NarrativeArc(
        "current_meter",
        "A current meter had begun ringing a warning bell beside the deep pool.",
        "Its clamp had detached and caught a starfish in the narrow channel below.",
        "The rushing water pushed the wedge away each time the hero reached down.",
        "A side channel became still when a broad shell covered its inlet.",
        "swam against the current to place the broad shell over the inlet",
        "entered the newly calm channel and twisted the wedge across the clamp's hinge",
        "In the softened current, the clamp opened and the starfish climbed onto a safe ledge.",
        "The emergency changed {hero}; after the transformation, fear became respect for water and a habit of planning.",
        "The warning bell fell silent, and five starfish arms waved from the ledge like a small good-bye.",
    ),
    NarrativeArc(
        "map_case",
        "The friends were following an old shell map to find a freshwater seep.",
        "At the final marker, the clamp of the map case had trapped a starfish in a rocky crack.",
        "The crack was too narrow for both friends to reach the hinge.",
        "Reflected light on the case revealed a second opening behind the rock.",
        "gave the only lantern shell to the hero and felt along the dark rear passage",
        "guided the wedge toward the hinge by following the friend's tapping signal",
        "A final tap guided the wedge home; the clamp opened and the starfish backed out of the crack.",
        "The quest transformed {hero} from the one who wanted to lead into the one who knew how to listen.",
        "Fresh water beaded on the open map case while the starfish traced a five-armed path across the pool floor.",
    ),
    NarrativeArc(
        "crab_hospital",
        "At the little animal hospital, the friends were delivering clean moss bandages.",
        "An empty supply-box clamp had sprung shut on a starfish volunteer.",
        "A frightened hermit crab crowded the doorway and blocked the shortest route.",
        "The crab calmed when someone spoke softly and showed it the open bandage basket.",
        "comforted the crab and cleared a path instead of rushing past it",
        "knelt beside the supply box and rocked the wedge gently until the clamp relaxed",
        "The clamp relaxed without a snap, and the starfish crawled onto the clean moss.",
        "The transformation made {hero} gentler under pressure: an emergency did not erase anyone else's fear.",
        "The starfish later placed one bright bandage on the empty box, a reminder to mend its clamp.",
    ),
    NarrativeArc(
        "bell_rope",
        "A reef bell announced the safe path home before the tide returned.",
        "The bell-rope clamp had dropped into a pool and pinned a starfish under its brass tongue.",
        "If the rope went loose, the other young animals would lose their warning signal.",
        "A forked branch could hold the rope while the clamp was opened below.",
        "raised the branch and kept the bell sounding for everyone still on the reef",
        "descended beside the starfish and levered the clamp away from the brass tongue",
        "The clamp lifted, the starfish escaped, and the bell continued its steady call.",
        "Responsibility completed {hero}'s transformation from a nervous traveler into a guardian of the path.",
        "As the tide covered the stones, the bell rang above one last star-shaped ripple.",
    ),
    NarrativeArc(
        "science_tag",
        "The two friends volunteered to count animals in the protected tidepool.",
        "A discarded tagging clamp had closed beside a starfish and wedged two of its arms beneath a slate.",
        "Moving the slate first would scrape the starfish against the rough pool floor.",
        "Tiny bubbles escaped from a release notch hidden under the clamp.",
        "held a mirror shell below the water so the hidden notch became visible",
        "aimed the shell wedge at the reflected notch and pressed until the spring yielded",
        "The spring yielded, the slate lifted, and the starfish walked away on all five arms.",
        "Curiosity and care worked a transformation in {hero}, turning a frightened witness into a thoughtful problem-solver.",
        "They drew the five clear arm tracks in their animal-count book and locked the broken clamp away.",
    ),
    NarrativeArc(
        "driftwood_cart",
        "A driftwood cart carried sea grass to animals stranded by the heat.",
        "When one wheel broke, its clamp bounced into a puddle and trapped a starfish at the puddle's edge.",
        "The loaded cart began rolling back toward the rescue place.",
        "A shallow groove beside the wheel was just wide enough for a stone brake.",
        "left the precious sea grass, caught the cart, and kicked a stone into the groove",
        "pressed the shell wedge with all available strength while {friend} held the cart secure",
        "The wheel stopped, the clamp opened, and the starfish slipped into the deeper pool.",
        "The transformation joined courage with friendship: {hero} learned that a quest succeeds when friends divide the danger.",
        "Later, the repaired cart rolled on, leaving a damp five-pointed mark on its lowest plank.",
    ),
]

OPENING_FORMS = [
    "{hero}, a {trait} {animal}, usually explored beside {friend}, a kind {friend_animal}.",
    "Whenever {hero} the {animal} felt unsure, {friend} the {friend_animal} made room for one more brave step.",
    "The tidepool knew {hero} as a {trait} {animal} and {friend} as the friend who always listened.",
    "This animal quest began with {hero} the {animal} and {friend} the {friend_animal} sharing an ordinary morning.",
    "{hero} and {friend} had different strengths, which was exactly why their friendship worked.",
    "Before the emergency, {hero} the {animal} thought every quest had to be completed alone.",
]

DIALOGUES = [
    ('"We need a plan, not a pull," said {friend}.', '"Stay with me while I try it," answered {hero}.'),
    ('"I can handle one part if you handle the other," said {friend}.', '"Then neither of us is alone," said {hero}.'),
    ('"Look at what the water is telling us," {friend} whispered.', '"I see the clue now," replied {hero}.'),
    ('"The starfish needs us to be careful," said {hero}.', '"Careful and together," {friend} agreed.'),
    ('"Being scared does not end the quest," said {friend}.', '"No, but it tells us to think," said {hero}.'),
    ('"First make the danger still," said {hero}.', '"Then open the clamp," replied {friend}.'),
]

GIRL_NAMES = ["Mina", "Luna", "Tia", "Nori", "Kiki"]
BOY_NAMES = ["Pip", "Milo", "Jasper", "Tomo", "Rai"]
ANIMALS = ["octopus", "otter", "seal", "crab", "fish", "turtle"]
TRAITS = ["gentle", "curious", "shy", "brave", "kind", "lively"]


@dataclass
class StoryParams:
    name: str
    animal: str
    trait: str
    friend_name: str
    friend_animal: str
    quest: str
    tool: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal Story world: emergency, clamp, starfish, friendship, quest, transformation."
    )
    ap.add_argument("--name", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--friend-name", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--friend-animal", choices=ANIMALS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    quest = args.quest or "rescue"
    tool = args.tool or "shell_wedge"
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    animal = args.animal or rng.choice(ANIMALS)
    trait = args.trait or rng.choice(TRAITS)
    friend_name = args.friend_name or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name])
    friend_animal = args.friend_animal or rng.choice([a for a in ANIMALS if a != animal])
    return StoryParams(
        name=name,
        animal=animal,
        trait=trait,
        friend_name=friend_name,
        friend_animal=friend_animal,
        quest=quest,
        tool=tool,
    )


def _do_quest(
    world: World,
    hero: Entity,
    friend: Entity,
    star: Entity,
    clamp: Entity,
    tool: Tool,
    arc: NarrativeArc,
    dialogue: tuple[str, str],
    structure: int,
) -> None:
    def names(text: str) -> str:
        return text.format(hero=hero.id, friend=friend.id)

    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.facts.update(
        obstacle=arc.obstacle,
        clue=arc.clue,
        friend_choice=arc.friend_choice,
        hero_action=names(arc.hero_action),
        release=arc.release,
        transformation=arc.transformation.format(hero=hero.id),
        ending=arc.ending,
    )

    if structure == 0:
        world.say(arc.opening)
        world.say(f"Then came the emergency: {arc.emergency}")
        world.say(arc.obstacle)
    elif structure == 1:
        world.say(f"The emergency arrived without warning. {arc.emergency}")
        world.say(arc.opening)
        world.say(f"The first rescue attempt failed. {arc.obstacle}")
    elif structure == 2:
        world.say(arc.opening)
        world.say(f'"A starfish needs help!" cried {hero.id}. {arc.emergency}')
        world.say(f"They paused before touching the clamp. {arc.obstacle}")
    else:
        world.say(f"Something was wrong at {world.setting.place}: {arc.emergency}")
        world.say(arc.opening)
        world.say(f"This would be no simple quest. {arc.obstacle}")

    world.para()
    world.say(dialogue[0].format(hero=hero.id, friend=friend.id))
    world.say(f"They studied the emergency instead of yanking at the clamp. {arc.clue}")
    world.say(
        f"For friendship's sake, {friend.id} {arc.friend_choice}. "
        f"That choice gave {hero.id} time to {tool.prep}."
    )
    world.say(dialogue[1].format(hero=hero.id, friend=friend.id))
    hero.meters["tool_use"] = hero.meters.get("tool_use", 0) + 1
    clamp.carried_by = hero.id
    hero.memes["brave"] = hero.memes.get("brave", 0) + 1
    friend.memes["support"] = friend.memes.get("support", 0) + 1
    world.say(f"Working as a team, {hero.id} {names(arc.hero_action)}.")
    propagate(world, narrate=True)
    clamp.carried_by = None
    world.para()
    if not star.stuck:
        world.say(
            f"{hero.id} thanked {friend.id}. The animal friends understood that their quest had succeeded "
            "because each had chosen a different useful part."
        )
        world.say(arc.ending)
    hero.memes["friendship"] = hero.memes.get("friendship", 0) + 1


def tell(params: StoryParams) -> World:
    seed = params.seed if params.seed is not None else 0
    combination_count = len(ARCS) * len(OPENING_FORMS) * len(DIALOGUES) * 4
    code = (seed * 137) % combination_count
    arc = ARCS[code % len(ARCS)]
    opening_index = (code // len(ARCS)) % len(OPENING_FORMS)
    dialogue_index = (code // (len(ARCS) * len(OPENING_FORMS))) % len(DIALOGUES)
    structure = (code // (len(ARCS) * len(OPENING_FORMS) * len(DIALOGUES))) % 4
    world = World(SETTING)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.animal,
        traits=[params.trait],
        meters={"tool_use": 0.0},
        memes={"worry": 0.0, "brave": 0.0, "friendship": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type=params.friend_animal,
        traits=["kind"],
        memes={"support": 0.0},
    ))
    star = world.add(Entity(
        id="starfish",
        kind="character",
        type="starfish",
        label="starfish",
        stuck=True,
        transformable=True,
        meters={"safe": 0.0, "glow": 0.0},
        memes={"hope": 0.0},
    ))
    clamp = world.add(Entity(
        id="clamp",
        type="clamp",
        label="clamp",
        phrase="the clamp",
        stuck=False,
        carried_by=None,
    ))
    world.facts.update(hero=hero, friend=friend, star=star, clamp=clamp, params=params, arc=arc)
    world.say(
        OPENING_FORMS[opening_index].format(
            hero=hero.id,
            trait=params.trait,
            animal=params.animal,
            friend=friend.id,
            friend_animal=params.friend_animal,
        )
    )
    world.say(
        "Their friendship was about to guide an animal rescue quest involving an emergency, a clamp, "
        "and a starfish toward a real transformation."
    )
    world.para()
    _do_quest(
        world,
        hero,
        friend,
        star,
        clamp,
        TOOLS[params.tool],
        arc,
        DIALOGUES[dialogue_index],
        structure,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    arc = f["arc"]
    return [
        f"Write a short animal story about {hero.id} the {hero.type}, {friend.id} the {friend.type}, "
        f"and the {arc.id.replace('_', ' ')} starfish emergency.",
        f"Tell a friendship quest in which {friend.id} helps {hero.id} understand this clue: {arc.clue}",
        f'Write an Animal Story with the words "emergency", "clamp", and "starfish" that ends in a transformation and this image: {arc.ending}',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    params = f["params"]
    arc = f["arc"]
    first_animal = ("an" if params.animal[0].lower() in "aeiou" else "a") + f" {params.animal}"
    second_animal = ("an" if params.friend_animal[0].lower() in "aeiou" else "a") + f" {params.friend_animal}"
    return [
        QAItem(
            question=f"What caused the starfish emergency that {hero.id} and {friend.id} found?",
            answer=arc.emergency,
        ),
        QAItem(
            question=f"What made the clamp difficult for {hero.id} to open?",
            answer=arc.obstacle,
        ),
        QAItem(
            question=f"What clue helped {hero.id} and {friend.id} form a safe plan?",
            answer=arc.clue,
        ),
        QAItem(
            question=f"What friendship choice did {friend.id} make?",
            answer=f"{friend.id} {arc.friend_choice}.",
        ),
        QAItem(
            question=f"How did {hero.id} complete the rescue?",
            answer=f"{hero.id} {f['hero_action']}. {f['release']}",
        ),
        QAItem(
            question=f"How did the animal quest transform {hero.id}?",
            answer=f["transformation"],
        ),
        QAItem(
            question=f"What final image showed {hero.id} and {friend.id} that the emergency was over?",
            answer=f["ending"],
        ),
        QAItem(
            question=f"What kind of story joined {first_animal} and {second_animal}?",
            answer=f"It was an Animal Story joining {hero.id} the {params.animal} and {friend.id} the {params.friend_animal} in a friendship quest and transformation.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a starfish?",
            answer="A starfish is a sea animal with arms that lives in salt water and moves slowly over rocks.",
        ),
        QAItem(
            question="What is a clamp?",
            answer="A clamp is something that holds tightly, like a tool or fastener that squeezes and keeps things in place.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means caring about another friend, helping them, and staying with them when things are hard.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or task where someone tries to reach a goal, like helping a friend or finding something important.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into a new state, like feeling braver or becoming safe after being stuck.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.stuck:
            bits.append("stuck=True")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def valid_story(params: StoryParams) -> bool:
    return params.quest in QUESTS and params.tool in TOOLS


CURATED = [
    StoryParams(name="Mina", animal="octopus", trait="shy", friend_name="Pip", friend_animal="otter", quest="rescue", tool="shell_wedge", seed=0),
    StoryParams(name="Luna", animal="seal", trait="gentle", friend_name="Rai", friend_animal="turtle", quest="rescue", tool="shell_wedge", seed=1),
    StoryParams(name="Tomo", animal="crab", trait="curious", friend_name="Kiki", friend_animal="fish", quest="rescue", tool="shell_wedge", seed=2),
]


def generate(params: StoryParams) -> StorySample:
    if not valid_story(params):
        raise StoryError("The requested story does not fit this small animal world.")
    world = tell(params)
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


ASP_RULES = r"""
% The Python world is tiny: a rescue story is valid when a quest, tool, and
% emergency all match the registries.
valid_story(N, F, Q, T) :- name(N), friend(F), quest(Q), tool(T), rescue_quest(Q), shell_tool(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for n in GIRL_NAMES + BOY_NAMES:
        lines.append(asp.fact("name", n))
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    lines.append(asp.fact("rescue_quest", "rescue"))
    lines.append(asp.fact("shell_tool", "shell_wedge"))
    for n in GIRL_NAMES + BOY_NAMES:
        lines.append(asp.fact("friend", n))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    py_set = set()
    for n in GIRL_NAMES + BOY_NAMES:
        for f in GIRL_NAMES + BOY_NAMES:
            for q in QUESTS:
                for t in TOOLS:
                    if q == "rescue" and t == "shell_wedge":
                        py_set.add((n, f, q, t))
    if clingo_set == py_set:
        print(f"OK: clingo gate matches python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in clingo:", sorted(clingo_set - py_set))
    print("only in python:", sorted(py_set - clingo_set))
    return 1


def build_story_from_args(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()
    i = 0
    while len(samples) < args.n and i < max(args.n * 50, 50):
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        i += 1
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} valid story combos.")
        for combo in combos[:20]:
            print(combo)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = build_story_from_args(args)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
