#!/usr/bin/env python3
"""
storyworlds/worlds/minimax_minimax-m3_service_20260625T022909Z_seed424242_n50/befriend_happy_ending_dialogue_sound_effects_bedtime.py
=============================================================================================================================

A standalone *story world* sketch for "The Quiet Sound at the Door" tale and close,
constraint-checked variations of it.

Initial story (used to build the world model):
---
Once upon a time, there was a little boy named Theo who was afraid of every
small sound at bedtime. Wind in the trees, the house ticking as it cooled,
a distant train -- each one made him pull the blanket up to his nose and
call for his mom.

One night, after his dad had said goodnight and turned out the lamp, Theo
heard a soft new sound just under his window. Tap tap. Tap tap tap. It was
gentle, but very steady, and Theo's heart beat fast. He whispered to his
stuffed bear, "What is that little sound, Bear? It might be scary."

Theo crept to the window on quiet feet. He pushed the curtain back a little
and looked down. There, sitting in the moonlight, was a small gray cat with
one torn ear. The cat looked up at him and mewed once, very small. Theo
felt his shoulders drop. The sound had not been scary at all. It was just a
hungry kitten, asking to come in.

Theo tiptoed downstairs and got a saucer of milk. He carried it back up and
set it gently on the windowsill. The kitten drank, and purred, and Theo's
bear seemed to nod from the pillow as if to say, "See? Some sounds are
friends." Theo smiled, climbed back into bed, and listened to the soft
purring outside his window as he fell asleep -- a happy sound, and a new
one.

Causal state updates (forward-chained from world state):
---
    night + small sound heard        -> actor.fear += 1
    sound identified as friendly     -> actor.fear -> 0 ; actor.joy += 1
    help offered to source of sound  -> source.trust += 1 ; actor.bravery += 1
    source accepts help              -> actor.friendship += 1 ; actor.belonging += 1
    source stays through the night   -> actor.calm += 1 ; actor.home += 1

Scripted social/emotional beats:
---
    bedtime routine                  -> actor.bedtime += 1
    parent tucks the child in        -> actor.loved += 1
    child whispers to a stuffed toy  -> actor.comfort_object += 1
    sound named with onomatopoeia    -> world.onomatopoeia += 1   (story contract)
    shared quiet moment at the end   -> actor.warmth += 1
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
# (``python storyworlds/worlds/<name>.py``): add the package dir (storyworlds/)
# to the path so ``results`` resolves regardless of the current directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0

# The catalogue of "sound families" the world recognises.  Each maps to a kind
# of source -- only friendly sources can be befriended, only scary ones raise
# fear that has to be named and resolved.
SCARY_KINDS = {"howl", "creak", "thump"}
NEUTRAL_KINDS = {"tap", "rustle", "hum"}
FRIENDLY_KINDS = {"mew", "purr", "chirp"}

# Onomatopoeia are the small words the story must use ("tap tap", "purrrrr")
# -- a hard story contract: every sample includes at least one onomatopoeia.
ONOMATOPOEIA = {
    "tap": "tap tap",
    "rustle": "rustle rustle",
    "hum": "hmmmmm",
    "howl": "aaaaooooo",
    "creak": "creeeak",
    "thump": "thump",
    "mew": "mew",
    "purr": "purrrrr",
    "chirp": "chirp chirp",
}

# Sound kinds we are willing to *narrate as scary-then-befriended*.  Anything
# outside this list (a burglar, a storm) is rejected at the gate -- the story
# genre is bedtime, and only gentle sources may be befriended.
BEFRIENDABLE = {"mew", "purr", "chirp"}


# ---------------------------------------------------------------------------
# Entities: characters, sources of sound, and comfort objects share one model.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "creature" | "object"
    type: str = "thing"            # boy, girl, mom, dad, cat, owl, bear ...
    label: str = ""                # short reference, e.g. "kitten", "bear"
    phrase: str = ""               # full noun phrase, e.g. "a small gray kitten"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    # Two numeric dimensions, treated uniformly (cf. story.py memeplex model):
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "mom"}
        male = {"boy", "father", "dad", "man", "kitten", "cat"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if getattr(self, "plural", False) else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this little domain.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    """Where the child sleeps and where the sound comes from."""
    place: str = "the bedroom"
    bed: str = "a small bed with a blue blanket"
    window: str = "the window"
    below: str = "the garden"        # where the source is sitting
    inside: bool = True              # bedroom scenes are indoors


@dataclass
class Sound:
    """The mysterious sound at the window, and the source making it."""
    id: str
    kind: str                        # one of NEUTRAL/SCARY/FRIENDLY
    onomatopoeia: str                # "tap tap", "purrrrr"
    verb: str                        # after "heard ... ": "tap softly"
    noun: str                        # what it sounded like to a scared child
    source: str                      # kitten | owlet | cricket | sparrow | small bird
    comfort: str                     # what soothes the source once befriended
    offer: str                       # phrase: "a saucer of milk"
    offer_verb: str                  # "set it on the windowsill"
    purr_back: str                   # the friendly sound the source gives back
    tag: str = ""


@dataclass
class Comfort:
    """The stuffed animal the child talks to when afraid."""
    id: str
    label: str                       # "bear"
    phrase: str                      # "a small stuffed bear"
    whisper: str                     # what the bear says: "we can be brave together"
    plural: bool = False


@dataclass
class Parent:
    """The caregiver who tucks the child in and is mentioned at the start."""
    type: str                        # mother | father
    label: str                       # "mom" | "dad"
    tuck: str                        # phrase used for tucking in


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()       # idempotency for the rule engine
        self.paragraphs: list[list[str]] = [[]]
        self.time: str = "night"
        self.onomatopoeia_used: list[str] = []
        # Facts recorded during the screenplay, read back by the Q&A generators.
        self.facts: dict = {}

    # -- entity helpers -----------------------------------------------------
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    # -- narration helpers --------------------------------------------------
    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        """Throwaway clone used for forward-simulation (prediction)."""
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.time = self.time
        clone.paragraphs = [[]]            # predictions are silent
        return clone


# ---------------------------------------------------------------------------
# Causal rules: forward-chained to a fixpoint.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_sound_kind_fear(world: World) -> list[str]:
    """If a non-befriendable sound is heard at night, fear rises."""
    out: list[str] = []
    sound = world.facts.get("sound")
    if not sound:
        return out
    if sound.kind in SCARY_KINDS and world.time == "night":
        for actor in world.characters():
            sig = ("fear", actor.id, sound.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["fear"] += 1
    # For our chosen befriended sources, sound is initially NEUTRAL -- the child
    # is *uncertain*, so the rule of thumb is: any non-befriendable source at
    # night raises fear; a befriendable source at first hearing is "wonder".
    elif sound.kind in NEUTRAL_KINDS and world.time == "night":
        for actor in world.characters():
            sig = ("wonder", actor.id, sound.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["wonder"] += 1
    return out


def _r_befriend(world: World) -> list[str]:
    """When the child offers help to a befriendable source, source.trust rises
    AND the child's bravery rises AND fear clears."""
    out: list[str] = []
    sound = world.facts.get("sound")
    if not sound:
        return out
    if sound.kind not in BEFRIENDABLE:
        return out
    src_id = world.facts.get("source_id")
    if not src_id or src_id not in world.entities:
        return out
    src = world.entities[src_id]
    for actor in world.characters():
        if actor.memes["offered_help"] < THRESHOLD:
            continue
        sig_trust = ("trust", src_id, actor.id)
        if sig_trust in world.fired:
            continue
        world.fired.add(sig_trust)
        src.meters["trust"] += 1
        actor.memes["bravery"] += 1
        # Fear resolves only when the friendly sound has been confirmed back.
        if world.facts.get("friend_confirmed"):
            actor.memes["fear"] = 0.0
            actor.memes["joy"] += 1
    return out


