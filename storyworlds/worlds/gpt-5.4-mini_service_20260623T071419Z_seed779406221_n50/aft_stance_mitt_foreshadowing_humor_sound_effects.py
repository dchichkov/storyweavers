#!/usr/bin/env python3
"""
storyworlds/worlds/aft_stance_mitt_foreshadowing_humor_sound_effects.py
=======================================================================

A small pirate-tale storyworld about a child crew in a boat's aft end, a tricky
stance, and a mitt that foreshadows a safer choice.

Premise:
A little pirate crew plays aboard a docked boat. One child wants to paddle
backward from the aft deck using a mitt as a pretend hook, but the grown-up
worries the stance will slip on the wet boards. The story turns on a noisy
warning, a funny mistake, and a safer way to keep playing.

This world models:
- physical meters: slickness, splash, balance, trouble, safety
- emotional memes: delight, worry, boldness, relief, humor, trust

Features:
- foreshadowing: an early clue about the wet aft deck and the loose mitt
- humor: a playful misread of the mitt and the crew's silly reactions
- sound effects: splash, thump, skrrt, clap, whoosh

Style target:
- child-facing, pirate-tale flavored, with a clear beginning, turn, and ending
- concrete state changes drive the prose
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

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------



def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    deck: object | None = None
    helper: object | None = None
    hero: object | None = None
    mitt: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

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
class StoryParams:
    crew: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    setting: str
    stance: str
    mitt: str
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


CREW_REGISTRY = {
    "pirates": "pirates",
    "deckhands": "deckhands",
    "scouts": "scouts",
}

SETTING_REGISTRY = {
    "aft_deck": "the aft deck",
    "harbor_dock": "the harbor dock",
    "boathouse": "the boathouse",
}

STANCE_REGISTRY = {
    "tiptoe": "tiptoe on the slick boards",
    "wide_stance": "stand with feet wide apart",
    "one_foot": "balance on one foot",
}

MITT_REGISTRY = {
    "hook_mitt": "a striped mitt",
    "wool_mitt": "a soft wool mitt",
    "blue_mitt": "a blue mitten",
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Finn", "Jude", "Theo", "Leo", "Max"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        ("pirates", "aft_deck", "hook_mitt"),
        ("pirates", "aft_deck", "wool_mitt"),
        ("deckhands", "harbor_dock", "blue_mitt"),
        ("scouts", "boathouse", "wool_mitt"),
    ]


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


def build_world(params: StoryParams) -> World:
    w = World()
    hero = w.add(Entity(
        id=params.hero,
        kind="character",
        type=params.hero_type,
        attrs={"role": "hero"},
        meters={"balance": 0.0, "splash": 0.0},
        memes={"boldness": 1.0, "delight": 1.0, "worry": 0.0, "relief": 0.0, "humor": 0.0},
    ))
    helper = w.add(Entity(
        id=params.helper,
        kind="character",
        type=params.helper_type,
        attrs={"role": "helper"},
        meters={"balance": 0.0},
        memes={"trust": 1.0, "worry": 0.0},
    ))
    deck = w.add(Entity(
        id="deck",
        kind="thing",
        type="deck",
        label=SETTING_REGISTRY[params.setting],
        meters={"slick": 1.0, "danger": 0.0},
        tags={"aft", "deck"},
    ))
    mitt = w.add(Entity(
        id="mitt",
        kind="thing",
        type="mitt",
        label=MITT_REGISTRY[params.mitt],
        meters={"loose": 1.0},
        tags={"mitt"},
    ))

    w.facts.update(hero=hero, helper=helper, deck=deck, mitt=mitt, params=params)
    return w


def foreshadow(world: World) -> None:
    hero: Entity = world.facts["hero"]
    deck: Entity = world.facts["deck"]
    mitt: Entity = world.facts["mitt"]
    world.say(
        f"At {deck.label}, the boards looked shiny and wet, and {mitt.label} kept sliding a little."
    )
    world.say(
        f"{hero.id} noticed it first. That little wobble was a clue that the aft deck might turn slippery."
    )
    hero.memes["worry"] += 0.5
    hero.memes["humor"] += 0.5


def setup(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    params: StoryParams = world.facts["params"]
    crew_word = CREW_REGISTRY[params.crew]
    stance_word = STANCE_REGISTRY[params.stance]
    world.say(
        f"One bright day, {hero.id} and {helper.id} played as {crew_word} aboard {SETTING_REGISTRY[params.setting]}."
    )
    world.say(
        f'{hero.id} wanted to use {world.facts["mitt"].label} like a hook and {stance_word} while pretending to steer.'
    )
    helper.memes["trust"] += 0.5
    hero.memes["boldness"] += 0.5


def warning(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    deck: Entity = world.facts["deck"]
    world.say(
        f'"Careful," {helper.id} said. "That stance could skrrt on the slick boards."'
    )
    helper.memes["worry"] += 1.0
    world.facts["warned"] = True
    if deck.meters["slick"] >= THRESHOLD:
        hero.memes["worry"] += 0.5


def slip_or_try(world: World) -> None:
    hero: Entity = world.facts["hero"]
    mitt: Entity = world.facts["mitt"]
    params: StoryParams = world.facts["params"]
    if params.stance == "one_foot":
        world.say(
            f"{hero.id} tried the one-foot stance anyway. Whoops -- skrrt!"
        )
        hero.meters["balance"] += 1.0
        hero.meters["splash"] += 1.0
        hero.memes["humor"] += 1.0
        world.facts["slipped"] = True
    else:
        world.say(
            f"{hero.id} adjusted the stance before any tumble, and {mitt.label} stayed in hand."
        )
        world.facts["slipped"] = False


def rescue_and_fix(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    deck: Entity = world.facts["deck"]
    mitt: Entity = world.facts["mitt"]

    if world.facts.get("slipped"):
        world.say(
            f"{helper.id} gave a quick clap-clap and pointed to the dry plank by the rail."
        )
        hero.memes["worry"] += 0.5
        helper.memes["trust"] += 0.5
        world.say(
            f"{hero.id} laughed, stepped back, and put both feet down before the aft deck could claim {mitt.label}."
        )
        world.say(
            f"Then the crew used the mitt to wave a tiny signal instead of a hook, and the game felt smarter than before."
        )
        hero.memes["relief"] += 1.0
        helper.memes["relief"] += 1.0
        deck.meters["danger"] = 0.0
    else:
        world.say(
            f"With a steadier stance, {hero.id} and {helper.id} kept playing, and the aft deck stayed safe."
        )
        hero.memes["relief"] += 1.0
        helper.memes["relief"] += 1.0


def ending(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    mitt: Entity = world.facts["mitt"]
    params: StoryParams = world.facts["params"]
    crew_word = CREW_REGISTRY[params.crew]
    world.say(
        f"In the end, {hero.id} and {helper.id} were still {crew_word}, but now they knew a safer stance for the slick aft deck."
    )
    world.say(
        f"{mitt.label} was still there, no longer a pretend hook but a silly little clue that helped them choose better."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    setup(world)
    world.para()
    foreshadow(world)
    warning(world)
    slip_or_try(world)
    world.para()
    rescue_and_fix(world)
    ending(world)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Registries and helpers
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(
        crew="pirates",
        hero="Mira",
        hero_type="girl",
        helper="Finn",
        helper_type="boy",
        setting="aft_deck",
        stance="one_foot",
        mitt="hook_mitt",
        seed=1,
    ),
    StoryParams(
        crew="pirates",
        hero="Leo",
        hero_type="boy",
        helper="Nora",
        helper_type="girl",
        setting="aft_deck",
        stance="wide_stance",
        mitt="wool_mitt",
        seed=2,
    ),
]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    mitt: Entity = world.facts["mitt"]
    deck: Entity = world.facts["deck"]
    qa = [
        QAItem(
            question=f"What were {hero.id} and {helper.id} playing like on {deck.label}?",
            answer=(
                f"They were playing like {CREW_REGISTRY[p.crew]}, and {hero.id} wanted to use {mitt.label} while keeping a tricky stance."
            ),
        ),
        QAItem(
            question=f"Why did {helper.id} warn {hero.id}?",
            answer=(
                f"{helper.id} saw that the aft deck was slick, and a shaky stance could make {hero.id} slip. The warning came from noticing the wet boards and the loose mitt."
            ),
        ),
    ]
    if world.facts.get("slipped"):
        qa.append(
            QAItem(
                question=f"What happened when {hero.id} tried the stance?",
                answer=(
                    f"{hero.id} slipped with a funny skrrt and a splash, so the game had to pause and change to a safer way."
                ),
            )
        )
    else:
        qa.append(
            QAItem(
                question=f"How did the story stay safe in the end?",
                answer=(
                    f"{hero.id} adjusted the stance, kept both feet down, and the aft deck stayed safe for the pirate game."
                ),
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does aft mean on a boat?",
            answer="Aft means the back part of a boat. Pirates and sailors use it to talk about where something is near the stern.",
        ),
        QAItem(
            question="What is a stance?",
            answer="A stance is the way someone stands. A steady stance helps you keep your balance.",
        ),
        QAItem(
            question="What is a mitt?",
            answer="A mitt is a soft hand covering like a mitten. It can keep hands warm and can also be used in pretend play.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f'Write a short pirate tale for a child that uses the words "aft", "stance", and "mitt".',
        f"Tell a playful story where {p.hero} wants to stand in a tricky stance on the aft deck, but a helper notices the danger first.",
        f"Write a gentle, funny story with a foreshadowing clue, a sound effect, and a safer ending aboard a boat.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes} attrs={e.attrs} tags={sorted(e.tags)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "setting", None) and getattr(args, "setting", None) not in SETTING_REGISTRY:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "stance", None) and getattr(args, "stance", None) not in STANCE_REGISTRY:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "mitt", None) and getattr(args, "mitt", None) not in MITT_REGISTRY:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    filtered = [
        c for c in combos
        if (not getattr(args, "setting", None) or c[1] == getattr(args, "setting", None))
        and (not getattr(args, "mitt", None) or c[2] == getattr(args, "mitt", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    crew, setting, mitt = rng.choice(filtered)
    stance = getattr(args, "stance", None) or rng.choice(list(STANCE_REGISTRY))
    hero_type = rng.choice(["girl", "boy"])
    helper_type = "boy" if hero_type == "girl" else "girl"
    hero = getattr(args, "hero", None) or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(GIRL_NAMES if helper_type == "girl" else BOY_NAMES)
    if helper == hero:
        helper = (helper + "a") if helper[-1].lower() != "a" else (helper + "x")
    return StoryParams(
        crew=crew,
        hero=hero,
        hero_type=hero_type,
        helper=helper,
        helper_type=helper_type,
        setting=setting,
        stance=stance,
        mitt=mitt,
    )


def generate(params: StoryParams) -> StorySample:
    if (params.crew, params.setting, params.mitt) not in valid_combos():
        pass
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
        print("== (1) Generation prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== (2) Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== (3) World knowledge ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
valid(Crew, Setting, Mitt) :- crew(Crew), setting(Setting), mitt(Mitt), combo(Crew, Setting, Mitt).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for crew in CREW_REGISTRY:
        lines.append(asp.fact("crew", crew))
    for setting in SETTING_REGISTRY:
        lines.append(asp.fact("setting", setting))
    for mitt in MITT_REGISTRY:
        lines.append(asp.fact("mitt", mitt))
    for crew, setting, mitt in valid_combos():
        lines.append(asp.fact("combo", crew, setting, mitt))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    ax = set(asp_valid_combos())
    if py == ax:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
        # smoke test ordinary generation
        sample = generate(CURATED[0])
        if not sample.story.strip():
            print("FAIL: smoke test produced empty story.")
            return 1
        print("OK: smoke test generation succeeded.")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - ax))
    print("asp-only:", sorted(ax - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-style storyworld with aft, stance, and mitt.")
    ap.add_argument("--setting", choices=SETTING_REGISTRY)
    ap.add_argument("--stance", choices=STANCE_REGISTRY)
    ap.add_argument("--mitt", choices=MITT_REGISTRY)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        raise SystemExit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid_combos())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
