#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/didey_esplanade_chief_suspense_tall_tale.py
=======================================================================

A standalone storyworld about a child called Didey, a windy esplanade, and the
harbor chief who helps turn a near-disaster into a brag-worthy tall tale.

Premise
-------
Didey brings something absurdly grand to the esplanade for a town celebration:
a kite, a banner, or a paper lantern shaped like a moon. The sea wind rises.
If the tether is poor, the thing breaks loose and sweeps toward trouble. A calm
chief predicts the risk, then helps solve it with a sensible anchor or capture
method. The ending proves the change: the show goes on safely, or everyone
learns why big wind needs big caution.

The style stays child-facing but leans into tall-tale exaggeration: hats fly,
gulls gossip, and gusts feel bigger than houses. The suspense comes from the
wind building, the line straining, and the crowd wondering whether the big show
will turn into a big mess.

Run it
------
python storyworlds/worlds/gpt-5.4/didey_esplanade_chief_suspense_tall_tale.py
python storyworlds/worlds/gpt-5.4/didey_esplanade_chief_suspense_tall_tale.py --show kite --wind gale
python storyworlds/worlds/gpt-5.4/didey_esplanade_chief_suspense_tall_tale.py --response grab_by_hand
python storyworlds/worlds/gpt-5.4/didey_esplanade_chief_suspense_tall_tale.py --all --qa
python storyworlds/worlds/gpt-5.4/didey_esplanade_chief_suspense_tall_tale.py --verify
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
SENSE_MIN = 2


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
        male = {"boy", "father", "man", "chief"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    image: str
    lookout: str
    edge: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ShowThing:
    id: str
    label: str
    phrase: str
    launch_text: str
    looming_text: str
    ending_text: str
    danger_target: str
    pull: int
    wind_ready: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Wind:
    id: str
    label: str
    gust_text: str
    warning_text: str
    force: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Tether:
    id: str
    label: str
    phrase: str
    hold_text: str
    snap_text: str
    strength: int
    sensible: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    label: str
    text: str
    fail_text: str
    qa_text: str
    power: int
    sense: int
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


def _r_loose_line(world: World) -> list[str]:
    out: list[str] = []
    show = world.get("show")
    line = world.get("line")
    wind = world.get("wind")
    if wind.meters["force"] < THRESHOLD:
        return out
    if line.meters["strain"] >= THRESHOLD:
        return out
    sig = ("strain", show.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    line.meters["strain"] += 1
    show.meters["risk"] += 1
    out.append("__strain__")
    return out


def _r_breakaway(world: World) -> list[str]:
    out: list[str] = []
    show = world.get("show")
    line = world.get("line")
    if show.meters["risk"] < THRESHOLD:
        return out
    if line.meters["secure"] >= THRESHOLD:
        return out
    if line.meters["broken"] >= THRESHOLD:
        return out
    sig = ("break", show.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    line.meters["broken"] += 1
    show.meters["airborne"] += 1
    crowd = world.get("crowd")
    crowd.memes["fear"] += 1
    world.get("hero").memes["fear"] += 1
    out.append("__break__")
    return out


def _r_crowd_hush(world: World) -> list[str]:
    crowd = world.get("crowd")
    if crowd.memes["fear"] < THRESHOLD:
        return []
    sig = ("hush", crowd.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crowd.meters["hushed"] += 1
    return ["__hush__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="loose_line", tag="physical", apply=_r_loose_line),
    Rule(name="breakaway", tag="physical", apply=_r_breakaway),
    Rule(name="crowd_hush", tag="social", apply=_r_crowd_hush),
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


def hazard_possible(show: ShowThing, wind: Wind) -> bool:
    return show.wind_ready and wind.force >= 1


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def trouble_score(show: ShowThing, wind: Wind, tether: Tether) -> int:
    return show.pull + wind.force - tether.strength


def breaks_loose(show: ShowThing, wind: Wind, tether: Tether) -> bool:
    return trouble_score(show, wind, tether) >= 1


def response_works(show: ShowThing, wind: Wind, tether: Tether, response: Response) -> bool:
    if not breaks_loose(show, wind, tether):
        return True
    return response.power >= trouble_score(show, wind, tether)


def predict_risk(show: ShowThing, wind: Wind, tether: Tether) -> dict:
    return {
        "breaks": breaks_loose(show, wind, tether),
        "score": trouble_score(show, wind, tether),
    }


def introduce(world: World, hero: Entity, setting: Setting, show: ShowThing) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"On the salt-bright {setting.place}, Didey came marching with {show.phrase} "
        f"so grand it looked as if it had borrowed cloth from the sky."
    )
    world.say(
        f"{setting.image} People turned to stare, because in a tall tale, even a morning walk can feel like a parade."
    )


def boast(world: World, hero: Entity, show: ShowThing) -> None:
    world.say(
        f'"Just wait till you see {show.label} rise," Didey said. '
        f'"It will make the gulls blink and the bandstand bow."'
    )


def gather(world: World, chief: Entity, setting: Setting) -> None:
    world.say(
        f"At the far end by {setting.lookout}, the harbor chief stood with boots planted wide, "
        f"watching the sea as if he could hear tomorrow coming."
    )


def wind_builds(world: World, wind: Wind) -> None:
    world.get("wind").meters["force"] = float(wind.force)
    world.say(
        f"Then the wind began to stir. {wind.gust_text} It was the sort of wind that could pick a hat clean off a statue."
    )


def chief_warns(world: World, chief: Entity, show: ShowThing, wind: Wind, tether: Tether) -> None:
    pred = predict_risk(show, wind, tether)
    world.facts["predicted_break"] = pred["breaks"]
    world.facts["predicted_score"] = pred["score"]
    world.say(
        f'The chief narrowed his eyes. "{wind.warning_text} {show.label.capitalize()} is mighty, '
        f'but {tether.label} is only {tether.label}. If that line jumps loose, it will head for {show.danger_target}."'
    )


def launch(world: World, hero: Entity, show: ShowThing, tether: Tether) -> None:
    world.say(
        f"Didey lifted the great thing high. {show.launch_text} {tether.hold_text}"
    )
    world.get("line").meters["secure"] = 1.0 if tether.strength >= world.facts["show_cfg"].pull + world.facts["wind_cfg"].force else 0.0


def suspense(world: World, show: ShowThing, tether: Tether) -> None:
    if world.get("line").meters["secure"] >= THRESHOLD:
        world.say(
            f"For three long heartbeats, everybody watched anyway. {show.looming_text} But the line only hummed and held."
        )
    else:
        world.say(
            f"For three long heartbeats, nobody on the esplanade made a peep. {show.looming_text} "
            f"The {tether.label} drew tight enough to sing."
        )


def breakaway(world: World, show: ShowThing, tether: Tether) -> None:
    world.get("line").meters["strain"] += 1
    propagate(world, narrate=False)
    if world.get("line").meters["broken"] >= THRESHOLD:
        world.say(
            f"Then it happened. {tether.snap_text} Up leapt {show.label}, dragging a shadow across the paving stones as it swept toward {show.danger_target}."
        )
        if world.get("crowd").meters["hushed"] >= THRESHOLD:
            world.say(
                "The whole crowd went quiet in one gulp, the way a pond goes still when a stone is about to drop."
            )


def calm_save(world: World, chief: Entity, response: Response, show: ShowThing) -> None:
    world.get("show").meters["airborne"] = 0.0
    world.get("show").meters["saved"] += 1
    world.get("line").meters["broken"] = 0.0
    world.get("line").meters["secure"] += 1
    world.get("crowd").memes["fear"] = 0.0
    world.get("hero").memes["relief"] += 1
    world.say(
        f"The chief did not shout. He {response.text}."
    )
    world.say(
        f"A cheer rolled down the esplanade so hard it might have rattled shells under the sea wall. {show.label.capitalize()} was safe again."
    )


def fail_save(world: World, chief: Entity, response: Response, show: ShowThing) -> None:
    world.get("show").meters["lost"] += 1
    world.get("crowd").memes["fear"] += 1
    world.get("hero").memes["sorrow"] += 1
    world.say(
        f"The chief tried fast and brave, but {response.fail_text}."
    )
    world.say(
        f"Past the lamps and past the benches flew {show.label}, until it snagged high above {show.danger_target} where no small pair of hands could reach."
    )


def lesson(world: World, hero: Entity, chief: Entity, show: ShowThing, tether: Tether) -> None:
    hero.memes["lesson"] += 1
    hero.memes["trust"] += 1
    world.say(
        f'Didey swallowed hard. "I thought bigger meant better," {hero.pronoun()} said.'
    )
    world.say(
        f'"Bigger needs steadier," the chief answered, kneeling so his voice felt near instead of loud. '
        f'"On a windy esplanade, a brave heart still needs a strong hold."'
    )


def bright_ending(world: World, hero: Entity, show: ShowThing, tether: Tether, setting: Setting) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"After that, Didey flew {show.label} the proper way, with {tether.phrase} and the chief watching the gusts. "
        f"{show.ending_text}"
    )
    world.say(
        f"By sunset, folks were still retelling it along {setting.edge}, and every retelling made Didey's brave little morning grow another inch taller."
    )


def wistful_ending(world: World, hero: Entity, show: ShowThing, setting: Setting) -> None:
    hero.memes["lesson"] += 1
    world.say(
        f"That evening, the lamps along {setting.edge} blinked on one by one, and Didey looked up at the lost {show.label} far above the town."
    )
    world.say(
        f"It was still a tall tale by supper, but now it was the kind with a lesson inside: wind is wonderful from a safe hand and wild from a weak one."
    )


def tell(
    setting: Setting,
    show: ShowThing,
    wind: Wind,
    tether: Tether,
    response: Response,
    hero_name: str = "Didey",
    hero_type: str = "girl",
    chief_name: str = "Chief Bram",
    chief_type: str = "chief",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name, role="hero"))
    chief = world.add(Entity(id=chief_name, kind="character", type=chief_type, label="the chief", role="chief"))
    crowd = world.add(Entity(id="crowd", kind="thing", type="crowd", label="crowd"))
    world.add(Entity(id="show", kind="thing", type="show", label=show.label, phrase=show.phrase, tags=set(show.tags)))
    world.add(Entity(id="line", kind="thing", type="tether", label=tether.label, phrase=tether.phrase, tags=set(tether.tags)))
    world.add(Entity(id="wind", kind="thing", type="wind", label=wind.label, tags=set(wind.tags)))

    world.facts.update(
        hero=hero,
        chief=chief,
        crowd=crowd,
        setting=setting,
        show_cfg=show,
        wind_cfg=wind,
        tether_cfg=tether,
        response=response,
    )

    introduce(world, hero, setting, show)
    boast(world, hero, show)
    gather(world, chief, setting)

    world.para()
    wind_builds(world, wind)
    chief_warns(world, chief, show, wind, tether)
    launch(world, hero, show, tether)
    suspense(world, show, tether)

    broke = breaks_loose(show, wind, tether)
    saved = False

    if broke:
        world.para()
        breakaway(world, show, tether)
        if response_works(show, wind, tether, response):
            saved = True
            calm_save(world, chief, response, show)
            lesson(world, hero, chief, show, tether)
            world.para()
            bright_ending(world, hero, show, tether, setting)
        else:
            fail_save(world, chief, response, show)
            lesson(world, hero, chief, show, tether)
            world.para()
            wistful_ending(world, hero, show, setting)
    else:
        world.para()
        world.say(
            f"The line held true. {show.label.capitalize()} pulled and danced, but it never got away, and the worried silence melted into clapping."
        )
        lesson(world, hero, chief, show, tether)
        world.para()
        bright_ending(world, hero, show, tether, setting)
        saved = True

    outcome = "steady" if not broke else ("saved" if saved else "lost")
    world.facts.update(
        broke=broke,
        saved=saved,
        outcome=outcome,
        trouble=trouble_score(show, wind, tether),
    )
    return world


SETTINGS = {
    "seaside": Setting(
        id="seaside",
        place="esplanade",
        image="The stones shone pale beside the water, and the railings flashed like fish scales.",
        lookout="the signal tower",
        edge="the esplanade rail",
        tags={"esplanade", "sea"},
    ),
    "festival": Setting(
        id="festival",
        place="festival esplanade",
        image="Bunting snapped overhead, and the benches were crowded with people eating sweet buns.",
        lookout="the brass bandstand",
        edge="the esplanade lamps",
        tags={"esplanade", "festival"},
    ),
    "harbor": Setting(
        id="harbor",
        place="harbor esplanade",
        image="Down below, boats knocked gently together while the tide muttered against the wall.",
        lookout="the harbor office",
        edge="the harbor rail",
        tags={"esplanade", "harbor"},
    ),
}

SHOWS = {
    "kite": ShowThing(
        id="kite",
        label="kite",
        phrase="a kite as broad as a fishing boat's sail",
        launch_text="It climbed at once, tugging for the clouds like it had a meeting with the moon.",
        looming_text="The kite wheeled once over the crowd, and every face tipped upward.",
        ending_text="Soon it rode the sky in big smooth circles, grand as a visiting dragon and twice as polite.",
        danger_target="the clock tower",
        pull=2,
        tags={"kite", "wind"},
    ),
    "banner": ShowThing(
        id="banner",
        label="banner",
        phrase="a parade banner so long it could have wrapped a whale",
        launch_text="The cloth bellied out and boomed like a bright sail catching a pirate wind.",
        looming_text="The banner swung high, and the painted letters seemed to blink in the sun.",
        ending_text="Before long it streamed above the crowd straight and proud, as if the whole town had lent it a spine.",
        danger_target="the brass bandstand",
        pull=3,
        tags={"banner", "wind"},
    ),
    "lantern": ShowThing(
        id="lantern",
        label="paper moon lantern",
        phrase="a paper moon lantern almost big enough to wink back at the real moon",
        launch_text="It bobbed upward with such dignity you might have thought night had come early just to watch.",
        looming_text="The lantern drifted sideways, huge and pale, and even the gulls gave it room.",
        ending_text="At last it floated in a long silver sway, looking less like trouble and more like a story made visible.",
        danger_target="the old lighthouse lamp",
        pull=2,
        tags={"lantern", "wind"},
    ),
}

WINDS = {
    "breeze": Wind(
        id="breeze",
        label="sea breeze",
        gust_text="First came a busy little breeze, sniffing at hats and ribbons.",
        warning_text="This breeze is playful, not cruel,",
        force=1,
        tags={"breeze", "wind"},
    ),
    "bluster": Wind(
        id="bluster",
        label="blustering wind",
        gust_text="Then a blustering wind came shouldering in from the water, rolling coats and skirts like waves.",
        warning_text="That wind is growing broad-shouldered,",
        force=2,
        tags={"bluster", "wind"},
    ),
    "gale": Wind(
        id="gale",
        label="harbor gale",
        gust_text="At last a harbor gale came stamping down the esplanade, flapping coats like flags and sending gulls sideways.",
        warning_text="That gale has lifting hands,",
        force=3,
        tags={"gale", "wind"},
    ),
}

TETHERS = {
    "ribbon": Tether(
        id="ribbon",
        label="ribbon",
        phrase="a ribbon tied in a pretty bow",
        hold_text="Only a ribbon held it.",
        snap_text="The ribbon twanged like a fiddle string and parted",
        strength=1,
        sensible=1,
        tags={"ribbon"},
    ),
    "twine": Tether(
        id="twine",
        label="twine",
        phrase="a stout roll of twine",
        hold_text="A stout twine line hummed in Didey's hands.",
        snap_text="The twine jerked, shivered, and slipped loose",
        strength=2,
        sensible=2,
        tags={"twine"},
    ),
    "harbor_rope": Tether(
        id="harbor_rope",
        label="harbor rope",
        phrase="a harbor rope thick as Didey's wrist",
        hold_text="A harbor rope ran from small hands to sky like a road built for tugging.",
        snap_text="Even the rope groaned before it gave an inch",
        strength=3,
        sensible=3,
        tags={"rope"},
    ),
}

RESPONSES = {
    "anchor_post": Response(
        id="anchor_post",
        label="anchor post",
        text="caught the dragging line with his boathook and looped it around an iron mooring post before the next gust could steal it again",
        fail_text="the line slapped past his boathook, and the gust was stronger than his reach",
        qa_text="used a boathook and an iron mooring post to catch and secure the line",
        power=3,
        sense=3,
        tags={"boathook", "mooring"},
    ),
    "sand_cart": Response(
        id="sand_cart",
        label="sand cart",
        text="heaved a sand cart against the line and pinned it low until the wind spent its first wild temper",
        fail_text="the sand cart skidded, but the runaway pull dragged it a yard across the stones",
        qa_text="pinned the line with a heavy sand cart until the wind calmed",
        power=2,
        sense=2,
        tags={"sand_cart", "weight"},
    ),
    "grab_by_hand": Response(
        id="grab_by_hand",
        label="grab by hand",
        text="snatched at the line with his bare hands and held on",
        fail_text="his bare hands slipped on the whipping line, and he could not stop it",
        qa_text="tried to grab the line with his bare hands",
        power=1,
        sense=1,
        tags={"hands"},
    ),
}

GIRL_NAMES = ["Didey", "Mina", "Nell", "Tess", "Poppy", "June"]
BOY_NAMES = ["Didey", "Bram", "Finn", "Toby", "Ned", "Jory"]


@dataclass
class StoryParams:
    setting: str
    show: str
    wind: str
    tether: str
    response: str
    hero_name: str
    hero_type: str
    chief_name: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "esplanade": [
        (
            "What is an esplanade?",
            "An esplanade is a wide walking path, often beside the sea. People stroll there, look at the water, and feel the wind."
        )
    ],
    "kite": [
        (
            "Why does a kite need a strong line on a windy day?",
            "A kite pulls hard when the wind catches it. A strong line helps keep it from tearing loose and flying away."
        )
    ],
    "banner": [
        (
            "Why can a big banner be hard to hold in the wind?",
            "A banner catches lots of air because it is broad cloth. That makes the wind push and pull on it like a sail."
        )
    ],
    "lantern": [
        (
            "Why can a big paper lantern drift in the wind?",
            "A light paper lantern can be pushed sideways by gusts. If it is tethered badly, the wind can carry it off."
        )
    ],
    "wind": [
        (
            "Why is strong wind tricky near the sea?",
            "Sea wind can change quickly and blow in hard gusts. That means something that felt easy one minute can become hard to control the next."
        )
    ],
    "chief": [
        (
            "What does a harbor chief do?",
            "A harbor chief watches what is happening near the waterfront and helps keep people safe. A good chief notices trouble early and stays calm."
        )
    ],
    "rope": [
        (
            "Why is rope stronger than ribbon for heavy pulling?",
            "Rope is made to hold weight and strain. Ribbon is pretty, but it is not meant for strong tugging."
        )
    ],
    "mooring": [
        (
            "What is a mooring post for?",
            "A mooring post is a strong post used to hold lines steady. Boats and other heavy things can be secured to it so they do not drift away."
        )
    ],
    "weight": [
        (
            "Why does adding weight help stop something from blowing away?",
            "Extra weight makes it harder for the wind to pull an object along. The heavier base gives the line something solid to fight against."
        )
    ],
}
KNOWLEDGE_ORDER = ["esplanade", "chief", "kite", "banner", "lantern", "wind", "rope", "mooring", "weight"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for show_id, show in SHOWS.items():
            for wind_id, wind in WINDS.items():
                if hazard_possible(show, wind):
                    combos.append((setting_id, show_id, wind_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    show = f["show_cfg"]
    wind = f["wind_cfg"]
    outcome = f["outcome"]
    if outcome == "lost":
        return [
            f'Write a suspenseful tall tale for a young child about Didey on an esplanade with a harbor chief and a runaway {show.label}.',
            f"Tell a seaside tall tale where Didey brings a huge {show.label}, the {wind.label} rises, and everyone waits to see if the chief can stop it in time.",
            f'Write a story that uses the words "didey", "esplanade", and "chief", with suspense and a lesson about using strong gear in strong wind.',
        ]
    return [
        f'Write a suspenseful tall tale for a young child about Didey on an esplanade with a harbor chief and a giant {show.label}.',
        f"Tell a story where the wind grows, the line strains, and the chief keeps a small seaside disaster from becoming a great one.",
        f'Write a child-facing tall tale that includes the words "didey", "esplanade", and "chief", with a nervous middle and a safe ending.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    chief = f["chief"]
    setting = f["setting"]
    show = f["show_cfg"]
    wind = f["wind_cfg"]
    tether = f["tether_cfg"]
    response = f["response"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Didey, a child showing off a giant {show.label} on the {setting.place}, and the harbor chief who watches over the waterfront."
        ),
        (
            f"What did Didey bring to the {setting.place}?",
            f"Didey brought {show.phrase}. It was so large that everybody stopped to stare."
        ),
        (
            "Why did the story feel suspenseful?",
            f"The wind kept growing stronger, and the chief could see that {show.label} might get away. Everyone had to wait through those long heartbeats to learn whether the line would hold."
        ),
        (
            f"Why was the chief worried about the {tether.label}?",
            f"He knew the wind was strong and the {show.label} pulled hard. That meant the {tether.label} might not be enough to keep it from breaking loose."
        ),
    ]
    if f["broke"]:
        qa.append(
            (
                f"What happened when the {tether.label} failed?",
                f"The {show.label} broke away and swept toward {show.danger_target}. The crowd went quiet because the danger suddenly felt real."
            )
        )
        if f["saved"]:
            qa.append(
                (
                    "How did the chief save the day?",
                    f"He {response.qa_text}. That worked because his fix was stronger than the pull of the wind."
                )
            )
            qa.append(
                (
                    "How did the story end?",
                    f"It ended safely. Didey learned that big wind needs a steady hold, and the giant {show.label} flew properly instead of getting away."
                )
            )
        else:
            qa.append(
                (
                    "Could the chief stop the runaway show piece?",
                    f"No. He acted quickly, but the wind and pull were too strong for that method. Didey could only watch the lost {show.label} hang far above the town."
                )
            )
            qa.append(
                (
                    "What lesson did Didey learn?",
                    f"Didey learned that brave plans still need strong gear. A weak hold can turn a proud show into a sad tall tale."
                )
            )
    else:
        qa.append(
            (
                "Did the big show piece actually get away?",
                f"No. The line held, even though everyone feared it might not. That is what turned the suspense into relief."
            )
        )
        qa.append(
            (
                "What changed by the ending?",
                f"At first Didey cared most about making the biggest show on the esplanade. By the end, Didey also cared about doing it the safe and steady way."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"esplanade", "chief", "wind"}
    tags |= set(f["show_cfg"].tags)
    if f["tether_cfg"].id == "harbor_rope":
        tags.add("rope")
    if f["response"].id == "anchor_post":
        tags.add("mooring")
    if f["response"].id == "sand_cart":
        tags.add("weight")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:12} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="seaside",
        show="kite",
        wind="bluster",
        tether="twine",
        response="anchor_post",
        hero_name="Didey",
        hero_type="girl",
        chief_name="Chief Bram",
    ),
    StoryParams(
        setting="festival",
        show="banner",
        wind="gale",
        tether="ribbon",
        response="sand_cart",
        hero_name="Didey",
        hero_type="boy",
        chief_name="Chief Rowan",
    ),
    StoryParams(
        setting="harbor",
        show="lantern",
        wind="breeze",
        tether="harbor_rope",
        response="anchor_post",
        hero_name="Didey",
        hero_type="girl",
        chief_name="Chief Bram",
    ),
    StoryParams(
        setting="seaside",
        show="banner",
        wind="gale",
        tether="twine",
        response="grab_by_hand",
        hero_name="Didey",
        hero_type="boy",
        chief_name="Chief Rowan",
    ),
]


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it is known to the world but scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    show = SHOWS[params.show]
    wind = WINDS[params.wind]
    tether = TETHERS[params.tether]
    response = RESPONSES[params.response]
    if not breaks_loose(show, wind, tether):
        return "steady"
    return "saved" if response_works(show, wind, tether, response) else "lost"


ASP_RULES = r"""
hazard(S, W) :- show(S), wind(W), wind_ready(S), force(W, F), F >= 1.
valid(St, S, W) :- setting(St), show(S), wind(W), hazard(S, W).

trouble(S, W, T, V) :- pull(S, P), force(W, F), strength(T, H), V = P + F - H.
breaks(S, W, T) :- trouble(S, W, T, V), V >= 1.

sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
works(S, W, T, R) :- trouble(S, W, T, V), power(R, P), V >= 1, P >= V.
steady(S, W, T) :- not breaks(S, W, T).

outcome(steady) :- chosen_show(S), chosen_wind(W), chosen_tether(T), steady(S, W, T).
outcome(saved) :- chosen_show(S), chosen_wind(W), chosen_tether(T), chosen_response(R),
                  breaks(S, W, T), works(S, W, T, R).
outcome(lost) :- chosen_show(S), chosen_wind(W), chosen_tether(T), chosen_response(R),
                 breaks(S, W, T), not works(S, W, T, R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, show in SHOWS.items():
        lines.append(asp.fact("show", sid))
        if show.wind_ready:
            lines.append(asp.fact("wind_ready", sid))
        lines.append(asp.fact("pull", sid, show.pull))
    for wid, wind in WINDS.items():
        lines.append(asp.fact("wind", wid))
        lines.append(asp.fact("force", wid, wind.force))
    for tid, tether in TETHERS.items():
        lines.append(asp.fact("tether", tid))
        lines.append(asp.fact("strength", tid, tether.strength))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("power", rid, response.power))
        lines.append(asp.fact("sense", rid, response.sense))
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

    extra = "\n".join(
        [
            asp.fact("chosen_show", params.show),
            asp.fact("chosen_wind", params.wind),
            asp.fact("chosen_tether", params.tether),
            asp.fact("chosen_response", params.response),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: gate matches valid_combos() ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    clingo_sens = set(asp_sensible())
    python_sens = {r.id for r in sensible_responses()}
    if clingo_sens == python_sens:
        print(f"OK: sensible responses match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke-test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Suspenseful seaside tall-tale storyworld with Didey, an esplanade, and a chief."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--show", choices=SHOWS)
    ap.add_argument("--wind", choices=WINDS)
    ap.add_argument("--tether", choices=TETHERS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--chief-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.show is None or c[1] == args.show)
        and (args.wind is None or c[2] == args.wind)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, show_id, wind_id = rng.choice(sorted(combos))
    show = SHOWS[show_id]
    wind = WINDS[wind_id]

    tether_choices = [
        tid for tid, tether in TETHERS.items()
        if not breaks_loose(show, wind, tether) or any(response_works(show, wind, tether, r) for r in sensible_responses())
    ]
    if args.tether is not None:
        if args.tether not in tether_choices:
            raise StoryError("(No reasonable story uses that tether with the chosen wind and show.)")
        tether_id = args.tether
    else:
        tether_id = rng.choice(sorted(tether_choices))

    response_choices = [
        rid for rid, response in RESPONSES.items()
        if response.sense >= SENSE_MIN and (not breaks_loose(show, wind, TETHERS[tether_id]) or response_works(show, wind, TETHERS[tether_id], response))
    ]
    if args.response is not None:
        if args.response not in response_choices:
            raise StoryError("(That response cannot reasonably solve this version of the problem.)")
        response_id = args.response
    else:
        response_id = rng.choice(sorted(response_choices))

    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    chief_name = args.chief_name or rng.choice(["Chief Bram", "Chief Rowan", "Chief Hale"])

    return StoryParams(
        setting=setting_id,
        show=show_id,
        wind=wind_id,
        tether=tether_id,
        response=response_id,
        hero_name=hero_name,
        hero_type=hero_type,
        chief_name=chief_name,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        show = SHOWS[params.show]
        wind = WINDS[params.wind]
        tether = TETHERS[params.tether]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Unknown story parameter: {err.args[0]})") from None

    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if (params.setting, params.show, params.wind) not in set(valid_combos()):
        raise StoryError("(The chosen setting, show, and wind do not form a valid story frame.)")

    world = tell(
        setting=setting,
        show=show,
        wind=wind,
        tether=tether,
        response=response,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        chief_name=params.chief_name,
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
        print(f"{len(combos)} compatible (setting, show, wind) combos:\n")
        for setting_id, show_id, wind_id in combos:
            print(f"  {setting_id:10} {show_id:8} {wind_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.show} on the {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