def _r_friend_response(world: World) -> list[str]:
    """When the source stays and replies with the friendly sound, friendship
    and belonging accumulate."""
    out: list[str] = []
    if not world.facts.get("friend_confirmed"):
        return out
    src_id = world.facts.get("source_id")
    if not src_id or src_id not in world.entities:
        return out
    src = world.entities[src_id]
    for actor in world.characters():
        sig = ("friend", actor.id, src_id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["friendship"] += 1
        actor.memes["belonging"] += 1
        actor.memes["calm"] += 1
        actor.meters["home"] += 1
        src.meters["comfort"] += 1
    return out


def _r_sleep(world: World) -> list[str]:
    """At the very end, when bedtime closes with a happy sound, warmth rises."""
    out: list[str] = []
    if not world.facts.get("fell_asleep"):
        return out
    for actor in world.characters():
        sig = ("sleep", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["warmth"] += 1
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="sound_kind_fear", tag="emotional", apply=_r_sound_kind_fear),
    Rule(name="befriend", tag="social", apply=_r_befriend),
    Rule(name="friend_response", tag="social", apply=_r_friend_response),
    Rule(name="sleep", tag="emotional", apply=_r_sleep),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    """Apply all rules until nothing new fires (forward chaining to fixpoint)."""
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
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers -- what is a *reasonable* befriending story.
# ---------------------------------------------------------------------------
def source_kind(sound: Sound) -> str:
    return sound.kind


def is_befriendable(sound: Sound) -> bool:
    return sound.kind in BEFRIENDABLE


def select_comfort(sound: Sound) -> Comfort:
    """Every befriended source is offered a small comfort -- the comfort is a
    property of the source, not a separate registry, so any sound has exactly
    one compatible comfort."""
    return COMFORTS[sound.comfort]


def select_parent(actor_type: str) -> Parent:
    """Default parent by actor gender; always returns a valid Parent."""
    if actor_type == "girl":
        return PARENTS["mother"]
    if actor_type == "boy":
        return PARENTS["father"]
    return PARENTS["mother"]


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def setting_open(world: World, hero: Entity, setting: Setting) -> None:
    world.say(
        f"The moon was up, and {world.setting.place} was quiet except for "
        f"the small ticking of the house going to sleep."
    )


def bedtime_routine(world: World, hero: Entity, parent: Parent) -> None:
    hero.memes["bedtime"] += 1
    world.say(
        f"{hero.id} was a little {hero.type} who was a little bit afraid "
        f"of every small sound after dark."
    )
    world.say(
        f"That night, after {parent.label} had said goodnight and turned "
        f"out the lamp, {hero.id} was lying in {world.setting.bed} "
        f"with the blanket pulled up to {hero.pronoun('possessive')} nose."
    )


def whispered_to_comfort(world: World, hero: Entity, comfort: Comfort) -> None:
    hero.memes["comfort_object"] += 1
    hero.memes["loved"] += 1
    bear = world.get(comfort.id) if comfort.id in world.entities else None
    if bear is None:
        bear = world.add(Entity(
            id=comfort.id, kind="object", type=comfort.id, label=comfort.label,
            phrase=comfort.phrase, owner=hero.id, caretaker=hero.id,
        ))
    world.say(
        f"{hero.id} hugged {hero.pronoun('possessive')} {comfort.label} "
        f"close and whispered, \"{comfort.whisper}.\""
    )


def mysterious_sound(world: World, hero: Entity, sound: Sound) -> None:
    world.facts["sound"] = sound
    world.time = "night"
    hero.memes["wonder"] += 1
    world.say(
        f"Just then, a soft new sound came from {world.setting.window}. "
        f"{sound.onomatopoeia.capitalize()}, {sound.onomatopoeia}. "
        f"It was gentle, but very steady, and {hero.id}'s heart beat fast."
    )
    world.onomatopoeia_used.append(sound.onomatopoeia)
    propagate(world, narrate=False)             # fire sound_kind_fear / wonder


def child_peek(world: World, hero: Entity, sound: Sound) -> None:
    world.say(
        f"{hero.id} crept to {world.setting.window} on quiet feet and "
        f"peeked through the curtain."
    )


def source_appears(world: World, hero: Entity, sound: Sound) -> Entity:
    """Add the source creature to the world and reveal it."""
    src = world.add(Entity(
        id=sound.source, kind="creature", type=sound.source, label=sound.source,
        phrase=SOUND_PHRASES[sound.source], traits=["small", "gentle"],
    ))
    world.facts["source_id"] = src.id
    world.say(
        f"There, sitting in the moonlight just under the window, was "
        f"{src.phrase}. It looked up at {hero.id} and went "
        f"\"{sound.onomatopoeia},\" very small."
    )
    hero.memes["wonder"] += 1
    src.meters["hunger"] += 1
    return src


def shoulders_drop(world: World, hero: Entity, sound: Sound) -> None:
    """The moment of realisation: the sound is friendly, not scary."""
    world.facts["friend_confirmed"] = True
    world.say(
        f"{hero.id} felt {hero.pronoun('possessive')} shoulders drop. "
        f"The sound had not been scary at all. It was just a hungry "
        f"{sound.source}, asking to come in."
    )


def offer_comfort(world: World, hero: Entity, parent: Parent, sound: Sound) -> None:
    hero.memes["offered_help"] += 1
    src = world.get(sound.source)
    world.say(
        f"{hero.id} tiptoed downstairs to the kitchen and came back with "
        f"{sound.offer}. {hero.pronoun().capitalize()} {sound.offer_verb} "
        f"and sat back on {hero.pronoun('possessive')} heels to wait."
    )
    propagate(world, narrate=False)             # fires befriend + friend_response


def source_responds(world: World, hero: Entity, sound: Sound) -> None:
    src = world.get(sound.source)
    world.say(
        f"The little {sound.source} drank, and then it began to "
        f"\"{sound.purr_back},\" so soft that {hero.id} could feel it "
        f"through the {world.setting.window} pane."
    )
    hero.memes["friendship"] += 1
    hero.memes["calm"] += 1


def comfort_replies(world: World, hero: Entity, comfort: Comfort) -> None:
    """The stuffed animal 'nods' in the story -- the comforting back-channel."""
    if comfort.id not in world.entities:
        return
    world.say(
        f"On the pillow, {hero.pronoun('possessive')} {comfort.label} "
        f"seemed to nod, as if to say, \"{comfort.whisper}.\""
    )


def bedtime_close(world: World, hero: Entity, sound: Sound, comfort: Comfort) -> None:
    world.facts["fell_asleep"] = True
    propagate(world, narrate=False)             # fires sleep -> warmth
    world.say(
        f"{hero.id} smiled, climbed back into {world.setting.bed}, and "
        f"pulled the blanket up. Outside the window, the little "
        f"{sound.source} kept on \"{sound.purr_back},\" a happy sound, "
        f"and a new one."
    )
    world.say(
        f"{hero.pronoun().capitalize()} listened to that sound as the "
        f"moonlight moved across the floor, and {hero.pronoun()} fell "
        f"asleep smiling."
    )


# ---------------------------------------------------------------------------
# The screenplay: bedtime beats, driven entirely by the verbs above.
# ---------------------------------------------------------------------------
def tell(setting: Setting, sound: Sound, comfort: Comfort, parent: Parent,
         hero_name: str = "Theo", hero_type: str = "boy",
         hero_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    world.time = "night"

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little", "shy"] + (hero_traits or ["gentle", "brave"]),
    ))
    # Comfort object exists in the world from the start so it can be referenced
    # consistently in dialogue and QA.
    world.add(Entity(
        id=comfort.id, kind="object", type=comfort.id, label=comfort.label,
        phrase=comfort.phrase, owner=hero.id, caretaker=hero.id,
    ))

    # Act 1 -- setup: who, where, the bedtime routine.
    setting_open(world, hero, setting)
    bedtime_routine(world, hero, parent)
    whispered_to_comfort(world, hero, comfort)

    # Act 2 -- the mysterious sound and its source.
    world.para()
    mysterious_sound(world, hero, sound)
    child_peek(world, hero, sound)
    src = source_appears(world, hero, sound)
    shoulders_drop(world, hero, sound)

    # Act 3 -- the happy ending: offer comfort, hear the friendly sound back,
    # fall asleep smiling.
    world.para()
    offer_comfort(world, hero, parent, sound)
    source_responds(world, hero, sound)
    comfort_replies(world, hero, comfort)
    bedtime_close(world, hero, sound, comfort)

    world.facts.update(
        hero=hero, parent=parent, sound=sound, comfort=comfort,
        src=src, setting=setting,
        befriended=True, fell_asleep=True,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "bedroom": Setting(
        place="the bedroom",
        bed="a small bed with a blue blanket",
        window="the window",
        below="the garden",
        inside=True,
    ),
    "loft": Setting(
        place="the loft",
        bed="a big bed under the sloping roof",
        window="the round window",
        below="the porch",
        inside=True,
    ),
    "cabin": Setting(
        place="the cabin",
        bed="a bunk with a patchwork quilt",
        window="the little window",
        below="the woodpile",
        inside=True,
    ),
}

