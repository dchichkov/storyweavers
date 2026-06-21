#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cootie_twist_sound_effects_lesson_learned_animal.py
===================================================================================

A standalone storyworld for a tiny animal-story domain with a playful twist:
a barnyard or forest animal hears a suspicious little sound, worries about a
"cootie," discovers the surprise behind it, and learns a gentle lesson.

The world is built for child-facing TinyStories-style output with:
- typed entities
- accumulating physical meters and emotional memes
- a small forward causal simulation
- a reasonableness gate
- grounded QA sets
- an inline ASP twin for parity checks

Theme: animal story
Seed words / instruments: cootie, twist, sound effects, lesson learned
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen"}
        male = {"boy", "father", "dad", "man", "rooster"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    sounds: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class Animal:
    id: str
    type: str
    label: str
    sound: str
    curiosity: int
    fear: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class Cootie:
    id: str
    label: str
    sound: str
    tiny: bool = True
    surprise: str = ""
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class Twist:
    id: str
    reveal: str
    lesson: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class HelpItem:
    id: str
    label: str
    effect: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


SETTINGS = {
    "barn": Setting(id="barn", place="the barn", detail="gold straw and dusty beams", sounds="rustle"),
    "orchard": Setting(id="orchard", place="the orchard", detail="apple leaves and a soft fence", sounds="swish"),
    "pond": Setting(id="pond", place="the pond", detail="reeds and round lily pads", sounds="plip"),
}

ANIMALS = {
    "rabbit": Animal(id="rabbit", type="rabbit", label="a rabbit", sound="thump-thump", curiosity=4, fear=3, tags={"animal", "forest"}),
    "mouse": Animal(id="mouse", type="mouse", label="a mouse", sound="squeak", curiosity=5, fear=4, tags={"animal", "barn"}),
    "duck": Animal(id="duck", type="duck", label="a duck", sound="waddle-splash", curiosity=3, fear=2, tags={"animal", "pond"}),
    "fox": Animal(id="fox", type="fox", label="a fox", sound="tip-tap", curiosity=6, fear=2, tags={"animal", "forest"}),
}

COOTIES = {
    "cootie": Cootie(id="cootie", label="cootie", sound="skitter-skitter", surprise="a tiny ladybug wearing a leaf hat", tags={"cootie", "tiny"}),
    "cootie_shell": Cootie(id="cootie_shell", label="cootie", sound="skritch-skratch", surprise="a little beetle hiding under a nutshell", tags={"cootie", "tiny"}),
}

TWISTS = {
    "friendly": Twist(id="friendly", reveal="it was not a scary bug at all", lesson="sometimes a strange sound is just a tiny helper trying to get by", tags={"twist", "lesson"}),
    "lost": Twist(id="lost", reveal="it was a lost baby animal looking for its mother", lesson="when something seems odd, the kind thing is to look closer and ask for help", tags={"twist", "lesson"}),
}

HELPS = {
    "listen": HelpItem(id="listen", label="quiet ears", effect="listened carefully", tags={"sound"}),
    "lamp": HelpItem(id="lamp", label="a little lamp", effect="shined a warm light", tags={"light"}),
    "call": HelpItem(id="call", label="a grown-up call", effect="called the farmer", tags={"help"}),
}


@dataclass
class StoryParams:
    setting: str
    animal: str
    cootie: str
    twist: str
    help_item: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld with cootie, twist, sound effects, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--cootie", choices=COOTIES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--help-item", choices=HELPS)
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


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    return [(s, a, c, t, h) for s in SETTINGS for a in ANIMALS for c in COOTIES for t in TWISTS for h in HELPS]


