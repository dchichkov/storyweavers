#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/grapple_toll_emulate_flashback_magic_heartwarming.py
====================================================================================

A standalone story world for a small heartwarming magical domain.

Seeded premise:
- A child wants to cross a little magical toll bridge.
- They "grapple" with the toll because they lack the right token or are tempted to skip it.
- A caring guide recalls a flashback about a kinder lesson and helps them emulate it.
- Magic provides a gentle solution, not a cheat.
- The ending proves what changed: the toll is paid, the bridge glows, and the child
  learns to copy the kind example.

This script follows the storyworld contract:
- self-contained stdlib script
- imports storyworlds/results eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes a Python reasonableness gate and an inline ASP twin
- generates story-grounded QA from state, not by parsing the story text
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRIGHT = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    magic: bool = False
    tollkeeper: bool = False

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"warmth": 0.0, "spark": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "kindness": 0.0}

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
    name: str
    detail: str
    mood: str

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
class Toll:
    id: str
    label: str
    phrase: str
    payment: str
    magical: bool = True
    required_kindness: bool = True

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
class Guide:
    id: str
    name: str
    relation: str
    magic_word: str
    flashback_line: str
    emulate_line: str

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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone.facts = copy.deepcopy(self.facts)
        return clone

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
@dataclass
class StoryParams:
    setting: str
    toll: str
    guide: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
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


SETTINGS = {
    "moon_gate": Setting("moon_gate", "the moon gate", "a silver bridge beside a moonlit creek", "gentle"),
    "garden_bridge": Setting("garden_bridge", "the garden bridge", "a little arch over a singing stream", "cozy"),
    "lantern_path": Setting("lantern_path", "the lantern path", "a stone walk lined with glowing jars", "safe"),
}

TOLLS = {
    "glow_coin": Toll("glow_coin", "glow coin", "a glow coin", "a smile and one warm coin"),
    "song_pebble": Toll("song_pebble", "song pebble", "a song pebble", "a kind word and one bright pebble"),
    "kind_ticket": Toll("kind_ticket", "kind ticket", "a kind ticket", "a helpful deed and one soft ticket"),
}

GUIDES = {
    "grandma": Guide("grandma", "Grandma", "grandmother", "twinkle", 
                     "long ago, she had once turned back to help a lost child", 
                     "be brave, pay kindly, and cross together"),
    "aunt": Guide("aunt", "Aunt May", "aunt", "glimmer",
                  "she remembered a rainy afternoon when she had shared her last umbrella",
                  "copy the gentle thing and the path will feel lighter"),
    "brother": Guide("brother", "Big Brother", "older brother", "shine",
                     "he had once watched a smaller kid struggle and then helped without boasting",
                     "emulate the kind choice and keep everyone safe"),
}

GIRL_NAMES = ["Mina", "Luna", "Nora", "Ivy", "Zoe", "Ruby", "Maya"]
BOY_NAMES = ["Finn", "Theo", "Eli", "Noah", "Owen", "Leo", "Max"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TOLLS:
            for g in GUIDES:
                combos.append((s, t, g))
    return combos


def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.toll not in TOLLS:
        raise StoryError("Unknown toll.")
    if params.guide not in GUIDES:
        raise StoryError("Unknown guide.")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError("Child gender must be girl or boy.")
    if params.helper_gender not in {"girl", "boy"}:
        raise StoryError("Helper gender must be girl or boy.")


def pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def choose_resolve(rng: random.Random, args: argparse.Namespace) -> StoryParams:
    combos = [c for c in valid_combos()]
    if not combos:
        raise StoryError("No valid story combinations exist.")
    setting, toll, guide = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"]) if hasattr(args, "gender") else rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"]) if hasattr(args, "helper_gender") else rng.choice(["girl", "boy"])
    child = args.child or pick_name(rng, child_gender)
    helper = args.helper or pick_name(rng, helper_gender)
    if helper == child:
        helper = pick_name(rng, "boy" if child_gender == "girl" else "girl")
    return StoryParams(
        setting=args.setting or setting,
        toll=args.toll or toll,
        guide=args.guide or guide,
        child=child,
        child_gender=child_gender,
        helper=helper,
        helper_gender=helper_gender,
    )