SOUND_PHRASES = {
    "kitten": "a small gray kitten with one torn ear",
    "owlet": "a tiny owlet with wide, surprised eyes",
    "sparrow": "a small sparrow with feathers all fluffed up",
    "cricket": "a friendly cricket with long, twitching whiskers",
}

# Order matters: NEUTRAL first (the child hears a sound, does not know what it
# is yet), then SCARY variants (which our bedtime story rejects at the gate),
# then the *befriended* sources whose onomatopoeia become the happy ending.
SOUNDS = {
    "kitten": Sound(
        id="kitten",
        kind="mew",                       # friendly sound, the gate accepts
        onomatopoeia="tap tap",
        verb="tap softly",
        noun="a small tap",
        source="kitten",
        comfort="milk",
        offer="a saucer of warm milk",
        offer_verb="set it on the windowsill",
        purr_back="purrrrr",
        tag="kitten",
    ),
    "owlet": Sound(
        id="owlet",
        kind="chirp",
        onomatopoeia="rustle rustle",
        verb="rustle softly",
        noun="a soft rustle",
        source="owlet",
        comfort="crumbs",
        offer="a few soft crumbs",
        offer_verb="scattered them on the sill",
        purr_back="chirp chirp",
        tag="owlet",
    ),
    "sparrow": Sound(
        id="sparrow",
        kind="chirp",
        onomatopoeia="hum",
        verb="hum quietly",
        noun="a tiny hum",
        source="sparrow",
        comfort="seed",
        offer="a little pile of seed",
        offer_verb="spread it on the ledge",
        purr_back="chirp chirp",
        tag="sparrow",
    ),
    "cricket": Sound(
        id="cricket",
        kind="chirp",
        onomatopoeia="tap tap",
        verb="tap softly",
        noun="a small tap",
        source="cricket",
        comfort="crumb",
        offer="a single soft crumb",
        offer_verb="set it near the sill",
        purr_back="chirp chirp",
        tag="cricket",
    ),
}

