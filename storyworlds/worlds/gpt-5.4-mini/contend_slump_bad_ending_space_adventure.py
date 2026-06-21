#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/contend_slump_bad_ending_space_adventure.py
===========================================================================

A standalone storyworld for a small Space Adventure domain with a bad ending:
two kids contend with a failing rover on a moon walk, but the rescue plan is too
weak and their ship loses the landing site. The story keeps the action grounded
in simulated world state, with physical meters and emotional memes, and always
includes the seed words "contend" and "slump".
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
class Setting:
    id: str
    scene: str
    sky: str
    base: str
    dark_spot: str
    destination: str
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
class Hazard:
    id: str
    label: str
    danger: str
    tags: set[str] = field(default_factory=set)
    slips: bool = False
    drains: bool = False

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
class Gear:
    id: str
    label: str
    phrase: str
    power: int
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


def _r_drain(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["drained"] < THRESHOLD:
            continue
        sig = ("drain", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["hopeless"] += 1
        out.append("__drain__")
    return out


def _r_slump(world: World) -> list[str]:
    out: list[str] = []
    rover = world.entities.get("rover")
    if rover and rover.meters["slump"] >= THRESHOLD:
        sig = ("slump", rover.id)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("site").meters["risk"] += 1
            for e in world.characters():
                e.memes["fear"] += 1
            out.append("__slump__")
    return out


CAUSAL_RULES = [
    Rule("drain", "social", _r_drain),
    Rule("slump", "physical", _r_slump),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def hazard_at_risk(hazard: Hazard, setting: Setting) -> bool:
    return hazard.slips and "vacuum" in setting.tags or hazard.drains and "space" in setting.tags


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def is_contained(response: Response, hazard: Hazard, delay: int) -> bool:
    return response.power >= hazard_severity(hazard, delay)


def hazard_severity(hazard: Hazard, delay: int) -> int:
    return 2 + delay if hazard.slips else 1 + delay


def predict_slump(world: World) -> dict:
    sim = world.copy()
    _do_hazard(sim, sim.get("hazard"), narrate=False)
    return {"slumped": sim.get("rover").meters["slump"] >= THRESHOLD,
            "risk": sim.get("site").meters["risk"]}


def _do_hazard(world: World, hazard_ent: Entity, narrate: bool = True) -> None:
    hazard_ent.meters["slump"] += 1
    hazard_ent.meters["damaged"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    hero.memes["wonder"] += 1
    friend.memes["wonder"] += 1
    world.say(
        f"On a bright day beyond Earth, {hero.id} and {friend.id} floated at the edge of {setting.scene}. "
        f"Their little ship rested by {setting.base}, and {setting.sky} glimmered over {setting.dark_spot}."
    )
    world.say(
        f"They were on a moon adventure to reach {setting.destination}, where the map said a shiny signal stone waited."
    )


def need_help(world: World, hero: Entity, setting: Setting) -> None:
    world.say(
        f"But the path ahead turned rough and cold. The rover track dipped near {setting.dark_spot}, and the wheels began to shake."
    )
    world.say(f'"We need help," {hero.id} said, peering into the dust.')


def contend(world: World, hero: Entity, friend: Entity, hazard: Hazard) -> None:
    hero.memes["determination"] += 1
    friend.memes["worry"] += 1
    world.say(
        f'{hero.id} wanted to contend with the problem alone. "I can fix it!" {hero.id} said, and {friend.id} frowned at the loose wheel.'
    )
    world.say(
        f'"Careful," {friend.id} said. "That {hazard.label} can make the rover {hazard.danger}."'
    )


def slump_event(world: World, hazard: Hazard) -> None:
    _do_hazard(world, world.get("hazard"))
    world.say(
        f"Before anyone could stop it, the rover gave a low groan and began to slump sideways. "
        f"{hazard.label.capitalize()} spilled dust all over the tracks."
    )


def attempt_fix(world: World, parent: Entity, response: Response, hazard: Hazard, delay: int) -> bool:
    world.say(
        f"{parent.label_word.capitalize()} called from the ship and tried to help with a quick plan: "
        f"{response.text.replace('{hazard}', hazard.label)}."
    )
    if is_contained(response, hazard, delay):
        return True
    world.say("It was not enough. The rover stayed stuck, and the dust kept sliding into the wrong places.")
    return False


def bad_ending(world: World, hero: Entity, friend: Entity, parent: Entity, setting: Setting) -> None:
    hero.memes["hope"] = 0.0
    friend.memes["hope"] = 0.0
    parent.memes["fear"] += 1
    world.say(
        f"The rescue took too long. The landing lights blinked, then the shuttle drifted away from {setting.base}. "
        f"{hero.id} and {friend.id} pressed their faces to the window and watched their little rover fade into the dust."
    )
    world.say(
        "By the time the engines hummed quiet, the signal stone was lost, the track was dark, and the moon adventure was over."
    )
    world.say(
        f"Both children sat very still, too tired to contend with anything else, while the stars went on shining above them."
    )


def tell(setting: Setting, hazard: Hazard, gear: Gear, response: Response,
         hero_name: str, hero_type: str, friend_name: str, friend_type: str,
         parent_type: str, delay: int = 1) -> World:
    world = World()
    hero = world.add(Entity(hero_name, kind="character", type=hero_type, role="hero"))
    friend = world.add(Entity(friend_name, kind="character", type=friend_type, role="friend"))
    parent = world.add(Entity("Captain", kind="character", type=parent_type, role="parent"))
    site = world.add(Entity("site", type="site", label=setting.id))
    rover = world.add(Entity("rover", type="rover", label="little rover"))
    hazard_ent = world.add(Entity("hazard", type="thing", label=hazard.label))
    world.facts["delay"] = delay

    setup(world, hero, friend, setting)
    need_help(world, hero, setting)
    world.para()
    contend(world, hero, friend, hazard)
    slump_event(world, hazard)
    world.para()

    world.say(
        f"{friend.id} tried to brace the wheel with {gear.phrase}, but the fix was clumsy and too small for the slip."
    )
    ok = attempt_fix(world, parent, response, hazard, delay)
    if not ok:
        bad_ending(world, hero, friend, parent, setting)
        world.facts["outcome"] = "bad"
    else:
        world.say("The rescue worked, but this world is built for the bad-ending branch; the weaker ending is not used.")
        world.facts["outcome"] = "good"

    world.facts.update(
        hero=hero, friend=friend, parent=parent, setting=setting, hazard=hazard,
        gear=gear, response=response, rover=rover, site=site,
        slumped=rover.meters["slump"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "moon_base": Setting(
        "moon base",
        "a silver moon base",
        "a black sky",
        "the docking bay",
        "the crater trail",
        "the signal stone",
        tags={"space", "vacuum"},
    ),
    "asteroid_port": Setting(
        "asteroid port",
        "a tiny asteroid port",
        "a starry sky",
        "the metal platform",
        "the drifting path",
        "the beacon gem",
        tags={"space", "vacuum"},
    ),
}

HAZARDS = {
    "dust_slip": Hazard("dust slip", "dust slip", "slump", slips=True, tags={"space"}),
    "fuel_drain": Hazard("fuel drain", "fuel drain", "drain", drains=True, tags={"space"}),
}

GEAR = {
    "strap": Gear("strap", "stability strap", "a stability strap", 1, tags={"space"}),
    "patch": Gear("patch", "patch kit", "a tiny patch kit", 1, tags={"space"}),
}

RESPONSES = {
    "tow": Response("tow", 2, 1, "hooked a tow line around the rover and pulled hard", "hooked a tow line around the rover, but the dust kept sliding", "towed the rover"),
    "shield": Response("shield", 3, 2, "set up a shield panel to block the worst dust", "set up a shield panel, but it was too late", "set up a shield panel"),
    "signal": Response("signal", 1, 1, "sent a small signal and hoped for the best", "sent a small signal, but nobody reached them in time", "sent a small signal"),
}

HERO_NAMES = ["Nova", "Milo", "Iris", "Kai", "Luna", "Orion"]
FRIEND_NAMES = ["Pip", "Rae", "Zed", "Tala", "Finn", "Juno"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    hazard: str
    gear: str
    response: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    parent: str
    delay: int = 1
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
    for sid, s in SETTINGS.items():
        for hid, h in HAZARDS.items():
            if hazard_at_risk(h, s):
                combos.append((sid, hid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld with a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--hero")
    ap.add_argument("--friend")
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


def explain_rejection() -> str:
    return "(No story: this space problem must be a real hazard in a vacuum setting.)"


def sensible_response_ids() -> list[str]:
    return [r.id for r in sensible_responses()]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("(Refusing response: too weak for a believable rescue.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.hazard is None or c[1] == args.hazard)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, hazard = rng.choice(sorted(combos))
    gear = args.gear or rng.choice(sorted(GEAR))
    response = args.response or rng.choice(sensible_response_ids())
    hero = args.hero or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, hazard, gear, response, hero, "girl", friend, "boy", parent, delay=1)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting], HAZARDS[params.hazard], GEAR[params.gear],
        RESPONSES[params.response], params.hero, params.hero_gender,
        params.friend, params.friend_gender, params.parent, params.delay
    )
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
        f'Write a space-adventure story for a 3-to-5-year-old that uses the words "contend" and "slump".',
        f"Tell a bad-ending moon story where {f['hero'].id} and {f['friend'].id} contend with a rover problem near {f['setting'].destination} but fail to fix it in time.",
        f"Write a child-facing space adventure with stars, a rover, and a sad ending where the ship leaves the landing site behind.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend, parent = f["hero"], f["friend"], f["parent"]
    setting, hazard = f["setting"], f["hazard"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id} and {friend.id}, who went on a moon adventure with {parent.label_word}."),
        ("What problem did they have?",
         f"The rover hit a {hazard.label} near {setting.dark_spot}. That made the rover slump and made the trip unsafe."),
        ("Why was the ending sad?",
         f"The fix came too late, so the ship drifted away from {setting.base}. They lost the landing site and the signal stone."),
        ("What words from the seed appear in the story?",
         "The story uses the words contend and slump while the children try to solve the rover problem."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a rover?",
         "A rover is a small vehicle that moves across a planet or moon. Space teams use it to travel over rough ground."),
        ("Why is a vacuum dangerous for a story like this?",
         "A vacuum has no air, so people cannot breathe there. That is why a moon story needs a ship and careful help."),
        ("What does a signal do?",
         "A signal is a message sent to tell someone where you are or that you need help."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(F, S) :- hazard(F), setting(S), space(S).
valid(S, H) :- setting(S), hazard(H), hazard_at_risk(H, S).
outcome(bad) :- chosen_response(R), response(R), sense(R, X), sense_min(M), X < M.
outcome(bad) :- not outcome(good).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        if h.slips:
            lines.append(asp.fact("slips", hid))
        if h.drains:
            lines.append(asp.fact("drains", hid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in ASP gate.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, hazard=None, gear=None, response=None, parent=None, hero=None, friend=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


CURATED = [
    StoryParams("moon_base", "dust_slip", "strap", "tow", "Nova", "girl", "Pip", "boy", "mother", 1),
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
        print(asp_program(show="#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, h in asp_valid_combos():
            print(f"  {s} {h}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
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
