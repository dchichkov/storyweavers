#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/persona_sound_effects_friendship_ghost_story.py
============================================================================

A standalone storyworld about two friends who hear spooky sounds, investigate
them, and discover a lonely child hiding behind a homemade ghost persona.

The world is small on purpose: a place has a certain kind of dimness and hiding
spot; a ghost persona fits only some places; a response must be gentle enough to
turn fear into friendship. The story is driven by simulated state, not by
swapping words into one fixed paragraph.

Run it
------
    python storyworlds/worlds/gpt-5.4/persona_sound_effects_friendship_ghost_story.py
    python storyworlds/worlds/gpt-5.4/persona_sound_effects_friendship_ghost_story.py --place attic --persona sheet
    python storyworlds/worlds/gpt-5.4/persona_sound_effects_friendship_ghost_story.py --response yank_mask
    python storyworlds/worlds/gpt-5.4/persona_sound_effects_friendship_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/persona_sound_effects_friendship_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/persona_sound_effects_friendship_ghost_story.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    opening: str
    hiding_spot: str
    ambient: str
    echoes: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Persona:
    id: str
    label: str
    phrase: str
    sound: str
    motion: str
    reveal: str
    reason: str
    fits: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Light:
    id: str
    label: str
    phrase: str
    glow: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    line: str
    follow: str
    qa_text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_noise_scares(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    if ghost.meters["noise"] < THRESHOLD:
        return out
    for kid in (world.get("lead"), world.get("friend")):
        sig = ("fear", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["fear"] += 1
        out.append("__fear__")
    return out


def _r_lonely_hides(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    if ghost.memes["lonely"] < THRESHOLD or ghost.meters["covered"] < THRESHOLD:
        return out
    sig = ("hiding", ghost.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.memes["shy"] += 1
    out.append("__shy__")
    return out


CAUSAL_RULES = [
    Rule(name="noise_scares", tag="emotion", apply=_r_noise_scares),
    Rule(name="lonely_hides", tag="emotion", apply=_r_lonely_hides),
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


def persona_fits(place: Place, persona: Persona) -> bool:
    return place.id in persona.fits


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def predict_reveal(place: Place, persona: Persona, response: Response) -> dict:
    if not persona_fits(place, persona):
        return {"friendly": False, "reason": "persona mismatch"}
    if response.sense < SENSE_MIN:
        return {"friendly": False, "reason": "rude response"}
    return {"friendly": True, "reason": "gentle reveal"}


def perform_persona(world: World, ghost: Entity, persona: Persona) -> None:
    ghost.meters["covered"] += 1
    ghost.meters["noise"] += 1
    world.facts["sound"] = persona.sound
    world.say(
        f"Then {persona.sound} came from {world.place.hiding_spot}, and something {persona.motion} in the dark."
    )
    propagate(world, narrate=False)


def setup(world: World, lead: Entity, friend: Entity, light: Light) -> None:
    for kid in (lead, friend):
        kid.memes["joy"] += 1
    world.say(world.place.opening)
    world.say(
        f"{lead.id} and {friend.id} were sharing stories and making tiny sound effects with their mouths. "
        f'{lead.id} whispered "boo," and {friend.id} answered with a soft "oooo," until they both giggled.'
    )
    world.say(
        f"But {world.place.ambient} and the room around them felt a little too still."
    )
    world.facts["light_phrase"] = light.phrase


def first_fear(world: World, lead: Entity, friend: Entity, light: Light) -> None:
    lead.memes["bravery"] += 1
    world.say(
        f'{friend.id} scooted closer. "{world.place.echoes}" {friend.pronoun()} whispered. '
        f'{lead.id} clicked on {light.phrase}, and the beam {light.glow}.'
    )


def choose_gentle_voice(world: World, lead: Entity, friend: Entity, response: Response) -> None:
    lead.memes["kindness"] += 1
    friend.memes["trust"] += 1
    world.say(
        f'{lead.id} took a slow breath. "{response.line}" {lead.pronoun()} said.'
    )
    world.say(response.follow)


def reveal_friend(world: World, ghost: Entity, persona: Persona) -> None:
    ghost.meters["covered"] = 0.0
    ghost.memes["fear"] = 0.0
    ghost.memes["trust"] += 1
    world.say(
        f"Out stepped {ghost.id}, not a real ghost at all, but a child wrapped in {persona.phrase}. "
        f"{persona.reveal}"
    )
    world.say(
        f'"I was trying out a ghost persona," {ghost.id} admitted. "{persona.reason}"'
    )


def mend_feelings(world: World, lead: Entity, friend: Entity, ghost: Entity, persona: Persona) -> None:
    for kid in (lead, friend):
        kid.memes["fear"] = 0.0
        kid.memes["joy"] += 1
        kid.memes["friendship"] += 1
    ghost.memes["lonely"] = 0.0
    ghost.memes["joy"] += 1
    ghost.memes["friendship"] += 1
    world.say(
        f'{friend.id} let out the breath {friend.pronoun()} had been holding. '
        f'"You scared us," {friend.pronoun()} said, "but that was a very spooky idea."'
    )
    world.say(
        f'{lead.id} smiled at {ghost.id}. "You do not have to hide to join us. '
        f'We can make a ghost story together."'
    )
    world.say(
        f"Together they improved the act: one child made {persona.sound}, another fluttered the cloth, "
        f"and another tapped the floor for extra shivers."
    )


def ending(world: World, lead: Entity, friend: Entity, ghost: Entity, light: Light) -> None:
    world.say(
        f"Soon the three friends were putting on a pretend haunting for the dust and moonbeams. "
        f"{light.phrase.capitalize()} lay between them, {light.glow}, while their new game sounded like "
        f'"whooo, tap tap, creak," and nobody felt alone anymore.'
    )


def tell(
    place: Place,
    persona: Persona,
    light: Light,
    response: Response,
    lead_name: str = "Lila",
    lead_gender: str = "girl",
    friend_name: str = "Ben",
    friend_gender: str = "boy",
    hidden_name: str = "Nora",
    hidden_gender: str = "girl",
) -> World:
    world = World(place=place)
    lead = world.add(Entity(id="lead", kind="character", type=lead_gender, label=lead_name, role="lead"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="friend"))
    ghost = world.add(
        Entity(
            id="ghost",
            kind="character",
            type=hidden_gender,
            label=hidden_name,
            role="hidden",
            tags=set(persona.tags),
        )
    )

    ghost.memes["lonely"] += 1
    world.facts.update(place=place, persona=persona, light=light, response=response)

    setup(world, lead, friend, light)
    world.para()
    perform_persona(world, ghost, persona)
    first_fear(world, lead, friend, light)
    world.para()
    choose_gentle_voice(world, lead, friend, response)
    reveal_friend(world, ghost, persona)
    world.para()
    mend_feelings(world, lead, friend, ghost, persona)
    ending(world, lead, friend, ghost, light)

    world.facts.update(
        lead=lead,
        friend=friend,
        hidden=ghost,
        sound=persona.sound,
        friendly_reveal=True,
        place_id=place.id,
        persona_id=persona.id,
        response_id=response.id,
    )
    return world


PLACES = {
    "attic": Place(
        id="attic",
        label="attic",
        opening="On a rainy evening, the attic above Grandma's stairs glowed with a thin silver line of moonlight.",
        hiding_spot="an old trunk under the eaves",
        ambient="the rafters gave a long creak, and old coats swayed on their hooks",
        echoes="Did you hear that?",
        tags={"attic", "ghost"},
    ),
    "hallway": Place(
        id="hallway",
        label="hallway",
        opening="Late in the school playhouse, the long hallway looked pale and hush-hush, like a place in a bedtime ghost story.",
        hiding_spot="the curtain by the costume rack",
        ambient="the floorboards waited with their own little creaks",
        echoes="Something moved by the costumes",
        tags={"hallway", "ghost"},
    ),
    "shed": Place(
        id="shed",
        label="garden shed",
        opening="At the edge of the garden, the old shed stood in blue evening light, with one tiny window shining like a sleepy eye.",
        hiding_spot="the stack of rakes and paint tins",
        ambient="the wooden walls popped softly as the night air cooled",
        echoes="That came from inside the shed",
        tags={"shed", "ghost"},
    ),
}

PERSONAS = {
    "sheet": Persona(
        id="sheet",
        label="sheet ghost",
        phrase="a white sheet with two careful eye holes",
        sound='"whoooo... swish... whoooo"',
        motion="drifted and rustled",
        reveal="The cloth slipped from the child's head, and a shy face blinked out from underneath.",
        reason="I thought if I looked mysterious first, maybe nobody would notice I was the new kid.",
        fits={"attic", "hallway"},
        tags={"sheet", "sound_effects", "friendship"},
    ),
    "lantern_mask": Persona(
        id="lantern_mask",
        label="glow-mask ghost",
        phrase="a paper mask painted with moon-pale loops and a little lamp behind it",
        sound='"ooo-ooo, tap tap"',
        motion="bobbed with a pale wobble",
        reveal="The little lamp lit the child's cheeks from below, and the mask folded down into laughing hands.",
        reason="I wanted to make a spooky show, but I did not know how to ask to play.",
        fits={"hallway", "shed"},
        tags={"mask", "sound_effects", "friendship"},
    ),
    "tin_chain": Persona(
        id="tin_chain",
        label="tin-chain ghost",
        phrase="an old blanket cape and a loop of shiny bottle caps",
        sound='"clink-clink... creak... clink"',
        motion="shivered and rattled",
        reveal="The bottle caps stopped jangling, and a nervous child peeped out from behind the blanket cape.",
        reason="I made the noises to sound brave, because I felt lonely all by myself out here.",
        fits={"shed", "attic"},
        tags={"chain", "sound_effects", "friendship"},
    ),
}

LIGHTS = {
    "flashlight": Light(
        id="flashlight",
        label="flashlight",
        phrase="a small flashlight",
        glow="cut a clean path through the dark",
        tags={"flashlight"},
    ),
    "lantern": Light(
        id="lantern",
        label="lantern",
        phrase="a camping lantern",
        glow="glowed warm and round on the floorboards",
        tags={"lantern"},
    ),
    "star_lamp": Light(
        id="star_lamp",
        label="star lamp",
        phrase="a little star lamp",
        glow="sprinkled star shapes over the wall",
        tags={"lamp"},
    ),
}

RESPONSES = {
    "soft_hello": Response(
        id="soft_hello",
        sense=3,
        line="If you are real, we are not here to be mean",
        follow="The beam stayed low and gentle instead of flashing right in the hidden face.",
        qa_text="spoke softly and showed they wanted to be kind",
        tags={"kindness"},
    ),
    "share_light": Response(
        id="share_light",
        sense=3,
        line="You can come sit by our light if you want",
        follow="That made the darkness feel less like a trap and more like an invitation.",
        qa_text="offered to share the light",
        tags={"kindness", "light"},
    ),
    "invite_game": Response(
        id="invite_game",
        sense=2,
        line="That was a spooky sound effect; do you want to join our story",
        follow="Instead of running away, the children answered the strange noise like it was the start of a game.",
        qa_text="invited the hidden child into the game",
        tags={"kindness", "game"},
    ),
    "yank_mask": Response(
        id="yank_mask",
        sense=1,
        line="Come out right now",
        follow="One scared tug would only make the hidden child feel worse.",
        qa_text="grabbed at the costume",
        tags={"rude"},
    ),
}

GIRL_NAMES = ["Lila", "Mia", "Nora", "Ella", "Zoe", "Ivy", "Rose", "Ava"]
BOY_NAMES = ["Ben", "Sam", "Leo", "Max", "Finn", "Noah", "Eli", "Theo"]


@dataclass
class StoryParams:
    place: str
    persona: str
    light: str
    response: str
    lead: str
    lead_gender: str
    friend: str
    friend_gender: str
    hidden: str
    hidden_gender: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="attic",
        persona="sheet",
        light="flashlight",
        response="share_light",
        lead="Lila",
        lead_gender="girl",
        friend="Ben",
        friend_gender="boy",
        hidden="Nora",
        hidden_gender="girl",
    ),
    StoryParams(
        place="hallway",
        persona="lantern_mask",
        light="lantern",
        response="soft_hello",
        lead="Mia",
        lead_gender="girl",
        friend="Leo",
        friend_gender="boy",
        hidden="Finn",
        hidden_gender="boy",
    ),
    StoryParams(
        place="shed",
        persona="tin_chain",
        light="star_lamp",
        response="invite_game",
        lead="Rose",
        lead_gender="girl",
        friend="Theo",
        friend_gender="boy",
        hidden="Ava",
        hidden_gender="girl",
    ),
]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place_id, place in PLACES.items():
        for persona_id, persona in PERSONAS.items():
            if persona_fits(place, persona):
                combos.append((place_id, persona_id))
    return sorted(combos)


def explain_rejection(place: Place, persona: Persona) -> str:
    return (
        f"(No story: the {persona.label} does not fit {place.label}. "
        f"That costume and sound setup make sense in {', '.join(sorted(persona.fits))}, "
        f"so pick a matching place.)"
    )


def explain_response(response_id: str) -> str:
    r = RESPONSES[response_id]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it is too harsh for this friendship story "
        f"(sense={r.sense} < {SENSE_MIN}). Try a gentler response such as {better}.)"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place, persona, hidden = f["place"], f["persona"], f["hidden"]
    return [
        'Write a ghost-story-style tale for a 3-to-5-year-old that includes the word "persona" and ends in friendship.',
        f"Tell a gentle spooky story where two friends hear {persona.sound} in the {place.label} and discover a lonely child hiding behind a ghost persona.",
        f"Write a child-facing story with sound effects, a scary turn, and a warm ending where {hidden.label} becomes part of the game instead of staying alone.",
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two friends"
    if a.type == "boy" and b.type == "boy":
        return "two friends"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead, friend, hidden = f["lead"], f["friend"], f["hidden"]
    place, persona, light, response = f["place"], f["persona"], f["light"], f["response"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(lead, friend)}, {lead.label} and {friend.label}, and a lonely child named {hidden.label}. "
            f"They meet in the {place.label} when a spooky noise pulls them together."
        ),
        (
            "What made the place feel spooky at first?",
            f"The {place.label} was dim and full of little sounds, and then {persona.sound} came from {place.hiding_spot}. "
            f"Those noises made the children think something ghostly might be there."
        ),
        (
            f"What was the ghost persona really made from?",
            f"It was not a real ghost at all. {hidden.label} was hiding in {persona.phrase} and using it to make a spooky persona."
        ),
        (
            f"Why was {hidden.label} hiding?",
            f"{hidden.label} felt lonely and did not know how to ask to join the game. "
            f"The ghost persona felt safer than walking out plainly and saying hello."
        ),
        (
            f"How did {lead.label} and {friend.label} make things better?",
            f"They did not shout or grab. They {response.qa_text}, which helped {hidden.label} feel safe enough to step out and talk."
        ),
        (
            "How did the story end?",
            f"It ended with the three children playing together by {light.phrase}. "
            f"The same spooky sound effects that caused fear at first became part of a happy game."
        ),
    ]
    return qa


KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a story that feels spooky and mysterious. In a child-friendly ghost story, the scary part often turns out to be safe in the end."
        )
    ],
    "sound_effects": [
        (
            "What are sound effects?",
            "Sound effects are noises used to make a story or game feel more real. People can make them with their mouths, with objects, or with little taps and rustles."
        )
    ],
    "friendship": [
        (
            "How can kindness help when something feels scary?",
            "Kindness can slow everyone down and make space for the truth. When people speak gently, a scary misunderstanding can turn into friendship."
        )
    ],
    "flashlight": [
        (
            "Why is a flashlight useful in the dark?",
            "A flashlight helps you see where things really are. That can make a dark place feel less confusing and less scary."
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern gives a steady glow that lights up the space around it. It can make a dark room feel warmer and easier to share."
        )
    ],
    "lamp": [
        (
            "What is a little lamp for?",
            "A little lamp gives soft light in a small place. Soft light can help people look closely without feeling startled."
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost", "sound_effects", "friendship", "flashlight", "lantern", "lamp"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"ghost", "sound_effects", "friendship"} | set(f["light"].tags)
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.label_word:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
fits(P, G) :- place(P), persona(G), allowed(G, P).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(P, G) :- fits(P, G).
friendly(P, G, R) :- valid(P, G), sensible(R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for persona_id, persona in PERSONAS.items():
        lines.append(asp.fact("persona", persona_id))
        for place_id in sorted(persona.fits):
            lines.append(asp.fact("allowed", persona_id, place_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sensible = set(asp_sensible())
    p_sensible = {r.id for r in sensible_responses()}
    if c_sensible == p_sensible:
        print(f"OK: sensible responses match ({sorted(c_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sensible)} python={sorted(p_sensible)}")

    smoke_cases = list(CURATED)
    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            print(f"OK: smoke story {idx} generated.")
        except Exception as err:
            rc = 1
            print(f"SMOKE TEST FAILED on curated case {idx}: {err}")

    try:
        params = resolve_params(build_parser().parse_args([]), random.Random(123))
        params.seed = 123
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: random smoke story generated.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED on random case: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a gentle ghost story with sound effects and friendship."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--persona", choices=PERSONAS)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name not in avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.persona:
        place = PLACES[args.place]
        persona = PERSONAS[args.persona]
        if not persona_fits(place, persona):
            raise StoryError(explain_rejection(place, persona))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.persona is None or combo[1] == args.persona)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, persona_id = rng.choice(combos)
    light_id = args.light or rng.choice(sorted(LIGHTS))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))

    lead_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    hidden_gender = rng.choice(["girl", "boy"])

    used: set[str] = set()
    lead = pick_name(rng, lead_gender, used)
    used.add(lead)
    friend = pick_name(rng, friend_gender, used)
    used.add(friend)
    hidden = pick_name(rng, hidden_gender, used)

    return StoryParams(
        place=place_id,
        persona=persona_id,
        light=light_id,
        response=response_id,
        lead=lead,
        lead_gender=lead_gender,
        friend=friend,
        friend_gender=friend_gender,
        hidden=hidden,
        hidden_gender=hidden_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.persona not in PERSONAS:
        raise StoryError(f"(Unknown persona: {params.persona})")
    if params.light not in LIGHTS:
        raise StoryError(f"(Unknown light: {params.light})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    place = PLACES[params.place]
    persona = PERSONAS[params.persona]
    light = LIGHTS[params.light]
    response = RESPONSES[params.response]

    if not persona_fits(place, persona):
        raise StoryError(explain_rejection(place, persona))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(response.id))

    world = tell(
        place=place,
        persona=persona,
        light=light,
        response=response,
        lead_name=params.lead,
        lead_gender=params.lead_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        hidden_name=params.hidden,
        hidden_gender=params.hidden_gender,
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
        print(asp_program("#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, persona) combos:\n")
        for place_id, persona_id in combos:
            print(f"  {place_id:8} {persona_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.place}: {p.persona} with {p.response}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
