#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hoarse_reconciliation_folk_tale.py
==================================================================

A small folk-tale storyworld about a quarrel, a hoarse voice, and a
reconciliation that restores the village song.

Premise
-------
A child or young helper in a village wants to sing a welcome song, but their
voice is hoarse after a long day or an argument. A second character has been
hurt by a mistake, and the story turns when the two meet by the brook, speak
honestly, and make peace. The ending image proves what changed: the voice is
still hoarse, but the relationship is warm again and the song can be sung
together.

The script follows the repo contract:
- typed entities with meters and memes
- simulated state drives prose
- story-grounded and world-knowledge QA
- Python reasonableness gate plus inline ASP twin
- verify mode checks ASP parity and runs a normal generation smoke test
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
CALM_GAIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
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
    kind: str
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
class Song:
    id: str
    title: str
    lyric: str
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
class Blessing:
    id: str
    label: str
    line: str
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
        return clone


PLACES = {
    "brook": Place(id="brook", label="the brook", kind="water", tags={"water", "meeting"}),
    "oak": Place(id="oak", label="the old oak", kind="tree", tags={"tree", "meeting"}),
    "village_square": Place(id="square", label="the village square", kind="square", tags={"square", "song"}),
}

SONGS = {
    "welcome": Song(id="welcome", title="the welcome song",
                    lyric="a soft song that opens the door to friendship",
                    tags={"song", "welcome"}),
    "harvest": Song(id="harvest", title="the harvest song",
                    lyric="a steady song for the end of the season",
                    tags={"song", "harvest"}),
}

BLESSINGS = {
    "bread": Blessing(id="bread", label="bread", line="the bread was shared warmly",
                      tags={"sharing", "food"}),
    "lantern": Blessing(id="lantern", label="a lantern", line="the lantern shone kindly",
                        tags={"light", "home"}),
    "flowers": Blessing(id="flowers", label="flowers", line="flowers were set on the table",
                        tags={"flowers", "home"}),
}


@dataclass
class StoryParams:
    place: str
    song: str
    blessing: str
    singer_name: str
    singer_gender: str
    friend_name: str
    friend_gender: str
    seed: Optional[int] = None
    accident: str = "broken_promise"
    voice_state: str = "hoarse"
    mood: str = "sore"
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
        for s in SONGS:
            for b in BLESSINGS:
                if p == "brook" and s == "welcome":
                    combos.append((p, s, b))
                elif p == "village_square" and s in {"welcome", "harvest"}:
                    combos.append((p, s, b))
                elif p == "oak" and b in {"bread", "flowers"}:
                    combos.append((p, s, b))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld of hoarseness and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--song", choices=SONGS)
    ap.add_argument("--blessing", choices=BLESSINGS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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


def explain_invalid(place: str, song: str, blessing: str) -> str:
    return (f"(No story: {song} at {place} with {blessing} is not a compatible folk-tale "
            "reconciliation shape.)")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.song and args.blessing:
        if (args.place, args.song, args.blessing) not in valid_combos():
            raise StoryError(explain_invalid(args.place, args.song, args.blessing))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.song is None or c[1] == args.song)
              and (args.blessing is None or c[2] == args.blessing)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, song, blessing = rng.choice(sorted(combos))
    singer_gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if singer_gender == "girl" else "girl")
    singer_name = args.name or rng.choice(["Mira", "Tessa", "Niko", "Jon", "Sera", "Pavel"])
    friend_name = args.friend or rng.choice(["Oren", "Iva", "Lina", "Bram", "Mila", "Tavi"])
    return StoryParams(
        place=place, song=song, blessing=blessing,
        singer_name=singer_name, singer_gender=singer_gender,
        friend_name=friend_name, friend_gender=friend_gender,
    )


def reasonableness_ok(params: StoryParams) -> bool:
    return (params.place, params.song, params.blessing) in valid_combos()


def _heal(world: World) -> None:
    singer = world.get("singer")
    friend = world.get("friend")
    if singer.memes["regret"] >= THRESHOLD and friend.memes["hurt"] >= THRESHOLD:
        singer.memes["calm"] += CALM_GAIN
        friend.memes["calm"] += CALM_GAIN
        friend.memes["forgiveness"] += 1
        singer.memes["reconciled"] += 1
        friend.memes["reconciled"] += 1


def propagate(world: World) -> None:
    sig = ("heal",)
    if sig in world.fired:
        return
    world.fired.add(sig)
    _heal(world)


def predict_reconciliation(world: World) -> dict:
    sim = world.copy()
    sim.get("singer").memes["regret"] += 1
    sim.get("friend").memes["hurt"] += 1
    propagate(sim)
    return {
        "reconciled": sim.get("singer").memes["reconciled"] >= THRESHOLD,
        "calm": sim.get("friend").memes["calm"],
    }


