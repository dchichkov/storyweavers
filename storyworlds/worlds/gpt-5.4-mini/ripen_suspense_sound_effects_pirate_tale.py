#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ripen_suspense_sound_effects_pirate_tale.py
============================================================================

A standalone story world about a small pirate crew, a ripening treasure fruit,
suspense, and sound effects.  The domain is deliberately tiny: children on a
dock or ship discover that a green prize needs time to ripen, hear ominous
sounds in the dark, wait for the right moment, and end with a satisfying
change in state.

The world is classical and state-driven: entities have physical meters and
emotional memes, the plot advances by mutating state, and the prose is rendered
from those changes.  The suspense beat is not just decorative; it is modeled as
a rising alert level, a noise source, and a final reveal.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/ripen_suspense_sound_effects_pirate_tale.py
    python storyworlds/worlds/gpt-5.4-mini/ripen_suspense_sound_effects_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/ripen_suspense_sound_effects_pirate_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/ripen_suspense_sound_effects_pirate_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/ripen_suspense_sound_effects_pirate_tale.py --verify
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
    ripe: bool = False
    noisy: bool = False
    hidden: bool = False

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
    dark_place: str
    smell: str
    cover: str
    deck_detail: str

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
class Fruit:
    id: str
    label: str
    phrase: str
    stage: str
    ripens_to: str
    hidden_spot: str
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
class SoundSource:
    id: str
    label: str
    sound: str
    meaning: str
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
    power: int
    sense: int
    text: str
    fail: str
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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_ripen(world: World) -> list[str]:
    out: list[str] = []
    time = world.get("time")
    fruit = world.get("fruit")
    if time.meters["waiting"] < THRESHOLD:
        return out
    sig = ("ripen",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    fruit.ripe = True
    fruit.meters["ripeness"] = 1.0
    fruit.label = "ripe mango"
    out.append("The fruit turned ripe at last.")
    return out


def _r_noisy_alarm(world: World) -> list[str]:
    out: list[str] = []
    if world.get("sound").meters["noise"] < THRESHOLD:
        return out
    sig = ("alarm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.characters():
        kid.memes["fear"] += 1
    out.append("__alarm__")
    return out


CAUSAL_RULES = [
    Rule("ripen", _r_ripen),
    Rule("alarm", _r_noisy_alarm),
]


def hazard_level(world: World) -> float:
    return world.get("sound").meters["noise"]


def is_reasonable_sound(sound: SoundSource) -> bool:
    return sound.sense >= 2


def tell(setting: Setting, fruit_cfg: Fruit, sound_cfg: SoundSource, response: Response,
         hero_name: str, hero_gender: str, mate_name: str, mate_gender: str,
         parent_gender: str, delay: int = 1) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    mate = world.add(Entity(id=mate_name, kind="character", type=mate_gender, role="mate"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_gender, role="parent", label="the parent"))
    fruit = world.add(Entity(id="fruit", type="fruit", label=fruit_cfg.label, attrs={"stage": fruit_cfg.stage}))
    sound = world.add(Entity(id="sound", type="sound", label=sound_cfg.label, noisy=True))
    time = world.add(Entity(id="time", type="time", label="the clock"))

    hero.memes["curiosity"] = 1.0
    mate.memes["caution"] = 1.0
    world.facts["setting"] = setting
    world.facts["fruit_cfg"] = fruit_cfg
    world.facts["sound_cfg"] = sound_cfg
    world.facts["response"] = response
    world.facts["hero"] = hero
    world.facts["mate"] = mate
    world.facts["parent"] = parent
    world.facts["fruit"] = fruit
    world.facts["sound"] = sound
    world.facts["delay"] = delay

    world.say(
        f"On a moonlit night aboard a little pirate ship, {hero.id} and {mate.id} "
        f"watched the deck {setting.deck_detail}. {setting.scene}"
    )
    world.say(
        f"Near {setting.dark_place}, they had hidden {fruit_cfg.phrase}. It was still "
        f"{fruit_cfg.stage}, and they wanted it to {fruit_cfg.ripens_to} before dawn."
    )
    world.para()
    world.say(
        f"Then came a hush. {setting.smell} hung in the air, and the only thing "
        f"moving was the shadow under {setting.cover}."
    )
    world.say(
        f'"Did you hear that?" {mate.id} whispered. '
        f'"Shh," {hero.id} said, "wait. Sometimes treasure takes time to ripen."'
    )

    world.para()
    world.say(
        f"From the dark place came {sound_cfg.sound} -- {sound_cfg.meaning}. "
        f"The sound made both children look up fast."
    )
    world.get("sound").meters["noise"] += 1
    propagate(world, narrate=False)
    if delay > 0:
        world.get("time").meters["waiting"] += float(delay)
    propagate(world, narrate=False)

    if fruit.ripe:
        world.say(
            f"At last, the secret was clear: {fruit.label} had ripened to a sweet, "
            f"golden smell."
        )
        world.say(
            f"{hero.id} parted the leaves and found {fruit.label} gleaming there, "
            f"safe to eat at just the right moment."
        )
        world.para()
        world.say(
            f'"Aha!" laughed {mate.id}. "The spooky sound was only the wind, '
            f"and the fruit was ready after all."
        )
        world.say(
            f"They shared the fruit on the deck while the stars blinked above the mast."
        )
    else:
        world.say(
            f"The hidden fruit still was not ready, so they did not touch it. "
            f"Instead they waited, listening to the dark."
        )
        world.say(
            f"{parent.label_word.capitalize()} came softly to the hatch, smiled, and "
            f"{response.text}."
        )
        world.say(
            f"In the end, the crew learned that patience keeps a pirate's treasure "
            f"better than any hurried grab."
        )

    world.facts.update(
        outcome="ripe" if fruit.ripe else "waited",
        waiting=world.get("time").meters["waiting"],
        noisy=world.get("sound").meters["noise"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "dock": Setting("dock", "The lanterns swayed on the dock, and the small ship rocked gently.", "the cargo crate", "salt", "the sailcloth", "the mast"),
    "ship": Setting("ship", "The lanterns swayed on the deck, and the small ship rocked gently.", "the cargo crate", "salt", "the sailcloth", "the mast"),
}

FRUITS = {
    "mango": Fruit("mango", "green mango", "a green mango", "green", "ripen into a sweet mango", "in the old net", tags={"ripen", "fruit"}),
    "banana": Fruit("banana", "green banana bunch", "a green banana bunch", "green", "ripen into a sweet bunch", "in a hanging basket", tags={"ripen", "fruit"}),
}

SOUNDS = {
    "creak": SoundSource("creak", "creak", "creak-creak", "the mast was shifting in the wind", tags={"sound"}),
    "splash": SoundSource("splash", "splash", "splish-splash", "something moved in the water below", tags={"sound"}),
    "rattle": SoundSource("rattle", "rattle", "clink-rattle", "a loose box rattled near the rail", tags={"sound"}),
}

RESPONSES = {
    "wait": Response("wait", 3, 3, "waited patiently and watched the fruit without touching it", "tried to rush the fruit, but it was still hard and sour"),
    "peek": Response("peek", 2, 2, "peeked behind the crate and found the hidden fruit", "peeked too quickly and nearly tipped the crate over"),
    "call_parent": Response("call_parent", 4, 4, "called for the parent and together they checked the hiding place", "called, but the answer was lost in the wind"),
}

GIRL_NAMES = ["Mina", "Luna", "Nora", "Ivy", "Tess", "Ruby"]
BOY_NAMES = ["Finn", "Jace", "Oren", "Toby", "Kai", "Eli"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    fruit: str
    sound: str
    response: str
    hero: str
    hero_gender: str
    mate: str
    mate_gender: str
    parent_gender: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, f, so) for s in SETTINGS for f in FRUITS for so in SOUNDS if is_reasonable_sound(SOUNDS[so])]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale about ripening fruit and suspenseful sounds.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--fruit", choices=FRUITS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--mate")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2, 3])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.sound and not is_reasonable_sound(SOUNDS[args.sound]):
        raise StoryError("The sound source is too weak for a suspense story.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.fruit is None or c[1] == args.fruit)
              and (args.sound is None or c[2] == args.sound)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, fruit, sound = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    hero_gender = rng.choice(["girl", "boy"])
    mate_gender = "boy" if hero_gender == "girl" else "girl"
    hero = args.name or _pick_name(rng, hero_gender)
    mate = args.mate or _pick_name(rng, mate_gender, avoid=hero)
    parent_gender = args.parent or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 3)
    return StoryParams(setting, fruit, sound, response, hero, hero_gender, mate, mate_gender, parent_gender, delay)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    fruit_cfg = f["fruit_cfg"]
    sound_cfg = f["sound_cfg"]
    return [
        f'Write a pirate tale for a 3-to-5-year-old that includes the word "ripen" and the sound "{sound_cfg.sound}".',
        f"Tell a suspenseful pirate story where {hero.id} waits for {fruit_cfg.label} to ripen while a strange sound comes from the dark.",
        "Write a child-facing story with suspense and sound effects about a hidden fruit on a pirate ship."
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mate = f["mate"]
    fruit = f["fruit_cfg"]
    sound = f["sound_cfg"]
    resp = f["response"]
    out = [
        QAItem(
            question="What were the children waiting for?",
            answer=f"They were waiting for {fruit.phrase} to ripen. They wanted to find out when it would be sweet and ready."
        ),
        QAItem(
            question="Why did the story feel suspenseful?",
            answer=f"It felt suspenseful because the children heard {sound.sound} from the dark place and did not know what it meant at first. They had to stay calm and look carefully instead of rushing."
        ),
        QAItem(
            question=f"What did {hero.id} and {mate.id} do at the end?",
            answer=f"They waited patiently, listened to the strange sound, and then discovered the fruit was finally ready. The ending shows that waiting helped them get the treasure safely."
        ),
    ]
    if f["outcome"] == "ripe":
        out.append(QAItem(
            question="What changed by the end of the story?",
            answer=f"The fruit changed from green to ripe, so it was sweet and ready to eat. The scary sound turned out to be only the wind, so the children could relax."
        ))
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does ripen mean?", "Ripen means to change from hard or green into something ready to eat, usually sweeter and softer."),
        QAItem("What is suspense?", "Suspense is the feeling of waiting to find out what will happen next. It can make a story feel exciting and a little tense."),
        QAItem("Why do stories use sound effects?", "Sound effects help you imagine what the characters hear, like creaks, splashes, or rattles. They make the scene feel more alive."),
        QAItem("What is a pirate tale?", "A pirate tale is a story about sailors on ships, hidden treasure, maps, and bold adventures on the sea."),
    ]


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
        if e.ripe:
            bits.append("ripe=True")
        if e.noisy:
            bits.append("noisy=True")
        if e.hidden:
            bits.append("hidden=True")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], FRUITS[params.fruit], SOUNDS[params.sound], RESPONSES[params.response],
                 params.hero, params.hero_gender, params.mate, params.mate_gender, params.parent_gender, params.delay)
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


ASP_RULES = r"""
ripened :- waiting(T), T >= delay.
outcome(ripe) :- ripened.
outcome(waited) :- not ripened.
"""

def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("waiting", "time"))
    lines.append(asp.fact("delay", 1))
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for f in FRUITS:
        lines.append(asp.fact("fruit", f))
    for so in SOUNDS:
        lines.append(asp.fact("sound", so))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    # smoke test normal generation
    sample = generate(resolve_params(argparse.Namespace(setting=None, fruit=None, sound=None, response=None, name=None, mate=None, parent=None, delay=None), random.Random(1)))
    _ = sample.story
    model = asp.one_model(asp_program("", "#show outcome/1."))
    _ = asp.atoms(model, "outcome")
    print("OK: generation and ASP smoke test passed.")
    return 0


def build_parser_and_main():  # pragma: no cover
    pass


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("ship", "mango", "creak", "wait", "Mina", "girl", "Finn", "boy", "mother", 1),
            StoryParams("dock", "banana", "rattle", "call_parent", "Oren", "boy", "Ruby", "girl", "father", 2),
            StoryParams("ship", "mango", "splash", "peek", "Luna", "girl", "Toby", "boy", "mother", 3),
        ]
        samples = [generate(p) for p in curated]
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
