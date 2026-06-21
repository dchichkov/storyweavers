#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/slippery_neighborhood_park_cautionary_magic_friendship_whodunit.py
===================================================================================================

A standalone storyworld for a small neighborhood-park whodunit with a cautionary,
magical, friendship-centered feel.

Premise
-------
Two friends walk through a neighborhood park after rain. Something is slippery,
a little magic is involved, and they must solve a small mystery without blaming
the wrong person. The story should feel like a child-safe whodunit: clues,
suspects, a careful reveal, and a friendly ending.

The world model tracks:
- who is present,
- physical meters like slipperiness, dropped items, and evidence,
- emotional memes like worry, trust, and relief,
- a simple causal chain from slippery ground -> mishap -> clue trail -> reveal.

This file is self-contained and uses only the stdlib plus the shared result
containers. ASP rules are inline as a twin to the Python validity gate.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/slippery_neighborhood_park_cautionary_magic_friendship_whodunit.py
    python storyworlds/worlds/gpt-5.4-mini/slippery_neighborhood_park_cautionary_magic_friendship_whodunit.py --all
    python storyworlds/worlds/gpt-5.4-mini/slippery_neighborhood_park_cautionary_magic_friendship_whodunit.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/slippery_neighborhood_park_cautionary_magic_friendship_whodunit.py --verify
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)
    suspicious: bool = False
    magical: bool = False

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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    clue_place: str
    cover_phrase: str
    weather: str
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Friend:
    id: str
    type: str
    label: str
    caution: str
    magic_skill: str
    tell: str
    role: str
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Mystery:
    id: str
    culprit: str
    object_moved: str
    object_label: str
    object_place: str
    trace: str
    reveal: str
    suspicious: bool = True
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class StoryParams:
    setting: str
    mystery: str
    friend1: str
    friend2: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_slip(world: World) -> list[str]:
    out = []
    park = world.get("park")
    if park.meters["slippery"] < THRESHOLD:
        return out
    if ("slip",) in world.fired:
        return out
    world.fired.add(("slip",))
    for kid in (world.get("friend1"), world.get("friend2")):
        kid.memes["worry"] += 1
    park.meters["evidence"] += 1
    out.append("__slip__")
    return out


def _r_magic_clue(world: World) -> list[str]:
    out = []
    spark = world.get("spark")
    if spark.meters["glow"] < THRESHOLD or ("clue",) in world.fired:
        return out
    world.fired.add(("clue",))
    world.get("path").meters["evidence"] += 1
    world.get("friend2").memes["confidence"] += 1
    out.append("__clue__")
    return out


