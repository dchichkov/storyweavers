#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tolerate_tit_dim_abbreviate_sound_effects_lesson.py
===================================================================================

A standalone story world for a tiny superhero-style scene with sound effects and a
lesson learned.

Seed idea
---------
A young hero and a mentor face a noisy city alarm. The hero first finds the alarm
annoying, then learns to tolerate the sound long enough to help. Along the way,
the hero must abbreviate a long warning into a short code message while the city
broadcast makes a cheerful "tit-dim" sound. The ending proves the change: the hero
can now work calmly with noise and use short, clear signals.

This script follows the Storyweavers contract:
- self-contained stdlib-only script
- typed entities with meters and memes
- forward-chained world state drives prose
- QA is grounded in simulated state
- inline ASP twin plus Python reasonableness gate
- supports --verify, --asp, --show-asp, --qa, --json, --trace, -n, --all, --seed
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Device:
    id: str
    label: str
    sound: str
    short_code: str
    purpose: str
    noisy: bool = False
    repairable: bool = False

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
class Trouble:
    id: str
    label: str
    danger: str
    spreads: int
    noisy: bool = False

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
        clone.facts = copy.deepcopy(self.facts)
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


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    alarm = world.entities.get("alarm")
    if not alarm:
        return out
    if alarm.meters["active"] < THRESHOLD:
        return out
    sig = ("noise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in list(world.entities.values()):
        if e.kind == "character":
            e.memes["stress"] += 1
    out.append("__noise__")
    return out


def _r_damage(world: World) -> list[str]:
    trouble = world.entities.get("trouble")
    if not trouble or trouble.meters["active"] < THRESHOLD:
        return []
    sig = ("damage",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if "city" in world.entities:
        world.get("city").meters["risk"] += trouble.meters["active"]
    return []


CAUSAL_RULES = [Rule("noise", "social", _r_noise), Rule("damage", "physical", _r_damage)]


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


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def hazard_ok(device: Device, trouble: Trouble) -> bool:
    return device.noisy and trouble.noisy


def is_contained(response: Response, trouble: Trouble, delay: int) -> bool:
    return response.power >= trouble.spreads + delay


def _do_alarm(world: World, trouble: Trouble, narrate: bool = True) -> None:
    world.get("alarm").meters["active"] += 1
    world.get("trouble").meters["active"] += 1
    propagate(world, narrate=narrate)


def predict(world: World) -> dict:
    sim = world.copy()
    _do_alarm(sim, TROUBLES["street_glitch"], narrate=False)
    return {"stress": sum(e.memes["stress"] for e in sim.entities.values()),
            "risk": sim.get("city").meters["risk"]}


def intro(world: World, hero: Entity, sidekick: Entity, city: Entity, device: Device) -> None:
    world.say(
        f"On a bright afternoon in Star Harbor, {hero.id} and {sidekick.id} watched over the city from the roof of the blue tower. "
        f"Their patrol speaker was called the {device.label}, and when it woke up it went {device.sound}."
    )
    world.say(
        f"{hero.id} loved big heroic moments, but {sidekick.id} liked tiny fixes and clear words. "
        f"The city below glittered like a tiny map."
    )


def trouble_start(world: World, hero: Entity, trouble: Trouble) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"Then the {trouble.label} began. {trouble.danger}, and the tower speaker flashed {trouble.id}."
    )


def tolerate(world: World, hero: Entity, sidekick: Entity, trouble: Trouble) -> None:
    pred = predict(world)
    hero.memes["tolerate"] += 1
    world.facts["predicted_risk"] = pred["risk"]
    world.say(
        f'{hero.id} frowned at the noise. "I do not like this {trouble.id}," {hero.id} muttered, '
        f'but {hero.id} tried to tolerate it long enough to help.'
    )
    if pred["stress"] >= THRESHOLD:
        world.say(
            f'{sidekick.id} put a hand on {hero.id}\'s shoulder. "We can keep going," {sidekick.id} said, '
            f'"if we stay calm together."'
        )


def abbreviate(world: World, hero: Entity, device: Device, trouble: Trouble) -> None:
    hero.memes["focus"] += 1
    code = device.short_code
    world.say(
        f"{hero.id} grabbed the patrol mic and decided to abbreviate the warning. "
        f'Instead of a long speech, {hero.id} said, "{code}!"'
    )


def siren(world: World, device: Device) -> None:
    world.say(f'The speaker answered with a cheerful "{device.sound}" and the red light spun like a toy top.')


def rescue(world: World, hero: Entity, sidekick: Entity, response: Response, trouble: Trouble) -> None:
    trouble_ent = world.get("trouble")
    trouble_ent.meters["active"] = 0
    world.get("alarm").meters["active"] = 0
    body = response.text.replace("{trouble}", trouble.label)
    world.say(f"{hero.id} listened to the plan. {sidekick.id} moved first, and together they {body}.")
    world.say("The loud danger faded, and the roof felt quiet again.")


def lesson(world: World, hero: Entity, sidekick: Entity, trouble: Trouble, device: Device) -> None:
    for e in (hero, sidekick):
        e.memes["relief"] += 1
        e.memes["lesson"] += 1
    world.say("For a moment, the two heroes just smiled at each other.")
    world.say(
        f'{sidekick.id} said, "A hero does not have to love every sound. A hero can tolerate it, '
        f'keep the message short, and still do the right thing."'
    )
    world.say(
        f"{hero.id} nodded. From then on, every warning got shorter, clearer, and faster."
    )
    world.say(
        f"That night, the tower speaker clicked {device.sound} one more time, and {hero.id} did not flinch."
    )


def tell(device: Device, trouble: Trouble, response: Response,
         hero_name: str = "Nova", hero_gender: str = "girl",
         sidekick_name: str = "Zip", sidekick_gender: str = "boy") -> World:
    world = World()
    hero = world.add(Entity(hero_name, "character", hero_gender, role="hero"))
    sidekick = world.add(Entity(sidekick_name, "character", sidekick_gender, role="sidekick"))
    city = world.add(Entity("city", "thing", "city"))
    world.add(Entity("alarm", "thing", "alarm"))
    world.add(Entity("trouble", "thing", trouble.label))
    world.get("alarm").meters["active"] = 0
    world.get("trouble").meters["active"] = 0

    intro(world, hero, sidekick, city, device)
    world.para()
    trouble_start(world, hero, trouble)
    siren(world, device)
    tolerate(world, hero, sidekick, trouble)
    abbreviate(world, hero, device, trouble)

    if is_contained(response, trouble, 0):
        world.para()
        rescue(world, hero, sidekick, response, trouble)
        lesson(world, hero, sidekick, trouble, device)
        outcome = "contained"
    else:
        world.para()
        world.say(
            f"{hero.id} tried the plan, but the {trouble.label} was too big. The warning kept echoing, and the city risk climbed."
        )
        world.say("So the heroes called for backup, and the lesson was to ask for help sooner.")
        for e in (hero, sidekick):
            e.memes["lesson"] += 1
        outcome = "spilled"

    world.facts.update(hero=hero, sidekick=sidekick, city=city, device=device,
                       trouble=trouble, response=response, outcome=outcome)
    return world


DEVICES = {
    "tower_speaker": Device("tower_speaker", "tower speaker", "tit-dim", "Help now!", "announces emergencies", noisy=True, repairable=True),
    "signal_lamp": Device("signal_lamp", "signal lamp", "tit-dim", "Roof clear!", "warns allies", noisy=False, repairable=True),
}

TROUBLES = {
    "street_glitch": Trouble("street_glitch", "street glitch", "A scooter jammed the crosswalk and the corner gate stuck shut", 2, noisy=True),
    "storm_burst": Trouble("storm_burst", "storm burst", "A gusty storm tossed trash bins and rattled window signs", 3, noisy=True),
    "bridge_hum": Trouble("bridge_hum", "bridge hum", "The old bridge started humming and shaking under a heavy truck", 4, noisy=True),
}

RESPONSES = {
    "radio": Response("radio", 3, 5, "radioed the rescue crew and guided them to the problem", "radioed too late and the trouble kept spreading", "radioed the rescue crew"),
    "rope": Response("rope", 2, 3, "secured the blocked gate with a rope and cleared the path", "tied the rope wrong and the path stayed blocked", "secured the blocked gate"),
    "signal": Response("signal", 3, 4, "sent a bright signal to the helpers and pointed them to the trouble", "sent a signal, but it was too weak to help", "sent a bright signal"),
}

NAMES_GIRL = ["Nova", "Iris", "Mina", "Zara", "Luna", "Tess"]
NAMES_BOY = ["Zip", "Kai", "Jax", "Milo", "Finn", "Theo"]
TRAITS = ["steady", "bright", "patient", "bold", "kind"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for d in DEVICES.values():
        for t in TROUBLES.values():
            if hazard_ok(d, t):
                combos.append((d.id, t.id))
    return combos


@dataclass
@dataclass
class StoryParams:
    device: str
    trouble: str
    response: str
    hero_name: str
    hero_gender: str
    sidekick_name: str
    sidekick_gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny superhero story world with sound effects and a lesson learned.")
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--sidekick-name")
    ap.add_argument("--sidekick-gender", choices=["girl", "boy"])
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
              if (args.device is None or c[0] == args.device)
              and (args.trouble is None or c[1] == args.trouble)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    device, trouble = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(NAMES_GIRL if hero_gender == "girl" else NAMES_BOY)
    sidekick_gender = args.sidekick_gender or ("boy" if hero_gender == "girl" else "girl")
    sidekick_name = args.sidekick_name or rng.choice(NAMES_BOY if sidekick_gender == "boy" else NAMES_GIRL)
    return StoryParams(device, trouble, response, hero_name, hero_gender, sidekick_name, sidekick_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(DEVICES[params.device], TROUBLES[params.trouble], RESPONSES[params.response],
                 params.hero_name, params.hero_gender, params.sidekick_name, params.sidekick_gender)
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
        f'Write a superhero story for a child that includes the sound effect "{f["device"].sound}" and the word "tolerate".',
        f'Tell a superhero rescue story where {f["hero"].id} learns to abbreviate a warning into a short code.',
        f'Write a story with a lesson learned: a hero does not need to love noise, but can still tolerate it and help.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, sidekick, device, trouble, response = f["hero"], f["sidekick"], f["device"], f["trouble"], f["response"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id} and {sidekick.id}, two young heroes keeping watch over the city. The tower speaker and the city trouble are part of their rescue day."),
        ("What did the hero do when the noise started?",
         f"{hero.id} tried to tolerate the noise long enough to help instead of giving up. That helped {hero.id} stay near the mic and use a short warning."),
        ("What did the hero abbreviate?",
         f"{hero.id} shortened the long warning into the short code \"{device.short_code}\". Using fewer words made the message quick and clear."),
    ]
    if f["outcome"] == "contained":
        qa.append((
            "How did they solve the problem?",
            f"They used {response.qa_text} and stopped the trouble before it could spread further. After that, the city felt calm again."
        ))
    qa.append((
        "What lesson did the heroes learn?",
        f"They learned that a hero can tolerate a noisy moment, keep the message short, and still do the right thing. That lesson is why the ending feels calm instead of chaotic."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {f["device"].id, f["trouble"].id, f["response"].id, "lesson"}
    out = []
    if "tower_speaker" in tags:
        out.append(("What is a tower speaker for?", "A tower speaker is a city device that announces urgent news so helpers can hear it fast."))
    out.append(("What does tolerate mean?", "To tolerate something means you allow it or endure it even if you do not like it very much."))
    out.append(("What does abbreviate mean?", "To abbreviate means to make a word or message shorter. That helps when you need quick, clear communication."))
    out.append(("What are sound effects in a story?", "Sound effects are words that help you hear a scene in your mind, like a buzzing siren or a cheerful ding."))
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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
noise(H) :- alarm(H), active(H).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
contained :- chosen_response(R), response(R), power(R,P), severity(S), P >= S.
outcome(contained) :- contained.
outcome(spilled) :- not contained.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for did, d in DEVICES.items():
        lines.append(asp.fact("alarm", did))
        if d.noisy:
            lines.append(asp.fact("noisy", did))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        if t.noisy:
            lines.append(asp.fact("noisy", tid))
        lines.append(asp.fact("severity", tid, t.spreads))
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
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP gate matches valid_combos().")
    else:
        print("MISMATCH in ASP gate.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(device=None, trouble=None, response=None,
                                                            hero_name=None, hero_gender=None,
                                                            sidekick_name=None, sidekick_gender=None),
                                   random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def explain_rejection(device: Device, trouble: Trouble) -> str:
    return f"(No story: {device.label} can make a {device.sound} sound, but this trouble is not a good enough match.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). Try: {better}.)"


def valid_story_combo(device: Device, trouble: Trouble, response: Response) -> bool:
    return hazard_ok(device, trouble) and response.sense >= SENSE_MIN


CURATED = [
    StoryParams("tower_speaker", "street_glitch", "radio", "Nova", "girl", "Zip", "boy"),
    StoryParams("tower_speaker", "storm_burst", "signal", "Iris", "girl", "Kai", "boy"),
    StoryParams("tower_speaker", "bridge_hum", "rope", "Mina", "girl", "Jax", "boy"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.device and args.trouble:
        if not hazard_ok(DEVICES[args.device], TROUBLES[args.trouble]):
            raise StoryError(explain_rejection(DEVICES[args.device], TROUBLES[args.trouble]))
    combos = [c for c in valid_combos()
              if (args.device is None or c[0] == args.device)
              and (args.trouble is None or c[1] == args.trouble)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    device, trouble = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    return StoryParams(device, trouble, response,
                       args.hero_name or rng.choice(NAMES_GIRL if (args.hero_gender or "girl") == "girl" else NAMES_BOY),
                       args.hero_gender or "girl",
                       args.sidekick_name or rng.choice(NAMES_BOY if (args.sidekick_gender or "boy") == "boy" else NAMES_GIRL),
                       args.sidekick_gender or "boy")


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
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible device/trouble combos.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
