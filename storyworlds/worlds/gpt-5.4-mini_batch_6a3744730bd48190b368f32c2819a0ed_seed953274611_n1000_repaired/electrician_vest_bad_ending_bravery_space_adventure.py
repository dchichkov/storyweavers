#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/electrician_vest_bad_ending_bravery_space_adventure.py
======================================================================================

A small standalone storyworld for a Space Adventure-style tale about bravery,
an electrician, and a vest. The premise is simple: a child on a space ship wants
to help an electrician fix a power problem, but bravery can turn into stubborn
risk-taking. When the wrong choice is made, the ship can drift into a bad ending.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRAVERY_MIN = 3.0
DANGER_LIMIT = 2.0


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
    risky: bool = False
    protective: bool = False

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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    scene: str
    place_line: str
    dark_spot: str
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
    risky: bool = True
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
class Gear:
    id: str
    label: str
    phrase: str
    safe: bool = True
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
    power: int
    sense: int
    text: str
    fail: str
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
class StoryParams:
    setting: str
    hazard: str
    gear: str
    response: str
    hero: str
    hero_gender: str
    electrician: str
    electrician_gender: str
    parent: str
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
        import copy
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


SETTINGS = {
    "rocket_bay": Setting(
        id="rocket_bay",
        scene="a bright rocket bay",
        place_line="The rocket bay hummed with blue lights and silver tools.",
        dark_spot="the shadow under the engine panel",
        tags={"space", "ship"},
    ),
    "moon_tunnel": Setting(
        id="moon_tunnel",
        scene="a quiet moon tunnel",
        place_line="The tunnel walls glowed softly, and little dust sparkled in the air.",
        dark_spot="the bend where the tunnel lights failed",
        tags={"space", "moon"},
    ),
    "orbit_lab": Setting(
        id="orbit_lab",
        scene="an orbit lab",
        place_line="The lab floated in the station, with cables tucked along the floor.",
        dark_spot="the far corner behind the control chair",
        tags={"space", "lab"},
    ),
}

HAZARDS = {
    "power_strip": Hazard("power_strip", "a sparking power strip", risky=True, tags={"electric"}),
    "broken_panel": Hazard("broken_panel", "a broken wall panel", risky=True, tags={"electric"}),
    "wire_bundle": Hazard("wire_bundle", "a loose wire bundle", risky=True, tags={"electric"}),
}

GEAR = {
    "vest": Gear("vest", "vest", "a bright safety vest", safe=True, tags={"vest"}),
    "gloves": Gear("gloves", "gloves", "thick work gloves", safe=True, tags={"gloves"}),
    "helmet": Gear("helmet", "helmet", "a padded helmet", safe=True, tags={"helmet"}),
}

RESPONSES = {
    "shutoff": Response(
        "shutoff",
        power=4,
        sense=4,
        text="switched off the main breaker and wrapped the cable ends safely",
        fail="switched things the wrong way and the panel sparked even harder",
        tags={"safe", "electric"},
    ),
    "call_help": Response(
        "call_help",
        power=3,
        sense=4,
        text="called mission control and waited for the remote reset",
        fail="called for help too late, after the lights had already failed",
        tags={"safe", "electric"},
    ),
    "patch": Response(
        "patch",
        power=2,
        sense=2,
        text="patched the circuit with a spare connector and tested it carefully",
        fail="patched it badly and the ship lost power anyway",
        tags={"safe", "electric"},
    ),
}

HERO_NAMES = ["Milo", "Nia", "Tessa", "Owen", "Pia", "Rey", "Luca", "Maya"]
ELECTRICIAN_NAMES = ["Ari", "June", "Noel", "Sage", "Iris", "Tariq"]
TRAITS = ["brave", "curious", "careful", "bold", "stubborn"]


def hazard_at_risk(setting: Setting, hazard: Hazard) -> bool:
    return setting.id in {"rocket_bay", "moon_tunnel", "orbit_lab"} and hazard.risky


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 3]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for h in HAZARDS:
            for g in GEAR:
                for r in RESPONSES:
                    if hazard_at_risk(SETTINGS[s], HAZARDS[h]):
                        combos.append((s, h, g, r))
    return combos


def outcome_of(params: StoryParams) -> str:
    if params.response == "call_help":
        return "bad"
    if params.response == "patch" and params.setting == "moon_tunnel":
        return "bad"
    return "bad"


