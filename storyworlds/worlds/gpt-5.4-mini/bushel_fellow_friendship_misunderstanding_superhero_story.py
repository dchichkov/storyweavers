#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bushel_fellow_friendship_misunderstanding_superhero_story.py
===========================================================================================

A standalone storyworld for a small superhero-style friendship misunderstanding
with the seed words "bushel" and "fellow".

Premise:
- Two kids are playing superhero.
- One gathers a bushel of "power berries" / "shiny beans" / "golden leaves" for a pretend hero signal.
- The other fellow thinks the bushel is being kept secret or taken away.
- A misunderstanding causes hurt feelings.
- A calm explanation and a shared rescue/mission repair the friendship.

The world is intentionally tiny and classical: typed entities with meters and
memes, a forward-chaining causal rule engine, a reasonableness gate, story and
QA generation from world state, and an inline ASP twin.
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
FRIENDSHIP_MIN = 2
MISUNDERSTANDING_MIN = 1


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
    backdrop: str
    mission: str
    hiding_place: str
    signal_name: str

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
class Cache:
    id: str
    label: str
    phrase: str
    count_word: str
    safe_use: str
    tags: set[str] = field(default_factory=set)

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
class Misunderstanding:
    id: str
    trigger: str
    false_thought: str
    words: str
    repair: str
    tags: set[str] = field(default_factory=set)

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
class Power:
    id: str
    label: str
    phrase: str
    glow: str
    tags: set[str] = field(default_factory=set)

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


