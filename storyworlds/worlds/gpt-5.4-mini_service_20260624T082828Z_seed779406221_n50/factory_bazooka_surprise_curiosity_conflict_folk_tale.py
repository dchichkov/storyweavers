#!/usr/bin/env python3
"""
factory_bazooka_surprise_curiosity_conflict_folk_tale.py
=========================================================

A small folk-tale storyworld about a clever child or animal helper at a factory,
where curiosity bumps into conflict and ends in a surprising, safe discovery.

Premise seed:
- A factory makes toys, trinkets, or festival goods.
- Someone finds a bazooka-like launcher, but in this world it is not a weapon;
  it is a silly surprise launcher that shoots ribbons, petals, or paper stars.
- Curiosity draws the hero toward it.
- Conflict appears when an adult or elder worries the machine is too loud or too
  risky.
- The ending turns on a gentle test, so the hero learns what the bazooka really
  does and the factory gets a new happy use.

The world model tracks both physical meters and emotional memes:
- Surprise
- Curiosity
- Conflict

The prose is intentionally authored in a folk-tale style: simple, concrete,
and causal, with a beginning, middle turn, and ending image.
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
            keys = [upper, upper + "S", upper + "ES"]
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    baz: object | None = None
    elder: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "aunt"}
        male = {"boy", "father", "man", "king", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

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
    place: str
    indoors: bool = True
    mood: str = "humming"
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
class Artifact:
    id: str
    label: str
    phrase: str
    reveal: str
    use: str
    sound: str
    surprise: str
    covers: set[str] = field(default_factory=set)
    safe: bool = True
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
class StoryParams:
    place: str
    artifact: str
    hero: str
    hero_type: str
    elder_type: str
    trait: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def join_clause(*parts: str) -> str:
    return " ".join(p for p in parts if p)


SETTINGS = {
    "bell_foundry": Setting(place="the bell factory", indoors=True, mood="ringing"),
    "paper_mill": Setting(place="the paper factory", indoors=True, mood="rustling"),
    "toy_shop_floor": Setting(place="the toy factory", indoors=True, mood="bright"),
}

ARTIFACTS = {
    "confetti_bazooka": Artifact(
        id="confetti_bazooka",
        label="bazooka",
        phrase="a painted bazooka with a round wooden grip",
        reveal="it launched a burst of confetti, ribbon, and paper stars",
        use="launch confetti for the festival",
        sound="whump",
        surprise="a spray of confetti and stars",
        covers={"floor"},
        safe=True,
    ),
    "bubble_bazooka": Artifact(
        id="bubble_bazooka",
        label="bazooka",
        phrase="a brass bazooka with a curly hose",
        reveal="it blew out a cloud of soap bubbles",
        use="blow bubbles over the worktables",
        sound="poof",
        surprise="a cloud of bright bubbles",
        covers={"air"},
        safe=True,
    ),
    "flower_bazooka": Artifact(
        id="flower_bazooka",
        label="bazooka",
        phrase="a flower-painted bazooka with a long tube",
        reveal="it tossed out flower petals like soft rain",
        use="scatter petals for a feast day",
        sound="fwump",
        surprise="a shower of petals",
        covers={"floor", "table"},
        safe=True,
    ),
}

TRAITS = ["curious", "bright-eyed", "patient", "gentle", "brave", "earnest"]
HERO_TYPES = ["girl", "boy"]
ELDER_TYPES = ["father", "mother", "uncle", "aunt", "grandfather", "grandmother"]
NAMES = ["Mina", "Pip", "Lina", "Tob", "Nori", "Bram", "Sela", "Jory"]


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
    for aid, a in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aid))
        lines.append(asp.fact("label", aid, a.label))
        lines.append(asp.fact("safe", aid))
    return "\n".join(lines)


ASP_RULES = r"""
% The world is reasonable if the bazooka is a safe surprise device.
reasonable(A) :- artifact(A), safe(A).