ASP_RULES = r"""
risk(S,H) :- setting(S), hazard(H), hazardous(H).
valid(S,H,G,R) :- risk(S,H), gear(G), response(R).
outcome(bad) :- chosen_response(call_help).
outcome(bad) :- chosen_response(patch), chosen_setting(moon_tunnel).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        if h.risky:
            lines.append(asp.fact("hazardous", hid))
    for gid in GEAR:
        lines.append(asp.fact("gear", gid))
    for rid in RESPONSES:
        lines.append(asp.fact("response", rid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, hazard=None, gear=None, response=None,
            hero=None, hero_gender=None, electrician=None, electrician_gender=None,
            parent=None
        ), random.Random(1)))
        if not sample.story.strip():
            ok = False
            print("MISMATCH: generate produced empty story.")
    except Exception as exc:
        ok = False
        print(f"MISMATCH: normal generation failed: {exc}")
    if ok:
        print("OK: ASP parity and generation smoke test passed.")
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A space-adventure storyworld about bravery and a vest.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", dest="hero_gender", choices=["girl", "boy"])
    ap.add_argument("--electrician")
    ap.add_argument("--electrician-gender", dest="electrician_gender", choices=["woman", "man", "girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.response and args.response not in RESPONSES:
        raise StoryError("unknown response")
    setting = args.setting or rng.choice(list(SETTINGS))
    hazard = args.hazard or rng.choice(list(HAZARDS))
    gear = args.gear or rng.choice(list(GEAR))
    response = args.response or rng.choice(list(RESPONSES))
    if not hazard_at_risk(SETTINGS[setting], HAZARDS[hazard]):
        raise StoryError("No story: that hazard doesn't create a useful problem in this setting.")
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    electrician_gender = args.electrician_gender or rng.choice(["woman", "man"])
    hero = args.hero or rng.choice(HERO_NAMES)
    electrician = args.electrician or rng.choice(ELECTRICIAN_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting, hazard=hazard, gear=gear, response=response,
        hero=hero, hero_gender=hero_gender, electrician=electrician,
        electrician_gender=electrician_gender, parent=parent
    )


def _story(world: World, params: StoryParams) -> None:
    setting = SETTINGS[params.setting]
    hazard = HAZARDS[params.hazard]
    gear = GEAR[params.gear]
    response = RESPONSES[params.response]
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    electrician = world.add(Entity(id=params.electrician, kind="character", type=params.electrician_gender, role="electrician", label="the electrician"))
    parent = world.add(Entity(id=params.parent, kind="character", type=params.parent, label="the parent"))
    ship = world.add(Entity(id="ship", kind="thing", type="ship", label="the ship"))
    panel = world.add(Entity(id="panel", kind="thing", type="thing", label=hazard.label, risky=True))
    vest = world.add(Entity(id="vest", kind="thing", type="thing", label=gear.label, protective=True))

    hero.memes["bravery"] = 4.0
    hero.memes["wanting"] = 1.0
    electrician.memes["worry"] = 1.0

    world.say(f"{hero.id} and {electrician.id} were aboard {setting.scene}. {setting.place_line}")
    world.say(f"{hero.id} wanted to help {electrician.id} with {hazard.label}, and {hero.id} wore {gear.phrase} like a tiny captain's badge.")
    world.para()
    world.say(f'“We need to be careful,” said {electrician.id}. “This is work for a real electrician.”')
    if hero.memes["bravery"] >= BRAVERY_MIN:
        world.say(f"But {hero.id}'s bravery swelled bigger than fear. {hero.id} reached for the panel anyway.")
        world.say(f"The {hazard.label} snapped, the lights blinked, and the {setting.dark_spot} filled with a nasty blue flash.")
        ship.meters["power_loss"] += 3
        hero.memes["fear"] += 2
        electrician.memes["fear"] += 2
        world.para()
        if response.power >= 3:
            world.say(f"{electrician.id} {response.text}.")
        else:
            world.say(f"{electrician.id} tried to help, but {response.fail}.")
        world.say("The ship drifted farther from the moon base, and the blinking lights went out one by one.")
        world.para()
        world.say(f"{hero.id} finally understood that bravery without listening can turn the dark bigger, not smaller.")
        world.say("By the time the rescue tug arrived, the little ship had already missed its safe landing path.")
        world.say("That was the bad ending: everyone lived, but the mission was lost.")
    else:
        world.say(f"{hero.id} listened, held still, and let {electrician.id} do the real fixing.")
        world.say(f"With the {gear.label} on, the tools stayed steady, and the danger stayed small.")
        world.say(f"Together they kept the ship bright, and the adventure ended with a clean safe dock.")
    world.facts.update(
        setting=setting, hazard=hazard, gear=gear, response=response,
        hero=hero, electrician=electrician, parent=parent, ship=ship, panel=panel,
        outcome="bad", bravery=hero.memes["bravery"]
    )


def generate(params: StoryParams) -> StorySample:
    world = World()
    _story(world, params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space adventure story that includes the words "{f["hero"].id}" and "electrician".',
        f"Tell a brave but risky spaceship story about a child wearing a vest and trying to help the electrician.",
        f"Write a bad-ending space story where bravery leads to trouble with a power problem on a ship.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero: Entity = f["hero"]
    electrician: Entity = f["electrician"]
    setting: Setting = f["setting"]
    hazard: Hazard = f["hazard"]
    return [
        ("Who is the story about?", f"It is about {hero.id} and {electrician.id} on a spaceship. The story shows how bravery can become a mistake when the wrong job is handled the wrong way."),
        ("What was the problem?", f"The ship had {hazard.label}, and the lights were failing in {setting.scene}. That made the place feel dangerous and hard to fix."),
        ("How did the story end?", "It ended badly. The ship drifted off course, so the mission was lost even though everyone stayed alive."),
        ("Why did the ending go wrong?", f"{hero.id} was too brave and reached for the panel instead of letting the electrician work. That choice made the danger grow faster than the repair could finish."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does an electrician do?", "An electrician fixes wires, power, and lights. They help keep machines and buildings working safely."),
        ("What is a vest?", "A vest is a piece of clothing you wear over your shirt. In this story it helps the child feel ready and important."),
        ("What is bravery?", "Bravery means doing something hard even when you feel scared. It is good when you listen, but it can be risky if you ignore safety."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        out.append(f"{e.id}: {' '.join(bits)}")
    return "\n".join(out)


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
        print(asp_program("", "#show valid/4.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    curated = [
        StoryParams(setting="rocket_bay", hazard="power_strip", gear="vest", response="shutoff",
                    hero="Milo", hero_gender="boy", electrician="Ari", electrician_gender="woman",
                    parent="mother"),
    ]

    if args.all:
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            seed = base_seed + i
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
