#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/llama_repertoire_curiosity_moral_value_rhyming_story.py
==================================================================================

A small storyworld about a curious young llama, a performer's repertoire, and the
moral difference between peeking first and asking first.

The world rebuilds a child-facing rhyming tale shape:

- a llama sees a special box, satchel, or basket full of performance pieces
- curiosity tugs hard
- a wiser owner says to ask before touching
- either the hero asks and is warmly included, or sneaks a peek and causes a spill
- the owner helps repair what can be repaired
- the ending proves the lesson: curiosity shines brightest with courtesy

Run it
------
    python storyworlds/worlds/gpt-5.4/llama_repertoire_curiosity_moral_value_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/llama_repertoire_curiosity_moral_value_rhyming_story.py --venue barn --repertoire song_cards
    python storyworlds/worlds/gpt-5.4/llama_repertoire_curiosity_moral_value_rhyming_story.py --choice sneak --delay 1
    python storyworlds/worlds/gpt-5.4/llama_repertoire_curiosity_moral_value_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/llama_repertoire_curiosity_moral_value_rhyming_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/llama_repertoire_curiosity_moral_value_rhyming_story.py --verify
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

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    portable: bool = False
    paper_light: bool = False
    tippy: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Venue:
    id: str
    place: str
    scene: str
    wind: int
    afford_tags: set[str] = field(default_factory=set)


@dataclass
class Repertoire:
    id: str
    label: str
    phrase: str
    inside_line: str
    item_word: str
    paper_light: bool
    fragility: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Storage:
    id: str
    label: str
    phrase: str
    closure: str
    tippy: bool
    spill_risk: int
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, venue: Venue) -> None:
        self.venue = venue
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
        clone = World(self.venue)
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


