#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402



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
    carried_by: Optional[str] = None
    hidden_in: str = ""
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "man", "grandfather", "uncle"}
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
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)
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
class Mystery:
    id: str
    clue: str
    clue2: str
    clue3: str
    reveal: str
    shadow: str
    foreshadow: str
    phenomenon: str
    tags: set[str] = field(default_factory=set)
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
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

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
    mystery: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None
    params: object | None = None
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
    "museum": Setting(place="the old museum", mood="quiet", affords={"echoes", "glow", "dust"}),
    "garden": Setting(place="the moonlit garden", mood="hushed", affords={"glow", "tracks", "whisper"}),
    "attic": Setting(place="the attic", mood="still", affords={"dust", "whisper", "glow"}),
}

MYSTERIES = {
    "lantern": Mystery(
        id="lantern",
        clue="a faint gold glow on the floor",
        clue2="tiny round tracks by the shelf",
        clue3="a soft tinkling sound from the dark corner",
        reveal="a glowing firefly lantern had been hiding behind a velvet curtain",
        shadow="something bright was making the room feel less empty",
        foreshadow="the gold glow looked like it wanted to be found",
        phenomenon="glow",
        tags={"glow", "mystery", "fantastic"},
    ),
    "music_box": Mystery(
        id="music_box",
        clue="a little tune humming under the dust",
        clue2="two delicate footprints in the ash",
        clue3="a silver key lying beside a cracked frame",
        reveal="a tiny clockwork music box was tucked inside a hollow book",
        shadow="the tune had been leading them all along",
        foreshadow="the careful footprints were a hint that the mystery was small and clever",
        phenomenon="whisper",
        tags={"whisper", "mystery", "fantastic"},
    ),
    "star_map": Mystery(
        id="star_map",
        clue="bright specks shaped like a trail",
        clue2="a paper corner folded into a sharp point",
        clue3="a cold breeze that seemed to point at the ceiling",
        reveal="a hidden star map was pinned above the beams with a silver tack",
        shadow="the specks matched the path to the roof beam",
        foreshadow="the breeze and specks were whispering about the ceiling",
        phenomenon="dust",
        tags={"dust", "mystery", "fantastic"},
    ),
}


class World:
    def __init__(self, setting: Setting, mystery: Mystery) -> None:
        self.setting = setting
        self.mystery = mystery
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def spooky_hint(world: World, hero: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} noticed {world.mystery.clue}. It felt {world.mystery.foreshadow}, "
        f"so {hero.pronoun()} slowed down and looked again."
    )


def second_hint(world: World, helper: Entity) -> None:
    helper.memes["attention"] += 1
    world.say(
        f"{helper.id} pointed to {world.mystery.clue2}. "
        f"That made the first clue feel less random and more like a trail."
    )


def third_hint(world: World, hero: Entity) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"Then {hero.id} heard {world.mystery.clue3}. "
        f"The sound was tiny, but it carried a huge question."
    )


def reveal(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"At last, {world.mystery.reveal}. "
        f"The answer fit the clues so neatly that the room seemed to breathe again."
    )
    world.say(
        f"{hero.id} smiled at {helper.id}, because the mystery had been strange, "
        f"but not frightening in the end."
    )