CURATED = [
    StoryParams(setting="barn", animal="mouse", cootie="cootie", twist="friendly", help_item="listen"),
    StoryParams(setting="orchard", animal="rabbit", cootie="cootie_shell", twist="lost", help_item="lamp"),
    StoryParams(setting="pond", animal="duck", cootie="cootie", twist="friendly", help_item="call"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    keys = valid_combos()
    setting = args.setting or rng.choice(list(SETTINGS))
    animal = args.animal or rng.choice(list(ANIMALS))
    cootie = args.cootie or rng.choice(list(COOTIES))
    twist = args.twist or rng.choice(list(TWISTS))
    help_item = args.help_item or rng.choice(list(HELPS))
    if (setting, animal, cootie, twist, help_item) not in keys:
        raise StoryError("The requested animal story combination is not reasonable in this tiny world.")
    return StoryParams(setting=setting, animal=animal, cootie=cootie, twist=twist, help_item=help_item)


def _sound(world: World, who: Entity, sfx: str) -> None:
    who.memes["alert"] += 1
    world.say(f"{sfx}!")


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    animal_cfg = ANIMALS[params.animal]
    cootie_cfg = COOTIES[params.cootie]
    twist_cfg = TWISTS[params.twist]
    help_cfg = HELPS[params.help_item]

    animal = world.add(Entity(id="animal", kind="character", type=animal_cfg.type, label=animal_cfg.label, tags=set(animal_cfg.tags)))
    friend = world.add(Entity(id="friend", kind="character", type="girl", label="a small friend", tags={"animal"}))
    cootie = world.add(Entity(id="cootie", kind="thing", type="thing", label=cootie_cfg.label, tags=set(cootie_cfg.tags)))
    helper = world.add(Entity(id="helper", kind="character", type="mother", label="the grown-up", tags={"help"}))
    spot = world.add(Entity(id="spot", kind="thing", type="thing", label=setting.place, tags=set(setting.tags)))

    animal.memes["curiosity"] += animal_cfg.curiosity
    animal.memes["fear"] += animal_cfg.fear
    friend.memes["curiosity"] += 2
    world.facts["setting"] = setting
    world.facts["animal_cfg"] = animal_cfg
    world.facts["cootie_cfg"] = cootie_cfg
    world.facts["twist_cfg"] = twist_cfg
    world.facts["help_cfg"] = help_cfg

    world.say(f"In {setting.place}, {animal.label} and {friend.label_word} played near {setting.detail}.")
    world.say(f"{animal.label_word.capitalize()} heard {setting.sounds}-{setting.sounds} and then {cootie_cfg.sound} from the hay.")

    world.para()
    _sound(world, animal, animal_cfg.sound)
    world.say(f'"Cootie!" {animal.label_word} whispered, and {friend.label_word} blinked at the little {cootie_cfg.label}.')
    animal.memes["fear"] += 1
    friend.memes["curiosity"] += 1

    world.para()
    _sound(world, friend, help_cfg.effect.replace(" ", "-"))
    if params.help_item == "listen":
        world.say(f"{friend.label_word.capitalize()} said, \"Wait. Listen again.\"")
    elif params.help_item == "lamp":
        world.say(f"{friend.label_word.capitalize()} shined the lamp, and the dark corner turned gold.")
    else:
        world.say(f"{friend.label_word.capitalize()} called the grown-up, because little worries are bigger when they stay alone.")

    world.para()
    cootie.meters["seen"] += 1
    world.say(f"Twist: {twist_cfg.reveal}.")
    world.say(f"Under the straw, the tiny {cootie_cfg.label} was really {cootie_cfg.surprise}.")

    world.para()
    helper.memes["warmth"] += 1
    animal.memes["relief"] += 2
    friend.memes["relief"] += 2
    world.say(f"The grown-up came with calm steps and a soft smile.")
    world.say(f"{twist_cfg.lesson.capitalize()}.")
    world.say(f"After that, {animal.label_word} laughed, {friend.label_word} laughed, and the little {cootie_cfg.label} got a safe new home outside.")

    world.facts.update(animal=animal, friend=friend, cootie=cootie, helper=helper, spot=spot, outcome="lesson")
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story that includes the word "cootie" and ends with a lesson learned.',
        f"Tell a child-friendly animal story where {f['animal_cfg'].label_word} hears a funny little sound, thinks of a cootie, and discovers a twist.",
        f"Write a short story with sound effects, a twist, and a kind lesson about a tiny cootie in {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    animal = f["animal"]
    friend = f["friend"]
    cootie = f["cootie"]
    twist = f["twist_cfg"]
    setting = f["setting"]
    help_cfg = f["help_cfg"]
    return [
        ("Who is the story about?", f"It is about {animal.label_word} and {friend.label_word} in {setting.place}. They hear a strange sound and then learn what it really is."),
        ("What sound did they hear?", f"They heard {f['animal_cfg'].sound} and then {cootie.sound}. Those sounds made them pause and look more closely."),
        ("What was the twist?", f"The twist was that {twist.reveal}. That changed the scary idea into something small and gentle."),
        ("What did they do to help?", f"They {help_cfg.effect} and looked again instead of guessing too fast. That helped them understand the sound without getting upset."),
        ("What lesson did they learn?", f"{twist.lesson.capitalize()}. The story ends with everyone calmer because they learned to look twice."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a cootie in this story?", "Here, a cootie is a tiny creature the animals notice in the straw. It is so small that it sounds bigger than it really is."),
        ("What does a twist do in a story?", "A twist changes what you think is happening. It makes the story surprising, but the ending still makes sense."),
        ("Why do sound effects matter?", "Sound effects help the reader hear the moment in their head. They make the scene feel lively and playful."),
        ("What is a lesson learned?", "A lesson learned is the helpful idea the characters remember at the end. It is what they carry away from the story."),
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for cid in COOTIES:
        lines.append(asp.fact("cootie", cid))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    for hid in HELPS:
        lines.append(asp.fact("help_item", hid))
    return "\n".join(lines)


ASP_RULES = r"""
chosen_story(S,A,C,T,H) :- setting(S), animal(A), cootie(C), twist(T), help_item(H).
#show chosen_story/5.
"""

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show chosen_story/5."))
    return sorted(set(asp.atoms(model, "chosen_story")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python combos.")
    try:
        sample = generate(CURATED[0])
        assert sample.story and sample.prompts and sample.story_qa and sample.world_qa
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    animal = args.animal or rng.choice(list(ANIMALS))
    cootie = args.cootie or rng.choice(list(COOTIES))
    twist = args.twist or rng.choice(list(TWISTS))
    help_item = args.help_item or rng.choice(list(HELPS))
    if (setting, animal, cootie, twist, help_item) not in valid_combos():
        raise StoryError("That animal story combination is not available.")
    return StoryParams(setting=setting, animal=animal, cootie=cootie, twist=twist, help_item=help_item)


def valid_story_filter(params: StoryParams) -> bool:
    return (params.setting, params.animal, params.cootie, params.twist, params.help_item) in valid_combos()


def generate_many(args: argparse.Namespace, base_seed: int) -> list[StorySample]:
    samples = []
    seen = set()
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
    return samples


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show chosen_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for row in combos[:50]:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = [generate(p) for p in CURATED] if args.all else generate_many(args, base_seed)

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
            header = f"### {p.setting} / {p.animal} / {p.cootie} / {p.twist}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
