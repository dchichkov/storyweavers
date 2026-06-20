#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/test_police_shake_dim_cautionary_folk_tale.py
=============================================================================

A small standalone storyworld for a cautionary folk-tale-style tale about a
child, a village light, and a worried police officer. The seed words are woven
into the domain: **test**, **police**, and **shake-dim**.

Premise
-------
In a little village, a child finds a curious "shake-dim" lantern trick and
wants to test it. The police officer warns that the village path will grow dark,
a bad thing on a night when people are walking home. If the child goes ahead,
the lantern dims, the path becomes unsafe, and the police officer must guide
everyone back to the lamp post and restore the light.

The simulation is intentionally small:
- typed entities with meters and memes
- a forward-chained causal rule for dim light and worry
- a reasonableness gate that only allows stories where the light-tampering really
  matters
- a calm cautionary ending that proves what changed

This is a complete standalone script following the Storyweavers contract.
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
BRAVERY_INIT = 5.5


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "police"}
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
class Signal:
    id: str
    label: str
    phrase: str
    action: str
    makes_dim: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Place:
    id: str
    label: str
    dark_spot: str
    path: str
    wind: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
            value = defaultdict(float)
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


def _r_dim(world: World) -> list[str]:
    out: list[str] = []
    lamp = world.entities.get("lamp")
    if not lamp or lamp.meters["dimmed"] < THRESHOLD:
        return out
    sig = ("dim",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in list(world.entities.values()):
        if e.role in {"child", "police"}:
            e.memes["worry"] += 1
    out.append("__dim__")
    return out


CAUSAL_RULES = [Rule("dim", "light", _r_dim)]


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


def hazard_at_risk(signal: Signal, place: Place) -> bool:
    return signal.makes_dim and "dark_path" in place.tags


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def fire_severity(place: Place, delay: int) -> int:
    return 1 + delay


def is_contained(response: Response, place: Place, delay: int) -> bool:
    return response.power >= fire_severity(place, delay)


def predict_dim(world: World, signal_id: str) -> dict:
    sim = world.copy()
    _do_signal(sim, sim.get(signal_id), narrate=False)
    return {
        "dimmed": sim.get("lamp").meters["dimmed"] >= THRESHOLD,
        "worry": sim.get("police").memes["worry"],
    }


def _do_signal(world: World, signal: Entity, narrate: bool = True) -> None:
    lamp = world.get("lamp")
    lamp.meters["dimmed"] += 1
    lamp.meters["swayed"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, child: Entity, guide: Entity, place: Place, signal: Signal) -> None:
    child.memes["curiosity"] += 1
    guide.memes["duty"] += 1
    world.say(
        f"Long ago, in a little village by the lane, {child.id} and {guide.label} "
        f"stood beside the old lamp post. {place.label} had a {place.dark_spot} "
        f"and a {place.path} that curled home under the trees."
    )
    world.say(
        f'"Let us not go wandering too late," said {guide.label}. '
        f'"The night wind is sharp, and the path should stay bright."'
    )


def tempt(world: World, child: Entity, signal: Signal) -> None:
    child.memes["bravery"] += 1
    world.say(
        f"But {child.id} found a curious {signal.phrase} and wanted to test it. "
        f'"If I {signal.action}, will the light play a trick?" {child.id} asked.'
    )
    world.say("For a moment, the idea seemed small and harmless.")


def warn(world: World, guide: Entity, child: Entity, place: Place, signal: Signal) -> None:
    pred = predict_dim(world, "signal")
    guide.memes["caution"] += 1
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'"Do not do that," said {guide.label}. "If you {signal.action}, the '
        f'lampshine will go soft, and {place.path} will grow hard to see."'
    )


def defy(world: World, child: Entity, signal: Signal) -> None:
    child.memes["defiance"] += 1
    world.say(f'{child.id} shook-dim the lantern anyway, and the village held its breath.')


def alarm(world: World, guide: Entity, child: Entity, place: Place) -> None:
    world.say(f'"{child.id}!" cried {guide.label}. "The {place.path} is dim!"')
    world.say(f'Then the police came at once, boots sounding on the stone.')


def rescue(world: World, police: Entity, response: Response, place: Place) -> None:
    body = response.text.replace("{place}", place.label)
    world.get("lamp").meters["dimmed"] = 0.0
    world.say(f"{police.label_word.capitalize()} {body}.")
    world.say(f"At once, the lamp glowed steady again, and the lane looked friendly.")


