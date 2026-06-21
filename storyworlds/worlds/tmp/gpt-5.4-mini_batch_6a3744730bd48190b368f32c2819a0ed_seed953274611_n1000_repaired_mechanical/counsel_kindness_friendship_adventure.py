#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/counsel_kindness_friendship_adventure.py
=======================================================================

A small storyworld about an adventure where a child and a friend face a tricky
choice, listen to counsel, practice kindness, and end up stronger friends.

The domain is intentionally compact:
- a pair of young adventurers travel a short route,
- they encounter a problem that could cause conflict,
- a helper gives counsel,
- the characters choose kindness over haste,
- friendship turns the ending into a bright discovery.

The world model uses typed entities with physical meters and emotional memes,
and the prose is rendered from the simulated state rather than from a frozen
template.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/counsel_kindness_friendship_adventure.py
    python storyworlds/worlds/gpt-5.4-mini/counsel_kindness_friendship_adventure.py --qa
    python storyworlds/worlds/gpt-5.4-mini/counsel_kindness_friendship_adventure.py --verify
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
BRAVERY_INIT = 5.0


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    scene: str
    route: str
    dark_spot: str
    view: str
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
class Trouble:
    id: str
    label: str
    provoke: str
    risk: str
    makes_tension: bool = True
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
class Counsel:
    id: str
    label: str
    text: str
    method: str
    kindness_hint: str
    power: int
    sense: int
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


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


def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["trouble"] < THRESHOLD or ("tension", ent.id) in world.fired:
            continue
        world.fired.add(("tension", ent.id))
        ent.memes["worry"] += 1
        out.append(f"{ent.id} felt the worry in the air.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["kindness"] < THRESHOLD or ("kindness", ent.id) in world.fired:
            continue
        world.fired.add(("kindness", ent.id))
        ent.memes["calm"] += 1
        out.append(f"{ent.id} grew calmer and kinder.")
    return out


CAUSAL_RULES = [Rule("tension", _r_tension), Rule("kindness", _r_kindness)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def reasonableness_ok(counsel: Counsel, trouble: Trouble, place: Place) -> bool:
    return counsel.sense >= 2 and trouble.makes_tension and "adventure" in place.tags


def useful_counsel(counsel: Counsel, trouble: Trouble) -> bool:
    return counsel.power >= 2 and counsel.sense >= 2 and trouble.makes_tension


def predict_turn(world: World, trouble: Trouble) -> dict:
    sim = world.copy()
    leader = sim.get("Leader")
    leader.meters["trouble"] += 1
    propagate(sim, narrate=False)
    return {"worry": leader.memes["worry"], "calm": leader.memes["calm"]}


def start_adventure(world: World, leader: Entity, friend: Entity, place: Place) -> None:
    leader.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On a bright morning, {leader.id} and {friend.id} set off on an adventure "
        f"through {place.label}. {place.scene}"
    )
    world.say(f"They followed {place.route} and watched for the {place.dark_spot}.")


def meet_trouble(world: World, leader: Entity, friend: Entity, trouble: Trouble) -> None:
    leader.meters["trouble"] += 1
    friend.meters["trouble"] += 1
    world.say(
        f"Then they found a problem: {trouble.label}. {trouble.provoke} "
        f"made the path feel risky."
    )


def offer_counsel(world: World, counselor: Entity, leader: Entity, trouble: Trouble, advice: Counsel) -> None:
    counselor.memes["care"] += 1
    pred = predict_turn(world, trouble)
    world.facts["prediction"] = pred
    world.say(
        f"{counselor.id} gave counsel in a gentle voice: \"{advice.text}\""
    )
    world.say(
        f"{counselor.id} pointed to the {trouble.risk} and showed a kinder way "
        f"to handle it."
    )


def choose_kindness(world: World, leader: Entity, friend: Entity, advice: Counsel) -> None:
    leader.memes["kindness"] += 1
    friend.memes["kindness"] += 1
    leader.memes["trust"] += 1
    friend.memes["trust"] += 1
    leader.meters["trouble"] = 0
    friend.meters["trouble"] = 0
    world.say(
        f"{leader.id} listened, nodded, and chose kindness. {friend.id} did too, "
        f"and the two friends worked together the kinder way."
    )
    world.say(f"They used {advice.method} and remembered {advice.kindness_hint}.")


def finish_adventure(world: World, leader: Entity, friend: Entity, place: Place) -> None:
    leader.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"In the end, they found the bright part of {place.label}: a small hidden "
        f"treasure, safe because they had stayed patient and kind."
    )
    world.say(
        f"{leader.id} and {friend.id} walked home side by side, smiling like two "
        f"friends who knew how to help each other."
    )


