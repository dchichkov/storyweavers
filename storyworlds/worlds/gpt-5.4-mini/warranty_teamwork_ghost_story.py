#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/warranty_teamwork_ghost_story.py
===============================================================

A standalone storyworld for a small ghost-story domain about teamwork and a
warranty.  The world is built around a child-friendly spooky setup: a little
house gets eerie at night, a treasured thing breaks, the family works together
to find the warranty, and the ending proves that cooperation turned the scary
problem into a safe fix.

The story model keeps the required contract shape:
- typed entities with physical meters and emotional memes
- a state-driven simulation, not a frozen paragraph template
- a Python reasonableness gate plus an inline ASP twin
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- QA sets grounded in the simulated world state
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
FEAR_START = 3.0
COOP_BONUS = 2.0


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

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class ItemKind:
    id: str
    label: str
    phrase: str
    place: str
    under_warranty: bool = True
    spooky: bool = False
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


@dataclass
class WarrantyHelp:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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


@dataclass
class Rule:
    name: str
    tag: str
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


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["spooky"] < THRESHOLD:
            continue
        sig = ("fear", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ch in list(world.entities.values()):
            if ch.kind == "character":
                ch.memes["fear"] += 1
        out.append("__fear__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("teamwork_done") and ("teamwork", "done") not in world.fired:
        world.fired.add(("teamwork", "done"))
        for ch in list(world.entities.values()):
            if ch.kind == "character":
                ch.memes["hope"] += COOP_BONUS
        out.append("__teamwork__")
    return out


CAUSAL_RULES = [Rule("fear", "social", _r_fear), Rule("teamwork", "social", _r_teamwork)]


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


def warranty_at_risk(item: ItemKind) -> bool:
    return item.under_warranty


def sensible_help() -> list[WarrantyHelp]:
    return [h for h in HELPS.values() if h.sense >= SENSE_MIN]


def product_broken(item: ItemKind, delay: int) -> bool:
    return item.spooky and delay >= 0


def can_fix(help_kind: WarrantyHelp, item: ItemKind, delay: int) -> bool:
    return help_kind.power >= (1 + delay)


def reason_for_story(item: ItemKind, help_kind: WarrantyHelp) -> str:
    if not item.under_warranty:
        return f"(No story: {item.label} is not under warranty, so there is no warranty lesson to tell.)"
    if help_kind.sense < SENSE_MIN:
        return f"(No story: response '{help_kind.id}' is too weak for a sensible teamwork story.)"
    return "(No story: this combination does not create a meaningful warranty problem.)"


def _break(world: World, item: Entity) -> None:
    item.meters["broken"] += 1
    item.meters["spooky"] += 1
    propagate(world, narrate=False)


def setup(world: World, child: Entity, helper: Entity, parent: Entity, item: ItemKind) -> None:
    child.memes["curiosity"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"On a windy night, {child.id} and {helper.id} were in the old house when a soft tap-tap sounded from the dark hall."
    )
    world.say(
        f"Near the stair closet sat {item.phrase}, and everyone knew it was still covered by a warranty card in a kitchen drawer."
    )


def eerie_turn(world: World, child: Entity, helper: Entity, item: ItemKind) -> None:
    child.memes["fear"] += FEAR_START
    helper.memes["fear"] += 1
    world.say(
        f"Then {item.label} gave a tiny shiver and went quiet. The room felt spooky, like the house itself was whispering."
    )


def teamwork_search(world: World, child: Entity, helper: Entity, item: ItemKind) -> None:
    world.facts["teamwork_done"] = True
    world.say(
        f'"Let\'s look together," {helper.id} said. {child.id} held a flashlight while {helper.id} checked the drawer, the counter, and the mailbox.'
    )
    world.say(
        f"At last they found the warranty card tucked under an old recipe book, right where the ghostly tapping had seemed to point."
    )


def claim_fix(world: World, parent: Entity, help_kind: WarrantyHelp, item: ItemKind) -> None:
    item_ent = world.get("item")
    if can_fix(help_kind, item, int(world.facts.get("delay", 0))):
        item_ent.meters["broken"] = 0.0
        item_ent.meters["spooky"] = 0.0
        body = help_kind.text.replace("{item}", item.label)
        world.say(
            f"{parent.label_word.capitalize()} phoned the company and, in a few days, {body}."
        )
        world.say(
            f"The strange tapping stopped once the new part arrived, and the old house felt safe again."
        )
    else:
        body = help_kind.fail.replace("{item}", item.label)
        world.say(f"{parent.label_word.capitalize()} tried, but {body}.")


def ending(world: World, child: Entity, helper: Entity, parent: Entity, item: ItemKind) -> None:
    child.memes["fear"] = 0.0
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"That night, {child.id} fell asleep with {helper.id} nearby, glad that teamwork had turned a spooky problem into a simple warranty fix."
    )
    world.say(
        f"By morning, the hallway was quiet, the card was safe on the table, and {item.label} was ready to be used again without any ghostly worry."
    )


def tell(item: ItemKind, help_kind: WarrantyHelp, child_name: str = "Maya",
         child_gender: str = "girl", helper_name: str = "Ben",
         helper_gender: str = "boy", parent_type: str = "mother", delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    item_ent = world.add(Entity(id="item", type="thing", label=item.label, attrs={"place": item.place}))

    setup(world, child, helper, parent, item)
    world.para()
    eerie_turn(world, child, helper, item)
    _break(world, item_ent)
    teamwork_search(world, child, helper, item)
    world.para()
    claim_fix(world, parent, help_kind, item)
    ending(world, child, helper, parent, item)

    world.facts.update(
        child=child, helper=helper, parent=parent, item=item, help_kind=help_kind,
        delay=delay, broke=item_ent.meters["broken"] >= THRESHOLD,
        teamwork=world.facts.get("teamwork_done", False),
    )
    return world


ITEMS = {
    "lantern": ItemKind("lantern", "lantern", "an old brass lantern", "the hallway", True, True, {"lantern", "ghost"}),
    "music_box": ItemKind("music_box", "music box", "a small music box", "the shelf", True, True, {"music_box", "ghost"}),
    "clock": ItemKind("clock", "clock", "a wall clock", "the upstairs landing", True, True, {"clock", "ghost"}),
    "vacuum": ItemKind("vacuum", "vacuum", "a noisy vacuum cleaner", "the closet", True, False, {"vacuum"}),
}

HELPS = {
    "replace": WarrantyHelp("replace", 3, 3, "sent a fresh {item} in a padded box", "could not replace the {item} because the warranty had run out", "replaced the {item} under warranty", {"warranty", "replace"}),
    "repair": WarrantyHelp("repair", 3, 2, "repaired the {item} and mailed it back", "could not repair the {item} because the damage was too much", "repaired the {item} under warranty", {"warranty", "repair"}),
    "ghost_bust": WarrantyHelp("ghost_bust", 1, 1, "sent a ghost catcher to chase the whispering away", "could not help because this was not really the right answer", "sent ghost catcher help", {"ghost"}),
}

NAMES = ["Maya", "Lila", "Nora", "Eli", "Ben", "Theo", "Ava", "Zoe"]
HELPER_NAMES = ["Ben", "Noah", "Iris", "Luca", "Mia", "Finn"]


@dataclass
@dataclass
class StoryParams:
    item: str
    help_kind: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    delay: int = 0
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for item_id, item in ITEMS.items():
        for help_id, help_kind in HELPS.items():
            if warranty_at_risk(item) and help_kind.sense >= SENSE_MIN and help_kind.id != "ghost_bust":
                combos.append((item_id, help_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story warranty teamwork world.")
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--help-kind", dest="help_kind", choices=HELPS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--child-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
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
    if args.help_kind and HELPS[args.help_kind].sense < SENSE_MIN:
        raise StoryError("(No story: chosen helper response is not sensible enough.)")
    combos = [c for c in valid_combos()
              if (args.item is None or c[0] == args.item)
              and (args.help_kind is None or c[1] == args.help_kind)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    item_id, help_id = rng.choice(sorted(combos))
    item = ITEMS[item_id]
    child_name = args.child_name or rng.choice(NAMES)
    helper_name = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != child_name] or HELPER_NAMES)
    child_gender = "girl" if child_name in {"Maya", "Lila", "Nora", "Ava", "Zoe", "Iris", "Mia"} else "boy"
    helper_gender = "girl" if helper_name in {"Maya", "Lila", "Nora", "Ava", "Zoe", "Iris", "Mia"} else "boy"
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(item_id, help_id, child_name, child_gender, helper_name, helper_gender, parent, args.delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(ITEMS[params.item], HELPS[params.help_kind], params.child_name, params.child_gender,
                 params.helper_name, params.helper_gender, params.parent, params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item = f["item"]
    return [
        f'Write a child-friendly ghost story that includes the word "warranty" and a teamwork fix for {item.label}.',
        f"Tell a spooky-but-kind story where {f['child'].id} and {f['helper'].id} work together to find the warranty for {item.phrase}.",
        f"Write a short ghost story with a safe ending where a broken {item.label} is handled by teamwork and warranty help.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, parent, item, help_kind = f["child"], f["helper"], f["parent"], f["item"], f["help_kind"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, {helper.id}, and {parent.label_word}. They work together around {item.label} when the house feels spooky."),
        ("What went wrong in the story?",
         f"{item.label} broke and made the hallway feel ghostly. That scary feeling was the problem the team had to solve."),
        ("How did they solve the problem?",
         f"{child.id} and {helper.id} searched together until they found the warranty card, and then {parent.label_word} used it to get {help_kind.qa_text}."),
        ("How did the ending change?",
         f"The spooky tapping stopped, {item.label} was safe again, and everyone felt relieved because the family worked as a team."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["item"].tags) | set(world.facts["help_kind"].tags) | {"warranty"}
    out: list[tuple[str, str]] = []
    if "warranty" in tags:
        out.append(("What is a warranty?",
                    "A warranty is a promise from the maker that they will help if something breaks in the covered time. It can mean a repair or a replacement."))
    if "ghost" in tags:
        out.append(("Why do ghost stories feel spooky?",
                    "Ghost stories use dark places, quiet sounds, and surprises to make the reader feel a little shivery. They are usually pretend stories, so the scare stays safe."))
    if "repair" in tags or "replace" in tags:
        out.append(("What does it mean to repair something?",
                    "To repair something means to fix it so it works again. A replacement means getting a new one instead."))
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes} role={e.role}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
under_warranty(I) :- item(I).
sensible(H) :- help(H), sense(H, S), sense_min(M), S >= M.
valid(I, H) :- item(I), help(H), under_warranty(I), sensible(H).
outcome(fixed) :- chosen_item(I), chosen_help(H), can_fix(I, H).
outcome(unchanged) :- chosen_item(I), chosen_help(H), not can_fix(I, H).
can_fix(I, H) :- item(I), help(H), power(H, P), delay(D), P >= 1 + D.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.under_warranty:
            lines.append(asp.fact("under_warranty", iid))
    for hid, help_kind in HELPS.items():
        lines.append(asp.fact("help", hid))
        lines.append(asp.fact("sense", hid, help_kind.sense))
        lines.append(asp.fact("power", hid, help_kind.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("chosen_item", params.item), asp.fact("chosen_help", params.help_kind), asp.fact("delay", params.delay)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    smoke = generate(resolve_params(argparse.Namespace(item=None, help_kind=None, parent=None, child_name=None, helper_name=None, delay=0), random.Random(7)))
    if not smoke.story.strip():
        rc = 1
        print("MISMATCH: smoke story empty.")
    else:
        print("OK: smoke generation succeeded.")
    cases = [StoryParams(i, h, "Maya", "girl", "Ben", "boy", "mother", 0) for i, h in valid_combos()]
    if any(asp_outcome(p) != "fixed" for p in cases):
        rc = 1
        print("MISMATCH: outcome check failed.")
    else:
        print("OK: outcome check passed.")
    return rc


CURATED = [
    StoryParams("lantern", "replace", "Maya", "girl", "Ben", "boy", "mother", 0),
    StoryParams("music_box", "repair", "Nora", "girl", "Iris", "girl", "father", 0),
    StoryParams("clock", "replace", "Eli", "boy", "Noah", "boy", "mother", 0),
]


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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid (item, help) combos:")
        for item, help_kind in asp_valid_combos():
            print(f"  {item:10} {help_kind}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
