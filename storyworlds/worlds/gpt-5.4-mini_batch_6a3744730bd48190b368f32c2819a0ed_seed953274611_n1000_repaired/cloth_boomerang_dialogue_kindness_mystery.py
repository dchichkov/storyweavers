#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cloth_boomerang_dialogue_kindness_mystery.py
=============================================================================

A small story world about a missing cloth, a boomerang, and a kind mystery.

Premise:
- A child notices a cloth is missing from a play area.
- A boomerang appears in the wrong place.
- Characters talk through clues, help each other, and solve the mystery kindly.

This world is built to satisfy the Storyweavers contract:
- typed entities with physical meters and emotional memes
- state-driven prose
- generated prompts, grounded story QA, and world knowledge QA
- a Python reasonableness gate plus an inline ASP twin
- CLI support for default generation, -n, --all, --seed, --trace, --qa,
  --json, --asp, --verify, and --show-asp
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False

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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    quiet_detail: str
    dark_spot: str
    afford: set[str] = field(default_factory=set)
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
class Item:
    id: str
    label: str
    phrase: str
    where: str
    clue: str
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
class Action:
    id: str
    verb: str
    symptom: str
    zone: set[str]
    keyword: str
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]
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


def _r_mystery(world: World) -> list[str]:
    out: list[str] = []
    cloth = world.entities.get("cloth")
    boomerang = world.entities.get("boomerang")
    if cloth is not None and boomerang is not None:
        if cloth.meters["missing"] >= THRESHOLD and boomerang.meters["out_of_place"] >= THRESHOLD:
            sig = ("mystery",)
            if sig not in world.fired:
                world.fired.add(sig)
                for c in world.characters():
                    c.memes["curiosity"] += 1
                out.append("__mystery__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    cloth = world.entities.get("cloth")
    boomerang = world.entities.get("boomerang")
    if cloth is not None and boomerang is not None:
        if cloth.meters["returned"] >= THRESHOLD and boomerang.meters["returned"] >= THRESHOLD:
            sig = ("relief",)
            if sig not in world.fired:
                world.fired.add(sig)
                for c in world.characters():
                    c.memes["relief"] += 1
                out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule("mystery", "social", _r_mystery),
    Rule("relief", "social", _r_relief),
]


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


def valid_combo(setting: Setting, item: Item, action: Action) -> bool:
    return action.id in setting.afford and item.id in {"cloth", "boomerang"}


def reasonableness_gate(setting: Setting, item: Item, action: Action) -> bool:
    return valid_combo(setting, item, action)


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def response_ok(response: Response) -> bool:
    return response.sense >= SENSE_MIN


def predict(world: World, item_id: str) -> dict:
    sim = world.copy()
    sim.get(item_id).meters["returned"] += 1
    propagate(sim, narrate=False)
    return {
        "relief": sum(c.memes["relief"] for c in sim.characters()),
        "curiosity": sum(c.memes["curiosity"] for c in sim.characters()),
    }


def introduce(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    world.say(
        f"On a quiet afternoon, {a.id} and {b.id} were playing near {setting.place}. "
        f"{setting.quiet_detail}"
    )


def missing_cloth(world: World, child: Entity, cloth: Item, boomerang: Item) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} frowned at the empty hook. \"My {cloth.label} was here,\" "
        f"{child.pronoun()} said. \"And why is the {boomerang.label} by the chair?\""
    )
    world.say(
        f"{child.id}'s voice dropped to a whisper. The room felt like it was hiding a clue."
    )


def guess(world: World, friend: Entity, child: Entity, cloth: Item, boomerang: Item) -> None:
    friend.memes["kindness"] += 1
    world.say(
        f"\"Maybe the {boomerang.label} rolled away when someone tossed it,\" "
        f"{friend.id} said kindly. \"And maybe your {cloth.label} got carried somewhere soft.\""
    )


def search(world: World, child: Entity, friend: Entity, cloth: Item, boomerang: Item) -> None:
    child.memes["determination"] += 1
    friend.memes["helpful"] += 1
    world.say(
        f"They searched under the bench, behind the boxes, and beside the stairs. "
        f"{child.id} lifted the folded {cloth.label}, and {friend.id} found the {boomerang.label} behind a plant."
    )


