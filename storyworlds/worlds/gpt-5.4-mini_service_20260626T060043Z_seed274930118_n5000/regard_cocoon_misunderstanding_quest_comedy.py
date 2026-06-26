#!/usr/bin/env python3
"""
storyworlds/worlds/regard_cocoon_misunderstanding_quest_comedy.py
==================================================================

A small comedy storyworld about a child, a cocoon, and a silly
misunderstanding over what it means to "regard" something on a quest.

Premise:
- A child finds a cocoon and is told to regard it.
- The child misunderstands "regard" as "re-guard" and tries to protect it in
  an over-the-top way.
- A quest follows to find the right cozy-but-not-too-cozy spot.
- The ending resolves the misunderstanding with a gentle comedy beat.

This world is state-driven: physical meters track where the cocoon is and how
safe/balanced it feels; emotional memes track curiosity, embarrassment, and
warm regard.
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
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    quiet: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    goal: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cocoon:
    label: str = "cocoon"
    phrase: str = "a pale little cocoon"
    fragile: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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


def _inc(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def _mem(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


def regard_is_misread(world: World) -> bool:
    return world.facts.get("misunderstanding", False)


def quiet_place(world: World, quest: Quest) -> bool:
    return world.setting.quiet and quest.id in world.setting.affords


def do_quest(world: World, hero: Entity, coco: Entity, quest: Quest, narrate: bool = True) -> None:
    if not quiet_place(world, quest):
        raise StoryError("This setting cannot host that quest in a believable way.")
    _inc(hero, "questing", 1)
    _mem(hero, "determination", 1)
    _inc(coco, "moved", 1)
    _inc(coco, "safe", 1)
    if narrate:
        world.say(f"{hero.id} began the quest to {quest.verb} while carrying {coco.label} carefully.")


def resolve(world: World, hero: Entity, helper: Entity, coco: Entity) -> None:
    _mem(hero, "regard", 2)
    _mem(hero, "embarrassment", 1)
    _inc(coco, "safe", 1)
    world.say(
        f"Then {helper.id} laughed kindly and explained that to regard the cocoon "
        f"meant to watch it with care, not to re-guard it like a tiny treasure vault."
    )
    world.say(
        f"{hero.id} blushed, set {coco.label} in a quiet spot, and sat very still to regard it properly."
    )


SETTINGS = {
    "garden": Setting(place="the garden", quiet=True, affords={"watch"}),
    "library_window": Setting(place="the library window seat", quiet=True, affords={"watch"}),
    "porch": Setting(place="the porch", quiet=True, affords={"watch"}),
}

QUESTS = {
    "watch": Quest(
        id="watch",
        verb="watch the cocoon",
        gerund="watching the cocoon",
        rush="dash to the window seat",
        goal="find the best quiet spot",
        keyword="regard",
        tags={"regard", "cocoon", "quiet"},
    ),
}

HEROES = {
    "girl": ["Mina", "Luna", "Pia", "Tessa", "Nina"],
    "boy": ["Owen", "Eli", "Milo", "Jasper", "Theo"],
}

HELPERS = {
    "aunt": ["Aunt Bea", "Aunt June", "Aunt Suri"],
    "mother": ["Mom", "Mama", "Mother"],
    "father": ["Dad", "Papa", "Father"],
}


@dataclass
class StoryParams:
    place: str
    quest: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Comedy story world about a cocoon, a misunderstanding, and a quest."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["aunt", "mother", "father"])
    ap.add_argument("--name")
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


def valid_combos() -> list[tuple[str, str]]:
    return [(p, q) for p in SETTINGS for q in QUESTS if q in SETTINGS[p].affords]


def explain_rejection(place: str, quest: str) -> str:
    return f"(No story: {QUESTS[quest].verb} does not fit {SETTINGS[place].place} in this world.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, quest = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HEROES[gender])
    helper = args.helper or rng.choice(list(HELPERS))
    return StoryParams(place=place, quest=quest, name=name, gender=gender, helper=helper)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    quest = QUESTS[params.quest]
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper_name = rng_helper(params.helper)
    helper = world.add(Entity(id=helper_name, kind="character", type=params.helper))
    coco = world.add(Entity(id="cocoon", type="cocoon", label="the cocoon", phrase="a pale little cocoon"))

    _mem(hero, "curiosity", 1)
    _mem(hero, "care", 1)
    _mem(hero, "joy", 1)

    world.say(
        f"{hero.id} found {coco.phrase} tucked beside a leaf in {world.setting.place}. "
        f"{hero.id} wanted to regard it, because it looked like a tiny sleeping secret."
    )
    world.say(
        f"But {helper.id} said, \"Please regard the cocoon carefully,\" and {hero.id} "
        f"misunderstood the word completely."
    )
    world.para()

    world.facts["misunderstanding"] = True
    _mem(hero, "confusion", 1)
    _mem(hero, "determination", 1)
    world.say(
        f"{hero.id} thought regard meant re-guard, so {hero.id} wrapped the cocoon in a napkin, "
        f"a scarf, and one very serious-looking mitten."
    )
    world.say(
        f"That turned into a silly quest to {quest.goal}, because the cocoon now looked less cozy "
        f"and more like it was packed for a parade."
    )
    world.say(
        f"{hero.id} rushed to {quest.rush}, carrying the cocoon as if it were a royal snack."
    )
    world.para()

    do_quest(world, hero, coco, quest, narrate=False)
    world.say(
        f"At the quiet spot, {hero.id} finally noticed the cocoon could not breathe well under all that cloth."
    )
    resolve(world, hero, helper, coco)
    world.say(
        f"After that, {hero.id} and {helper.id} sat together and listened to the hush of the room, "
        f"waiting for the little life inside to wake up."
    )

    world.facts.update(hero=hero, helper=helper, cocoon=coco, quest=quest, params=params)
    return world


def rng_helper(kind: str) -> str:
    return random.choice(HELPERS[kind])


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, quest = f["hero"], f["helper"], f["quest"]
    return [
        f'Write a short comedy for a young child about {hero.id}, a cocoon, and the word "regard".',
        f"Tell a gentle story where {hero.id} misunderstands what {helper.id} meant and goes on a quest.",
        f"Write a funny but caring story about watching a cocoon the right way in {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, quest = f["hero"], f["helper"], f["quest"]
    coco = f["cocoon"]
    return [
        QAItem(
            question=f"What did {hero.id} find in {world.setting.place}?",
            answer=f"{hero.id} found {coco.phrase}, which looked like a tiny sleeping secret.",
        ),
        QAItem(
            question=f"Why did {hero.id} start a quest after {helper.id} gave the instruction?",
            answer=(
                f"{hero.id} misunderstood regard and thought it meant re-guard, so {hero.id} "
                f"overwrapped the cocoon and went looking for a better, quieter spot."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} learn at the end of the story?",
            answer=(
                f"{hero.id} learned that to regard the cocoon means to watch it with care, "
                f"not to smother it in too many blankets."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does regard mean in this world?",
            answer="In this world, to regard something means to look at it with care and attention.",
        ),
        QAItem(
            question="What is a cocoon?",
            answer="A cocoon is a small protective covering made by some insects while they change inside it.",
        ),
        QAItem(
            question="Why can too many covers be a problem for a cocoon?",
            answer="Too many covers can trap the cocoon and stop it from having the quiet air it needs.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="garden", quest="watch", name="Mina", gender="girl", helper="aunt"),
    StoryParams(place="library_window", quest="watch", name="Theo", gender="boy", helper="mother"),
    StoryParams(place="porch", quest="watch", name="Luna", gender="girl", helper="father"),
]


ASP_RULES = r"""
valid(Place,Quest) :- setting(Place), quest(Quest), affords(Place,Quest).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p, s in SETTINGS.items():
        lines.append(asp.fact("setting", p))
        for q in sorted(s.affords):
            lines.append(asp.fact("affords", p, q))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, quest) combos:\n")
        for place, quest in combos:
            print(f"  {place:16} {quest}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
            header = f"### {p.name}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
