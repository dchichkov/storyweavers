#!/usr/bin/env python3
"""
A standalone storyworld for a tiny folk-tale suspense domain:
a child, a lurking bogey, a blot, and a reflex that saves the day.

Premise:
- A child is sent at dusk to fetch something from a shed or cellar.
- A dark bogey seems to follow.
- A sudden reflex—covering a lantern, stamping a heel, or singing back—
  changes the bogey's power.
- The blot is either soot, mud, or berry stain that becomes the proof of the turn.

The world is deliberately small and state-driven:
- physical meters: distance, light, stain, noise, safety, tidiness
- emotional memes: fear, courage, relief, caution, wonder
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

# Shared containers
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
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    blot: object | None = None
    hero: object | None = None
    reflex: object | None = None
    threat: object | None = None
    def __post_init__(self):
        for k in ("distance", "light", "stain", "noise", "safety", "tidiness"):
            self.meters.setdefault(k, 0.0)
        for k in ("fear", "courage", "relief", "caution", "wonder", "suspense"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "witch"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str = "the old lane"
    twilight: bool = True
    affords: set[str] = field(default_factory=set)
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
class Threat:
    name: str
    label: str
    shadow: str
    mutter: str
    fades_from: set[str]
    fears: set[str]
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
class Reflex:
    name: str
    cue: str
    action: str
    consequence: str
    quiets: set[str]
    guards: set[str]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_bits: list[str] = []

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


def _blend(world: World, actor: Entity, threat: Entity, blot: Entity) -> None:
    actor.memes["fear"] += 1
    actor.memes["suspense"] += 1
    threat.meters["distance"] = max(0.0, threat.meters["distance"] - 1)
    blot.meters["stain"] += 1
    world.say(f"A dark {threat.label} seemed to follow {actor.id} at {world.setting.place}.")
    world.say(f"Then a {blot.label} showed on the cloth, small as a thumbprint and just as strange.")


def _reflex(world: World, actor: Entity, reflex: Entity, threat: Entity, blot: Entity) -> None:
    if actor.meters["light"] < THRESHOLD and reflex.id == "shield_lantern":
        actor.meters["light"] += 1
    actor.memes["courage"] += 1
    actor.memes["fear"] = max(0.0, actor.memes["fear"] - 0.5)
    actor.memes["relief"] += 1
    if threat.meters["distance"] < 1.0:
        threat.meters["distance"] += 2
    blot.meters["stain"] += 0.0
    blot.meters["tidiness"] = 0.0
    world.say(f"{actor.id} had a quick reflex: {reflex.action}.")
    world.say(f"That little answer made the {threat.label} fade and left the {blot.label} plain to see.")


def _resolve(world: World, actor: Entity, threat: Entity, blot: Entity) -> None:
    actor.memes["wonder"] += 1
    actor.memes["suspense"] = 0.0
    world.say(
        f"In the end, the {threat.label} was only a shadowy worry, and the {blot.label} was "
        f"just a real mark from the road."
    )
    world.say(
        f"{actor.id} went home calmer, with the blot on the sleeve and courage in the heart."
    )


@dataclass
class StoryParams:
    setting: str
    hero: str
    hero_type: str
    threat: str
    blot: str
    reflex: str
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


SETTINGS = {
    "lane": Setting(place="the old lane", twilight=True, affords={"walk", "hear"}),
    "yard": Setting(place="the quiet yard", twilight=True, affords={"walk", "hear"}),
    "crossing": Setting(place="the river crossing", twilight=True, affords={"walk", "hear"}),
}

THREATS = {
    "bogey": Threat(
        name="bogey",
        label="bogey",
        shadow="long and lean",
        mutter="hush-hush",
        fades_from={"light", "song", "bravery"},
        fears={"light", "noise"},
    ),
}

BLOTS = {
    "soot": "soot",
    "mud": "mud",
    "berry": "berry blot",
}

REFLEXES = {
    "shield": Reflex(
        name="shield",
        cue="the lantern flickered",
        action="she lifted her apron over the lantern flame",
        consequence="the dark could not grow any longer",
        quiets={"bogey"},
        guards={"light"},
    ),
    "stamp": Reflex(
        name="stamp",
        cue="the floorboard creaked",
        action="he stamped once, hard and brave",
        consequence="the sound sent the bogey back",
        quiets={"bogey"},
        guards={"noise"},
    ),
    "song": Reflex(
        name="song",
        cue="the wind whispered at the door",
        action="she sang a bright little tune",
        consequence="the tune made the shadows seem small",
        quiets={"bogey"},
        guards={"song"},
    ),
}

GIRL_NAMES = ["Mara", "Elsie", "Nell", "Rose", "Wren", "Tilda"]
BOY_NAMES = ["Alder", "Pip", "Jonah", "Bram", "Otis", "Finn"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale suspense storyworld with a bogey and a blot.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--blot", choices=BLOTS)
    ap.add_argument("--reflex", choices=REFLEXES)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    threat = getattr(args, "threat", None) or "bogey"
    blot = getattr(args, "blot", None) or rng.choice(list(BLOTS))
    reflex = getattr(args, "reflex", None) or rng.choice(list(REFLEXES))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    hero = getattr(args, "hero", None) or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    return StoryParams(setting=setting, hero=hero, hero_type=hero_type, threat=threat, blot=blot, reflex=reflex)


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, label=params.hero))
    threat = world.add(Entity(id="bogey", kind="thing", type="bogey", label="bogey"))
    blot = world.add(Entity(id="blot", kind="thing", type="blot", label=_safe_lookup(BLOTS, params.blot)))
    reflex = world.add(Entity(id="reflex", kind="thing", type="reflex", label=params.reflex))

    hero.location = world.setting.place
    threat.location = "shadow"
    blot.location = "sleeve"
    hero.meters["light"] = 0.0
    world.say(f"Once in {world.setting.place}, {hero.id} walked out near dusk with a careful step.")
    world.say(f"The air was still, but {hero.pronoun('possessive')} heart beat fast with a little suspense.")
    world.para()

    _blend(world, hero, threat, blot)
    world.say(f"{hero.id} felt a cold shiver, because a bogey in a folk tale is never a welcome guest.")
    world.para()

    _reflex(world, hero, reflex, threat, blot)
    world.para()

    _resolve(world, hero, threat, blot)

    world.facts.update(hero=hero, threat=threat, blot=blot, reflex=reflex, params=params)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    params = f["params"]
    return [
        f'Write a short folk tale for a child about {hero.id}, a {params.threat}, and a sudden {params.reflex}.',
        f'Create a suspenseful story where a small {hero.type} sees a bogey and uses a quick reflex to stay brave.',
        f'Write a simple tale that includes the words "bogey", "blot", and "reflex" and ends with a calm walk home.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    params = f["params"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little {params.hero_type} who walked out at dusk and met a bogey in a folk-tale kind of way.",
        ),
        QAItem(
            question=f"What made the scene feel suspenseful?",
            answer=f"It felt suspenseful because a bogey seemed to follow {hero.id}, and the darkness made every step feel careful.",
        ),
        QAItem(
            question=f"What was the blot in the story?",
            answer=f"The blot was a real mark on the cloth, not magic. It stayed behind after the scare and showed what had happened.",
        ),
        QAItem(
            question=f"What reflex helped {hero.id}?",
            answer=f"{hero.id}'s reflex was to {f['reflex'].label}. That quick move brought light or sound against the bogey and helped the fear fade.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a bogey in a folk tale?", answer="A bogey is a scary-looking creature or shadowy figure that makes a child feel uneasy, even when it may not be truly dangerous."),
        QAItem(question="What is a blot?", answer="A blot is a spot or stain, like soot, mud, or berry juice, that leaves a dark mark on cloth or paper."),
        QAItem(question="What is a reflex?", answer="A reflex is a quick action your body does almost at once, like flinching, stamping, shielding a light, or jumping back."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"{e.id}: meters={{{', '.join(f'{k}={v:g}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}={v:g}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in THREATS:
        lines.append(asp.fact("threat", tid))
    for bid in BLOTS:
        lines.append(asp.fact("blot_kind", bid))
    for rid in REFLEXES:
        lines.append(asp.fact("reflex_kind", rid))
    return "\n".join(lines)


ASP_RULES = r"""
% The world is valid when a setting, bogey, blot, and reflex exist.
valid_story(S,T,B,R) :- setting(S), threat(T), blot_kind(B), reflex_kind(R).

% Suspense comes from the bogey being shadowy and the reflex being a quick answer.
suspenseful(S,T) :- setting(S), threat(T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {(s, t, b, r) for s in SETTINGS for t in THREATS for b in BLOTS for r in REFLEXES}
    if asp_set == py_set:
        print(f"OK: ASP parity matches Python registry facts ({len(py_set)} stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in ASP:", sorted(asp_set - py_set))
    print("only in Python:", sorted(py_set - asp_set))
    return 1


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(s, t, b, r) for s in SETTINGS for t in THREATS for b in BLOTS for r in REFLEXES]


CURATED = [
    StoryParams(setting="lane", hero="Mara", hero_type="girl", threat="bogey", blot="soot", reflex="shield"),
    StoryParams(setting="yard", hero="Pip", hero_type="boy", threat="bogey", blot="mud", reflex="stamp"),
    StoryParams(setting="crossing", hero="Nell", hero_type="girl", threat="bogey", blot="berry", reflex="song"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
