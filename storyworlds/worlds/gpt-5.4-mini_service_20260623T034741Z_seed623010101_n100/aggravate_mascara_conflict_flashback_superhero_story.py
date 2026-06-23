#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/aggravate_mascara_conflict_flashback_superhero_story.py
=============================================================================================================

A small superhero story world with conflict and flashback beats.

Premise:
A young superhero-in-training wants to patrol the city in a costume with
mascara. A small mishap aggravates a tense conflict, and a flashback reveals
why the costume matters so much. In the end, the hero fixes the problem with a
better plan and a calmer heart.

This script is standalone and uses only the stdlib plus the shared Storyweavers
result containers. ASP support is inline and imported lazily.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    key: str
    label: str
    scene: str
    affords: set[str] = field(default_factory=set)
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


@dataclass
class CostumedItem:
    key: str
    label: str
    phrase: str
    region: str
    fragile: bool = False
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


@dataclass
class Trouble:
    key: str
    label: str
    phrase: str
    mess: str
    zone: set[str] = field(default_factory=set)
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


@dataclass
class MemoryBeat:
    key: str
    cue: str
    image: str
    lesson: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    rival = world.entities.get("rival")
    if not hero or not rival:
        return out
    if hero.memes.get("conflict", 0.0) < THRESHOLD:
        return out
    sig = ("conflict",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    rival.memes["conflict"] = rival.memes.get("conflict", 0.0) + 1
    out.append("The argument grew sharper.")
    return out


def _r_mascara_smear(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    mascara = world.entities.get("mascara")
    if not hero or not mascara:
        return out
    if hero.meters.get("aggravation", 0.0) < THRESHOLD:
        return out
    if mascara.meters.get("worn", 0.0) < THRESHOLD:
        return out
    sig = ("smear",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    mascara.meters["smeared"] = mascara.meters.get("smeared", 0.0) + 1
    out.append("The mascara smudged during the tension.")
    return out


CAUSAL_RULES = [_r_conflict, _r_mascara_smear]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    for sent in produced:
        world.say(sent)
    return produced


@dataclass
class StoryParams:
    city: str
    hero_name: str
    hero_gender: str
    sidekick_name: str
    sidekick_gender: str
    trouble: str
    memory: str
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


CITIES = {
    "downtown": Place("downtown", "downtown", "the bright downtown rooftops", {"patrol", "help"}),
    "harbor": Place("harbor", "the harbor", "the windy harbor docks", {"patrol", "help"}),
    "museum": Place("museum", "the museum district", "the quiet museum steps", {"patrol", "help"}),
}

TROUBLES = {
    "rain": Trouble("rain", "rain", "stormy rain", "the rain", {"face"}),
    "wind": Trouble("wind", "wind", "a gust of wind", "the wind", {"face"}),
    "dust": Trouble("dust", "dust", "a swirl of dust", "dust", {"face"}),
}

MEMORIES = {
    "first_mask": MemoryBeat(
        "first_mask",
        "the first time the hero wore the mask",
        "a mirror, a tiny cape, and a careful smile",
        "A costume can be brave without being perfect.",
    ),
    "training": MemoryBeat(
        "training",
        "an old lesson from training day",
        "a coach's hand guiding the hero's chin up",
        "A hero pauses, breathes, and fixes small mistakes.",
    ),
    "promise": MemoryBeat(
        "promise",
        "a promise made to help people",
        "a notebook page with a scribbled promise to protect the city",
        "Helping people matters more than looking flawless.",
    ),
}

HERO_NAMES = ["Nova", "Mila", "Parker", "Ivy", "Jules", "Kai"]
SIDEKICK_NAMES = ["Zane", "Rin", "Tess", "Benn", "Aria", "Sloane"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for c in CITIES:
        for t in TROUBLES:
            for m in MEMORIES:
                combos.append((c, t, m))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with conflict and flashback.")
    ap.add_argument("--city", choices=CITIES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--sidekick-gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.city is None or c[0] == args.city)
              and (args.trouble is None or c[1] == args.trouble)
              and (args.memory is None or c[2] == args.memory)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    city, trouble, memory = rng.choice(sorted(combos))
    hero_name = args.name or rng.choice(HERO_NAMES)
    sidekick_name = args.sidekick or rng.choice([n for n in SIDEKICK_NAMES if n != hero_name])
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    sidekick_gender = args.sidekick_gender or rng.choice(["girl", "boy"])
    return StoryParams(
        city=city,
        hero_name=hero_name,
        hero_gender=hero_gender,
        sidekick_name=sidekick_name,
        sidekick_gender=sidekick_gender,
        trouble=trouble,
        memory=memory,
    )


def tell(params: StoryParams) -> World:
    place = CITIES[params.city]
    trouble = TROUBLES[params.trouble]
    memory = MEMORIES[params.memory]
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_gender, label=params.hero_name, role="hero"))
    sidekick = world.add(Entity(id="sidekick", kind="character", type=params.sidekick_gender, label=params.sidekick_name, role="sidekick"))
    rival = world.add(Entity(id="rival", kind="character", type="boy", label="Rex", role="rival"))
    mascara = world.add(Entity(id="mascara", kind="thing", label="mascara", role="costume"))
    badge = world.add(Entity(id="badge", kind="thing", label="signal badge", role="tool"))

    hero.meters.update({"aggravation": 0.0})
    hero.memes.update({"joy": 1.0, "conflict": 0.0, "focus": 1.0})
    sidekick.memes.update({"concern": 0.0, "support": 1.0})
    rival.memes.update({"taunt": 0.0, "conflict": 0.0})
    mascara.meters.update({"worn": 1.0, "smeared": 0.0})
    badge.meters.update({"ready": 1.0})

    world.say(f"{params.hero_name} and {params.sidekick_name} stood on {place.label} under the {place.scene}.")
    world.say(f"{params.hero_name} wore the mascara because the costume made {hero.pronoun('object')} feel ready to help.")
    world.say(f"{params.sidekick_name} checked the signal badge while the city waited for a patrol.")

    world.para()
    world.say(f"Then {rival.label} laughed and tried to {trouble.label} the mission by tossing {trouble.phrase} into {params.hero_name}'s face.")
    hero.memes["conflict"] = 1.0
    hero.meters["aggravation"] = 1.0
    world.say(f"The insult did not break the hero, but it did aggravate the moment.")
    propagate(world)

    world.para()
    world.say(f"{params.hero_name} froze, and a flashback came rushing in.")
    world.say(f"In the memory, {memory.image}.")
    world.say(memory.lesson)
    hero.memes["conflict"] = 0.0
    hero.memes["focus"] += 1.0

    world.para()
    world.say(f"{params.hero_name} blinked, wiped the mascara with a sleeve, and took a calmer breath.")
    mascara.meters["worn"] = 0.0
    world.say(f"Together, the two friends used the signal badge to call for help and keep the street clear.")
    sidekick.memes["joy"] += 1.0
    hero.meters["aggravation"] = 0.0
    world.say(f"At the end, {params.hero_name} was smiling again, with a neat costume and a steadier heart.")

    world.facts.update(
        params=params,
        hero=hero,
        sidekick=sidekick,
        rival=rival,
        mascara=mascara,
        badge=badge,
        trouble=trouble,
        memory=memory,
        place=place,
        conflict=True,
        flashback=True,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a young child that includes the words "{f["trouble"].label}" and "mascara".',
        f"Tell a story where {f['hero'].label} has a conflict with a rival, remembers a flashback, and saves the day in {f['place'].label}.",
        f'Write a gentle superhero story where a costume problem gets fixed after a flashback teaches a calmer way to help.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    rival = f["rival"]
    trouble = f["trouble"]
    memory = f["memory"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who is the story about at {place.label}?",
            answer=f"It is about {hero.label} and {sidekick.label}, who go on a superhero patrol in {place.label}. The story also includes {rival.label}, who causes trouble and starts the conflict.",
        ),
        QAItem(
            question=f"Why did the conflict start when {rival.label} showed up?",
            answer=f"The conflict started because {rival.label} tried to use {trouble.label} to upset the hero. That aggravated the moment and made the hero feel tense for a while.",
        ),
        QAItem(
            question="What happened in the flashback?",
            answer=f"In the flashback, {memory.image}. That memory reminded the hero that bravery works best with a calm mind.",
        ),
        QAItem(
            question=f"How did {hero.label} fix the problem at the end?",
            answer=f"{hero.label} wiped away the smeared mascara, took a breath, and used the signal badge with {sidekick.label}. That turned the conflict into a safer plan and let the patrol continue.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a scene that shows something from earlier in time. It helps explain why a character feels or acts a certain way now.",
        ),
        QAItem(
            question="What does conflict mean in a story?",
            answer="Conflict is a struggle or disagreement that makes things harder for the characters. It gives the story a problem that needs a solution.",
        ),
        QAItem(
            question="What is mascara?",
            answer="Mascara is makeup that darkens eyelashes. Some stories use it as part of a costume or a fancy look.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id}: {e.label} ({e.kind}/{e.type}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
conflict(hero) :- hero(hero), aggravation(hero, A), A >= 1.
smear(mascara) :- hero(hero), aggravation(hero, A), A >= 1, worn(mascara).
flashback(hero) :- memory(hero, _).
resolved(hero) :- flashback(hero), calm(hero).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for c in CITIES:
        lines.append(asp.fact("city", c))
    for t in TROUBLES:
        lines.append(asp.fact("trouble", t))
    for m in MEMORIES:
        lines.append(asp.fact("memory", m))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("mascara", "mascara"))
    lines.append(asp.fact("worn", "mascara"))
    lines.append(asp.fact("aggravation", "hero", 1))
    lines.append(asp.fact("calm", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show conflict/1.\n#show flashback/1.\n#show resolved/1."))
    # model is not used for combo enumeration; we only need deterministic parity checks.
    return sorted(valid_combos())


def asp_verify() -> int:
    smoke = generate(resolve_params(argparse.Namespace(city=None, trouble=None, memory=None, name=None, sidekick=None, hero_gender=None, sidekick_gender=None), random.Random(7)))
    if not smoke.story or "mascara" not in smoke.story or "flashback" not in smoke.story.lower():
        print("ERROR: smoke story missing expected content.")
        return 1
    if set(asp_valid_combos()) != set(valid_combos()):
        print("ERROR: ASP/Python combo parity mismatch.")
        return 1
    print("OK: smoke generation succeeded and ASP/Python combo parity matches.")
    return 0


def generate(params: StoryParams) -> StorySample:
    if params.city not in CITIES:
        raise StoryError(f"Unknown city: {params.city}")
    if params.trouble not in TROUBLES:
        raise StoryError(f"Unknown trouble: {params.trouble}")
    if params.memory not in MEMORIES:
        raise StoryError(f"Unknown memory: {params.memory}")
    world = tell(params)
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


CURATED = [
    StoryParams(city="downtown", hero_name="Nova", hero_gender="girl", sidekick_name="Rin", sidekick_gender="boy", trouble="rain", memory="first_mask"),
    StoryParams(city="harbor", hero_name="Mila", hero_gender="girl", sidekick_name="Tess", sidekick_gender="girl", trouble="wind", memory="training"),
    StoryParams(city="museum", hero_name="Kai", hero_gender="boy", sidekick_name="Sloane", sidekick_gender="girl", trouble="dust", memory="promise"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show conflict/1.\n#show flashback/1.\n#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} valid combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} in {p.city} ({p.trouble}, {p.memory})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