def tell_story(setting: Setting, mystery: Mystery, hero_name: str, hero_type: str,
               helper_name: str, helper_type: str) -> World:
    world = World(setting, mystery)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))

    world.say(
        f"One quiet evening at {setting.place}, {hero.id} and {helper.id} went looking "
        f"for a missing thing that had vanished without a sound."
    )
    world.say(
        f"The room felt {setting.mood}, and the air carried a {mystery.phenomenon} "
        f"that made everything seem a little fantastic."
    )
    world.para()

    spooky_hint(world, hero)
    second_hint(world, helper)
    world.para()
    third_hint(world, hero)
    world.say(
        f"{world.mystery.shadow.capitalize()}, and that made the last corner worth checking."
    )
    world.para()
    reveal(world, hero, helper)

    world.facts.update(
        hero=hero,
        helper=helper,
        setting=setting,
        mystery=mystery,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short mystery story for a child about {f['hero'].id} and a strange clue at {f['setting'].place}.",
        f"Tell a fantastic but gentle story where {f['helper'].id} helps solve a mystery using small clues and a calm ending.",
        f"Write a simple story that begins with a hidden hint, grows into a careful search, and ends with the answer revealed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, mystery, setting = f["hero"], f["helper"], f["mystery"], f["setting"]
    return [
        QAItem(
            question=f"Where did {hero.id} and {helper.id} look for the missing thing?",
            answer=f"They looked at {setting.place}, where the air felt {setting.mood} and full of mystery.",
        ),
        QAItem(
            question=f"What was the first clue {hero.id} noticed?",
            answer=f"The first clue was {mystery.clue}. It was small, but it hinted that something magical was nearby.",
        ),
        QAItem(
            question=f"What did the clues finally lead to?",
            answer=f"They led to the truth that {mystery.reveal}. The clues all pointed to that answer.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"{hero.id} ended the story feeling relieved and curious, because the mystery had been solved.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "mystery": [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not known at first, so people look for clues to figure it out.",
        )
    ],
    "fantastic": [
        QAItem(
            question="What does fantastic mean in a story?",
            answer="Fantastic means the story has something magical, unusual, or delightfully impossible.",
        )
    ],
    "glow": [
        QAItem(
            question="What is a glow?",
            answer="A glow is a soft light that shines gently instead of flashing brightly.",
        )
    ],
    "whisper": [
        QAItem(
            question="What is a whisper?",
            answer="A whisper is a very quiet way of speaking.",
        )
    ],
    "dust": [
        QAItem(
            question="What is dust?",
            answer="Dust is made of tiny bits that gather on surfaces when places are left alone for a while.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.mystery.tags)
    out: list[QAItem] = []
    for tag in ("mystery", "fantastic", "glow", "whisper", "dust"):
        if tag in tags or tag in {"mystery", "fantastic"}:
            out.extend(WORLD_KNOWLEDGE[tag])
    return out


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
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  mystery: {world.mystery.id}")
    return "\n".join(lines)


ASP_RULES = r"""
setting_old_museum.
setting_moonlit_garden.
setting_attic.

mystery_lantern.
mystery_music_box.
mystery_star_map.

valid(S, M) :- setting(S), mystery(M).
"""
def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = {(s, m) for s in SETTINGS for m in MYSTERIES}
    asp_set = set(asp_valid_pairs())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid pairs ({len(asp_set)}).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in asp:", sorted(asp_set - python_set))
    print("only in python:", sorted(python_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fantastic mystery storyworld with foreshadowing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["mother", "father", "girl", "boy"])
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
    mystery = getattr(args, "mystery", None) or rng.choice(list(MYSTERIES))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    helper_type = getattr(args, "helper_type", None) or rng.choice(["mother", "father"])
    hero_name = getattr(args, "hero_name", None) or rng.choice(["Mina", "Iris", "Theo", "Nico", "Lena", "Ari"])
    helper_name = getattr(args, "helper_name", None) or rng.choice(["June", "Parker", "Mara", "Eli", "Sage"])
    return StoryParams(
        setting=setting,
        mystery=mystery,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(MYSTERIES, params.mystery),
        params.hero_name,
        params.hero_type,
        params.helper_name,
        params.helper_type,
    )
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

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} valid setting/mystery pairs:")
        for s, m in pairs:
            print(f"  {s:10} {m}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for s in SETTINGS:
            for m in MYSTERIES:
                params = StoryParams(
                    setting=s,
                    mystery=m,
                    hero_name="Mina",
                    hero_type="girl",
                    helper_name="June",
                    helper_type="mother",
                )
                samples.append(generate(params))
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
            header = f"### {p.setting} / {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
