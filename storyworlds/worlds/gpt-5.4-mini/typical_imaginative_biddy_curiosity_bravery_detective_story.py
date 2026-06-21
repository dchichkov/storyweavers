#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/typical_imaginative_biddy_curiosity_bravery_detective_story.py
=============================================================================================

A small storyworld for a child-sized detective tale.

Base seed idea
--------------
A typical day gets interesting when a biddy little detective with strong
Curiosity and Bravery follows imaginative clues through a neighborhood mystery.
The world keeps the domain tiny: one child detective, one missing object, a few
physical clues, a cautious helper, and a brave little turn where the truth is
found in a normal place that only seemed strange at first.

The story is built from simulated state, not a frozen paragraph. The detective's
curiosity changes the clues found, bravery changes whether they keep searching,
and the ending image proves what changed: the object is recovered, the mystery is
solved, and the child feels proud.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/typical_imaginative_biddy_curiosity_bravery_detective_story.py
    python storyworlds/worlds/gpt-5.4-mini/typical_imaginative_biddy_curiosity_bravery_detective_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/typical_imaginative_biddy_curiosity_bravery_detective_story.py --qa
    python storyworlds/worlds/gpt-5.4-mini/typical_imaginative_biddy_curiosity_bravery_detective_story.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    location: str = ""
    found: bool = False
    hidden: bool = False
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
    typical_detail: str
    clue_zone: str

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
class Suspect:
    id: str
    label: str
    alibi: str
    clue: str
    truthful: bool = True

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
    hiding_place: str
    clue_kind: str
    ordinary_spot: bool = False

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


def _r_curiosity(world: World) -> list[str]:
    out: list[str] = []
    d = world.get("Detective")
    if d.memes["curiosity"] < THRESHOLD:
        return out
    if world.fired.__contains__(("curiosity",)):
        return out
    world.fired.add(("curiosity",))
    d.memes["search"] += 1
    out.append("__curious__")
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    d = world.get("Detective")
    if d.memes["bravery"] < THRESHOLD:
        return out
    if world.fired.__contains__(("bravery",)):
        return out
    world.fired.add(("bravery",))
    d.memes["resolve"] += 1
    out.append("__brave__")
    return out


CAUSAL_RULES = [Rule("curiosity", "mind", _r_curiosity), Rule("bravery", "mind", _r_bravery)]


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


def predict_mystery(world: World, item_id: str) -> dict:
    sim = world.copy()
    _search(sim, item_id, narrate=False)
    item = sim.get(item_id)
    return {"found": item.found, "hidden": item.hidden, "confidence": sim.get("Detective").memes["resolve"]}


def _search(world: World, item_id: str, narrate: bool = True) -> None:
    detective = world.get("Detective")
    item = world.get(item_id)
    if item.found:
        return
    item.found = True
    item.hidden = False
    detective.meters["evidence"] += 1
    detective.memes["curiosity"] += 1
    detective.memes["bravery"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, setting: Setting, detective: Entity, helper: Entity) -> None:
    detective.memes["curiosity"] = 2.0
    detective.memes["bravery"] = 2.0
    helper.memes["worry"] = 1.0
    world.say(
        f"It was a typical day in {setting.place}, and {setting.typical_detail}. "
        f"{detective.id}, a biddy little detective, noticed something odd near {setting.clue_zone}."
    )
    world.say(
        f"{helper.id} followed along, hoping the mystery would be simple this time."
    )


def case_intro(world: World, detective: Entity, item: Entity, suspect: Suspect) -> None:
    world.say(
        f"Then {item.label} went missing. {detective.id} put on {detective.pronoun('possessive')} serious face and said, "
        f'"I will find the clue."'
    )
    world.say(
        f"The first suspect was {suspect.label}, who said, \"{suspect.alibi}\" "
        f"But the answer did not feel quite right."
    )


