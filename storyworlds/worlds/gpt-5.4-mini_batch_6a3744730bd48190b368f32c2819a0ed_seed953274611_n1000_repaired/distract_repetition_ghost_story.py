#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/distract_repetition_ghost_story.py
===================================================================

A small ghost-story storyworld: a child, a spooky room, a repeating sound,
a distraction, a brave turn, and a calm ending. The domain is built from the
seed words "distract" and the feature "repetition" in a child-facing ghost
story style.

The world keeps state in typed entities with physical meters and emotional
memes. Repetition is modeled as an accumulating haunt meter and repeated
sounds. A safe distraction helps the child regain courage and resolve the
spooky moment.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/distract_repetition_ghost_story.py
    python storyworlds/worlds/gpt-5.4-mini/distract_repetition_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/distract_repetition_ghost_story.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/distract_repetition_ghost_story.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/distract_repetition_ghost_story.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
REPETITION_MIN = 2
FEAR_START = 3.0
CALM_TARGET = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    dark: bool = True
    repeats: list[str] = field(default_factory=list)
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
class Sound:
    id: str
    label: str
    phrase: str
    repeat_phrase: str
    volume: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Distraction:
    id: str
    label: str
    phrase: str
    calm_gain: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
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


def _r_haunt(world: World) -> list[str]:
    out: list[str] = []
    room = world.entities.get("room")
    if not room:
        return out
    for sound in world.facts.get("sounds", []):
        if room.meters["haunt"] < sound.volume:
            continue
        sig = ("haunt", sound.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in world.characters():
            kid.memes["fear"] += 1
        out.append(sound.repeat_phrase)
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    kid = world.entities.get("kid")
    if not kid:
        return out
    if kid.memes["fear"] < CALM_TARGET:
        return out
    sig = ("calm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kid.memes["bravery"] += 1
    out.append("__calm__")
    return out


RULES = [Rule("haunt", "physical", _r_haunt), Rule("calm", "social", _r_calm)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predicted_repetition(world: World, sound: Sound) -> int:
    sim = world.copy()
    sim.get("room").meters["haunt"] += 1
    for _ in range(REPETITION_MIN):
        sim.get("room").meters["haunt"] += 1
        propagate(sim, narrate=False)
    return int(sim.get("kid").memes["fear"])


def same_reasonable(sound: Sound, distraction: Distraction) -> bool:
    return sound.volume >= REPETITION_MIN and distraction.calm_gain >= 1


def introduce(world: World, kid: Entity, room: Place) -> None:
    world.say(
        f"{kid.id} stepped into {room.label} and listened to the dark hush."
    )
    world.say("It was quiet. Too quiet. Quiet enough to feel like someone was waiting.")


def repeat_scare(world: World, sound: Sound, kid: Entity) -> None:
    room = world.get("room")
    room.meters["haunt"] += 1
    world.say(f"Then came {sound.phrase}.")
    room.meters["haunt"] += 1
    world.say(f"Then came {sound.phrase} again.")
    room.meters["haunt"] += 1
    world.say(f"And then came {sound.phrase} one more time.")
    kid.memes["fear"] += 1
    propagate(world, narrate=False)


def distract_and_brave(world: World, kid: Entity, adult: Entity, distraction: Distraction) -> None:
    kid.memes["fear"] += 1
    world.say(
        f'{kid.id} whispered, "I hear it again." {adult.id} smiled and said, '
        f'"Let us {distraction.label} and distract the spooky feeling."'
    )
    world.say(
        f"{adult.id} showed {kid.pronoun('object')} {distraction.phrase}, bright and simple."
    )
    kid.memes["fear"] = max(0.0, kid.memes["fear"] - distraction.calm_gain)
    kid.memes["bravery"] += 1
    world.say(f"{kid.id} took a breath. The room felt a little less ghostly.")


def ending(world: World, kid: Entity, room: Place, sound: Sound, distraction: Distraction) -> None:
    if kid.memes["fear"] <= 0:
        world.say(
            f"In {room.label}, the repeating sound still drifted by, but it no longer felt scary."
        )
    else:
        world.say(
            f"In {room.label}, the sound still repeated, but {kid.id} could stand still and listen."
        )
    world.say(
        f"{kid.id} kept {distraction.phrase} close, and the night felt small enough to hold."
    )


def tell(place: Place, sound: Sound, distraction: Distraction, child_name: str = "Mia",
         child_type: str = "girl", adult_name: str = "Mom", adult_type: str = "mother") -> World:
    world = World()
    kid = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_type, role="adult"))
    room = world.add(Entity(id="room", type="room", label=place.label))
    kid.memes["fear"] = FEAR_START
    kid.memes["bravery"] = 0.0
    world.facts["sound"] = sound
    world.facts["distraction"] = distraction

    introduce(world, kid, place)
    world.para()
    repeat_scare(world, sound, kid)
    if kid.memes["fear"] >= CALM_TARGET:
        world.para()
        distract_and_brave(world, kid, adult, distraction)
    world.para()
    ending(world, kid, place, sound, distraction)

    world.facts.update(
        kid=kid, adult=adult, room=room, place=place,
        fear=kid.memes["fear"], bravery=kid.memes["bravery"],
        repeated=True, calmed=kid.memes["fear"] <= 1.0,
    )
    return world


PLACES = {
    "hall": Place(id="hall", label="the hall", dark=True, tags={"hall", "ghost"}),
    "attic": Place(id="attic", label="the attic", dark=True, tags={"attic", "ghost"}),
    "closet": Place(id="closet", label="the closet", dark=True, tags={"closet", "ghost"}),
}

SOUNDS = {
    "tap": Sound(id="tap", label="tap", phrase="tap, tap, tap", repeat_phrase="Tap. Tap. Tap.",
                 volume=2, tags={"sound", "repeat"}),
    "knock": Sound(id="knock", label="knock", phrase="knock, knock, knock", repeat_phrase="Knock. Knock. Knock.",
                   volume=2, tags={"sound", "repeat"}),
    "sway": Sound(id="sway", label="sway", phrase="sway, sway, sway", repeat_phrase="Sway. Sway. Sway.",
                  volume=3, tags={"sound", "repeat"}),
}

DISTRACTIONS = {
    "song": Distraction(id="song", label="sing a song", phrase="a funny little song", calm_gain=2, tags={"distract"}),
    "count": Distraction(id="count", label="count the steps", phrase="the steps on the rug", calm_gain=1, tags={"distract"}),
    "lantern": Distraction(id="lantern", label="turn on a lantern", phrase="a small lantern", calm_gain=2, tags={"distract"}),
}


@dataclass
class StoryParams:
    place: str
    sound: str
    distraction: str
    name: str = "Mia"
    gender: str = "girl"
    adult: str = "Mom"
    adult_type: str = "mother"
    seed: Optional[int] = None
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for s in SOUNDS:
            for d in DISTRACTIONS:
                if same_reasonable(SOUNDS[s], DISTRACTIONS[d]):
                    combos.append((p, s, d))
    return combos


KNOWLEDGE = {
    "ghost": [("What is a ghost story?", "A ghost story is a spooky story that is meant to feel a little scary, but in a safe way for children.")],
    "repeat": [("What does repeating mean?", "Repeating means something happens or is said again and again.")],
    "sound": [("What is a sound?", "A sound is something you hear with your ears.")],
    "distract": [("What does it mean to distract someone?", "To distract someone means to help them pay attention to something else instead of the scary thing.")],
    "lantern": [("What is a lantern?", "A lantern is a light that helps people see in the dark.")],
}
KNOWLEDGE_ORDER = ["ghost", "repeat", "sound", "distract", "lantern"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"].label
    sound = f["sound"].phrase
    distraction = f["distraction"].label
    return [
        f'Write a ghost story for a 3-to-5-year-old set in {place} with the repeating sound "{sound}".',
        f"Tell a gentle spooky story where a child feels afraid, then gets distracted by {distraction} and becomes brave.",
        f'Write a short story that repeats the phrase "{sound}" and includes the word "distract".',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid = f["kid"]
    adult = f["adult"]
    sound = f["sound"]
    distraction = f["distraction"]
    return [
        (f"Who is the story about?",
         f"It is about {kid.id} and {adult.id} in {f['place'].label}. {kid.id} is the child who hears the spooky repeating sound."),
        (f"What did {kid.id} hear?",
         f"{kid.id} heard {sound.phrase} again and again. The repetition made the room feel haunted and a little eerie."),
        (f"How did {adult.id} help?",
         f"{adult.id} helped by using {distraction.phrase} to distract {kid.id}. That gave {kid.id} something calm to focus on instead of the spooky noise."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["sound"].tags) | set(world.facts["distraction"].tags) | {"ghost"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hall", sound="tap", distraction="song", name="Mia", gender="girl", adult="Mom", adult_type="mother"),
    StoryParams(place="attic", sound="knock", distraction="lantern", name="Noah", gender="boy", adult="Dad", adult_type="father"),
    StoryParams(place="closet", sound="sway", distraction="count", name="Ava", gender="girl", adult="Mom", adult_type="mother"),
]


def explain_rejection(sound: Sound, distraction: Distraction) -> str:
    return f"(No story: the sound '{sound.phrase}' must repeat enough to feel spooky, and the distraction must genuinely calm the child.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for sid, s in SOUNDS.items():
        lines.append(asp.fact("sound", sid))
        lines.append(asp.fact("volume", sid, s.volume))
    for did, d in DISTRACTIONS.items():
        lines.append(asp.fact("distraction", did))
        lines.append(asp.fact("calm_gain", did, d.calm_gain))
    lines.append(asp.fact("repetition_min", REPETITION_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(S,D) :- sound(S), distraction(D), volume(S,V), repetition_min(M), V >= M, calm_gain(D,C), C >= 1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/2."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set((s, d) for _, s, d in valid_combos()):
        print("OK: ASP gate matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH: ASP gate differs from valid_combos().")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test succeeded.")
    except Exception as exc:
        rc = 1
        print(f"MISMATCH: generation smoke test failed: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with repetition and a distraction.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--distract", choices=DISTRACTIONS)
    ap.add_argument("--name")
    ap.add_argument("--adult", choices=["Mom", "Dad"])
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
    if args.sound and args.distract:
        if not same_reasonable(SOUNDS[args.sound], DISTRACTIONS[args.distract]):
            raise StoryError(explain_rejection(SOUNDS[args.sound], DISTRACTIONS[args.distract]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.sound is None or c[1] == args.sound)
              and (args.distract is None or c[2] == args.distract)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, sound, distract = rng.choice(sorted(combos))
    name = args.name or rng.choice(["Mia", "Noah", "Ava", "Eli", "Luna", "Finn"])
    adult = args.adult or rng.choice(["Mom", "Dad"])
    return StoryParams(place=place, sound=sound, distraction=distract, name=name, adult=adult, gender="girl" if name in {"Mia", "Ava", "Luna"} else "boy", adult_type="mother" if adult == "Mom" else "father")


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.sound not in SOUNDS or params.distraction not in DISTRACTIONS:
        raise StoryError("invalid story parameters")
    world = tell(PLACES[params.place], SOUNDS[params.sound], DISTRACTIONS[params.distraction], params.name, params.gender, params.adult, params.adult_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show reasonable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} reasonable (sound, distraction) combos:\n")
        for sound, distract in combos:
            print(f"  {sound:8} {distract}")
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
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
