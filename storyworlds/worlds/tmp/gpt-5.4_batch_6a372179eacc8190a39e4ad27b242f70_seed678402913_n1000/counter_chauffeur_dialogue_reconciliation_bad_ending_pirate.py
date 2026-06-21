#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/counter_chauffeur_dialogue_reconciliation_bad_ending_pirate.py
==========================================================================================

A standalone storyworld about two children in a pirate mood, a missing clue, a
quarrel, a chauffeur who urges them to talk plainly, and a sad ending that comes
from reconciling too late. The seed words "counter" and "chauffeur" are part of
the world model itself, not just dropped into the prose.

The core domain:
- two children are playing pirates on the way to a harbor outing
- a paper clue was set on a harbor counter by the chauffeur while buying tickets
- one child wrongly blames the other for losing it
- dialogue and apology repair the friendship
- but the delay means the tide or ferry is gone, so the pirate outing is lost

The model prefers plausible variants:
- only clue items that make sense on a public counter
- only destinations that truly depend on catching a timed departure
- explicit invalid choices raise StoryError with a clear reason

Run it
------
    python storyworlds/worlds/gpt-5.4/counter_chauffeur_dialogue_reconciliation_bad_ending_pirate.py
    python storyworlds/worlds/gpt-5.4/counter_chauffeur_dialogue_reconciliation_bad_ending_pirate.py --all
    python storyworlds/worlds/gpt-5.4/counter_chauffeur_dialogue_reconciliation_bad_ending_pirate.py --trace --qa
    python storyworlds/worlds/gpt-5.4/counter_chauffeur_dialogue_reconciliation_bad_ending_pirate.py --verify
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
PATIENCE_LIMIT = 2


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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "chauffeur_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        mapping = {
            "mother": "mom",
            "father": "dad",
            "chauffeur_man": "chauffeur",
        }
        return mapping.get(self.type, self.label or self.type)


@dataclass
class Theme:
    id: str
    scene: str
    rig: str
    titles: tuple[str, str]
    goal: str
    plural_role: str
    send_off: str


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    plural: bool = False
    flat_item: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class CounterPlace:
    id: str
    label: str
    phrase: str
    worker: str
    departure_kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Destination:
    id: str
    label: str
    phrase: str
    route: str
    departure_word: str
    tide_bound: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    theme: str
    clue: str
    counter_place: str
    destination: str
    captain_name: str
    captain_gender: str
    mate_name: str
    mate_gender: str
    chauffeur_name: str
    chauffeur_gender: str
    driver_patience: int
    blame: str
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


