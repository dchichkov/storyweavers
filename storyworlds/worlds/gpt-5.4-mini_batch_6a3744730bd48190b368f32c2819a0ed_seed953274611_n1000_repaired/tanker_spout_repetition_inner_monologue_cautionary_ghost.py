#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tanker_spout_repetition_inner_monologue_cautionary_ghost.py
===========================================================================================

A tiny standalone storyworld with a ghost-story mood.

Premise:
- A child and a cautious grown-up stand on a foggy dock.
- A tanker looms in the mist.
- A little spout on the tanker keeps hissing and dripping.
- The child is tempted to go closer, but the inner monologue and the cautionary
  warning keep the story from becoming a bad idea.

The world is intentionally small and state-driven:
- physical meters: fog, wet, danger, distance, light
- emotional memes: fear, caution, relief, curiosity, resolve

The prose is built from the simulated state, not from a frozen paragraph.
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
    attrs: dict = field(default_factory=dict)
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
    mood: str
    weather: str
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
class Hazard:
    id: str
    label: str
    phrase: str
    whisper: str
    repeat: str
    risky: bool = True
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
class Response:
    id: str
    sense: int
    text: str
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


def _r_danger(world: World) -> list[str]:
    out: list[str] = []
    tanker = world.entities.get("tanker")
    if tanker and tanker.meters["looming"] >= THRESHOLD:
        sig = ("danger",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        for e in list(world.entities.values()):
            if e.kind == "character":
                e.memes["fear"] += 1
        world.get("dock").meters["danger"] += 1
        out.append("__danger__")
    return out


CAUSAL_RULES = [Rule("danger", _r_danger)]


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


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for hid, h in HAZARDS.items():
            if setting.id == "fog_dock" and h.risky:
                combos.append((sid, hid))
    return combos


@dataclass
class StoryParams:
    setting: str
    hazard: str
    response: str
    child_name: str
    child_gender: str
    adult_name: str
    adult_gender: str
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


def predict(world: World) -> dict:
    sim = world.copy()
    sim.get("tanker").meters["looming"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("dock").meters["danger"],
        "fear": sim.get("child").memes["fear"],
    }


def open_scene(world: World, child: Entity, adult: Entity, setting: Setting, hazard: Hazard) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"In {setting.place}, the fog lay thick and soft, and the night made every "
        f"sound seem closer than it was. A tanker waited at the dock, and a small "
        f"spout on its side hissed into the dark."
    )
    world.say(
        f"{child.id} stared at the tanker and thought, "
        f'"{hazard.repeat} {hazard.repeat.lower()}... it sounds like the ship is whispering."'
    )


def inner_monologue(world: World, child: Entity, hazard: Hazard) -> None:
    child.memes["resolve"] += 1
    world.say(
        f"In {child.id}'s head, the thought came again and again: "
        f'"Maybe I should go closer. Maybe I should not. Maybe the tanker is only "
        f"quiet because it is old."'
    )


def warn(world: World, adult: Entity, child: Entity, hazard: Hazard) -> None:
    adult.memes["caution"] += 1
    pred = predict(world)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_fear"] = pred["fear"]
    world.say(
        f'{adult.id} put out a hand. "{child.id}, stay back," {adult.pronoun()} said. '
        f'"That spout can spray cold water, and slippery decks are trouble in fog."'
    )
    world.say(
        f'The warning felt steady, like a light tied to a rope. "{hazard.label} '
        f'is not a toy," {adult.id} said again.'
    )


def approach(world: World, child: Entity, hazard: Hazard) -> None:
    child.memes["fear"] += 1
    world.say(
        f'{child.id} took one small step, then stopped. '
        f'One step. Then another thought. Then another. '
        f'"Maybe not," {child.id} whispered to {child.pronoun("object")}self.'
    )


def heed(world: World, child: Entity, adult: Entity, hazard: Hazard) -> None:
    child.memes["caution"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} looked at the tanker, looked at the spout, and looked back at "
        f"{adult.id}. The fog kept listening, but {child.id} chose to listen too."
    )
    world.say(
        f'"I can wait," {child.id} said. "The tanker can be scary from far away."'
    )


def resolve(world: World, child: Entity, adult: Entity, hazard: Hazard, response: Response) -> None:
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1)
    child.memes["relief"] += 1
    adult.memes["relief"] += 1
    world.say(
        f"{adult.id} smiled and switched on a lantern. The yellow light made the fog "
        f"look thinner at once."
    )
    body = response.text
    world.say(
        f"{adult.id} said, 'Good listening. We do {hazard.label} safely: we keep back, "
        f"use the light, and let the grown-up parts do the worrying.' Then {adult.id} {body}."
    )
    world.say(
        f"The tanker stayed in the mist, and the spout kept dripping, but it was only "
        f"a quiet sound now. {child.id} stood beside {adult.id} with warm light in "
        f"{child.pronoun('possessive')} hands and no need to be brave in the wrong way."
    )


def tell(setting: Setting, hazard: Hazard, response: Response, child_name: str,
         child_gender: str, adult_name: str, adult_gender: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="adult"))
    dock = world.add(Entity(id="dock", type="place", label="the dock"))
    tanker = world.add(Entity(id="tanker", type="thing", label="the tanker", role="object"))
    spout = world.add(Entity(id="spout", type="thing", label="the spout", role="object"))

    world.facts["child"] = child
    world.facts["adult"] = adult
    world.facts["setting"] = setting
    world.facts["hazard"] = hazard
    world.facts["response"] = response

    open_scene(world, child, adult, setting, hazard)
    world.para()
    inner_monologue(world, child, hazard)
    warn(world, adult, child, hazard)

    tanker.meters["looming"] += 1
    spout.meters["drip"] += 1
    propagate(world, narrate=False)

    world.para()
    approach(world, child, hazard)
    heed(world, child, adult, hazard)

    world.para()
    resolve(world, child, adult, hazard, response)
    world.facts["outcome"] = "safe"
    return world


