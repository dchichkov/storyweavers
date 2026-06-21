#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bust_jimmy_sharing_kindness_twist_bedtime_story.py
==============================================================================

A standalone story world for a soft bedtime tale about Jimmy, a frightened
bedtime moment, an act of sharing, and a gentle twist that reveals the "scary"
thing was harmless all along.

The domain is intentionally small and constraint-checked:

- a bedtime room affords only certain kinds of little nighttime scares
- each scare has a real soothing need
- each shared comfort item offers concrete help
- only compatible combinations are allowed

The story always aims for a calm, child-facing arc:
setup -> small scare -> kind sharing -> harmless reveal -> sleepy ending
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly
# from a nested world directory such as storyworlds/worlds/gpt-5.4/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


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


@dataclass
class Room:
    id: str
    label: str
    opening: str
    bedtime_image: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Source:
    id: str
    signal: str
    seem: str
    truth: str
    need: str
    location: str
    reveal_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SharedItem:
    id: str
    label: str
    phrase: str
    offers: set[str] = field(default_factory=set)
    share_line: str = ""
    calm_line: str = ""
    ending_image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
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
        clone = World(self.room)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_fear_spreads(world: World) -> list[str]:
    out: list[str] = []
    buddy = world.get("buddy")
    if buddy.memes["fear"] < THRESHOLD:
        return out
    sig = ("fear_spreads", "jimmy")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    jimmy = world.get("jimmy")
    jimmy.memes["care"] += 1
    out.append("__care__")
    return out


