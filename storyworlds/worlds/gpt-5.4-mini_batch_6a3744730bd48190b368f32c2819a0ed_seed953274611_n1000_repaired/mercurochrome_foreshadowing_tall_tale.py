#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/mercurochrome_foreshadowing_tall_tale.py
========================================================================

A standalone storyworld for a tall-tale style safety story centered on a small
child, a skinned knee, a bottle of mercurochrome, and a bit of foreshadowing.

Premise
-------
A boastful child rushes into play, gets a scrape, and a wise grown-up uses the
red medicine carefully while a few early signs hint that the day will turn out
better than the child expects.

The world is kept small on purpose:
- one child
- one grown-up
- one injury
- one old-fashioned medicine
- one safe ending image

The narrative instrument is foreshadowing: a little omen or repeated detail is
seeded early, then pays off at the end. The style is a tall tale: concrete,
slightly larger-than-life, but still child-facing and grounded in state changes.
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    cue: str
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
class Injury:
    id: str
    label: str
    kind: str
    severity: int
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
class Medicine:
    id: str
    label: str
    bottle_name: str
    color: str
    effect: str
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
class Foreshadow:
    id: str
    sign: str
    payoff: str
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
class StoryParams:
    setting: str = "county_fair"
    child_name: str = "Ned"
    child_gender: str = "boy"
    adult_name: str = "Aunt June"
    adult_gender: str = "woman"
    injury: str = "knee_scrape"
    medicine: str = "mercurochrome"
    foreshadow: str = "red_bandana"
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "county_fair": Setting(
        id="county_fair",
        place="the county fair",
        detail="The tents leaned like sleepy giants, and the ferris wheel blinked one eye at a time.",
        cue="A ribbon-red bandana kept fluttering from the prize stand, like it knew something before anyone else did.",
        tags={"fair", "foreshadow"},
    ),
    "riverbank": Setting(
        id="riverbank",
        place="the riverbank",
        detail="The river rolled along with a voice like a kettle singing at low heat.",
        cue="A line of red reeds bent in the wind, pointing toward the picnic blanket as if they were warning bells.",
        tags={"river", "foreshadow"},
    ),
    "barn_auction": Setting(
        id="barn_auction",
        place="the old barn auction",
        detail="The barn boards creaked so loudly they sounded like they were telling jokes to the moon.",
        cue="A red lantern on a nail kept swaying even though the air was still, and that was a clue in plain sight.",
        tags={"barn", "foreshadow"},
    ),
}

INJURIES = {
    "knee_scrape": Injury(
        id="knee_scrape",
        label="scraped knee",
        kind="scrape",
        severity=1,
        tags={"scrape", "skin"},
    ),
    "elbow_bump": Injury(
        id="elbow_bump",
        label="bumped elbow",
        kind="bruise",
        severity=1,
        tags={"bruise", "skin"},
    ),
}

MEDICINES = {
    "mercurochrome": Medicine(
        id="mercurochrome",
        label="mercurochrome",
        bottle_name="the tiny red bottle of mercurochrome",
        color="red",
        effect="stung for just a blink and then left a bright red star on the scrape",
        tags={"medicine", "red"},
    ),
}

FORESHADOWS = {
    "red_bandana": Foreshadow(
        id="red_bandana",
        sign="a red bandana",
        payoff="that same red color marked the scrape after it was cleaned",
        tags={"red", "foreshadow"},
    ),
    "red_lantern": Foreshadow(
        id="red_lantern",
        sign="a red lantern",
        payoff="the lantern's red glow matched the medicine bottle later",
        tags={"red", "foreshadow"},
    ),
    "red_reeds": Foreshadow(
        id="red_reeds",
        sign="red reeds in the wind",
        payoff="their red color echoed the medicine on the child's knee",
        tags={"red", "foreshadow"},
    ),
}

