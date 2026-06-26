#!/usr/bin/env python3
"""
Standalone storyworld: a small comedy about an accident while serving snacks.

Seed premise:
A child helps serve food or drinks, an accident happens with a funny sound, and
the characters solve the problem together.

The world model tracks physical meters and emotional memes. The generated story
must be driven by the simulated state: who is serving, what slips or spills, what
sound the accident makes, and how the problem gets fixed.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class ServiceItem:
    id: str
    label: str
    phrase: str
    mess: str
    sound: str
    spill_kind: str
    zone: str
    cleanup_tool: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperTool:
    id: str
    label: str
    phrase: str
    fixes: set[str]
    target_zone: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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
            self.trace.append(text)

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


@dataclass
class StoryParams:
    place: str
    item: str
    helper: str
    child_name: str
    child_gender: str
    parent_type: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"serve"}),
    "party_table": Setting(place="the party table", indoor=True, affords={"serve"}),
    "picnic": Setting(place="the picnic blanket", indoor=False, affords={"serve"}),
}

SERVICE_ITEMS = {
    "juice": ServiceItem(
        id="juice",
        label="juice",
        phrase="a tall cup of bright juice",
        mess="sticky",
        sound="sploosh",
        spill_kind="spill",
        zone="table",
        cleanup_tool="towel",
        tags={"drink", "sticky", "sound_effect"},
    ),
    "soup": ServiceItem(
        id="soup",
        label="soup",
        phrase="a warm bowl of soup",
        mess="soup",
        sound="plip",
        spill_kind="splash",
        zone="shirt",
        cleanup_tool="napkin",
        tags={"food", "messy", "sound_effect"},
    ),
    "jelly": ServiceItem(
        id="jelly",
        label="jelly",
        phrase="a wobbly plate of jelly",
        mess="wobbly",
        sound="wibble",
        spill_kind="jiggle",
        zone="table",
        cleanup_tool="spoon",
        tags={"food", "wobbly", "sound_effect"},
    ),
}

HELPERS = {
    "towel": HelperTool(
        id="towel",
        label="a towel",
        phrase="a soft kitchen towel",
        fixes={"sticky", "soup", "wobbly"},
        target_zone="table",
        tags={"clean", "problem_solving"},
    ),
    "napkin": HelperTool(
        id="napkin",
        label="a napkin",
        phrase="a clean napkin",
        fixes={"soup", "sticky"},
        target_zone="shirt",
        tags={"clean", "problem_solving"},
    ),
    "spoon": HelperTool(
        id="spoon",
        label="a spoon",
        phrase="a long spoon",
        fixes={"wobbly"},
        target_zone="plate",
        tags={"problem_solving", "tool"},
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Zoe", "Ivy", "Ella", "Ava"]
BOY_NAMES = ["Leo", "Max", "Ben", "Theo", "Finn", "Owen", "Sam"]
TRAITS = ["cheerful", "curious", "silly", "brave", "bouncy"]


def service_risk(item: ServiceItem, setting: Setting) -> bool:
    return "serve" in setting.affords


def compatible_helper(item: ServiceItem, helper: HelperTool) -> bool:
    return item.mess in helper.fixes


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for item_id, item in SERVICE_ITEMS.items():
            if not service_risk(item, setting):
                continue
            for helper_id, helper in HELPERS.items():
                if compatible_helper(item, helper):
                    out.append((place, item_id, helper_id))
    return out


def _serve(world: World, child: Entity, parent: Entity, item: ServiceItem, helper: HelperTool) -> None:
    world.facts["item"] = item
    world.facts["helper"] = helper
    world.facts["child"] = child
    world.facts["parent"] = parent

    child.memes["helpful"] = child.memes.get("helpful", 0) + 1
    child.memes["pride"] = child.memes.get("pride", 0) + 1
    world.say(f"{child.id} was helping {parent.label_word} serve {item.phrase}.")
    world.say(f"The room felt ready for snacks, and {child.pronoun().capitalize()} tried to be very careful.")

    if item.id == "juice":
        sound_line = f"Then came the {item.sound}! The cup tipped with a tiny {item.sound}-splat."
    elif item.id == "soup":
        sound_line = f"Then came the {item.sound}! The bowl went {item.sound}-plip right onto the rim."
    else:
        sound_line = f"Then came the {item.sound}! The jelly went {item.sound}-wibble and wobbled away."
    world.say(sound_line)

    child.meters[item.mess] = child.meters.get(item.mess, 0) + 1
    child.memes["oops"] = child.memes.get("oops", 0) + 1
    parent.memes["alert"] = parent.memes.get("alert", 0) + 1

    if item.mess == "sticky":
        child.meters["sticky"] = child.meters.get("sticky", 0) + 1
    elif item.mess == "soup":
        child.meters["wet"] = child.meters.get("wet", 0) + 1
    else:
        child.meters["mess"] = child.meters.get("mess", 0) + 1

    world.say(f"{child.id} froze for a second, then {parent.label_word} gave a funny little grin instead of a frown.")


def _problem_solve(world: World, child: Entity, parent: Entity, item: ServiceItem, helper: HelperTool) -> None:
    world.para()
    if item.mess == "sticky":
        action = "wiped the table with the towel"
        fix_line = "Wipe, wipe, wipe!"
    elif item.mess == "soup":
        action = "dabbed the spill with the napkin"
        fix_line = "Dab, dab, dab!"
    else:
        action = "slid the spoon under the wobbly jelly"
        fix_line = "Clink, clink, clink!"
    world.say(f'{parent.label_word} said, "No big deal. We can fix this."')
    world.say(f"{child.id} and {parent.label_word} used {helper.label} and {action}. {fix_line}")
    child.memes["relief"] = child.memes.get("relief", 0) + 1
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    parent.memes["pride"] = parent.memes.get("pride", 0) + 1
    child.meters[item.mess] = 0
    if item.mess == "sticky":
        child.meters["sticky"] = 0
    elif item.mess == "soup":
        child.meters["wet"] = 0
    else:
        child.meters["mess"] = 0
    world.say(f"In the end, the snacks were safe, the floor was fine, and everybody laughed at the tiny accident.")


def tell(setting: Setting, item: ServiceItem, helper: HelperTool,
         child_name: str = "Milo", child_gender: str = "boy",
         parent_type: str = "mother", trait: str = "cheerful") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    tool = world.add(Entity(id=helper.id, type="tool", label=helper.label, phrase=helper.phrase))
    world.facts["setting"] = setting
    world.facts["item"] = item
    world.facts["helper"] = helper
    world.facts["child"] = child
    world.facts["parent"] = parent
    world.facts["trait"] = trait

    world.say(f"{child.id} was a little {trait} {child_gender} who loved to help serve snacks.")
    world.say(f"{child.id} wanted to carry {item.phrase} all by {child.pronoun('object')}self.")
    world.say(f"{parent.label_word} smiled because {child.id} really did try.")

    world.para()
    world.say(f"At {setting.place}, it was finally time to serve.")
    _serve(world, child, parent, item, helper)
    _problem_solve(world, child, parent, item, tool)

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    item = f["item"]
    return [
        f'Write a short comedy story for a young child about an accident while serving {item.label}.',
        f"Tell a gentle story where {child.id} helps {parent.label_word} serve {item.phrase}, something goes {item.spill_kind}, and they solve it together.",
        f'Create a story with a funny sound like "{item.sound}" and a problem-solving ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    item = f["item"]
    helper = f["helper"]
    setting = f["setting"]
    qa = [
        QAItem(
            question=f"What was {child.id} helping {parent.label_word} do?",
            answer=f"{child.id} was helping {parent.label_word} serve {item.phrase} at {setting.place}.",
        ),
        QAItem(
            question=f"What funny sound happened when the accident took place?",
            answer=f"The accident made a funny {item.sound} sound.",
        ),
        QAItem(
            question=f"How did they fix the mess?",
            answer=f"{child.id} and {parent.label_word} used {helper.label} to clean up the mess and make the snack time work again.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    item = f["item"]
    helper = f["helper"]
    items = []
    if item.id == "juice":
        items.append(QAItem(
            question="What is juice usually like?",
            answer="Juice is a drink, so it can spill if a cup tips over.",
        ))
    elif item.id == "soup":
        items.append(QAItem(
            question="What is soup usually like?",
            answer="Soup is warm and liquid, so it can splash if a bowl gets bumped.",
        ))
    else:
        items.append(QAItem(
            question="What is jelly usually like?",
            answer="Jelly is wobbly, so it can jiggle and slide around on a plate.",
        ))
    if helper.id == "towel":
        items.append(QAItem(
            question="What does a towel help with?",
            answer="A towel can wipe up spills and dry a wet place.",
        ))
    elif helper.id == "napkin":
        items.append(QAItem(
            question="What does a napkin help with?",
            answer="A napkin can dab little spills and keep fingers and tables cleaner.",
        ))
    else:
        items.append(QAItem(
            question="What does a spoon help with?",
            answer="A spoon can scoop, stir, and help with wobbly food.",
        ))
    return items


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


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


def valid_helper_story(place: str, item_id: str, helper_id: str) -> bool:
    return (place, item_id, helper_id) in valid_combos()


ASP_RULES = r"""
valid(Place, Item, Helper) :- place(Place), item(Item), helper(Helper),
                              serves(Place, Item), fixes(Helper, Item).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("serves", pid, a))
    for iid, item in SERVICE_ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("mess", iid, item.mess))
        lines.append(asp.fact("sound", iid, item.sound))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for m in sorted(helper.fixes):
            lines.append(asp.fact("fixes", hid, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about an accident while serving snacks.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--item", choices=SERVICE_ITEMS.keys())
    ap.add_argument("--helper", choices=HELPERS.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.item:
        combos = [c for c in combos if c[1] == args.item]
    if args.helper:
        combos = [c for c in combos if c[2] == args.helper]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item, helper = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, item=item, helper=helper, child_name=name, child_gender=gender, parent_type=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], SERVICE_ITEMS[params.item], HELPERS[params.helper],
                 params.child_name, params.child_gender, params.parent_type, params.trait)
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
    StoryParams(place="kitchen", item="juice", helper="towel", child_name="Mia", child_gender="girl", parent_type="mother", trait="cheerful"),
    StoryParams(place="party_table", item="soup", helper="napkin", child_name="Leo", child_gender="boy", parent_type="father", trait="silly"),
    StoryParams(place="picnic", item="jelly", helper="spoon", child_name="Nora", child_gender="girl", parent_type="father", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for place, item, helper in triples:
            print(f"  {place:12} {item:8} {helper:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
            header = f"### {p.child_name}: {p.item} at {p.place} (helper: {p.helper})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