def _r_shared_comfort(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    buddy = world.get("buddy")
    if item.meters["shared"] < THRESHOLD or buddy.memes["fear"] < THRESHOLD:
        return out
    sig = ("shared_comfort", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    buddy.memes["calm"] += 1
    buddy.memes["trust"] += 1
    world.get("jimmy").memes["kindness"] += 1
    out.append("__comfort__")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    buddy = world.get("buddy")
    item = world.get("item")
    source = world.get("source")
    needed = source.attrs.get("need", "")
    if buddy.memes["calm"] < THRESHOLD:
        return out
    if needed not in item.attrs.get("offers", set()):
        return out
    sig = ("reveal", source.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    source.meters["understood"] += 1
    buddy.memes["fear"] = 0.0
    buddy.memes["wonder"] += 1
    world.get("jimmy").memes["wonder"] += 1
    out.append("__reveal__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="fear_spreads", tag="emotional", apply=_r_fear_spreads),
    Rule(name="shared_comfort", tag="emotional", apply=_r_shared_comfort),
    Rule(name="reveal", tag="epistemic", apply=_r_reveal),
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


ROOMS = {
    "hallroom": Room(
        id="hallroom",
        label="the little room by the hall",
        opening="A stripe of moonlight lay across the floor from the half-open door.",
        bedtime_image="The hallway stayed silver and still outside their room.",
        affords={"bust_shadow", "draft_whistle"},
        tags={"bedroom", "hall"},
    ),
    "windowroom": Room(
        id="windowroom",
        label="the window room",
        opening="Curtains moved a little whenever the night breeze slipped past the glass.",
        bedtime_image="The window looked quiet again, with the stars pinned far above it.",
        affords={"branch_tap", "draft_whistle"},
        tags={"bedroom", "window"},
    ),
    "moonroom": Room(
        id="moonroom",
        label="the moon room",
        opening="A round patch of moonlight rested on the rug like pale milk.",
        bedtime_image="The moon kept watch while the room softened into sleep.",
        affords={"bust_shadow", "branch_tap"},
        tags={"bedroom", "moon"},
    ),
}

SOURCES = {
    "bust_shadow": Source(
        id="bust_shadow",
        signal="a tall shadow with a round head and a sharp nose",
        seem="It looked like a waiting giant outside the door.",
        truth="the old marble bust on the hall table, stretched long by moonlight",
        need="light",
        location="the hall table",
        reveal_line="When the warm light touched it, the giant melted into a quiet bust with a dusty nose.",
        tags={"shadow", "bust", "moonlight"},
    ),
    "branch_tap": Source(
        id="branch_tap",
        signal="a tick-tick-tap at the window",
        seem="It sounded as if tiny fingers were knocking to come in.",
        truth="a thin apple-tree branch brushing the glass whenever the breeze swayed it",
        need="story",
        location="the window",
        reveal_line="After Jimmy's gentle story slowed their breathing, they listened again and heard that the knocking had leaves in it.",
        tags={"window", "tree", "sound"},
    ),
    "draft_whistle": Source(
        id="draft_whistle",
        signal="a long soft whooo in the dark",
        seem="It sounded like a lonely night voice hiding near the curtain.",
        truth="a cool draft slipping through the loose corner of the window frame",
        need="warmth",
        location="the curtain",
        reveal_line="Once they were tucked warmly together, the lonely voice turned into plain old wind looking for a crack.",
        tags={"wind", "window", "sound"},
    ),
}

ITEMS = {
    "lantern": SharedItem(
        id="lantern",
        label="lantern",
        phrase="a small amber lantern",
        offers={"light"},
        share_line="Jimmy clicked on his little lantern and set it between them instead of keeping it on his own pillow.",
        calm_line="The warm circle of light made the room look smaller and kinder.",
        ending_image="The lantern glowed like a sleepy peach beside the bed.",
        tags={"light", "lantern"},
    ),
    "storybook": SharedItem(
        id="storybook",
        label="storybook",
        phrase="his favorite moon-and-mice storybook",
        offers={"story"},
        share_line="Jimmy opened his storybook in the middle and said there was plenty of moonlight on the pages for two children to share.",
        calm_line="The soft story voice gave the dark less room to grow.",
        ending_image="The storybook lay open on the blanket, as calm as a pond.",
        tags={"book", "story"},
    ),
    "quilt": SharedItem(
        id="quilt",
        label="quilt",
        phrase="a soft patchwork quilt",
        offers={"warmth"},
        share_line="Jimmy lifted his patchwork quilt and wrapped half around himself and half around his friend.",
        calm_line="Shared warmth made the room feel less wide and strange.",
        ending_image="The quilt rose and fell with two slow, sleepy breaths underneath it.",
        tags={"quilt", "warmth"},
    ),
}


@dataclass
class StoryParams:
    room: str
    source: str
    item: str
    buddy_name: str
    buddy_gender: str
    parent: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        room="hallroom",
        source="bust_shadow",
        item="lantern",
        buddy_name="Mina",
        buddy_gender="girl",
        parent="mother",
    ),
    StoryParams(
        room="windowroom",
        source="branch_tap",
        item="storybook",
        buddy_name="Theo",
        buddy_gender="boy",
        parent="father",
    ),
    StoryParams(
        room="windowroom",
        source="draft_whistle",
        item="quilt",
        buddy_name="Nora",
        buddy_gender="girl",
        parent="mother",
    ),
    StoryParams(
        room="moonroom",
        source="bust_shadow",
        item="lantern",
        buddy_name="Ben",
        buddy_gender="boy",
        parent="father",
    ),
]

GIRL_NAMES = ["Mina", "Nora", "Lulu", "Ava", "Tess", "Ruby", "Ella", "May"]
BOY_NAMES = ["Theo", "Ben", "Max", "Sam", "Eli", "Finn", "Noah", "Leo"]


def valid_combo(room_id: str, source_id: str, item_id: str) -> bool:
    if room_id not in ROOMS or source_id not in SOURCES or item_id not in ITEMS:
        return False
    room = ROOMS[room_id]
    source = SOURCES[source_id]
    item = ITEMS[item_id]
    return source_id in room.affords and source.need in item.offers


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for room_id, room in ROOMS.items():
        for source_id in room.affords:
            for item_id in ITEMS:
                if valid_combo(room_id, source_id, item_id):
                    combos.append((room_id, source_id, item_id))
    return sorted(combos)


def explain_rejection(room_id: str, source_id: str, item_id: str) -> str:
    room = ROOMS.get(room_id)
    source = SOURCES.get(source_id)
    item = ITEMS.get(item_id)
    if room is None or source is None or item is None:
        return "(No story: one of the chosen options does not exist in this world.)"
    if source_id not in room.affords:
        return (
            f"(No story: {room.label} does not create that bedtime scare. "
            f"Choose a source that can happen there.)"
        )
    return (
        f"(No story: sharing {item.phrase} does not solve the problem of "
        f"{source.signal}. This scare needs {source.need}, so the kindness has "
        f"to help in a concrete way.)"
    )


def predict_relief(world: World, source_id: str, item_id: str) -> dict:
    sim = world.copy()
    source = sim.get("source")
    item = sim.get("item")
    buddy = sim.get("buddy")
    source.attrs["need"] = SOURCES[source_id].need
    item.attrs["offers"] = set(ITEMS[item_id].offers)
    buddy.memes["fear"] += 1
    item.meters["shared"] += 1
    propagate(sim, narrate=False)
    return {
        "calm": buddy.memes["calm"],
        "revealed": source.meters["understood"] >= THRESHOLD,
    }


def setup_bed(world: World, jimmy: Entity, buddy: Entity, room: Room, item: SharedItem) -> None:
    jimmy.memes["sleepy"] += 1
    buddy.memes["sleepy"] += 1
    world.say(
        f"It was bedtime, and Jimmy and {buddy.id} were tucked into {room.label}."
    )
    world.say(room.opening)
    world.say(
        f"Between them waited {item.phrase}, because bedtime felt nicer when small things were shared."
    )


def little_scare(world: World, buddy: Entity, source: Source) -> None:
    buddy.memes["fear"] += 1
    source.attrs["need"] = source.need
    world.say(
        f"Then {buddy.id} noticed {source.signal} and sat very still. {source.seem}"
    )
    world.say(
        f'"Jimmy," {buddy.id} whispered, "did you see that?"'
    )
    propagate(world, narrate=False)


def kind_share(world: World, jimmy: Entity, buddy: Entity, item_cfg: SharedItem) -> None:
    item = world.get("item")
    item.meters["shared"] += 1
    item.attrs["offers"] = set(item_cfg.offers)
    world.say(item_cfg.share_line)
    world.say(item_cfg.calm_line)
    propagate(world, narrate=False)
    if buddy.memes["calm"] >= THRESHOLD:
        world.say(
            f"{buddy.id} leaned a little closer, and Jimmy stayed close too."
        )


def reveal_truth(world: World, source_cfg: Source, parent: Entity) -> None:
    source = world.get("source")
    if source.meters["understood"] < THRESHOLD:
        raise StoryError("The chosen comfort did not lead to a believable bedtime reveal.")
    world.say(
        f"Together they looked toward {source_cfg.location}, and the twist arrived all at once: it was only {source_cfg.truth}."
    )
    world.say(source_cfg.reveal_line)
    if source_cfg.id == "draft_whistle":
        world.say(
            f"{parent.label_word.capitalize()} came in, smiled, and pressed the loose window corner snug again."
        )
    else:
        world.say(
            f"{parent.label_word.capitalize()} peeped in, saw their brave little faces, and smiled from the doorway."
        )


def bedtime_end(world: World, jimmy: Entity, buddy: Entity, room: Room, item_cfg: SharedItem) -> None:
    jimmy.memes["calm"] += 1
    buddy.memes["calm"] += 1
    jimmy.memes["sleepy"] += 1
    buddy.memes["sleepy"] += 1
    world.say(
        f"Soon the room did not feel scary at all. It felt shared."
    )
    world.say(
        f"{item_cfg.ending_image} {room.bedtime_image}"
    )
    world.say(
        f"Jimmy and {buddy.id} drifted toward sleep, kinder and braver than they had been a little while before."
    )


def tell(
    room_cfg: Room,
    source_cfg: Source,
    item_cfg: SharedItem,
    buddy_name: str,
    buddy_gender: str,
    parent_type: str,
) -> World:
    world = World(room_cfg)
    jimmy = world.add(Entity(id="Jimmy", kind="character", type="boy", role="hero", label="Jimmy"))
    buddy = world.add(
        Entity(id=buddy_name, kind="character", type=buddy_gender, role="buddy", label=buddy_name)
    )
    parent = world.add(
        Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent")
    )
    source = world.add(
        Entity(id="source", kind="thing", type="source", label=source_cfg.id, attrs={"need": source_cfg.need})
    )
    item = world.add(
        Entity(
            id="item",
            kind="thing",
            type="comfort",
            label=item_cfg.label,
            phrase=item_cfg.phrase,
            attrs={"offers": set(item_cfg.offers)},
        )
    )

    setup_bed(world, jimmy, buddy, room_cfg, item_cfg)
    world.para()
    little_scare(world, buddy, source_cfg)

    pred = predict_relief(world, source_cfg.id, item_cfg.id)
    world.facts["predicted_relief"] = pred

    world.para()
    kind_share(world, jimmy, buddy, item_cfg)
    reveal_truth(world, source_cfg, parent)

    world.para()
    bedtime_end(world, jimmy, buddy, room_cfg, item_cfg)

    world.facts.update(
        jimmy=jimmy,
        buddy=buddy,
        parent=parent,
        room=room_cfg,
        source_cfg=source_cfg,
        item_cfg=item_cfg,
        item=item,
        source=source,
        kindness=item.meters["shared"] >= THRESHOLD,
        revealed=source.meters["understood"] >= THRESHOLD,
        buddy_was_scared=True,
    )
    return world


KNOWLEDGE = {
    "bust": [
        (
            "What is a bust?",
            "A bust is a statue of just a person's head and shoulders. In dim light, its shape can make a surprising shadow."
        )
    ],
    "shadow": [
        (
            "Why can shadows look bigger at night?",
            "A small thing can make a big shadow when light stretches behind it. That is why harmless objects can seem strange in the dark."
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern makes a soft light so you can see better. Seeing clearly often helps a scary guess turn into an ordinary thing."
        )
    ],
    "story": [
        (
            "How can a bedtime story help?",
            "A gentle story slows breathing and helps worried thoughts settle down. When a child feels calmer, it is easier to notice what is really happening."
        )
    ],
    "quilt": [
        (
            "Why can sharing a quilt feel comforting?",
            "Warmth and closeness help a body relax. When children feel safe together, little nighttime sounds often seem less scary."
        )
    ],
    "wind": [
        (
            "Why do windows sometimes whistle?",
            "Wind can squeeze through a tiny gap and make a soft sound. It can seem mysterious until you find where the air is slipping through."
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is choosing to help someone feel safer, happier, or less alone. Sharing something good is one simple way to show kindness."
        )
    ],
    "sharing": [
        (
            "What does sharing mean?",
            "Sharing means letting another person use something with you instead of keeping it only for yourself. It can turn one small comfort into comfort for two."
        )
    ],
    "tree": [
        (
            "Why do branches tap on windows?",
            "When the wind moves a branch, it can brush the glass and make a tapping sound. That sound may seem spooky until you notice the leaves and the breeze."
        )
    ],
}
KNOWLEDGE_ORDER = ["sharing", "kindness", "bust", "shadow", "lantern", "story", "quilt", "wind", "tree"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    buddy = f["buddy"]
    source_cfg = f["source_cfg"]
    item_cfg = f["item_cfg"]
    room = f["room"]
    return [
        (
            f'Write a gentle bedtime story for a 3-to-5-year-old where Jimmy shares '
            f'{item_cfg.phrase} with {buddy.id} after a small nighttime scare.'
        ),
        (
            f"Tell a story set in {room.label} where {source_cfg.signal} seems scary "
            f"at first, but a kind act of sharing leads to a soft twist."
        ),
        (
            f'Write a cozy story that includes the word "bust" and shows kindness, '
            f'sharing, and a harmless bedtime surprise.'
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    jimmy = f["jimmy"]
    buddy = f["buddy"]
    parent = f["parent"]
    room = f["room"]
    source_cfg = f["source_cfg"]
    item_cfg = f["item_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Jimmy and {buddy.id} at bedtime in {room.label}. They are together when a small nighttime scare begins."
        ),
        (
            f"What scared {buddy.id}?",
            f"{buddy.id} saw or heard {source_cfg.signal}. It seemed frightening at first because the dark made it easy to guess the wrong thing."
        ),
        (
            "How did Jimmy show kindness?",
            f"Jimmy shared {item_cfg.phrase} instead of keeping it all for himself. That kind choice helped {buddy.id} feel less alone and more calm."
        ),
        (
            "What was the twist?",
            f"The scary thing was not dangerous at all. It turned out to be {source_cfg.truth}."
        ),
        (
            f"Why did sharing help in this story?",
            f"Sharing helped because this scare needed {source_cfg.need}, and Jimmy's shared {item_cfg.label} offered exactly that. Once {buddy.id} felt calmer, they could notice the harmless truth."
        ),
        (
            f"What did {parent.label_word} do after the truth was known?",
            (
                f"{parent.label_word.capitalize()} came in and saw that the children were safe and calmer. "
                f"That gentle grown-up moment helps prove the bedtime worry has truly ended."
            ),
        ),
        (
            "How did the story end?",
            f"It ended quietly, with the room feeling shared instead of scary. Jimmy and {buddy.id} fell sleepy again after the harmless surprise was understood."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"sharing", "kindness"} | set(f["source_cfg"].tags) | set(f["item_cfg"].tags)
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
        shown_attrs = {k: v for k, v in e.attrs.items() if v}
        if shown_attrs:
            bits.append(f"attrs={shown_attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% room/source compatibility
room_has(Room, Source) :- affords(Room, Source).

% a comfort item works only if it offers the need required by the scare
fits(Source, Item) :- source(Source), item(Item), need(Source, Need), offers(Item, Need).

valid(Room, Source, Item) :- room(Room), source(Source), item(Item),
                             room_has(Room, Source), fits(Source, Item).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for room_id, room in ROOMS.items():
        lines.append(asp.fact("room", room_id))
        for source_id in sorted(room.affords):
            lines.append(asp.fact("affords", room_id, source_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        lines.append(asp.fact("need", source_id, source.need))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        for offer in sorted(item.offers):
            lines.append(asp.fact("offers", item_id, offer))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if cl - py:
            print("  only in ASP:", sorted(cl - py))
        if py - cl:
            print("  only in Python:", sorted(py - cl))

    # Smoke test ordinary generation and emission.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(7))
        sample2 = generate(params)
        if "Jimmy" not in sample2.story:
            raise StoryError("Smoke test story did not include Jimmy.")
        print("OK: smoke-test generation and emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world: Jimmy shares a comfort item, a small scare softens, and a twist reveals the harmless truth."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--buddy")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.room and args.source and args.item:
        if not valid_combo(args.room, args.source, args.item):
            raise StoryError(explain_rejection(args.room, args.source, args.item))

    combos = [
        combo for combo in valid_combos()
        if (args.room is None or combo[0] == args.room)
        and (args.source is None or combo[1] == args.source)
        and (args.item is None or combo[2] == args.item)
    ]
    if not combos:
        # Give a clearer reason when the user pinned an impossible partial choice.
        if args.room and args.source and args.item:
            raise StoryError(explain_rejection(args.room, args.source, args.item))
        raise StoryError("(No valid combination matches the given options.)")

    room_id, source_id, item_id = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    buddy_name = args.buddy or rng.choice(pool)
    if buddy_name == "Jimmy":
        buddy_name = rng.choice([n for n in pool if n != "Jimmy"])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        room=room_id,
        source=source_id,
        item=item_id,
        buddy_name=buddy_name,
        buddy_gender=gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS:
        raise StoryError(f"(No story: unknown room '{params.room}'.)")
    if params.source not in SOURCES:
        raise StoryError(f"(No story: unknown source '{params.source}'.)")
    if params.item not in ITEMS:
        raise StoryError(f"(No story: unknown item '{params.item}'.)")
    if not valid_combo(params.room, params.source, params.item):
        raise StoryError(explain_rejection(params.room, params.source, params.item))

    world = tell(
        room_cfg=ROOMS[params.room],
        source_cfg=SOURCES[params.source],
        item_cfg=ITEMS[params.item],
        buddy_name=params.buddy_name,
        buddy_gender=params.buddy_gender,
        parent_type=params.parent,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (room, source, item) combos:\n")
        for room_id, source_id, item_id in combos:
            print(f"  {room_id:10} {source_id:14} {item_id}")
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
            header = f"### Jimmy and {p.buddy_name}: {p.source} in {p.room} with {p.item}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
