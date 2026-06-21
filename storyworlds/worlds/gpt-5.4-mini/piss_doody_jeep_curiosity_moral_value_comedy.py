#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/piss_doody_jeep_curiosity_moral_value_comedy.py
==============================================================================

A small comedy storyworld about a child, a very curious jeep, and a moral-value
choice to clean up a silly mess. The seed words are folded into the world model:
"piss", "doody", and "jeep" are treated as story-relevant objects/events rather
than random decorations.

The domain:
- a child has a curious plan to inspect a toy jeep
- the jeep becomes involved in a goofy accident involving pee and poop
- a parent or helper responds with a calm moral lesson about honesty, cleanup,
  and not teasing others
- the ending proves the world changed by showing cleaned-up gear, relief, and a
  wiser choice for the next play session

The script follows the Storyweavers contract:
- typed entities with meters and memes
- a reasonableness gate plus inline ASP twin
- story-grounded QA and world-knowledge QA
- standalone stdlib-only execution
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Thing:
    id: str
    label: str
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    cleanable: bool = False
    reusable: bool = False

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
class Setup:
    id: str
    place: str
    opening: str
    toy_context: str
    ending_image: str
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
class Trigger:
    id: str
    label: str
    action: str
    curiosity: int
    risk: int
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
class Cleanup:
    id: str
    label: str
    action: str
    value: int
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
        self.things: dict[str, Thing] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_thing(self, thing: Thing) -> Thing:
        self.things[thing.id] = thing
        return thing

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def thing(self, tid: str) -> Thing:
        return self.things[tid]

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
        clone.things = copy.deepcopy(self.things)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
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


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    kid = world.get("kid")
    jeep = world.thing("jeep")
    if kid.memes["curiosity"] < THRESHOLD:
        return out
    if kid.meters["near_jeep"] < THRESHOLD:
        return out
    sig = ("mess",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    jeep.meters["piss"] += 1
    jeep.meters["doody"] += 1
    kid.memes["embarrassment"] += 1
    out.append("__mess__")
    return out


def _r_smell(world: World) -> list[str]:
    jeep = world.thing("jeep")
    if jeep.meters["piss"] + jeep.meters["doody"] < THRESHOLD:
        return []
    sig = ("smell",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for e in list(world.entities.values()):
        if e.role in {"kid", "parent"}:
            e.memes["surprise"] += 1
    return ["__smell__"]


RULES = [Rule("mess", _r_mess), Rule("smell", _r_smell)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend([s for s in lines if not s.startswith("__")])
    if narrate:
        for line in produced:
            world.say(line)
    return produced


SETUPS = {
    "driveway": Setup(
        "driveway",
        "the driveway",
        "On a warm afternoon, the front of the house felt like a tiny race track.",
        "A toy jeep waited beside a chalk road and a paper cone tollbooth.",
        "The cleaned jeep sat shining by the steps, ready for the next silly adventure.",
        {"outside", "jeep"},
    ),
    "garage": Setup(
        "garage",
        "the garage",
        "The garage was a little echo cave with boxes, bikes, and one squeaky toy jeep.",
        "The toy jeep sat under a shelf with old rags and a flashlight.",
        "The jeep stayed dry and shiny on the shelf, and the floor was clean again.",
        {"inside", "jeep"},
    ),
}

TRIGGERS = {
    "peek": Trigger(
        "peek",
        "peek under the seat",
        "look under the jeep seat",
        curiosity=3,
        risk=1,
        tags={"curiosity"},
    ),
    "switch": Trigger(
        "switch",
        "press the little button",
        "press the jeep button",
        curiosity=4,
        risk=2,
        tags={"curiosity"},
    ),
    "drive": Trigger(
        "drive",
        "race the jeep",
        "race the jeep over bumps",
        curiosity=2,
        risk=3,
        tags={"jeep"},
    ),
}

CLEANUPS = {
    "towel": Cleanup(
        "towel",
        "a big towel",
        "wipe the jeep clean with a towel",
        value=3,
        tags={"clean"},
    ),
    "soap": Cleanup(
        "soap",
        "warm soapy water",
        "wash the jeep with warm soapy water",
        value=4,
        tags={"clean"},
    ),
    "admit": Cleanup(
        "admit",
        "a truthful sorry",
        "tell the truth and help clean up",
        value=2,
        tags={"moral"},
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Zoe", "Ava"]
BOY_NAMES = ["Max", "Leo", "Theo", "Finn", "Ben"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setup in SETUPS.items():
        for tid in TRIGGERS:
            for cid in CLEANUPS:
                if setup and TRIGGERS[tid].curiosity >= 2 and CLEANUPS[cid].value >= 2:
                    combos.append((sid, tid, cid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setup: str
    trigger: str
    cleanup: str
    kid: str
    gender: str
    parent: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about curiosity, a jeep, and a moral-value cleanup.")
    ap.add_argument("--setup", choices=SETUPS)
    ap.add_argument("--trigger", choices=TRIGGERS)
    ap.add_argument("--cleanup", choices=CLEANUPS)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
              if (args.setup is None or c[0] == args.setup)
              and (args.trigger is None or c[1] == args.trigger)
              and (args.cleanup is None or c[2] == args.cleanup)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, tid, cid = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    kid = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(sid, tid, cid, kid, gender, parent)


def _make_world(params: StoryParams) -> World:
    setup = SETUPS[params.setup]
    trigger = TRIGGERS[params.trigger]
    cleanup = CLEANUPS[params.cleanup]
    world = World()
    kid = world.add(Entity("kid", kind="character", type=params.gender, role="kid", label=params.kid))
    parent = world.add(Entity("parent", kind="character", type=params.parent, role="parent", label="the parent"))
    jeep = world.add_thing(Thing("jeep", "jeep", tags={"jeep"}, cleanable=True, reusable=True))
    tr = world.add_thing(Thing(trigger.id, trigger.label, tags=trigger.tags))
    cl = world.add_thing(Thing(cleanup.id, cleanup.label, tags=cleanup.tags))
    kid.memes["curiosity"] = float(trigger.curiosity)
    kid.meters["near_jeep"] = 1
    world.say(f"{setup.opening} {setup.toy_context}")
    world.say(f'{kid.label} was a curious little {kid.type} who wanted to {trigger.action}.')
    world.say(f'When {kid.label} looked closer, the whole thing turned into a goofy surprise.')
    world.para()
    world.say(f'All at once, {kid.label} let out a tiny accident, and the jeep got { "piss" } and { "doody" }.')
    propagate(world, narrate=False)
    kid.memes["guilt"] += 1
    world.say(f'{parent.label_word.capitalize()} came over with a calm face and a funny sigh.')
    if cleanup.id == "admit":
        world.say(f'"Thanks for telling me the truth," {parent.label_word} said. "That is the moral thing to do."')
        world.say(f'Together they cleaned the jeep and the floor, and nobody had to hide anything.')
    elif cleanup.id == "towel":
        world.say(f'"Let\'s wipe it first, then wash our hands," {parent.label_word} said.')
        world.say(f'{kid.label} helped with {cl.label}, and the mess disappeared in little swipes.')
    else:
        world.say(f'"Warm water and soap will fix this," {parent.label_word} said, reaching for {cl.label}.')
        world.say(f'{kid.label} scrubbed until the jeep stopped smelling silly and started shining again.')
    kid.memes["relief"] += 1
    kid.memes["moral_value"] += 1
    world.para()
    world.say(f'{setup.ending_image}')
    world.facts.update(setup=setup, trigger=trigger, cleanup=cleanup, kid=kid, parent=parent, jeep=jeep, tr=tr, cl=cl)
    return world


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
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
    return [
        f'Write a comedy story for a preschooler that includes the words "piss", "doody", and "jeep".',
        f'Write a story where {f["kid"].label} gets curious about a jeep, makes a silly mess, and learns a moral-value lesson about telling the truth.',
        f'Tell a funny but kind story with a toy jeep, a cleanup, and a grown-up who helps instead of shaming the child.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid, parent, setup, trigger, cleanup = f["kid"], f["parent"], f["setup"], f["trigger"], f["cleanup"]
    qa = [
        ("Who is the story about?",
         f"It is about {kid.label} and {kid.pronoun('possessive')} {parent.label_word}. The two of them deal with a silly jeep mess together."),
        ("What did the child get curious about?",
         f"{kid.label} got curious about the jeep and wanted to {trigger.action}. Curiosity led {kid.label} closer to the toy than planned."),
        ("What went wrong?",
         f"The jeep got covered in piss and doody. That made the room smell silly and gave {kid.label} a reason to feel embarrassed."),
        ("How was the problem fixed?",
         f"They used {cleanup.label} and cleaned up together. The grown-up also helped {kid.label} tell the truth, which was the moral choice."),
    ]
    if f["jeep"].meters["piss"] + f["jeep"].meters["doody"] >= THRESHOLD:
        qa.append(("How did the jeep end up looking?",
                    f"It ended up clean and shiny again. The messy episode did not last because they cleaned it right away."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is curiosity?",
         "Curiosity is the feeling that makes you want to look, ask, and find out how something works. It can be helpful when it is paired with careful choices."),
        ("What is a moral value?",
         "A moral value is a good rule for how to treat other people. Telling the truth and helping clean up are examples of moral values."),
        ("What is a jeep?",
         "A jeep is a kind of vehicle, but in this story it is a toy jeep that can be pushed around and played with."),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    for t in world.things.values():
        meters = {k: v for k, v in t.meters.items() if v}
        lines.append(f"  {t.id:8} (thing  ) meters={meters} tags={sorted(t.tags)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("driveway", "peek", "admit", "Mia", "girl", "mother"),
    StoryParams("garage", "switch", "soap", "Max", "boy", "father"),
    StoryParams("driveway", "drive", "towel", "Lily", "girl", "mother"),
]


def explain_rejection() -> str:
    return "(No story: the chosen combination is not reasonable for this little comedy world.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETUPS:
        lines.append(asp.fact("setup", sid))
    for tid, t in TRIGGERS.items():
        lines.append(asp.fact("trigger", tid))
        lines.append(asp.fact("curiosity", tid, t.curiosity))
        lines.append(asp.fact("risk", tid, t.risk))
    for cid, c in CLEANUPS.items():
        lines.append(asp.fact("cleanup", cid))
        lines.append(asp.fact("value", cid, c.value))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, T, C) :- setup(S), trigger(T), cleanup(C), curiosity(T, K), K >= 2, value(C, V), V >= 2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    if rc == 0:
        print("OK: ASP parity and generation smoke test passed.")
    return rc


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
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a comedy story for a preschooler that includes the words "piss", "doody", and "jeep".',
        f'Write a story where {f["kid"].label} gets curious about a jeep, makes a silly mess, and learns a moral-value lesson about telling the truth.',
        f'Tell a funny but kind story with a toy jeep, a cleanup, and a grown-up who helps instead of shaming the child.',
    ]


if __name__ == "__main__":
    main()
