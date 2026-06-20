#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/schooner_heed_brocolli_humor_mystery.py
========================================================================

A tiny standalone storyworld for a humorous mystery aboard a schooner.

Seed words:
- schooner
- heed
- brocolli

Style:
- Mystery, with a light humorous turn.

This world models a small cast on a sailing schooner where a curious child,
a careful grown-up, and a missing crate of brocolli create a comic mystery.
The story turns on noticing clues, heeding a warning, and finding that the
"mystery" is smaller than it first seemed: the brocolli was moved for a
sensible reason and the final reveal is a playful surprise.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/schooner_heed_brocolli_humor_mystery.py
    python storyworlds/worlds/gpt-5.4-mini/schooner_heed_brocolli_humor_mystery.py --all
    python storyworlds/worlds/gpt-5.4-mini/schooner_heed_brocolli_humor_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/schooner_heed_brocolli_humor_mystery.py --verify
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
class Setting:
    id: str
    place: str
    mood: str
    mystery_detail: str
    humor_detail: str

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
class Clue:
    id: str
    label: str
    where_found: str
    reveals: str
    funny: str = ""

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
class Response:
    id: str
    sense: int
    result: str
    explanation: str

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
        clone.facts = copy.deepcopy(self.facts)
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


def _r_notice(world: World) -> list[str]:
    out = []
    if world.get("mystery_box").meters["opened"] >= THRESHOLD and ("notice",) not in world.fired:
        world.fired.add(("notice",))
        world.get("child").memes["curiosity"] += 1
        out.append("__notice__")
    return out


def _r_laugh(world: World) -> list[str]:
    out = []
    if world.get("cook").memes["flustered"] >= THRESHOLD and ("laugh",) not in world.fired:
        world.fired.add(("laugh",))
        world.get("child").memes["joy"] += 1
        out.append("__laugh__")
    return out


CAUSAL_RULES = [Rule("notice", "social", _r_notice), Rule("laugh", "social", _r_laugh)]


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


SETTINGS = {
    "deck": Setting("deck", "the schooner's deck", "salt-bright",
                    "a crate was missing from the galley hatch",
                    "the gulls kept watching like tiny nosy detectives"),
    "galley": Setting("galley", "the galley", "busy and warm",
                      "the brocolli crate had gone quiet",
                      "a spoon balanced in a cup like it was listening"),
}

CHARACTERS = {
    "child": ("Mina", "girl"),
    "captain": ("Captain Reed", "man"),
    "cook": ("Nell", "woman"),
}


CLUES = {
    "seaweed": Clue("seaweed", "a strand of seaweed", "on the railing",
                    "someone had been near the net before breakfast",
                    "It looked like the schooner had a salad wearing a hat."),
    "crayon": Clue("crayon", "a green crayon", "by the chart table",
                   "the child had been drawing a map of the ship",
                   "The map had a fish in the corner, which did not help."),
    "crumbs": Clue("crumbs", "crumbs on a plate", "beside the galley door",
                   "the cook had hurried past with lunch",
                   "The crumbs were suspiciously broccoli-colored."),
}

RESPONSES = {
    "check_hatch": Response("check_hatch", 3, "opened the hatch and looked below",
                            "looked under the hatch and found the crate was only moved",
                            "opened the hatch and looked below"),
    "call_cook": Response("call_cook", 3, "asked the cook with a patient smile",
                          "asked the cook, who laughed and explained the whole thing",
                          "asked the cook with a patient smile"),
    "storm_off": Response("storm_off", 1, "stormed around and blamed the gulls",
                          "made everybody more confused",
                          "stormed around and blamed the gulls"),
}