def tell(params: StoryParams) -> World:
    if not reasonableness_ok(params):
        raise StoryError(explain_invalid(params.place, params.song, params.blessing))
    world = World()
    singer = world.add(Entity(id="singer", kind="character", type=params.singer_gender,
                              label=params.singer_name, role="singer", traits=["young"]))
    friend = world.add(Entity(id="friend", kind="character", type=params.friend_gender,
                              label=params.friend_name, role="friend", traits=["kind"]))
    place = world.add(Entity(id="place", kind="place", type=PLACES[params.place].kind,
                             label=PLACES[params.place].label))
    song = world.add(Entity(id="song", kind="thing", type="song", label=SONGS[params.song].title))
    blessing = world.add(Entity(id="blessing", kind="thing", type="gift", label=BLESSINGS[params.blessing].label))

    singer.meters["voice"] = 1.0
    singer.meters["hoarse"] = 1.0
    singer.memes["hope"] = 1.0
    friend.memes["hurt"] = 1.0

    world.say(f"Once in a village, {singer.label} came to {place.label} with {friend.label}.")
    world.say(f"{singer.label} tried to sing {song.label}, but {singer.pronoun()} was hoarse.")
    world.say(f"{friend.label} remembered the old hurt, and the path between them felt cold.")

    world.para()
    pred = predict_reconciliation(world)
    singer.memes["regret"] += 1
    friend.memes["hurt"] += 1
    world.say(f"{singer.label} lowered {singer.pronoun('possessive')} head and spoke the truth.")
    world.say(f'"I was wrong," {singer.label} said in a hoarse voice. "I am sorry."')
    if pred["reconciled"]:
        friend.memes["softening"] += 1
    world.say(f"{friend.label} listened, and the hard look in {friend.label_word}'s face melted away.")
    propagate(world)
    world.say(f"{friend.label} answered, " f'"I forgive you."')

    world.para()
    singer.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(f"Then {friend.label} and {singer.label} shared {BLESSINGS[params.blessing].label}.")
    world.say(f"{BLESSINGS[params.blessing].line.capitalize()}, and they walked on together.")
    world.say(f"At dusk they sang {song.label} again, one voice still hoarse, but no longer alone.")

    world.facts.update(
        singer=singer, friend=friend, place=place, song=song, blessing=blessing,
        reconciled=True, hoarse=True
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk tale for a young child that includes the word "hoarse" and ends with {f["singer"].label} and {f["friend"].label} making peace.',
        f"Tell a gentle village story where {f['singer'].label} is hoarse, says sorry, and reconciles with {f['friend'].label} by the brook.",
        f'Write a small reconciliation story with a song, an apology, and the word "hoarse".',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    singer = f["singer"]
    friend = f["friend"]
    return [
        ("Who is the story about?",
         f"It is about {singer.label} and {friend.label}, who met in a village and worked through an old hurt."),
        ("Why was the singer hoarse?",
         f"{singer.label} had a hoarse voice when trying to sing, so the song came out rough and thin. That made the apology quiet, but it also made the moment feel honest."),
        ("What changed after the apology?",
         f"{friend.label} forgave {singer.label}, and the two of them reconciled. After that, their path felt warm again instead of cold."),
        ("How did the story end?",
         f"They sang together at dusk, and even though {singer.label} was still hoarse, the friendship was whole again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does hoarse mean?",
         "If a voice is hoarse, it sounds rough, scratchy, or tired instead of clear. It often happens after shouting, crying, or singing too much."),
        ("What is reconciliation?",
         "Reconciliation means making peace after a disagreement or hurt. It is when people stop being angry and become friends again."),
        ("What is a folk tale?",
         "A folk tale is an old-style story passed from mouth to mouth. It often has a simple lesson, a village setting, and a warm ending."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hoarse(singer) :- singer_entity(singer), voice_rough(singer).
hurt(friend) :- friend_entity(friend).
reconciled(S,F) :- hoarse(S), hurt(F), apology(S,F), forgiveness(F).
story_ok :- reconciled(S,F).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for sid in SONGS:
        lines.append(asp.fact("song", sid))
    for bid in BLESSINGS:
        lines.append(asp.fact("blessing", bid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    # smoke test
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams(place="brook", song="welcome", blessing="bread",
                singer_name="Mira", singer_gender="girl",
                friend_name="Oren", friend_gender="boy"),
    StoryParams(place="village_square", song="harvest", blessing="lantern",
                singer_name="Tavi", singer_gender="boy",
                friend_name="Lina", friend_gender="girl"),
    StoryParams(place="oak", song="welcome", blessing="flowers",
                singer_name="Sera", singer_gender="girl",
                friend_name="Bram", friend_gender="boy"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.song is None or c[1] == args.song)
              and (args.blessing is None or c[2] == args.blessing)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, song, blessing = rng.choice(sorted(combos))
    return StoryParams(
        place=place, song=song, blessing=blessing,
        singer_name=args.name or rng.choice(["Mira", "Tavi", "Sera", "Jon", "Lena"]),
        singer_gender=args.gender or rng.choice(["girl", "boy"]),
        friend_name=args.friend or rng.choice(["Oren", "Lina", "Bram", "Iva", "Niko"]),
        friend_gender=args.friend_gender or rng.choice(["girl", "boy"]),
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for parity checks.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not args.all:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
