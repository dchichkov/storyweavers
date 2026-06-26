#!/usr/bin/env python3
"""
A tiny fairy-tale storyworld about a mirror, potpourri, and a magical tonight
transformation.

Premise:
A child in a small cottage has a plain mirror that shows no magic. Tonight,
the child and a kindly fairy discover that the mirror can reflect a spell of
potpourri-scented magic, but only if the room is prepared with care.

Tension:
The child wants a change right away, yet the mirror is sleepy and the magic
won't work while the room is dusty and the scent is missing.

Turn:
The fairy teaches the child to warm the room with potpourri and speak a gentle
spell.

Resolution:
The mirror glows, the child transforms into a shining dance-sprite for one
night, and the story ends with a soft magical image that proves the change.

This script follows the Storyweavers contract:
- self-contained stdlib world script
- shared results containers imported eagerly
- clingo imported lazily only in ASP helpers
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wears: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "fairy"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Feature:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    kind: str
    guards: set[str]
    boosts: set[str]
    prep: str
    tail: str


@dataclass
class StoryParams:
    place: str
    feature: str
    charm: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.night: bool = True
        self.scent: float = 0.0
        self.spark: float = 0.0
        self.transformed: bool = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.night = self.night
        clone.scent = self.scent
        clone.spark = self.spark
        clone.transformed = self.transformed
        return clone


def _r_scent(world: World) -> list[str]:
    out: list[str] = []
    if world.scent < THRESHOLD:
        return out
    for hero in world.characters():
        if hero.memes.get("hope", 0.0) < THRESHOLD:
            continue
        sig = ("scent", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
        out.append("The room filled with a sweet, steady calm.")
    return out


def _r_magic(world: World) -> list[str]:
    out: list[str] = []
    if world.spark < THRESHOLD or world.scent < THRESHOLD or not world.night:
        return out
    for hero in world.characters():
        if hero.memes.get("ready", 0.0) < THRESHOLD:
            continue
        sig = ("magic", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.meters["glow"] = hero.meters.get("glow", 0.0) + 1
        hero.meters["changed"] = hero.meters.get("changed", 0.0) + 1
        hero.memes["wonder"] = hero.memes.get("wonder", 0.0) + 1
        world.transformed = True
        out.append("The mirror answered with a silver glow.")
    return out


CAUSAL_RULES = [
    _r_scent,
    _r_magic,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def mirror_ready(world: World) -> bool:
    return world.scent >= THRESHOLD and world.spark >= THRESHOLD and world.night


def tell(place: Place, feature: Feature, charm: Charm,
         hero_name: str, hero_type: str, helper_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little", "kind", "curious"],
        memes={"hope": 0.0, "wonder": 0.0, "ready": 0.0, "worry": 0.0},
        meters={"glow": 0.0, "changed": 0.0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label="the fairy helper",
        traits=["gentle", "bright"],
        memes={"hope": 0.0},
    ))
    mirror = world.add(Entity(
        id="Mirror",
        type="mirror",
        label="mirror",
        phrase="an old silver mirror",
        caretaker=helper.id,
        meters={"glow": 0.0},
    ))
    potpourri = world.add(Entity(
        id="Potpourri",
        type="potpourri",
        label="potpourri bowl",
        phrase="a small bowl of dried roses and herbs",
        owner=helper.id,
        meters={"scent": 0.0},
    ))
    world.facts.update(hero=hero, helper=helper, mirror=mirror, potpourri=potpourri,
                       feature=feature, charm=charm)

    world.say(
        f"Once upon a tonight, {hero.id} lived in a little room beside the mirror."
    )
    world.say(
        f"{hero.id} was a little {hero_type} who loved {feature.gerund} and wished for magic."
    )
    world.say(
        f"{helper.id} kept {charm.phrase} near the mirror, because old mirrors liked careful hands."
    )

    world.para()
    world.say(
        f"Tonight, {hero.id} stood before the mirror and whispered, "
        f'"I want to {feature.verb} now."'
    )
    hero.memes["hope"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"But the mirror stayed dim, and the room still smelled plain."
    )

    world.para()
    world.say(
        f"{helper.id} smiled and said, '{charm.prep}, and the mirror may wake.'"
    )
    world.scent += 1
    world.spark += 1
    hero.memes["ready"] += 1
    propagate(world, narrate=True)
    world.say(
        f"{hero.id} held the bowl of {charm.label}, and the air turned sweet."
    )
    world.say(
        f"Then {helper.id} traced a small circle in the air and told {hero.id} to trust the magic."
    )

    world.para()
    if mirror_ready(world):
        hero.meters["glow"] += 1
        hero.meters["changed"] += 1
        world.transformed = True
        world.say(
            f"The mirror shone like moonwater, and {hero.id} transformed into a shining dance-sprite."
        )
        world.say(
            f"By the last hush of tonight, {hero.id} was {feature.gerund}, "
            f"{hero.pronoun('possessive')} feet light as thistledown, while the mirror kept a silver smile."
        )
    else:
        world.say(
            f"The mirror only blinked, because the magic was not ready yet."
        )

    world.facts["result"] = "transformed" if world.transformed else "unchanged"
    return world


SETTINGS = {
    "cottage": Place(name="the cottage", indoor=True, affords={"mirror_magic"}),
    "attic": Place(name="the attic", indoor=True, affords={"mirror_magic"}),
    "garden_room": Place(name="the garden room", indoor=True, affords={"mirror_magic"}),
}

FEATURES = {
    "dance": Feature(
        id="dance",
        verb="dance in the moonlight",
        gerund="dancing in the moonlight",
        rush="rush to spin by the mirror",
        risk="the night would stay ordinary",
        zone={"feet", "hands"},
        keyword="dance",
        tags={"magic", "mirror"},
    ),
    "sing": Feature(
        id="sing",
        verb="sing a silver song",
        gerund="singing silver songs",
        rush="hurry to sing at the mirror",
        risk="the hush would stay heavy",
        zone={"mouth", "hands"},
        keyword="song",
        tags={"magic", "mirror"},
    ),
    "change": Feature(
        id="change",
        verb="change into a star-bright child",
        gerund="changing like a star in water",
        rush="dart toward the mirror",
        risk="the wish would remain asleep",
        zone={"whole"},
        keyword="change",
        tags={"transformation", "magic", "mirror"},
    ),
}

CHARMS = {
    "potpourri": Charm(
        id="potpourri",
        label="potpourri",
        phrase="a bowl of rose potpourri",
        kind="scent",
        guards={"dusty"},
        boosts={"scent"},
        prep="Warm the room with potpourri first",
        tail="the sweet scent drifted to the glass",
    ),
    "sparkle": Charm(
        id="sparkle",
        label="sparkle dust",
        phrase="a pinch of glittering dust",
        kind="spark",
        guards={"dim"},
        boosts={"spark"},
        prep="Scatter a pinch of sparkle dust first",
        tail="the tiny sparks kissed the mirror",
    ),
    "lantern": Charm(
        id="lantern",
        label="lantern light",
        phrase="a little lantern with a golden flame",
        kind="light",
        guards={"dark"},
        boosts={"spark"},
        prep="Light the lantern first",
        tail="the warm light woke the silver frame",
    ),
}

NAMES_GIRL = ["Mina", "Luna", "Elin", "Iris", "Nora"]
NAMES_BOY = ["Finn", "Theo", "Owen", "Milo", "Ari"]
TRAITS = ["curious", "gentle", "brave", "dreamy", "quiet"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        for feat in FEATURES:
            for charm in CHARMS:
                combos.append((place, feat, charm))
    return combos


def explain_rejection(feature: Feature, charm: Charm) -> str:
    return (
        f"(No story: the mirror magic needs both {feature.keyword} and {charm.label}; "
        f"this combination cannot make the transformation feel earned.)"
    )


def explain_gender(gender: str, name: str) -> str:
    return f"(No story: the chosen name {name} does not match the requested {gender}.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, feat, charm = f["hero"], f["feature"], f["charm"]
    return [
        f'Write a fairy tale for a small child about a mirror, potpourri, and {feat.keyword} tonight.',
        f"Tell a gentle magical story where {hero.id} wants to {feat.verb} but needs {charm.label} first.",
        f"Make a cozy story with a transformation in the mirror and a sweet potpourri scent.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, feat, charm, mirror = f["hero"], f["helper"], f["feature"], f["charm"], f["mirror"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do tonight?",
            answer=f"{hero.id} wanted to {feat.verb} by the mirror tonight.",
        ),
        QAItem(
            question=f"Why did {helper.id} bring potpourri to the mirror?",
            answer=f"{helper.id} brought potpourri so the room would smell sweet and the mirror magic could wake.",
        ),
        QAItem(
            question=f"What changed after the scent and spark were ready?",
            answer=f"The mirror glowed, and {hero.id} transformed into a shining dance-sprite.",
        ),
        QAItem(
            question=f"What did the mirror do at the end of the story?",
            answer=f"The mirror shone like moonwater and kept a silver smile while {hero.id} danced nearby.",
        ),
    ]
    if world.transformed:
        qa.append(QAItem(
            question=f"How did the magic transform {hero.id}?",
            answer=f"After the potpourri and sparkle were set out, the mirror answered, and {hero.id} became a shining {hero.type} full of wonder.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mirror?",
            answer="A mirror is a shiny surface that shows back what is standing in front of it.",
        ),
        QAItem(
            question="What is potpourri?",
            answer="Potpourri is a mix of dried flowers and herbs that makes a room smell sweet.",
        ),
        QAItem(
            question="What does magic mean in a fairy tale?",
            answer="Magic is a special kind of power in fairy tales that can make surprising things happen.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form into another.",
        ),
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  night={world.night} scent={world.scent} spark={world.spark} transformed={world.transformed}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="cottage", feature="change", charm="potpourri", name="Mina", gender="girl", helper="fairy", trait="dreamy"),
    StoryParams(place="attic", feature="dance", charm="sparkle", name="Finn", gender="boy", helper="fairy", trait="brave"),
    StoryParams(place="garden_room", feature="sing", charm="lantern", name="Luna", gender="girl", helper="fairy", trait="gentle"),
]


ASP_RULES = r"""
featured_story(P,F,C) :- place(P), feature(F), charm(C).
needs_scent(C) :- charm(C), boosts(C,scent).
needs_spark(C) :- charm(C), boosts(C,spark).
good_combo(P,F,C) :- featured_story(P,F,C), place(P), feature(F), charm(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for fid, feat in FEATURES.items():
        lines.append(asp.fact("feature", fid))
        for tag in sorted(feat.tags):
            lines.append(asp.fact("tagged", fid, tag))
    for cid, charm in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        for b in sorted(charm.boosts):
            lines.append(asp.fact("boosts", cid, b))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_combo/3."))
    clingo_set = set(asp.atoms(model, "good_combo"))
    python_set = set((p, f, c) for p, f, c in valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale story world: mirror, potpourri, and tonight's magic transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--feature", choices=FEATURES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["fairy"])
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
    if args.feature and args.charm:
        feat, charm = FEATURES[args.feature], CHARMS[args.charm]
        if args.charm == "potpourri" and "scent" not in charm.boosts:
            raise StoryError(explain_rejection(feat, charm))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.feature is None or c[1] == args.feature)
              and (args.charm is None or c[2] == args.charm)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, feature, charm = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper = args.helper or "fairy"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, feature=feature, charm=charm, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], FEATURES[params.feature], CHARMS[params.charm],
                 params.name, "girl" if params.gender == "girl" else "boy", params.helper)
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
        print(asp_program("#show good_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show good_combo/3."))
        combos = sorted(set(asp.atoms(model, "good_combo")))
        print(f"{len(combos)} compatible combos:\n")
        for p, f, c in combos:
            print(f"  {p:12} {f:10} {c:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.name}: {p.feature} with {p.charm} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
