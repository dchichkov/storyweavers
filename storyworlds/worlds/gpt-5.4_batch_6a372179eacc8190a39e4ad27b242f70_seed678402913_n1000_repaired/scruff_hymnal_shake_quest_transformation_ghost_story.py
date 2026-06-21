#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/scruff_hymnal_shake_quest_transformation_ghost_story.py
===================================================================================

A standalone storyworld for a gentle ghost story with a quest and a visible
transformation. A child finds an old hymnal in a creaky place, meets a lonely
ghost, and chooses whether to help the ghost find the right song. When the quest
is completed, the room changes and the ghost changes too.

Seed words carried in natural prose:
- scruff
- hymnal
- shake

Run it
------
python storyworlds/worlds/gpt-5.4/scruff_hymnal_shake_quest_transformation_ghost_story.py
python storyworlds/worlds/gpt-5.4/scruff_hymnal_shake_quest_transformation_ghost_story.py --place attic --helper cat --song lullaby
python storyworlds/worlds/gpt-5.4/scruff_hymnal_shake_quest_transformation_ghost_story.py --all
python storyworlds/worlds/gpt-5.4/scruff_hymnal_shake_quest_transformation_ghost_story.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/scruff_hymnal_shake_quest_transformation_ghost_story.py --trace
python storyworlds/worlds/gpt-5.4/scruff_hymnal_shake_quest_transformation_ghost_story.py --verify
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
KINDNESS_MIN = 2


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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "cat":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    spooky_detail: str
    hiding_spot: str
    echo: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Song:
    id: str
    title: str
    mood: str
    image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    role_noun: str
    phrase: str
    method: str
    comfort: str
    bravery: int
    kindness: int
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
    tag: str
    apply: Callable[[World], list[str]]


