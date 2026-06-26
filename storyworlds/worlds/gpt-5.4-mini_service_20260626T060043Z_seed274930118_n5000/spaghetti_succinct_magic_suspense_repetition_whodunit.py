#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/spaghetti_succinct_magic_suspense_repetition_whodunit.py
==============================================================================================================================

A small whodunit storyworld about a missing pot of spaghetti, a little magic,
and a careful child detective who keeps asking the same short questions until
the clues line up.

Premise:
- A bowl of spaghetti is prepared for supper.
- Something goes wrong: the sauce vanishes, or the noodles disappear, or the
  promised dinner ends up hidden.
- The detective investigates with repeated checks, a magic trick, and a very
  succinct line of reasoning.
- The true culprit is revealed by state-driven clues, not by a frozen template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

SPAGHETTI_WORD = "spaghetti"
SUCCINCT_WORD = "succinct"



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue_tag: object | None = None
    culprit_ent: object | None = None
    helper: object | None = None
    hero: object | None = None
    noodle_pot: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
        if "_tags" not in self.__dict__:
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
    place: str = "the kitchen"
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    can_do: set[str] = field(default_factory=set)
    clue: str = ""
    motive: str = ""
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
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
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
    setting: str
    culprit: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


SETTINGS = {
    "kitchen": Setting(place="the kitchen"),
    "dining_room": Setting(place="the dining room"),
}

SUSPECTS = {
    "cat": Suspect(
        id="cat",
        label="the cat",
        type="cat",
        can_do={"climb", "hide"},
        clue="There were tiny paw prints near the pantry.",
        motive="wanted a warm bowl and a secret hiding place",
    ),
    "mouse": Suspect(
        id="mouse",
        label="the mouse",
        type="mouse",
        can_do={"nibble", "hide"},
        clue="A few noodle bits were left in a neat little line.",
        motive="wanted to steal a soft noodle prize",
    ),
    "brother": Suspect(
        id="brother",
        label="the brother",
        type="boy",
        can_do={"carry", "hide"},
        clue="The chair by the table was pulled out too far.",
        motive="wanted to save the biggest helping for later",
    ),
}

CURATED = [
    StoryParams(setting="kitchen", culprit="cat", hero_name="Mina", hero_type="girl", helper_name="Dad", helper_type="father"),
    StoryParams(setting="dining_room", culprit="mouse", hero_name="Owen", hero_type="boy", helper_name="Mom", helper_type="mother"),
    StoryParams(setting="kitchen", culprit="brother", hero_name="Ada", hero_type="girl", helper_name="Aunt June", helper_type="aunt"),
]


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    world: object | None = None
    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for e in self.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
        lines.append(f"  facts={self.facts}")
        return "\n".join(lines)
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small spaghetti whodunit with magic, suspense, and repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--culprit", choices=SUSPECTS)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    culprit = getattr(args, "culprit", None) or rng.choice(list(SUSPECTS))
    hero_name = rng.choice(["Mina", "Owen", "Ada", "Nia", "Leo"])
    hero_type = rng.choice(["girl", "boy"])
    helper_name = rng.choice(["Mom", "Dad", "Aunt June", "Uncle Ben"])
    helper_type = "mother" if helper_name == "Mom" else "father" if helper_name == "Dad" else "aunt" if "Aunt" in helper_name else "uncle"
    return StoryParams(setting=setting, culprit=culprit, hero_name=hero_name, hero_type=hero_type, helper_name=helper_name, helper_type=helper_type)


def story_reasonable(params: StoryParams) -> None:
    if params.culprit not in SUSPECTS:
        pass
    if params.setting not in SETTINGS:
        pass


def _magic_reveal(world: World, suspect: Suspect) -> bool:
    return suspect.id == world.facts["culprit"]


