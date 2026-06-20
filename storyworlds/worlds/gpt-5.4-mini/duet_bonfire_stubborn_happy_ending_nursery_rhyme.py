#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/duet_bonfire_stubborn_happy_ending_nursery_rhyme.py
===================================================================================

A small standalone storyworld for a nursery-rhyme-style tale about a duet, a
bonfire, and a stubborn child who learns the safer, brighter way to sing.

Domain sketch
-------------
Two children make a little duet by the garden, but one of them wants to keep a
bonfire going after a grown-up says it is time to stop. The world models a
simple physical state: the fire's heat, the yard's safety, the children's
feelings, and whether the music keeps going or turns into a calm happy ending.

The story always stays child-facing and concrete:
- setup: a cozy rhyme, a song, and a warm bonfire
- tension: one child is stubborn and wants to stay
- turn: the other child calls for help and the grown-up gives a safer choice
- ending: the duet continues with lanterns, and the bonfire is safely ended

It includes the seed words duet, bonfire, and stubborn, with a nursery-rhyme
feel and a happy ending.
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
    rhyme: str
    stage: str
    quiet_spot: str

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
class Act:
    id: str
    song_line: str
    want_line: str
    stubborn_line: str
    safe_line: str
    sings: str
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
class Fire:
    id: str
    label: str
    flame_line: str
    danger_line: str
    safe_out: str
    heat: int
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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


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