CAUSAL_RULES = [Rule("slip", _r_slip), Rule("clue", _r_magic_clue)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for mystery in MYSTERIES:
            for f1 in FRIENDS:
                for f2 in FRIENDS:
                    if f1 != f2:
                        combos.append((setting, mystery, f1, f2))
    return combos


def is_reasonable(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.mystery in MYSTERIES and params.friend1 in FRIENDS and params.friend2 in FRIENDS and params.friend1 != params.friend2


def _do_slip(world: World, narrate: bool = True) -> None:
    world.get("park").meters["slippery"] += 1
    propagate(world, narrate=narrate)


def tell(setting: Setting, mystery: Mystery, f1: Friend, f2: Friend) -> World:
    world = World()
    park = world.add(Entity(id="park", kind="place", type="place", label=setting.place))
    path = world.add(Entity(id="path", kind="thing", type="path", label=setting.clue_place))
    spark = world.add(Entity(id="spark", kind="thing", type="magic", label="a tiny spark", magical=True))
    a = world.add(Entity(id="friend1", kind="character", type=f1.type, label=f1.label, role=f1.role, traits=["curious"], attrs={"caution": f1.caution, "magic_skill": f1.magic_skill, "tell": f1.tell}))
    b = world.add(Entity(id="friend2", kind="character", type=f2.type, label=f2.label, role=f2.role, traits=["careful"], attrs={"caution": f2.caution, "magic_skill": f2.magic_skill, "tell": f2.tell}))
    culprit = world.add(Entity(id="culprit", kind="character", type="adult", label="the gardener", role="suspect", suspicious=True))
    box = world.add(Entity(id="box", kind="thing", type="thing", label=mystery.object_label, attrs={"place": mystery.object_place}, suspicious=True))
    world.facts.update(setting=setting, mystery=mystery, friend1=a, friend2=b, culprit=culprit, box=box, park=park, path=path, spark=spark)

    world.say(f"After the rain, {f1.label} and {f2.label} walked into {setting.place}. {setting.cover_phrase}")
    world.say(f"They were looking for a small mystery, because {mystery.object_label} had vanished from {mystery.object_place}.")
    world.say(f'"Something feels {setting.mood}," {f1.label} whispered. "{f1.caution}."')
    world.para()
    world.say(f"They followed the soft clues past the benches and the swings. Then the ground turned slippery.")
    _do_slip(world, narrate=False)
    world.say(f'{f2.label} gasped, but {f1.label} caught {f2.pronoun("object")} before a fall. "Careful," {f1.label} said, "this is where the trick starts."')
    world.say(f"That was when {f2.label} noticed a tiny spark near the path. {f2.label} knew the old magic: where little light goes, small clues appear.")
    spark.meters["glow"] += 1
    propagate(world, narrate=False)
    world.para()
    world.say(f'The spark pointed the way to the {mystery.object_label}. It was tucked exactly where {mystery.object_place} said it would be.')
    culprit.memes["nervous"] += 1
    world.say(f'At first, the gardener looked suspicious, because {mystery.trace}. But {f1.label} noticed the real trail: mud on the wheels, a bent ribbon, and one tiny shiny footprint.')
    world.say(f'That trail led to the answer. {mystery.reveal}')
    world.para()
    world.say(f"The gardener had not stolen anything after all. {mystery.object_label} had rolled away in the wind and stopped near the fountain.")
    world.say(f"{f1.label} and {f2.label} laughed, then shared the best part: a little teamwork spell that made the lost thing easy to spot, not scary at all.")
    world.say(f"They walked home together, side by side, while the park stayed slippery but safe.")
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.facts["resolved"] = True
    return world


SETTINGS = {
    "neighborhood_park": Setting(
        id="neighborhood_park",
        place="the neighborhood park",
        mood="mysterious",
        clue_place="the winding path",
        cover_phrase="The benches were wet, the swings were quiet, and the pavement shone like glass.",
        weather="after rain",
    ),
    "rose_garden_park": Setting(
        id="rose_garden_park",
        place="the neighborhood park with the rose garden",
        mood="shiny",
        clue_place="the rose path",
        cover_phrase="The flower beds smelled sweet, and every leaf held a bead of rain.",
        weather="after rain",
    ),
}

MYSTERIES = {
    "missing_ball": Mystery(
        id="missing_ball",
        culprit="the wind",
        object_moved="ball",
        object_label="the red ball",
        object_place="under the big oak tree",
        trace="the ball was not where it had been left",
        reveal="Under the oak tree, they found the red ball, and a little chalk arrow on the ground showed how it had rolled.",
    ),
    "missing_kite": Mystery(
        id="missing_kite",
        culprit="the wind",
        object_moved="kite",
        object_label="the blue kite",
        object_place="beside the fence",
        trace="the kite string had looped around a bench leg",
        reveal="By the fence, they found the blue kite tangled in a bush, smiling ribbon and all.",
    ),
    "missing_chalk": Mystery(
        id="missing_chalk",
        culprit="a squirrel",
        object_moved="chalk box",
        object_label="the chalk box",
        object_place="near the sandbox",
        trace="tiny paw prints circled the sandbox",
        reveal="Near the sandbox, they found the chalk box and a nest of scribbly clues leading right to it.",
    ),
}

FRIENDS = {
    "maya": Friend(id="maya", type="girl", label="Maya", caution="don't rush on wet paths", magic_skill="glow-hints", tell="Maya always noticed shiny clues.", role="detective"),
    "leo": Friend(id="leo", type="boy", label="Leo", caution="we should look before we leap", magic_skill="spark-reading", tell="Leo could read a spark like a map.", role="helper"),
    "nina": Friend(id="nina", type="girl", label="Nina", caution="slippery places like to surprise people", magic_skill="soft-light", tell="Nina carried a tiny magic charm on her wrist.", role="detective"),
    "sam": Friend(id="sam", type="boy", label="Sam", caution="slow steps solve fast problems", magic_skill="glow-hints", tell="Sam loved quiet clues.", role="helper"),
}

CURATED = [
    StoryParams(setting="neighborhood_park", mystery="missing_ball", friend1="maya", friend2="leo"),
    StoryParams(setting="neighborhood_park", mystery="missing_kite", friend1="nina", friend2="sam"),
    StoryParams(setting="rose_garden_park", mystery="missing_chalk", friend1="leo", friend2="maya"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slippery neighborhood park whodunit with magic and friendship.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--friend1", choices=FRIENDS)
    ap.add_argument("--friend2", choices=FRIENDS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    friend1 = args.friend1 or rng.choice(list(FRIENDS))
    friend2 = args.friend2 or rng.choice([k for k in FRIENDS if k != friend1])
    params = StoryParams(setting=setting, mystery=mystery, friend1=friend1, friend2=friend2)
    if not is_reasonable(params):
        raise StoryError("The chosen neighborhood-park mystery is not reasonable.")
    return params


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly whodunit set in {f["setting"].place} that uses the word "slippery" and includes a tiny magic clue.',
        f"Tell a friendship story where {f['friend1'].label} and {f['friend2'].label} solve a mystery in a neighborhood park after rain.",
        f"Write a cautionary mystery where a slippery path almost causes a fall, but the friends stay safe and solve the case together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    setting: Setting = f["setting"]
    mystery: Mystery = f["mystery"]
    a: Entity = f["friend1"]
    b: Entity = f["friend2"]
    return [
        QAItem(question="Where does the story happen?", answer=f"It happens in {setting.place}. The wet park paths and benches make the mystery feel real."),
        QAItem(question="What made the friends careful?", answer="The path was slippery after the rain, so one wrong step could have made someone fall. They slowed down and watched each other closely."),
        QAItem(question=f"What did {a.label} and {b.label} solve?", answer=f"They solved the case of {mystery.object_label}. At first it seemed suspicious, but the clue trail showed what really happened."),
        QAItem(question="Was the gardener the culprit?", answer="No. The gardener only looked suspicious for a moment, because the story wanted a mystery twist, but the clues pointed elsewhere."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does slippery mean?", answer="Slippery means something is hard to walk on because feet can slide. Wet pavement and shiny paths can be slippery."),
        QAItem(question="Why can rain make a park tricky?", answer="Rain can leave water on paths, benches, and playground edges. That water can make them slick and easy to slide on."),
        QAItem(question="What is a clue in a whodunit?", answer="A clue is a small piece of information that helps solve a mystery. Clues can be footprints, a trail, a sound, or something out of place."),
        QAItem(question="What does a careful friend do?", answer="A careful friend slows down, warns others, and pays attention. Carefulness helps everyone stay safe and find the answer."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
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
        if e.suspicious:
            bits.append("suspicious")
        if e.magical:
            bits.append("magical")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
slippery(park) :- park(park), wet_after_rain(park).
careful(friend1) :- friend(friend1).
careful(friend2) :- friend(friend2).
clue_found(path) :- spark(glow), slippery(park), path(path).
resolved :- clue_found(path).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("park", sid))
        lines.append(asp.fact("wet_after_rain", sid))
    for fid in FRIENDS:
        lines.append(asp.fact("friend", fid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show park/1."))
    return sorted(set(asp.atoms(model, "park")))


def asp_verify() -> int:
    rc = 0
    py = {c[0] for c in valid_combos()}
    cl = {c[0] for c in asp_valid_combos()}
    if py == cl:
        print(f"OK: ASP and Python agree on settings ({sorted(py)}).")
    else:
        rc = 1
        print("MISMATCH in ASP/Python gate.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as ex:
        rc = 1
        print(f"SMOKE TEST FAILED: {ex}")
    return rc


def generate(params: StoryParams) -> StorySample:
    if not is_reasonable(params):
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], FRIENDS[params.friend1], FRIENDS[params.friend2])
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
        print(asp_program("", "#show park/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{x[0]}" for x in asp_valid_combos()))
        return
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            p = resolve_params(args, random.Random((args.seed or 0) + i))
            sample = generate(p)
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
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
