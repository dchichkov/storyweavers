#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/deal_bad_ending_whodunit.py
============================================================

A standalone story world for a tiny whodunit about a promised deal, a missing
object, clues in a small room, and a bad ending where the wrong choice leaves
the mystery unresolved.

This world keeps the mystery narrow and child-facing:
- someone makes or breaks a deal,
- one small object goes missing,
- clues point to a likely suspect,
- the search turns into a whodunit-style reveal,
- the ending is bad: the lost thing is not recovered, and the deal leaves the
  characters worse off.

It follows the Storyweavers storyworld contract:
- stdlib only,
- eager import of storyworlds/results.py for QAItem, StoryError, StorySample,
- lazy import of storyworlds/asp.py inside ASP helpers,
- build_parser / resolve_params / generate / emit / main,
- --verify, --asp, --show-asp, --qa, --json, --trace, --all, -n, --seed.

The story is built from world state, not by swapping nouns in a frozen paragraph.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: {"tension": 0.0, "lost": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"worry": 0.0, "suspicion": 0.0, "relief": 0.0})
    attrs: dict[str, str] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    weather: str
    room: str
    clue_spots: list[str]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Deal:
    id: str
    promise: str
    price: str
    deadline: str
    broken_by: str
    bad_choice: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class MissingThing:
    id: str
    label: str
    phrase: str
    place_hint: str
    value: str
    fragile: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Suspect:
    id: str
    label: str
    clue: str
    alibi: str
    motive: str
    suspicious: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "school": Setting("school", "the school hallway", "rainy", "the coat room", ["desk", "hooks", "shoe rack"]),
    "library": Setting("library", "the library corner", "windy", "the reading nook", ["table", "shelf", "window ledge"]),
    "kitchen": Setting("kitchen", "the kitchen", "gray", "the back counter", ["counter", "sink", "stool"]),
}

DEALS = {
    "recess": Deal("recess", "a deal to share the big red ball at recess", "one turn each", "before the bell", "someone grabbed the ball early", "snatched the ball and ran"),
    "cookies": Deal("cookies", "a deal to save one cookie for later", "two cookies now, one cookie later", "after lunch", "someone ate the last cookie early", "ate the last cookie before the deal was done"),
    "book": Deal("book", "a deal to return the shiny library book on time", "keep it safe all afternoon", "before closing time", "someone hid the book under a jacket", "hid the book and forgot where it went"),
}

MISSING = {
    "ball": MissingThing("ball", "red ball", "the big red ball", "under the table", "play"),
    "cookie": MissingThing("cookie", "cookie", "the last cookie", "behind the jar", "treat"),
    "book": MissingThing("book", "library book", "the shiny library book", "under a jacket", "story time"),
}

SUSPECTS = {
    "cat": Suspect("cat", "the cat", "crumbs on the paws", "it was napping by the chair", "wanted the crumbs", True),
    "teacher": Suspect("teacher", "the teacher", "a key on a string", "was helping near the desk", "wanted to keep things tidy", False),
    "brother": Suspect("brother", "the older brother", "paint on the sleeve", "was in art class", "wanted to borrow it", False),
}