def _r_argument_costs_time(world: World) -> list[str]:
    out: list[str] = []
    captain = world.get("captain")
    mate = world.get("mate")
    if captain.memes["blaming"] < THRESHOLD:
        return out
    sig = ("argument",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    captain.memes["anger"] += 1
    mate.memes["hurt"] += 1
    world.get("clock").meters["delay"] += 1
    out.append("__argument__")
    return out


def _r_reconciliation_clears_conflict(world: World) -> list[str]:
    out: list[str] = []
    captain = world.get("captain")
    mate = world.get("mate")
    if captain.memes["apology"] < THRESHOLD or mate.memes["forgiveness"] < THRESHOLD:
        return out
    sig = ("peace",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    captain.memes["anger"] = 0.0
    mate.memes["hurt"] = 0.0
    captain.memes["trust"] += 1
    mate.memes["trust"] += 1
    out.append("__peace__")
    return out


def _r_missed_departure(world: World) -> list[str]:
    out: list[str] = []
    clock = world.get("clock")
    if clock.meters["delay"] < THRESHOLD:
        return out
    chauffeur = world.get("chauffeur")
    destination = world.get("destination")
    if destination.attrs.get("tide_bound") and chauffeur.memes["ready_to_go"] >= THRESHOLD:
        sig = ("missed",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        destination.meters["departed"] += 1
        out.append("__missed__")
    return out


CAUSAL_RULES = [
    Rule(name="argument_costs_time", tag="social", apply=_r_argument_costs_time),
    Rule(name="reconciliation_clears_conflict", tag="social", apply=_r_reconciliation_clears_conflict),
    Rule(name="missed_departure", tag="physical", apply=_r_missed_departure),
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
        for sent in produced:
            world.say(sent)
    return produced


THEMES = {
    "pirates": Theme(
        id="pirates",
        scene="a harbor of make-believe coves",
        rig="A striped scarf was a captain's sash, a rolled map was a sea chart, and every post by the quay looked ready to be a mast.",
        titles=("Captain", "First Mate"),
        goal="the little island fort beyond the harbor mouth",
        plural_role="pirates",
        send_off="could have sailed for the fort",
    ),
    "corsairs": Theme(
        id="corsairs",
        scene="a windy coast full of secret coves",
        rig="A cardboard tube became a spyglass, a string bag became a treasure sack, and the stone steps down to the water felt like a gangplank.",
        titles=("Captain", "Lookout"),
        goal="the old watchtower on Gull Rock",
        plural_role="corsairs",
        send_off="could have crossed to the watchtower",
    ),
}

CLUES = {
    "map": Clue(
        id="map",
        label="map",
        phrase="a folded pirate map",
        plural=False,
        flat_item=True,
        tags={"map", "paper"},
    ),
    "ticket_envelope": Clue(
        id="ticket_envelope",
        label="ticket envelope",
        phrase="a flat envelope with the boat tickets inside",
        plural=False,
        flat_item=True,
        tags={"ticket", "paper"},
    ),
    "postcard": Clue(
        id="postcard",
        label="postcard clue",
        phrase="a postcard with a red X drawn on the back",
        plural=False,
        flat_item=True,
        tags={"postcard", "paper"},
    ),
    "shell_bucket": Clue(
        id="shell_bucket",
        label="shell bucket",
        phrase="a blue shell bucket",
        plural=False,
        flat_item=False,
        tags={"bucket"},
    ),
}

COUNTER_PLACES = {
    "ticket_booth": CounterPlace(
        id="ticket_booth",
        label="ticket booth",
        phrase="the wooden ticket booth by the quay",
        worker="the ticket seller",
        departure_kind="ferry",
        tags={"booth", "counter"},
    ),
    "harbor_cafe": CounterPlace(
        id="harbor_cafe",
        label="harbor café",
        phrase="the little harbor café",
        worker="the café lady",
        departure_kind="launch",
        tags={"cafe", "counter"},
    ),
    "museum_desk": CounterPlace(
        id="museum_desk",
        label="museum desk",
        phrase="the sea museum desk",
        worker="the museum clerk",
        departure_kind="tour boat",
        tags={"desk", "counter"},
    ),
}

DESTINATIONS = {
    "island_fort": Destination(
        id="island_fort",
        label="island fort",
        phrase="the little fort on the island",
        route="a short ferry ride",
        departure_word="ferry",
        tide_bound=True,
        tags={"island", "boat"},
    ),
    "gull_rock": Destination(
        id="gull_rock",
        label="Gull Rock",
        phrase="the watchtower on Gull Rock",
        route="the harbor launch",
        departure_word="launch",
        tide_bound=True,
        tags={"rock", "boat"},
    ),
    "seal_steps": Destination(
        id="seal_steps",
        label="Seal Steps",
        phrase="the bright stone steps by Seal Steps",
        route="the museum tour boat",
        departure_word="tour boat",
        tide_bound=True,
        tags={"steps", "boat"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Ava", "Nora", "Zoe", "Anna"]
BOY_NAMES = ["Tom", "Ben", "Max", "Finn", "Leo", "Sam"]
DRIVER_NAMES = ["Mr. Reed", "Mr. Vale", "Mr. Pike", "Mr. Rowan"]
TRAITS = ["bold", "careful", "quick", "proud", "eager"]


def clue_fits_counter(clue: Clue, counter_place: CounterPlace) -> bool:
    return clue.flat_item


def departure_matches(counter_place: CounterPlace, destination: Destination) -> bool:
    return counter_place.departure_kind == destination.departure_word


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for theme_id in THEMES:
        for clue_id, clue in CLUES.items():
            for place_id, place in COUNTER_PLACES.items():
                for dest_id, dest in DESTINATIONS.items():
                    if clue_fits_counter(clue, place) and departure_matches(place, dest):
                        combos.append((theme_id, clue_id, place_id, dest_id))
    return combos


def explain_rejection(clue: Clue, counter_place: CounterPlace, destination: Destination) -> str:
    if not clue.flat_item:
        return (
            f"(No story: {clue.phrase} is not the kind of thing a chauffeur would casually set on "
            f"{counter_place.phrase}'s counter while paying. Pick a flat paper clue like a map or ticket envelope.)"
        )
    return (
        f"(No story: {counter_place.phrase} serves a {counter_place.departure_kind}, but "
        f"{destination.phrase} is reached by {destination.departure_word}. The clue and departure should belong to the same harbor errand.)"
    )


def predict_loss(world: World) -> dict:
    sim = world.copy()
    sim.get("captain").memes["blaming"] += 1
    propagate(sim, narrate=False)
    sim.get("chauffeur").memes["ready_to_go"] += 1
    propagate(sim, narrate=False)
    return {
        "delay": sim.get("clock").meters["delay"],
        "missed": sim.get("destination").meters["departed"] >= THRESHOLD,
    }


def pirate_opening(world: World, captain: Entity, mate: Entity, chauffeur: Entity, theme: Theme) -> None:
    t1, t2 = theme.titles
    world.say(
        f"{captain.id} and {mate.id} arrived at the harbor feeling sure the morning belonged to {theme.plural_role}. "
        f"{theme.rig}"
    )
    world.say(
        f'"{t1} {captain.id}!" cried {mate.id}. "{t2} {mate.id} is ready for {theme.goal}."'
    )
    world.say(
        f"Their chauffeur, {chauffeur.id}, smiled as he opened the car door and called them his tidy little crew."
    )


def harbor_setup(world: World, chauffeur: Entity, clue: Clue, counter_place: CounterPlace, destination: Destination) -> None:
    chauffeur.memes["care"] += 1
    world.say(
        f"He took them to {counter_place.phrase}, where he meant to collect what they needed for {destination.route} to {destination.phrase}."
    )
    world.say(
        f"While speaking to {counter_place.worker}, the chauffeur set {clue.phrase} on the counter for one absent-minded moment."
    )
    world.facts["left_on_counter"] = True


def discover_missing(world: World, captain: Entity, mate: Entity, clue: Clue) -> None:
    captain.memes["worry"] += 1
    world.say(
        f"But when the children turned back, {clue.phrase} was no longer where {captain.id} expected it to be."
    )
    world.say(
        f'"Where is the {clue.label}?" {captain.id} gasped. The bright game turned sharp all at once.'
    )


def blame_scene(world: World, captain: Entity, mate: Entity, clue: Clue) -> None:
    captain.memes["blaming"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"You touched it last!" {captain.id} said. "You moved the {clue.label}, and now the tide will beat us."'
    )
    world.say(
        f'{mate.id} drew back as if a cold splash had hit {mate.pronoun("object")}. '
        f'"I did not," {mate.pronoun()} said. "I was looking at the boats."'
    )


def chauffeur_intervenes(world: World, chauffeur: Entity, captain: Entity, mate: Entity) -> None:
    chauffeur.memes["ready_to_go"] += 1
    pred = predict_loss(world)
    world.facts["predicted_delay"] = pred["delay"]
    world.facts["predicted_loss"] = pred["missed"]
    world.say(
        f'{chauffeur.id} lifted a calm hand. "Crewmates," he said, "a quarrel chews time faster than any tide. '
        f'Use true words first, and then use sharp eyes."'
    )
    world.say(
        f'"Did you see {mate.id} move it?" the chauffeur asked. "{captain.id}, speak only what you know."'
    )


def apology(world: World, captain: Entity, mate: Entity) -> None:
    captain.memes["apology"] += 1
    mate.memes["forgiveness"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{captain.id} looked at {mate.id}, then at the empty space by the till. '
        f'"I am sorry," {captain.pronoun()} said quietly. "I was frightened and blamed you before I knew the truth."'
    )
    world.say(
        f'"I was hurt," {mate.id} answered, "but I still want to help." Then {mate.pronoun()} gave a small nod, and the hard knot between them loosened.'
    )


def search_and_realize(world: World, chauffeur: Entity, clue: Clue, counter_place: CounterPlace) -> None:
    world.say(
        f"Together they searched around {counter_place.phrase}. Then the chauffeur stopped, touched his coat pocket, and let out a soft groan."
    )
    world.say(
        f'"Oh, dear," he said. "When I paid at the counter, I tucked {clue.phrase} under my driving gloves so the wind would not lift it. '
        f'This loss was mine, not yours."'
    )
    world.facts["chauffeur_caused_mixup"] = True


def missed_departure(world: World, destination: Entity, chauffeur: Entity, theme: Theme) -> None:
    chauffeur.memes["ready_to_go"] += 1
    propagate(world, narrate=False)
    destination.meters["departed"] += 1
    world.say(
        f"But by then a horn had already sounded over the water. The last {destination.attrs['departure_word']} slipped away from the quay, leaving only a widening stripe of silver wake."
    )
    world.say(
        f'{chauffeur.id} removed his cap. "I am sorry, my crew," he said. "We made our peace, but not before the harbor made its choice."'
    )
    world.say(
        f"So the young {theme.plural_role} stood arm in arm and watched {theme.goal} stay far beyond their reach that day."
    )


def final_image(world: World, captain: Entity, mate: Entity, clue: Clue) -> None:
    captain.memes["sadness"] += 1
    mate.memes["sadness"] += 1
    world.say(
        f"{captain.id} and {mate.id} did not quarrel again. Yet the folded {clue.label} felt heavy and useless in the chauffeur's hand, because the boat they needed was already gone."
    )
    world.say(
        "The sea kept glittering as if nothing had happened, and that made the bad ending feel even quieter."
    )


def tell(
    theme: Theme,
    clue: Clue,
    counter_place: CounterPlace,
    destination_cfg: Destination,
    captain_name: str,
    captain_gender: str,
    mate_name: str,
    mate_gender: str,
    chauffeur_name: str,
    chauffeur_gender: str,
    driver_patience: int,
    blame: str,
) -> World:
    world = World()
    captain = world.add(Entity(id="captain", kind="character", type=captain_gender, label=captain_name, role="captain"))
    mate = world.add(Entity(id="mate", kind="character", type=mate_gender, label=mate_name, role="mate"))
    chauffeur_type = "chauffeur_man" if chauffeur_gender == "boy" else chauffeur_gender
    chauffeur = world.add(Entity(id="chauffeur", kind="character", type=chauffeur_type, label=chauffeur_name, role="chauffeur"))
    world.add(Entity(id="clock", type="clock", label="harbor clock"))
    destination = world.add(
        Entity(
            id="destination",
            type="destination",
            label=destination_cfg.label,
            phrase=destination_cfg.phrase,
            attrs={"departure_word": destination_cfg.departure_word, "tide_bound": destination_cfg.tide_bound},
            tags=set(destination_cfg.tags),
        )
    )

    captain.attrs["display_name"] = captain_name
    mate.attrs["display_name"] = mate_name
    chauffeur.attrs["display_name"] = chauffeur_name
    captain.attrs["blame_style"] = blame
    chauffeur.attrs["patience"] = driver_patience

    pirate_opening(world, captain, mate, chauffeur, theme)
    harbor_setup(world, chauffeur, clue, counter_place, destination_cfg)

    world.para()
    discover_missing(world, captain, mate, clue)
    blame_scene(world, captain, mate, clue)
    chauffeur_intervenes(world, chauffeur, captain, mate)

    world.para()
    apology(world, captain, mate)
    search_and_realize(world, chauffeur, clue, counter_place)

    world.para()
    missed_departure(world, destination, chauffeur, theme)
    final_image(world, captain, mate, clue)

    world.facts.update(
        theme=theme,
        clue=clue,
        counter_place=counter_place,
        destination_cfg=destination_cfg,
        captain=captain,
        mate=mate,
        chauffeur=chauffeur,
        driver_patience=driver_patience,
        blame=blame,
        reconciled=captain.memes["apology"] >= THRESHOLD and mate.memes["forgiveness"] >= THRESHOLD,
        bad_ending=destination.meters["departed"] >= THRESHOLD,
        delay=int(world.get("clock").meters["delay"]),
        departure_word=destination_cfg.departure_word,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    chauffeur = f["chauffeur"]
    clue = f["clue"]
    counter_place = f["counter_place"]
    destination = f["destination_cfg"]
    theme = f["theme"]
    return [
        f'Write a pirate-style story for a 3-to-5-year-old that includes the words "counter" and "chauffeur", with dialogue, reconciliation, and a bad ending.',
        f"Tell a harbor pirate tale where {captain.label} wrongly blames {mate.label} after {clue.phrase} goes missing from {counter_place.phrase}, and their chauffeur helps them speak honestly.",
        f"Write a sad but gentle story in which two child pirates make peace too late and miss the {destination.departure_word} to {destination.phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    chauffeur = f["chauffeur"]
    clue = f["clue"]
    counter_place = f["counter_place"]
    destination = f["destination_cfg"]
    theme = f["theme"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two children, {captain.label} and {mate.label}, who were pretending to be {theme.plural_role}, and their chauffeur {chauffeur.label}. They were on the way to {destination.phrase} from the harbor."
        ),
        (
            f"Why did {captain.label} get upset?",
            f"{captain.label} thought {clue.phrase} had vanished from the counter and was afraid their outing would be lost. That fear made {captain.pronoun()} accuse {mate.label} before knowing what had really happened."
        ),
        (
            "How did the chauffeur help?",
            f"The chauffeur told them to use true words instead of angry guesses. His calm question made {captain.label} stop, think, and apologize."
        ),
        (
            "How did the children reconcile?",
            f"{captain.label} admitted the blame had been unfair and said sorry. {mate.label} said the accusation had hurt, but still chose to help, so they became a team again."
        ),
        (
            f"What was the real reason the {clue.label} was missing?",
            f"It was not stolen or moved by {mate.label}. The chauffeur had tucked it under his gloves after setting it on the counter so the wind would not blow it away."
        ),
        (
            "Why is the ending bad even though they made peace?",
            f"They reconciled after the quarrel had already cost them time. By then the last {destination.departure_word} had left the quay, so the outing to {destination.phrase} was over for that day."
        ),
    ]
    return qa


KNOWLEDGE = {
    "counter": [
        (
            "What is a counter?",
            "A counter is a flat surface in a shop or booth where people pay, ask questions, or pick things up."
        )
    ],
    "chauffeur": [
        (
            "What is a chauffeur?",
            "A chauffeur is a driver whose job is to take people where they need to go. A careful chauffeur also helps keep riders safe and on time."
        )
    ],
    "apology": [
        (
            "What is an apology?",
            "An apology is when you say you were wrong and that you are sorry. It helps mend hurt feelings when you speak honestly."
        )
    ],
    "ferry": [
        (
            "What is a ferry?",
            "A ferry is a boat that carries people across water from one place to another. Ferries leave at set times, so being late can mean missing the trip."
        )
    ],
    "tide": [
        (
            "What is a tide?",
            "A tide is the way the sea slowly rises and falls. Some boats and harbor trips have to match the tide to travel safely."
        )
    ],
    "blame": [
        (
            "Why is it unkind to blame someone before you know the truth?",
            "It can hurt feelings and start a fight for no fair reason. It is better to ask what happened first."
        )
    ],
}
KNOWLEDGE_ORDER = ["counter", "chauffeur", "apology", "blame", "ferry", "tide"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:11} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
flat_counter_item(C) :- clue(C), flat_item(C).
matching_departure(P, D) :- counter_place(P), destination(D), serves(P, K), departure_word(D, K).
valid(T, C, P, D) :- theme(T), flat_counter_item(C), matching_departure(P, D).

% All generated stories in this world reconcile, but the departure is still missed.
reconciled :- apology_happened, forgiveness_happened.
bad_ending :- reconciled, delay(Del), patience_limit(L), Del >= 1, L >= 0.
outcome(bad_reconciled) :- reconciled, bad_ending.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        if clue.flat_item:
            lines.append(asp.fact("flat_item", clue_id))
    for place_id, place in COUNTER_PLACES.items():
        lines.append(asp.fact("counter_place", place_id))
        lines.append(asp.fact("serves", place_id, place.departure_kind))
    for dest_id, dest in DESTINATIONS.items():
        lines.append(asp.fact("destination", dest_id))
        lines.append(asp.fact("departure_word", dest_id, dest.departure_word))
    lines.append(asp.fact("patience_limit", PATIENCE_LIMIT))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("apology_happened"),
            asp.fact("forgiveness_happened"),
            asp.fact("delay", 1),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        theme="pirates",
        clue="map",
        counter_place="ticket_booth",
        destination="island_fort",
        captain_name="Tom",
        captain_gender="boy",
        mate_name="Lily",
        mate_gender="girl",
        chauffeur_name="Mr. Reed",
        chauffeur_gender="boy",
        driver_patience=1,
        blame="sharp",
    ),
    StoryParams(
        theme="corsairs",
        clue="ticket_envelope",
        counter_place="harbor_cafe",
        destination="gull_rock",
        captain_name="Ava",
        captain_gender="girl",
        mate_name="Ben",
        mate_gender="boy",
        chauffeur_name="Mr. Vale",
        chauffeur_gender="boy",
        driver_patience=2,
        blame="frightened",
    ),
    StoryParams(
        theme="pirates",
        clue="postcard",
        counter_place="museum_desk",
        destination="seal_steps",
        captain_name="Finn",
        captain_gender="boy",
        mate_name="Nora",
        mate_gender="girl",
        chauffeur_name="Mr. Pike",
        chauffeur_gender="boy",
        driver_patience=0,
        blame="hasty",
    ),
]


def outcome_of(params: StoryParams) -> str:
    return "bad_reconciled"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Pirate-style harbor storyworld: a missing clue on a counter, a chauffeur, reconciliation, and a bad ending."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--counter-place", dest="counter_place", choices=COUNTER_PLACES)
    ap.add_argument("--destination", choices=DESTINATIONS)
    ap.add_argument("--captain-name")
    ap.add_argument("--mate-name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.clue and args.counter_place and args.destination:
        clue = CLUES[args.clue]
        place = COUNTER_PLACES[args.counter_place]
        dest = DESTINATIONS[args.destination]
        if not (clue_fits_counter(clue, place) and departure_matches(place, dest)):
            raise StoryError(explain_rejection(clue, place, dest))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.clue is None or combo[1] == args.clue)
        and (args.counter_place is None or combo[2] == args.counter_place)
        and (args.destination is None or combo[3] == args.destination)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, clue_id, place_id, dest_id = rng.choice(sorted(combos))
    captain_gender = rng.choice(["girl", "boy"])
    mate_gender = "boy" if captain_gender == "girl" else "girl"
    captain_name = args.captain_name or _pick_name(rng, captain_gender)
    mate_name = args.mate_name or _pick_name(rng, mate_gender, avoid=captain_name)
    chauffeur_name = rng.choice(DRIVER_NAMES)
    driver_patience = rng.randint(0, PATIENCE_LIMIT)
    blame = rng.choice(["sharp", "frightened", "hasty"])
    return StoryParams(
        theme=theme_id,
        clue=clue_id,
        counter_place=place_id,
        destination=dest_id,
        captain_name=captain_name,
        captain_gender=captain_gender,
        mate_name=mate_name,
        mate_gender=mate_gender,
        chauffeur_name=chauffeur_name,
        chauffeur_gender="boy",
        driver_patience=driver_patience,
        blame=blame,
    )


def _validate_params(params: StoryParams) -> None:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.counter_place not in COUNTER_PLACES:
        raise StoryError(f"(Unknown counter_place: {params.counter_place})")
    if params.destination not in DESTINATIONS:
        raise StoryError(f"(Unknown destination: {params.destination})")

    clue = CLUES[params.clue]
    place = COUNTER_PLACES[params.counter_place]
    dest = DESTINATIONS[params.destination]
    if not clue_fits_counter(clue, place) or not departure_matches(place, dest):
        raise StoryError(explain_rejection(clue, place, dest))


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        theme=THEMES[params.theme],
        clue=CLUES[params.clue],
        counter_place=COUNTER_PLACES[params.counter_place],
        destination_cfg=DESTINATIONS[params.destination],
        captain_name=params.captain_name,
        captain_gender=params.captain_gender,
        mate_name=params.mate_name,
        mate_gender=params.mate_gender,
        chauffeur_name=params.chauffeur_name,
        chauffeur_gender=params.chauffeur_gender,
        driver_patience=params.driver_patience,
        blame=params.blame,
    )
    return StorySample(
        params=params,
        story=world.render().replace("captain", params.captain_name).replace("mate", params.mate_name),
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


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    checked = 0
    for params in CURATED:
        py = outcome_of(params)
        asp = asp_outcome(params)
        checked += 1
        if py != asp:
            rc = 1
            print(f"MISMATCH in outcome for {params}: python={py} asp={asp}")
    if rc == 0:
        print(f"OK: outcome model matches on {checked} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, clue, counter_place, destination) combos:\n")
        for theme, clue, place, dest in combos:
            print(f"  {theme:8} {clue:15} {place:12} {dest}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.captain_name} & {p.mate_name}: {p.clue} at {p.counter_place} -> {p.destination}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
