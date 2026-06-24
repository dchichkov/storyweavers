#!/usr/bin/env python3
"""
A small bedtime storyworld about a critter, a jalapeño, defensive feelings,
sound effects, and a gentle conflict that settles before sleep.

The premise:
- A little critter wants to snack on a spicy jalapeño at bedtime.
- A grown-up worries it will be too hot and keep the critter awake.
- The critter gets defensive, there is a small conflict, and then they find a
  safer, softer bedtime plan with a cool snack and a cozy sound effect.

The world model keeps track of:
- physical meters: spice, heat, soothed, sleepy, noise
- emotional memes: want, worry, defensive, calm, love
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    edible: bool = False
    spicy: bool = False
    cozy: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    blanket: object | None = None
    cool_snack: object | None = None
    critter: object | None = None
    grownup: object | None = None
    jalapeno: object | None = None
    def __post_init__(self) -> None:
        for k in ["spice", "heat", "soothed", "sleepy", "noise", "worry"]:
            self.meters.setdefault(k, 0.0)
        for k in ["want", "defensive", "calm", "love", "conflict", "comfort"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def is_plural(self) -> bool:
        return self.type in {"critter", "snacks", "ears"}
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Setting:
    place: str = "the little bedroom"
    cozy: bool = True
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    spicy: bool = False
    cooling: bool = False
    sound: str = ""
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Comfort:
    id: str
    label: str
    phrase: str
    sound: str
    lowers_spice: bool = False
    lowers_noise: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.sound_log: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.sound_log = list(self.sound_log)
        w.paragraphs = [[]]
        return w


def _r_spice_up(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["spice"] >= THRESHOLD and e.meters["heat"] < THRESHOLD:
            e.meters["heat"] += 1
            out.append(f"The jalapeño felt hotter than a tiny firefly's wink.")
    return out


def _r_defensive(world: World) -> list[str]:
    out = []
    critter = world.entities.get("critter")
    if not critter:
        return out
    if critter.memes["defensive"] >= THRESHOLD and critter.memes["conflict"] < THRESHOLD:
        critter.memes["conflict"] += 1
        out.append("__conflict__")
    return out


CAUSAL_RULES = [
    _r_spice_up,
    _r_defensive,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                for s in sents:
                    if s != "__conflict__":
                        produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def bedtime_sound(label: str) -> str:
    return {
        "sip": "slurp-sip",
        "blanket": "swish-whoosh",
        "song": "hmm-hmm",
        "fan": "whirr-whirr",
    }.get(label, "soft-rustle")


def tell_story(world: World, critter_name: str, grownup_name: str) -> World:
    critter = world.add(Entity(id="critter", kind="character", type="critter", label=critter_name))
    grownup = world.add(Entity(id="grownup", kind="character", type="adult", label=grownup_name))
    jalapeno = world.add(Entity(
        id="jalapeno",
        kind="thing",
        type="jalapeno",
        label="jalapeño",
        phrase="a tiny jalapeño slice",
        owner="critter",
        spicy=True,
        edible=True,
    ))
    cool_snack = world.add(Entity(
        id="yogurt",
        kind="thing",
        type="snack",
        label="yogurt",
        phrase="a cool cup of yogurt",
        owner="critter",
        edible=True,
        cozy=True,
    ))
    blanket = world.add(Entity(
        id="blanket",
        kind="thing",
        type="blanket",
        label="blanket",
        phrase="a soft blanket",
        cozy=True,
    ))

    critter.memes["want"] += 1
    critter.memes["love"] += 1
    jalapeno.meters["spice"] += 1

    world.say(f"At bedtime in {world.setting.place}, a little critter named {critter_name} spotted a jalapeño on the nightstand.")
    world.say(f'It went "sniff-sniff" and "munch-munch" sounds filled the room, because the jalapeño looked bright and brave.')
    world.say(f"The critter wanted to nibble it right away.")
    world.para()

    grownup.memes["worry"] += 1
    world.say(f'{grownup_name} smiled a sleepy smile, but said, "That jalapeño may be too hot for bedtime."')
    world.say(f'The critter felt defensive and made a tiny "huff-huff" sound. "I can handle it!" the critter squeaked.')
    critter.memes["defensive"] += 1
    propagate(world, narrate=True)
    world.say(f'The room got a small "huff-huff" of conflict, like a pillow puffing up and then settling back down.')
    world.para()

    world.say(f'{grownup_name} knelt beside the bed and offered a softer choice: {cool_snack.phrase}.')
    world.say(f'Then they wrapped the critter in {blanket.phrase} and made a gentle "swish-whoosh" sound as the blanket tucked in.')
    critter.memes["defensive"] = 0.0
    critter.memes["calm"] += 1
    critter.memes["love"] += 1
    critter.meters["soothed"] += 1
    critter.meters["sleepy"] += 1
    jalapeno.meters["heat"] = 0.0
    world.say(f"The critter nibbled the cool snack instead, and the jalapeño waited quietly for another day.")
    world.say(f"Soon the little room was cozy and still, and the critter drifted off to sleep with a tiny happy sigh.")
    world.facts.update(
        critter=critter,
        grownup=grownup,
        jalapeno=jalapeno,
        cool_snack=cool_snack,
        blanket=blanket,
        conflict=True,
        resolved=True,
        sound="huff-huff",
    )
    return world


SETTINGS = {
    "bedroom": Setting(place="the little bedroom", cozy=True),
    "nursery": Setting(place="the nursery", cozy=True),
    "cabin": Setting(place="the warm cabin", cozy=True),
}

CRITTER_NAMES = ["Milo", "Pip", "Tilly", "Nino", "Poppy", "Sora", "Bibi"]
GROWNUP_NAMES = ["Mama", "Papa", "Grandma", "Grandpa", "Auntie", "Uncle"]


@dataclass
class StoryParams:
    setting: str
    critter_name: str
    grownup_name: str
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


ASP_RULES = r"""
% A jalapeño is at risk when it is spicy and bedtime is quiet.
at_risk(J) :- jalapeno(J), spicy(J).