CHILD_NAMES = ["Mia", "Noah", "Lily", "Ben", "Ava", "Theo", "Zoe", "Max"]
PARENT_NAMES = ["Mom", "Dad"]
TRAITS = ["careful", "curious", "quiet", "thoughtful", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for did, deal in DEALS.items():
            for mid, missing in MISSING.items():
                if deal.id == "book" and missing.id == "book":
                    combos.append((sid, did, mid))
                elif deal.id == "cookies" and missing.id == "cookie":
                    combos.append((sid, did, mid))
                elif deal.id == "recess" and missing.id == "ball":
                    combos.append((sid, did, mid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    deal: str
    missing: str
    suspect: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def _risk(deal: Deal, missing: MissingThing) -> bool:
    return deal.id == missing.id


def _predict(world: World, deal: Deal, missing: MissingThing) -> dict:
    sim = world.copy()
    sim.get("missing").meters["lost"] += 1
    sim.get("hero").memes["suspicion"] += 1
    return {"resolved": False, "lost": sim.get("missing").meters["lost"] >= THRESHOLD}


def setup(world: World, hero: Entity, helper: Entity, parent: Entity, deal: Deal, missing: MissingThing) -> None:
    world.say(
        f"On a gray afternoon, {hero.id} and {helper.id} found a small mystery in {world.setting.place}. "
        f"They had made {deal.promise}, but somebody had broken {deal.bad_choice}, and now {missing.phrase} was gone."
    )
    world.say(
        f'"{deal.broken_by}," {hero.id} whispered. '
        f'"If we solve this, we can keep our {deal.price}."'
    )


def suspect_clue(world: World, suspect: Suspect) -> None:
    world.say(
        f"They looked for clues near {world.setting.room}. A scrap of {suspect.clue} was there, and that made {suspect.label} seem suspicious."
    )


def warning(world: World, helper: Entity, hero: Entity, deal: Deal, missing: MissingThing) -> None:
    helper.memes["worry"] += 1
    hero.memes["suspicion"] += 1
    world.say(
        f'{helper.id} tapped the table and said, "{hero.id}, this is a deal story, but the clue is not the whole truth. '
        f'If we rush, we may blame the wrong one."'
    )


def accuse_wrongly(world: World, hero: Entity, suspect: Suspect, missing: MissingThing) -> None:
    hero.memes["suspicion"] += 1
    world.say(
        f'{hero.id} pointed at {suspect.label}. "{suspect.label} did it!" {hero.id} cried. '
        f'But the clue only looked good for a moment.'
    )


def reveal(world: World, suspect: Suspect, missing: MissingThing, deal: Deal) -> None:
    world.say(
        f"At last, they found {missing.phrase} where it had been tucked away. "
        f"But it was too late for the deal: the bell, the timer, or the last crumb had already ruined it."
    )


def bad_ending(world: World, hero: Entity, helper: Entity, parent: Entity, deal: Deal, missing: MissingThing) -> None:
    hero.memes["worry"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came over, saw the mess, and shook {parent.pronoun('possessive')} head. "
        f'"The deal is over," {parent.pronoun()} said softly.'
    )
    world.say(
        f"{missing.phrase} was found, but it was bent, sticky, or late, so nobody got the happy prize they wanted. "
        f"{hero.id} and {helper.id} stared at the dark corner and learned that a broken promise can spoil the whole day."
    )


def tell(setting: Setting, deal: Deal, missing: MissingThing, suspect: Suspect,
         hero_name: str = "Mia", hero_gender: str = "girl",
         helper_name: str = "Noah", helper_gender: str = "boy",
         parent: str = "Mom", trait: str = "careful") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", traits=[trait]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper", traits=["quiet"]))
    adult = world.add(Entity(id=parent, kind="character", type="mother" if parent == "Mom" else "father", role="adult"))
    world.add(Entity(id="missing", type=missing.id, label=missing.label, attrs={"place_hint": missing.place_hint}))
    world.add(Entity(id="suspect", type="thing", label=suspect.label, attrs={"clue": suspect.clue, "alibi": suspect.alibi}))

    setup(world, hero, helper, adult, deal, missing)
    world.para()
    suspect_clue(world, suspect)
    warning(world, helper, hero, deal, missing)
    accuse_wrongly(world, hero, suspect, missing)
    world.para()
    reveal(world, suspect, missing, deal)
    bad_ending(world, hero, helper, adult, deal, missing)

    world.facts.update(
        hero=hero, helper=helper, adult=adult, deal=deal, missing=missing, suspect=suspect,
        resolved=False, bad_ending=True
    )
    return world


KNOWLEDGE = {
    "deal": [("What is a deal?",
              "A deal is a promise between people about what each person will do. When someone breaks a deal, the promise is not kept.")],
    "clue": [("What is a clue?",
              "A clue is a small piece of information that helps solve a mystery. Good detectives look at clues carefully before they guess.")],
    "suspicious": [("What does suspicious mean?",
                    "Suspicious means something looks strange or does not fit yet. It is not the same as proof.")],
    "promise": [("Why should people keep promises?",
                 "Promises matter because other people trust them. If a promise is broken, someone may be disappointed or hurt.")],
    "lost": [("What does it mean when something is lost?",
               "Something is lost when you cannot find it where you left it. Sometimes a careful search can find it again.")],
    "mystery": [("What is a mystery?",
                  "A mystery is something that is not explained yet. You solve it by looking for clues and asking good questions.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit story for a 3-to-5-year-old that includes the word "deal" and ends badly.',
        f'Tell a mystery story where {f["hero"].id} tries to solve a deal that went wrong, but the ending is sad and the promise is not fixed.',
        f'Write a child-friendly whodunit about a broken deal, a missing thing, clues, and the wrong person nearly getting blamed.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, adult = f["hero"], f["helper"], f["adult"]
    deal, missing, suspect = f["deal"], f["missing"], f["suspect"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id} and {helper.id}, who tried to solve a small mystery after a deal went wrong."
        ),
        QAItem(
            question="What went wrong in the story?",
            answer=f"The deal was broken, and {missing.phrase} went missing. That is why the children started looking for clues."
        ),
        QAItem(
            question="Why did the children think {0} was suspicious?".format(suspect.label),
            answer=f"They saw a clue near {world.setting.room}, so {suspect.label} looked suspicious at first. But a clue is not proof, and they should have been careful before guessing."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended badly. {missing.phrase} was found too late, and the deal was already ruined, so nobody got the happy ending they hoped for."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"deal", "clue", "suspicious", "promise", "lost", "mystery"}
    out: list[QAItem] = []
    for tag, items in KNOWLEDGE.items():
        if tag in tags:
            for q, a in items:
                out.append(QAItem(q, a))
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("school", "recess", "ball", "Mia", "girl", "Noah", "boy", "Mom", "careful"),
    StoryParams("library", "book", "book", "Lily", "girl", "Ben", "boy", "Dad", "curious"),
    StoryParams("kitchen", "cookies", "cookie", "Ava", "girl", "Theo", "boy", "Mom", "thoughtful"),
]


def explain_rejection(setting: Setting, deal: Deal, missing: MissingThing) -> str:
    if not _risk(deal, missing):
        return "(No story: this deal and missing thing do not fit the mystery well enough.)"
    return "(No story: the requested combination is not a reasonable whodunit for this world.)"


def valid_story(deal_id: str, missing_id: str) -> bool:
    return _risk(DEALS[deal_id], MISSING[missing_id])


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for did in DEALS:
        lines.append(asp.fact("deal", did))
    for mid in MISSING:
        lines.append(asp.fact("missing", mid))
    for sid, did, mid in valid_combos():
        lines.append(asp.fact("valid", sid, did, mid))
    lines.append(asp.fact("threshold", int(THRESHOLD)))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S, D, M) :- valid(S, D, M).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in ASP:", sorted(cl - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, deal=None, missing=None, suspect=None, seed=None), random.Random(1)))
        print("OK: generate() smoke test produced a story.")
        _ = sample.story
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit story world with a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--deal", choices=DEALS)
    ap.add_argument("--missing", choices=MISSING)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["Mom", "Dad"])
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
    if args.deal and args.missing and not valid_story(args.deal, args.missing):
        raise StoryError(explain_rejection(SETTINGS[args.setting] if args.setting else SETTINGS["school"],
                                           DEALS[args.deal], MISSING[args.missing]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.deal is None or c[1] == args.deal)
              and (args.missing is None or c[2] == args.missing)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, deal, missing = rng.choice(sorted(combos))
    suspect = args.suspect or rng.choice(list(SUSPECTS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice([n for n in CHILD_NAMES if n != hero])
    parent = args.parent or rng.choice(PARENT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, deal, missing, suspect, hero, hero_gender, helper, helper_gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        DEALS[params.deal],
        MISSING[params.missing],
        SUSPECTS[params.suspect],
        params.hero,
        params.hero_gender,
        params.helper,
        params.helper_gender,
        params.parent,
        params.trait,
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
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.deal} / {p.missing} / {p.suspect}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