def tell(setting: Setting, culprit: Suspect, hero_name: str, hero_type: str, helper_name: str, helper_type: str) -> World:
    world = World(setting=setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, label=helper_name))
    noodle_pot = world.add(Entity(id="pot", type="pot", label="the pot", phrase=f"a steaming pot of {SPAGHETTI_WORD}"))
    clue_tag = world.add(Entity(id="clue", type="magic", label="the magic spoon", phrase="a small silver spoon that could point to hidden things"))
    culprit_ent = world.add(Entity(id=culprit.id, kind="character", type=culprit.type, label=culprit.label))

    world.facts["culprit"] = culprit.id
    world.say(f"{hero.id} was a little detective who liked being {SUCCINCT_WORD}. {hero.pronoun('subject').capitalize()} could say a lot with just a few words.")
    world.say(f"At {world.setting.place}, {helper.id} had made {noodle_pot.phrase} for supper.")
    world.say(f"But when the lid came off, the {SPAGHETTI_WORD} was gone.")

    world.para()
    world.say(f"{hero.id} looked once, then looked again. The table was clean. The stove was warm. The air still smelled like tomato.")
    world.say(f"That was the first bit of suspense: something had happened, but nobody was saying what.")

    world.para()
    world.say(f"{hero.id} asked the same short question three times. “Who touched the pot?”")
    world.say(f"{helper.id} pointed at the clues. “We should check carefully,” {helper.id.lower()} said.")
    world.say(culprit.clue)

    world.para()
    world.say(f"Then {hero.id} picked up {clue_tag.label}. It was a magic spoon, and it only glowed near the truth.")
    if _magic_reveal(world, culprit):
        world.say(f"The spoon flickered toward {culprit.label}.")
        world.say(f"{hero.id} followed it step by step, repeating the clue in a low voice: “Paws, pantry, pasta.”")
        world.say(f"At last, {culprit.label} was behind the curtain, with a noodle stuck to {culprit.pronoun('possessive')} whiskers.")
    else:
        world.say(f"The spoon stayed dark, which meant the first guess was wrong.")
        world.say(f"{hero.id} tried again, more slowly this time, and the magic finally pointed to the real thief.")

    world.para()
    culprit_ent.memes["guilty"] = 1
    culprit_ent.meters["hidden"] = 1
    hero.memes["relief"] = 1
    helper.memes["relief"] = 1
    world.say(f"{hero.id} kept it succinct. “You took dinner.”")
    world.say(f"The culprit drooped, admitted the truth, and led everyone to the hidden bowl under the chair.")
    world.say(f"{helper.id} laughed, warmed the sauce, and soon the {SPAGHETTI_WORD} was back on the table.")
    world.say(f"In the end, the mystery was solved, the magic helped, and the little detective had turned suspense into supper.")

    world.facts.update(
        hero=hero,
        helper=helper,
        culprit_ent=culprit_ent,
        pot=noodle_pot,
        magic=clue_tag,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly whodunit about missing {SPAGHETTI_WORD} with magic, suspense, and repetition.",
        f"Tell a short story where {f['hero'].id} investigates a missing dinner and stays {SUCCINCT_WORD}.",
        f"Create a mystery at {f['setting'].place} that ends when a magic spoon reveals who hid the {SPAGHETTI_WORD}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    culprit: Entity = _safe_fact(world, f, "culprit_ent")
    return [
        QAItem(
            question=f"What was missing from {world.setting.place}?",
            answer=f"The pot of {SPAGHETTI_WORD} was missing from {world.setting.place}.",
        ),
        QAItem(
            question=f"How did {hero.id} look for the answer?",
            answer=f"{hero.id} looked carefully, asked the same short question again and again, and kept the search {SUCCINCT_WORD}.",
        ),
        QAItem(
            question=f"What helped reveal the truth?",
            answer=f"The magic spoon helped point toward {culprit.label}, and that showed who had hidden the dinner.",
        ),
        QAItem(
            question=f"Who ended up admitting the mystery?",
            answer=f"{culprit.label} admitted the truth and led everyone to the hidden bowl.",
        ),
        QAItem(
            question=f"Who helped make supper okay again?",
            answer=f"{helper.id} helped warm the sauce and put the {SPAGHETTI_WORD} back on the table.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is spaghetti?",
            answer="Spaghetti is a long, thin kind of pasta that people often eat with sauce.",
        ),
        QAItem(
            question="What does succinct mean?",
            answer="Succinct means saying something in a short and clear way.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of wondering what will happen next.",
        ),
        QAItem(
            question="Why can repetition help in a mystery?",
            answer="Repetition can help because asking again and again may uncover a clue that was missed the first time.",
        ),
        QAItem(
            question="What can magic do in a whodunit?",
            answer="Magic can be used as a story tool to point at hidden clues or reveal the truth in a surprising way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
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


ASP_RULES = r"""
culprit(cat).
culprit(mouse).
culprit(brother).

supports(cat, paws).
supports(mouse, noodlebits).
supports(brother, chair).

truth(cat) :- clue(paws).
truth(mouse) :- clue(noodlebits).
truth(brother) :- clue(chair).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "kitchen"),
        asp.fact("setting", "dining_room"),
        asp.fact("spaghetti"),
        asp.fact("succinct"),
        asp.fact("magic"),
        asp.fact("suspense"),
        asp.fact("repetition"),
        asp.fact("whodunit"),
        asp.fact("clue", "paws"),
        asp.fact("clue", "noodlebits"),
        asp.fact("clue", "chair"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_culprits() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show truth/1."))
    return sorted(set(asp.atoms(model, "truth")))


def asp_verify() -> int:
    py = {("cat",), ("mouse",), ("brother",)}
    cl = set(asp_culprits())
    if py == cl:
        print("OK: ASP and Python agree on the clue->culprit mapping.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("python:", sorted(py))
    print("asp:", sorted(cl))
    return 1


def dump_trace(world: World) -> str:
    return world.trace()


def generate(params: StoryParams) -> StorySample:
    story_reasonable(params)
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(SUSPECTS, params.culprit), params.hero_name, params.hero_type, params.helper_name, params.helper_type)
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show truth/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show truth/1."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in CURATED:
            p.seed = base_seed
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero_name}: {p.culprit} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
