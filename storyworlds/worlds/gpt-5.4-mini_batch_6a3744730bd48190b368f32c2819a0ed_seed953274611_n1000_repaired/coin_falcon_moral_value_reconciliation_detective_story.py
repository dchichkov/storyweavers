#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/coin_falcon_moral_value_reconciliation_detective_story.py
=========================================================================================

A small detective-style storyworld built from the seed words ``coin`` and
``falcon`` with the features Moral Value and Reconciliation.

Premise
-------
A child detective finds a missing coin, learns that a frightened falcon is the
real reason the coin disappeared, and chooses a fair, kind solution instead of
blaming the wrong suspect. The ending is a reconciliation: people and falcon are
all safer, and the coin is returned.

The world uses physical meters and emotional memes, a small forward-chained
simulation, a reasonableness gate, inline ASP twin rules, and a state-driven
renderer so the story is not just fixed prose with swapped nouns.
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
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    scene: str
    quiet: str
    cover: str
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
class Clue:
    id: str
    label: str
    phrase: str
    where: str
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
class Suspect:
    id: str
    label: str
    type: str
    motives: list[str]
    is_falcon: bool = False
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
class Resolution:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    moral: str
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


def _r_suspicion(world: World) -> list[str]:
    out: list[str] = []
    if world.get("coin").meters["missing"] < THRESHOLD:
        return out
    if world.get("child").memes["doubt"] < THRESHOLD:
        return out
    sig = ("suspicion",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("child").memes["focus"] += 1
    out.append("__suspicion__")
    return out


def _r_truth(world: World) -> list[str]:
    out: list[str] = []
    coin = world.get("coin")
    falcon = world.get("falcon")
    if coin.meters["found"] < THRESHOLD or falcon.meters["safe"] < THRESHOLD:
        return out
    sig = ("truth",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("child").memes["relief"] += 1
    world.get("neighbor").memes["trust"] += 1
    out.append("__truth__")
    return out


CAUSAL_RULES = [
    Rule("suspicion", "social", _r_suspicion),
    Rule("truth", "social", _r_truth),
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


def reasonable_resolutions() -> list[Resolution]:
    return [r for r in RESOLUTIONS.values() if r.sense >= SENSE_MIN]


def valid_combo(place: Place, clue: Clue, suspect: Suspect) -> bool:
    return "detective" in place.tags and clue.label == "coin" and suspect.is_falcon


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, p in PLACES.items():
        for cid, c in CLUES.items():
            for sid, s in SUSPECTS.items():
                if valid_combo(p, c, s):
                    out.append((pid, cid, sid))
    return out


def clue_prediction(world: World, clue: Clue) -> dict:
    sim = world.copy()
    sim.get("coin").meters["missing"] += 1
    sim.get("child").memes["doubt"] += 1
    propagate(sim, narrate=False)
    return {"suspicion": sim.get("child").memes["focus"], "missing": sim.get("coin").meters["missing"]}


def tell(place: Place, clue: Clue, suspect: Suspect, resolution: Resolution,
         child_name: str = "Nina", child_gender: str = "girl",
         neighbor_name: str = "Mr. Reed", neighbor_gender: str = "man") -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="detective"))
    neighbor = world.add(Entity(id="neighbor", kind="character", type=neighbor_gender, label=neighbor_name, role="neighbor"))
    coin = world.add(Entity(id="coin", type="coin", label="coin", tags={"coin"}))
    falcon = world.add(Entity(id="falcon", type="falcon", label="falcon", tags={"falcon"}, attrs={"suspect": suspect.label}))
    world.facts["place"] = place
    world.facts["clue"] = clue
    world.facts["suspect"] = suspect
    world.facts["resolution"] = resolution

    child.memes["doubt"] = 1
    child.meters["attention"] = 1
    world.say(
        f"{child_name} was a small detective in {place.scene}. "
        f"{place.cover} and {place.quiet} made the room feel full of secrets."
    )
    world.say(
        f"Then {child_name} found a {clue.phrase} near {clue.where}. "
        f"It was the kind of clue that made a detective stop and look twice."
    )

    world.para()
    child.memes["doubt"] += 1
    world.say(
        f"{child_name} guessed someone had taken the coin, but the clue did not fit that guess. "
        f"A scratch mark by the window pointed toward a bird instead."
    )
    pred = clue_prediction(world, clue)
    world.facts["prediction"] = pred
    world.say(
        f"{neighbor_name} listened carefully and said, "
        f"\"Let's follow the facts before we blame anybody.\""
    )

    world.para()
    if suspect.is_falcon:
        world.say(
            f"Under the ledge, they found a frightened falcon with a shiny coin beside its nest. "
            f"It had picked up the coin to guard it, not to steal it."
        )
        coin.meters["missing"] = 1
        falcon.meters["safe"] = 1
        coin.meters["found"] = 1
        world.say(
            f"{child_name} spoke softly, backed away, and set a little dish of water near the fence. "
            f"The falcon blinked and stayed calm."
        )
        propagate(world, narrate=False)
        world.say(
            f"{neighbor_name} used a long glove to lift the coin from the ledge, and {child_name} put it back where it belonged."
        )
        world.para()
        body = resolution.text
        world.say(
            f"After that, {neighbor_name} thanked {child_name} for being honest, and {child_name} thanked the falcon for not being hurt."
        )
        world.say(
            f"{resolution.moral}. {child_name} learned that a fair detective should protect the truth, even when the truth is gentler than the first guess."
        )
        world.say(
            f"By the end, the coin shone on the table, the falcon rested safely outside, and the case felt solved the right way."
        )
    else:
        world.say("The bird was not the answer after all, and the case stayed muddy.")
        if resolution.power >= 2:
            world.say("Still, the detective kept looking until the real owner came forward.")
        else:
            world.say("The wrong guess left everyone uneasy.")
    world.facts.update(
        child=child, neighbor=neighbor, coin=coin, falcon=falcon,
        outcome="reconciled" if suspect.is_falcon else "unclear",
    )
    return world


PLACES = {
    "museum": Place(id="museum", scene="the little coin room at the museum", quiet="The hall was quiet", cover="Glass cases lined the walls", tags={"detective"}),
    "attic": Place(id="attic", scene="a dusty attic office", quiet="The boards creaked softly", cover="Old boxes leaned in corners", tags={"detective"}),
    "station": Place(id="station", scene="the back room of the little station", quiet="Rain tapped the window", cover="A lamp made a small pool of light", tags={"detective"}),
}

CLUES = {
    "coin": Clue(id="coin", label="coin", phrase="small silver coin", where="the windowsill", tags={"coin"}),
    "feather": Clue(id="feather", label="feather", phrase="gray feather", where="the open latch", tags={"falcon"}),
    "scrape": Clue(id="scrape", label="scrape", phrase="thin scrape mark", where="the ledge", tags={"falcon"}),
}

SUSPECTS = {
    "falcon": Suspect(id="falcon", label="falcon", type="falcon", motives=["nesting", "shiny things"], is_falcon=True, tags={"falcon"}),
    "thief": Suspect(id="thief", label="night thief", type="person", motives=["hiding", "greed"], is_falcon=False, tags={"crime"}),
}

RESOLUTIONS = {
    "gentle": Resolution(id="gentle", sense=3, power=3, text="carefully returned the coin to its owner", fail="could not make sense of the clue", moral="Kindness matters when facts are still new"),
    "glove": Resolution(id="glove", sense=3, power=3, text="lifted the coin with a long glove and carried it home safely", fail="could not reach the coin in time", moral="A careful hand can solve a hard case"),
    "blame": Resolution(id="blame", sense=1, power=1, text="tried to blame the bird too quickly", fail="blamed the wrong suspect and felt sorry later", moral="It is better to ask than accuse"),
}

GIRL_NAMES = ["Nina", "Maya", "Iris", "Lena"]
BOY_NAMES = ["Owen", "Theo", "Eli", "Noah"]
NEIGHBOR_NAMES = ["Mr. Reed", "Ms. Bell", "Dr. Lane"]


@dataclass
class StoryParams:
    place: str
    clue: str
    suspect: str
    resolution: str
    child_name: str
    child_gender: str
    neighbor_name: str
    neighbor_gender: str
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
    ap = argparse.ArgumentParser(description="Detective storyworld with coin, falcon, moral value, and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--neighbor")
    ap.add_argument("--neighbor-gender", choices=["woman", "man"])
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
    if args.clue and args.clue != "coin":
        raise StoryError("This detective story needs the coin clue so the case can actually be solved.")
    if args.suspect and args.suspect != "falcon":
        raise StoryError("This storyworld only supports the falcon suspect; the moral turn depends on it.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.suspect is None or c[2] == args.suspect)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, suspect = rng.choice(sorted(combos))
    resolution = args.resolution or rng.choice(sorted(r.id for r in reasonable_resolutions()))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    neighbor_gender = args.neighbor_gender or rng.choice(["woman", "man"])
    neighbor_name = args.neighbor or rng.choice(NEIGHBOR_NAMES)
    return StoryParams(place=place, clue=clue, suspect=suspect, resolution=resolution,
                       child_name=child_name, child_gender=gender,
                       neighbor_name=neighbor_name, neighbor_gender=neighbor_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a detective story for a 3-to-5-year-old that includes the words "coin" and "falcon".',
        f"Tell a gentle mystery where {f['child'].label} follows clues, learns the falcon is not a villain, and ends with a fair reconciliation.",
        f"Write a story with a moral lesson about not blaming too quickly, using a coin, a falcon, and a kind detective.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    neighbor = f["neighbor"]
    falcon = f["falcon"]
    coin = f["coin"]
    resolution = f["resolution"]
    items = [
        QAItem(
            question="What kind of story is this?",
            answer=f"It is a detective story about {child.label} following clues and solving a small mystery with a coin and a falcon. The case matters because the first guess is not the right one."
        ),
        QAItem(
            question="What did the child learn about the falcon?",
            answer="The falcon was not a thief. It had the coin near its nest and was acting from instinct, so the detective needed patience instead of blame."
        ),
        QAItem(
            question="How did the story show reconciliation?",
            answer=f"{child.label} and {neighbor.label} chose a calm, fair solution and gave the coin back without hurting the falcon. That turned a misunderstanding into a peaceful ending."
        ),
    ]
    if f["outcome"] == "reconciled":
        items.append(
            QAItem(
                question="What was the moral of the story?",
                answer=f"{resolution.moral}. The detective proved that listening and checking facts can mend a problem better than accusing too fast."
            )
        )
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a coin?",
            answer="A coin is a small round piece of money. People can use it to pay for little things or keep it as change."
        ),
        QAItem(
            question="What is a falcon?",
            answer="A falcon is a bird of prey with sharp eyes and fast wings. It can fly very quickly and likes high places."
        ),
        QAItem(
            question="Why should a detective check the facts?",
            answer="A detective checks the facts so the wrong person does not get blamed. Careful looking helps solve the real problem."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== Story QA =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        if e.label:
            parts.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("detective_place", pid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
        if cid == "coin":
            lines.append(asp.fact("coin_clue", cid))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        if s.is_falcon:
            lines.append(asp.fact("falcon_suspect", sid))
    for rid, r in RESOLUTIONS.items():
        lines.append(asp.fact("resolution", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,C,S) :- detective_place(P), coin_clue(C), falcon_suspect(S).
reasonable(R) :- resolution(R), sense(R,S), sense_min(M), S >= M.
outcome(reconciled) :- valid(_,_,_), reasonable(_).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_reasonable() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/1."))
    return sorted(r for (r,) in asp.atoms(model, "reasonable"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid combos differ.")
        rc = 1
    if set(asp_reasonable()) != {r.id for r in reasonable_resolutions()}:
        print("MISMATCH: ASP and Python reasonable resolutions differ.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        _ = sample.story
        _ = sample.to_json()
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.clue not in CLUES or params.suspect not in SUSPECTS or params.resolution not in RESOLUTIONS:
        raise StoryError("Invalid parameters for this storyworld.")
    if params.clue != "coin" or params.suspect != "falcon":
        raise StoryError("This storyworld needs the coin clue and the falcon suspect.")
    world = tell(PLACES[params.place], CLUES[params.clue], SUSPECTS[params.suspect], RESOLUTIONS[params.resolution], params.child_name, params.child_gender, params.neighbor_name, params.neighbor_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(place="museum", clue="coin", suspect="falcon", resolution="gentle", child_name="Nina", child_gender="girl", neighbor_name="Mr. Reed", neighbor_gender="man"),
    StoryParams(place="attic", clue="coin", suspect="falcon", resolution="glove", child_name="Owen", child_gender="boy", neighbor_name="Ms. Bell", neighbor_gender="woman"),
    StoryParams(place="station", clue="coin", suspect="falcon", resolution="gentle", child_name="Maya", child_gender="girl", neighbor_name="Dr. Lane", neighbor_gender="woman"),
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
        print(asp_program("#show valid/3.\n#show reasonable/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, clue, suspect) combos:")
        for p, c, s in combos:
            print(f"  {p:8} {c:6} {s}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