def tell(place: Place, trouble: Trouble, counsel: Counsel,
         leader_name: str = "Mina", leader_type: str = "girl",
         friend_name: str = "Theo", friend_type: str = "boy",
         counselor_name: str = "Aunt June", counselor_type: str = "woman") -> World:
    world = World()
    leader = world.add(Entity(id=leader_name, kind="character", type=leader_type, role="leader"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend"))
    counselor = world.add(Entity(id=counselor_name, kind="character", type=counselor_type, role="counselor"))
    world.add(Entity(id=place.id, type="place", label=place.label))
    world.add(Entity(id=trouble.id, type="trouble", label=trouble.label))

    start_adventure(world, leader, friend, place)
    world.para()
    meet_trouble(world, leader, friend, trouble)
    offer_counsel(world, counselor, leader, trouble, counsel)
    world.para()
    choose_kindness(world, leader, friend, counsel)
    finish_adventure(world, leader, friend, place)

    world.facts.update(
        leader=leader,
        friend=friend,
        counselor=counselor,
        place=place,
        trouble=trouble,
        counsel=counsel,
        outcome="kindness",
        predicted=world.facts.get("prediction", {}),
    )
    return world


PLACES = {
    "woods": Place(
        id="woods",
        label="the whispering woods",
        scene="Tall pines leaned together like old friends, and a narrow path curved ahead.",
        route="a mossy trail",
        dark_spot="shadowy fern patch",
        view="a bright clearing",
        tags={"adventure", "forest"},
    ),
    "cove": Place(
        id="cove",
        label="the little cove",
        scene="The waves tapped the rocks, and gulls called overhead like playful bells.",
        route="a shell-lined path",
        dark_spot="rocky tunnel",
        view="a bright tidepool",
        tags={"adventure", "sea"},
    ),
    "hills": Place(
        id="hills",
        label="the grassy hills",
        scene="The hill path rolled up and down, with daisies bending in the breeze.",
        route="a winding hill road",
        dark_spot="a steep bend",
        view="a sunny ridge",
        tags={"adventure", "trail"},
    ),
}

TROUBLES = {
    "lost_map": Trouble(
        id="lost_map",
        label="a torn map",
        provoke="The map had a missing corner",
        risk="the wrong turn",
        makes_tension=True,
        tags={"map"},
    ),
    "scary_bridge": Trouble(
        id="scary_bridge",
        label="a wobbly bridge",
        provoke="The bridge swayed and creaked",
        risk="the shaky boards",
        makes_tension=True,
        tags={"bridge"},
    ),
    "spilled_snack": Trouble(
        id="spilled_snack",
        label="a spilled snack box",
        provoke="The snack box had fallen open",
        risk="the crumbs on the path",
        makes_tension=True,
        tags={"snack"},
    ),
}

COUNSELS = {
    "share_map": Counsel(
        id="share_map",
        label="share the map",
        text="Let's slow down, share the map, and point together.",
        method="one child holding the map while the other watched the path",
        kindness_hint="kindness can make a hard path easier",
        power=3,
        sense=3,
        tags={"map", "kindness"},
    ),
    "hold_hands": Counsel(
        id="hold_hands",
        label="hold hands",
        text="Take my hand and we will cross one careful step at a time.",
        method="the friends holding hands and walking slowly",
        kindness_hint="friends stay brave when they help each other",
        power=3,
        sense=3,
        tags={"bridge", "friendship"},
    ),
    "offer_share": Counsel(
        id="offer_share",
        label="offer a share",
        text="We can offer a share and keep moving gently.",
        method="the friends sharing the snack instead of arguing",
        kindness_hint="kindness turns a small problem into teamwork",
        power=2,
        sense=2,
        tags={"snack", "kindness"},
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Nina", "Aria", "Zoe"]
BOY_NAMES = ["Theo", "Finn", "Owen", "Jude", "Eli"]


@dataclass
class StoryParams:
    place: str
    trouble: str
    counsel: str
    leader_name: str
    leader_type: str
    friend_name: str
    friend_type: str
    counselor_name: str
    counselor_type: str
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
    for pid, place in PLACES.items():
        for tid, trouble in TROUBLES.items():
            for cid, counsel in COUNSELS.items():
                if reasonableness_ok(counsel, trouble, place):
                    combos.append((pid, tid, cid))
    return combos


def explain_rejection(counsel: Counsel, trouble: Trouble, place: Place) -> str:
    return (
        f"(No story: {counsel.label} is too weak or odd for {trouble.label} at "
        f"{place.label}. The adventure needs a real problem and a real bit of counsel.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld about counsel, kindness, and friendship.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--counsel", choices=COUNSELS)
    ap.add_argument("--leader-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--counselor-name")
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
              and (args.trouble is None or c[1] == args.trouble)
              and (args.counsel is None or c[2] == args.counsel)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, trouble, counsel = rng.choice(sorted(combos))
    leader_type = rng.choice(["girl", "boy"])
    friend_type = "boy" if leader_type == "girl" else "girl"
    leader_name = args.leader_name or rng.choice(GIRL_NAMES if leader_type == "girl" else BOY_NAMES)
    friend_name = args.friend_name or rng.choice(BOY_NAMES if friend_type == "boy" else GIRL_NAMES)
    counselor_name = args.counselor_name or rng.choice(["Aunt June", "Uncle Reed", "Ms. Coral"])
    counselor_type = rng.choice(["woman", "man"])
    return StoryParams(
        place=place, trouble=trouble, counsel=counsel,
        leader_name=leader_name, leader_type=leader_type,
        friend_name=friend_name, friend_type=friend_type,
        counselor_name=counselor_name, counselor_type=counselor_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.trouble not in TROUBLES or params.counsel not in COUNSELS:
        raise StoryError("(Invalid StoryParams values.)")
    world = tell(
        PLACES[params.place], TROUBLES[params.trouble], COUNSELS[params.counsel],
        leader_name=params.leader_name, leader_type=params.leader_type,
        friend_name=params.friend_name, friend_type=params.friend_type,
        counselor_name=params.counselor_name, counselor_type=params.counselor_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle adventure story that includes the word "counsel" and shows kindness.',
        f"Tell a story about {f['leader'].id} and {f['friend'].id} on an adventure where a helper gives counsel and the friends choose kindness.",
        f"Write a child-friendly adventure where friendship grows stronger after some kind counsel.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    friend = f["friend"]
    counselor = f["counselor"]
    place = f["place"]
    trouble = f["trouble"]
    counsel = f["counsel"]
    pred = f.get("predicted", {})
    return [
        ("Who is the story about?",
         f"It is about {leader.id}, {friend.id}, and {counselor.id}. They go on a small adventure together."),
        ("What problem did they find?",
         f"They found {trouble.label}. It made the adventure feel tricky and called for a calm choice."),
        ("What did the helper give them?",
         f"{counselor.id} gave them counsel: {counsel.text} The advice helped them choose a kinder way forward."),
        ("How did kindness change the trip?",
         f"Kindness slowed them down and kept their friendship steady. The worry dropped, and they could work together instead of arguing."),
        ("How did the story end?",
         f"It ended with a happy discovery at {place.label}. The friends went home side by side, still friends and a little braver.")
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is counsel?",
         "Counsel is advice that helps someone make a good choice. In a story, counsel often comes from a wise helper."),
        ("What is kindness?",
         "Kindness means being gentle, thoughtful, and helpful to others. It can turn a hard moment into a better one."),
        ("What is friendship?",
         "Friendship is the caring bond between friends who trust and help each other."),
        ("What is an adventure?",
         "An adventure is an exciting journey or task, often with a problem to solve or a new place to explore."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:12} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="woods", trouble="lost_map", counsel="share_map",
        leader_name="Mina", leader_type="girl",
        friend_name="Theo", friend_type="boy",
        counselor_name="Aunt June", counselor_type="woman",
    ),
    StoryParams(
        place="cove", trouble="scary_bridge", counsel="hold_hands",
        leader_name="Aria", leader_type="girl",
        friend_name="Finn", friend_type="boy",
        counselor_name="Uncle Reed", counselor_type="man",
    ),
    StoryParams(
        place="hills", trouble="spilled_snack", counsel="offer_share",
        leader_name="Nina", leader_type="girl",
        friend_name="Owen", friend_type="boy",
        counselor_name="Ms. Coral", counselor_type="woman",
    ),
]


ASP_RULES = r"""
valid(P,T,C) :- place(P), trouble(T), counsel(C), okay(P,T,C).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("adventure", pid))
    for tid in TROUBLES:
        lines.append(asp.fact("trouble", tid))
    for cid in COUNSELS:
        lines.append(asp.fact("counsel", cid))
    for pid, place in PLACES.items():
        for tid, trouble in TROUBLES.items():
            for cid, counsel in COUNSELS.items():
                if reasonableness_ok(counsel, trouble, place):
                    lines.append(asp.fact("okay", pid, tid, cid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    try:
        cset, pset = set(asp_valid_combos()), set(valid_combos())
        if cset != pset:
            rc = 1
            print("MISMATCH in valid_combos:")
            print("only in clingo:", sorted(cset - pset))
            print("only in python:", sorted(pset - cset))
        else:
            print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test produced a story.")
    except Exception as e:
        rc = 1
        print("VERIFY FAILED:", e)
        traceback.print_exc()
    return rc


def build_storyworld() -> None:
    pass


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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for p, t, c in combos:
            print(f"  {p:8} {t:12} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