def _r_drift(world: World) -> list[str]:
    out: list[str] = []
    venue = world.venue
    storage = world.entities.get("storage")
    repertoire = world.entities.get("repertoire")
    if not storage or not repertoire:
        return out
    if repertoire.meters["spilled"] < THRESHOLD:
        return out
    sig = ("drift", venue.id, repertoire.id)
    if sig in world.fired:
        return out
    if venue.wind > 0 and repertoire.paper_light:
        world.fired.add(sig)
        repertoire.meters["drifting"] += 1
        repertoire.meters["severity"] += venue.wind
        out.append("__drift__")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    repertoire = world.entities.get("repertoire")
    hero = world.entities.get("hero")
    owner = world.entities.get("owner")
    if not repertoire or not hero or not owner:
        return out
    if repertoire.meters["spilled"] < THRESHOLD:
        return out
    sig = ("worry", repertoire.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["shame"] += 1
    hero.memes["fear"] += 1
    owner.memes["concern"] += 1
    out.append("__worry__")
    return out


CAUSAL_RULES = [
    Rule(name="drift", tag="physical", apply=_r_drift),
    Rule(name="worry", tag="social", apply=_r_worry),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


THEMES = {
    "barn": Venue(
        id="barn",
        place="the red barn stage",
        scene="Sunbeams made striped ladders across the floor, and the boards stayed still and warm.",
        wind=0,
        afford_tags={"music", "dance", "show"},
    ),
    "meadow": Venue(
        id="meadow",
        place="the clover meadow",
        scene="Buttercups nodded by the path, and a playful breeze skipped over the grass.",
        wind=1,
        afford_tags={"music", "dance", "show"},
    ),
    "hill": Venue(
        id="hill",
        place="the hilltop fair",
        scene="Bright bunting snapped in the air, and the wind liked to tug at anything light.",
        wind=2,
        afford_tags={"music", "dance", "show"},
    ),
}

REPERTOIRES = {
    "song_cards": Repertoire(
        id="song_cards",
        label="song-card repertoire",
        phrase="a neat song-card repertoire",
        inside_line="Inside were little cards with tunes for humming, strumming, and parade-time drumming.",
        item_word="cards",
        paper_light=True,
        fragility=2,
        tags={"music", "paper", "repertoire", "asking"},
    ),
    "dance_ribbons": Repertoire(
        id="dance_ribbons",
        label="ribbon repertoire",
        phrase="a bright ribbon repertoire",
        inside_line="Inside were loops of ribbon for twirling, swirling, dipping, and whirling.",
        item_word="ribbons",
        paper_light=False,
        fragility=1,
        tags={"dance", "ribbons", "repertoire", "asking"},
    ),
    "rhyme_booklets": Repertoire(
        id="rhyme_booklets",
        label="rhyme repertoire",
        phrase="a tidy rhyme repertoire",
        inside_line="Inside were tiny booklets full of verses for stomping feet and laughing choruses.",
        item_word="booklets",
        paper_light=True,
        fragility=2,
        tags={"music", "paper", "repertoire", "asking", "rhymes"},
    ),
}

STORAGES = {
    "basket": Storage(
        id="basket",
        label="basket",
        phrase="a willow basket",
        closure="with no lid at all",
        tippy=True,
        spill_risk=2,
        supports={"song_cards", "dance_ribbons"},
        tags={"basket"},
    ),
    "satchel": Storage(
        id="satchel",
        label="satchel",
        phrase="a soft satchel",
        closure="with a flap that needed two careful paws",
        tippy=False,
        spill_risk=1,
        supports={"song_cards", "rhyme_booklets"},
        tags={"bag"},
    ),
    "trunk": Storage(
        id="trunk",
        label="trunk",
        phrase="a painted trunk",
        closure="with a snug brass latch",
        tippy=False,
        spill_risk=0,
        supports={"song_cards", "dance_ribbons", "rhyme_booklets"},
        tags={"box"},
    ),
}

RESPONSES = {
    "sort_together": Response(
        id="sort_together",
        sense=3,
        power=2,
        text="gathered the scattered {item_word}s, knelt beside the little mess, and sorted them back into order together",
        fail="tried to gather the blown-about {item_word}s, but too many were already skipping away in the wind",
        qa_text="gathered the scattered pieces and sorted them back together",
        tags={"help", "cleanup"},
    ),
    "clip_and_sort": Response(
        id="clip_and_sort",
        sense=3,
        power=3,
        text="caught the fluttering {item_word}s under a rehearsal cloth, clipped them with wooden pegs, and then sorted them back together",
        fail="spread a cloth and reached for the fluttering {item_word}s, but the wind had already carried too many away",
        qa_text="covered the flying pieces, clipped them down, and sorted them back together",
        tags={"help", "cleanup", "wind"},
    ),
    "shrug": Response(
        id="shrug",
        sense=1,
        power=0,
        text="only shrugged at the mess",
        fail="only shrugged while the pieces kept blowing away",
        qa_text="did nothing useful",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Zuri", "Nora", "Ayla", "Pipa", "Rosa", "Tula"]
BOY_NAMES = ["Paco", "Timo", "Nico", "Bram", "Luca", "Milo", "Oren", "Teo"]
TRAITS = ["polite", "eager", "curious", "careful", "bouncy", "thoughtful"]


def hazard_supported(storage: Storage, repertoire: Repertoire) -> bool:
    return repertoire.id in storage.supports


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def spill_severity(venue: Venue, repertoire: Repertoire, storage: Storage, delay: int) -> int:
    base = storage.spill_risk + delay
    if repertoire.paper_light:
        base += venue.wind
    return base


def is_recovered(response: Response, venue: Venue, repertoire: Repertoire, storage: Storage, delay: int) -> bool:
    return response.power >= spill_severity(venue, repertoire, storage, delay)


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for venue_id in THEMES:
        for repertoire_id, repertoire in REPERTOIRES.items():
            for storage_id, storage in STORAGES.items():
                if hazard_supported(storage, repertoire):
                    out.append((venue_id, repertoire_id, storage_id))
    return out


@dataclass
class StoryParams:
    venue: str
    repertoire: str
    storage: str
    response: str
    hero: str
    hero_gender: str
    owner: str
    owner_gender: str
    elder: str
    trait: str
    choice: str
    delay: int = 0
    seed: Optional[int] = None


def predict_spill(world: World) -> dict:
    sim = world.copy()
    storage = sim.get("storage")
    repertoire = sim.get("repertoire")
    storage.meters["jostled"] += 1
    if storage.tippy or storage.meters["jostled"] >= THRESHOLD:
        repertoire.meters["spilled"] += 1
    propagate(sim, narrate=False)
    return {
        "spilled": repertoire.meters["spilled"] >= THRESHOLD,
        "drifting": repertoire.meters["drifting"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, venue: Venue) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"In {venue.place}, where clover liked to sway, a little llama named {hero.id} skipped through the day. "
        f"{venue.scene}"
    )


def owner_arrives(world: World, owner: Entity, storage: Storage, repertoire: Repertoire) -> None:
    world.say(
        f"Soon {owner.id} came by with {storage.phrase} {storage.closure}. "
        f"It held {repertoire.phrase}, a performer's repertoire for the afternoon show."
    )
    world.say(repertoire.inside_line)


def admire(world: World, hero: Entity, repertoire: Repertoire) -> None:
    world.say(
        f"{hero.id}'s ears stood high with a sparkly glow. "
        f'"May I see your repertoire?" {hero.pronoun()} almost asked, soft and low.'
    )


def tempt(world: World, hero: Entity, owner: Entity, storage: Storage) -> None:
    hero.memes["temptation"] += 1
    world.say(
        f"But {owner.id} had turned to wave at the fiddler by the row, and {storage.label} sat near enough for a quick little peep below."
    )


def warn(world: World, owner: Entity, hero: Entity, elder: Entity, storage: Storage) -> None:
    pred = predict_spill(world)
    world.facts["predicted_spill"] = pred["spilled"]
    world.facts["predicted_drift"] = pred["drifting"]
    hero.memes["hesitation"] += 1
    drift = " and the light pieces could drift" if pred["drifting"] else ""
    world.say(
        f'{elder.id} saw {hero.id} inching near and spoke before the trouble grew. '
        f'"Curious hearts are good," {elder.pronoun()} said, "but asking first is what kind friends do. '
        f'That {storage.label} could tip{drift}, and then the show would need repair, not only ooohs and ahhs in the air."'
    )


def ask_first(world: World, hero: Entity, owner: Entity, repertoire: Repertoire) -> None:
    hero.memes["courtesy"] += 1
    hero.memes["joy"] += 1
    owner.memes["trust"] += 1
    world.say(
        f"So {hero.id} took one breath and chose the brighter part: "
        f'"{owner.id}, may I look?" {hero.pronoun()} asked with an open, gentle heart.'
    )
    world.say(
        f'{owner.id} smiled. "Of course," {owner.pronoun()} said. '
        f'Together they opened the repertoire and picked one happy piece to know.'
    )


def sneak_peek(world: World, hero: Entity, storage: Entity, repertoire: Entity) -> None:
    hero.memes["defiance"] += 1
    storage.meters["jostled"] += 1
    if storage.tippy or storage.meters["jostled"] >= THRESHOLD:
        repertoire.meters["spilled"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But curiosity tugged faster than manners could speak. "
        f"{hero.id} reached one hoof toward the {storage.label} for a tiny sneaky peek."
    )
    if repertoire.meters["spilled"] >= THRESHOLD:
        if repertoire.meters["drifting"] >= THRESHOLD:
            world.say(
                f"Tip-tap, flip-flap -- out flew the {world.facts['repertoire_cfg'].item_word} in a flurry bright and quick, "
                f"and the breeze made some of them dance and flick."
            )
        else:
            world.say(
                f"Tip-tap, clatter-clack -- out slid the {world.facts['repertoire_cfg'].item_word} in a wrinkly track, "
                f"and neat little rows became a mixed-up stack."
            )


def alarm(world: World, owner: Entity, hero: Entity, repertoire: Repertoire) -> None:
    hero.memes["fear"] += 1
    world.say(
        f'{hero.id} froze. "{owner.id}!" {hero.pronoun()} cried. '
        f'"I spilled your {repertoire.label} -- I should have asked before I tried."'
    )


def rescue(world: World, owner: Entity, response: Response, repertoire: Entity, repertoire_cfg: Repertoire) -> None:
    owner.memes["care"] += 1
    hero = world.get("hero")
    repertoire.meters["spilled"] = 0.0
    repertoire.meters["drifting"] = 0.0
    hero.memes["fear"] = 0.0
    body = response.text.format(item_word=repertoire_cfg.item_word)
    world.say(
        f"{owner.id} did not stomp or scold or roar. "
        f"{owner.pronoun().capitalize()} {body}."
    )
    world.say(
        "Little by little the jumble turned neat, and the muddled-up worry grew smaller with each sorted sheet."
    )


def rescue_fail(world: World, owner: Entity, response: Response, repertoire_cfg: Repertoire) -> None:
    hero = world.get("hero")
    owner.memes["care"] += 1
    hero.memes["fear"] += 1
    body = response.fail.format(item_word=repertoire_cfg.item_word)
    world.say(
        f"{owner.id} hurried to help and {body}."
    )
    world.say(
        f"Still, the wind whisked away part of the repertoire, and the afternoon show could not use every piece after all."
    )


def lesson(world: World, elder: Entity, hero: Entity, owner: Entity) -> None:
    hero.memes["lesson"] += 1
    hero.memes["relief"] += 1
    owner.memes["trust"] += 1
    world.say(
        f'Then {elder.id} knelt by {hero.id} and stroked {hero.pronoun("possessive")} woolly neck. '
        f'"Curiosity is a lantern," {elder.pronoun()} said, "but courtesy keeps it in check."'
    )
    world.say(
        f'"Asking first keeps hearts unhurt and treasured things in place. '
        f'And when we make a muddle, helping mend it is part of grace."'
    )


def shared_ending(world: World, hero: Entity, owner: Entity, repertoire: Repertoire) -> None:
    hero.memes["joy"] += 1
    hero.memes["belonging"] += 1
    world.say(
        f"Soon {owner.id} let {hero.id} choose one piece from the repertoire to try. "
        f"They hummed and stepped together under the roomy sky."
    )
    world.say(
        f"And from that day, if wonder made {hero.id}'s bright questions start, "
        f"{hero.pronoun()} asked before touching -- and that made room in every heart."
    )


def mended_ending(world: World, hero: Entity, owner: Entity, repertoire: Repertoire) -> None:
    hero.memes["joy"] += 1
    hero.memes["belonging"] += 1
    world.say(
        f"When the last piece was safe again, {owner.id} still saved a place in line. "
        f'"You may help me choose one number now," {owner.pronoun()} said, "and this time we will choose just fine."'
    )
    world.say(
        f"So the little llama learned with cheeks still warm but eyes still bright: "
        f"ask before touching, help when things go wrong, and turn a stumble right."
    )


def lost_ending(world: World, hero: Entity, owner: Entity, repertoire: Repertoire) -> None:
    hero.memes["lesson"] += 1
    hero.memes["sadness"] += 1
    world.say(
        f"That evening the song was softer and shorter than before, because part of the repertoire had blown beyond the fairground door."
    )
    world.say(
        f"{hero.id} stood close beside {owner.id} and promised, with a quiet sight, "
        f'"Next time I will ask before I touch. Curiosity should walk with what is right."'
    )


def tell(
    venue: Venue,
    repertoire_cfg: Repertoire,
    storage_cfg: Storage,
    response_cfg: Response,
    hero_name: str,
    hero_gender: str,
    owner_name: str,
    owner_gender: str,
    elder_type: str,
    trait: str,
    choice: str,
    delay: int,
) -> World:
    world = World(venue)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        traits=[trait, "llama"],
        label=hero_name,
    ))
    owner = world.add(Entity(
        id=owner_name,
        kind="character",
        type=owner_gender,
        role="owner",
        traits=["patient", "llama"],
        label=owner_name,
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        role="elder",
        label="the elder",
        traits=["gentle"],
    ))
    storage = world.add(Entity(
        id="storage",
        type="storage",
        label=storage_cfg.label,
        phrase=storage_cfg.phrase,
        tippy=storage_cfg.tippy,
        portable=True,
        tags=set(storage_cfg.tags),
    ))
    repertoire = world.add(Entity(
        id="repertoire",
        type="repertoire",
        label=repertoire_cfg.label,
        phrase=repertoire_cfg.phrase,
        paper_light=repertoire_cfg.paper_light,
        tags=set(repertoire_cfg.tags),
    ))

    introduce(world, hero, venue)
    owner_arrives(world, owner, storage_cfg, repertoire_cfg)
    admire(world, hero, repertoire_cfg)

    world.para()
    tempt(world, hero, owner, storage_cfg)
    warn(world, owner, hero, elder, storage_cfg)

    if choice == "ask":
        world.para()
        ask_first(world, hero, owner, repertoire_cfg)
        lesson(world, elder, hero, owner)
        world.para()
        shared_ending(world, hero, owner, repertoire_cfg)
        outcome = "shared"
    else:
        world.para()
        sneak_peek(world, hero, storage, repertoire)
        alarm(world, owner, hero, repertoire_cfg)
        world.para()
        recovered = is_recovered(response_cfg, venue, repertoire_cfg, storage_cfg, delay)
        if recovered:
            rescue(world, owner, response_cfg, repertoire, repertoire_cfg)
            lesson(world, elder, hero, owner)
            world.para()
            mended_ending(world, hero, owner, repertoire_cfg)
            outcome = "mended"
        else:
            rescue_fail(world, owner, response_cfg, repertoire_cfg)
            lesson(world, elder, hero, owner)
            world.para()
            lost_ending(world, hero, owner, repertoire_cfg)
            outcome = "lost"

    world.facts.update(
        hero=hero,
        owner=owner,
        elder=elder,
        venue=venue,
        repertoire_cfg=repertoire_cfg,
        repertoire=repertoire,
        storage_cfg=storage_cfg,
        storage=storage,
        response=response_cfg,
        choice=choice,
        outcome=outcome,
        delay=delay,
        spilled=repertoire.meters["spilled"] >= THRESHOLD or choice == "sneak",
        drifting=world.facts.get("predicted_drift", False),
        recovered=(outcome == "mended"),
    )
    return world


KNOWLEDGE = {
    "repertoire": [(
        "What is a repertoire?",
        "A repertoire is a set of songs, dances, or pieces someone is ready to perform. It is like a practiced collection they can choose from."
    )],
    "asking": [(
        "Why should you ask before touching someone else's things?",
        "Asking shows respect for the other person and their belongings. It also helps you learn any careful way the thing needs to be handled."
    )],
    "paper": [(
        "Why can paper pieces blow away outside?",
        "Paper is light, so moving air can lift it and push it along. A breeze that seems small to you can still carry paper away."
    )],
    "ribbons": [(
        "Why are ribbons easier to pick up than loose paper cards?",
        "Ribbons are softer and heavier than a thin sheet of paper, and they do not flutter as far in the wind. That makes them easier to gather again."
    )],
    "wind": [(
        "What does the wind do to light things?",
        "Wind can nudge, lift, and scatter light things across the ground. That is why people clip papers down on breezy days."
    )],
    "cleanup": [(
        "What should you do if you make a mess by mistake?",
        "Tell the truth and help clean it up. Helping repair the problem is part of taking responsibility."
    )],
}

KNOWLEDGE_ORDER = ["repertoire", "asking", "paper", "ribbons", "wind", "cleanup"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    venue = f["venue"]
    repertoire = f["repertoire_cfg"]
    outcome = f["outcome"]
    if outcome == "shared":
        return [
            f'Write a rhyming story for ages 3 to 5 about a llama in {venue.place} whose curiosity leads to a polite question about a {repertoire.label}. Include the word "repertoire".',
            f"Tell a gentle moral story where {hero.id} the llama wants a closer look at a performer's things, asks first, and is warmly included.",
            "Write a child-facing story in rhyming prose about curiosity guided by courtesy."
        ]
    if outcome == "mended":
        return [
            f'Write a rhyming story where a curious llama sneaks a peek at a {repertoire.label}, causes a spill, then helps mend the mistake. Include the word "llama".',
            "Tell a moral story in soft rhyme where curiosity causes trouble, honesty follows fast, and a kind helper turns the mistake into a lesson.",
            "Write a simple story that teaches asking before touching and helping clean up when something goes wrong."
        ]
    return [
        f'Write a rhyming cautionary story where a llama peeks into a {repertoire.label} without asking, and part of the repertoire is lost in the wind.',
        "Tell a child-friendly moral story about curiosity, courtesy, and the sadness of being too late to fix every part of a mistake.",
        'Write a gentle but serious story that includes the word "repertoire" and ends with a promise to ask first next time.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    owner = f["owner"]
    elder = f["elder"]
    venue = f["venue"]
    repertoire = f["repertoire_cfg"]
    storage = f["storage_cfg"]
    response = f["response"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a little llama named {hero.id}, the performer {owner.id}, and {elder.label_word if elder.label_word in {'mom', 'dad', 'aunt', 'uncle'} else 'a gentle elder'} who gives the lesson."
        ),
        (
            f"What made {hero.id} curious?",
            f"{hero.id} saw {owner.id} carrying {storage.phrase} filled with {repertoire.phrase}. The special performance pieces made the llama want a closer look."
        ),
        (
            "What was inside the repertoire?",
            f"It held {repertoire.inside_line.lower()} The repertoire was a collection of performance pieces ready for the show."
        ),
    ]
    if f["choice"] == "ask":
        qa.append((
            f"What did {hero.id} do instead of peeking?",
            f"{hero.id} asked {owner.id} for permission before touching anything. That polite choice turned curiosity into sharing instead of trouble."
        ))
        qa.append((
            "What moral did the story teach?",
            f"The story taught that curiosity is good when it travels with courtesy. Asking first kept the repertoire safe and made room for trust."
        ))
    elif f["outcome"] == "mended":
        qa.append((
            f"What happened when {hero.id} sneaked a peek?",
            f"{hero.id} jostled the {storage.label}, and the repertoire spilled out. Because the pieces were loose and the place was not perfectly still, the mess needed quick help."
        ))
        qa.append((
            f"How did {owner.id} fix the problem?",
            f"{owner.id} {response.qa_text}. The calm help stopped the mistake from becoming a bigger loss."
        ))
        qa.append((
            "What did the llama learn?",
            f"{hero.id} learned to ask before touching and to help mend a problem right away. The lesson came from feeling worried, telling the truth, and working beside {owner.id}."
        ))
    else:
        qa.append((
            f"Why could the mess not be fully fixed?",
            f"The pieces were light, the wind was strong, and help came too late to save every part. That is why some of the repertoire blew away before it could all be gathered."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with a softer show and a quiet promise from {hero.id} to ask first next time. The ending proves that one small choice can change what is left for later."
        ))
        qa.append((
            "What moral did the story teach?",
            f"The story taught that curiosity needs courtesy, and that some mistakes cannot be completely undone. Telling the truth still mattered, but asking first would have protected the repertoire from the start."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["repertoire_cfg"].tags) | {"cleanup"}
    if world.facts["venue"].wind > 0:
        tags.add("wind")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = []
        if ent.paper_light:
            flags.append("paper_light")
        if ent.tippy:
            flags.append("tippy")
        if ent.portable:
            flags.append("portable")
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        venue="barn",
        repertoire="dance_ribbons",
        storage="basket",
        response="sort_together",
        hero="Lina",
        hero_gender="girl",
        owner="Milo",
        owner_gender="boy",
        elder="aunt",
        trait="polite",
        choice="ask",
        delay=0,
    ),
    StoryParams(
        venue="meadow",
        repertoire="song_cards",
        storage="basket",
        response="clip_and_sort",
        hero="Paco",
        hero_gender="boy",
        owner="Zuri",
        owner_gender="girl",
        elder="mother",
        trait="curious",
        choice="sneak",
        delay=0,
    ),
    StoryParams(
        venue="hill",
        repertoire="rhyme_booklets",
        storage="satchel",
        response="sort_together",
        hero="Nora",
        hero_gender="girl",
        owner="Teo",
        owner_gender="boy",
        elder="father",
        trait="eager",
        choice="sneak",
        delay=1,
    ),
    StoryParams(
        venue="hill",
        repertoire="song_cards",
        storage="basket",
        response="clip_and_sort",
        hero="Luca",
        hero_gender="boy",
        owner="Ayla",
        owner_gender="girl",
        elder="uncle",
        trait="thoughtful",
        choice="sneak",
        delay=0,
    ),
]


def explain_rejection(storage: Storage, repertoire: Repertoire) -> str:
    return (
        f"(No story: a {storage.label} is not a reasonable home for {repertoire.phrase}. "
        f"The storage must plausibly hold that kind of repertoire.)"
    )


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it is too weak for this world's common-sense gate "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if params.choice == "ask":
        return "shared"
    venue = THEMES[params.venue]
    repertoire = REPERTOIRES[params.repertoire]
    storage = STORAGES[params.storage]
    response = RESPONSES[params.response]
    return "mended" if is_recovered(response, venue, repertoire, storage, params.delay) else "lost"


ASP_RULES = r"""
supports_pair(S, R) :- supports(S, R).
valid(V, R, S) :- venue(V), repertoire(R), storage(S), supports_pair(S, R).

severity(Sp + D + W) :- chosen_storage(S), spill_risk(S, Sp),
                        delay(D), chosen_repertoire(R), paper_light(R),
                        chosen_venue(V), wind(V, W).
severity(Sp + D) :- chosen_storage(S), spill_risk(S, Sp),
                    delay(D), chosen_repertoire(R), not paper_light(R).

sensible(Rs) :- response(Rs), sense(Rs, S), sense_min(M), S >= M.
recovered :- chosen_response(Rs), power(Rs, P), severity(V), P >= V.

outcome(shared) :- choice(ask).
outcome(mended) :- choice(sneak), recovered.
outcome(lost) :- choice(sneak), not recovered.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for venue_id, venue in THEMES.items():
        lines.append(asp.fact("venue", venue_id))
        lines.append(asp.fact("wind", venue_id, venue.wind))
    for repertoire_id, repertoire in REPERTOIRES.items():
        lines.append(asp.fact("repertoire", repertoire_id))
        if repertoire.paper_light:
            lines.append(asp.fact("paper_light", repertoire_id))
    for storage_id, storage in STORAGES.items():
        lines.append(asp.fact("storage", storage_id))
        lines.append(asp.fact("spill_risk", storage_id, storage.spill_risk))
        for repertoire_id in sorted(storage.supports):
            lines.append(asp.fact("supports", storage_id, repertoire_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_venue", params.venue),
        asp.fact("chosen_repertoire", params.repertoire),
        asp.fact("chosen_storage", params.storage),
        asp.fact("chosen_response", params.response),
        asp.fact("choice", params.choice),
        asp.fact("delay", params.delay),
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
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens, p_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(30):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a llama, curiosity, and a repertoire handled the courteous way."
    )
    ap.add_argument("--venue", choices=THEMES)
    ap.add_argument("--repertoire", choices=REPERTOIRES)
    ap.add_argument("--storage", choices=STORAGES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--choice", choices=["ask", "sneak"])
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--owner")
    ap.add_argument("--owner-gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1], help="how long help takes after a spill")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (venue, repertoire, storage) sets from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.repertoire and args.storage:
        repertoire = REPERTOIRES[args.repertoire]
        storage = STORAGES[args.storage]
        if not hazard_supported(storage, repertoire):
            raise StoryError(explain_rejection(storage, repertoire))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.venue is None or combo[0] == args.venue)
        and (args.repertoire is None or combo[1] == args.repertoire)
        and (args.storage is None or combo[2] == args.storage)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    venue_id, repertoire_id, storage_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    choice = args.choice or rng.choice(["ask", "sneak", "sneak"])
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hero_gender)
    owner_gender = args.owner_gender or rng.choice(["girl", "boy"])
    owner = args.owner or _pick_name(rng, owner_gender, avoid=hero)
    elder = args.elder or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = args.trait or rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 0, 1])
    return StoryParams(
        venue=venue_id,
        repertoire=repertoire_id,
        storage=storage_id,
        response=response_id,
        hero=hero,
        hero_gender=hero_gender,
        owner=owner,
        owner_gender=owner_gender,
        elder=elder,
        trait=trait,
        choice=choice,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.venue not in THEMES:
        raise StoryError(f"(Unknown venue: {params.venue})")
    if params.repertoire not in REPERTOIRES:
        raise StoryError(f"(Unknown repertoire: {params.repertoire})")
    if params.storage not in STORAGES:
        raise StoryError(f"(Unknown storage: {params.storage})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.choice not in {"ask", "sneak"}:
        raise StoryError(f"(Unknown choice: {params.choice})")

    venue = THEMES[params.venue]
    repertoire = REPERTOIRES[params.repertoire]
    storage = STORAGES[params.storage]
    response = RESPONSES[params.response]

    if not hazard_supported(storage, repertoire):
        raise StoryError(explain_rejection(storage, repertoire))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        venue=venue,
        repertoire_cfg=repertoire,
        storage_cfg=storage,
        response_cfg=response,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        owner_name=params.owner,
        owner_gender=params.owner_gender,
        elder_type=params.elder,
        trait=params.trait,
        choice=params.choice,
        delay=params.delay,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (venue, repertoire, storage) combos:\n")
        for venue, repertoire, storage in combos:
            print(f"  {venue:8} {repertoire:14} {storage}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} at {p.venue}: {p.choice} with {p.repertoire} in {p.storage} ({outcome_of(p)})"
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