COMFORTS = {
    "milk": Comfort(
        id="bear",
        label="bear",
        phrase="a small stuffed bear",
        whisper="we can be brave together",
    ),
    "crumbs": Comfort(
        id="rabbit",
        label="rabbit",
        phrase="a soft stuffed rabbit",
        whisper="a friend is just a sound away",
    ),
    "seed": Comfort(
        id="fox",
        label="fox",
        phrase="a floppy stuffed fox",
        whisper="listen closely, little friend",
    ),
    "crumb": Comfort(
        id="mouse",
        label="mouse",
        phrase="a tiny stuffed mouse",
        whisper="every sound has a name",
    ),
}

PARENTS = {
    "mother": Parent(type="mother", label="mom",
                     tuck="tucked the blanket under her chin"),
    "father": Parent(type="father", label="dad",
                     tuck="smoothed the blanket flat"),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Theo", "Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli"]
NEUTRAL_NAMES = ["Robin", "Sage", "Wren"]
TRAITS = ["gentle", "brave", "shy", "kind", "soft-spoken", "careful"]


def valid_combos() -> list[tuple[str, str]]:
    """(place, sound) pairs that pass the reasonableness constraint."""
    combos = []
    for place in SETTINGS:
        for sound_id in SOUNDS:
            sound = SOUNDS[sound_id]
            if is_befriendable(sound):                 # only befriended sources
                combos.append((place, sound_id))
    return combos


# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific; the generic StorySample/QAItem live in
# storyworlds/results.py).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    place: str
    sound: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
# (3) Child-level world knowledge, keyed by topic.  These are answerable WITHOUT
# the story; they explain the *elements* the world is built from.
KNOWLEDGE = {
    "kitten": [("What sound does a kitten make?",
                "A small kitten makes a tiny \"mew\" sound when it wants "
                "attention, and a soft purring sound when it feels safe.")],
    "owlet": [("What is an owlet?",
               "An owlet is a very young owl, with fluffy feathers and big "
               "round eyes. It makes a small chirping sound.")],
    "sparrow": [("Where do sparrows sleep?",
                 "Sparrows like to sleep in hedges, ivy, or little holes in "
                 "walls, where they are tucked away from the wind.")],
    "cricket": [("Why does a cricket chirp at night?",
                 "A cricket chirps by rubbing its wings together, and the "
                 "warm nights make it chirp faster.")],
    "bedtime": [("Why do people feel afraid of small sounds at bedtime?",
                 "At bedtime the house is quiet, so small sounds feel bigger "
                 "than they really are, and the dark makes it hard to see "
                 "where they come from.")],
    "friend": [("How do you make a new friend?",
                "You make a new friend by being gentle, offering something "
                "kind, and listening to what the other one needs.")],
    "onomatopoeia": [("What is an onomatopoeia?",
                      "An onomatopoeia is a word that sounds like the thing "
                      "it names, like \"tap,\" \"purr,\" or \"chirp.\"")],
    "moonlight": [("What is moonlight?",
                   "Moonlight is the light that comes from the moon at "
                   "night. It is softer than sunlight and makes shadows "
                   "look silvery.")],
}
KNOWLEDGE_ORDER = ["kitten", "owlet", "sparrow", "cricket",
                   "bedtime", "friend", "onomatopoeia", "moonlight"]


def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this one."""
    f = world.facts
    hero, sound, parent = f["hero"], f["sound"], f["parent"]
    kw = sound.source
    return [
        f'Write a gentle bedtime story for a 3-to-5-year-old about a child '
        f'who hears a small sound at the window and makes a new friend. '
        f'Include the word "{kw}".',
        f'Tell a quiet story where {hero.id} listens to a "{sound.onomatopoeia}" '
        f'sound from outside, finds a little {sound.source}, and falls asleep '
        f'smiling with a happy sound in {hero.pronoun("possessive")} ears.',
        f'Write a bedtime story that uses the onomatopoeia "{sound.onomatopoeia}" '
        f'and ends with a child and a small creature sharing a calm moment.',
    ]


def story_qa(world: World) -> list[QAItem]:
    """(2) Questions answerable from the text/world of THIS story."""
    f = world.facts
    hero, parent, sound = f["hero"], f["parent"], f["sound"]
    comfort = f["comfort"]
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    place = world.setting.place
    trait = next((t for t in hero.traits if t not in {"little", "shy"}), hero.type)
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about when {hero.id} hears a sound at "
                f"{world.setting.window} on a bedtime in {place}?"
            ),
            answer=(
                f"It is about a little {trait} {hero.type} named {hero.id}, "
                f"who was a little bit afraid of small sounds at night. "
                f"{pos.capitalize()} {parent.label} had just said goodnight."
            ),
        ),
        QAItem(
            question=(
                f"What was the mysterious sound {trait} {hero.id} heard from "
                f"{world.setting.window} in {place}?"
            ),
            answer=(
                f"It was a soft \"{sound.onomatopoeia}\" sound, very gentle and "
                f"steady. When {hero.id} peeked through the curtain, the sound "
                f"turned out to be a small {sound.source} sitting in the moonlight."
            ),
        ),
        QAItem(
            question=(
                f"What did {trait} {hero.id} whisper to {pos} {comfort.label} "
                f"when {sub} first heard the sound at {world.setting.window}?"
            ),
            answer=(
                f"{sub.capitalize()} hugged the {comfort.label} close and "
                f"whispered, \"{comfort.whisper}.\""
            ),
        ),
        QAItem(
            question=(
                f"How did {trait} {hero.id} make friends with the {sound.source} "
                f"at {world.setting.window} in {place}?"
            ),
            answer=(
                f"{sub.capitalize()} tiptoed downstairs and brought back "
                f"{sound.offer}. {sub.capitalize()} {sound.offer_verb} and "
                f"waited. The little {sound.source} drank, and began to "
                f"\"{sound.purr_back},\" a happy sound."
            ),
        ),
        QAItem(
            question=(
                f"How did {trait} {hero.id} feel at the end of the bedtime in "
                f"{place} with the {sound.source}?"
            ),
            answer=(
                f"{sub.capitalize()} felt calm and brave, and fell asleep "
                f"smiling with the happy \"{sound.purr_back}\" sound outside "
                f"{world.setting.window}. The {comfort.label} seemed to nod "
                f"as if to say, \"{comfort.whisper}.\""
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Generic, child-level questions about the world's elements."""
    f = world.facts
    sound = f["sound"]
    tags = {"bedtime", "friend", "onomatopoeia", "moonlight", sound.source}
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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


# ---------------------------------------------------------------------------
# CLI / trace
# ---------------------------------------------------------------------------
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
        lines.append(f"  {e.id:9} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  onomatopoeia used: {world.onomatopoeia_used}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(
        place="bedroom", sound="kitten",
        name="Theo", gender="boy", parent="father", trait="gentle",
    ),
    StoryParams(
        place="loft", sound="owlet",
        name="Lily", gender="girl", parent="mother", trait="brave",
    ),
    StoryParams(
        place="cabin", sound="sparrow",
        name="Finn", gender="boy", parent="mother", trait="soft-spoken",
    ),
    StoryParams(
        place="bedroom", sound="cricket",
        name="Mia", gender="girl", parent="father", trait="careful",
    ),
]


