#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/blanket_tights_mistaken_twist_tall_tale.py
==========================================================================

A small standalone storyworld in a tall-tale style: a rider with a magical
blanket, a pair of tights, and a mistaken identity twist. The world is built
around one little premise: a kid and a grown-up keep a traveling blanket cart
moving through a windy valley, mistake a harmless thing for a stranger, and then
discover the twist that turns worry into a laugh.

Contract notes:
- stdlib-only storyworld script
- imports storyworlds/results.py eagerly for QAItem, StoryError, StorySample
- imports storyworlds/asp.py lazily in ASP helpers only
- defines StoryParams, registries, build_parser, resolve_params, generate, emit,
  and main
- supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    sky: str
    sound: str
    horizon: str
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
class Item:
    id: str
    label: str
    phrase: str
    type: str
    tags: set[str] = field(default_factory=set)
    plural: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    clue: str
    ending: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone
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
    hero: str
    hero_type: str
    companion: str
    companion_type: str
    blanket: str
    tights: str
    mistaken: str
    twist: str
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


SETTINGS = {
    "prairie": Setting(
        id="prairie",
        place="the wide prairie road",
        sky="the sky was big as a blue bowl",
        sound="the wind went whistle-whoo through the grass",
        horizon="the horizon rolled like a sleepy sea",
        tags={"prairie", "wind"},
    ),
    "harbor": Setting(
        id="harbor",
        place="the harbor hill",
        sky="the clouds sailed low like wooly ships",
        sound="the gulls cried and the ropes sang on the docks",
        horizon="the harbor blinked with tinny lanterns",
        tags={"harbor", "wind"},
    ),
    "canyon": Setting(
        id="canyon",
        place="the red canyon path",
        sky="the sky stretched long and gold above the cliffs",
        sound="the wind bounced from rock to rock like a fiddle tune",
        horizon="the far rim curled like a giant smile",
        tags={"canyon", "wind"},
    ),
}

BLANKETS = {
    "wagon_blanket": Item("wagon_blanket", "blanket", "a patched wool blanket", "blanket", tags={"blanket"}),
    "star_blanket": Item("star_blanket", "blanket", "a starry blanket", "blanket", tags={"blanket"}),
    "blue_blanket": Item("blue_blanket", "blanket", "a blue blanket with brass buttons", "blanket", tags={"blanket"}),
}

TIGHTS = {
    "striped_tights": Item("striped_tights", "tights", "striped tights", "tights", tags={"tights"}),
    "silver_tights": Item("silver_tights", "tights", "silver tights", "tights", tags={"tights"}),
    "green_tights": Item("green_tights", "tights", "green tights", "tights", tags={"tights"}),
}

MISTAKENS = {
    "mistaken_mail": Item("mistaken_mail", "mistaken", "a mistaken bundle of mail", "mistaken", tags={"mistaken"}),
    "mistaken_shadow": Item("mistaken_shadow", "mistaken", "a mistaken shadow-puppet", "mistaken", tags={"mistaken"}),
    "mistaken_wind": Item("mistaken_wind", "mistaken", "a mistaken whirl of wind", "mistaken", tags={"mistaken"}),
}

TWISTS = {
    "twist_mule": Twist(
        id="twist_mule",
        reveal="the 'mysterious stranger' was only a mule wearing the blanket as a saddle-wrap",
        clue="the hoofbeats had been clopping in time with the cart all along",
        ending="the mule bowed, the blanket stayed, and everybody laughed until the stars shook",
        tags={"twist", "mule"},
    ),
    "twist_grandmother": Twist(
        id="twist_grandmother",
        reveal="the mistaken shape was really Grandmother coming up the hill in her tall riding cloak",
        clue="the little lantern swing had looked like a floating eye in the dark",
        ending="Grandmother laughed, shook out the blanket, and called it the best surprise of the year",
        tags={"twist", "grandmother"},
    ),
    "twist_wagon": Twist(
        id="twist_wagon",
        reveal="the 'lost stranger' was only their own wagon rolling back with the wind",
        clue="the old wheel kept creaking in the same lopsided tune",
        ending="the wagon came home, the blanket fluttered like a flag, and the whole road grinned",
        tags={"twist", "wagon"},
    ),
}

GIRL_NAMES = ["Mabel", "Lily", "Nora", "Hazel", "Elsie", "June"]
BOY_NAMES = ["Ezra", "Ollie", "Cal", "Wes", "Bram", "Toby"]
TRAITS = ["brave", "breezy", "bright-eyed", "lively", "curious"]


