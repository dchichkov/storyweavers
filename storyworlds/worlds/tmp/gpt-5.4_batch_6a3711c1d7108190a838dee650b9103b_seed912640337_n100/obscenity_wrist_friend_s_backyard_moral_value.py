#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/obscenity_wrist_friend_s_backyard_moral_value.py
============================================================================

A small ghost-story-flavored storyworld about two children in a friend's backyard
who hear a rhyme in the dark, notice something strange on a wrist, and mistake
an ordinary backyard problem for a ghostly warning. The word "obscenity" appears
as part of a grown-up cleanup note about rude writing on a fence; the children do
not repeat any rude word itself.

The world model tracks simple physical meters and emotional memes so the prose is
driven by state: a creak or chime at dusk raises fear, a wrist mark plus a hard
word on a note deepens the misunderstanding, and a calm helper resolves both the
sound and the mark with a gentle moral about asking before guessing.

Run it
------
    python storyworlds/worlds/gpt-5.4/obscenity_wrist_friend_s_backyard_moral_value.py
    python storyworlds/worlds/gpt-5.4/obscenity_wrist_friend_s_backyard_moral_value.py --sound gate --mark vine
    python storyworlds/worlds/gpt-5.4/obscenity_wrist_friend_s_backyard_moral_value.py --note seed_packet
    python storyworlds/worlds/gpt-5.4/obscenity_wrist_friend_s_backyard_moral_value.py --all
    python storyworlds/worlds/gpt-5.4/obscenity_wrist_friend_s_backyard_moral_value.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/obscenity_wrist_friend_s_backyard_moral_value.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma"}.get(self.type, self.type)


@dataclass
class TimeOfDay:
    id: str
    sky: str
    glow: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SoundSource:
    id: str
    label: str
    place: str
    rhyme: str
    cause: str
    creepy: int
    tags: set[str] = field(default_factory=set)


@dataclass
class WristMark:
    id: str
    label: str
    text: str
    cause: str
    gentle_fix: str
    scary: int
    tags: set[str] = field(default_factory=set)


@dataclass
class NoteClue:
    id: str
    label: str
    text: str
    explanation: str
    mentions_obscenity: bool
    spooky: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    type: str
    entrance: str
    comfort: str
    lesson: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_night_fear(world: World) -> list[str]:
    out: list[str] = []
    sky = world.facts["time"]
    sound = world.get("sound")
    for kid_id in ("hero", "friend"):
        kid = world.get(kid_id)
        if sound.meters["rattling"] >= THRESHOLD and sky.id in {"dusk", "moonrise", "mist"}:
            sig = ("fear", kid.id)
            if sig not in world.fired:
                world.fired.add(sig)
                kid.memes["fear"] += 1
                out.append("__fear__")
    return out