% A valid story is one in a factory setting with a safe bazooka.
valid_story(S, A) :- setting(S), artifact(A), reasonable(A), indoors(S).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place in SETTINGS:
        for artifact in ARTIFACTS:
            out.append((place, artifact))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale factory storyworld with a surprising bazooka.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--artifact", choices=ARTIFACTS.keys())
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=HERO_TYPES)
    ap.add_argument("--elder", choices=ELDER_TYPES)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "artifact", None):
        combos = [c for c in combos if c[1] == getattr(args, "artifact", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, artifact = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(HERO_TYPES)
    hero = getattr(args, "hero", None) or rng.choice(NAMES)
    elder = getattr(args, "elder", None) or rng.choice(ELDER_TYPES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, artifact=artifact, hero=hero, hero_type=gender, elder_type=elder, trait=trait)


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    artifact = f["artifact"]
    setting = f["setting"]
    qa = [
        QAItem(
            question=f"Where did {hero.id} find the bazooka?",
            answer=f"{hero.id} found the bazooka at {setting.place}, where the worktables hummed and the lamps shone.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel curious about the bazooka?",
            answer=f"{hero.id} felt curious because the bazooka sat under a cloth and looked like it was hiding a surprise.",
        ),
        QAItem(
            question=f"Why did {elder.pronoun('subject').capitalize()} worry at first?",
            answer=f"{elder.pronoun('subject').capitalize()} worried because a loud bazooka in a factory could cause trouble if nobody knew what it did.",
        ),
    ]
    if f.get("conflict"):
        qa.append(
            QAItem(
                question=f"What caused the conflict in the factory?",
                answer=f"The conflict began when {hero.id} wanted to try the bazooka right away, but {elder.id} was afraid it might be unsafe.",
            )
        )
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did the story end with the bazooka?",
                answer=f"It ended safely: {artifact.reveal}, so the factory could use it for a feast-day surprise.",
            )
        )
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a factory?",
            answer="A factory is a place where people or helpers make things together, often with tools, tables, and noisy machines.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn more about something new.",
        ),
        QAItem(
            question="What is conflict?",
            answer="Conflict is when two wants bump into each other, like wanting to try something and wanting to keep it safe.",
        ),
        QAItem(
            question="What is a bazooka in this storyworld?",
            answer="In this storyworld, a bazooka is a silly surprise launcher, not a weapon. It sends out confetti, bubbles, or petals.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short folk tale about a curious child in a factory who finds a bazooka that is really a surprise launcher.",
        f"Tell a gentle story where {f['hero'].id} and {f['elder'].id} disagree about a bazooka in {f['setting'].place}, then discover its safe use.",
        f"Write a child-friendly factory tale with surprise, curiosity, and conflict, and end with {f['artifact'].label} used for a happy celebration.",
    ]


def tell(setting: Setting, artifact: Artifact, hero_name: str, hero_type: str, elder_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait]))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, label="the elder"))
    baz = world.add(Entity(id="Bazooka", type="artifact", label="bazooka", phrase=artifact.phrase))
    world.facts.update(hero=hero, elder=elder, artifact=baz, setting=setting, artifact_cfg=artifact)

    world.say(f"Once, in {setting.place}, there lived a little {trait} {hero.type} named {hero.id}.")
    world.say(f"{hero.id} liked the hum of the machines and the soft clatter of the worktables.")
    world.say(f"One day, {hero.id} saw {artifact.phrase} hidden beneath a cloth.")
    hero.memes["curiosity"] = 1
    hero.memes["surprise"] = 1
    world.say(f"{hero.id} blinked in {join_clause('surprise', 'and wonder')} and leaned closer, because the strange thing looked like it wanted to tell a story.")

    world.para()
    world.say(f"{hero.id} asked what the bazooka was for, and {elder.id} frowned a little.")
    elder.memes["conflict"] = 1
    hero.memes["curiosity"] = 2
    world.say(f'"Not yet," said {elder.id}. "A loud bazooka could make a mess if we do not know its use."')
    world.say(f"But {hero.id} could not stop wondering, and that made the air feel tight with conflict.")

    world.para()
    world.say(f"{hero.id} and {elder.id} stood by the machine and listened to its little metal clicks.")
    world.say(f"{hero.id} noticed a painted sign that said it would {artifact.use}.")
    hero.memes["surprise"] = 2
    world.say(f'Then {hero.id} pulled the cord, and the bazooka went "{artifact.sound}!"')
    world.say(f"Out came {artifact.reveal}, shining bright as bits of festival sky.")
    elder.memes["conflict"] = 0
    world.say(f"{elder.id} laughed in relief, because the bazooka was not a danger at all; it was a surprise for happy days.")
    world.say(f"By dusk, the factory was sprinkled with {artifact.surprise}, and {hero.id} was smiling beside the warm machines.")

    world.facts["conflict"] = True
    world.facts["resolved"] = True
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ARTIFACTS, params.artifact), params.hero, params.hero_type, params.elder_type, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x for x, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="bell_foundry", artifact="confetti_bazooka", hero="Mina", hero_type="girl", elder_type="grandmother", trait="curious"),
    StoryParams(place="paper_mill", artifact="bubble_bazooka", hero="Pip", hero_type="boy", elder_type="father", trait="earnest"),
    StoryParams(place="toy_shop_floor", artifact="flower_bazooka", hero="Lina", hero_type="girl", elder_type="aunt", trait="bright-eyed"),
]


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify_and_report() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def valid_story_reasonable(params: StoryParams) -> bool:
    return params.place in SETTINGS and params.artifact in ARTIFACTS


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

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify_and_report())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, artifact) combos:\n")
        for setting, artifact in combos:
            print(f"  {setting:16} {artifact}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero}: {p.artifact} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