def imaginative_turn(world: World, detective: Entity, item: Entity, suspect: Suspect) -> None:
    detective.memes["imagination"] += 1
    world.say(
        f"{detective.id} looked at the room like a map. {detective.pronoun().capitalize()} imagined tiny footprints, secret doors, and a whisper trail."
    )
    if suspect.truthful:
        world.say(
            f"That wild picture helped in a sensible way: {suspect.clue} was the clue that pointed toward {item.hiding_place}."
        )
    else:
        world.say(
            f"Even the imaginative guess was wrong, so {detective.id} kept searching calmly."
        )


def warn(world: World, helper: Entity, detective: Entity, item: Entity, setting: Setting) -> None:
    pred = predict_mystery(world, item.id)
    helper.memes["worry"] += 1
    world.facts["predicted_found"] = pred["found"]
    world.say(
        f"{helper.id} frowned. \"You might be right to look there,\" {helper.pronoun()} said, "
        f"\"because {item.label} could be hidden in an ordinary spot like {item.hiding_place}.\""
    )


def search_scene(world: World, detective: Entity, item: Entity, suspect: Suspect) -> None:
    detective.memes["curiosity"] += 1
    world.say(
        f"{detective.id} took a brave breath and searched {suspect.clue}. "
        f"{detective.pronoun().capitalize()} checked carefully instead of giving up."
    )
    _search(world, item.id)


def reveal(world: World, detective: Entity, item: Entity, helper: Entity) -> None:
    world.say(
        f"At last, {detective.id} found {item.phrase} tucked inside {item.hiding_place}. "
        f"It had been hiding in a very normal place all along."
    )
    world.say(
        f"{helper.id} laughed with relief, and {detective.id} held up the clue like a small treasure."
    )
    detective.memes["pride"] += 1
    helper.memes["relief"] += 1


def ending(world: World, detective: Entity, item: Entity) -> None:
    world.say(
        f"{detective.id} walked home with {item.label} safe again, feeling not just curious but brave too."
    )
    world.say(
        f"By bedtime, the biddy detective knew that imagination could help solve a mystery, especially when paired with careful eyes."
    )


def tell(setting: Setting, item_cfg: Item, suspect_cfg: Suspect,
         detective_name: str = "Mina", detective_type: str = "girl",
         helper_name: str = "Aunt May", helper_type: str = "woman") -> World:
    world = World()
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_type, role="detective"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    item = world.add(Entity(id=item_cfg.id, type="thing", label=item_cfg.label, owner=detective.id, location=item_cfg.hiding_place, hidden=True))
    world.facts.update(setting=setting, item=item_cfg, suspect=suspect_cfg, detective=detective, helper=helper)

    setup(world, setting, detective, helper)
    world.para()
    case_intro(world, detective, item, suspect_cfg)
    imaginative_turn(world, detective, item, suspect_cfg)
    warn(world, helper, detective, item, setting)
    world.para()
    search_scene(world, detective, item, suspect_cfg)
    reveal(world, detective, item, helper)
    world.para()
    ending(world, detective, item)
    world.facts.update(found=item.found)
    return world


SETTINGS = {
    "street": Setting("street", "the quiet street", "the mailboxes stood in a neat row", "the front steps"),
    "house": Setting("house", "the cozy house", "the kitchen smelled like toast", "the shoe rack"),
    "school": Setting("school", "the little school", "the hallway buzzed with pencils and chatter", "the reading corner"),
}

ITEMS = {
    "badge": Item("badge", "a shiny badge", "the shiny badge", "inside a toy box", "object"),
    "notebook": Item("notebook", "a striped notebook", "the striped notebook", "under a cushion", "paper"),
    "key": Item("key", "a small key", "the small key", "in a bowl of crayons", "metal"),
}

SUSPECTS = {
    "cat": Suspect("cat", "the cat", "I never touched it", "a paw print by the box"),
    "brother": Suspect("brother", "the big brother", "I only read comics", "a comic book page on the floor"),
    "teacher": Suspect("teacher", "the teacher", "I only moved the chairs", "chalk dust on the shelf"),
}

