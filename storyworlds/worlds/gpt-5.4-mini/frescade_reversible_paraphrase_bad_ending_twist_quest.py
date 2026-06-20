#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/frescade_reversible_paraphrase_bad_ending_twist_quest.py
========================================================================================

A standalone comedy storyworld built from the seed words:
frescade, reversible, paraphrase.

Premise:
- A child goes on a small quest to prepare a silly frescade poster.
- They use a reversible costume idea and a paraphrase machine in a playful way.
- A twist changes what the child thinks they found.
- The ending is a bad ending in the comic sense: the quest fails, but no one is hurt,
  and the final image proves the change in world state.

This file follows the Storyweavers contract:
- self-contained stdlib script
- imports storyworlds/results.py eagerly
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports --all, --seed, -n, --trace, --qa, --json, --asp, --verify, --show-asp
- includes Python validity checks and an inline ASP twin
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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Location:
    id: str
    label: str
    scene: str
    cozy: bool = True
    questy: bool = False

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
class ObjectSpec:
    id: str
    label: str
    phrase: str
    oddness: str
    reversible: bool = False
    printable: bool = False
    helpful: bool = False
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
class TwistSpec:
    id: str
    reveal: str
    consequence: str
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
    def __init__(self, location: Location) -> None:
        self.location = location
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
        clone = World(self.location)
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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["messy"] < THRESHOLD:
            continue
        sig = ("spill", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "floor" in world.entities:
            world.get("floor").meters["messy"] += 1
        out.append("__spill__")
    return out


def _r_misread(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["confused"] < THRESHOLD:
            continue
        sig = ("misread", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["certainty"] += 1
        out.append("__misread__")
    return out


CAUSAL_RULES = [
    Rule("spill", "physical", _r_spill),
    Rule("misread", "social", _r_misread),
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


def reason_ok(obj: ObjectSpec, twist: TwistSpec) -> bool:
    return obj.printable and twist.id in {"wrong_label", "mirror_name", "backwards_card"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for loc in LOCATIONS:
        for obj_id, obj in OBJECTS.items():
            for tw_id, tw in TWISTS.items():
                if reason_ok(obj, tw):
                    combos.append((loc, obj_id, tw_id))
    return combos


def sensible_responses() -> list[str]:
    return [r for r in RESPONSES if RESPONSES[r]["sense"] >= SENSE_MIN]


def should_bad_end(delay: int, confusion: int) -> bool:
    return delay + confusion >= 2


def predict(world: World, obj: ObjectSpec, twist: TwistSpec) -> dict:
    sim = world.copy()
    sim.get("hero").memes["confused"] += 1
    sim.get("artifact").meters["messy"] += 1
    propagate(sim, narrate=False)
    return {
        "messy_floor": sim.get("floor").meters["messy"] >= THRESHOLD,
        "certainty": sim.get("hero").memes["certainty"],
    }


def intro(world: World, hero: Entity, helper: Entity, loc: Location, quest: str) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {hero.id} and {helper.id} started a small quest at "
        f"{loc.label}. {loc.scene}"
    )
    world.say(
        f"{hero.id} had one goal: find the missing frescade sign before the show."
    )


def setup_props(world: World, obj: ObjectSpec) -> None:
    world.say(
        f"On the table sat {obj.phrase}, because the parade crew said the sign had to be "
        f"easy to read and a little silly."
    )
    world.say(
        f"The sign was for frescade, a word everyone kept saying with a grin."
    )


def use_reversible(world: World, hero: Entity, obj: ObjectSpec) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"{hero.id} found a reversible cape idea. If the blue side looked wrong, the red side "
        f"could flip over like a joke that changed its mind."
    )
    if obj.reversible:
        world.say(
            f"{hero.id} liked that {obj.label} was reversible too, so the plan felt clever."
        )


def warn_twist(world: World, helper: Entity, obj: ObjectSpec, twist: TwistSpec) -> None:
    pred = predict(world, obj, twist)
    helper.memes["concern"] += 1
    world.facts["prediction"] = pred
    world.say(
        f'{helper.id} squinted at the sign and said, "Are you sure that text says what you think it says?"'
    )
    world.say(
        f'{helper.id} pointed out that the word could slip into a paraphrase if the letters got turned around.'
    )


def take_step(world: World, hero: Entity, obj: ObjectSpec, twist: TwistSpec) -> None:
    hero.memes["confused"] += 1
    world.say(
        f"{hero.id} stepped toward the sign anyway and tried to read it out loud."
    )
    world.say(
        f"Then the twist arrived: the page was a mirror copy, so every line looked almost right and very wrong."
    )


def misread(world: World, hero: Entity, obj: ObjectSpec, twist: TwistSpec) -> None:
    hero.memes["confused"] += 1
    hero.meters["messy"] += 1
    world.get("artifact").meters["messy"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} read a paraphrase of the plan instead of the plan itself, and the words came out in the wrong order."
    )
    world.say(
        f"{obj.label.capitalize()} ended up on the back side of the page, where nobody could see it from the stage."
    )


def ending_bad(world: World, hero: Entity, helper: Entity, obj: ObjectSpec, resp: dict) -> None:
    world.say("For a moment everyone stared.")
    world.say(
        f"Then the speaker announced the show as if nothing had happened, which was the funniest bad ending of all."
    )
    world.say(
        f"{hero.id} and {helper.id} waved their empty paws, because the frescade sign had gone missing right when the crowd looked up."
    )


def ending_twist(world: World, hero: Entity, helper: Entity, obj: ObjectSpec, twist: TwistSpec) -> None:
    hero.memes["acceptance"] += 1
    helper.memes["acceptance"] += 1
    world.say(
        f"{helper.id} shrugged and said the twist had turned the quest into a comedy."
    )
    world.say(
        f"{hero.id} laughed, because the sign was not truly lost forever; it was just facing the wrong way."
    )
    world.say(
        f"At the end, the whole room saw a blank back page and still cheered for frescade."
    )


def tell(location: Location, obj: ObjectSpec, twist: TwistSpec, response: dict,
         hero_name: str = "Mina", hero_gender: str = "girl",
         helper_name: str = "Pip", helper_gender: str = "boy") -> World:
    world = World(location)
    hero = world.add(Entity(hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(helper_name, kind="character", type=helper_gender, role="helper"))
    artifact = world.add(Entity("artifact", type="thing", label=obj.label))
    world.add(Entity("floor", type="thing", label="the floor"))

    intro(world, hero, helper, location, "quest")
    world.para()
    setup_props(world, obj)
    use_reversible(world, hero, obj)
    warn_twist(world, helper, obj, twist)
    take_step(world, hero, obj, twist)

    world.para()
    if should_bad_end(delay=response["delay"], confusion=int(hero.memes["confused"])):
        misread(world, hero, obj, twist)
        ending_bad(world, hero, helper, obj, response)
        outcome = "bad"
    else:
        world.say(
            f"{hero.id} caught the mistake in time and turned the page back over."
        )
        world.say(
            f"The paraphrase was only a joke now, not a disaster."
        )
        ending_twist(world, hero, helper, obj, twist)
        outcome = "twist"

    world.facts.update(
        hero=hero, helper=helper, artifact=artifact, location=location,
        object_spec=obj, twist=twist, response=response, outcome=outcome
    )
    return world


LOCATIONS = {
    "school": Location("school", "the school hallway", "The lockers echoed like a drumline, and the stage door waited at the end.", questy=True),
    "kitchen": Location("kitchen", "the kitchen", "The kitchen smelled like toast, and the fridge had a magnet shaped like a star.", questy=True),
    "library": Location("library", "the library corner", "The library was hush-hush, except for one squeaky cart.", questy=True),
}

OBJECTS = {
    "banner": ObjectSpec("banner", "frescade banner", "a shiny frescade banner", "it loves being read backward", reversible=True, printable=True, tags={"frescade"}),
    "card": ObjectSpec("card", "paraphrase card", "a paraphrase card with big letters", "it keeps changing the joke", printable=True, tags={"paraphrase"}),
    "poster": ObjectSpec("poster", "reversible poster", "a reversible poster board", "one side smiles, the other side frowns", reversible=True, printable=True, tags={"reversible"}),
}

TWISTS = {
    "wrong_label": TwistSpec("wrong_label", "The sign says frescade, but the arrow points to the snack table.", "the quest becomes a silly chase", tags={"twist"}),
    "mirror_name": TwistSpec("mirror_name", "The letters are mirrored, like they were made by a mischievous twin.", "everyone reads a paraphrase by accident", tags={"twist"}),
    "backwards_card": TwistSpec("backwards_card", "The card is upside down, so the joke walks in backwards.", "the punchline arrives first and leaves the sign behind", tags={"twist"}),
}

RESPONSES = {
    "gasp": {"sense": 3, "delay": 0},
    "shrug": {"sense": 2, "delay": 1},
    "giggle": {"sense": 2, "delay": 1},
    "water_bucket": {"sense": 1, "delay": 2},
}

HEROES = ["Mina", "Pip", "Toby", "Lola", "Nia", "Owen"]
HELPERS = ["Pip", "Milo", "June", "Zed", "Bea", "Rae"]


@dataclass
@dataclass
class StoryParams:
    location: str
    object_id: str
    twist_id: str
    response_id: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
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
    ap = argparse.ArgumentParser(description="Comedy storyworld with frescade, reversible, paraphrase, twist, and quest.")
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--object", dest="object_id", choices=OBJECTS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
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
              if (args.location is None or c[0] == args.location)
              and (args.object_id is None or c[1] == args.object_id)
              and (args.twist is None or c[2] == args.twist)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    loc, obj_id, tw_id = rng.choice(sorted(combos))
    resp_id = args.response or rng.choice(sorted(sensible_responses()))
    hero_gender = "girl" if rng.random() < 0.5 else "boy"
    helper_gender = "boy" if hero_gender == "girl" else "girl"
    hero = args.hero or rng.choice(HEROES)
    helper = args.helper or rng.choice([n for n in HELPERS if n != hero])
    return StoryParams(loc, obj_id, tw_id, resp_id, hero, hero_gender, helper, helper_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny story for a 3-to-5-year-old that includes the words "frescade", "reversible", and "paraphrase".',
        f"Tell a comedy quest where {f['hero'].id} tries to save a frescade sign, but a twist makes the plan go wrong in a playful way.",
        f"Write a short story about a reversible prop and a paraphrase mistake, ending with a bad ending that is still silly, not scary.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper = f["hero"], f["helper"]
    obj, tw = f["object_spec"], f["twist"]
    out: list[QAItem] = [
        QAItem(
            question="What were the children trying to do?",
            answer=f"They were on a little quest to get the frescade sign ready before the show. They wanted to keep the joke readable and keep the stage from turning into a mess."
        ),
        QAItem(
            question=f"Why did {helper.id} warn {hero.id}?",
            answer=f"{helper.id} noticed that the sign could turn into a paraphrase if the letters were read the wrong way. That warning mattered because the twist would soon make the page look almost right but not quite."
        ),
    ]
    if f["outcome"] == "bad":
        qa_answer = (
            f"{hero.id} read the sign backward by mistake, so the quest ended with the frescade banner facing the wrong way. "
            f"The room still laughed, but the group did not get the sign fixed in time."
        )
    else:
        qa_answer = (
            f"{hero.id} spotted the twist and flipped the reversible page back over. "
            f"The paraphrase joke stayed funny, and the sign could still be used for the show."
        )
    qa.append(QAItem(question="How did the story end?", answer=qa_answer))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["object_spec"].tags) | set(world.facts["twist"].tags)
    out: list[QAItem] = []
    if "frescade" in tags:
        out.append(QAItem(
            question="What does frescade mean in this story?",
            answer="Frescade is the silly word on the show sign. It sounds playful, like a made-up festival name that everyone can cheer for."
        ))
    if "reversible" in tags:
        out.append(QAItem(
            question="What is reversible?",
            answer="Reversible means something can be flipped over and still work on the other side. A reversible thing can show one look now and a different look later."
        ))
    if "paraphrase" in tags:
        out.append(QAItem(
            question="What is a paraphrase?",
            answer="A paraphrase is a version of words that says the same thing in a different way. Sometimes it is helpful, and sometimes it can make a joke sound a little mixed up."
        ))
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("school", "banner", "mirror_name", "gasp", "Mina", "girl", "Pip", "boy"),
    StoryParams("library", "poster", "backwards_card", "shrug", "Toby", "boy", "June", "girl"),
    StoryParams("kitchen", "card", "wrong_label", "giggle", "Lola", "girl", "Zed", "boy"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for lid in LOCATIONS:
        lines.append(asp.fact("location", lid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.printable:
            lines.append(asp.fact("printable", oid))
        if o.reversible:
            lines.append(asp.fact("reversible", oid))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r["sense"]))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(L,O,T) :- location(L), object(O), twist(T), printable(O), reversible(O).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program(show="#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
    if set(asp_sensible()) == set(sensible_responses()):
        print(f"OK: sensible responses match ({sensible_responses()}).")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_story(world: World) -> str:
    return world.render()


def generate(params: StoryParams) -> StorySample:
    world = tell(
        LOCATIONS[params.location],
        OBJECTS[params.object_id],
        TWISTS[params.twist_id],
        RESPONSES[params.response_id],
        params.hero,
        params.hero_gender,
        params.helper,
        params.helper_gender,
    )
    return StorySample(
        params=params,
        story=build_story(world),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        print(asp_program(show="#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}")
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.hero} and {p.helper}: {p.object_id} / {p.twist_id}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
