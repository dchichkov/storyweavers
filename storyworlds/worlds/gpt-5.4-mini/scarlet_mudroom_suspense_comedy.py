#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/scarlet_mudroom_suspense_comedy.py
===================================================================

A standalone story world for a tiny comedy-with-suspense set in a mudroom.

Premise:
- A child prepares for a small outing or arrival in a mudroom.
- A scarlet item goes missing, creating a suspenseful search.
- The tension resolves with a comic reveal: the item was being used in a silly,
  harmless way.
- The ending proves the state change: the mudroom is tidy, the item is found,
  and everyone is relieved.

The script follows the Storyweavers world contract:
- typed entities with meters and memes
- state-driven prose
- reasonableness gate
- inline ASP twin
- three Q&A sets grounded in simulated state
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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    details: str
    afford: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    color: str
    type: str
    region: str
    visible: bool = True
    suspicious: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Query:
    id: str
    question: str
    answer: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_search(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("searched"):
        return out
    if world.facts.get("scarlet_hidden"):
        return out
    if world.facts.get("scarlet_missing"):
        if "mudroom" in world.entities:
            world.get("mudroom").meters["mystery"] += 1
        out.append("__tension__")
        world.facts["searched"] = True
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("searched") or world.facts.get("revealed"):
        return out
    if world.facts.get("scarlet_found"):
        world.get("mudroom").meters["mystery"] = 0.0
        out.append("__reveal__")
        world.facts["revealed"] = True
    return out


RULES = [Rule("search", _r_search), Rule("reveal", _r_reveal)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(s for s in bits if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def reasonableness_gate(setting: Setting, item: Item) -> bool:
    return setting.id == "mudroom" and item.color == "scarlet"


def choose_hiding_spot() -> str:
    return "inside a boot"


def _find_scarlet(world: World) -> None:
    world.facts["scarlet_missing"] = False
    world.facts["scarlet_found"] = True
    world.get("scarlet_item").meters["found"] += 1


def setup(world: World, child: Entity, parent: Entity, item: Entity) -> None:
    child.memes["curiosity"] += 1
    child.memes["joy"] += 1
    world.say(
        f"On a busy afternoon in the mudroom, {child.id} and {parent.label_word} were getting ready to go."
    )
    world.say(
        f"The hooks were full, the boots were lined up, and one thing was missing: the {item.label}."
    )


def suspense(world: World, child: Entity, parent: Entity, item: Entity) -> None:
    child.memes["worry"] += 1
    world.say(
        f'{child.id} blinked. "Wait... where is my {item.label}?" {child.pronoun()} asked.'
    )
    world.say(
        f"{parent.label_word.capitalize()} looked on the bench, then under the bench, then at the door."
    )
    world.say("For one funny second, the mudroom felt like a tiny mystery room.")


def comic_clue(world: World, child: Entity, item: Entity) -> None:
    world.say(
        f"Then a bright scarlet flash peeked out from {choose_hiding_spot()}. It was not stolen at all."
    )
    world.say(
        f"Someone had tucked the {item.label} there like a secret treasure, and the secret treasure had been sitting on a boot the whole time."
    )


def reveal(world: World, child: Entity, parent: Entity, item: Entity) -> None:
    child.memes["relief"] += 1
    parent.memes["relief"] += 1
    _find_scarlet(world)
    propagate(world, narrate=False)
    world.say(
        f'{child.id} pointed and laughed. "Oh! There you are!" {child.pronoun()} said.'
    )
    world.say(
        f"{parent.label_word.capitalize()} found the {item.label}, and both of them giggled because the great mystery was only a silly hiding place."
    )


def tidy_ending(world: World, child: Entity, parent: Entity, item: Entity) -> None:
    child.memes["safety"] += 1
    parent.memes["safety"] += 1
    world.say(
        f"In the end, the {item.label} was back where it belonged, the boots were lined up again, and the mudroom looked neat and calm."
    )
    world.say(
        f"{child.id} grinned at {parent.label_word}. " + "\"A scarlet surprise!\""
    )


def tell(setting: Setting, item: Item, child_name: str = "Mina", child_type: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    mudroom = world.add(Entity(id="mudroom", type="room", label="the mudroom"))
    scarlet = world.add(Entity(id="scarlet_item", type=item.type, label=item.label, attrs={"region": item.region}))
    world.facts["setting"] = setting.id
    world.facts["item"] = item
    world.facts["child"] = child
    world.facts["parent"] = parent
    world.facts["scarlet_hidden"] = True
    world.facts["scarlet_found"] = False

    setup(world, child, parent, scarlet)
    world.para()
    suspense(world, child, parent, scarlet)
    if reasonableness_gate(setting, item):
        comic_clue(world, child, scarlet)
        world.para()
        reveal(world, child, parent, scarlet)
        world.para()
        tidy_ending(world, child, parent, scarlet)
    else:
        raise StoryError("This story world only makes sense with a scarlet item in the mudroom.")
    return world


SETTINGS = {
    "mudroom": Setting(
        id="mudroom",
        place="the mudroom",
        details="A row of boots stood by the door, and a bench waited under a wall of hooks.",
        afford={"search", "hide"},
    )
}

ITEMS = {
    "scarlet_hat": Item("scarlet_hat", "hat", "a scarlet hat", "scarlet", "hat", "head"),
    "scarlet_glove": Item("scarlet_glove", "glove", "a scarlet glove", "scarlet", "glove", "hand"),
    "scarlet_scarf": Item("scarlet_scarf", "scarf", "a scarlet scarf", "scarlet", "scarf", "neck"),
}

NAMES_GIRL = ["Mina", "Lia", "Nora", "Pia", "Tess", "Ada"]
NAMES_BOY = ["Owen", "Theo", "Finn", "Max", "Eli", "Noah"]


def valid_combos() -> list[tuple[str, str]]:
    return [(sid, iid) for sid, s in SETTINGS.items() for iid, it in ITEMS.items() if reasonableness_gate(s, it)]


@dataclass
@dataclass
class StoryParams:
    setting: str
    item: str
    child: str
    child_type: str
    parent_type: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


KNOWLEDGE = {
    "mudroom": [(
        "What is a mudroom?",
        "A mudroom is a room near the door where people keep boots, coats, and other outdoor things.",
    )],
    "scarlet": [(
        "What does scarlet mean?",
        "Scarlet means a bright red color. It is a bold, cheerful color that is easy to notice.",
    )],
    "hide": [(
        "Why do people hide things in funny places?",
        "People sometimes hide things in funny places as a game or a joke so someone can have a little surprise.",
    )],
    "search": [(
        "What do you do when you lose something?",
        "You look carefully in the places it might be, and you ask for help if you need it.",
    )],
    "boot": [(
        "Why are boots useful by a door?",
        "Boots are useful by a door because they are easy to put on when you are going outside.",
    )],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item = f["item"]
    return [
        f'Write a short comedy story set in a mudroom that includes the word "{item.color}".',
        f"Tell a suspenseful but funny story about a child who thinks {item.phrase} has gone missing in the mudroom.",
        f"Write a child-friendly mystery-comedy where a scarlet thing is found in a silly place near the boots.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    item = f["item"]
    qa = [
        ("Where does the story take place?",
         "It takes place in the mudroom, where the boots and hooks made the search feel like a tiny mystery."),
        (f"What was missing at first?",
         f"{item.phrase} seemed to be missing, so {child.id} and {parent.label_word} had to look carefully."),
        (f"How did the story end?",
         f"The {item.label} was found in a silly hiding place, and the mudroom ended neat and calm."),
    ]
    if world.facts.get("scarlet_found"):
        qa.append((
            "Why was the ending funny?",
            "It was funny because the big mystery turned out to be a harmless joke. The missing thing had only been tucked away in an obvious little spot.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"mudroom", "scarlet", "search", "hide", "boot"}
    out: list[tuple[str, str]] = []
    for key in ["mudroom", "scarlet", "hide", "search", "boot"]:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("mudroom", "scarlet_hat", "Mina", "girl", "mother"),
    StoryParams("mudroom", "scarlet_glove", "Owen", "boy", "father"),
    StoryParams("mudroom", "scarlet_scarf", "Nora", "girl", "mother"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting != "mudroom":
        raise StoryError("This tiny story world only supports the mudroom setting.")
    item_id = args.item or rng.choice(sorted(ITEMS))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(NAMES_GIRL if child_type == "girl" else NAMES_BOY)
    parent_type = args.parent_type or rng.choice(["mother", "father"])
    return StoryParams("mudroom", item_id, child, child_type, parent_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ITEMS[params.item], params.child, params.child_type, params.parent_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


ASP_RULES = r"""
valid(setting, item) :- setting(setting), item(item), scarlet_item(item), mudroom(setting).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", sid) for sid in SETTINGS]
    lines += [asp.fact("item", iid) for iid in ITEMS]
    lines += [asp.fact("scarlet_item", iid) for iid, it in ITEMS.items() if it.color == "scarlet"]
    lines += [asp.fact("mudroom", "mudroom")]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH between ASP and Python valid_combos().")
    else:
        print(f"OK: valid_combos() matches ASP ({len(valid_combos())} combos).")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as ex:
        print(f"SMOKE TEST FAILED: {ex}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Scarlet mudroom mystery-comedy story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=["mother", "father"])
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