GIRL_NAMES = ["Mina", "Lily", "Zoe", "Anna", "Nora", "Ella"]
BOY_NAMES = ["Toby", "Ben", "Leo", "Sam", "Owen", "Finn"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for i in ITEMS.values():
            if i.ordinary_spot:
                continue
            for su in SUSPECTS:
                combos.append((s, i.id, su))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    item: str
    suspect: str
    detective_name: str
    detective_type: str
    helper_name: str
    helper_type: str
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
    "curiosity": [("What is curiosity?", "Curiosity is the feeling that makes you want to know more and look for answers.")],
    "bravery": [("What is bravery?", "Bravery is doing something hard or a little scary because it needs to be done.")],
    "detective": [("What does a detective do?", "A detective looks for clues and uses them to solve a mystery.")],
    "clue": [("What is a clue?", "A clue is a little piece of information that helps solve a problem or mystery.")],
    "ordinary": [("What does ordinary mean?", "Ordinary means normal, common, or not special in a strange way.")],
}
KNOWLEDGE_ORDER = ["curiosity", "bravery", "detective", "clue", "ordinary"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a detective story for a child that includes the words "typical", "imaginative", and "biddy".',
        f"Tell a story where {f['detective'].id} uses curiosity and bravery to solve a small mystery about {f['item'].label}.",
        f"Write a gentle detective story where an imaginative little detective finds a missing object in an ordinary place.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    d = f["detective"]
    h = f["helper"]
    item = f["item"]
    return [
        ("Who is the story about?",
         f"It is about {d.id}, a biddy little detective, and {h.id}, who helped with the search."),
        ("What was missing?",
         f"{item.label.capitalize()} was missing, and that made {d.id} start looking for clues."),
        ("How did the detective solve the mystery?",
         f"{d.id} used curiosity, bravery, and an imaginative guess to search an ordinary hiding place. That is how {d.id} found {item.phrase}."),
        ("How did the story end?",
         f"It ended happily, with {item.label} found again and the detective feeling brave and proud."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"curiosity", "bravery", "detective", "clue", "ordinary"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("street", "badge", "cat", "Mina", "girl", "Aunt May", "woman"),
    StoryParams("house", "notebook", "brother", "Toby", "boy", "Dad", "father"),
    StoryParams("school", "key", "teacher", "Nora", "girl", "Mom", "mother"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.item is None or c[1] == args.item)
              and (args.suspect is None or c[2] == args.suspect)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, suspect = rng.choice(sorted(combos))
    if args.item == "badge" and args.setting == "school":
        pass
    detective_type = args.detective_type if hasattr(args, "detective_type") and args.detective_type else rng.choice(["girl", "boy"])
    detective_name = args.detective_name if hasattr(args, "detective_name") and args.detective_name else rng.choice(GIRL_NAMES if detective_type == "girl" else BOY_NAMES)
    helper_name = args.helper_name if hasattr(args, "helper_name") and args.helper_name else rng.choice(["Aunt May", "Dad", "Mom", "Uncle Lee"])
    helper_type = args.helper_type if hasattr(args, "helper_type") and args.helper_type else ("woman" if helper_name == "Aunt May" else "father")
    return StoryParams(setting, item, suspect, detective_name, detective_type, helper_name, helper_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ITEMS[params.item], SUSPECTS[params.suspect],
                 params.detective_name, params.detective_type, params.helper_name, params.helper_type)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["mother", "father", "woman", "man"])
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for suid in SUSPECTS:
        lines.append(asp.fact("suspect", suid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, I, U) :- setting(S), item(I), suspect(U).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos()")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        _ = sample.to_dict()
        print("OK: smoke test story generation works.")
    except Exception:
        rc = 1
        traceback.print_exc()
    print("OK: verify completed." if rc == 0 else "VERIFY FAILED.")
    return rc


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, i, u) for s in SETTINGS for i in ITEMS for u in SUSPECTS]


def explain_rejection() -> str:
    return "(No story: those choices do not describe a sensible little mystery.)"


def generate_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_gendered_name(args: argparse.Namespace, rng: random.Random) -> tuple[str, str]:
    gender = args.detective_type or rng.choice(["girl", "boy"])
    name = args.detective_name or generate_name(rng, gender)
    return name, gender


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
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
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(json.dumps([s.to_dict() for s in samples] if len(samples) > 1 else samples[0].to_dict(), indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