GIRL_NAMES = ["Mina", "Lily", "Ada", "Nora", "Zoe"]
BOY_NAMES = ["Eli", "Noah", "Finn", "Theo", "Leo"]
TRAITS = ["curious", "careful", "sensible", "mischievous"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    clue: str
    response: str
    child_name: str
    child_gender: str
    trait: str
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


def reasonableness_ok(setting: Setting, clue: Clue) -> bool:
    return setting.id in {"deck", "galley"} and clue.id in CLUES


def valid_combos() -> list[tuple[str, str]]:
    return [(s, c) for s in SETTINGS for c in CLUES if reasonableness_ok(SETTINGS[s], CLUES[c])]


def explain_rejection() -> str:
    return "(No story: that combination does not leave a clear, child-sized mystery.)"


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def tell(setting: Setting, clue: Clue, response: Response, child_name: str, child_gender: str, trait: str) -> World:
    world = World()
    child = world.add(Entity("child", "character", child_gender, role="observer", traits=[trait]))
    captain = world.add(Entity("captain", "character", "man", role="adult", label="the captain"))
    cook = world.add(Entity("cook", "character", "woman", role="adult", label="the cook"))
    box = world.add(Entity("mystery_box", "thing", "thing", label="the brocolli crate"))
    box.meters["opened"] = 0.0

    world.facts["setting"] = setting
    world.facts["clue"] = clue
    world.facts["response"] = response
    world.facts["child_name"] = child_name
    world.facts["child_gender"] = child_gender
    world.facts["trait"] = trait

    child.id = child_name
    child.type = child_gender
    world.entities[child_name] = world.entities.pop("child")
    captain.id = "Captain Reed"
    cook.id = "Nell"
    world.entities[captain.id] = world.entities.pop("captain")
    world.entities[cook.id] = world.entities.pop("cook")

    world.say(
        f"On the schooner, {child_name} liked to solve little mysteries. "
        f"The day began on {setting.place}, where the air smelled of salt and breakfast."
    )
    world.say(
        f"Then everyone noticed the brocolli crate was gone. "
        f"{setting.mystery_detail.capitalize()}"
    )

    world.para()
    world.say(
        f"{child_name} found {clue.label} {clue.where_found}. "
        f"{clue.reveals.capitalize()}."
    )
    world.say(
        f"{child_name} had to heed the clue instead of guessing too fast."
    )

    world.para()
    child.memes["curiosity"] += 1
    if response.sense >= SENSE_MIN:
        world.say(
            f"{child_name} chose to {response.result}. "
            f"{response.explanation.capitalize()}."
        )
        box.meters["opened"] += 1
        cook.memes["flustered"] += 1
        propagate(world, narrate=False)
        world.say(
            f"Sure enough, the brocolli was not stolen at all. "
            f"It had been moved so the cook could keep it cool and stop the gulls from peeking."
        )
        world.say(
            f"The cook laughed, the captain snorted, and {child_name} grinned at the very normal mystery."
        )
        world.say(
            f"At the end, the brocolli came back to the galley, and the schooner sailed on with a tidy crate and a much happier breakfast."
        )
    else:
        world.say(
            f"{child_name} tried to {response.result}, but that only made everybody more confused. "
            f"The captain had to intervene and point to the obvious answer."
        )
        world.say(
            f"Even then, the brocolli was only hidden for safety, so the mystery still ended with a laugh."
        )

    world.facts.update(
        setting=setting,
        clue=clue,
        response=response,
        child=child,
        captain=world.get("Captain Reed"),
        cook=world.get("Nell"),
        box=box,
        solved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    clue = f["clue"]
    return [
        f'Write a humorous mystery story for a young child that takes place on {setting.place} and includes the word "schooner".',
        f"Tell a playful detective story where a child notices {clue.label} and has to heed it before finding out where the brocolli went.",
        "Write a short mystery with a funny ending about a missing vegetable crate aboard a schooner.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    clue = f["clue"]
    setting = f["setting"]
    return [
        QAItem("What kind of boat was the story set on?", "It was set on a schooner, which made the mystery feel like a little shipboard adventure."),
        QAItem("What went missing?", "The brocolli crate went missing, which is why everyone started looking around so carefully."),
        QAItem(f"What clue did {child.id} find?", f"{child.id} found {clue.label} {clue.where_found}. That clue helped point toward the cook and the galley, so the mystery could be solved without a wild guess."),
        QAItem("How did the mystery end?", "It ended with a laugh, because the brocolli had been moved for a sensible reason instead of being stolen."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a schooner?", "A schooner is a sailing boat with tall sails."),
        QAItem("What is brocolli?", "Brocolli is a green vegetable with little tree-like tops. It is often served cooked at meals."),
        QAItem("What does it mean to heed a warning?", "To heed a warning means to listen carefully and pay attention to it."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    parts.extend(sample.prompts)
    parts.append("== story qa ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("== world qa ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams("deck", "seaweed", "check_hatch", "Mina", "girl", "curious"),
    StoryParams("galley", "crumbs", "call_cook", "Eli", "boy", "careful"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A humorous schooner mystery with a brocolli clue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
              and (args.clue is None or c[1] == args.clue)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, clue = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, clue, response, name, gender, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CLUES[params.clue], RESPONSES[params.response],
                 params.child_name, params.child_gender, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
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


ASP_RULES = r"""
valid(S, C) :- setting(S), clue(C).
response_ok(R) :- response(R), sense(R, N), sense_min(M), N >= M.
outcome(solved) :- response_ok(_).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP gate matches Python valid_combos().")
    else:
        print("MISMATCH: ASP gate differs from Python valid_combos().")
        rc = 1
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print("SMOKE TEST FAILED:", e)
        rc = 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
