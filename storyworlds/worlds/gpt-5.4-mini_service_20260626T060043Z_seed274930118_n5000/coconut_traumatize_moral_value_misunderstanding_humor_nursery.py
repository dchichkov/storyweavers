#!/usr/bin/env python3
"""
storyworlds/worlds/coconut_traumatize_moral_value_misunderstanding_humor_nursery.py
====================================================================================

A small nursery-rhyme storyworld about a coconut, a misunderstanding, a little
fright, and a kind moral turn.

The seed idea:
- A child finds a coconut.
- Someone misunderstands what it is for.
- A loud bump or prank startles a friend.
- Humor keeps the tale light.
- The ending teaches a gentle moral: be honest, be careful, and help fix the
  mistake.

The world is intentionally tiny and constraint-checked: the coconut can roll,
fall, crack, or be used as a snack/drum/hat, but only in ways that fit the
selected setting and the chosen misunderstanding.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wearable: bool = False
    edible: bool = False
    playable: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class CoconutUse:
    id: str
    verb: str
    gerund: str
    risk: str
    punchline: str
    effect: str
    kind: str  # "roll" | "drop" | "tap"
    tags: set[str] = field(default_factory=set)


@dataclass
class Token:
    id: str
    label: str
    phrase: str
    region: str
    tag: str
    playable: bool = False
    wearable: bool = False
    edible: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = copy.deepcopy(self.facts)
        return w


SETTINGS = {
    "beach": Setting(place="the beach", indoor=False, affords={"roll", "tap", "drop"}),
    "yard": Setting(place="the yard", indoor=False, affords={"roll", "drop"}),
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"tap", "drop"}),
    "porch": Setting(place="the porch", indoor=False, affords={"roll", "tap", "drop"}),
}

USES = {
    "roll": CoconutUse(
        id="roll",
        verb="roll the coconut",
        gerund="rolling the coconut",
        risk="it may bump into toes and startle someone",
        punchline="it goes boing-boing like a tiny drum",
        effect="rolled",
        kind="roll",
        tags={"coconut", "humor", "misunderstanding"},
    ),
    "tap": CoconutUse(
        id="tap",
        verb="tap the coconut",
        gerund="tapping the coconut",
        risk="a loud tap can sound like a knock at the door",
        punchline="it sounds like a polite little knock",
        effect="tapped",
        kind="tap",
        tags={"coconut", "humor", "misunderstanding"},
    ),
    "drop": CoconutUse(
        id="drop",
        verb="drop the coconut",
        gerund="dropping the coconut",
        risk="it might crack and make everyone gasp",
        punchline="the shell gives one surprising crack",
        effect="dropped",
        kind="drop",
        tags={"coconut", "traumatize", "humor", "moral"},
    ),
}

TOKENS = {
    "shell": Token(id="shell", label="shell", phrase="a hard brown shell", region="hands", tag="coconut", playable=True),
    "bowl": Token(id="bowl", label="bowl", phrase="a little bowl", region="table", tag="misunderstanding", wearable=False, edible=False),
    "hat": Token(id="hat", label="hat", phrase="a funny hat", region="head", tag="humor", wearable=True),
    "milk": Token(id="milk", label="milk", phrase="sweet coconut milk", region="mouth", tag="moral", edible=True),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ella", "Ruby"]
BOY_NAMES = ["Ben", "Leo", "Max", "Noah", "Finn", "Owen"]
TRAITS = ["tiny", "bright", "cheery", "curious", "bouncy", "silly"]


@dataclass
class StoryParams:
    place: str
    use: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for use in USES:
            if use in setting.affords:
                out.append((place, use))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world about coconut, misunderstanding, humor, and a gentle moral.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--use", choices=USES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father", "grandma", "grandpa"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.use is None or c[1] == args.use)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, use = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father", "grandma", "grandpa"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, use=use, name=name, gender=gender, helper=helper, trait=trait)


def _narrate_misunderstanding(world: World, child: Entity, helper: Entity, use: CoconutUse) -> None:
    world.say(f"{child.id} found a coconut by the {world.setting.place}.")
    world.say(f"{child.pronoun().capitalize()} thought {child.pronoun('possessive')} coconut could do {use.verb}, and that looked like fun.")
    world.say(f"But {helper.label} misunderstood the plan and said, \"Careful now, that coconut may make a rumpity bump!\"")
    world.say(f"{use.punchline.capitalize()}, and that made {helper.label} laugh even while the child blinked in surprise.")


def _apply_use(world: World, child: Entity, use: CoconutUse) -> None:
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1.0
    if use.kind == "drop":
        child.memes["startle"] = child.memes.get("startle", 0.0) + 1.0
        child.memes["worry"] = child.memes.get("worry", 0.0) + 1.0
    elif use.kind == "tap":
        child.memes["humor"] = child.memes.get("humor", 0.0) + 1.0
    else:
        child.memes["humor"] = child.memes.get("humor", 0.0) + 1.0


def _apply_moral_turn(world: World, child: Entity, helper: Entity, use: CoconutUse) -> None:
    world.say(f"{helper.label} smiled and showed {child.id} the safe way to do it.")
    if use.id == "drop":
        world.say(f"They did not keep the mistake a secret; {child.id} said sorry for the fright.")
        child.memes["guilt"] = child.memes.get("guilt", 0.0) + 1.0
    world.say(f"Together they shared the coconut, and the little lesson was clear: tell the truth, slow your hands, and mind your friends.")
    child.memes["moral"] = child.memes.get("moral", 0.0) + 1.0


def tell(setting: Setting, use: CoconutUse, child_name: str, gender: str, helper_kind: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=gender))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_kind, label=f"the {helper_kind}"))
    coconut = world.add(Entity(id="Coconut", type="coconut", label="coconut", phrase="a coconut", owner=child.id))
    shell = world.add(Entity(id="Shell", type="shell", label="shell", phrase="a hard shell", caretaker=helper.id))
    world.facts.update(child=child, helper=helper, coconut=coconut, shell=shell, use=use, setting=setting)
    world.say(f"Little {trait} {child_name} lived near {setting.place}.")
    world.say(f"{child_name} liked the coconut because it looked like a round brown moon with a grin.")
    world.para()
    _narrate_misunderstanding(world, child, helper, use)
    _apply_use(world, child, use)
    world.para()
    if use.kind == "drop":
        world.say(f"{use.effect.capitalize()}! The shell made a cracky sound, and the room went hush for one tiny beat.")
    elif use.kind == "tap":
        world.say(f"{use.effect.capitalize()}! It sounded like a tiny tune, and even the kettle seemed to listen.")
    else:
        world.say(f"{use.effect.capitalize()}! The coconut wobbled along, as busy as a beetle in a bowl.")
    _apply_moral_turn(world, child, helper, use)
    world.say(f"At the end, {child_name} held the coconut gently, and nobody felt frightened anymore.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    use = f["use"]
    return [
        'Write a short nursery-rhyme story for a small child about a coconut and a funny misunderstanding.',
        f"Tell a gentle story where {child.id} tries to {use.verb} and a helper misunderstands, but the ending teaches a moral.",
        "Write a rhyme-like tale with humor, a little surprise, and a kind apology.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    use = f["use"]
    place = f["setting"].place
    qa = [
        QAItem(
            question=f"What did {child.id} find near {place}?",
            answer=f"{child.id} found a coconut near {place}, and thought it might be fun to {use.verb}.",
        ),
        QAItem(
            question=f"Why did {helper.label} worry about the coconut?",
            answer=f"{helper.label} worried because {use.risk}. That worry was a little serious, but the story stayed light and silly.",
        ),
        QAItem(
            question=f"What did the misunderstanding add to the story?",
            answer="It added humor, because the helper took the coconut the wrong way at first, and everyone had to untangle the mistake kindly.",
        ),
    ]
    if use.id == "drop":
        qa.append(QAItem(
            question="What moral did the story teach after the loud crack?",
            answer="It taught that we should tell the truth, be careful with other people's feelings, and help fix a mistake after we make it.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a coconut?",
            answer="A coconut is a hard round fruit with a thick shell and soft white meat inside.",
        ),
        QAItem(
            question="Why can a misunderstanding be funny in a story?",
            answer="A misunderstanding can be funny when someone guesses wrong in a harmless way, and the mistake is quickly shown in a gentle, silly moment.",
        ),
        QAItem(
            question="What does moral value mean in a story?",
            answer="Moral value means the story points to a good lesson, like honesty, kindness, or taking care not to frighten others.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(beach). setting(yard). setting(kitchen). setting(porch).
affords(beach,roll). affords(beach,tap). affords(beach,drop).
affords(yard,roll). affords(yard,drop).
affords(kitchen,tap). affords(kitchen,drop).
affords(porch,roll). affords(porch,tap). affords(porch,drop).

use(roll). use(tap). use(drop).

moral(drop).
humor(roll). humor(tap). humor(drop).
misunderstanding(roll). misunderstanding(tap). misunderstanding(drop).

valid(Place,Use) :- affords(Place,Use), use(Use).
good_story(Place,Use) :- valid(Place,Use), humor(Use), misunderstanding(Use).
show good_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
        for u in sorted(SETTINGS[pid].affords):
            lines.append(asp.fact("affords", pid, u))
    for uid in USES:
        lines.append(asp.fact("use", uid))
        if uid == "drop":
            lines.append(asp.fact("moral", uid))
        lines.append(asp.fact("humor", uid))
        lines.append(asp.fact("misunderstanding", uid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in clingo:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


def explain_rejection(place: str, use: str) -> str:
    return f"(No story: {use} does not fit the setting {place} in this small nursery world.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.use and args.use not in SETTINGS[args.place].affords:
        raise StoryError(explain_rejection(args.place, args.use))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.use is None or c[1] == args.use)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, use = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father", "grandma", "grandpa"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, use=use, name=name, gender=gender, helper=helper, trait=trait)


def valid_combos() -> list[tuple[str, str]]:
    return [(place, use) for place, s in SETTINGS.items() for use in s.affords if use in USES]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], USES[params.use], params.name, params.gender, params.helper, params.trait)
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
    StoryParams(place="beach", use="tap", name="Mia", gender="girl", helper="mother", trait="cheery"),
    StoryParams(place="yard", use="roll", name="Leo", gender="boy", helper="father", trait="bouncy"),
    StoryParams(place="kitchen", use="drop", name="Nora", gender="girl", helper="grandma", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible setting/use combos:\n")
        for place, use in combos:
            print(f"  {place:8} {use}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
