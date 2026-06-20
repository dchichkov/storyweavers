#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dejected_mutton_boo_happy_ending_superhero_story.py
===================================================================================

A standalone storyworld for a tiny superhero rescue tale with a happy ending.
It keeps the tone close to a classic superhero story: a child hero feels
dejected, a misunderstood mutton truck causes trouble, a boo from the crowd
turns into a cheer, and the day ends with a bright, safe win.

Seed words: dejected, mutton, boo
Features: Happy Ending
Style: Superhero Story
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
    scene: str
    dark_spot: str
    public: bool = True

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
class Threat:
    id: str
    label: str
    noise: str
    mess: str
    spreads: bool = False
    harmless_misunderstanding: bool = False

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
class Tool:
    id: str
    label: str
    phrase: str
    glow: str
    plural: bool = False

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
class Rescue:
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
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


def _r_dejected(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    if hero.memes["dejection"] < THRESHOLD:
        return out
    sig = ("dejected", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["hope"] += 1
    out.append("__dejected__")
    return out


def _r_mess(world: World) -> list[str]:
    out = []
    threat = world.get("threat")
    hero = world.get("hero")
    if threat.meters["trouble"] < THRESHOLD:
        return out
    sig = ("mess", threat.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] += 1
    out.append("__mess__")
    return out


CAUSAL_RULES = [Rule("dejected", "social", _r_dejected), Rule("mess", "physical", _r_mess)]


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


def threat_at_risk(threat: Threat) -> bool:
    return not threat.harmless_misunderstanding


def sensible_rescues() -> list[Rescue]:
    return [r for r in RESCUES.values() if r.sense >= 2]


def fire_like_severity(threat: Threat, delay: int) -> int:
    return 1 + delay + (1 if threat.spreads else 0)


def is_resolved(rescue: Rescue, threat: Threat, delay: int) -> bool:
    return rescue.power >= fire_like_severity(threat, delay)


def setup(world: World, hero: Entity, sidekick: Entity, setting: Setting, threat: Threat) -> None:
    hero.memes["dejection"] = 1.0
    sidekick.memes["loyalty"] = 1.0
    world.say(
        f"On a bright afternoon, {hero.id} and {sidekick.id} stood at {setting.place}. "
        f"{setting.scene}"
    )
    world.say(
        f"{hero.id} was a little superhero, but {hero.pronoun()} felt dejected because "
        f"the day had gone wrong."
    )
    world.say(
        f"Then a strange rumble came from {setting.dark_spot}, and everyone looked up."
    )


def discover(world: World, sidekick: Entity, threat: Threat) -> None:
    world.say(
        f'"Boo?" {sidekick.id} asked, peeking toward the noise. '
        f'It sounded like {threat.noise}, not like a real villain.'
    )
    world.say(
        f"{sidekick.id} pointed at the crates and laughed. \"I think it's only {threat.label}.\""
    )


def worry(world: World, hero: Entity, threat: Threat) -> None:
    hero.memes["dejection"] += 1
    hero.memes["courage"] += 1
    world.say(
        f"{hero.id} straightened {hero.pronoun('possessive')} cape, took a breath, "
        f"and said the whole block was in danger."
    )
    world.say(
        f"For one shaky moment, {hero.id} thought {threat.label} might ruin everything."
    )


def take_action(world: World, hero: Entity, threat: Threat) -> None:
    threat.meters["trouble"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} rushed in and lifted the cover from the pile. The noise was only "
        f"{threat.label} rattling in a delivery cart."
    )


def reveal(world: World, threat: Threat) -> None:
    threat.meters["trouble"] = 0.0
    world.say(
        f"Under the cover was a crate of mutton for the soup kitchen, and the thunking "
        f"sound had been its wheels bumping the curb."
    )
    world.say(
        f"It was never a monster at all -- just a hungry delivery needing help."
    )


def happy_turn(world: World, hero: Entity, sidekick: Entity, tool: Tool) -> None:
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    hero.memes["dejection"] = 0.0
    world.say(
        f'Then {sidekick.id} grinned and called, "Boo!" in the friendly way, and the street '
        f'answered with cheers.'
    )
    world.say(
        f"{hero.id} clicked on {tool.phrase}, which {tool.glow}, and guided the cart into the light."
    )


def ending(world: World, hero: Entity, sidekick: Entity, tool: Tool) -> None:
    hero.memes["pride"] += 1
    sidekick.memes["pride"] += 1
    world.say(
        f"By sunset, {hero.id} was smiling again. {hero.id} and {sidekick.id} rolled "
        f"the mutton to the shelter, and the whole crowd cheered a warm, happy boo."
    )
    world.say(
        f"The little superhero lifted {tool.label} high, and the town glowed safe and bright."
    )


def tell(setting: Setting, threat: Threat, tool: Tool,
         hero_name: str = "Nova", hero_gender: str = "girl",
         sidekick_name: str = "Bix", sidekick_gender: str = "boy",
         delay: int = 0) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type=sidekick_gender, role="sidekick"))
    world.add(Entity(id="threat", type="thing", label=threat.label))
    setup(world, hero, sidekick, setting, threat)
    world.para()
    discover(world, sidekick, threat)
    worry(world, hero, threat)
    if not threat_at_risk(threat):
        world.say("But it was only a harmless mistake, so no rescue was needed.")
    else:
        take_action(world, hero, threat)
        if is_resolved(RESCUES["beam"], threat, delay):
            reveal(world, threat)
            world.para()
            happy_turn(world, hero, sidekick, tool)
            ending(world, hero, sidekick, tool)
    world.facts.update(
        hero=hero, sidekick=sidekick, setting=setting, threat=threat, tool=tool,
        delay=delay, resolved=True, outcome="happy"
    )
    return world


