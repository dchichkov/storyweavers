#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/spree_appetizing_conflict_misunderstanding_sound_effects_superhero.py
====================================================================================================

A standalone storyworld about a tiny superhero-style snack spree: two kids are
playing heroes, an appetizing snack basket goes missing, a misunderstanding
starts a conflict, and sound effects plus a calm grown-up help them fix it.

The world is intentionally small and classical:
- typed entities with physical meters and emotional memes
- a state-driven causal model, not a frozen paragraph
- a reasonableness gate plus an inline ASP twin
- three QA sets generated from world state

The seed words are used directly in the story output: "spree" and
"appetizing".
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
class Place:
    id: str
    label: str
    scene: str
    has_table: bool = True
    has_window: bool = True

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
class Snack:
    id: str
    label: str
    phrase: str
    appetizing: bool = True
    spillable: bool = True
    crumbs: str = "crumbs"

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
class Costume:
    id: str
    label: str
    phrase: str
    sparkle: str
    sound: str
    heroic: bool = True

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
class Misread:
    id: str
    misunderstanding: str
    true_meaning: str
    conflict_line: str
    fix_line: str

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
class SoundEffect:
    id: str
    text: str
    action: str

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
        clone.facts = copy.deepcopy(self.facts)
        return clone

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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    snack = world.get("snack")
    if hero.memes["accusation"] >= THRESHOLD and sidekick.memes["hurt"] >= THRESHOLD:
        sig = ("conflict",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["anger"] += 1
            sidekick.memes["anger"] += 1
            out.append("__conflict__")
    if snack.meters["spilled"] >= THRESHOLD:
        snack.meters["messy"] += 1
    return out


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


CAUSAL_RULES = [Rule("conflict", "social", _r_conflict)]


def reasonableness_gate(place: Place, snack: Snack, misread: Misread) -> bool:
    return place.has_table and snack.appetizing and misread.id in MISREADS


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for sid, snack in SNACKS.items():
            for mid, misread in MISREADS.items():
                if reasonableness_gate(place, snack, misread):
                    combos.append((pid, sid, mid))
    return combos


def _do_spree(world: World, hero: Entity, sidekick: Entity, snack: Snack, sound: SoundEffect) -> None:
    hero.meters["busy"] += 1
    sidekick.meters["busy"] += 1
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    snack.meters["wanted"] += 1
    world.say(
        f"On a bright afternoon, {hero.id} and {sidekick.id} launched a superhero spree around {world.facts['place'].label}."
    )
    world.say(
        f"They wore capes, raced in circles, and made the loud sound of {sound.text} every time they leapt."
    )
    world.say(
        f"Near the table sat {snack.phrase}, and it looked very appetizing."
    )


def misunderstand(world: World, hero: Entity, sidekick: Entity, snack: Snack, misread: Misread) -> None:
    hero.memes["curiosity"] += 1
    sidekick.memes["worry"] += 1
    world.say(
        f"Then {hero.id} noticed the basket and said, '{misread.misunderstanding}!'"
    )
    world.say(
        f"{sidekick.id} heard that as a mean idea, not a hungry one, and {misread.conflict_line}"
    )
    hero.memes["accusation"] += 1
    sidekick.memes["hurt"] += 1
    propagate(world, narrate=False)


def clash(world: World, hero: Entity, sidekick: Entity) -> None:
    world.say(
        f'"{hero.id}, stop!" shouted {sidekick.id}. "I thought you were taking it!"'
    )
    world.say(
        f'"No, I meant the snack was appetizing!" {hero.id} said. "{sidekick.id}, listen!"'
    )
    world.say("The capes fluttered, and the room filled with staccato footsteps and gasp-gasp sighs.")


def calm_fix(world: World, parent: Entity, snack: Snack, misread: Misread, sound: SoundEffect) -> None:
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    hero.memes["relief"] += 1
    sidekick.memes["relief"] += 1
    snack.meters["spilled"] = 0.0
    world.say(
        f"At last {parent.id} came in with a calm smile and said, '{misread.fix_line}'"
    )
    world.say(
        f"With a soft {sound.text}, {parent.id} showed them the basket was only for sharing, not for stealing."
    )
    world.say(
        f"The two kids laughed, picked up the napkins, and lined the appetizing snacks back in a neat row."
    )
    hero.memes["love"] += 1
    sidekick.memes["love"] += 1


def ending_image(world: World) -> None:
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    snack = world.get("snack")
    world.say(
        f"By the end, their superhero spree was still exciting, but now it was a kind one: {hero.id} held the tray, {sidekick.id} handed out fruit, and the appetizing basket stayed full."
    )


def tell(place: Place, snack: Snack, misread: Misread, sound: SoundEffect) -> World:
    world = World()
    hero = world.add(Entity(id="Milo", kind="character", type="boy", role="hero"))
    sidekick = world.add(Entity(id="Nia", kind="character", type="girl", role="sidekick"))
    parent = world.add(Entity(id="Aunt Rae", kind="character", type="mother", role="parent"))
    basket = world.add(Entity(id="snack", kind="thing", type="snack", label=snack.label))
    world.facts["place"] = place
    world.facts["snack_cfg"] = snack
    world.facts["misread"] = misread
    world.facts["sound"] = sound
    world.facts["hero"] = hero
    world.facts["sidekick"] = sidekick
    world.facts["parent"] = parent
    world.facts["snack"] = basket
    _do_spree(world, hero, sidekick, snack, sound)
    world.para()
    misunderstand(world, hero, sidekick, snack, misread)
    clash(world, hero, sidekick)
    world.para()
    calm_fix(world, parent, snack, misread, sound)
    ending_image(world)
    return world


PLACES = {
    "kitchen": Place("kitchen", "the kitchen", "a sunny kitchen with a big round table"),
    "playroom": Place("playroom", "the playroom", "a playroom with a table, a window, and a bright rug"),
}

SNACKS = {
    "fruit": Snack("fruit", "a fruit basket", "a fruit basket with sliced apples and grapes"),
    "cookies": Snack("cookies", "a cookie tray", "a cookie tray with tiny star cookies"),
}

MISREADS = {
    "take": Misread(
        "take",
        "I should take it!",
        "I think it looks tasty!",
        "grabbed their arms and glared",
        "was only pointing at the snack and asking to share it",
    ),
    "share": Misread(
        "share",
        "Can I share?",
        "Can I help pass them out?",
        "crossed her arms and thought she was being left out",
        "was asking to help serve the treats",
    ),
}

SOUNDS = {
    "whoosh": SoundEffect("whoosh", "whoosh", "a fast cape swoop"),
    "pow": SoundEffect("pow", "pow", "a bouncy landing"),
    "zap": SoundEffect("zap", "zap", "a sparkly jump"),
}

GIRL_NAMES = ["Nia", "Ava", "Mina", "Lena"]
BOY_NAMES = ["Milo", "Arlo", "Toby", "Jude"]
TRAITS = ["bright", "curious", "careful", "cheerful"]


@dataclass
@dataclass
class StoryParams:
    place: str
    snack: str
    misread: str
    sound: str
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


KNOWLEDGE = {
    "appetizing": [("What does appetizing mean?", "Appetizing means it looks so tasty that you want to eat it.")],
    "share": [("What does it mean to share food?", "Sharing food means giving some to other people so everyone can have a little.")],
    "snack": [("What is a snack?", "A snack is a small amount of food you eat between bigger meals.")],
    "sound": [("What is a sound effect?", "A sound effect is a special sound that helps a story feel exciting, like whoosh or zap.")],
    "conflict": [("What is conflict in a story?", "Conflict is when characters want different things and start to argue or disagree.")],
    "misunderstanding": [("What is a misunderstanding?", "A misunderstanding is when someone thinks something means one thing, but it really means something else.")],
}
KNOWLEDGE_ORDER = ["appetizing", "share", "snack", "sound", "conflict", "misunderstanding"]


def generation_prompts(world: World) -> list[str]:
    p = world.facts["place"]
    s = world.facts["snack_cfg"]
    m = world.facts["misread"]
    return [
        f'Write a superhero story for a young child set in {p.label} that includes the words "spree" and "appetizing".',
        f"Tell a story where two kids are on a superhero spree, see {s.phrase}, and have a misunderstanding that turns into conflict before a grown-up fixes it.",
        f"Write a gentle superhero tale with sound effects, a mistaken accusation, and a happy ending where an appetizing snack is shared.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    parent = world.facts["parent"]
    snack = world.facts["snack_cfg"]
    misread = world.facts["misread"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id} and {sidekick.id}, two kids in capes, and {parent.id}, who helped them sort things out."),
        ("What looked appetizing?",
         f"{snack.phrase} looked appetizing, so {hero.id} got excited and tried to explain that they wanted to share it."),
        ("Why did the conflict start?",
         f"The conflict started because {sidekick.id} misunderstood {hero.id}'s words. {sidekick.id} thought {hero.id} was trying to take the snack, so both of them got upset."),
        ("What fixed the misunderstanding?",
         f"{parent.id} explained that {misread.true_meaning}. That calm explanation helped both kids stop arguing and work together."),
    ]
    if world.facts.get("sound"):
        qa.append((
            "How did the sound effects help the story?",
            f"The {world.facts['sound'].text} sound made the superhero spree feel lively. It also gave the scene a playful rhythm while the kids rushed around and then settled down."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"appetizing", "share", "snack", "sound", "conflict", "misunderstanding"}
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "fruit", "take", "whoosh"),
    StoryParams("playroom", "cookies", "share", "zap"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("has_table", pid))
    for sid in SNACKS:
        lines.append(asp.fact("snack", sid))
        lines.append(asp.fact("appetizing", sid))
    for mid in MISREADS:
        lines.append(asp.fact("misread", mid))
    for sid in SOUNDS:
        lines.append(asp.fact("sound", sid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,S,M) :- place(P), snack(S), misread(M), has_table(P), appetizing(S).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    cl = set(asp_valid_combos())
    py = set(valid_combos())
    ok = True
    if cl != py:
        ok = False
        print("MISMATCH in valid_combos:")
        print("  only in clingo:", sorted(cl - py))
        print("  only in python:", sorted(py - cl))
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, snack=None, misread=None, sound=None, seed=None), random.Random(7)))
        assert sample.story
    except Exception as exc:
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    if ok:
        print(f"OK: verify passed with {len(cl)} combos and smoke-tested generation.")
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero snack spree storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--misread", choices=MISREADS)
    ap.add_argument("--sound", choices=SOUNDS)
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
              if (args.place is None or c[0] == args.place)
              and (args.snack is None or c[1] == args.snack)
              and (args.misread is None or c[2] == args.misread)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, snack, misread = rng.choice(sorted(combos))
    sound = args.sound or rng.choice(sorted(SOUNDS))
    return StoryParams(place, snack, misread, sound)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], SNACKS[params.snack], MISREADS[params.misread], SOUNDS[params.sound])
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
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(" ", c)
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