def explain_rejection(sound: Sound) -> str:
    return (f"(No story: a '{sound.id}' sound is not in the befriended set for "
            f"this bedtime world -- the genre requires a small, gentle source "
            f"the child can befriend. Try one of: {sorted(BEFRIENDABLE)}.)")


def explain_gender(gender: str) -> str:
    return (f"(No story: a {gender} protagonist is supported; the parent is "
            f"chosen to match. Try --gender boy|girl.)")


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of the reasonableness gate
# (is_befriendable / valid_combos).  The rules are inline below; the facts are
# generated from the registries above so the two can never drift.  Uses the
# shared `asp` helper + clingo, imported lazily so the prose engine runs
# without them.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A source is befriendable when its sound_kind is in the befriended set
% (the bedtime contract: only gentle sources may be befriended).
befriendable(S) :- source(S), sound_kind(S, K), befriend_kind(K).

% A (place, sound) is valid when the source is befriendable (any indoor
% bedroom-class place can host the encounter; the world is small and
% explicitly indoors).
valid(Place, S) :- setting(Place), source(S), befriendable(S).
valid_story(Place, S, Gender) :- valid(Place, S), protagonist(Gender).
"""


def asp_facts() -> str:
    """Emit the registries above as ASP base facts."""
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.inside:
            lines.append(asp.fact("indoor", pid))
    for sid, snd in SOUNDS.items():
        lines.append(asp.fact("source", sid))
        lines.append(asp.fact("sound_kind", sid, snd.kind))
    for k in sorted(BEFRIENDABLE):
        lines.append(asp.fact("befriend_kind", k))
    for g in ("boy", "girl"):
        lines.append(asp.fact("protagonist", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    """Clingo's version of valid_combos(): (place, sound) pairs."""
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    """(place, sound, gender) -- gender-aware compatible stories."""
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    """Check the inline ASP gate agrees with the Python valid_combos()."""
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Standard storyworld interface (see storyworlds/AGENTS.md):
#   build_parser() -> ArgumentParser
#   resolve_params(args, rng) -> StoryParams        (random where unspecified)
#   generate(params) -> StorySample                  (the core; world -> story+QA)
#   emit(sample, ...) -> None                        (human-readable output)
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child hears a small sound at bedtime "
                    "and makes a new friend. Unspecified choices are picked at "
                    "random (seeded).")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    # Clingo (ASP) modes -- the inline declarative reasoner (needs clingo).
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    """Fill in any unspecified choices at random, keeping the combo reasonable.

    Raises StoryError if the *explicit* options describe an invalid story."""
    if args.sound and not is_befriendable(SOUNDS[args.sound]):
        raise StoryError(explain_rejection(SOUNDS[args.sound]))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.sound is None or c[1] == args.sound)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, sound_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        sound=sound_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    sound = SOUNDS[params.sound]
    comfort = select_comfort(sound)
    parent = PARENTS[params.parent]
    world = tell(SETTINGS[params.place], sound, comfort, parent,
                 params.name, params.gender, [params.trait, "shy"])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(pairs)} compatible (place, sound) combos "
              f"({len(stories)} with gender):\n")
        for place, snd in pairs:
            genders = sorted(g for (pl, s, g) in stories
                             if (pl, s) == (place, snd))
            print(f"  {place:9} {snd:9}  [{', '.join(genders)}]")
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
            header = f"### {p.name}: {p.sound} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
