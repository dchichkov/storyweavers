#!/usr/bin/env python3
"""
storyworlds/worlds/gpt_5_4_mini_chr_friendship_magic_fable.py
==============================================================

A small fable-like storyworld about friendship, a little magic, and a child
named Chr. Two friends face a problem with a magical object; one tries a
reckless spell, the other offers a kinder path, and the ending proves that
friendship makes the magic work better.

The stories are intentionally compact and classical: a setup, a test, a turn,
and a concluding image that shows what changed.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {"glow": 0.0, "broken": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"joy": 0.0, "trust": 0.0, "fear": 0.0})

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
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    mood: str
    light_need: str
    risky_if: str
    safe_need: str


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    power: int
    sense: int
    risk: int
    help_text: str
    fail_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    power: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
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
        import copy
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


def _rule_shatter(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.meters["broken"] >= THRESHOLD and ("shatter", e.id) not in world.fired:
            world.fired.add(("shatter", e.id))
            for ch in world.entities.values():
                if ch.kind == "character":
                    ch.memes["fear"] += 1
            out.append("__shatter__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for s in _rule_shatter(world):
            changed = True
            if not s.startswith("__"):
                out.append(s)
    if narrate:
        for s in out:
            world.say(s)
    return out


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for c in CHARMS:
            for r in REMEDIES:
                if c.sense >= SENSE_MIN and c.power <= r.power:
                    combos.append((p.id, c.id, r.id))
    return combos


def choose_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    pool = [n for n in pool if n != avoid] or pool
    return rng.choice(pool), gender


def warning_needed(place: Place, charm: Charm) -> bool:
    return charm.risk > 0 and place.light_need in charm.tags


def can_repair(charm: Charm, remedy: Remedy) -> bool:
    return remedy.power >= charm.power


def spell_outcome(charm: Charm, remedy: Remedy) -> str:
    return "fixed" if can_repair(charm, remedy) else "ruined"


def tell(place: Place, charm: Charm, remedy: Remedy,
         chr_name: str = "Chr", chr_gender: str = "boy",
         friend_name: str = "Mira", friend_gender: str = "girl",
         elder_name: str = "Grandma", elder_gender: str = "woman") -> World:
    world = World()
    chrn = world.add(Entity(id=chr_name, kind="character", type=chr_gender, role="seeker",
                            traits=["curious"]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend",
                              traits=["gentle", "wise"]))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_gender, role="elder",
                             label="the elder"))
    lantern = world.add(Entity(id="lantern", kind="thing", type="thing", label="the lantern"))
    spark = world.add(Entity(id="spark", kind="thing", type="thing", label=charm.label))
    world.facts["place"] = place
    world.facts["charm"] = charm
    world.facts["remedy"] = remedy
    world.facts["chr"] = chrn
    world.facts["friend"] = friend
    world.facts["elder"] = elder

    chrn.memes["joy"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"In the little village there was a child named {chrn.id}, and {friend.id}, "
        f"who were friends as steady as roots. They loved to meet beside {place.label}."
    )
    world.say(
        f"The place looked {place.mood}, and it needed {place.safe_need}. "
        f"{chrn.id} found {charm.phrase}, a magic charm that promised light."
    )
    world.para()
    world.say(
        f'"Let me try the {charm.label}," said {chrn.id}. "{charm.help_text}."'
    )
    world.say(
        f"{friend.id} touched {friend.pronoun('possessive')} chin and frowned. "
        f'"That charm is not meant to be used alone," {friend.pronoun()} said.'
    )

    if not warning_needed(place, charm):
        raise StoryError("This storyworld needs a place that truly needs the charm's light.")

    world.para()
    if charm.sense < SENSE_MIN:
        raise StoryError(f"Refusing charm '{charm.id}': it is too reckless for a fable.")

    if charm.power <= 1:
        world.say(
            f"{chrn.id} lifted the charm, and a weak flicker leapt out. It trembled, "
            f"then bit the old paint on the wall."
        )
        spark.meters["broken"] += 1
        world.say(f"The little magic sputtered and went dim.")
    else:
        world.say(
            f"{chrn.id} lifted the charm, and the glow rushed out bright as dawn. "
            f"It should have been enough, but it ran wild."
        )
        spark.meters["broken"] += 1
        propagate(world, narrate=False)
        world.say(f"The bright spell cracked the lantern's glass and made the room shiver.")

    world.para()
    world.say(
        f"{friend.id} did not laugh. Instead, {friend.pronoun()} ran to {elder.label_word}."
    )
    world.say(
        f"The elder came with {remedy.phrase}, a calm old answer that knew how to mend the crack."
    )
    if can_repair(charm, remedy):
        spark.meters["broken"] = 0.0
        lantern.meters["glow"] = 1.0
        chrn.memes["fear"] += 1
        chrn.memes["trust"] += 1
        friend.memes["joy"] += 1
        world.say(
            f"{elder.id} placed the remedy near the broken lantern and whispered a careful word. "
            f"The crack closed, and the light returned softer than before."
        )
        world.say(
            f"{chrn.id} bowed {chrn.pronoun('possessive')} head. "
            f'"I thought the loudest magic was the best," {chrn.id} said. '
            f'"But friendship kept the light from being lost."'
        )
        world.para()
        world.say(
            f"After that, {chrn.id} and {friend.id} used the charm only with the elder nearby. "
            f"The lantern glowed each evening, and the village road shone kindly under it."
        )
        outcome = "fixed"
    else:
        world.say(
            f"The remedy was too small, and the crack stayed open. So {elder.id} told them "
            f"to carry the lantern outside and leave the charm alone."
        )
        world.say(
            f"They did, and at sunrise the village still had work to do, but the friends were safe "
            f"and wiser."
        )
        outcome = "broken"

    world.facts["outcome"] = outcome
    world.facts["lantern"] = lantern
    return world


def prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tiny fable for a young child that includes the word "{f["chr"].id}" and a magic mistake, then ends with friendship helping to fix it.',
        f"Tell a story where {f['chr'].id} and a friend find {f['charm'].label}, make trouble with it, and then listen to an elder.",
        f'Write a gentle fable about friendship and magic near {f["place"].label}, with a lesson about using power wisely.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    chrn = f["chr"]
    friend = f["friend"]
    elder = f["elder"]
    place = f["place"]
    charm = f["charm"]
    remedy = f["remedy"]
    out = f["outcome"]
    items = [
        QAItem(
            question="Who are the friends in the story?",
            answer=f"The friends are {chrn.id} and {friend.id}. They care about each other and face the magic problem together."
        ),
        QAItem(
            question="Why was the magic trouble?",
            answer=f"The charm was used in a place that needed careful light, and {chrn.id} tried to use it alone. That made the glow crack the lantern instead of helping gently."
        ),
    ]
    if out == "fixed":
        items.append(
            QAItem(
                question="How did the story end?",
                answer=f"The elder used {remedy.phrase} and mended the broken lantern. After that, {chrn.id} and {friend.id} shared the light safely and their friendship felt stronger."
            )
        )
        items.append(
            QAItem(
                question="What did {0} learn?".format(chrn.id),
                answer=f"{chrn.id} learned that magic works best with patience and good company. A friend and an elder can make a hard thing gentle."
            )
        )
    else:
        items.append(
            QAItem(
                question="How did the story end?",
                answer=f"The crack could not be fully fixed, so the elder asked them to leave the charm alone. They stayed safe, and the lesson still made them wiser."
            )
        )
    return items


WORLD_KNOWLEDGE = {
    "friendship": [
        QAItem(question="What is friendship?", answer="Friendship is a kind bond between people who care for and help one another."),
        QAItem(question="Why is a good friend helpful?", answer="A good friend can warn you, share ideas, and help you do the safe and kind thing."),
    ],
    "magic": [
        QAItem(question="What is magic in a fable?", answer="Magic is a wondrous power in the story, but it still needs wise use and careful choices."),
        QAItem(question="Can magic be dangerous?", answer="Yes. In stories, magic can be dangerous if it is used carelessly or for the wrong purpose."),
    ],
    "lantern": [
        QAItem(question="What is a lantern?", answer="A lantern is a light that helps people see in the dark."),
    ],
}


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = {"friendship", "magic", "lantern"}
    if f["place"].id == "moon_gate":
        tags.add("moon")
    out: list[QAItem] = []
    for tag in ["friendship", "magic", "lantern"]:
        out.extend(WORLD_KNOWLEDGE.get(tag, []))
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
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


PLACES = [
    Place(id="oak_hill", label="Oak Hill", mood="quiet and misty", light_need="light", risky_if="alone", safe_need="a lantern"),
    Place(id="moon_gate", label="the Moon Gate", mood="dark and silver", light_need="light", risky_if="alone", safe_need="a lantern"),
    Place(id="old_bridge", label="the old bridge", mood="windy and dim", light_need="light", risky_if="alone", safe_need="a lantern"),
]

CHARMS = [
    Charm(id="spark_word", label="spark word", phrase="a spark word etched on a pebble", power=2, sense=3, risk=1,
          help_text="I can make the path bright", fail_text="I can make the path bright but I may crack the glass",
          tags={"light"}),
    Charm(id="silver_whistle", label="silver whistle", phrase="a silver whistle that woke shining moths", power=1, sense=2, risk=1,
          help_text="I can call light from the dusk", fail_text="I can call light from the dusk, if it is used gently",
          tags={"light"}),
    Charm(id="star_seed", label="star seed", phrase="a tiny star seed in a blue pouch", power=3, sense=4, risk=1,
          help_text="I can glow like a small star", fail_text="I can glow like a small star, but I need a careful hand",
          tags={"light"}),
]

REMEDIES = [
    Remedy(id="mend_ink", label="mend ink", phrase="mend ink from a warm bottle", power=3, tags={"repair"}),
    Remedy(id="soft_cloth", label="soft cloth", phrase="a soft cloth and calm hands", power=2, tags={"repair"}),
    Remedy(id="gold_thread", label="gold thread", phrase="gold thread for careful repair", power=4, tags={"repair"}),
]

GIRL_NAMES = ["Mira", "Lina", "Ivy", "Nia", "Tess", "Sana"]
BOY_NAMES = ["Arin", "Bram", "Cato", "Finn", "Jory", "Ludo"]
SENSE_MIN = 2


@dataclass
class StoryParams:
    place: str
    charm: str
    remedy: str
    chr_name: str
    chr_gender: str
    friend_name: str
    friend_gender: str
    elder_name: str
    elder_gender: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="oak_hill", charm="spark_word", remedy="gold_thread", chr_name="Chr", chr_gender="boy", friend_name="Mira", friend_gender="girl", elder_name="Grandma", elder_gender="woman"),
    StoryParams(place="moon_gate", charm="star_seed", remedy="mend_ink", chr_name="Chr", chr_gender="boy", friend_name="Arin", friend_gender="boy", elder_name="Grandma", elder_gender="woman"),
    StoryParams(place="old_bridge", charm="silver_whistle", remedy="soft_cloth", chr_name="Chr", chr_gender="boy", friend_name="Nia", friend_gender="girl", elder_name="Grandpa", elder_gender="man"),
]


def valid_story(params: StoryParams) -> bool:
    try:
        p = PLACES_BY_ID[params.place]
        c = CHARMS_BY_ID[params.charm]
        r = REMEDIES_BY_ID[params.remedy]
    except KeyError:
        return False
    return warning_needed(p, c) and can_repair(c, r) and c.sense >= SENSE_MIN


def explain_rejection(params: StoryParams) -> str:
    return "(No story: the chosen magic is too weak, too reckless, or doesn't fit the place.)"


PLACES_BY_ID = {p.id: p for p in PLACES}
CHARMS_BY_ID = {c.id: c for c in CHARMS}
REMEDIES_BY_ID = {r.id: r for r in REMEDIES}


ASP_RULES = r"""
place(oak_hill). place(moon_gate). place(old_bridge).
needs_light(oak_hill). needs_light(moon_gate). needs_light(old_bridge).
charm(spark_word). charm(silver_whistle). charm(star_seed).
sense(spark_word,3). sense(silver_whistle,2). sense(star_seed,4).
risk(spark_word,1). risk(silver_whistle,1). risk(star_seed,1).
tags_light(spark_word). tags_light(silver_whistle). tags_light(star_seed).
remedy(mend_ink). remedy(soft_cloth). remedy(gold_thread).
power(mend_ink,3). power(soft_cloth,2). power(gold_thread,4).

