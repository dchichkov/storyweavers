#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/universe_porpoise_orange_moral_value_superhero_story.py
======================================================================================

A standalone storyworld about a tiny superhero rescue in a bright universe:
a porpoise is protecting an orange, a moral choice matters, and the ending
proves what changed.

The world is intentionally small. It uses typed entities with physical meters
and emotional memes, a simple forward rule engine, a Python reasonableness gate,
and an inline ASP twin for parity checks.
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
MORAL_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "dad", "hero"}
        female = {"girl", "woman", "mother", "mom", "heroine"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    name: str
    sky: str
    has_space: bool = True
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


@dataclass
class Threat:
    id: str
    label: str
    danger: str
    damage: str
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
class MoralChoice:
    id: str
    value: str
    reason: str
    rescue: str
    lesson: str
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
class Power:
    id: str
    label: str
    action: str
    aura: str
    power: int
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    orange = world.get("orange")
    if orange.meters["trapped"] < THRESHOLD:
        return out
    sig = ("worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in list(world.entities.values()):
        if e.role in {"hero", "helper"}:
            e.memes["worry"] += 1
    out.append("__worry__")
    return out


def _r_shine(world: World) -> list[str]:
    out: list[str] = []
    if world.get("orange").meters["safe"] >= THRESHOLD:
        sig = ("shine",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("hero").memes["hope"] += 1
            out.append("__shine__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("shine", _r_shine)]


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


def is_reasonable(setting: Setting, threat: Threat, choice: MoralChoice) -> bool:
    return setting.has_space and "moral_value" in choice.tags and "universe" in threat.tags


def rescue_strength(power: Power) -> int:
    return power.power


def needed_strength(threat: Threat, delay: int) -> int:
    return 2 + delay


def success(power: Power, threat: Threat, delay: int) -> bool:
    return rescue_strength(power) >= needed_strength(threat, delay)


def predict(world: World, delay: int) -> dict:
    sim = world.copy()
    sim.get("orange").meters["trapped"] += 1
    propagate(sim, narrate=False)
    return {"worried": sim.get("hero").memes["worry"] >= THRESHOLD, "delay": delay}


def setup(world: World, setting: Setting, hero: Entity, helper: Entity, orange: Entity) -> None:
    hero.memes["courage"] = 2.0
    helper.memes["care"] = 2.0
    world.say(
        f"In the {setting.name}, the sky glowed {setting.sky}, and the whole universe "
        f"felt wide open."
    )
    world.say(
        f"{hero.id} and {helper.id} watched an orange float near a crack in the star-gate."
    )
    world.say(
        f'\"We have to save the orange,\" {hero.id} said. \"A hero should protect what is '
        f'small and helpless.\"'
    )


def tempt(world: World, threat: Threat, hero: Entity, orange: Entity) -> None:
    hero.memes["impulse"] += 1
    world.say(
        f"Then {threat.label} rolled in, grinning at the orange and daring {hero.id} "
        f"to leave it behind."
    )
    world.say(
        f"{hero.id} clenched {hero.pronoun('possessive')} fists. The orange wobbled in the wind."
    )


def warn(world: World, helper: Entity, hero: Entity, choice: MoralChoice, orange: Entity, delay: int) -> None:
    pred = predict(world, delay)
    helper.memes["wisdom"] += 1
    world.facts["predicted_worry"] = pred["worried"]
    world.say(
        f"{helper.id} shook {helper.pronoun('possessive')} head. "
        f'\"{choice.reason},\" {helper.id} said. \"If we wait, the orange could get hurt.\"'
    )


def choose_good(world: World, hero: Entity, helper: Entity, choice: MoralChoice, orange: Entity) -> None:
    hero.memes["moral_value"] += 1
    orange.meters["safe"] += 1
    world.say(
        f"{hero.id} took a breath and chose the kinder path. {choice.lesson}."
    )
    world.say(
        f"Together they followed {choice.rescue}, and the orange slipped into safe hands."
    )


def rescue(world: World, power: Power, threat: Threat, orange: Entity, delay: int) -> None:
    if success(power, threat, delay):
        orange.meters["trapped"] = 0.0
        orange.meters["safe"] += 1
        world.get("hero").memes["pride"] += 1
        world.say(
            f"{world.get('hero').id} used {power.label} to {power.action}. "
            f"{power.aura} flashed, and the danger let go."
        )
        world.say(
            "The orange tumbled free, bright as a little sunrise."
        )
    else:
        orange.meters["trapped"] += 1
        world.get("hero").memes["fear"] += 1
        world.say(
            f"{world.get('hero').id} tried {power.label}, but the danger stayed too strong."
        )
        world.say(
            f"The orange stayed stuck while the stormy crack grew wider."
        )


def ending(world: World, hero: Entity, helper: Entity, orange: Entity, moral: MoralChoice) -> None:
    world.say(
        f"At the end, {hero.id} and {helper.id} stood under the stars with the orange "
        f"safe beside them."
    )
    world.say(
        f'{moral.value.capitalize()} mattered more than speed, and that was the real superhero win.'
    )


def tell(setting: Setting, threat: Threat, choice: MoralChoice, power: Power, delay: int = 0) -> World:
    world = World()
    hero = world.add(Entity(id="Nova", kind="character", type="hero", role="hero"))
    helper = world.add(Entity(id="Beacon", kind="character", type="hero", role="helper"))
    orange = world.add(Entity(id="orange", kind="thing", type="thing", label="orange"))
    world.add(Entity(id="universe", kind="thing", type="thing", label="universe"))
    setup(world, setting, hero, helper, orange)
    world.para()
    tempt(world, threat, hero, orange)
    warn(world, helper, hero, choice, orange, delay)
    if choice.id == "help_first":
        choose_good(world, hero, helper, choice, orange)
    else:
        hero.memes["moral_value"] += 1
        orange.meters["trapped"] += 1
        world.say(f"{hero.id} chose to help first anyway, because doing the right thing felt important.")
        rescue(world, power, threat, orange, delay)
    world.para()
    ending(world, hero, helper, orange, choice)
    world.facts.update(
        hero=hero, helper=helper, orange=orange, setting=setting, threat=threat,
        choice=choice, power=power, delay=delay, succeeded=orange.meters["safe"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "city": Setting(id="city", name="Sky Harbor City", sky="orange"),
    "orbit": Setting(id="orbit", name="Orbit Station", sky="silver"),
    "reef": Setting(id="reef", name="Coral Reef Dome", sky="blue"),
}

THREATS = {
    "space_rift": Threat(id="space_rift", label="a space rift", danger="rift", damage="pull apart", tags={"universe"}),
    "dark_cloud": Threat(id="dark_cloud", label="a dark cloud", danger="cloud", damage="swallow", tags={"universe"}),
}

CHOICES = {
    "help_first": MoralChoice(
        id="help_first",
        value="Kindness comes first",
        reason="Helping the orange is the brave thing to do",
        rescue="a careful rope, a bright signal, and a steady hand",
        lesson="Nova remembered that a true hero helps first",
        tags={"moral_value"},
    ),
    "tell_truth": MoralChoice(
        id="tell_truth",
        value="Truth matters",
        reason="The best heroes tell the truth before trouble grows",
        rescue="Beacon's honest warning",
        lesson="Nova remembered that honesty keeps everyone safer",
        tags={"moral_value"},
    ),
}

POWERS = {
    "sunbeam": Power(id="sunbeam", label="sunbeam shield", action="lift the orange free", aura="A warm beam", power=3, tags={"shield"}),
    "bubble": Power(id="bubble", label="bubble lift", action="carry the orange clear", aura="A round bubble", power=2, tags={"shield"}),
}

GIRL_NAMES = ["Nova", "Iris", "Mira", "Zara"]
BOY_NAMES = ["Atlas", "Leo", "Kai", "Finn"]


@dataclass
class StoryParams:
    setting: str
    threat: str
    choice: str
    power: str
    delay: int = 0
    hero_name: str = "Nova"
    hero_gender: str = "girl"
    helper_name: str = "Beacon"
    helper_gender: str = "boy"
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for tid in THREATS:
            for cid in CHOICES:
                if is_reasonable(SETTINGS[sid], THREATS[tid], CHOICES[cid]):
                    combos.append((sid, tid, cid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny superhero storyworld with a moral choice.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.choice and args.choice not in CHOICES:
        raise StoryError("Unknown moral choice.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.threat is None or c[1] == args.threat)
              and (args.choice is None or c[2] == args.choice)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, threat, choice = rng.choice(sorted(combos))
    power = args.power or rng.choice(sorted(POWERS))
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    hero_name = rng.choice(GIRL_NAMES)
    helper_name = rng.choice(BOY_NAMES)
    return StoryParams(setting=setting, threat=threat, choice=choice, power=power, delay=delay, hero_name=hero_name, helper_name=helper_name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story that includes the words "universe", "porpoise", and "orange".',
        f"Tell a kid-friendly superhero tale where {f['hero'].id} protects an orange in the universe and makes a moral choice.",
        f"Write a bright rescue story about a porpoise helper, an orange, and a hero who chooses kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, orange, choice, threat = f["hero"], f["helper"], f["orange"], f["choice"], f["threat"]
    qa = [
        QAItem(question="Who is the story about?", answer=f"It is about {hero.id}, {helper.id}, and the orange they worked to protect."),
        QAItem(question="What problem did they face?", answer=f"They faced {threat.label}, which threatened the orange and made the rescue important."),
        QAItem(question="What moral value mattered in the story?", answer=f"{choice.value}. {choice.lesson}"),
        QAItem(question="How did the story end?", answer="The orange ended up safe under the stars, and the heroes ended with a calm, glowing victory."),
    ]
    if orange.meters["safe"] >= THRESHOLD:
        qa.append(QAItem(question="Why was the ending happy?", answer="The heroes chose the good path and used their powers to keep the orange safe. That changed the final image from danger to safety."))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a porpoise?", answer="A porpoise is a sea animal related to dolphins. It swims fast and likes the water."),
        QAItem(question="What is an orange?", answer="An orange is a round fruit. It is sweet, juicy, and bright in color."),
        QAItem(question="What does the universe mean?", answer="The universe is everything that exists, including stars, planets, and all the space between them."),
        QAItem(question="What is a moral value?", answer="A moral value is a good rule for how to treat others, like kindness, honesty, and helping someone in need."),
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
    StoryParams(setting="city", threat="space_rift", choice="help_first", power="sunbeam", delay=0, hero_name="Nova", hero_gender="girl", helper_name="Poro", helper_gender="boy"),
    StoryParams(setting="orbit", threat="dark_cloud", choice="tell_truth", power="bubble", delay=1, hero_name="Mira", hero_gender="girl", helper_name="Poro", helper_gender="boy"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in THREATS.items():
        lines.append(asp.fact("threat", tid))
        if "universe" in t.tags:
            lines.append(asp.fact("universe_threat", tid))
    for cid, c in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        if "moral_value" in c.tags:
            lines.append(asp.fact("moral_value_choice", cid))
    for pid, p in POWERS.items():
        lines.append(asp.fact("power", pid))
        lines.append(asp.fact("strength", pid, p.power))
    lines.append(asp.fact("moral_min", int(MORAL_MIN)))
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(S,T,C) :- setting(S), threat(T), choice(C), universe_threat(T), moral_value_choice(C).
strong(P) :- power(P), strength(P,X), X >= 2.
outcome(success) :- chosen_power(P), chosen_threat(T), strong(P), universe_threat(T).
"""


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in ASP gate.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, threat=None, choice=None, power=None, delay=None), random.Random(7)))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.threat not in THREATS or params.choice not in CHOICES or params.power not in POWERS:
        raise StoryError("Invalid story parameters.")
    setting = SETTINGS[params.setting]
    threat = THREATS[params.threat]
    choice = CHOICES[params.choice]
    power = POWERS[params.power]
    if not is_reasonable(setting, threat, choice):
        raise StoryError("This combination is not a reasonable superhero story.")
    world = tell(setting, threat, choice, power, delay=params.delay)
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


def resolve_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show reasonable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} reasonable combos:")
        for item in combos:
            print(item)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
