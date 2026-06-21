#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/widow_audio_transformation_misunderstanding_humor_slice_of.py
=========================================================================================

A standalone storyworld for a gentle slice-of-life misunderstanding:
a widow hears a transformed audio message, imagines the wrong speaker,
then laughs when a child explains the trick and helps her make a playful reply.

Seed requirements covered:
- includes the words "widow" and "audio"
- uses Transformation, Misunderstanding, Humor
- stays in a small, domestic slice-of-life world

Run it
------
python storyworlds/worlds/gpt-5.4/widow_audio_transformation_misunderstanding_humor_slice_of.py
python storyworlds/worlds/gpt-5.4/widow_audio_transformation_misunderstanding_humor_slice_of.py --transform robot --mistake radio_host
python storyworlds/worlds/gpt-5.4/widow_audio_transformation_misunderstanding_humor_slice_of.py --transform deep --mistake teapot_giant
python storyworlds/worlds/gpt-5.4/widow_audio_transformation_misunderstanding_humor_slice_of.py --all
python storyworlds/worlds/gpt-5.4/widow_audio_transformation_misunderstanding_humor_slice_of.py --qa --json
python storyworlds/worlds/gpt-5.4/widow_audio_transformation_misunderstanding_humor_slice_of.py --verify
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
# from a nested world directory: .../storyworlds/worlds/gpt-5.4/<file>.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # character | thing
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
        female = {"girl", "woman", "widow", "grandmother", "neighbor_woman"}
        male = {"boy", "man", "grandson", "neighbor_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


# ---------------------------------------------------------------------------
# Domain configs
# ---------------------------------------------------------------------------
@dataclass
class Home:
    id: str
    room: str
    detail: str
    resting_spot: str
    tags: set[str] = field(default_factory=set)


@dataclass
class DeviceCfg:
    id: str
    label: str
    phrase: str
    place: str
    plays_audio: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class TransformCfg:
    id: str
    label: str
    voice_desc: str
    effect_text: str
    fits: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class MistakeCfg:
    id: str
    guess: str
    exclaim: str
    because: str
    fit_tags: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class FixCfg:
    id: str
    label: str
    action_text: str
    reveal_text: str
    works_for: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_confusion(world: World) -> list[str]:
    out: list[str] = []
    widow = world.get("widow")
    message = world.get("message")
    if message.meters["distorted"] >= THRESHOLD and widow.meters["heard"] >= THRESHOLD:
        sig = ("confusion",)
        if sig not in world.fired:
            world.fired.add(sig)
            widow.memes["confusion"] += 1
            widow.memes["curiosity"] += 1
            out.append("__confusion__")
    return out


def _r_explained(world: World) -> list[str]:
    out: list[str] = []
    widow = world.get("widow")
    helper = world.get("helper")
    if helper.meters["explained"] >= THRESHOLD and widow.memes["confusion"] >= THRESHOLD:
        sig = ("explained",)
        if sig not in world.fired:
            world.fired.add(sig)
            widow.memes["confusion"] = 0.0
            widow.memes["relief"] += 1
            widow.memes["laughter"] += 1
            helper.memes["pride"] += 1
            out.append("__explained__")
    return out


def _r_reply(world: World) -> list[str]:
    out: list[str] = []
    widow = world.get("widow")
    if widow.meters["reply_sent"] >= THRESHOLD:
        sig = ("reply",)
        if sig not in world.fired:
            world.fired.add(sig)
            widow.memes["playfulness"] += 1
            widow.memes["warmth"] += 1
            out.append("__reply__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="confusion", tag="social", apply=_r_confusion),
    Rule(name="explained", tag="social", apply=_r_explained),
    Rule(name="reply", tag="social", apply=_r_reply),
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


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def mistake_matches(transform: TransformCfg, mistake: MistakeCfg) -> bool:
    return bool(transform.fits & mistake.fit_tags)


def fix_works(transform: TransformCfg, fix: FixCfg) -> bool:
    return transform.id in fix.works_for


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for home_id in HOMES:
        for transform_id, transform in TRANSFORMS.items():
            for mistake_id, mistake in MISTAKES.items():
                for fix_id, fix in FIXES.items():
                    if mistake_matches(transform, mistake) and fix_works(transform, fix):
                        combos.append((home_id, transform_id, mistake_id, fix_id))
    return combos


def explain_mismatch(transform: TransformCfg, mistake: MistakeCfg) -> str:
    return (
        f"(No story: a {transform.label} voice would not reasonably make someone think of "
        f"{mistake.guess}. Pick a misunderstanding that fits how the audio sounds.)"
    )


def explain_fix(transform: TransformCfg, fix: FixCfg) -> str:
    return (
        f"(No story: the fix '{fix.label}' does not actually clear up a {transform.label} voice. "
        f"The explanation must reveal the real speaker in a believable way.)"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_misunderstanding(world: World, mistake_id: str) -> dict:
    sim = world.copy()
    widow = sim.get("widow")
    widow.meters["heard"] += 1
    propagate(sim, narrate=False)
    return {
        "confused": widow.memes["confusion"] >= THRESHOLD,
        "guess": MISTAKES[mistake_id].guess,
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def scene_setup(world: World, home: Home, widow: Entity, helper: Entity, device: Entity) -> None:
    widow.memes["calm"] += 1
    world.say(
        f"In {home.room}, {widow.id}, a kind widow, was straightening the cushions by "
        f"{home.resting_spot}. {home.detail}"
    )
    world.say(
        f"{helper.id} was nearby with {device.phrase} on {device.attrs['place']}, trying to send "
        f"a cheerful audio greeting before snack time."
    )


def record_trick(world: World, helper: Entity, transform: TransformCfg) -> None:
    message = world.get("message")
    helper.memes["mischief"] += 1
    message.meters["recorded"] += 1
    message.meters["distorted"] += 1
    message.attrs["transform"] = transform.id
    world.say(
        f"{helper.id} tapped a silly voice button and turned the message into {transform.voice_desc}. "
        f"{transform.effect_text}"
    )


def hear_message(world: World, widow: Entity, device: Entity, transform: TransformCfg) -> None:
    device.meters["playing"] += 1
    widow.meters["heard"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {device.label} gave a little chime, and the transformed audio floated out in "
        f"{transform.voice_desc}."
    )


def guess_wrong(world: World, widow: Entity, mistake: MistakeCfg) -> None:
    pred = predict_misunderstanding(world, mistake.id)
    world.facts["predicted_confused"] = pred["confused"]
    widow.memes["imagination"] += 1
    world.say(
        f'{widow.id} blinked and said, "{mistake.exclaim}"'
    )
    world.say(
        f"To {widow.pronoun('object')}, it really sounded as if {mistake.guess} had started speaking "
        f"from the room, because {mistake.because}."
    )


def helper_laughs(world: World, helper: Entity) -> None:
    helper.memes["laughter"] += 1
    world.say(
        f"{helper.id} pressed both hands over {helper.pronoun('possessive')} mouth, trying not to laugh too soon."
    )


def explain_trick(world: World, helper: Entity, widow: Entity, device: Entity, fix: FixCfg, sender: Entity) -> None:
    helper.meters["explained"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At last, {helper.id} hurried over to {device.label} and {fix.action_text}."
    )
    world.say(
        f"{fix.reveal_text} It was only {sender.id}'s voice after all, and the phone app had dressed it up."
    )
    world.say(
        f"{widow.id} looked at {helper.id}, then at {device.label}, and the whole mistake untied itself at once."
    )


def shared_laughter(world: World, widow: Entity, helper: Entity) -> None:
    widow.memes["laughter"] += 1
    helper.memes["laughter"] += 1
    world.say(
        f"First {widow.id} laughed, then {helper.id} laughed, and soon they were both leaning on the table and giggling."
    )


def playful_reply(world: World, widow: Entity, helper: Entity, transform: TransformCfg, sender: Entity) -> None:
    widow.meters["reply_sent"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Instead of being cross, {widow.id} asked if {helper.id} could show {widow.pronoun('object')} the same button."
    )
    world.say(
        f"Together they made a reply in an even sillier {transform.label} voice: "
        f'"Thank you, dear. Next time warn a widow before the audio turns into a circus!"'
    )
    world.say(
        f"When they sent it back to {sender.id}, the room felt lighter, as if the afternoon itself had learned a joke."
    )


def closing_image(world: World, home: Home, widow: Entity, helper: Entity, device: Entity) -> None:
    world.say(
        f"By the time the tea was poured, {device.label} sat quietly on {device.attrs['place']}, "
        f"and every time it chimed again, {widow.id} smiled first instead of jumping."
    )
    world.say(
        f"The misunderstanding was gone, but the laughter stayed in {home.room} like a warm little echo."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    home: Home,
    device_cfg: DeviceCfg,
    transform: TransformCfg,
    mistake: MistakeCfg,
    fix: FixCfg,
    widow_name: str = "Mrs. Vale",
    helper_name: str = "Nina",
    helper_type: str = "girl",
    sender_name: str = "Owen",
    sender_type: str = "grandson",
) -> World:
    world = World()
    widow = world.add(Entity(id=widow_name, kind="character", type="widow", label="widow", role="widow"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, label="child", role="helper"))
    sender = world.add(Entity(id=sender_name, kind="character", type=sender_type, label="sender", role="sender"))
    device = world.add(
        Entity(
            id="device",
            kind="thing",
            type="device",
            label=device_cfg.label,
            phrase=device_cfg.phrase,
            role="device",
            attrs={"place": device_cfg.place},
            tags=set(device_cfg.tags),
        )
    )
    world.add(Entity(id="message", kind="thing", type="audio_message", label="message", role="message"))

    scene_setup(world, home, widow, helper, device)
    world.para()
    record_trick(world, helper, transform)
    hear_message(world, widow, device, transform)
    guess_wrong(world, widow, mistake)
    helper_laughs(world, helper)
    world.para()
    explain_trick(world, helper, widow, device, fix, sender)
    shared_laughter(world, widow, helper)
    world.para()
    playful_reply(world, widow, helper, transform, sender)
    closing_image(world, home, widow, helper, device)

    world.facts.update(
        home=home,
        widow=widow,
        helper=helper,
        sender=sender,
        device=device,
        transform=transform,
        mistake=mistake,
        fix=fix,
        confused=world.get("widow").memes["curiosity"] >= THRESHOLD,
        understood=world.get("widow").memes["relief"] >= THRESHOLD,
        reply_sent=world.get("widow").meters["reply_sent"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
HOMES = {
    "parlor": Home(
        id="parlor",
        room="the small front parlor",
        detail="A neat tray waited on the side table, and the curtains moved a little in the open window.",
        resting_spot="the armchair",
        tags={"home"},
    ),
    "kitchen": Home(
        id="kitchen",
        room="the sunny kitchen",
        detail="A blue teapot sat on the stove, and a plate of butter biscuits cooled beside the sink.",
        resting_spot="the wooden chair",
        tags={"home", "tea"},
    ),
    "sitting_room": Home(
        id="sitting_room",
        room="the sitting room",
        detail="A knitting basket rested under the lamp, and the clock ticked with a soft, steady sound.",
        resting_spot="the sofa",
        tags={"home"},
    ),
}

DEVICES = {
    "phone": DeviceCfg(
        id="phone",
        label="the phone",
        phrase="a bright little phone",
        place="the table",
        plays_audio=True,
        tags={"phone", "audio"},
    ),
    "speaker": DeviceCfg(
        id="speaker",
        label="the speaker",
        phrase="a small round speaker",
        place="the shelf",
        plays_audio=True,
        tags={"speaker", "audio"},
    ),
    "tablet": DeviceCfg(
        id="tablet",
        label="the tablet",
        phrase="a family tablet",
        place="the counter",
        plays_audio=True,
        tags={"tablet", "audio"},
    ),
}

TRANSFORMS = {
    "robot": TransformCfg(
        id="robot",
        label="robot",
        voice_desc="a tinny robot voice",
        effect_text="The words came out in neat little buzzes, like a toy from the future.",
        fits={"metal", "broadcast"},
        tags={"audio", "robot"},
    ),
    "chipmunk": TransformCfg(
        id="chipmunk",
        label="squeaky",
        voice_desc="a squeaky, high little voice",
        effect_text="Every thank-you bounced upward until it sounded hardly bigger than a spoon.",
        fits={"tiny", "bird"},
        tags={"audio", "squeaky"},
    ),
    "deep": TransformCfg(
        id="deep",
        label="booming",
        voice_desc="a slow, booming voice",
        effect_text="The message rolled out low and grand, as if the floorboards themselves were helping.",
        fits={"giant", "theater"},
        tags={"audio", "deep"},
    ),
}

MISTAKES = {
    "radio_host": MistakeCfg(
        id="radio_host",
        guess="a tiny radio host",
        exclaim="Goodness, who let a radio announcer into my tea hour?",
        because="the words were clipped and buzzy, almost like a little show coming through the walls",
        fit_tags={"broadcast", "metal"},
        tags={"misunderstanding", "radio"},
    ),
    "canary": MistakeCfg(
        id="canary",
        guess="a canary with very polite manners",
        exclaim="Well! Since when does a canary say thank you?",
        because="the voice was so high and chirpy that it seemed ready to hop onto the curtain rod",
        fit_tags={"tiny", "bird"},
        tags={"misunderstanding", "bird"},
    ),
    "teapot_giant": MistakeCfg(
        id="teapot_giant",
        guess="a giant hiding inside the blue teapot",
        exclaim="Mercy me, has a giant moved into the teapot?",
        because="the sound came out so deep and round that even the crockery seemed to listen",
        fit_tags={"giant", "theater"},
        tags={"misunderstanding", "giant"},
    ),
}

FIXES = {
    "play_plain": FixCfg(
        id="play_plain",
        label="play plain recording",
        action_text="tapped the screen and played the same message again without the trick voice",
        reveal_text="This time the words sounded warm and ordinary",
        works_for={"robot", "chipmunk", "deep"},
        tags={"explain", "replay"},
    ),
    "show_app": FixCfg(
        id="show_app",
        label="show app buttons",
        action_text="opened the voice app and showed how one tap changed the whole sound",
        reveal_text="Then the plain version played right after, clear as a hand on a shoulder",
        works_for={"robot", "chipmunk"},
        tags={"explain", "app"},
    ),
    "live_call": FixCfg(
        id="live_call",
        label="call sender live",
        action_text="pressed the call button so the real voice could answer right away",
        reveal_text="The deep thunder vanished the moment the real voice said hello",
        works_for={"deep"},
        tags={"explain", "call"},
    ),
}

WIDOW_NAMES = ["Mrs. Vale", "Mrs. Rowan", "Mrs. Hart", "Mrs. Bell", "Mrs. Lane"]
HELPER_NAMES_GIRL = ["Nina", "Elsie", "Mara", "Lila", "Tess"]
HELPER_NAMES_BOY = ["Ben", "Theo", "Milo", "Sam", "Ira"]
SENDER_NAMES = ["Owen", "Ruby", "Cal", "June", "Max"]


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    home: str
    device: str
    transform: str
    mistake: str
    fix: str
    widow_name: str
    helper_name: str
    helper_type: str
    sender_name: str
    sender_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "audio": [
        (
            "What is audio?",
            "Audio is sound that has been recorded or played through a device. It can be a voice, music, or any other sound you hear."
        )
    ],
    "robot": [
        (
            "What does a robot voice sound like?",
            "A robot voice often sounds buzzy, flat, or metallic. That can make a real person sound like a machine."
        )
    ],
    "squeaky": [
        (
            "Why can a squeaky voice sound funny?",
            "A squeaky voice sounds much higher than an ordinary voice. When a familiar person suddenly sounds tiny and chirpy, it can surprise people and make them laugh."
        )
    ],
    "deep": [
        (
            "Why can a deep voice sound strange on a recording?",
            "A very deep voice can make a speaker sound much bigger or older than they really are. On a recording, that can lead to silly wrong guesses."
        )
    ],
    "phone": [
        (
            "What can a phone do with sound?",
            "A phone can record voices and play them back. Some apps can also change how the voice sounds."
        )
    ],
    "speaker": [
        (
            "What does a speaker do?",
            "A speaker plays sound out loud so people in the room can hear it. It turns an audio file into sound in the air."
        )
    ],
    "tablet": [
        (
            "Can a tablet play recorded voices?",
            "Yes. A tablet can store and play recordings, just like a phone can."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks something means one thing, but it really means another. Once the truth is explained, the confusion goes away."
        )
    ],
    "app": [
        (
            "What is a voice app?",
            "A voice app is a little program on a device that can record sound and sometimes change it. It can make a voice sound funny or different."
        )
    ],
    "call": [
        (
            "Why does hearing a real voice help clear up confusion?",
            "A live voice sounds more natural than a trick recording. Hearing the person speak normally can show who it really is."
        )
    ],
}

KNOWLEDGE_ORDER = [
    "audio",
    "phone",
    "speaker",
    "tablet",
    "robot",
    "squeaky",
    "deep",
    "misunderstanding",
    "app",
    "call",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    widow = f["widow"]
    transform = f["transform"]
    mistake = f["mistake"]
    helper = f["helper"]
    return [
        'Write a gentle slice-of-life story that includes the words "widow" and "audio", where a funny transformed recording causes a misunderstanding.',
        f"Tell a warm domestic story where {widow.id}, a widow, hears an audio message in a {transform.label} voice and briefly thinks it is {mistake.guess}.",
        f"Write a humorous misunderstanding story in which {helper.id} explains a silly voice trick, and the ending shows everyone laughing together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    widow = f["widow"]
    helper = f["helper"]
    sender = f["sender"]
    transform = f["transform"]
    mistake = f["mistake"]
    fix = f["fix"]
    device = f["device"]
    home = f["home"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {widow.id}, a widow at home, and {helper.id}, who is nearby with {device.label}. A playful audio message from {sender.id} starts the trouble."
        ),
        (
            "What caused the misunderstanding?",
            f"The message was changed into {transform.voice_desc}, so it did not sound like an ordinary person at first. Because of that strange sound, {widow.id} thought it might be {mistake.guess}."
        ),
        (
            f"Why did {widow.id} make the wrong guess?",
            f"{widow.id} only heard the transformed audio before anyone explained it. {mistake.because.capitalize()}, so the wrong idea felt funny but believable for a moment."
        ),
        (
            f"How was the problem solved?",
            f"{helper.id} {fix.action_text}, and then the real voice was clear. That explanation removed the confusion because {widow.id} could finally hear who was really speaking."
        ),
    ]
    if f.get("reply_sent"):
        qa.append(
            (
                "What changed by the end of the story?",
                f"At first {widow.id} was puzzled, but by the end {widow.pronoun()} was laughing and making a joke back. The same trick that caused the misunderstanding turned into a shared game in {home.room}."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"audio", "misunderstanding"} | set(f["device"].tags) | set(f["transform"].tags) | set(f["fix"].tags)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
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
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        home="kitchen",
        device="phone",
        transform="robot",
        mistake="radio_host",
        fix="play_plain",
        widow_name="Mrs. Vale",
        helper_name="Nina",
        helper_type="girl",
        sender_name="Owen",
        sender_type="grandson",
    ),
    StoryParams(
        home="parlor",
        device="speaker",
        transform="chipmunk",
        mistake="canary",
        fix="show_app",
        widow_name="Mrs. Rowan",
        helper_name="Ben",
        helper_type="boy",
        sender_name="Ruby",
        sender_type="girl",
    ),
    StoryParams(
        home="sitting_room",
        device="tablet",
        transform="deep",
        mistake="teapot_giant",
        fix="live_call",
        widow_name="Mrs. Bell",
        helper_name="Milo",
        helper_type="boy",
        sender_name="June",
        sender_type="girl",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
fits(T, M) :- transform(T), mistake(M), has_fit(T, Tag), needs_tag(M, Tag).
works(T, F) :- transform(T), fix(F), fix_handles(F, T).

valid(H, T, M, F) :- home(H), transform(T), mistake(M), fix(F), fits(T, M), works(T, F).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for home_id in HOMES:
        lines.append(asp.fact("home", home_id))
    for transform_id, transform in TRANSFORMS.items():
        lines.append(asp.fact("transform", transform_id))
        for tag in sorted(transform.fits):
            lines.append(asp.fact("has_fit", transform_id, tag))
    for mistake_id, mistake in MISTAKES.items():
        lines.append(asp.fact("mistake", mistake_id))
        for tag in sorted(mistake.fit_tags):
            lines.append(asp.fact("needs_tag", mistake_id, tag))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        for transform_id in sorted(fix.works_for):
            lines.append(asp.fact("fix_handles", fix_id, transform_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify smoke test.")
        print("OK: generate() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a widow hears transformed audio, misunderstands it, then laughs when the trick is explained."
    )
    ap.add_argument("--home", choices=HOMES)
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--transform", choices=TRANSFORMS)
    ap.add_argument("--mistake", choices=MISTAKES)
    ap.add_argument("--fix", choices=FIXES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.transform and args.mistake:
        transform = TRANSFORMS[args.transform]
        mistake = MISTAKES[args.mistake]
        if not mistake_matches(transform, mistake):
            raise StoryError(explain_mismatch(transform, mistake))
    if args.transform and args.fix:
        transform = TRANSFORMS[args.transform]
        fix = FIXES[args.fix]
        if not fix_works(transform, fix):
            raise StoryError(explain_fix(transform, fix))

    combos = [
        combo for combo in valid_combos()
        if (args.home is None or combo[0] == args.home)
        and (args.transform is None or combo[1] == args.transform)
        and (args.mistake is None or combo[2] == args.mistake)
        and (args.fix is None or combo[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    home_id, transform_id, mistake_id, fix_id = rng.choice(sorted(combos))
    device_id = args.device or rng.choice(sorted(DEVICES))
    helper_type = rng.choice(["girl", "boy"])
    helper_name = rng.choice(HELPER_NAMES_GIRL if helper_type == "girl" else HELPER_NAMES_BOY)
    sender_name = rng.choice([n for n in SENDER_NAMES if n != helper_name])
    sender_type = "grandson" if sender_name in {"Owen", "Cal", "Max"} else "girl"
    widow_name = rng.choice(WIDOW_NAMES)
    return StoryParams(
        home=home_id,
        device=device_id,
        transform=transform_id,
        mistake=mistake_id,
        fix=fix_id,
        widow_name=widow_name,
        helper_name=helper_name,
        helper_type=helper_type,
        sender_name=sender_name,
        sender_type=sender_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.home not in HOMES:
        raise StoryError(f"(Invalid home: {params.home})")
    if params.device not in DEVICES:
        raise StoryError(f"(Invalid device: {params.device})")
    if params.transform not in TRANSFORMS:
        raise StoryError(f"(Invalid transform: {params.transform})")
    if params.mistake not in MISTAKES:
        raise StoryError(f"(Invalid mistake: {params.mistake})")
    if params.fix not in FIXES:
        raise StoryError(f"(Invalid fix: {params.fix})")

    transform = TRANSFORMS[params.transform]
    mistake = MISTAKES[params.mistake]
    fix = FIXES[params.fix]
    if not mistake_matches(transform, mistake):
        raise StoryError(explain_mismatch(transform, mistake))
    if not fix_works(transform, fix):
        raise StoryError(explain_fix(transform, fix))

    world = tell(
        home=HOMES[params.home],
        device_cfg=DEVICES[params.device],
        transform=transform,
        mistake=mistake,
        fix=fix,
        widow_name=params.widow_name,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        sender_name=params.sender_name,
        sender_type=params.sender_type,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (home, transform, mistake, fix) combos:\n")
        for home_id, transform_id, mistake_id, fix_id in combos:
            print(f"  {home_id:12} {transform_id:9} {mistake_id:14} {fix_id}")
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
            header = f"### {p.widow_name}: {p.transform} audio -> {p.mistake} ({p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
