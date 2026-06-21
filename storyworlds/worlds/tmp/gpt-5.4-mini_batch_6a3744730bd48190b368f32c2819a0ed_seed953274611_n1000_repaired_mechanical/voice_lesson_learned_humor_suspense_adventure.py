#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/voice_lesson_learned_humor_suspense_adventure.py
=================================================================================

A standalone story world for a tiny adventure about voice, echo, suspense,
humor, and a small lesson learned.

Premise:
- Two children explore a cave or hollow place looking for a lost object.
- One child uses a loud voice and nearly causes trouble.
- The other child learns to use a careful voice.
- A helpful, slightly funny guide or object adds humor.
- The story ends with a concrete change: they solve the problem by using a
  better voice, and the ending image proves that the world has changed.

The world is intentionally small and classical:
- typed entities
- physical meters and emotional memes
- a causal rule engine
- a reasonableness gate
- a Python gate plus an inline ASP twin
- three Q&A sets grounded in the simulated state

Run:
    python storyworlds/worlds/gpt-5.4-mini/voice_lesson_learned_humor_suspense_adventure.py
    python storyworlds/worlds/gpt-5.4-mini/voice_lesson_learned_humor_suspense_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/voice_lesson_learned_humor_suspense_adventure.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"sound": 0.0, "distance": 0.0, "risk": 0.0, "found": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "fear": 0.0, "humor": 0.0, "lesson": 0.0, "relief": 0.0}

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
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    echo_level: int
    dark: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class VoiceTool:
    id: str
    label: str
    loudness: int
    whisper: bool
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class LostThing:
    id: str
    label: str
    place_hint: str
    hidden: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Guide:
    id: str
    label: str
    funny_line: str
    calm_line: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_echo(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.kind != "character":
            continue
        if e.meters.get("sound", 0.0) < THRESHOLD:
            continue
        if ("echo", e.id) in world.fired:
            continue
        world.fired.add(("echo", e.id))
        place = world.get("place")
        place.meters["echo_risk"] = place.meters.get("echo_risk", 0.0) + 1
        e.memes["fear"] += 1
        out.append("__echo__")
    return out


def _r_find(world: World) -> list[str]:
    if world.get("lost").meters.get("found", 0.0) >= THRESHOLD:
        return []
    seeker = world.get("seeker")
    if seeker.meters.get("sound", 0.0) >= 0.5 and seeker.memes.get("lesson", 0.0) >= THRESHOLD:
        sig = ("find", seeker.id)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        world.get("lost").meters["found"] = 1.0
        seeker.meters["distance"] = 1.0
        seeker.memes["relief"] += 1
        return ["__find__"]
    return []


CAUSAL_RULES = [Rule("echo", _r_echo), Rule("find", _r_find)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def reasonableness_gate(place: Place, tool: VoiceTool, lost: LostThing) -> bool:
    return place.dark and place.echo_level >= 2 and not (tool.whisper and place.echo_level == 0) and lost.hidden


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        for tid, tool in VOICES.items():
            for lid, lost in LOST_THINGS.items():
                if reasonableness_gate(place, tool, lost):
                    out.append((pid, tid, lid))
    return out


@dataclass
class StoryParams:
    place: str
    voice: str
    lost: str
    seeker_name: str
    seeker_gender: str
    friend_name: str
    friend_gender: str
    guide: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


PLACES = {
    "cave": Place(id="cave", label="a cave", echo_level=3, dark=True, tags={"echo", "dark"}),
    "attic": Place(id="attic", label="an attic", echo_level=2, dark=True, tags={"echo", "dark"}),
    "hollow": Place(id="hollow", label="a tree hollow", echo_level=2, dark=True, tags={"echo", "dark"}),
}

VOICES = {
    "shout": VoiceTool(id="shout", label="a shout", loudness=3, whisper=False, tags={"voice", "loud"}),
    "call": VoiceTool(id="call", label="a calling voice", loudness=2, whisper=False, tags={"voice"}),
    "whisper": VoiceTool(id="whisper", label="a whisper", loudness=1, whisper=True, tags={"voice", "quiet"}),
}

LOST_THINGS = {
    "map": LostThing(id="map", label="a folded map", place_hint="behind a stone", tags={"map", "adventure"}),
    "lantern": LostThing(id="lantern", label="a little lantern", place_hint="on a shelf", tags={"lantern", "adventure"}),
    "kite": LostThing(id="kite", label="a red kite", place_hint="under roots", tags={"kite", "adventure"}),
}

GUIDES = {
    "bat": Guide(id="bat", label="a bat", funny_line="The bat hung upside down and looked grumpy about the noise.", calm_line="The bat flapped once, as if to say, 'Use a softer voice.'", tags={"humor", "suspense"}),
    "mouse": Guide(id="mouse", label="a mouse", funny_line="A tiny mouse squeaked at the giant echo like it had been tickled.", calm_line="The mouse pointed with one paw toward the hiding place.", tags={"humor", "suspense"}),
}

GIRL_NAMES = ["Lily", "Mina", "Zoe", "Ava", "Nora", "Ivy"]
BOY_NAMES = ["Leo", "Milo", "Noah", "Theo", "Ben", "Max"]


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny adventure story world about voice, suspense, and a lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--voice", choices=VOICES)
    ap.add_argument("--lost", choices=LOST_THINGS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.voice is None or c[1] == args.voice)
              and (args.lost is None or c[2] == args.lost)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, voice, lost = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if gender == "girl" else "girl")
    seeker_name = args.name or _pick_name(rng, gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=seeker_name)
    guide = args.guide or rng.choice(sorted(GUIDES))
    return StoryParams(place=place, voice=voice, lost=lost,
                       seeker_name=seeker_name, seeker_gender=gender,
                       friend_name=friend_name, friend_gender=friend_gender,
                       guide=guide)


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    voice = VOICES[params.voice]
    lost = LOST_THINGS[params.lost]
    guide = GUIDES[params.guide]
    world = World()
    world.add(Entity(id="place", type="place", label=place.label, meters={"echo_risk": 0.0}, attrs={"echo_level": place.echo_level}))
    seeker = world.add(Entity(id="seeker", kind="character", type=params.seeker_gender, label=params.seeker_name, role="seeker"))
    friend = world.add(Entity(id="friend", kind="character", type=params.friend_gender, label=params.friend_name, role="friend"))
    lost_ent = world.add(Entity(id="lost", type="thing", label=lost.label, meters={"found": 0.0}, attrs={"hint": lost.place_hint}))
    world.add(Entity(id="guide", type="creature", label=guide.label, attrs={"funny": guide.funny_line}))
    seeker.memes["curiosity"] = 1.0
    friend.memes["humor"] = 1.0
    world.say(f"{seeker.label} and {friend.label} went into {place.label} to look for {lost.label}.")
    world.say(f"It was dark, and the walls loved to throw voices back.")
    world.say(f"{guide.funny_line}")
    world.para()
    world.say(f"{seeker.label} took a breath and made {voice.label}, and the sound bounced everywhere.")
    seeker.meters["sound"] += float(voice.loudness)
    friend.memes["fear"] += 1
    propagate(world, narrate=True)
    world.say(f"{friend.label} hugged the rock and said, 'I think the cave is listening too hard.'")
    if voice.whisper:
        world.say(f"{seeker.label} tried a whisper instead, and the echo calmed down.")
    else:
        world.say(f"{friend.label} pointed to the dark corner where {lost.place_hint} waited.")
    world.para()
    seeker.memes["lesson"] += 1
    seeker.meters["sound"] = 1.0
    world.say(f"{seeker.label} remembered that a smaller voice can be the bravest one.")
    if voice.whisper:
        world.say(f"With the careful voice, they found {lost.label} at {lost.place_hint} and carried it home.")
    else:
        world.say(f"Then {guide.calm_line}")
        lost_ent.meters["found"] = 1.0
        world.get("place").meters["distance"] = 1.0
        world.say(f"They followed the hint, found {lost.label} at {lost.place_hint}, and smiled all the way out.")
    world.say(f"At the end, {seeker.label} held {lost.label} up like treasure and spoke in a calm voice that barely echoed at all.")
    world.facts.update(place=place, voice=voice, lost=lost, guide=guide, seeker=seeker, friend=friend, outcome="found")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a child that includes the word "voice" and shows how a louder voice turns into a smarter voice.',
        f"Tell a suspenseful but funny story where {f['seeker'].label} explores {f['place'].label} with {f['friend'].label} and learns that voice matters.",
        f"Write a small cave adventure with humor, a lesson learned, and an ending where the voice becomes calm.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    seeker = f["seeker"]
    friend = f["friend"]
    place = f["place"]
    lost = f["lost"]
    guide = f["guide"]
    return [
        QAItem(question="Who went on the adventure?", answer=f"{seeker.label} and {friend.label} went into {place.label} together to look for {lost.label}."),
        QAItem(question="What made the cave suspenseful?", answer=f"The cave was dark and echoed every sound, so even one voice bounced around and made the children feel unsure. That made them slow down and pay attention to how they spoke."),
        QAItem(question="How did the story end?", answer=f"It ended with {seeker.label} using a calm voice, finding {lost.label}, and walking out with a better idea about when to be loud and when to be quiet. The final image shows the adventure was solved by a safer voice."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is an echo?", answer="An echo is a sound that bounces back after it hits a wall or other hard surface. Caves and attics can make voices echo a lot."),
        QAItem(question="Why can a whisper be helpful in a quiet place?", answer="A whisper makes less sound, so it is less likely to startle animals or make the space too noisy. In a dark place, a quiet voice can help you listen and think."),
        QAItem(question="Why is a careful voice sometimes better than a loud voice?", answer="A careful voice can help people stay calm and notice what is happening around them. It is often the safer choice when the place is dark, echoey, or mysterious."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    parts.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    parts.append("")
    parts.append("== story QA ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== world QA ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: type={e.type} label={e.label!r} meters={e.meters} memes={e.memes} attrs={e.attrs}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
echo(E) :- sound(E,S), S >= 1.
found :- lesson(S), sound(S, X), X >= 1.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for vid in VOICES:
        lines.append(asp.fact("voice", vid))
    for lid in LOST_THINGS:
        lines.append(asp.fact("lost", lid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as exc:
        print(f"FAIL: normal generation smoke test crashed: {exc}")
        return 1
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP parity matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP parity.")
    return rc


CURATED = [
    StoryParams(place="cave", voice="shout", lost="map", seeker_name="Lily", seeker_gender="girl", friend_name="Max", friend_gender="boy", guide="bat"),
    StoryParams(place="attic", voice="call", lost="lantern", seeker_name="Mina", seeker_gender="girl", friend_name="Leo", friend_gender="boy", guide="mouse"),
    StoryParams(place="hollow", voice="whisper", lost="kite", seeker_name="Noah", seeker_gender="boy", friend_name="Ava", friend_gender="girl", guide="bat"),
]


def resolve_story_combo(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:")
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_story_combo(args, random.Random(seed))
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

    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {idx + 1}" if len(samples) > 1 else ""))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
