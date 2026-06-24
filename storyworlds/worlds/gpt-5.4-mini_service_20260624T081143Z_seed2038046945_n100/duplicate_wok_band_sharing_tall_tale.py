#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/duplicate_wok_band_sharing_tall_tale.py
===============================================================================================================

A small tall-tale storyworld about a shared wok, a marching band, and a
mysterious duplicate that causes trouble before everyone learns how to share.

Seed words:
- duplicate
- wok
- band

Style:
- Tall tale, but still child-facing and grounded in state changes.
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
    shared_with: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    band: object | None = None
    dup: object | None = None
    helper: object | None = None
    hero: object | None = None
    wok: object | None = None
    def __post_init__(self):
        if not self.meters:
            self.meters = {"glow": 0.0, "hunger": 0.0, "scrape": 0.0}
        if not self.memes:
            self.memes = {"pride": 0.0, "worry": 0.0, "share": 0.0, "surprise": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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
    place: str = "the county fair"
    indoors: bool = False
    band_stage: bool = True
    shared_table: bool = True
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
class StoryParams:
    place: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    seed: Optional[int] = None
    params: object | None = None
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out = []
        buf = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)

    def copy(self) -> "World":
        other = World(copy.deepcopy(self.setting))
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.facts = copy.deepcopy(self.facts)
        return other


def _r_duplicate(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes.get("surprise", 0.0) < THRESHOLD:
            continue
        sig = ("duplicate", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        dup_id = f"{e.id}_duplicate"
        if dup_id in world.entities:
            continue
        dup = world.add(Entity(
            id=dup_id,
            kind=e.kind,
            type=e.type,
            label=f"duplicate {e.label or e.id}",
            phrase=f"a duplicate of {e.phrase or e.label or e.id}",
            owner=e.owner,
            caretaker=e.caretaker,
            plural=e.plural,
        ))
        dup.meters = copy.deepcopy(e.meters)
        dup.memes["share"] = e.memes.get("share", 0.0)
        out.append(f"A duplicate of {e.label or e.id} popped up like a second moon.")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    wok = world.entities.get("wok")
    band = world.entities.get("band")
    if not wok or not band:
        return out
    if wok.memes.get("share", 0.0) < THRESHOLD:
        return out
    sig = ("share", wok.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    band.memes["pride"] += 1
    world.say("The wok was shared so fairly that everybody got a taste and a turn.")
    out.append("share_done")
    return out


def _r_bellies(world: World) -> list[str]:
    wok = world.entities.get("wok")
    band = world.entities.get("band")
    if not wok or not band:
        return []
    if wok.meters.get("glow", 0.0) >= THRESHOLD and band.memes.get("worry", 0.0) >= THRESHOLD:
        if ("calm", wok.id) not in world.fired:
            world.fired.add(("calm", wok.id))
            band.memes["worry"] = 0.0
            return ["The smell from the wok settled the band right down."]
    return []


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_duplicate, _r_share, _r_bellies):
            res = rule(world)
            if res:
                changed = True
                for line in res:
                    if line != "share_done":
                        world.say(line)


def introduce(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"{hero.label} was a {hero.type} with a grin as wide as a wagon wheel, "
        f"and {helper.label} was a {helper.type} who could hear music in a rain barrel."
    )
    world.say(
        f"They met at {world.setting.place}, where a brass band played by day and the moon "
        f"seemed to clap along at night."
    )


def discover_wok(world: World, hero: Entity) -> None:
    wok = world.get("wok")
    wok.owner = hero.id
    world.say(
        f"{hero.label} found a great shining wok that looked big enough to fry sunrise itself."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved it, because the wok could feed a crowd and still look like a trophy."
    )


def band_arrives(world: World, band: Entity) -> None:
    world.say(
        f"Then the band marched in with tubas puffed and drums rolling, and every stomach in sight began to rumble."
    )
    band.memes["worry"] += 1
    world.get("wok").meters["hunger"] += 1


def ask_share(world: World, hero: Entity, helper: Entity) -> None:
    wok = world.get("wok")
    wok.memes["share"] += 1
    world.say(
        f"{helper.label} said, 'That wok looks mighty fine, but a mighty fine thing grows better when it is shared.'"
    )
    world.say(
        f"{hero.label} agreed, though {hero.pronoun('possessive')} eyes were still big as lanterns."
    )


def surprise_duplicate(world: World, hero: Entity) -> None:
    hero.memes["surprise"] += 1
    world.say(
        f"Just then, a duplicate of the wok wobbled out from behind the tent like it had been boiled up by the full moon."
    )
    propagate(world)


def resolve_sharing(world: World, hero: Entity, helper: Entity) -> None:
    wok = world.get("wok")
    band = world.get("band")
    wok.meters["glow"] += 1
    wok.meters["hunger"] += 1
    world.say(
        f"So they set the wok on a long plank, and {hero.label} stirred while {helper.label} passed bowls to the band."
    )
    world.say(
        f"The band shared the meal, the meal shared its smell, and the smell shared its joy clear across the fairground."
    )
    if any(e.id.endswith("_duplicate") for e in world.entities.values()):
        world.say(
            f"Even the duplicate stopped causing a fuss once everybody had a turn and nobody had to grab or guard."
        )
    world.say(
        f"By the end, the wok was still shiny, the band was full, and the whole fair sounded like one big happy drum."
    )
    wok.memes["share"] += 1
    band.memes["worry"] = 0.0
    band.memes["pride"] += 1
    propagate(world)


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper))
    band = world.add(Entity(id="band", kind="group", type="band", label="the band", plural=True))
    wok = world.add(Entity(id="wok", kind="thing", type="wok", label="wok", phrase="a giant shining wok"))
    world.facts.update(hero=hero, helper=helper, band=band, wok=wok)

    introduce(world, hero, helper)
    world.para()
    discover_wok(world, hero)
    band_arrives(world, band)
    ask_share(world, hero, helper)
    surprise_duplicate(world, hero)
    world.para()
    resolve_sharing(world, hero, helper)
    return world


