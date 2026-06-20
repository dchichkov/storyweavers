#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/millenium_loyal_convention_rhyme_transformation_fairy_tale.py
================================================================================================

A small fairy-tale storyworld about a loyal child at a convention of rhyme
makers who must use a transformation charm to save a forgotten song before the
millenium bell. The domain is intentionally tiny and classical: characters with
meters and memes, a state-driven turn, and a bright ending image proving what
changed.

The seed words are woven into the world:
- millenium
- loyal
- convention

Features:
- Rhyme: the story includes short rhymed lines in a child-facing fairy-tale
  voice.
- Transformation: a magical change converts a plain object into the needed one.

This file is standalone and stdlib-only.
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    detail: str
    time_mark: str
    rhyme_cue: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    rhyme_line: str
    power: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Transformable:
    id: str
    label: str
    phrase: str
    transformed_label: str
    transformed_phrase: str
    needed: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_time_bell(world: World) -> list[str]:
    out = []
    bell = world.get("bell")
    if bell.meters["ready"] < THRESHOLD:
        return out
    sig = ("time_bell",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("hall").memes["wonder"] += 1
    out.append("__bell__")
    return out


def _r_transformation(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["blessed"] < THRESHOLD:
            continue
        sig = ("transform", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if e.id == "plain_cloak":
            e.label = "moon-silver cloak"
            e.attrs["glimmer"] = True
            out.append("__transform__")
    return out


RULES = [Rule("time_bell", _r_time_bell), Rule("transformation", _r_transformation)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def make_rhyme(beat: str, end1: str, end2: str) -> str:
    return f"{beat}, {end1}; {end2}."


def is_reasonable(charm: Charm, item: Transformable) -> bool:
    return charm.power >= 2 and item.needed == "song"


def do_charm(world: World, charm: Charm, item: Transformable) -> None:
    world.get("plain_cloak").meters["blessed"] += 1
    world.get("plain_cloak").meters["changed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The {charm.label} sparkled softly, and with a twirl and a word the "
        f"{item.label} turned into {item.transformed_label}."
    )


def setup(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    hero.memes["loyalty"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"In {setting.place}, at {setting.time_mark}, {hero.id} and {friend.id} "
        f"came to a fairytale convention where singers traded rhymes."
    )
    world.say(setting.detail)
    world.say(
        f'"{setting.rhyme_cue}," said {hero.id}, and the hall answered with a song.'
    )


def trouble(world: World, hero: Entity, friend: Entity, charm: Charm, item: Transformable) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"But just then the millenium bell was near, and the old song-book had lost "
        f"the page that kept the chorus bright."
    )
    world.say(
        f'{friend.id} frowned. "Without the chorus, the convention will go quiet."'
    )
    world.say(
        f'{hero.id} held the {item.label} close and said, "I am loyal, and I will not '
        f"let the song sleep away."
    )
    world.say(make_rhyme("The moon was high", "the hall grew still", "but not for long"))
    world.facts["worry"] = True


def solve(world: World, hero: Entity, friend: Entity, charm: Charm, item: Transformable) -> None:
    do_charm(world, charm, item)
    world.say(
        f"With the new {item.transformed_label}, {hero.id} read the chorus aloud, "
        f"and the hall found its tune again."
    )
    world.say(
        make_rhyme("The bell rang clear", "the singers spun", "and every voice came home")
    )
    hero.memes["joy"] += 2
    friend.memes["joy"] += 2
    world.get("hall").meters["music"] += 1
    world.get("bell").meters["ready"] = 0


def ending(world: World, hero: Entity, friend: Entity, item: Transformable) -> None:
    world.say(
        f"At last the convention glittered bright, with {hero.id} smiling beside "
        f"{friend.id} as the moon-silver page shone in the candlelight."
    )
    world.say(
        f"And so the millenium came with music, rhyme, and a loyal heart that kept "
        f"the story alive."
    )


def tell(setting: Setting, hero_name: str, friend_name: str, charm: Charm, item: Transformable) -> World:
    world = World(setting)
    hero = world.add(Entity(hero_name, kind="character", type="girl", role="hero", traits=["loyal"]))
    friend = world.add(Entity(friend_name, kind="character", type="boy", role="friend"))
    hall = world.add(Entity("hall", type="place", label="the hall"))
    bell = world.add(Entity("bell", type="object", label="the millenium bell"))
    plain = world.add(Entity("plain_cloak", type="object", label=item.label))
    bell.meters["ready"] = 1
    setup(world, hero, friend, setting)
    world.para()
    trouble(world, hero, friend, charm, item)
    world.para()
    solve(world, hero, friend, charm, item)
    world.para()
    ending(world, hero, friend, item)
    world.facts.update(
        hero=hero,
        friend=friend,
        hall=hall,
        bell=bell,
        plain=plain,
        charm=charm,
        item=item,
        setting=setting,
    )
    return world


SETTINGS = {
    "castle": Setting(
        "castle",
        "the castle hall",
        "Rows of lanterns shone on banners, and the windows sang with a winter wind.",
        "the last hour before midnight",
        "Rhyme, friends, and kindly light",
        tags={"castle", "fairy", "convention"},
    ),
    "meadow": Setting(
        "meadow",
        "the meadow pavilion",
        "The tents were stitched with gold thread, and the grass wore silver dew.",
        "the hush before the moon-bell",
        "Rhyme, friends, and kindly light",
        tags={"meadow", "fairy", "convention"},
    ),
}

CHARMES = {
    "spark": Charm(
        "spark",
        "silver rhyme charm",
        "a silver rhyme charm",
        "When words were bright and hearts were true, the charm would glow with morning dew",
        power=3,
        tags={"rhyme", "magic"},
    ),
    "thread": Charm(
        "thread",
        "luminous thread charm",
        "a luminous thread charm",
        "Tie the line and sing it right, and thread shall shine like woven light",
        power=2,
        tags={"rhyme", "magic"},
    ),
}

ITEMS = {
    "cloak": Transformable(
        "cloak",
        "plain cloak",
        "a plain cloak",
        "moon-silver cloak",
        "a moon-silver cloak",
        needed="song",
        tags={"transformation", "cloak"},
    ),
    "page": Transformable(
        "page",
        "blank page",
        "a blank page",
        "golden page",
        "a golden page",
        needed="song",
        tags={"transformation", "page"},
    ),
}

HEROES = ["Elara", "Nia", "Mira", "Lina", "Tessa", "Ada"]
FRIENDS = ["Robin", "Finn", "Oren", "Bram", "Pip", "Jules"]
TRAITS = ["loyal", "gentle", "brave", "kind"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CHARMES:
            for i in ITEMS:
                if is_reasonable(CHARMES[c], ITEMS[i]):
                    combos.append((s, c, i))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    charm: str
    item: str
    hero: str
    friend: str
    trait: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world with rhyme and transformation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--charm", choices=CHARMES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
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
    if args.charm and args.item and not is_reasonable(CHARMES[args.charm], ITEMS[args.item]):
        raise StoryError("That charm cannot reasonably transform that item in this tiny storyworld.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.charm is None or c[1] == args.charm)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, charm, item = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HEROES)
    friend = args.friend or rng.choice([x for x in FRIENDS if x != hero])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, charm, item, hero, friend, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy tale for a young child that includes the words "millenium", '
        f'"loyal", and "convention" and uses a soft rhyme.',
        f"Tell a small magical story where {f['hero'].id} stays loyal at a convention "
        f"and uses a transformation charm to save a song before the millenium bell.",
        f"Write a child-friendly fairy tale about rhyme and transformation with a "
        f"happy ending in which a plain thing becomes something magical.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    setting = f["setting"]
    item = f["item"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id}, who stayed loyal to {friend.id} at a fairytale convention. "
         f"{hero.id} used a little magic to help the song survive the millenium bell."),
        ("What problem needed solving?",
         f"The old song-book had lost the chorus page, so the convention could have gone quiet. "
         f"{hero.id} needed a transformation charm to make a new page shine."),
        ("How was the problem solved?",
         f"{hero.id} used the {f['charm'].label} to transform the {item.label} into a moon-silver help. "
         f"That gave the singers the missing chorus again."),
        ("How did the story end?",
         f"It ended with music, rhyme, and a bright hall at {setting.place}. "
         f"The loyal heart in the story helped everyone welcome the millenium together."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["setting"].tags) | set(f["charm"].tags) | set(f["item"].tags)
    out = []
    kb = {
        "rhyme": [("What is a rhyme?",
                   "A rhyme is when words end with the same or a similar sound. It makes a song or story sound musical.")],
        "magic": [("What does a magic charm do in stories?",
                  "A magic charm can change something, help with a problem, or reveal a hidden wonder in a fairy tale.")],
        "transformation": [("What is a transformation?",
                             "A transformation is a change from one thing into another thing.")],
        "fairy": [("What is a fairy tale?",
                   "A fairy tale is a magical story with a wonder-filled place, a problem, and a happy ending.")],
        "convention": [("What is a convention?",
                       "A convention is a gathering where many people come together because they share the same interest.")],
    }
    order = ["fairy", "convention", "rhyme", "magic", "transformation"]
    for tag in order:
        if tag in tags and tag in kb:
            out.extend(kb[tag])
    return out


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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("castle", "spark", "cloak", "Elara", "Robin", "loyal"),
    StoryParams("meadow", "thread", "page", "Mira", "Finn", "kind"),
]


def explain_rejection() -> str:
    return "This tiny fairy-tale world only allows a charm that can transform the chosen item."


ASP_RULES = r"""
valid(S,C,I) :- setting(S), charm(C), item(I), reasonable(C,I).
reasonable(C,I) :- charm(C), item(I), charm_power(C,P), P >= 2, needed(I,"song").
outcome(ok) :- valid(_,_,_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c, v in CHARMES.items():
        lines.append(asp.fact("charm", c))
        lines.append(asp.fact("charm_power", c, v.power))
    for i, v in ITEMS.items():
        lines.append(asp.fact("item", i))
        lines.append(asp.fact("needed", i, v.needed))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in gate.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, charm=None, item=None, hero=None, friend=None, trait=None), random.Random(0)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], params.hero, params.friend, CHARMES[params.charm], ITEMS[params.item])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos:")
        for s, c, i in asp_valid_combos():
            print(f"  {s:8} {c:8} {i}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} at the {p.setting} ({p.charm}, {p.item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