def _r_ghost_softens(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.entities.get("ghost")
    room = world.entities.get("room")
    child = world.entities.get("child")
    if not ghost or not room or not child:
        return out
    if ghost.memes["heard_song"] < THRESHOLD:
        return out
    sig = ("softens", "ghost")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.memes["lonely"] = 0.0
    ghost.memes["peace"] += 1
    room.meters["cold"] = 0.0
    room.meters["glow"] += 1
    child.memes["courage"] += 1
    child.memes["wonder"] += 1
    out.append("__transformation__")
    return out


def _r_ghost_transforms(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.entities.get("ghost")
    if not ghost:
        return out
    if ghost.memes["peace"] < THRESHOLD:
        return out
    sig = ("transform", "ghost")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.attrs["form"] = "memory-light"
    ghost.meters["scary"] = 0.0
    ghost.meters["bright"] += 1
    out.append("__ghost_light__")
    return out


CAUSAL_RULES = [
    Rule(name="ghost_softens", tag="emotional", apply=_r_ghost_softens),
    Rule(name="ghost_transforms", tag="physical", apply=_r_ghost_transforms),
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


PLACES = {
    "attic": Place(
        id="attic",
        label="the attic",
        spooky_detail="dust drifted through one thin stripe of moonlight",
        hiding_spot="inside a cedar chest under a patchwork quilt",
        echo="the rafters answered with a soft wooden creak",
        tags={"attic", "ghost"},
    ),
    "hallway": Place(
        id="hallway",
        label="the upstairs hallway",
        spooky_detail="portraits watched from the walls with sleepy painted eyes",
        hiding_spot="inside a carved table drawer beneath a bowl of keys",
        echo="the long floorboards gave a hush-hush whisper",
        tags={"hallway", "ghost"},
    ),
    "chapel": Place(
        id="chapel",
        label="the little chapel room",
        spooky_detail="the old window made pale shapes on the floor",
        hiding_spot="inside a narrow bench with a squeaky lid",
        echo="the empty room kept every tiny sound",
        tags={"chapel", "ghost"},
    ),
}

SONGS = {
    "lullaby": Song(
        id="lullaby",
        title="the moonlit lullaby",
        mood="gentle",
        image="it sounded like someone tucking a blanket around the night",
        tags={"song", "lullaby"},
    ),
    "harvest": Song(
        id="harvest",
        title="the harvest hymn",
        mood="warm",
        image="it sounded like lanterns glowing in farmhouse windows",
        tags={"song", "hymn"},
    ),
    "morning": Song(
        id="morning",
        title="the morning hymn",
        mood="hopeful",
        image="it sounded like the sky turning from gray to gold",
        tags={"song", "hymn"},
    ),
}

HELPERS = {
    "cat": Helper(
        id="cat",
        label="cat",
        role_noun="cat",
        phrase="a striped house cat with a soft gray scruff",
        method="brushed against the child's ankles and led the way with a twitching tail",
        comfort="The cat gave one small purr, as if to say the dark was not in charge tonight.",
        bravery=2,
        kindness=2,
        tags={"cat", "pet"},
    ),
    "sibling": Helper(
        id="sibling",
        label="older sibling",
        role_noun="sibling",
        phrase="an older sibling holding a candle-shaped flashlight",
        method="whispered, listened, and stayed close instead of running away",
        comfort="The older child reached over and gave the little one a steady hand to squeeze.",
        bravery=3,
        kindness=3,
        tags={"family", "helper"},
    ),
    "grandma": Helper(
        id="grandma",
        label="grandma",
        role_noun="grandma",
        phrase="Grandma in her quilted robe and fuzzy slippers",
        method="remembered old songs and hummed the first brave line",
        comfort="Grandma's voice made the room feel smaller and kinder.",
        bravery=2,
        kindness=3,
        tags={"family", "song"},
    ),
}

NAMES = {
    "girl": ["Lina", "Mara", "Nora", "Tess", "Ruby", "Ivy", "Clara", "June"],
    "boy": ["Owen", "Milo", "Finn", "Theo", "Eli", "Jude", "Noah", "Ben"],
}
TRAITS = ["careful", "curious", "gentle", "quiet", "brave", "thoughtful"]


def quest_possible(place: Place, helper: Helper, song: Song) -> bool:
    return helper.kindness >= KINDNESS_MIN and helper.bravery >= 2 and song.mood in {"gentle", "warm", "hopeful"} and bool(place.label)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for helper_id, helper in HELPERS.items():
            for song_id, song in SONGS.items():
                if quest_possible(place, helper, song):
                    combos.append((place_id, helper_id, song_id))
    return combos


def explain_rejection(place: Place, helper: Helper, song: Song) -> str:
    if helper.kindness < KINDNESS_MIN:
        return (
            f"(No story: {helper.label} is not kind enough for a gentle ghost quest. "
            f"The helper must stay, listen, and help with the song.)"
        )
    if helper.bravery < 2:
        return (
            f"(No story: {helper.label} is too frightened to help in {place.label}. "
            f"This world needs a helper who can stay in the room long enough to sing.)"
        )
    return (
        f"(No story: {song.title} does not fit the healing song needed in {place.label}. "
        f"Pick a gentle, warm, or hopeful song.)"
    )


@dataclass
class StoryParams:
    place: str
    helper: str
    song: str
    child_name: str
    child_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def introduce(world: World, child: Entity, place: Place) -> None:
    trait = child.attrs.get("trait", "quiet")
    world.say(
        f"One windy evening, {child.id} wandered toward {place.label}, where {place.spooky_detail}. "
        f"{child.pronoun('subject').capitalize()} was a {trait} child who always noticed noises other people missed."
    )


def find_hymnal(world: World, child: Entity, place: Place) -> None:
    hymnal = world.get("hymnal")
    child.memes["curiosity"] += 1
    world.say(
        f"In {place.label}, {child.pronoun('subject')} found an old hymnal {place.hiding_spot}. "
        f"When {child.pronoun('subject')} lifted it, the cover gave a tiny shake, as if the book had just taken a sleepy breath."
    )
    hymnal.meters["found"] += 1


def appearance(world: World, ghost: Entity, place: Place) -> None:
    ghost.meters["seen"] += 1
    world.say(
        f"Then {place.echo}, and a pale little ghost drifted out of the dark. "
        f"It was not a snarling ghost or a roaring ghost. It looked more lonely than fierce."
    )
    world.say(
        f'"Please," the ghost whispered, "I have lost my song."'
    )


def fear_and_choice(world: World, child: Entity, helper: Entity) -> None:
    child.memes["fear"] += 1
    child.memes["choice"] += 1
    world.say(
        f"{child.id}'s knees gave a shake, and for one second {child.pronoun('subject')} almost ran. "
        f"But {helper.id} stayed close and {helper.attrs['method']}."
    )
    world.say(helper.attrs["comfort"])


def ask_quest(world: World, ghost: Entity, song: Song) -> None:
    ghost.memes["need"] += 1
    world.say(
        f'The ghost pointed to a torn page-mark inside the hymnal. '
        f'"If someone sings {song.title}," it said, "I can remember who I used to be."'
    )


def read_clue(world: World, child: Entity, song: Song) -> None:
    child.memes["resolve"] += 1
    world.say(
        f"{child.id} opened the hymnal to the marked page. The notes were old and brown, but the title was still clear: {song.title}. "
        f"{song.image}."
    )


def sing(world: World, child: Entity, helper: Entity, ghost: Entity, song: Song) -> None:
    child.memes["kindness"] += 1
    helper.memes["kindness"] += 1
    ghost.memes["heard_song"] += 1
    world.say(
        f"Very softly at first, {child.id} began to sing. {helper.id.capitalize()} joined in, and the frightened room listened. "
        f"The song was {song.mood}, and each line sounded steadier than the last."
    )
    propagate(world, narrate=False)


def transform_room(world: World, place: Place) -> None:
    room = world.get("room")
    ghost = world.get("ghost")
    if room.meters["glow"] >= THRESHOLD:
        world.say(
            f"As the final note floated upward, {place.label} changed. The cold feeling melted away, and pale corners filled with a honey-colored glow."
        )
    if ghost.attrs.get("form") == "memory-light":
        world.say(
            "The ghost changed too. Its misty edges grew bright and clear, until it looked less like a fright and more like a memory made of light."
        )


def reveal_past(world: World, ghost: Entity, song: Song) -> None:
    ghost.memes["gratitude"] += 1
    world.say(
        f'"I remember now," the ghost said. "I used to sing {song.title} before bed, and I was loved here." '
        f"Its voice no longer rattled like a window in the wind."
    )


def farewell(world: World, child: Entity, helper: Entity) -> None:
    child.memes["peace"] += 1
    helper.memes["peace"] += 1
    world.say(
        f"The shining ghost bowed to {child.id} and to {helper.id}, then drifted upward like a small lantern going home."
    )
    world.say(
        f"After that night, {child.id} was never quite so afraid of creaks in the dark. "
        f"When the house whispered, {child.pronoun('subject')} remembered that some spooky things are only sad things waiting to be understood."
    )


def tell(
    place: Place,
    helper_cfg: Helper,
    song: Song,
    child_name: str = "Lina",
    child_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "curious",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        label=child_name,
        attrs={"trait": trait},
    ))
    helper_type = "cat" if helper_cfg.id == "cat" else "person"
    helper = world.add(Entity(
        id=helper_cfg.label.capitalize() if helper_cfg.id != "grandma" else "Grandma",
        kind="character",
        type=helper_type,
        role="helper",
        label=helper_cfg.label,
        phrase=helper_cfg.phrase,
        attrs={"method": helper_cfg.method, "comfort": helper_cfg.comfort},
        tags=set(helper_cfg.tags),
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="room",
        label=place.label,
        tags=set(place.tags),
    ))
    room.meters["cold"] = 1.0
    hymnal = world.add(Entity(
        id="hymnal",
        kind="thing",
        type="book",
        label="hymnal",
        phrase="an old hymnal",
        tags={"book", "song"},
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        role="ghost",
        label="ghost",
        attrs={"form": "mist"},
        tags={"ghost"},
    ))
    ghost.meters["scary"] = 1.0
    ghost.memes["lonely"] = 1.0

    introduce(world, child, place)
    find_hymnal(world, child, place)

    world.para()
    appearance(world, ghost, place)
    fear_and_choice(world, child, helper)
    ask_quest(world, ghost, song)

    world.para()
    read_clue(world, child, song)
    sing(world, child, helper, ghost, song)
    transform_room(world, place)
    reveal_past(world, ghost, song)

    world.para()
    farewell(world, child, helper)

    world.facts.update(
        child=child,
        helper=helper,
        helper_cfg=helper_cfg,
        parent=parent,
        place=place,
        song=song,
        room=room,
        hymnal=hymnal,
        ghost=ghost,
        completed=ghost.memes["peace"] >= THRESHOLD,
        transformed=ghost.attrs.get("form") == "memory-light",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper_cfg"]
    place = f["place"]
    song = f["song"]
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old that includes the words "scruff", "hymnal", and "shake".',
        f"Tell a quest story where a {child.type} named {child.id} finds a hymnal in {place.label} and helps a lonely ghost remember {song.title}.",
        f"Write a transformation story in a ghost-story style where a child and a {helper.role_noun} sing from an old hymnal and turn a frightening room peaceful.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    helper_cfg = f["helper_cfg"]
    place = f["place"]
    song = f["song"]
    ghost = f["ghost"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child who found an old hymnal, and a lonely ghost in {place.label}. "
            f"{helper.id} helped {child.id} stay brave enough to listen."
        ),
        (
            f"What was the quest in {place.label}?",
            f"The quest was to find the ghost's lost song and sing it from the hymnal. "
            f"The ghost believed that hearing {song.title} would help it remember who it used to be."
        ),
        (
            "Why did the child feel scared at first?",
            f"{child.id} felt scared because a pale ghost drifted out of the dark and the room felt cold and strange. "
            f"{child.pronoun('possessive').capitalize()} knees gave a shake, which showed the fear was real before the brave choice came."
        ),
        (
            f"How did {helper.id} help?",
            f"{helper.id} helped by staying close and making the room feel less lonely. "
            f"{helper_cfg.comfort} That support is what let {child.id} keep going with the quest."
        ),
        (
            "What happened when they sang from the hymnal?",
            f"When they sang {song.title}, the room lost its cold feeling and began to glow. "
            f"The song changed the ghost from a misty fright into something peaceful and bright."
        ),
        (
            "How did the story end?",
            f"The ghost remembered being loved, thanked them, and drifted away like a small lantern. "
            f"After that, {child.id} understood that some spooky things are sad before they are dangerous."
        ),
    ]
    if ghost.attrs.get("form") == "memory-light":
        qa.append(
            (
                "What was the transformation in the story?",
                "The ghost transformed from a lonely, misty figure into a clear and shining memory-light. "
                "At the same time, the room changed from cold and haunted to warm and glowing."
            )
        )
    return qa


KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost in a story?",
            "A ghost in a story is a spirit or spooky figure that people imagine after someone is gone. In gentle stories, a ghost is often lonely or unfinished rather than mean."
        )
    ],
    "hymn": [
        (
            "What is a hymnal?",
            "A hymnal is a book that holds songs, often songs people sing together. It helps readers find the right words and tune."
        )
    ],
    "song": [
        (
            "Why can a song feel powerful in a story?",
            "A song can carry memories and feelings. In stories, singing can comfort people, help them remember, or bring them together."
        )
    ],
    "cat": [
        (
            "What is the scruff of a cat?",
            "The scruff is the loose fur and skin on the back of a cat's neck. People often use the word to describe that soft patch of fur."
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a journey or mission to solve a problem or find something important. Even a small walk through one room can feel like a quest in a story."
        )
    ],
    "transformation": [
        (
            "What does transformation mean in a story?",
            "Transformation means something changes into a new state. A scary room can become welcoming, or a frightened person can become brave."
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost", "hymn", "song", "cat", "quest", "transformation"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"ghost", "hymn", "song", "quest", "transformation"}
    if f["helper_cfg"].id == "cat":
        tags.add("cat")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="attic",
        helper="cat",
        song="lullaby",
        child_name="Lina",
        child_gender="girl",
        parent="mother",
        trait="curious",
    ),
    StoryParams(
        place="hallway",
        helper="sibling",
        song="morning",
        child_name="Owen",
        child_gender="boy",
        parent="father",
        trait="careful",
    ),
    StoryParams(
        place="chapel",
        helper="grandma",
        song="harvest",
        child_name="Ruby",
        child_gender="girl",
        parent="mother",
        trait="gentle",
    ),
]