FALLBACK_NAMES = ["Ned", "Mabel", "Ruby", "Otis", "Belle", "Ira", "June", "Milo"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for injury in INJURIES:
            for medicine in MEDICINES:
                for foreshadow in FORESHADOWS:
                    combos.append((setting, injury, medicine, foreshadow))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale foreshadowing storyworld with mercurochrome.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--injury", choices=INJURIES)
    ap.add_argument("--medicine", choices=MEDICINES)
    ap.add_argument("--foreshadow", choices=FORESHADOWS)
    ap.add_argument("--child-name")
    ap.add_argument("--adult-name")
    ap.add_argument("--child-gender", choices=["boy", "girl"])
    ap.add_argument("--adult-gender", choices=["man", "woman"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.injury is None or c[1] == args.injury)
              and (args.medicine is None or c[2] == args.medicine)
              and (args.foreshadow is None or c[3] == args.foreshadow)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, injury, medicine, foreshadow = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["boy", "girl"])
    adult_gender = args.adult_gender or rng.choice(["man", "woman"])
    child_name = args.child_name or rng.choice(FALLBACK_NAMES)
    adult_name = args.adult_name or ("Aunt June" if adult_gender == "woman" else "Uncle Ben")
    return StoryParams(
        setting=setting,
        child_name=child_name,
        child_gender=child_gender,
        adult_name=adult_name,
        adult_gender=adult_gender,
        injury=injury,
        medicine=medicine,
        foreshadow=foreshadow,
    )


def _actor(r: World, params: StoryParams) -> tuple[Entity, Entity, Entity, Entity]:
    child = r.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    adult = r.add(Entity(id=params.adult_name, kind="character", type=params.adult_gender, role="adult"))
    setting = r.add(Entity(id=params.setting, kind="thing", type="place", label=SETTINGS[params.setting].place))
    injury = r.add(Entity(id=params.injury, kind="thing", type="injury", label=INJURIES[params.injury].label))
    medicine = r.add(Entity(id=params.medicine, kind="thing", type="medicine", label=MEDICINES[params.medicine].label))
    foreshadow = r.add(Entity(id=params.foreshadow, kind="thing", type="sign", label=FORESHADOWS[params.foreshadow].sign))
    r.facts["setting"] = SETTINGS[params.setting]
    r.facts["injury"] = INJURIES[params.injury]
    r.facts["medicine"] = MEDICINES[params.medicine]
    r.facts["foreshadow"] = FORESHADOWS[params.foreshadow]
    r.facts["child"] = child
    r.facts["adult"] = adult
    r.facts["scene"] = setting
    return child, adult, injury, medicine


def _stitch(world: World) -> None:
    child = world.facts["child"]
    injury = world.facts["injury"]
    if world.facts.get("tended"):
        child.memes["relief"] += 1
        injury.tags.add("healed")


def tell(params: StoryParams) -> World:
    world = World()
    child, adult, injury, medicine = _actor(world, params)
    setting = SETTINGS[params.setting]
    foreshadow = FORESHADOWS[params.foreshadow]

    child.memes["pride"] += 1
    world.say(
        f"At {setting.place}, {child.id} went trotting along like a colt with a thunder drum in {child.pronoun('possessive')} chest."
    )
    world.say(
        f"{setting.detail} {setting.cue}"
    )
    world.say(
        f"{child.id} laughed and said {child.pronoun('subject').capitalize()} could outrun a prairie wind, but the ground had other ideas."
    )
    world.para()
    child.meters["reckless"] += 1
    child.meters["hurt"] += float(INJURIES[params.injury].severity)
    world.say(
        f"Down {child.id} went, and {child.pronoun('possessive')} {injury.label} came up smarting like it had been kissed by a nettle."
    )
    world.say(
        f"{adult.id} came over with the tiny red bottle of mercurochrome, and the bottle looked about as small as a matchbox beside a house cat."
    )
    world.say(
        f'"Hold still," {adult.id} said, "and watch the red."'
    )
    world.para()
    child.memes["fear"] += 1
    child.memes["trust"] += 1
    world.say(
        f"The mercurochrome stung for a blink, then turned the scrape into a bright red badge, as if the knee had been painted by a sunset."
    )
    world.say(
        f"That was when the earlier clue made sense: {foreshadow.sign} had been telling the truth all along, and now {foreshadow.payoff}."
    )
    world.say(
        f"{adult.id} tied a clean cloth around the spot, and {child.id} felt grand enough to tame a tornado and calm enough to sit on a fence."
    )
    world.para()
    child.memes["joy"] += 1
    world.say(
        f"By supper time, {child.id} was hopping again, only this time {child.pronoun('subject')} watched the ground first, just in case the world planned another surprise."
    )
    world.say(
        f"And the red bottle stayed on the shelf, small as a bean and important as a lighthouse, waiting for the next scrape that never grew into a storm."
    )
    world.facts["tended"] = True
    _stitch(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    setting = f["setting"]
    return [
        f"Write a tall tale for a child in which {child.id} gets a scrape at {setting.place} and mercurochrome helps.",
        f"Tell a story with foreshadowing where an early red clue hints at the red mercurochrome that will later treat a little injury.",
        f"Write a child-friendly tall tale about {adult.id} tending a scraped knee with mercurochrome after a big, foolish rush of play.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    injury = f["injury"]
    medicine = f["medicine"]
    foreshadow = f["foreshadow"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id} and {adult.id}. {child.id} is the child who gets hurt, and {adult.id} helps with care."
        ),
        QAItem(
            question="What happened to the child?",
            answer=f"{child.id} got {injury.label} while rushing around. The scrape hurt, but it was small enough for careful tending."
        ),
        QAItem(
            question="How did mercurochrome matter in the story?",
            answer=f"{adult.id} used mercurochrome to clean and soothe the scrape. It stung for a moment, then left the injury bright and tidy so the child could keep going."
        ),
        QAItem(
            question="What did the early clue foreshadow?",
            answer=f"The earlier clue was {foreshadow.sign}. It foreshadowed the red mercurochrome later, because the same red color came back on the child's scrape after it was treated."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {child.id} feeling brave again and watching the ground a little more carefully. The scrape was tended, the red bottle went back on the shelf, and the day settled down."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is mercurochrome?",
            answer="Mercurochrome is an old-fashioned antiseptic medicine for small scrapes and cuts. Grown-ups used it to clean a little wound so it would stay tidy."
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue early in a story that hints at something important later. It helps the ending feel like it was waiting in the story all along."
        ),
        QAItem(
            question="What makes a tall tale a tall tale?",
            answer="A tall tale is told in a larger-than-life way, with bold comparisons and lively exaggeration. The events still make sense, but they sound big and colorful."
        ),
    ]


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
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
foreshadowed(S) :- sign(S).
tall_tale :- mercurochrome(M), sign(S), uses(M), foreshadowed(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid in INJURIES:
        lines.append(asp.fact("injury", iid))
    for mid in MEDICINES:
        lines.append(asp.fact("medicine", mid))
        lines.append(asp.fact("uses", mid))
    for fid in FORESHADOWS:
        lines.append(asp.fact("sign", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting/1.\n#show injury/1.\n#show medicine/1.\n#show sign/1."))
    # The world is intentionally fully connected; just prove the atoms exist.
    return sorted(set(asp.atoms(model, "setting"))), sorted(set(asp.atoms(model, "medicine")))


def asp_verify() -> int:
    rc = 0
    if len(valid_combos()) != len(SETTINGS) * len(INJURIES) * len(MEDICINES) * len(FORESHADOWS):
        print("MISMATCH: Python combo count is wrong.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            print("MISMATCH: smoke-test story is empty.")
            rc = 1
    except Exception as err:  # noqa: BLE001
        print(f"MISMATCH: smoke test crashed: {err}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.injury not in INJURIES:
        raise StoryError(f"Unknown injury: {params.injury}")
    if params.medicine not in MEDICINES:
        raise StoryError(f"Unknown medicine: {params.medicine}")
    if params.foreshadow not in FORESHADOWS:
        raise StoryError(f"Unknown foreshadowing cue: {params.foreshadow}")
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


CURATED = [
    StoryParams(setting="county_fair", child_name="Ned", child_gender="boy", adult_name="Aunt June", adult_gender="woman", injury="knee_scrape", medicine="mercurochrome", foreshadow="red_bandana"),
    StoryParams(setting="riverbank", child_name="Mabel", child_gender="girl", adult_name="Uncle Ben", adult_gender="man", injury="elbow_bump", medicine="mercurochrome", foreshadow="red_reeds"),
    StoryParams(setting="barn_auction", child_name="Ira", child_gender="boy", adult_name="Aunt June", adult_gender="woman", injury="knee_scrape", medicine="mercurochrome", foreshadow="red_lantern"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show setting/1.\n#show injury/1.\n#show medicine/1.\n#show sign/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible combos exist.")
        for combo in valid_combos():
            print("  " + " ".join(combo))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.child_name} at {p.setting} ({p.medicine})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