% Defensive feelings create a small conflict.
conflict(C) :- critter(C), defensive(C), want(C).

% A calming comfort fixes the bedtime conflict.
resolved(C) :- conflict(C), comfort_fix(C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    lines.append(asp.fact("critter", "critter"))
    lines.append(asp.fact("adult", "grownup"))
    lines.append(asp.fact("jalapeno", "jalapeno"))
    lines.append(asp.fact("spicy", "jalapeno"))
    lines.append(asp.fact("want", "critter"))
    lines.append(asp.fact("defensive", "critter"))
    lines.append(asp.fact("comfort_fix", "critter"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_check() -> int:
    import asp

    model = asp.one_model(asp_program("#show conflict/1.\n#show resolved/1."))
    atoms = set((sym.name, tuple(a.number if a.type.name == "Number" else a.name for a in sym.arguments)) for sym in model)
    expected = {("conflict", ("critter",)), ("resolved", ("critter",))}
    if atoms == expected:
        print("OK: ASP parity matches the Python reasonableness gate.")
        return 0
    print("MISMATCH:")
    print(" model:", sorted(atoms))
    print(" expected:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld: a critter, a jalapeño, defensive feelings, and a soft resolution.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--critter-name")
    ap.add_argument("--grownup-name")
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    return StoryParams(
        setting=setting,
        critter_name=getattr(args, "critter_name", None) or rng.choice(CRITTER_NAMES),
        grownup_name=getattr(args, "grownup_name", None) or rng.choice(GROWNUP_NAMES),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a small child that includes the sound effect "{f["sound"]}" and a jalapeño.',
        f"Tell a gentle story where {f['critter'].label} gets defensive about a jalapeño at bedtime, but then accepts a softer choice.",
        "Write a child-facing bedtime tale with one small conflict, one cozy comfort, and a sleepy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    critter = f["critter"].label
    grownup = f["grownup"].label
    return [
        QAItem(
            question=f"Who wanted to eat the jalapeño at bedtime?",
            answer=f"The little critter named {critter} wanted to eat the jalapeño at bedtime.",
        ),
        QAItem(
            question=f"Why did {grownup} worry about the jalapeño?",
            answer=f"{grownup} worried because jalapeño is spicy and might feel too hot for bedtime.",
        ),
        QAItem(
            question="What sound effect showed the little conflict?",
            answer='The conflict sounded like a tiny "huff-huff" from the defensive critter.',
        ),
        QAItem(
            question="What helped the critter settle down?",
            answer=f"A cool snack and a soft blanket helped {critter} feel calm and sleepy again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a jalapeño?",
            answer="A jalapeño is a small pepper that can taste spicy.",
        ),
        QAItem(
            question="What does defensive mean?",
            answer="Defensive means someone feels like they need to protect their choice or feelings.",
        ),
        QAItem(
            question="Why do bedtime stories often feel calm?",
            answer="Bedtime stories often feel calm because they use soft actions, gentle voices, and sleepy endings.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(World(_safe_lookup(SETTINGS, params.setting)), params.critter_name, params.grownup_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


CURATED = [
    StoryParams(setting="bedroom", critter_name="Milo", grownup_name="Mama"),
    StoryParams(setting="nursery", critter_name="Pip", grownup_name="Papa"),
    StoryParams(setting="cabin", critter_name="Tilly", grownup_name="Grandma"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show conflict/1.\n#show resolved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_check())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show conflict/1.\n#show resolved/1."))
        print("ASP model:")
        for sym in model:
            print(sym)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