def _do_grapple(world: World, child: Entity, toll: Toll) -> None:
    child.memes["worry"] += 1
    child.memes["kindness"] += 0.5
    child.meters["spark"] += 1
    world.say(
        f"{child.id} stopped at {world.setting.name} and stared at {toll.phrase}. "
        f"{child.pronoun().capitalize()} wanted to cross, but {toll.label} felt like a puzzle."
    )
    world.say(
        f"{child.id} had to grapple with the choice: go on the easy way, or do the kind thing and pay."
    )


def _flashback(world: World, guide: Entity, child: Entity, toll: Toll, setting: Setting) -> None:
    guide.memes["kindness"] += 1
    world.say(
        f"{guide.id} smiled softly. \"I remember something,\" {guide.pronoun()} said, "
        f"and a flashback warmed the air."
    )
    world.say(
        f"{guide.flashback_line.capitalize()}. Back then, {guide.id} had learned that "
        f"even a small payment could make a bridge feel like a promise kept."
    )
    world.facts["flashback"] = True
    world.facts["flashback_message"] = guide.flashback_line
    world.facts["setting_mood"] = setting.mood
    world.facts["toll_payment"] = toll.payment


def _emulate(world: World, child: Entity, guide: Entity, toll: Toll) -> None:
    child.memes["kindness"] += 1
    child.memes["joy"] += 1
    world.say(
        f"{child.id} looked at {guide.id} and decided to emulate {guide.pronoun('possessive')} gentle way."
    )
    world.say(
        f"{child.id} took out {toll.payment}, held it with both hands, and paid the toll honestly."
    )


def _magic_finish(world: World, child: Entity, helper: Entity, toll: Toll) -> None:
    child.meters["warmth"] += 1
    helper.meters["warmth"] += 1
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Then a little magic answered. The gate gave a bright hum, the bridge lights glowed, "
        f"and the tollkeeper smiled as the way opened."
    )
    world.say(
        f"{helper.id} walked beside {child.id}, and together they crossed the shining bridge, "
        f"feeling proud that they had chosen the kind way."
    )
    world.say(
        f"At the far end, {child.id} tucked away the memory, happy to have paid the toll and learned from it."
    )


def _tollkeeper_line(world: World, child: Entity, toll: Toll) -> None:
    keeper = world.get("keeper")
    keeper.memes["joy"] += 1
    world.say(
        f"{keeper.label_word.capitalize()} nodded. \"A toll is not just a fee,\" {keeper.pronoun()} said. "
        f"\"It is a little chance to show care.\""
    )