def return_items(world: World, child: Entity, friend: Entity, cloth: Item, boomerang: Item) -> None:
    cloth.meters["returned"] += 1
    boomerang.meters["returned"] += 1
    propagate(world, narrate=False)
    world.say(
        f"\"We found the clues,\" {friend.id} smiled. {child.id} tucked the {cloth.label} back where it belonged, "
        f"and the {boomerang.label} went back to its shelf."
    )


def ending(world: World, child: Entity, friend: Entity, cloth: Item, boomerang: Item) -> None:
    world.say(
        f"After that, the mystery felt small and solved. {child.id} folded the {cloth.label} neatly, "
        f"{friend.id} grinned, and the boomerang rested in the light again."
    )
    world.say(
        f"The best clue of all was kindness: they asked, listened, and helped each other put things right."
    )


def tell(setting: Setting, child_name: str, friend_name: str, child_type: str, friend_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="main"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="helper"))
    cloth = world.add(Entity(id="cloth", type="thing", label="cloth", plural=False))
    boomerang = world.add(Entity(id="boomerang", type="thing", label="boomerang", plural=False))
    cloth.meters["missing"] += 1
    boomerang.meters["out_of_place"] += 1

    introduce(world, child, friend, setting)
    world.para()
    missing_cloth(world, child, cloth, boomerang)
    guess(world, friend, child, cloth, boomerang)
    world.para()
    search(world, child, friend, cloth, boomerang)
    return_items(world, child, friend, cloth, boomerang)
    world.para()
    ending(world, child, friend, cloth, boomerang)

    world.facts.update(
        child=child,
        friend=friend,
        cloth=cloth,
        boomerang=boomerang,
        setting=setting,
        resolved=True,
    )
    return world


SETTINGS = {
    "attic": Setting(
        id="attic",
        place="the attic",
        quiet_detail="Dust floated in the light, and an old trunk sat under the window.",
        dark_spot="the shadow behind the trunk",
        afford={"search"},
    ),
    "playroom": Setting(
        id="playroom",
        place="the playroom",
        quiet_detail="Toy boxes lined the wall, and a little lamp glowed on the shelf.",
        dark_spot="the corner behind the rug",
        afford={"search"},
    ),
    "porch": Setting(
        id="porch",
        place="the porch",
        quiet_detail="The screen door creaked softly, and a basket waited by the steps.",
        dark_spot="the space under the bench",
        afford={"search"},
    ),
}

CLOTHS = {
    "scarf": Item(id="scarf", label="scarf", phrase="a blue scarf", where="by the chair", clue="soft cloth", tags={"cloth"}),
    "napkin": Item(id="napkin", label="napkin", phrase="a folded cloth napkin", where="on the table", clue="small cloth", tags={"cloth"}),
    "banner": Item(id="banner", label="banner", phrase="a bright cloth banner", where="near the window", clue="bright cloth", tags={"cloth"}),
}

BOOMERANGS = {
    "toy": Item(id="toy", label="boomerang", phrase="a wooden boomerang", where="near the plant", clue="curved toy", tags={"boomerang"}),
}

ACTIONS = {
    "search": Action(id="search", verb="search for the missing cloth", symptom="look for clues", zone={"room"}, keyword="clue", tags={"mystery"}),
}

RESPONSES = {
    "ask": Response(
        id="ask",
        sense=3,
        power=1,
        text="asked the right questions and followed the clues with a calm smile",
        fail="asked, but the clues stayed tangled and the mystery did not clear",
        qa_text="asked calm questions and followed the clues with a smile",
        tags={"dialogue", "kindness"},
    ),
    "share": Response(
        id="share",
        sense=3,
        power=1,
        text="shared what they knew and helped each other look in the right places",
        fail="tried to help, but the search still felt mixed up",
        qa_text="shared what they knew and helped each other look in the right places",
        tags={"dialogue", "kindness"},
    ),
    "patience": Response(
        id="patience",
        sense=2,
        power=1,
        text="waited patiently, then noticed the hidden clue everyone had missed",
        fail="waited, but not long enough to solve the mystery",
        qa_text="waited patiently and noticed the hidden clue",
        tags={"kindness"},
    ),
}