SETTINGS = {
    "city": Setting("city", "the city square", "Tall buildings wrapped the square like friendly giants.", "the covered market"),
    "harbor": Setting("harbor", "the harbor pier", "Boats rocked in the water while gulls cried overhead.", "the old supply crate"),
    "park": Setting("park", "the park", "Trees made a cool green tunnel beside the path.", "the picnic shelter"),
}

THREATS = {
    "mutton_cart": Threat("mutton_cart", "mutton", "a clatter-clump, clatter-clump", "a crate of mutton", spreads=False, harmless_misunderstanding=False),
    "boo_echo": Threat("boo_echo", "boo", "a long boo-o-o in the wind", "a birthday boo banner", spreads=False, harmless_misunderstanding=False),
    "shadow": Threat("shadow", "shadow", "a soft boo from behind the bins", "a shadowy tarp", spreads=False, harmless_misunderstanding=False),
}

TOOLS = {
    "lantern": Tool("lantern", "lantern", "the lantern", "glowed gold like a tiny sun"),
    "beacon": Tool("beacon", "signal beacon", "the signal beacon", "blinked bright and blue"),
    "flashlight": Tool("flashlight", "flashlight", "the flashlight", "shone silver and steady"),
}

RESCUES = {
    "beam": Rescue("beam", 3, 3, "swung the beam across the street until the way was clear",
                   "waved the beam too late to help", "used a beam of light to clear the street"),
    "lift": Rescue("lift", 2, 2, "lifted the cover and showed everyone the harmless crate beneath",
                   "tried to lift it, but the crowd was too shaky", "lifted the cover and found the crate"),
}