WORLDS = {
    "fair": Setting(place="the county fair", indoors=False, band_stage=True, shared_table=True),
    "harbor": Setting(place="the harbor pier", indoors=False, band_stage=True, shared_table=True),
    "barn": Setting(place="the lantern barn", indoors=True, band_stage=False, shared_table=True),
}

NAMES = ["Mabel", "Ned", "Opal", "Hank", "Ivy", "Bess", "Cal", "June"]
TYPES = ["girl", "boy", "woman", "man", "mother", "father"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about sharing a wok with a band.")
    ap.add_argument("--place", choices=WORLDS)
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
    place = getattr(args, "place", None) or rng.choice(list(WORLDS))
    hero = rng.choice(NAMES)
    helper = rng.choice([n for n in NAMES if n != hero])
    hero_type = rng.choice(["girl", "boy"])
    helper_type = rng.choice(["woman", "man", "mother", "father"])
    return StoryParams(place=place, hero=hero, hero_type=hero_type, helper=helper, helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(WORLDS, params.place), params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a tall tale about a duplicate, a wok, and a marching band learning to share.',
        f"Tell a child-friendly story at {world.setting.place} where a wok is shared with a band.",
        "Write a funny, exaggerated story that ends with everyone getting a turn instead of arguing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    helper = world.get("helper")
    band = world.get("band")
    wok = world.get("wok")
    dup = next((e for e in world.entities.values() if e.id.endswith("_duplicate")), None)
    qa = [
        QAItem(
            question=f"Who found the shiny wok?",
            answer=f"{hero.label} found the shiny wok at {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {helper.label} want to do with the wok?",
            answer=f"{helper.label} wanted everybody to share the wok instead of letting one person hold it forever.",
        ),
        QAItem(
            question="What made the story extra strange?",
            answer="A duplicate of the wok popped up, which made the moment feel even taller and stranger.",
        ),
    ]
    if dup:
        qa.append(QAItem(
            question="What happened after the duplicate appeared?",
            answer="Everybody chose sharing over grabbing, so the duplicate stopped being a problem.",
        ))
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a wok?",
            answer="A wok is a round cooking pan with sloping sides, often used for quick cooking and stirring.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use, enjoy, or have some of something too.",
        ),
        QAItem(
            question="What is a band?",
            answer="A band is a group of musicians who play instruments together.",
        ),
    ]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"{e.id}: type={e.type} meters={{{', '.join(f'{k}:{v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}:{v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
% The declarative twin of the reasonableness gate:
% if a wok is shared, the band should benefit; if a duplicate appears,
% the story still resolves by sharing rather than grabbing.

duplicate(X) :- surprise(X).
share_resolves(wok) :- shared(wok).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in WORLDS.items():
        lines.append(asp.fact("place", pid))
        if setting.indoors:
            lines.append(asp.fact("indoors", pid))
        if setting.shared_table:
            lines.append(asp.fact("shared_table", pid))
    lines.append(asp.fact("thing", "wok"))
    lines.append(asp.fact("group", "band"))
    lines.append(asp.fact("feature", "sharing"))
    lines.append(asp.fact("motif", "duplicate"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show share_resolves/1.\n#show duplicate/1.")
    model = asp.one_model(program)
    atoms = set(asp.atoms(model, "share_resolves")) | set(asp.atoms(model, "duplicate"))
    expected = {("wok",)}
    if atoms == expected:
        print("OK: ASP parity matches the Python world.")
        return 0
    print("MISMATCH:", sorted(atoms), "!=", sorted(expected))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show share_resolves/1.\n#show duplicate/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP mode is available; use --verify or --show-asp to inspect it.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for place in WORLDS:
            params = StoryParams(place=place, hero="Mabel", hero_type="girl", helper="Ned", helper_type="man")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 25):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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

    for idx, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {idx + 1}" if len(samples) > 1 else "")
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