def _r_hurt_feelings(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["misunderstood"] < THRESHOLD:
            continue
        sig = ("hurt", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["hurt"] += 1
        out.append("")
    return out


def _r_friendship_pull(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("hero")
    b = world.get("fellow")
    if a.memes["hurt"] >= THRESHOLD or b.memes["hurt"] >= THRESHOLD:
        sig = ("pull",)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["want_fix"] += 1
            b.memes["want_fix"] += 1
            out.append("__repair__")
    return out


CAUSAL_RULES = [
    Rule("hurt_feelings", "social", _r_hurt_feelings),
    Rule("friendship_pull", "social", _r_friendship_pull),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s and not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def safe_combo(cache: Cache, setting: Setting) -> bool:
    return cache.id in setting.signal_name or "shared" in cache.tags


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for sid in SETTINGS:
        for cid in CACHES:
            if safe_combo(CACHES[cid], SETTINGS[sid]):
                out.append((sid, cid))
    return out


@dataclass
@dataclass
class StoryParams:
    setting: str
    cache: str
    power: str
    hero_name: str
    fellow_name: str
    hero_gender: str
    fellow_gender: str
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
    ap = argparse.ArgumentParser(
        description="A superhero friendship misunderstanding storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cache", choices=CACHES)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--fellow-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--fellow-gender", choices=["girl", "boy"])
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


SETTINGS = {
    "rooftop": Setting("rooftop", "on the rooftop garden",
                       "The city wind ruffled the capes on the clothesline.",
                       "a tiny rescue mission", "the tomato patch", "signal berries"),
    "alley": Setting("alley", "in the sunlit alley",
                     "Bright paint cans and old posters made it feel like a secret base.",
                     "a helper mission", "the bike rack", "signal beans"),
    "park": Setting("park", "in the park",
                    "The playground looked like a city full of towers.",
                    "a rescue drill", "the sandbox", "signal leaves"),
}

CACHES = {
    "bushel": Cache("bushel", "bushel", "a bushel of signal berries", "bushel",
                    "kept for the whole team", {"shared", "signal"}),
    "basket": Cache("basket", "basket", "a basket of signal beans", "basket",
                    "shared with friends", {"shared", "signal"}),
    "bag": Cache("bag", "bag", "a bag of signal leaves", "bag",
                "carried for everyone", {"shared", "signal"}),
}

MISUNDERSTANDINGS = {
    "secret": Misunderstanding("secret", "looked hidden",
                              "thought it was being kept secret",
                              "You hid the bushel from me!",
                              "The bushel was for both of us.", {"misunderstanding"}),
    "took": Misunderstanding("took", "picked up first",
                            "thought it had been taken away",
                            "You took the bushel and left me out!",
                            "I only moved it so we could carry it together.",
                            {"misunderstanding"}),
}

POWERS = {
    "flash": Power("flash", "flashlight", "a bright flashlight", "glowed like a tiny moon", {"light"}),
    "boom": Power("boom", "signal", "a big sky signal", "shone over the rooftops", {"light"}),
    "shield": Power("shield", "shield", "a cardboard shield", "looked brave and round", {"tool"}),
}

GIRL_NAMES = ["Luna", "Mina", "Zoe", "Aria", "Nina", "Rae", "Maya", "Tia"]
BOY_NAMES = ["Leo", "Nico", "Ben", "Finn", "Owen", "Jude", "Kai", "Theo"]
TRAITS = ["brave", "kind", "quick", "curious", "steady", "gentle"]


def reasonableness_gate(setting: Setting, cache: Cache, misunderstanding: Misunderstanding) -> bool:
    return safe_combo(cache, setting) and misunderstanding.id in {"secret", "took"}


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CACHES.items():
        lines.append(asp.fact("cache", cid))
        if "shared" in c.tags:
            lines.append(asp.fact("shared", cid))
    for mid in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", mid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, C) :- setting(S), cache(C), shared(C).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def explain_rejection(setting: Setting, cache: Cache) -> str:
    return (f"(No story: the {cache.label} does not fit this mission well enough. "
            f"Try the bushel, basket, or bag with this setting.)")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.cache and not reasonableness_gate(
        SETTINGS[args.setting], CACHES[args.cache], MISUNDERSTANDINGS["secret"]
    ):
        raise StoryError(explain_rejection(SETTINGS[args.setting], CACHES[args.cache]))
    combos = [c for c in valid_combos()
              if args.setting is None or c[0] == args.setting
              and args.cache is None or c[1] == args.cache]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, cache = rng.choice(sorted(combos))
    power = args.power or rng.choice(sorted(POWERS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    fellow_gender = args.fellow_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    fellow_name = args.fellow_name or rng.choice([n for n in (BOY_NAMES if fellow_gender == "boy" else GIRL_NAMES) if n != hero_name])
    return StoryParams(setting, cache, power, hero_name, fellow_name, hero_gender, fellow_gender)


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    cache = CACHES[params.cache]
    power = POWERS[params.power]
    mis = MISUNDERSTANDINGS["secret"] if params.cache == "bushel" else MISUNDERSTANDINGS["took"]
    hero = world.add(Entity("hero", kind="character", type=params.hero_gender, role="hero",
                            label=params.hero_name, traits=["heroic", "kind"]))
    fellow = world.add(Entity("fellow", kind="character", type=params.fellow_gender, role="fellow",
                              label=params.fellow_name, traits=["friend", "watchful"]))
    adult = world.add(Entity("adult", kind="character", type="mother", role="adult", label="the grown-up"))
    world.facts["setting"] = setting
    world.facts["cache"] = cache
    world.facts["power"] = power
    world.facts["mis"] = mis

    hero.memes["friendship"] = 3
    fellow.memes["friendship"] = 3

    world.say(f"{hero.label} and {fellow.label} were a superhero team in {setting.place}.")
    world.say(f"{setting.backdrop} They were ready for {setting.mission}.")

    world.para()
    world.say(f"{hero.label} found {cache.phrase} near {setting.hiding_place}.")
    world.say(f'\"Look!\" {hero.label} said. \"This bushel could help our {setting.signal_name}.\"')
    world.say(f"{fellow.label} smiled, but then {mis.false_thought}")

    world.para()
    hero.memes["intent"] += 1
    fellow.memes["misunderstood"] += 1
    fellow.memes["hurt"] += 1
    hero.meters["carrying"] += 1
    propagate(world, narrate=False)
    world.say(f"{fellow.label} frowned and crossed {fellow.pronoun('possessive')} arms.")
    world.say(f'\"{mis.words}\" {fellow.label} blurted, sounding small and hurt.')
    world.say(f"{hero.label} blinked. \"No, fellow,\" {hero.label} said softly, \"I was saving it for us.\"")

    world.para()
    if params.power == "flash":
        world.say(f"{adult.label_word.capitalize()} came over with a calm smile and a {power.phrase}.")
        world.say(f"{power.glow}.")
    elif params.power == "boom":
        world.say(f"{adult.label_word.capitalize()} raised a {power.phrase} to show where the team would meet.")
        world.say(f"It {power.glow}.")
    else:
        world.say(f"{adult.label_word.capitalize()} held up a {power.phrase} and nodded at both kids.")
        world.say(f"It {power.glow}.")

    fellow.memes["misunderstood"] = 0
    fellow.memes["hurt"] = 0
    fellow.memes["friendship"] += 1
    hero.memes["friendship"] += 1
    world.say(mis.repair)
    world.say(f"The two friends carried the bushel together, one on each side.")
    world.say(f"By the end, the signal was bright, and the fellow was no longer a fellow left out, but a true teammate.")

    world.facts.update(hero=hero, fellow=fellow, adult=adult, setting=setting, cache=cache,
                       mis=mis, power=power, outcome="repaired")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero friendship story that includes the words "bushel" and "fellow".',
        f"Tell a story where {f['hero'].label} and {f['fellow'].label} have a misunderstanding about a {f['cache'].label} and then fix it together.",
        f"Write a child-friendly superhero story about a mistaken idea, a calm explanation, and friends sharing a {f['cache'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, fellow, setting, cache, mis = f["hero"], f["fellow"], f["setting"], f["cache"], f["mis"]
    return [
        QAItem(
            question="Who are the story about?",
            answer=f"The story is about {hero.label} and {fellow.label}, two superhero friends who were working in {setting.place}."
        ),
        QAItem(
            question="What caused the misunderstanding?",
            answer=f"{fellow.label} saw the {cache.label} and thought {mis.false_thought.lower()}. That made {fellow.label} feel left out even though {hero.label} meant to share."
        ),
        QAItem(
            question="How did they fix the problem?",
            answer=f"The grown-up explained that {mis.repair.lower()} Then the two friends carried the {cache.label} together, so the team felt united again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What is a bushel?",
            answer="A bushel is a big container or basket for holding a lot of small things. It helps keep items together so they can be carried as one load."
        ),
        QAItem(
            question="What does a fellow mean?",
            answer="A fellow is another person, often a friend or companion. In a story, it can mean the kid who is helping on the team."
        ),
        QAItem(
            question="Why can misunderstanding hurt friendship?",
            answer="A misunderstanding can make someone think something unfair or unkind happened. Friends may feel sad until they talk clearly and fix the mistake."
        ),
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("rooftop", "bushel", "flash", "Luna", "Kai", "girl", "boy"),
    StoryParams("park", "basket", "boom", "Mina", "Theo", "girl", "boy"),
    StoryParams("alley", "bag", "shield", "Ben", "Rae", "boy", "girl"),
]


def explain_response(rid: str) -> str:
    return f"(Refusing response '{rid}': not used in this world.)"


def asp_verify() -> int:
    import asp
    try:
        py = set(valid_combos())
        cl = set(asp_valid_combos())
    except Exception as exc:
        print(f"ERROR: ASP check crashed: {exc}")
        return 1
    if py != cl:
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, cache=None, power=None, hero_name=None, fellow_name=None,
            hero_gender=None, fellow_gender=None
        ), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"ERROR: story generation crashed: {exc}")
        return 1
    print(f"OK: gate matches and story generation works ({len(py)} combos).")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, cache) combos:\n")
        for sid, cid in combos:
            print(f"  {sid:8} {cid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} and {p.fellow_name}: {p.cache} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