def _r_scared(world: World) -> list[str]:
    out: list[str] = []
    if "fire" not in world.entities:
        return out
    fire = world.get("fire")
    if fire.meters["burning"] < THRESHOLD:
        return out
    for e in world.characters():
        sig = ("scared", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["fear"] += 1
        out.append("__fear__")
    return out


CAUSAL_RULES = [Rule("scared", "social", _r_scared)]


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


def fire_at_risk(fire: Fire) -> bool:
    return True


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def fire_severity(fire: Fire, delay: int) -> int:
    return fire.heat + delay


def is_contained(response: Response, fire: Fire, delay: int) -> bool:
    return response.power >= fire_severity(fire, delay)


def _do_fire(world: World, narrate: bool = True) -> None:
    world.get("fire").meters["burning"] += 1
    world.get("fire").meters["glow"] += 1
    propagate(world, narrate=narrate)


def predict_fire(world: World) -> dict:
    sim = world.copy()
    _do_fire(sim, narrate=False)
    return {
        "burning": sim.get("fire").meters["burning"] >= THRESHOLD,
        "fear": sum(e.memes["fear"] for e in sim.characters()),
    }


def intro(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"At {setting.place}, by a little bright {setting.stage}, {a.id} and {b.id} sang a duet. "
        f"{setting.rhyme}"
    )


def bonfire_glow(world: World, fire: Fire, setting: Setting, a: Entity, b: Entity) -> None:
    world.say(
        f"Near the {setting.quiet_spot}, the {fire.label} gave off a warm glow. "
        f"{fire.flame_line}"
    )
    world.say(f"{a.id} clapped along in time, and {b.id} kept the tune nice and neat.")


def want_more(world: World, stubborn: Entity, fire: Fire) -> None:
    stubborn.memes["stubborn"] += 1
    world.say(
        f'"{fire.label} can stay!" said {stubborn.id}, stubborn as a small red drum. '
        f"{stubborn.pronoun().capitalize()} wanted one more chorus by the fire."
    )


def warn(world: World, helper: Entity, stubborn: Entity, fire: Fire) -> None:
    pred = predict_fire(world)
    helper.memes["care"] += 1
    world.facts["predicted_fear"] = pred["fear"]
    world.say(
        f'{helper.id} frowned a little and sang, "The {fire.label} is hot, '
        f"and sparks can jump and roam. Let's call a grown-up and carry the song back home."
    )


def call_grownup(world: World, grownup: Entity, fire: Fire) -> None:
    world.say(f'"{grownup.label_word.capitalize()}!" the children called, and footsteps came quick as rain.')
    world.say(f"{grownup.label_word.capitalize()} knelt down and nodded at the safe choice they had made.")


def calm_turn(world: World, grownup: Entity, response: Response, fire: Fire) -> None:
    world.say(
        f"In a flash, {grownup.pronoun()} {response.text.replace('{fire}', fire.label)}."
    )
    world.say(f"The hot little {fire.label} dimmed and went out, leaving only warm ashes and dusk.")


def happy_finish(world: World, a: Entity, b: Entity, setting: Setting, fire: Fire) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    a.memes["fear"] = 0.0
    b.memes["fear"] = 0.0
    world.say(
        f"Then {a.id} and {b.id} picked up their duet again by lantern light, "
        f"soft and merry beside the {setting.quiet_spot}."
    )
    world.say(
        f"The bonfire was safely done, the night was calm, and the rhyme ended with smiles all around."
    )


def burn_fail(world: World, grownup: Entity, response: Response, fire: Fire) -> None:
    world.say(f"In a flash, {grownup.pronoun()} {response.fail.replace('{fire}', fire.label)}.")
    world.say("The flames got too tall, so everyone hurried away, safe but sad.")


def sad_but_safe(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    world.say(
        f"They left the {setting.quiet_spot} behind and promised to sing together again another day."
    )


def tell(setting: Setting, act: Act, fire: Fire, response: Response,
         singer_a: str = "Nia", singer_b: str = "Bo",
         a_type: str = "girl", b_type: str = "boy",
         grownup_type: str = "mother", stubborn_name: str = "Bo",
         delay: int = 0) -> World:
    world = World()
    a = world.add(Entity(id=singer_a, kind="character", type=a_type, role="singer"))
    b = world.add(Entity(id=singer_b, kind="character", type=b_type, role="stubborn"))
    grownup = world.add(Entity(id="Grownup", kind="character", type=grownup_type, label="the grown-up"))
    fire_ent = world.add(Entity(id="fire", type="thing", label=fire.label))
    fire_ent.meters["burning"] = 0.0

    intro(world, a, b, setting)
    world.para()
    bonfire_glow(world, fire, setting, a, b)
    want_more(world, b if stubborn_name == b.id else a, fire)
    warn(world, a if stubborn_name == b.id else b, b if stubborn_name == b.id else a, fire)
    world.para()
    call_grownup(world, grownup, fire)
    _do_fire(world, narrate=False)
    if is_contained(response, fire, delay):
        calm_turn(world, grownup, response, fire)
        happy_finish(world, a, b, setting, fire)
        outcome = "contained"
    else:
        burn_fail(world, grownup, response, fire)
        sad_but_safe(world, a, b, setting)
        outcome = "burned"
    world.facts.update(a=a, b=b, grownup=grownup, setting=setting, act=act, fire=fire,
                       response=response, delay=delay, outcome=outcome, stubborn=b)
    return world


SETTINGS = {
    "garden": Setting("garden", "the garden", "The daisies nodded, the crickets chimed, and evening folded like a quilt.", "little stone path", "rosebush"),
    "meadow": Setting("meadow", "the meadow", "The grass was green, the bees were slow, and the sky was a lullaby.", "soft hill", "tall grass"),
    "backyard": Setting("backyard", "the backyard", "The fence stood still, the moon hung high, and the air felt sweet and mild.", "brick path", "apple tree"),
}

ACTS = {
    "duet": Act("duet", "sing a duet", "keep singing the duet", "keep the duet going", "sing the duet again by lantern light", "singing a duet", tags={"duet", "song"}),
}

FIRES = {
    "bonfire": Fire("bonfire", "bonfire", "The bonfire flickered and made the shadows dance like kittens.", "A bonfire can pop and sparkle if it gets too lively.", "The bonfire was put out with care.", 2, tags={"bonfire", "fire"}),
}

RESPONSES = {
    "water": Response("water", 2, 3, "poured water over the {fire} until the sparks stopped dancing", "threw a little water at the {fire}, but it stayed bright and hot", "poured water over the {fire} until the sparks stopped", tags={"water"}),
    "cover": Response("cover", 3, 4, "covered the {fire} with a metal lid and smothered the glow", "tried to cover the {fire}, but it was already too tall and wild", "covered the {fire} with a lid and smothered the glow", tags={"lid"}),
    "call_firefighter": Response("call_firefighter", 4, 5, "called the firefighters, who came with hoses and careful hands", "called the firefighters, but the {fire} had already spread too far", "called the firefighters, who came with hoses and careful hands", tags={"firefighters"}),
}



@dataclass
class StoryParams:
    setting: str
    act: str
    fire: str
    response: str
    singer_a: str
    singer_b: str
    a_type: str
    b_type: str
    grownup: str
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

CURATED = [
    ("garden", "duet", "bonfire", "cover", "Nia", "Bo", "girl", "boy", "mother", 0),
    ("meadow", "duet", "bonfire", "water", "Lina", "Milo", "girl", "boy", "father", 1),
    ("backyard", "duet", "bonfire", "call_firefighter", "Ava", "Eli", "girl", "boy", "mother", 0),
]



def valid_combos() -> list[tuple[str, str, str]]:
    return [(sid, "duet", fid) for sid in SETTINGS for fid in FIRES]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme-style story that includes the words "duet", "bonfire", and "stubborn".',
        f"Tell a happy-ending story where {f['a'].id} and {f['b'].id} sing a duet near a bonfire, but a stubborn child does not want to keep it going unsafely.",
        f"Write a gentle rhyme about children who need a grown-up to finish a bonfire and then sing by lantern light.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, grownup, fire = f["a"], f["b"], f["grownup"], f["fire"]
    return [
        ("Who is the story about?", f"It is about {a.id} and {b.id}, who sang a duet near a bonfire, and the grown-up who helped them be safe."),
        ("What did the stubborn child want to do?", f"{b.id} wanted to keep the bonfire going and sing one more chorus. {b.id} was stubborn, but the safer choice was to stop and call for help."),
        ("How did the story end?", f"It ended happily. The bonfire was put out, and {a.id} and {b.id} sang their duet again by lantern light."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["act"].tags) | set(world.facts["fire"].tags) | set(world.facts["response"].tags)
    out: list[tuple[str, str]] = []
    if "duet" in tags:
        out.append(("What is a duet?", "A duet is a song or piece sung or played by two people together. They share the tune and take turns or sing side by side."))
    if "bonfire" in tags:
        out.append(("What is a bonfire?", "A bonfire is a large outdoor fire made for warmth, light, or a special gathering. It must be watched carefully."))
    if "firefighters" in tags:
        out.append(("Who are firefighters?", "Firefighters are trained helpers who put out fires and keep people safe."))
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, A, F) :- setting(S), act(A), fire(F).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
contained :- chosen_response(R), response(R), power(R, P), severity(V), P >= V.
outcome(contained) :- contained.
outcome(burned) :- not contained.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ACTS:
        lines.append(asp.fact("act", aid))
    for fid, f in FIRES.items():
        lines.append(asp.fact("fire", fid))
        lines.append(asp.fact("severity", fid, f.heat))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
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
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("chosen_response", params.response), asp.fact("severity", params.fire)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate.")
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    try:
        for p in CURATED[:1]:
            sample = generate(StoryParams(*p))
            if not sample.story.strip():
                raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    cases = [StoryParams(*p) for p in CURATED]
    if all(asp_outcome(p) in {"contained", "burned"} for p in cases):
        print("OK: ASP outcome model exercised.")
    else:
        rc = 1
        print("MISMATCH in ASP outcome model.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme duet and bonfire story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
    ap.add_argument("--singer-a")
    ap.add_argument("--singer-b")
    ap.add_argument("--n", type=int, default=1)
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("That response is too weak for this story world.")
    setting = args.setting or rng.choice(sorted(SETTINGS))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    singer_a = args.singer_a or rng.choice(["Nia", "Luna", "Mina", "Rae", "Ada"])
    singer_b = args.singer_b or rng.choice(["Bo", "Pip", "Finn", "Otto", "Ivy"])
    if singer_a == singer_b:
        singer_b = "Bo"
    a_type = "girl"
    b_type = "boy"
    grownup = rng.choice(["mother", "father"])
    return StoryParams(setting, "duet", "bonfire", response, singer_a, singer_b, a_type, b_type, grownup, args.delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ACTS[params.act], FIRES[params.fire], RESPONSES[params.response],
                 params.singer_a, params.singer_b, params.a_type, params.b_type, params.grownup, params.singer_b, params.delay)
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}")
        print(f"{len(asp_valid_combos())} compatible combos.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(*p)) for p in CURATED]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.singer_a} & {p.singer_b}: {p.setting} / {p.response}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