def _r_mark_guess(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    mark = world.get("mark")
    note = world.get("note")
    if hero.memes["fear"] >= THRESHOLD and mark.meters["noticed"] >= THRESHOLD:
        sig = ("mark_guess",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["misunderstanding"] += 1
            world.get("friend").memes["misunderstanding"] += 1
            out.append("__guess__")
    if hero.memes["fear"] >= THRESHOLD and note.meters["read"] >= THRESHOLD and world.facts["note_cfg"].mentions_obscenity:
        sig = ("note_guess",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["misunderstanding"] += 1
            world.get("friend").memes["misunderstanding"] += 1
            out.append("__guess__")
    return out


def _r_explained_relief(world: World) -> list[str]:
    hero = world.get("hero")
    friend = world.get("friend")
    helper = world.get("helper")
    if helper.meters["explained"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in (hero, friend):
        kid.memes["fear"] = 0.0
        kid.memes["misunderstanding"] = 0.0
        kid.memes["relief"] += 1
        kid.memes["trust"] += 1
    return ["__relief__"]


CAUSAL_RULES = [
    Rule("night_fear", "emotional", _r_night_fear),
    Rule("mark_guess", "emotional", _r_mark_guess),
    Rule("explained_relief", "emotional", _r_explained_relief),
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


def note_is_spooky(note: NoteClue) -> bool:
    return note.mentions_obscenity and note.spooky >= 2


def sound_is_spooky(sound: SoundSource) -> bool:
    return sound.creepy >= 2


def valid_combo(time_id: str, sound_id: str, mark_id: str, note_id: str) -> bool:
    time_cfg = TIMES[time_id]
    sound = SOUNDS[sound_id]
    mark = MARKS[mark_id]
    note = NOTES[note_id]
    return time_cfg.id in {"dusk", "moonrise", "mist"} and sound_is_spooky(sound) and note_is_spooky(note) and mark.scary >= 1


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for t in TIMES:
        for s in SOUNDS:
            for m in MARKS:
                for n in NOTES:
                    if valid_combo(t, s, m, n):
                        combos.append((t, s, m, n))
    return combos


def predict_spook(time_cfg: TimeOfDay, sound: SoundSource, mark: WristMark, note: NoteClue) -> dict:
    fear = 1 if time_cfg.id in {"dusk", "moonrise", "mist"} and sound.creepy >= 2 else 0
    misunderstanding = 0
    if fear and mark.scary >= 1:
        misunderstanding += 1
    if fear and note.mentions_obscenity and note.spooky >= 2:
        misunderstanding += 1
    return {"fear": fear, "misunderstanding": misunderstanding}


def introduce(world: World, hero: Entity, friend: Entity, time_cfg: TimeOfDay) -> None:
    for kid in (hero, friend):
        kid.memes["curiosity"] += 1
    world.say(
        f"{time_cfg.sky.capitalize()}, {hero.id} was playing in {friend.id}'s backyard. "
        f"{time_cfg.glow}"
    )
    world.say(
        f"{hero.id} and {friend.id} were making leaf boats beside the garden bed and pretending "
        f"the tomato stakes were a tiny forest."
    )


def first_shiver(world: World, sound_cfg: SoundSource) -> None:
    sound = world.get("sound")
    sound.meters["rattling"] += 1
    world.say(
        f"Then something sounded from {sound_cfg.place}: {sound_cfg.rhyme}. "
        f"It was only a backyard noise, but in the growing dark it felt like a ghost rhyme."
    )
    propagate(world, narrate=False)


def notice_mark(world: World, hero: Entity, mark_cfg: WristMark) -> None:
    mark = world.get("mark")
    mark.meters["noticed"] += 1
    world.say(
        f"{hero.id} looked down and saw {mark_cfg.text} on {hero.pronoun('possessive')} wrist. "
        f"For one little gulp, it felt as if invisible fingers had brushed past."
    )
    propagate(world, narrate=False)


def read_note(world: World, hero: Entity, friend: Entity, note_cfg: NoteClue) -> None:
    note = world.get("note")
    note.meters["read"] += 1
    world.say(
        f"On the fence, a paper fluttered. {friend.id} sounded out the biggest word: "
        f'"{note_cfg.text}"'
    )
    world.say(
        f"Neither child knew the whole meaning. The word obscenity felt heavy and secret, "
        f"which made the backyard seem even more haunted."
    )
    propagate(world, narrate=False)


def misunderstand(world: World, hero: Entity, friend: Entity, sound_cfg: SoundSource) -> None:
    fear = hero.memes["fear"] + friend.memes["fear"]
    guess = hero.memes["misunderstanding"] + friend.memes["misunderstanding"]
    if fear >= THRESHOLD and guess >= THRESHOLD:
        hero.memes["courage"] += 1
        friend.memes["cling"] += 1
        world.say(
            f'"Did you hear it?" whispered {friend.id}. "{sound_cfg.rhyme} sounded like a warning."'
        )
        world.say(
            f"{hero.id} held {hero.pronoun('possessive')} own wrist and whispered back that maybe "
            f"a backyard ghost did not like rude words on fences."
        )
        world.say(
            "The misunderstanding grew all by itself: a rhyme in the dark, a strange mark, "
            "and a hard word on paper all seemed to belong together."
        )


def call_helper(world: World, helper_cfg: Helper, friend: Entity) -> None:
    world.para()
    world.say(
        f"Just then, {helper_cfg.entrance}. {friend.id} hurried over and asked if something ghostly "
        f"was walking near the fence."
    )


def explain(world: World, helper_cfg: Helper, sound_cfg: SoundSource, mark_cfg: WristMark, note_cfg: NoteClue) -> None:
    helper = world.get("helper")
    helper.meters["explained"] += 1
    world.say(
        f'{helper_cfg.comfort} "That rhyme was only the {sound_cfg.label}," {helper.label_word} said. '
        f"It happened because {sound_cfg.cause}."
    )
    world.say(
        f"{helper.label_word.capitalize()} gently touched the wrist mark. It was {mark_cfg.cause}. "
        f"{mark_cfg.gentle_fix}."
    )
    world.say(
        f"Then {helper.pronoun().capitalize()} pointed to the note. It was not from any ghost at all; "
        f"{note_cfg.explanation}"
    )
    propagate(world, narrate=False)


def repair(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["kindness"] += 1
    friend.memes["kindness"] += 1
    world.say(
        f"Soon the two children helped fetch a sponge and a little bucket so the fence could be cleaned."
    )
    world.say(
        "Scrub, rub, kindly clean; keep the wooden boards bright and serene, "
        "they sang, turning the scary rhyme into a cheerful one."
    )


def moral_ending(world: World, helper_cfg: Helper, hero: Entity, friend: Entity) -> None:
    world.para()
    world.say(
        f'When the last gray edge of evening softened, {helper_cfg.lesson}'
    )
    world.say(
        f"{hero.id} looked at {hero.pronoun('possessive')} wrist again. It was only small and ordinary now."
    )
    world.say(
        f"{friend.id}'s backyard did not feel haunted anymore. The chime of the night was only a backyard song, "
        f"and the children went back to their leaf boats braver, kinder, and wiser than before."
    )


def tell(time_cfg: TimeOfDay, sound_cfg: SoundSource, mark_cfg: WristMark,
         note_cfg: NoteClue, helper_cfg: Helper, hero_name: str = "Nora",
         hero_type: str = "girl", friend_name: str = "Ben", friend_type: str = "boy") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend"))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_cfg.type, role="helper"))
    world.add(Entity(id="sound", type="thing", label=sound_cfg.label))
    world.add(Entity(id="mark", type="thing", label=mark_cfg.label))
    world.add(Entity(id="note", type="thing", label=note_cfg.label))
    world.facts.update(time=time_cfg, sound_cfg=sound_cfg, mark_cfg=mark_cfg, note_cfg=note_cfg, helper_cfg=helper_cfg)

    introduce(world, hero, friend, time_cfg)
    world.para()
    first_shiver(world, sound_cfg)
    notice_mark(world, hero, mark_cfg)
    read_note(world, hero, friend, note_cfg)
    misunderstand(world, hero, friend, sound_cfg)
    call_helper(world, helper_cfg, friend)
    explain(world, helper_cfg, sound_cfg, mark_cfg, note_cfg)
    repair(world, hero, friend)
    moral_ending(world, helper_cfg, hero, friend)

    world.facts.update(
        hero=hero,
        friend=friend,
        helper=helper,
        fear_before=2 if time_cfg.id in {"dusk", "moonrise", "mist"} and sound_cfg.creepy >= 2 else 0,
        misunderstanding_before=predict_spook(time_cfg, sound_cfg, mark_cfg, note_cfg)["misunderstanding"],
        learned=True,
        cleaned=True,
    )
    return world


TIMES = {
    "dusk": TimeOfDay("dusk", "at dusk", "The sky over the friend's backyard was purple at the edges, and the bean poles made thin, leaning shadows.", tags={"night"}),
    "moonrise": TimeOfDay("moonrise", "at moonrise", "A round moon was climbing above the fence, and silver light lay across the grass.", tags={"night", "moon"}),
    "mist": TimeOfDay("mist", "on a misty evening", "A pale mist sat low over the friend's backyard and made the marigolds look soft and far away.", tags={"night", "mist"}),
    "afternoon": TimeOfDay("afternoon", "in the late afternoon", "The sun was still bright on the grass, and every corner of the backyard looked plain and clear.", tags={"day"}),
}

SOUNDS = {
    "gate": SoundSource("gate", "back gate", "the loose back gate", "Clack-clack, back gate, don't be late", "the wind kept nudging the latch against the post", 3, tags={"gate", "rhyme"}),
    "chime": SoundSource("chime", "spoon chime", "a string of old spoons hanging near the shed", "Cling-cling, silver string, hear me sing", "the spoons bumped together whenever the wind wandered through", 3, tags={"chime", "rhyme"}),
    "bucket": SoundSource("bucket", "rain bucket", "a metal rain bucket under the spout", "Ting-ting, little ring", "one last drip from the spout tapped the bucket now and then", 1, tags={"bucket"}),
}

MARKS = {
    "vine": WristMark("vine", "vine mark", "a thin red line", "only a bean vine that had lightly scratched the skin", "A dab of cool cream and a wash at the tap would make it fade soon", 2, tags={"scratch", "wrist"}),
    "berry": WristMark("berry", "berry stain", "a dark purple smudge", "just blackberry juice from the bowl by the steps", "Soap and water would lift most of the stain right away", 1, tags={"berry", "wrist"}),
    "glowband": WristMark("glowband", "glow bracelet", "a chilly green ring of light", "the loose glow band from their game slipping down around the wrist", "Once pushed back up, it looked playful instead of spooky", 2, tags={"bracelet", "wrist"}),
}

NOTES = {
    "cleanup_note": NoteClue("cleanup_note", "cleanup note", "Please wash away the obscenity on this fence.", "it was a grown-up note asking for rude scribble to be scrubbed away", True, 3, tags={"obscenity", "clean"}),
    "dictionary_card": NoteClue("dictionary_card", "word card", "obscenity", "it was a dictionary card the older cousin had dropped while studying hard words", True, 2, tags={"obscenity", "word"}),
    "seed_packet": NoteClue("seed_packet", "seed packet", "morning glory", "it was only a seed packet tucked into the fence slat", False, 0, tags={"garden"}),
}

HELPERS = {
    "grandma": Helper("grandma", "grandmother", "Ben's grandma stepped out with a porch light glowing behind her", "Grandma knelt so her face was warm and near.", "Grandma said that brave hearts ask kind questions before they believe the darkest answer.", tags={"grandma"}),
    "dad": Helper("dad", "father", "Ben's dad came from the shed carrying a coil of string", "Dad set the string down and smiled in the calm way grown-ups do when they already understand the puzzle.", "Dad said that when something feels spooky, it is wise to look closely and speak kindly before making a scary story in your head.", tags={"dad"}),
}

GIRL_NAMES = ["Nora", "Mia", "Lila", "Ava", "Elsie", "Rose"]
BOY_NAMES = ["Ben", "Theo", "Max", "Sam", "Eli", "Noah"]


@dataclass
class StoryParams:
    time: str
    sound: str
    mark: str
    note: str
    helper: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "obscenity": [
        ("What does the word obscenity mean?",
         "It means rude or hurtful words or pictures that people do not want written or shown around children. In this story, the children only saw the word itself on a note, not the rude writing.")
    ],
    "gate": [
        ("Why can a loose gate sound spooky at night?",
         "A loose gate can knock and rattle when the wind pushes it. In the dark, an ordinary sound can feel bigger and stranger than it really is.")
    ],
    "chime": [
        ("Why does a wind chime make little songs?",
         "Pieces of metal or wood tap together when the wind moves them. That can make a pattern that sounds almost like music or words.")
    ],
    "scratch": [
        ("Why can a tiny scratch on a wrist look scary at first?",
         "A small scratch can sting and appear suddenly, especially when you are already nervous. Your mind may guess something spooky before you notice the simple cause.")
    ],
    "berry": [
        ("How can berry juice get on your skin?",
         "Berry juice can drip or smear when you hold or squeeze fruit. It can look dark for a while, but it usually washes off.")
    ],
    "bracelet": [
        ("Why can a glow bracelet look different in the dark?",
         "It shines more brightly when the yard is dark, so it can seem mysterious for a moment. In daylight it just looks like a toy.")
    ],
    "clean": [
        ("Why should rude writing be cleaned off a fence?",
         "Cleaning it away keeps the yard kind and welcoming. It also stops younger children from seeing mean or rude words.")
    ],
    "misunderstanding": [
        ("What is a misunderstanding?",
         "A misunderstanding happens when someone guesses wrong about what they saw or heard. Asking calm questions can help people find the true answer.")
    ],
    "moral": [
        ("What is the moral of this story?",
         "When something seems scary, do not rush to the darkest idea. Look closely, ask kindly, and help fix the real problem.")
    ],
}
KNOWLEDGE_ORDER = ["obscenity", "gate", "chime", "scratch", "berry", "bracelet", "clean", "misunderstanding", "moral"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    helper = f["helper"]
    sound = f["sound_cfg"]
    return [
        'Write a gentle ghost-story for a 3-to-5-year-old set in a friend\'s backyard that includes the words "obscenity" and "wrist".',
        f"Tell a spooky-but-safe story where {hero.id} and {friend.id} hear a rhyme from {sound.label}, misunderstand it, and a calm {helper.label_word} explains the truth.",
        "Write a story with a misunderstanding, a moral value about asking before guessing, and an ending where the children help make the yard kind again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    helper = f["helper"]
    sound = f["sound_cfg"]
    mark = f["mark_cfg"]
    note = f["note_cfg"]
    qa: list[tuple[str, str]] = [
        ("Who is the story about?",
         f"It is about {hero.id} visiting {friend.id} in a friend's backyard, and {friend.id}'s {helper.label_word} who solves the mystery."),
        ("What first made the backyard feel spooky?",
         f"The children heard {sound.rhyme} from {sound.place}, and the sound seemed like a ghostly rhyme in the dark. Because evening had already made the yard shadowy, the noise felt scarier than it really was."),
        (f"What did {hero.id} notice on {hero.pronoun('possessive')} wrist?",
         f"{hero.id} noticed {mark.text} on {hero.pronoun('possessive')} wrist. Since {hero.pronoun()} was already nervous, the mark felt mysterious before anyone checked its real cause."),
        ("Why did the word obscenity scare the children?",
         f"They found the word on a note and did not understand it fully. Because it sounded like a serious grown-up word and came right after the spooky rhyme, they folded it into their misunderstanding."),
        ("What was the misunderstanding?",
         f"The children thought the rhyme, the wrist mark, and the note all came from a ghost in the backyard. Really, each thing had an ordinary cause, but fear made them seem connected."),
        ("How was the mystery solved?",
         f"{helper.label_word.capitalize()} explained that the sound came from {sound.cause}, the wrist mark came from {mark.cause}, and the note was ordinary too. Once the real causes were named, the fear vanished and the children could help clean the fence."),
        ("What moral did the children learn?",
         f"They learned to ask kind questions before believing the scariest idea. They also learned that if something rude or unkind is left behind, helping fix it is better than whispering about it."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"misunderstanding", "moral"}
    note = world.facts["note_cfg"]
    sound = world.facts["sound_cfg"]
    mark = world.facts["mark_cfg"]
    tags |= set(note.tags)
    tags |= set(sound.tags)
    tags |= set(mark.tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("dusk", "gate", "vine", "cleanup_note", "grandma", "Nora", "girl", "Ben", "boy"),
    StoryParams("moonrise", "chime", "glowband", "dictionary_card", "dad", "Mia", "girl", "Theo", "boy"),
    StoryParams("mist", "gate", "berry", "cleanup_note", "dad", "Eli", "boy", "Rose", "girl"),
]


def explain_rejection(time_id: str, sound_id: str, mark_id: str, note_id: str) -> str:
    problems: list[str] = []
    if TIMES[time_id].id not in {"dusk", "moonrise", "mist"}:
        problems.append("the yard is too bright for this little ghost-story misunderstanding")
    if not sound_is_spooky(SOUNDS[sound_id]):
        problems.append(f"{SOUNDS[sound_id].label} does not make a strong enough eerie rhyme")
    if not note_is_spooky(NOTES[note_id]):
        problems.append(f"{NOTES[note_id].label} does not actually bring in the word obscenity as a spooky clue")
    if MARKS[mark_id].scary < 1:
        problems.append(f"{MARKS[mark_id].label} gives no wrist clue to misunderstand")
    joined = "; ".join(problems)
    return f"(No story: {joined}.)"


ASP_RULES = r"""
night_like(dusk).
night_like(moonrise).
night_like(mist).

spooky_sound(S) :- sound(S), creepy(S, C), C >= 2.
spooky_note(N)  :- note(N), mentions_obscenity(N), spooky(N, K), K >= 2.
visible_mark(M) :- mark(M), scary(M, K), K >= 1.

valid(T, S, M, N) :- time(T), sound(S), mark(M), note(N),
                     night_like(T), spooky_sound(S), visible_mark(M), spooky_note(N).

fear(1) :- chosen_time(T), chosen_sound(S), night_like(T), spooky_sound(S).
fear(0) :- not fear(1).

misunderstanding(1) :- fear(1), chosen_mark(M), visible_mark(M), not chosen_note(_).
misunderstanding(1) :- fear(1), chosen_note(N), spooky_note(N), not chosen_mark(_).
misunderstanding(2) :- fear(1), chosen_mark(M), visible_mark(M), chosen_note(N), spooky_note(N).
misunderstanding(0) :- not misunderstanding(1), not misunderstanding(2).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in TIMES:
        lines.append(asp.fact("time", tid))
    for sid, s in SOUNDS.items():
        lines.append(asp.fact("sound", sid))
        lines.append(asp.fact("creepy", sid, s.creepy))
    for mid, m in MARKS.items():
        lines.append(asp.fact("mark", mid))
        lines.append(asp.fact("scary", mid, m.scary))
    for nid, n in NOTES.items():
        lines.append(asp.fact("note", nid))
        lines.append(asp.fact("spooky", nid, n.spooky))
        if n.mentions_obscenity:
            lines.append(asp.fact("mentions_obscenity", nid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_predicted_misunderstanding(params: StoryParams) -> int:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_time", params.time),
        asp.fact("chosen_sound", params.sound),
        asp.fact("chosen_mark", params.mark),
        asp.fact("chosen_note", params.note),
    ])
    model = asp.one_model(asp_program(scenario, "#show misunderstanding/1."))
    atoms = asp.atoms(model, "misunderstanding")
    return int(atoms[0][0]) if atoms else -1


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for s in range(20):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(p)
    bad = 0
    for p in cases:
        py_m = predict_spook(TIMES[p.time], SOUNDS[p.sound], MARKS[p.mark], NOTES[p.note])["misunderstanding"]
        cl_m = asp_predicted_misunderstanding(p)
        if py_m != cl_m:
            bad += 1
    if bad == 0:
        print(f"OK: misunderstanding model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} misunderstanding counts differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle ghost-story storyworld: a rhyme, a wrist clue, and a misunderstanding in a friend's backyard."
    )
    ap.add_argument("--time", choices=TIMES)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--mark", choices=MARKS)
    ap.add_argument("--note", choices=NOTES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    time_id = args.time or rng.choice(sorted(TIMES))
    sound_id = args.sound or rng.choice(sorted(SOUNDS))
    mark_id = args.mark or rng.choice(sorted(MARKS))
    note_id = args.note or rng.choice(sorted(NOTES))
    if any(v is not None for v in (args.time, args.sound, args.mark, args.note)):
        if not valid_combo(time_id, sound_id, mark_id, note_id):
            raise StoryError(explain_rejection(time_id, sound_id, mark_id, note_id))

    combos = [
        c for c in valid_combos()
        if (args.time is None or c[0] == args.time)
        and (args.sound is None or c[1] == args.sound)
        and (args.mark is None or c[2] == args.mark)
        and (args.note is None or c[3] == args.note)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    time_id, sound_id, mark_id, note_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero = args.hero or pick_name(rng, hero_gender)
    friend = args.friend or pick_name(rng, friend_gender, avoid=hero)
    return StoryParams(time_id, sound_id, mark_id, note_id, helper_id, hero, hero_gender, friend, friend_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        TIMES[params.time],
        SOUNDS[params.sound],
        MARKS[params.mark],
        NOTES[params.note],
        HELPERS[params.helper],
        params.hero,
        params.hero_gender,
        params.friend,
        params.friend_gender,
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
        print(asp_program("", "#show valid/4.\n#show misunderstanding/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (time, sound, mark, note) combos:\n")
        for time_id, sound_id, mark_id, note_id in combos:
            print(f"  {time_id:10} {sound_id:8} {mark_id:9} {note_id}")
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
            header = f"### {p.hero} & {p.friend}: {p.sound} / {p.mark} / {p.note}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