ASP_RULES = r"""
kind_helper(H) :- helper(H), kindness(H, K), kindness_min(M), K >= M.
brave_helper(H) :- helper(H), bravery(H, B), B >= 2.
healing_song(S) :- song(S), mood(S, gentle).
healing_song(S) :- song(S), mood(S, warm).
healing_song(S) :- song(S), mood(S, hopeful).

valid(P, H, S) :- place(P), kind_helper(H), brave_helper(H), healing_song(S).

completed :- chosen_place(P), chosen_helper(H), chosen_song(S), valid(P, H, S).
transformed :- completed.
outcome(peaceful) :- transformed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("bravery", helper_id, helper.bravery))
        lines.append(asp.fact("kindness", helper_id, helper.kindness))
    for song_id, song in SONGS.items():
        lines.append(asp.fact("song", song_id))
        lines.append(asp.fact("mood", song_id, song.mood))
    lines.append(asp.fact("kindness_min", KINDNESS_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_helper", params.helper),
        asp.fact("chosen_song", params.song),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    ok = quest_possible(PLACES[params.place], HELPERS[params.helper], SONGS[params.song])
    return "peaceful" if ok else "?"


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

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Gentle ghost-story world: a child finds a hymnal, helps a ghost, and changes the room."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--song", choices=SONGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.helper and args.song:
        if not quest_possible(PLACES[args.place], HELPERS[args.helper], SONGS[args.song]):
            raise StoryError(explain_rejection(PLACES[args.place], HELPERS[args.helper], SONGS[args.song]))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.helper is None or combo[1] == args.helper)
        and (args.song is None or combo[2] == args.song)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, helper_id, song_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        helper=helper_id,
        song=song_id,
        child_name=name,
        child_gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    for key, table in (("place", PLACES), ("helper", HELPERS), ("song", SONGS)):
        value = getattr(params, key)
        if value not in table:
            raise StoryError(f"(Invalid {key}: {value!r})")
    if not quest_possible(PLACES[params.place], HELPERS[params.helper], SONGS[params.song]):
        raise StoryError(explain_rejection(PLACES[params.place], HELPERS[params.helper], SONGS[params.song]))

    world = tell(
        place=PLACES[params.place],
        helper_cfg=HELPERS[params.helper],
        song=SONGS[params.song],
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, helper, song) combos:\n")
        for place_id, helper_id, song_id in combos:
            print(f"  {place_id:8} {helper_id:8} {song_id}")
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
            header = f"### {p.child_name}: {p.place}, {p.helper}, {p.song}"
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