def lesson(world: World, police: Entity, child: Entity, guide: Entity, signal: Signal) -> None:
    for e in (child, guide):
        e.memes["relief"] += 1
        e.memes["lesson"] += 1
    world.say(
        f'{police.label_word.capitalize()} knelt and spoke kindly. '
        f'"A light is for everyone. Never test it by shaking it dim. '
        f'Call a grown-up if something seems wrong."'
    )
    world.say(f'"We will remember," whispered {child.id} and {guide.id}.')
    world.say(
        f"After that, {child.id} kept the curious hands to {child.id}'s pockets, "
        f"and the lamp post shone over the path like a good moon."
    )


def rescue_fail(world: World, police: Entity, response: Response, place: Place) -> None:
    world.say(
        f"{police.label_word.capitalize()} tried to help, but {response.fail.replace('{place}', place.label)}."
    )
    world.say(
        f"The dark spread over {place.path}, and everyone hurried to the hall before the night got too deep."
    )


def grim_end(world: World, police: Entity, child: Entity, guide: Entity) -> None:
    world.say(
        f"{police.label_word.capitalize()} led them safely home, but the village folk knew "
        f"they had learned a hard lesson about what not to touch."
    )
    world.say(
        f"From then on, {child.id} never tested a public lamp again, and the road stayed for walking, not for tricks."
    )