SETTINGS = {
    "fog_dock": Setting(
        id="fog_dock",
        place="the foggy dock",
        mood="ghostly",
        weather="fog",
        tags={"ghost", "dock", "fog"},
    ),
}

HAZARDS = {
    "tanker_spout": Hazard(
        id="tanker_spout",
        label="the tanker spout",
        phrase="a tanker spout in the fog",
        whisper="hiss",
        repeat="hush",
        risky=True,
        tags={"tanker", "spout", "ghost", "cautionary"},
    ),
}

RESPONSES = {
    "lantern": Response(
        id="lantern",
        sense=3,
        text="held the lantern up and kept everyone on the safe side of the rope",
        qa_text="held the lantern up and kept everyone safely behind the rope",
        tags={"light", "safe"},
    ),
    "wait": Response(
        id="wait",
        sense=2,
        text="waited for the harbor bell and the day crew to come in",
        qa_text="waited for the harbor bell and the day crew to come in",
        tags={"wait", "safe"},
    ),
    "call_help": Response(
        id="call_help",
        sense=3,
        text="called the harbor worker and asked for help right away",
        qa_text="called the harbor worker and asked for help right away",
        tags={"help", "safe"},
    ),
}

NAMES_GIRL = ["Mina", "Ivy", "Nora", "Elsie", "June"]
NAMES_BOY = ["Finn", "Owen", "Leo", "Miles", "Theo"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost-story storyworld about a tanker and a spout.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-gender", choices=["woman", "man", "girl", "boy", "mother", "father"])
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("The response is too weak for a cautious ghost story.")
    setting = args.setting or rng.choice(list(SETTINGS))
    hazard = args.hazard or rng.choice(list(HAZARDS))
    response = args.response or rng.choice([r.id for r in sensible_responses()])
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    adult_gender = args.adult_gender or rng.choice(["mother", "father"])
    child = args.child or rng.choice(NAMES_GIRL if child_gender == "girl" else NAMES_BOY)
    adult = args.adult or rng.choice(["Ms. Reed", "Mr. Hale", "Aunt Jo", "Uncle Ben"])
    return StoryParams(
        setting=setting,
        hazard=hazard,
        response=response,
        child_name=child,
        child_gender=child_gender,
        adult_name=adult,
        adult_gender=adult_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.hazard not in HAZARDS or params.response not in RESPONSES:
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], HAZARDS[params.hazard], RESPONSES[params.response],
                 params.child_name, params.child_gender, params.adult_name, params.adult_gender)
    prompts = [
        "Write a ghost-story scene on a foggy dock with a tanker and a spout.",
        "Tell a cautionary story where a child hears a spooky tanker and listens to a wiser adult.",
        "Write a story with repetition and inner monologue that ends safely at the dock.",
    ]
    story_qa = [
        QAItem(
            question="Why did the child stay back?",
            answer="The child stayed back because the adult warned that the tanker spout could spray cold water and make the deck slippery in the fog. The child also heard the warning again in their own head and chose the safer way."
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The fog was still there, but the child was no longer trying to creep closer. A lantern came on, the rope line stayed in place, and the tanker became something to watch from a safe distance."
        ),
        QAItem(
            question="How did the adult help?",
            answer="The adult gave a clear warning, turned on a lantern, and kept the child behind the rope. That made the scary dock feel manageable instead of dangerous."
        ),
    ]
    world_qa = [
        QAItem(
            question="What is fog?",
            answer="Fog is a cloud that sits low to the ground and makes faraway things look ghostly and dim."
        ),
        QAItem(
            question="Why can a wet deck be dangerous?",
            answer="A wet deck can be dangerous because shoes can slip on it, especially when you cannot see well."
        ),
        QAItem(
            question="What does a lantern do?",
            answer="A lantern makes safe light without a flame that needs to be held close to something risky."
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
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


ASP_RULES = r"""
valid(setting_fog_dock, tanker_spout, response) :- response(response).
safe(response) :- response(response), sense(response,S), sense_min(M), S >= M.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "fog_dock"), asp.fact("hazard", "tanker_spout")]
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, resp.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show safe/1."))
    return sorted(x for (x,) in asp.atoms(model, "safe"))


def asp_verify() -> int:
    rc = 0
    py = {(s, h, r) for s, h in valid_combos() for r in RESPONSES if RESPONSES[r].sense >= SENSE_MIN}
    cl = set(asp_valid_combos())
    if cl:
        print(f"OK: ASP returned {len(cl)} valid combinations.")
    else:
        rc = 1
        print("MISMATCH: ASP returned no combinations.")
    if set(asp_sensible()) == {r for r in RESPONSES if RESPONSES[r].sense >= SENSE_MIN}:
        print("OK: ASP sensible responses match.")
    else:
        rc = 1
        print("MISMATCH: ASP sensible responses differ.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, hazard=None, response=None, child=None, child_gender=None, adult=None, adult_gender=None), random.Random(0)))
        assert sample.story
        print("OK: default generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


CURATED = [
    StoryParams(
        setting="fog_dock",
        hazard="tanker_spout",
        response="lantern",
        child_name="Mina",
        child_gender="girl",
        adult_name="Ms. Reed",
        adult_gender="mother",
    ),
    StoryParams(
        setting="fog_dock",
        hazard="tanker_spout",
        response="call_help",
        child_name="Finn",
        child_gender="boy",
        adult_name="Mr. Hale",
        adult_gender="father",
    ),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show safe/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}")
        for item in asp_valid_combos():
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} and {p.adult_name}: {p.hazard} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