valid(P,C,R) :- place(P), charm(C), remedy(R), needs_light(P), tags_light(C), sense(C,S), sense_min(M), S >= M, power(R,PR), power(C,PC), PR >= PC.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("sense_min", SENSE_MIN)]
    for p in PLACES:
        lines.append(asp.fact("place", p.id))
        lines.append(asp.fact("needs_light", p.id))
    for c in CHARMS:
        lines.append(asp.fact("charm", c.id))
        lines.append(asp.fact("sense", c.id, c.sense))
        lines.append(asp.fact("power", c.id, c.power))
        if "light" in c.tags:
            lines.append(asp.fact("tags_light", c.id))
    for r in REMEDIES:
        lines.append(asp.fact("remedy", r.id))
        lines.append(asp.fact("power", r.id, r.power))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos:")
        print("  only in python:", sorted(py - cl))
        print("  only in asp:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=True, qa=True)
        print("OK: story generation and emit smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like storyworld of friendship and magic.")
    ap.add_argument("--place", choices=PLACES_BY_ID)
    ap.add_argument("--charm", choices=CHARMS_BY_ID)
    ap.add_argument("--remedy", choices=REMEDIES_BY_ID)
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
    if args.place and args.charm and args.remedy:
        if not valid_story(StoryParams(place=args.place, charm=args.charm, remedy=args.remedy,
                                       chr_name="Chr", chr_gender="boy", friend_name="Mira",
                                       friend_gender="girl", elder_name="Grandma", elder_gender="woman")):
            raise StoryError(explain_rejection(StoryParams(place=args.place, charm=args.charm, remedy=args.remedy,
                                                           chr_name="Chr", chr_gender="boy", friend_name="Mira",
                                                           friend_gender="girl", elder_name="Grandma", elder_gender="woman")))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.charm is None or c[1] == args.charm)
              and (args.remedy is None or c[2] == args.remedy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, charm, remedy = rng.choice(sorted(combos))
    friend_name, friend_gender = choose_name(rng, avoid="Chr")
    elder_name = rng.choice(["Grandma", "Grandpa", "Aunt Wren"])
    elder_gender = {"Grandma": "woman", "Grandpa": "man", "Aunt Wren": "woman"}[elder_name]
    return StoryParams(place=place, charm=charm, remedy=remedy,
                       chr_name="Chr", chr_gender="boy",
                       friend_name=friend_name, friend_gender=friend_gender,
                       elder_name=elder_name, elder_gender=elder_gender)


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES_BY_ID[params.place]
        charm = CHARMS_BY_ID[params.charm]
        remedy = REMEDIES_BY_ID[params.remedy]
    except KeyError as e:
        raise StoryError(f"Invalid parameter: {e.args[0]}") from None
    if not valid_story(params):
        raise StoryError(explain_rejection(params))
    world = tell(place, charm, remedy, params.chr_name, params.chr_gender,
                 params.friend_name, params.friend_gender, params.elder_name, params.elder_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
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
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for p, c, r in combos:
            print(f"  {p:10} {c:16} {r}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