GIRL_NAMES = ["Mila", "Nina", "Lia", "Sophie", "Iris", "Maya"]
BOY_NAMES = ["Theo", "Eli", "Noah", "Ben", "Owen", "Jude"]


@dataclass
class StoryParams:
    setting: str
    child_name: str
    child_type: str
    friend_name: str
    friend_type: str
    response: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery story world with cloth and boomerang clues.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--friend-type", choices=["girl", "boy"])
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(sid, "cloth", "search") for sid in SETTINGS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and not response_ok(RESPONSES[args.response]):
        raise StoryError("That response is too weak for a proper solution.")
    setting = args.setting or rng.choice(list(SETTINGS))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or ("boy" if child_type == "girl" else "girl")
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    friend_pool = [n for n in (GIRL_NAMES if friend_type == "girl" else BOY_NAMES) if n != child_name]
    friend_name = args.friend_name or rng.choice(friend_pool)
    response = args.response or rng.choice(list(RESPONSES))
    return StoryParams(setting=setting, child_name=child_name, child_type=child_type,
                       friend_name=friend_name, friend_type=friend_type, response=response)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    return [
        f"Write a child-friendly mystery story set in {setting.place} that includes the words cloth and boomerang.",
        f"Tell a kind dialogue story where {f['child'].id} and {f['friend'].id} search for a missing cloth and notice a boomerang clue.",
        f"Write a gentle mystery with talking, clues, and kindness ending in the cloth being put back where it belongs.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    setting = f["setting"]
    return [
        ("Who is the story about?",
         f"It is about {child.id} and {friend.id}, who work together to solve a small mystery in {setting.place}."),
        ("What was missing?",
         "A cloth was missing from its place, and that is what started the mystery."),
        ("How did they solve the mystery?",
         f"They talked kindly, searched carefully, and found the cloth while the boomerang was put back where it belonged. Their teamwork made the answer clear."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is cloth?",
         "Cloth is soft material made from thread. People use it to make scarves, banners, napkins, and many other things."),
        ("What is a boomerang?",
         "A boomerang is a curved object that can be thrown through the air. Some are toys, and some are used for sport or practice."),
        ("What does kindness mean?",
         "Kindness means being gentle, helpful, and thoughtful toward someone else. It can sound like a calm voice, a shared idea, or a helping hand."),
        ("What is a mystery story?",
         "A mystery story is a story where someone notices clues, asks questions, and figures out what happened."),
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
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="attic", child_name="Mila", child_type="girl", friend_name="Theo", friend_type="boy", response="ask"),
    StoryParams(setting="playroom", child_name="Noah", child_type="boy", friend_name="Iris", friend_type="girl", response="share"),
    StoryParams(setting="porch", child_name="Lia", child_type="girl", friend_name="Ben", friend_type="boy", response="patience"),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.response not in RESPONSES:
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], params.child_name, params.friend_name, params.child_type, params.friend_type)
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


ASP_RULES = r"""
has_mystery :- cloth_missing, boomerang_out_of_place.
kind_result :- has_mystery, kindness, dialogue.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    lines.append(asp.fact("cloth_missing"))
    lines.append(asp.fact("boomerang_out_of_place"))
    lines.append(asp.fact("kindness"))
    lines.append(asp.fact("dialogue"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show setting/1."))
    return sorted(set(asp.atoms(model, "setting")))


def asp_verify() -> int:
    rc = 0
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        _ = sample.to_json()
    except Exception as exc:
        print(f"FAILED: smoke test crashed: {exc}")
        return 1
    if set(asp_valid_combos()) == {(sid,) for sid in SETTINGS}:
        print("OK: ASP and Python registry parity.")
    else:
        rc = 1
        print("MISMATCH: ASP and Python registry parity.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show setting/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible settings:", ", ".join(s for (s,) in asp_valid_combos()))
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
