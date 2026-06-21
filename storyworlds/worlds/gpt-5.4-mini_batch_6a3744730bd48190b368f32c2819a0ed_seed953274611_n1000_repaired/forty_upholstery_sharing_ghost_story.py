#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/forty_upholstery_sharing_ghost_story.py
=======================================================================

A small, child-friendly ghost story world about sharing a cozy seat in a quiet
old room. The seed words are **forty** and **upholstery**; the core action is
**sharing**; the style aims for a gentle **ghost story** with a clear turn and
a warm ending.

The world model is simple but stateful:
- a room with old upholstery that can feel eerie,
- two children who want a shared cozy spot,
- a ghostly presence that starts as a scare and ends as a helper,
- a sharing resolution that changes the emotional state of the room.

The story is generated from simulated state, not from a frozen paragraph.
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
    tags: set[str] = field(default_factory=set)

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


@dataclass
class Setting:
    id: str
    place: str
    upholstery: str
    eerie_detail: str
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


@dataclass
class ShareItem:
    id: str
    label: str
    phrase: str
    comfort: str
    can_share: bool = True
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class GhostBeat:
    id: str
    start_fear: int
    comfort_gain: int
    helper_line: str
    ending_image: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


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


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    room = world.entities.get("room")
    if not room:
        return out
    if room.meters["eerie"] < THRESHOLD:
        return out
    sig = ("fear",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in list(world.entities.values()):
        if e.role in {"child1", "child2"}:
            e.memes["fear"] += 1
    out.append("__quiet__")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    if world.entities["child1"].memes["share"] < THRESHOLD:
        return out
    if world.entities["child2"].memes["share"] < THRESHOLD:
        return out
    sig = ("share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.entities["room"].memes["warmth"] += 1
    out.append("__warm__")
    return out


CAUSAL_RULES = [Rule("fear", _r_fear), Rule("share", _r_share)]


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


def predict_room(world: World, beat: GhostBeat) -> dict:
    sim = world.copy()
    sim.get("room").meters["eerie"] += beat.start_fear
    propagate(sim, narrate=False)
    return {
        "fear": sum(sim.get(eid).memes["fear"] for eid in ("child1", "child2")),
        "warmth": sim.get("room").memes["warmth"],
    }


def tell(setting: Setting, share_item: ShareItem, beat: GhostBeat,
         child1: str = "Maya", child1_gender: str = "girl",
         child2: str = "Noah", child2_gender: str = "boy",
         parent: str = "mother") -> World:
    world = World()
    a = world.add(Entity(id=child1, kind="character", type=child1_gender, role="child1"))
    b = world.add(Entity(id=child2, kind="character", type=child2_gender, role="child2"))
    mom = world.add(Entity(id=parent, kind="character", type="mother", role="parent", label="mom"))
    room = world.add(Entity(id="room", kind="room", type="room", label=setting.place))
    sofa = world.add(Entity(id="sofa", label=setting.upholstery, attrs={"material": "upholstery"}))
    ghost = world.add(Entity(id="ghost", kind="character", type="thing", label="the little ghost", role="ghost"))

    a.memes["curious"] += 1
    b.memes["curious"] += 1
    room.meters["eerie"] += beat.start_fear
    ghost.meters["present"] += 1

    world.say(
        f"On a windy night, {a.id} and {b.id} crept into {setting.place}. "
        f"The old {sofa.label} was covered in {setting.upholstery}, and it looked as if it had heard forty secrets."
    )
    world.say(
        f"{setting.eerie_detail} Somewhere in the dark, a little shape seemed to wait by the sofa."
    )
    world.say(
        f'"Let\'s sit together," {a.id} whispered. "There is room for both of us on the {share_item.label}."'
    )

    world.para()
    prediction = predict_room(world, beat)
    world.facts["prediction"] = prediction
    world.facts["ghost_line"] = beat.helper_line
    world.facts["ending_image"] = beat.ending_image
    world.facts["share_item"] = share_item

    world.say(
        f"{b.id} heard a soft creak. {b.pronoun().capitalize()} clutched {b.pronoun('possessive')} sleeve, but {a.id} held out a hand and smiled."
    )
    world.say(
        f'"We can share the cozy spot," {a.id} said. "Even ghosts like a turn."'
    )
    a.memes["share"] += 1
    b.memes["share"] += 1
    propagate(world, narrate=False)

    world.para()
    room.meters["eerie"] = max(0.0, room.meters["eerie"] - 1.0)
    room.memes["warmth"] += 1
    world.say(
        f"Then the little ghost drifted out from behind the armchair and gave a tiny bow. {beat.helper_line}"
    )
    world.say(
        f"It did not want to scare anyone. It only wanted a turn on the soft {setting.upholstery} and a friend to share with."
    )
    world.say(
        f"{a.id} and {b.id} scooted over, making a neat space for three. The room felt less cold at once."
    )

    world.para()
    mom.memes["proud"] += 1
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"{mom.id} came in with a lamp and laughed softly. " f'"Good sharing," {mom.id} said. "That is how spooky rooms turn kind."'
    )
    world.say(
        f"By the end, the ghost was only a flutter of mist on the cushion, and {beat.ending_image}"
    )
    world.say(
        f"{a.id} and {b.id} sat shoulder to shoulder on the old upholstery, warm and brave, with one extra place left for the shy little ghost."
    )

    world.facts.update(
        child1=a, child2=b, parent=mom, room=room, sofa=sofa, ghost=ghost,
        setting=setting, share_item=share_item, beat=beat
    )
    return world


SETTINGS = {
    "parlor": Setting(id="parlor", place="the old parlor", upholstery="velvet upholstery",
                      eerie_detail="The wallpaper was shadowy and the clock had stopped at midnight."),
    "attic": Setting(id="attic", place="the attic room", upholstery="striped upholstery",
                     eerie_detail="Dust floated in the moonbeam, and a tiny draft made the curtains whisper."),
}

SHARE_ITEMS = {
    "sofa": ShareItem(id="sofa", label="sofa", phrase="the sofa", comfort="soft"),
    "bench": ShareItem(id="bench", label="bench", phrase="the bench", comfort="narrow"),
}

GHOST_BEATS = {
    "gentle": GhostBeat(
        id="gentle",
        start_fear=1,
        comfort_gain=1,
        helper_line="The ghost was only lonely, not scary.",
        ending_image="the old room felt like a place where everyone belonged",
    ),
    "warm": GhostBeat(
        id="warm",
        start_fear=2,
        comfort_gain=2,
        helper_line="It waved, as if asking politely for a seat.",
        ending_image="the upholstery looked less haunted and more inviting",
    ),
}

NAMES = ["Maya", "Noah", "Lena", "Owen", "Ivy", "Eli", "Zoe", "Finn"]


@dataclass
class StoryParams:
    setting: str
    share_item: str
    ghost_beat: str
    child1: str = "Maya"
    child1_gender: str = "girl"
    child2: str = "Noah"
    child2_gender: str = "boy"
    parent: str = "mother"
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for i in SHARE_ITEMS:
            for g in GHOST_BEATS:
                combos.append((s, i, g))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost story world about sharing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--share-item", choices=SHARE_ITEMS)
    ap.add_argument("--ghost-beat", choices=GHOST_BEATS)
    ap.add_argument("--child1")
    ap.add_argument("--child1-gender", choices=["girl", "boy"])
    ap.add_argument("--child2")
    ap.add_argument("--child2-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.share_item is None or c[1] == args.share_item)
              and (args.ghost_beat is None or c[2] == args.ghost_beat)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, share_item, beat = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        share_item=share_item,
        ghost_beat=beat,
        child1=args.child1 or rng.choice(NAMES),
        child1_gender=args.child1_gender or rng.choice(["girl", "boy"]),
        child2=args.child2 or rng.choice([n for n in NAMES if n != (args.child1 or "")]),
        child2_gender=args.child2_gender or rng.choice(["girl", "boy"]),
        parent=args.parent or rng.choice(["mother", "father"]),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old that includes the word "forty" and the word "upholstery".',
        f"Tell a sharing story set in {setting.place} where two children make room for a shy ghost on the old sofa.",
        f"Write a cozy spooky story in which children share {f['share_item'].phrase} and discover the ghost only wanted company.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["child1"]
    b = f["child2"]
    setting = f["setting"]
    share_item = f["share_item"]
    beat = f["beat"]
    return [
        ("Where does the story happen?",
         f"It happens in {setting.place}. The room has old upholstery, which is why it feels spooky at first."),
        ("What are the children sharing?",
         f"They are sharing {share_item.phrase}. Sharing the cozy spot helps the room feel less lonely."),
        ("Why did the room feel eerie at first?",
         f"The room felt eerie because it was quiet, dark, and old. The old upholstery and stopped clock made it seem like a ghost story."),
        ("What did the ghost really want?",
         f"The ghost only wanted a turn and someone to sit with. That is why the children were able to welcome it instead of running away."),
        ("How did the story end?",
         f"It ended with everyone sharing the soft seat. {beat.ending_image}."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does sharing mean?",
         "Sharing means letting someone else use or enjoy something with you. It is a kind way to make room for others."),
        ("What is upholstery?",
         "Upholstery is the soft covering on chairs, sofas, and benches. It makes furniture comfy to sit on."),
        ("What is a ghost story?",
         "A ghost story is a spooky tale about a ghost or a mysterious presence. In a child-friendly ghost story, the scare can turn into something kind."),
        ("What does forty mean?",
         "Forty is the number after thirty-nine and before forty-one. It is a bigger number used for counting."),
    ]


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


ASP_RULES = r"""
eerie(room) :- room_eerie(room, E), E >= 1.
fear(ch) :- eerie(room), child(ch).
shared(ch) :- share(ch), child(ch).
warm(room) :- shared(c1), shared(c2).
outcome(kind) :- warm(room), kind = calm.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for i in SHARE_ITEMS:
        lines.append(asp.fact("share_item", i))
    for g in GHOST_BEATS:
        lines.append(asp.fact("ghost_beat", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting/1.\n#show share_item/1.\n#show ghost_beat/1."))
    s = asp.atoms(model, "setting")
    i = asp.atoms(model, "share_item")
    g = asp.atoms(model, "ghost_beat")
    return [(a[0], b[0], c[0]) for a in s for b in i for c in g]


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python combo gates differ.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as exc:  # pragma: no cover
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    if rc == 0:
        print("OK: ASP and Python parity look good.")
    return rc


def explain_rejection(args: argparse.Namespace) -> str:
    return "(No story: the chosen settings do not make a meaningful sharing ghost story.)"


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.share_item not in SHARE_ITEMS or params.ghost_beat not in GHOST_BEATS:
        raise StoryError("(Invalid story parameters.)")
    world = tell(
        SETTINGS[params.setting],
        SHARE_ITEMS[params.share_item],
        GHOST_BEATS[params.ghost_beat],
        child1=params.child1,
        child1_gender=params.child1_gender,
        child2=params.child2,
        child2_gender=params.child2_gender,
        parent=params.parent,
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
        lines = ["== (1) Generation prompts =="]
        for i, p in enumerate(sample.prompts, 1):
            lines.append(f"{i}. {p}")
        lines.append("")
        lines.append("== (2) Story QA ==")
        for item in sample.story_qa:
            lines.append(f"Q: {item.question}")
            lines.append(f"A: {item.answer}")
        lines.append("")
        lines.append("== (3) World QA ==")
        for item in sample.world_qa:
            lines.append(f"Q: {item.question}")
            lines.append(f"A: {item.answer}")
        print("\n".join(lines))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show setting/1.\n#show share_item/1.\n#show ghost_beat/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatibly simple world combinations:")
        for combo in valid_combos():
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(setting="parlor", share_item="sofa", ghost_beat="gentle", child1="Maya", child1_gender="girl", child2="Noah", child2_gender="boy", parent="mother"),
            StoryParams(setting="attic", share_item="bench", ghost_beat="warm", child1="Lena", child1_gender="girl", child2="Owen", child2_gender="boy", parent="father"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