def tell(place: Place, signal: Signal, response: Response,
         child_name: str = "Mina", child_gender: str = "girl",
         guide_name: str = "Officer Reed", guide_gender: str = "police",
         delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    guide = world.add(Entity(id=guide_name, kind="character", type=guide_gender, role="police", label="the police officer"))
    lamp = world.add(Entity(id="lamp", kind="thing", type="thing", label="the lamp post"))
    world.facts["place"] = place
    world.facts["signal"] = signal
    world.facts["response"] = response

    setup(world, child, guide, place, signal)
    world.para()
    tempt(world, child, signal)
    warn(world, guide, child, place, signal)

    world.para()
    defy(world, child, signal)
    _do_signal(world, lamp, narrate=True)
    alarm(world, guide, child, place)

    contained = is_contained(response, place, delay)
    world.para()
    if contained:
        rescue(world, guide, response, place)
        lesson(world, guide, child, guide, signal)
    else:
        rescue_fail(world, guide, response, place)
        grim_end(world, guide, child, guide)

    world.facts.update(
        child=child, guide=guide, lamp=lamp, outcome="contained" if contained else "burned",
    )
    return world


PLACES = {
    "village": Place("village", "the village green", "a shadowy well", "the lane", "cold", {"dark_path"}),
    "market": Place("market", "the market square", "a black archway", "the road home", "windy", {"dark_path"}),
    "bridge": Place("bridge", "the stone bridge", "the riverbank", "the path by the river", "misty", {"dark_path"}),
}

SIGNALS = {
    "shake-dim": Signal("shake-dim", "shake-dim", "shake-dim charm", "shake-dim the lantern", True, {"shake", "dim"}),
    "twist-dim": Signal("twist-dim", "shake-dim", "shake-dim switch", "twist the switch until it shakes-dims", True, {"shake", "dim"}),
}

RESPONSES = {
    "steadying": Response("steadying", 3, 3,
                          "set the lamp straight and mended the wick so it shone steady",
                          "could not mend the wick before the dark swallowed the lane",
                          "set the lamp straight and made it shine steady", {"lamp"}),
    "covering": Response("covering", 2, 2,
                         "covered the flame with a glass hood and lit it safe again",
                         "could not reach the hood before the lantern went too dim",
                         "covered the flame and lit it safe again", {"lamp"}),
    "weep": Response("weep", 1, 1,
                     "stood and wept over the lamp",
                     "stood and wept while the lane grew darker",
                     "stood and wept", {"lamp"}),
}



@dataclass
class StoryParams:
    place: str
    signal: str
    response: str
    child_name: str
    child_gender: str
    guide_name: str
    guide_gender: str
    delay: int = 0
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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

CURATED = [
    __import__("types").SimpleNamespace(place="village", signal="shake-dim", response="steadying", delay=0),
    __import__("types").SimpleNamespace(place="market", signal="twist-dim", response="covering", delay=0),
    __import__("types").SimpleNamespace(place="bridge", signal="shake-dim", response="steadying", delay=1),
]



GIRL_NAMES = ["Mina", "Lily", "Nora", "Asha", "Pia"]
BOY_NAMES = ["Tomas", "Jory", "Eli", "Bram", "Oren"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for sid, signal in SIGNALS.items():
            if hazard_at_risk(signal, place):
                for rid, resp in RESPONSES.items():
                    if resp.sense >= SENSE_MIN:
                        combos.append((pid, sid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a cautionary folk tale that includes the words "test", "police", and "shake-dim".',
        f"Tell a small village story where {f['child'].id} wants to test a shake-dim trick on the lamp post, but the police warn against it.",
        f"Write a folk-tale-style warning about a child, a police officer, and a lantern that should never be shaken dim.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, guide, place, signal, response = f["child"], f["guide"], f["place"], f["signal"], f["response"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and the police officer who watches over the lane. The tale is a cautionary one, so the warning matters as much as the trick."),
        ("What did the child want to do?",
         f"{child.id} wanted to test the {signal.label} on the lamp post. That was risky because it could make the village path grow dim."),
        ("Why did the police officer warn the child?",
         f"The police officer warned {child.id} because the light could be shaken dim and the road home would be harder to see. In a folk tale, that kind of small mistake can become a bigger trouble very fast."),
    ]
    if f["outcome"] == "contained":
        qa.append((
            "How did the police officer fix the problem?",
            f"The police officer {response.qa_text}. That brought the light back and kept the lane safe for everyone walking home."
        ))
        qa.append((
            "How did the story end?",
            f"It ended safely, with the lamp shining steady over the path. {child.id} learned to leave the village light alone and call a grown-up instead."
        ))
    else:
        qa.append((
            "How did the police officer try to fix the problem?",
            f"The police officer {response.fail.replace('{place}', place.label)}. The lane stayed dark, so everyone had to hurry home."
        ))
        qa.append((
            "What did the child learn?",
            f"{child.id} learned not to test the lamp with a shake-dim trick. The lesson was hard, but it kept the village folk safer the next time."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does a police officer do?",
         "A police officer helps keep people safe, watches for trouble, and tells others what to do in an emergency."),
        ("Why can a dim path be dangerous?",
         "A dim path is hard to see, so people can trip or wander the wrong way. Bright light helps them walk safely."),
        ("What should you do if you want to test something strange in the dark?",
         "Stop and ask a grown-up first. That is the safest way to test an idea."),
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
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(S,P) :- signal(S), place(P), dark_path(P), makes_dim(S).
valid(P,S) :- hazard(S,P).
contained(R,P) :- response(R), sense(R, Sen), sense_min(M), Sen >= M, place(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for t in sorted(place.tags):
            lines.append(asp.fact(t, pid))
    for sid, s in SIGNALS.items():
        lines.append(asp.fact("signal", sid))
        if s.makes_dim:
            lines.append(asp.fact("makes_dim", sid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, signal=None, response=None, seed=None, all=False, trace=False, qa=False, json=False, asp=False, verify=False, show_asp=False), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary folk tale: test, police, shake-dim.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--signal", choices=SIGNALS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--guide")
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


def explain_rejection(signal: Signal, place: Place) -> str:
    return f"(No story: {signal.label} would not matter in {place.label}; pick a dark-path place.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.signal:
        if not hazard_at_risk(SIGNALS[args.signal], PLACES[args.place]):
            raise StoryError(explain_rejection(SIGNALS[args.signal], PLACES[args.place]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.signal is None or c[1] == args.signal)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, signal = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    child_gender = rng.choice(["girl", "boy"])
    child_name = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    guide_name = args.guide or "Officer Reed"
    return StoryParams(place, signal, response, child_name, child_gender, guide_name, "police")


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], SIGNALS[params.signal], RESPONSES[params.response],
                 params.child_name, params.child_gender, params.guide_name, params.guide_gender, params.delay)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:\n")
        for p, s in asp_valid_combos():
            print(f"  {p:10} {s}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("village", "shake-dim", "steadying", "Mina", "girl", "Officer Reed", "police", 0),
            StoryParams("market", "twist-dim", "covering", "Tomas", "boy", "Officer Reed", "police", 0),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