def hazard_reason(setting: Setting, mistaken: Item) -> bool:
    return setting.id in {"prairie", "harbor", "canyon"} and "mistaken" in mistaken.tags


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for bid in BLANKETS:
            for tid in TIGHTS:
                for mid in MISTAKENS:
                    if hazard_reason(SETTINGS[sid], MISTAKENS[mid]):
                        combos.append((sid, bid, tid, mid))
    return combos


def reason_for_rejection(setting: Setting, mistaken: Item) -> str:
    return (
        f"(No story: this tall tale needs a real mistaken sighting in the windy setting, "
        f"but {mistaken.phrase} will not create that kind of twist here.)"
    )


def choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about a blanket, tights, and a mistaken twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--blanket", choices=BLANKETS)
    ap.add_argument("--tights", choices=TIGHTS)
    ap.add_argument("--mistaken", choices=MISTAKENS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--companion")
    ap.add_argument("--companion-type", choices=["girl", "boy"])
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
    if args.setting and args.mistaken:
        if not hazard_reason(SETTINGS[args.setting], MISTAKENS[args.mistaken]):
            raise StoryError(reason_for_rejection(SETTINGS[args.setting], MISTAKENS[args.mistaken]))
    combos = [c for c in valid_combos()
              if args.setting in (None, c[0])
              and args.blanket in (None, c[1])
              and args.tights in (None, c[2])
              and args.mistaken in (None, c[3])]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, blanket, tights, mistaken = rng.choice(sorted(combos))
    twist = args.twist or rng.choice(sorted(TWISTS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    companion_type = args.companion_type or ("boy" if hero_type == "girl" else "girl")
    hero = args.hero or choose_name(rng, hero_type)
    companion = args.companion or choose_name(rng, companion_type)
    if hero == companion:
        companion = choose_name(rng, companion_type)
    return StoryParams(
        setting=setting,
        hero=hero,
        hero_type=hero_type,
        companion=companion,
        companion_type=companion_type,
        blanket=blanket,
        tights=tights,
        mistaken=mistaken,
        twist=twist,
    )


def _story_opening(world: World, hero: Entity, companion: Entity, blanket: Item, tights: Item) -> None:
    s = world.setting
    hero.memes["wonder"] += 1
    companion.memes["wonder"] += 1
    world.say(
        f"On a day when {s.sky} and {s.sound}, {hero.id} and {companion.id} set out along {s.place}."
    )
    world.say(
        f"{hero.id} wore {tights.phrase}, and {companion.id} carried {blanket.phrase} rolled up like a sleeping moon."
    )


def _build_tall_tale(world: World, hero: Entity, companion: Entity, mistaken: Item) -> None:
    world.para()
    hero.memes["pride"] += 1
    companion.memes["pride"] += 1
    world.say(
        f"They were so tall in their own minds that each step felt like a drumbeat for the whole valley."
    )
    world.say(
        f"Then {mistaken.phrase} bobbed at the bend in the road, and {hero.id} pointed straight at it."
    )


def _mistake(world: World, hero: Entity, companion: Entity, mistaken: Item) -> None:
    hero.memes["fear"] += 1
    companion.memes["alert"] += 1
    world.say(
        f'"Look!" said {hero.id}. "It is a stranger, and I am mistaken if it is not trouble!"'
    )
    world.say(
        f"{companion.id} squinted hard and called it a {mistaken.label_word if hasattr(mistaken, 'label_word') else mistaken.label}."
    )


def _twist(world: World, twist: Twist, mistaken: Item, blanket: Item) -> None:
    world.para()
    world.say(f"But the wind kept on, and then came the twist: {twist.reveal}.")
    world.say(
        f"That was the clue's true meaning: {twist.clue}, and the blanket was never lost at all."
    )
    world.say(
        f"{twist.ending}. The blanket flapped high as a banner, and the mistaken thing turned out to be harmless."
    )
    world.facts["twist_reveal"] = twist.reveal
    world.facts["twist_clue"] = twist.clue
    world.facts["mistaken"] = mistaken
    world.facts["blanket"] = blanket


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, role="hero"))
    companion = world.add(Entity(id=params.companion, kind="character", type=params.companion_type, role="companion"))
    blanket = world.add(Entity(id="blanket", type="blanket", label=BLANKETS[params.blanket].label_word, attrs={"phrase": BLANKETS[params.blanket].phrase}))
    tights = world.add(Entity(id="tights", type="tights", label=TIGHTS[params.tights].label_word))
    mistaken = world.add(Entity(id="mistaken", type="mistaken", label=MISTAKENS[params.mistaken].label_word, tags={"mistaken"}))
    twist = TWISTS[params.twist]

    _story_opening(world, hero, companion, BLANKETS[params.blanket], TIGHTS[params.tights])
    _build_tall_tale(world, hero, companion, MISTAKENS[params.mistaken])
    _mistake(world, hero, companion, MISTAKENS[params.mistaken])
    _twist(world, twist, MISTAKENS[params.mistaken], BLANKETS[params.blanket])

    world.facts.update(
        hero=hero,
        companion=companion,
        blanket=blanket,
        tights=tights,
        mistaken=mistaken,
        twist=twist,
        setting=world.setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall tale for a child that includes the words "{f["blanket"].type}", "{f["tights"].type}", and "{f["mistaken"].type}".',
        f"Tell a windy adventure where {f['hero'].id} and {f['companion'].id} travel with a blanket and tights, then realize they were mistaken about what they saw.",
        f'Write a story with a twist ending in the style of a tall tale, using the word "{f["mistaken"].type}" and a harmless reveal.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    companion: Entity = f["companion"]
    twist: Twist = f["twist"]
    blanket: Entity = f["blanket"]
    mistaken: Entity = f["mistaken"]
    return [
        QAItem(
            question="Who are the story's main characters?",
            answer=f"The story follows {hero.id} and {companion.id}. They travel together through the windy place and carry the blanket while the twist unfolds.",
        ),
        QAItem(
            question="What did the mistaken thing cause the characters to think?",
            answer=f"It made {hero.id} think they had found trouble. The shape looked strange in the wind, so both children started out uneasy before the truth came clear.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that {twist.reveal}. The scary-looking shape was harmless, so the worry turned into a laugh.",
        ),
        QAItem(
            question="How did the blanket matter in the ending?",
            answer=f"The blanket stayed part of the journey and was never truly lost. It ended up fluttering proudly in the scene, which proved the mistake had been harmless.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is a blanket for?",
            answer="A blanket is something you can use to keep warm or to cover things. It can also be carried on a trip to make a bed or bundle feel safe.",
        ),
        QAItem(
            question="What are tights?",
            answer="Tights are close-fitting clothes for the legs. People wear them under dresses, costumes, or other outfits to keep their legs covered.",
        ),
        QAItem(
            question="What does mistaken mean?",
            answer="Mistaken means wrong about what you thought you saw or understood. If you are mistaken, the truth is different from your first guess.",
        ),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== (2) Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.extend(["", "== (3) World knowledge questions =="])
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="prairie", hero="Mabel", hero_type="girl", companion="Wes", companion_type="boy", blanket="wagon_blanket", tights="striped_tights", mistaken="mistaken_mail", twist="twist_mule"),
    StoryParams(setting="harbor", hero="Ezra", hero_type="boy", companion="Lily", companion_type="girl", blanket="star_blanket", tights="silver_tights", mistaken="mistaken_shadow", twist="twist_grandmother"),
    StoryParams(setting="canyon", hero="Hazel", hero_type="girl", companion="Toby", companion_type="boy", blanket="blue_blanket", tights="green_tights", mistaken="mistaken_wind", twist="twist_wagon"),
]


ASP_RULES = r"""
valid(S,B,T,M) :- setting(S), blanket(B), tights(T), mistaken(M), windy(S), twisty(M).
windy(prairie). windy(harbor). windy(canyon).
twisty(mistaken_mail). twisty(mistaken_shadow). twisty(mistaken_wind).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for b in BLANKETS:
        lines.append(asp.fact("blanket", b))
    for t in TIGHTS:
        lines.append(asp.fact("tights", t))
    for m in MISTAKENS:
        lines.append(asp.fact("mistaken", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combo sets differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        _ = sample.prompts
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def explain_rejection(setting: str, mistaken: str) -> str:
    return reason_for_rejection(SETTINGS[setting], MISTAKENS[mistaken])


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.blanket not in BLANKETS or params.tights not in TIGHTS or params.mistaken not in MISTAKENS or params.twist not in TWISTS:
        raise StoryError("(Invalid parameters for this storyworld.)")
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


def resolve_from_combo(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if args.setting in (None, c[0])
              and args.blanket in (None, c[1])
              and args.tights in (None, c[2])
              and args.mistaken in (None, c[3])]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, blanket, tights, mistaken = rng.choice(sorted(combos))
    twist = args.twist or rng.choice(sorted(TWISTS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    companion_type = args.companion_type or ("boy" if hero_type == "girl" else "girl")
    hero = args.hero or choose_name(rng, hero_type)
    companion = args.companion or choose_name(rng, companion_type)
    if hero == companion:
        companion = choose_name(rng, companion_type)
    return StoryParams(
        setting=setting,
        hero=hero,
        hero_type=hero_type,
        companion=companion,
        companion_type=companion_type,
        blanket=blanket,
        tights=tights,
        mistaken=mistaken,
        twist=twist,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_from_combo(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