def tell(setting: Setting, toll: Toll, guide: Guide, child_name: str, child_gender: str,
         helper_name: str, helper_gender: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    g = world.add(Entity(id=guide.id, kind="character", type="woman" if guide.id != "brother" else "boy",
                         label=guide.name, role="guide"))
    keeper = world.add(Entity(id="keeper", kind="character", type="man", label="the tollkeeper", tollkeeper=True))
    world.facts.update(child=child, helper=helper, guide=g, keeper=keeper, setting=setting, toll=toll)

    world.say(
        f"On {setting.name}, {child.id} and {helper.id} came to a small bridge. "
        f"{setting.detail.capitalize()} made the place feel almost like a secret."
    )
    world.say(
        f"{child.id} noticed the gate and the toll box, and {child.pronoun('possessive')} heart thumped with wonder."
    )

    world.para()
    _do_grapple(world, child, toll)
    _flashback(world, g, child, toll, setting)
    _tollkeeper_line(world, child, toll)
    world.say(
        f"{helper.id} watched closely, hoping {child.id} would do what {g.id} had once done."
    )

    world.para()
    _emulate(world, child, g, toll)
    _magic_finish(world, child, helper, toll)

    world.facts["outcome"] = "paid"
    world.facts["kind_choice"] = True
    world.facts["magic"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    guide = f["guide"]
    toll = f["toll"]
    return [
        f'Write a heartwarming magic story for a 3-to-5-year-old that includes the words "grapple", "toll", and "emulate".',
        f"Tell a gentle story about {child.id} at {f['setting'].name} where {guide.label} shares a flashback and helps {child.id} emulate a kind choice about the {toll.label}.",
        f"Write a cozy magical bridge story where a child grapples with paying a toll, remembers a sweet lesson, and crosses happily in the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    guide: Entity = f["guide"]
    toll: Toll = f["toll"]
    keeper: Entity = f["keeper"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {helper.id}, and {guide.label}, all meeting at the bridge with the tollkeeper. The story follows how {child.id} learns to choose the kind way."
        ),
        (
            f"What did {child.id} have to grapple with?",
            f"{child.id} had to grapple with whether to pay the {toll.label} honestly or try to hurry past the gate. That choice mattered because the bridge only opened for kind travelers."
        ),
        (
            "What did the flashback help with?",
            f"The flashback reminded everyone that {guide.flashback_line}. It helped {child.id} understand that copying a good example can make a hard moment easier."
        ),
        (
            "How did the problem get solved?",
            f"{child.id} decided to emulate {guide.id}'s gentle example and paid the toll with {toll.payment}. Then the little magic at the gate opened the bridge for them."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    toll: Toll = f["toll"]
    guide: Guide = f["guide"]
    return [
        QAItem(
            question="What is a toll?",
            answer="A toll is something you pay to use a bridge, road, or gate. It can be money, a token, or another small payment."
        ),
        QAItem(
            question="What does emulate mean?",
            answer="To emulate someone means to copy a good example. Children can emulate kind actions to make a better choice."
        ),
        QAItem(
            "What is a flashback?",
            "A flashback is a brief memory of something that happened before. Stories use it to show why a character knows what to do."
        ),
        QAItem(
            "What kind of feeling does magic have in this story?",
            "The magic is gentle and helpful. It glows, opens the bridge, and makes the kind choice feel special."
        ),
        QAItem(
            "Why is the tollkeeper friendly here?",
            "The tollkeeper likes honest travelers and smiles when they pay carefully. That keeps the story warm and heartwarming."
        ),
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.magic:
            bits.append("magic")
        if e.tollkeeper:
            bits.append("tollkeeper")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(sig[0] for sig in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("moon_gate", "glow_coin", "grandma", "Mina", "girl", "Finn", "boy"),
    StoryParams("garden_bridge", "song_pebble", "aunt", "Theo", "boy", "Luna", "girl"),
    StoryParams("lantern_path", "kind_ticket", "brother", "Ivy", "girl", "Max", "boy"),
]


ASP_RULES = r"""
% A story is valid when the setting, toll, and guide exist.
valid(S, T, G) :- setting(S), toll(T), guide(G).

% The narrative turn is built from all three instruments.
grapple_turn(C) :- child(C).
flashback_turn(G) :- guide(G).
emulate_turn(C, G) :- child(C), guide(G).

% Outcome: the child pays, the gate opens, and the bridge feels warm.
kind_outcome(C, T) :- child(C), toll(T), magical(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TOLLS:
        lines.append(asp.fact("toll", tid))
        lines.append(asp.fact("magical", tid))
    for gid in GUIDES:
        lines.append(asp.fact("guide", gid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def valid_combos_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(valid_combos()) == set(valid_combos_asp()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid-combo parity.")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: normal story generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming magical bridge story world with grapple, toll, emulate."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--toll", choices=TOLLS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.toll and args.toll not in TOLLS:
        raise StoryError("Unknown toll.")
    if args.guide and args.guide not in GUIDES:
        raise StoryError("Unknown guide.")
    setting = args.setting or rng.choice(list(SETTINGS))
    toll = args.toll or rng.choice(list(TOLLS))
    guide = args.guide or rng.choice(list(GUIDES))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child = args.child or pick_name(rng, gender)
    helper = args.helper or pick_name(rng, helper_gender)
    if helper == child:
        helper = pick_name(rng, "boy" if gender == "girl" else "girl")
    params = StoryParams(setting, toll, guide, child, gender, helper, helper_gender)
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        TOLLS[params.toll],
        GUIDES[params.guide],
        params.child,
        params.child_gender,
        params.helper,
        params.helper_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = valid_combos()
        print(f"{len(combos)} compatible (setting, toll, guide) combos:\n")
        for s, t, g in combos:
            print(f"  {s:14} {t:12} {g}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