HERO_NAMES = ["Nova", "Ivy", "Mina", "Pip", "Rae"]
SIDEKICK_NAMES = ["Bix", "Tess", "Jo", "Max", "Zed"]
TRAITS = ["brave", "kind", "curious", "steady", "hopeful"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    threat: str
    tool: str
    hero_name: str
    hero_gender: str
    sidekick_name: str
    sidekick_gender: str
    trait: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid in THREATS:
            for uid in TOOLS:
                if threat_at_risk(THREATS[tid]):
                    combos.append((sid, tid, uid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a 3-to-5-year-old that includes the words "dejected", "{f["threat"].label}", and "boo", and ends happily.',
        f"Tell a short superhero story where {f['hero'].id} starts dejected, hears a boo in the distance, and discovers {f['threat'].label} is not a real danger.",
        f"Write a bright, child-friendly rescue story set in {f['setting'].place} with a happy ending and a gentle crowd cheer.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    threat = f["threat"]
    tool = f["tool"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id}, a little superhero, and {sidekick.id}, who stayed beside {hero.id} when the day felt hard."),
        (f"Why was {hero.id} dejected?",
         f"{hero.id} felt dejected because the day had gone wrong and the strange noise sounded like trouble. The worry made {hero.id} think a rescue was needed before the truth was clear."),
        (f"What did the boo sound like?",
         f"The boo was friendly, not scary. It turned out to be part of the cheer and the joke that helped everyone relax."),
    ]
    if f["outcome"] == "happy":
        qa.append((
            f"What was {threat.label} really?",
            f"It was really a crate of {threat.label} for the soup kitchen, not a villain at all. The noisy bumping just made it sound bigger than it was."
        ))
        qa.append((
            "How did the story end?",
            f"It ended happily, with {hero.id} smiling again and the crowd cheering. The town was safe, the delivery was helped along, and the little superhero felt proud."
        ))
        qa.append((
            f"What did {hero.id} use to help?",
            f"{hero.id} used {tool.phrase} because it {tool.glow}. That light helped guide the cart and made the street feel calm again."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = [
        ("What does a superhero do?",
         "A superhero helps people, solves problems, and tries to keep everyone safe."),
        ("What is mutton?",
         "Mutton is meat from a grown sheep, often used in soup or stew."),
        ("What is a boo?",
         "A boo can be a spooky sound, but it can also be a silly cheer when people mean it kindly."),
        ("What is a lantern?",
         "A lantern is a light that glows brightly so people can see in the dark."),
    ]
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
    StoryParams("city", "mutton_cart", "flashlight", "Nova", "girl", "Bix", "boy", "brave", 0),
    StoryParams("harbor", "boo_echo", "lantern", "Ivy", "girl", "Tess", "girl", "hopeful", 0),
    StoryParams("park", "shadow", "beacon", "Pip", "boy", "Jo", "boy", "steady", 0),
]


def explain_rejection(threat: Threat) -> str:
    if threat.harmless_misunderstanding:
        return "(No story: that threat is too harmless to drive a superhero rescue.)"
    return "(No story: this setup does not support a clear superhero-style happy ending.)"


def outcome_of(params: StoryParams) -> str:
    return "happy"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in THREATS.items():
        lines.append(asp.fact("threat", tid))
        if t.spreads:
            lines.append(asp.fact("spreads", tid))
    for uid in TOOLS:
        lines.append(asp.fact("tool", uid))
    for rid, r in RESCUES.items():
        lines.append(asp.fact("rescue", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, T, U) :- setting(S), threat(T), tool(U).
happy(T) :- threat(T), not harmless(T).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos()")
    # smoke test ordinary generation
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        assert sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny superhero storyworld with a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--sidekick-name")
    ap.add_argument("--sidekick-gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=["brave", "kind", "curious", "steady", "hopeful"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
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
    if args.threat and args.threat not in THREATS:
        raise StoryError("Unknown threat.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.threat is None or c[1] == args.threat)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, threat, tool = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    sidekick_gender = args.sidekick_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    sidekick_name = args.sidekick_name or rng.choice([n for n in SIDEKICK_NAMES if n != hero_name])
    trait = args.trait or rng.choice(TRAITS)
    delay = 0 if args.delay is None else args.delay
    return StoryParams(setting, threat, tool, hero_name, hero_gender, sidekick_name, sidekick_gender, trait, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], THREATS[params.threat], TOOLS[params.tool],
                 params.hero_name, params.hero_gender, params.sidekick_name, params.sidekick_gender,
                 params.delay)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, threat, tool) combos:")
        for c in combos:
            print("  ", c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
