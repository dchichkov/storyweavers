#!/usr/bin/env python3
"""
storyworlds/worlds/antique_problem_solving_sharing_heartwarming.py
===================================================================

A small heartwarming storyworld about an antique heirloom, a gentle problem,
and a shared solution.

The seed image is simple:
a child and a caring older relative discover an antique object that needs a
patient fix. They share the work, solve the problem together, and end with a
warm image that proves the object is safe and loved again.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "child":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"grandma", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"grandpa", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class SettingSpec:
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class ToolSpec:
    id: str
    label: str
    phrase: str


@dataclass
class AntiqueSpec:
    id: str
    label: str
    phrase: str
    problem_noun: str
    problem_meter: str
    tool_id: str
    repair_sentence: str
    ending_sentence: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: SettingSpec) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def held_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.held_by == actor.id]

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS: dict[str, SettingSpec] = {
    "attic": SettingSpec(
        place="the attic",
        detail="Dusty trunks lined the wall, and a small window let in a shy square of light.",
        affords={"quilt", "music_box"},
    ),
    "parlor": SettingSpec(
        place="the parlor",
        detail="A lamp glowed on the side table, and the rug felt soft under careful feet.",
        affords={"quilt", "music_box", "frame"},
    ),
    "sunroom": SettingSpec(
        place="the sunroom",
        detail="Sunlight fell in bright squares across the floor, and the whole room felt calm.",
        affords={"quilt", "music_box", "frame"},
    ),
}

TOOL_SPECS: dict[str, ToolSpec] = {
    "thread": ToolSpec(
        id="thread",
        label="needle and thread",
        phrase="a little basket of needle and thread",
    ),
    "cloth": ToolSpec(
        id="cloth",
        label="soft cloth",
        phrase="a soft cloth",
    ),
    "keycloth": ToolSpec(
        id="keycloth",
        label="soft cloth and winding key",
        phrase="a soft cloth and a tiny winding key",
    ),
}

ANTIQUE_SPECS: dict[str, AntiqueSpec] = {
    "quilt": AntiqueSpec(
        id="quilt",
        label="quilt",
        phrase="an antique patchwork quilt",
        problem_noun="loose seam",
        problem_meter="tear",
        tool_id="thread",
        repair_sentence="They stitched the loose seam with tiny, careful loops.",
        ending_sentence="Soon the quilt was smooth again, and it spread warm across both laps.",
        tags={"antique", "quilt", "mend", "sharing"},
    ),
    "music_box": AntiqueSpec(
        id="music_box",
        label="music box",
        phrase="an antique music box",
        problem_noun="stuck key",
        problem_meter="stuck",
        tool_id="keycloth",
        repair_sentence="They wiped the dusty gears and turned the key very slowly.",
        ending_sentence="Soon the music box chimed a tiny tune through the room.",
        tags={"antique", "music_box", "dust", "sharing", "music"},
    ),
    "frame": AntiqueSpec(
        id="frame",
        label="picture frame",
        phrase="an antique picture frame",
        problem_noun="dusty glass",
        problem_meter="dust",
        tool_id="cloth",
        repair_sentence="They polished the glass and straightened the little photo inside.",
        ending_sentence="Soon the old picture shone by the lamp like a tiny window.",
        tags={"antique", "frame", "dust", "sharing", "picture"},
    ),
}

HELPERS: dict[str, str] = {
    "grandma": "Grandma",
    "grandpa": "Grandpa",
}

CHILD_NAMES = [
    "Ari",
    "Maya",
    "Theo",
    "Iris",
    "Nora",
    "Jude",
    "Lena",
    "Owen",
    "Mila",
    "Ezra",
]

TRAITS = ["gentle", "curious", "careful", "patient", "helpful", "bright"]


@dataclass
class StoryParams:
    setting: str
    item: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


def select_tool(item: AntiqueSpec) -> Optional[ToolSpec]:
    return TOOL_SPECS.get(item.tool_id)


def item_in_risk(setting: SettingSpec, item: AntiqueSpec) -> bool:
    return item.id in setting.affords and select_tool(item) is not None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for item_id, item in ANTIQUE_SPECS.items():
            if item_in_risk(setting, item):
                combos.append((setting_id, item_id))
    return combos


def explain_rejection(setting: SettingSpec, item: AntiqueSpec) -> str:
    allowed = ", ".join(sorted(setting.affords))
    return (
        f"(No story: {setting.place} does not fit {item.phrase}. "
        f"That setting works for: {allowed}. Choose a matching place and object.)"
    )


def setting_narration(setting: SettingSpec) -> str:
    return setting.detail


def item_intro(item: AntiqueSpec, child: Entity, helper: Entity) -> str:
    return f"{child.label_word} and {helper.label_word} found {item.phrase}."


def item_problem_sentence(item: AntiqueSpec) -> str:
    if item.id == "quilt":
        return "One seam had come loose, so the quilt sagged a little in the middle."
    if item.id == "music_box":
        return "The little key felt stuck, so the music box would not sing yet."
    if item.id == "frame":
        return "The glass looked dusty, so the old picture was hard to see clearly."
    return f"{item.phrase} had a small problem."


def share_sentence(item: AntiqueSpec, tool: ToolSpec, child: Entity, helper: Entity) -> str:
    if item.id == "quilt":
        return (
            f"{helper.label_word} shared {tool.phrase} with {child.label_word}, "
            f"and {child.label_word} shared the work by holding the cloth flat."
        )
    if item.id == "music_box":
        return (
            f"{helper.label_word} shared {tool.phrase} with {child.label_word}, "
            f"and {child.label_word} shared a patient smile back."
        )
    if item.id == "frame":
        return (
            f"{helper.label_word} shared {tool.phrase} with {child.label_word}, "
            f"and {child.label_word} shared the careful job of wiping every corner."
        )
    return f"{helper.label_word} shared {tool.phrase} with {child.label_word}."


def ending_sentence(item: AntiqueSpec, child: Entity, helper: Entity) -> str:
    if item.id == "quilt":
        return (
            f"{item.ending_sentence} {child.label_word} and {helper.label_word} "
            f"shared a cozy little smile over it."
        )
    if item.id == "music_box":
        return (
            f"{item.ending_sentence} {child.label_word} and {helper.label_word} "
            f"shared the tune like a small gift."
        )
    if item.id == "frame":
        return (
            f"{item.ending_sentence} {child.label_word} and {helper.label_word} "
            f"shared a quiet look at the picture."
        )
    return item.ending_sentence


def predict_fix(world: World, item: AntiqueSpec) -> bool:
    sim = world.copy()
    sim_item = sim.get(item.id)
    tool = select_tool(item)
    if tool is None:
        return False
    return item_in_risk(sim.setting, item) and sim_item.meters.get(item.problem_meter, 0.0) >= THRESHOLD


def setup_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    item = ANTIQUE_SPECS[params.item]
    world = World(setting)

    child = world.add(Entity(
        id="child",
        kind="character",
        type="child",
        label=params.name,
        traits=[params.trait, "gentle"],
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper,
        label=HELPERS[params.helper],
        traits=["kind", "patient"],
    ))
    antique = world.add(Entity(
        id=item.id,
        kind="artifact",
        type=item.id,
        label=item.label,
        phrase=item.phrase,
        owner=helper.id,
        meters={item.problem_meter: 1.0, "fixed": 0.0},
        memes={"cherished": 1.0},
    ))
    tool = select_tool(item)
    if tool is None:
        raise StoryError(f"(No story: there is no sensible tool for {item.phrase}.)")
    world.add(Entity(
        id=tool.id,
        kind="tool",
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        owner=helper.id,
        held_by=helper.id,
    ))

    world.facts.update(
        child=child,
        helper=helper,
        item=antique,
        tool=tool,
        setting=setting,
        item_spec=item,
    )
    return world


def tell(setting: SettingSpec, item: AntiqueSpec, child_name: str, helper_role: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(
        id="child",
        kind="character",
        type="child",
        label=child_name,
        traits=[trait, "gentle"],
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_role,
        label=HELPERS[helper_role],
        traits=["kind", "patient"],
    ))
    antique = world.add(Entity(
        id=item.id,
        kind="artifact",
        type=item.id,
        label=item.label,
        phrase=item.phrase,
        owner=helper.id,
        meters={item.problem_meter: 1.0, "fixed": 0.0},
        memes={"cherished": 1.0},
    ))
    tool = select_tool(item)
    if tool is None:
        raise StoryError(f"(No story: there is no sensible tool for {item.phrase}.)")
    tool_entity = world.add(Entity(
        id=tool.id,
        kind="tool",
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        owner=helper.id,
        held_by=helper.id,
    ))

    # Act 1: introduce the cozy place and the antique thing.
    world.say(f"{child.label_word} and {helper.label_word} were in {setting.place}.")
    world.say(setting_narration(setting))
    world.say(item_intro(item, child, helper))
    world.say(item_problem_sentence(item))

    # Act 2: the worry and the shared idea.
    world.para()
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1.0
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1.0
    helper.memes["patience"] = helper.memes.get("patience", 0.0) + 1.0
    world.say(
        f"{child.label_word} wanted to touch the old treasure right away, "
        f"but {helper.label_word} noticed the problem first."
    )
    if item.id == "quilt":
        world.say(
            f"{helper.label_word} smiled and said they could fix it together "
            f"if they took their time."
        )
    elif item.id == "music_box":
        world.say(
            f"{helper.label_word} whispered that a little dust could stop a tiny song, "
            f"but gentle hands could wake it up again."
        )
    elif item.id == "frame":
        world.say(
            f"{helper.label_word} said the picture only needed careful hands and a soft cloth."
        )
    else:
        world.say(f"{helper.label_word} said they would solve it together.")
    world.say(share_sentence(item, tool_entity, child, helper))

    # Act 3: the repair and the warm finish.
    world.para()
    if predict_fix(world, item):
        item_entity = world.get(item.id)
        item_entity.meters[item.problem_meter] = 0.0
        item_entity.meters["fixed"] = 1.0
        item_entity.memes["cherished"] = item_entity.memes.get("cherished", 0.0) + 1.0
        child.memes["sharing"] = child.memes.get("sharing", 0.0) + 1.0
        helper.memes["sharing"] = helper.memes.get("sharing", 0.0) + 1.0
        child.memes["joy"] = child.memes.get("joy", 0.0) + 1.0
        helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1.0
        tool_entity.held_by = child.id
        world.say(item.repair_sentence)
        world.say(ending_sentence(item, child, helper))
    else:
        raise StoryError(f"(No story: the antique {item.label} cannot be fixed in a believable way here.)")

    world.facts.update(
        child=child,
        helper=helper,
        item=world.get(item.id),
        tool=tool_entity,
        setting=setting,
        item_spec=item,
        solved=True,
        shared=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    item: Entity = f["item"]
    setting: SettingSpec = f["setting"]
    return [
        f'Write a short heartwarming story for a young child about an antique {item.label} in {setting.place}.',
        f"Tell a gentle story where {child.label_word} and {helper.label_word} solve a small problem together and share the work.",
        f'Write a simple story that includes the word "antique" and ends with {item.label} being safe, fixed, and loved again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    item: Entity = f["item"]
    spec: AntiqueSpec = f["item_spec"]
    setting: SettingSpec = f["setting"]
    tool: ToolSpec = f["tool"]

    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=(
                f"The story was about {child.label_word} and {helper.label_word}, "
                f"who found {spec.phrase} in {setting.place}."
            ),
        ),
        QAItem(
            question=f"What problem did {spec.label} have?",
            answer=(
                f"{spec.label_word if hasattr(spec, 'label_word') else spec.label.capitalize()} had {spec.problem_noun}, "
                f"so it needed a careful fix before it could be enjoyed again."
            ),
        ),
        QAItem(
            question=f"What did {helper.label_word} share with {child.label_word}?",
            answer=(
                f"{helper.label_word} shared {tool.phrase} with {child.label_word}, "
                f"and that let them solve the problem together."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"It ended with the antique {item.label} fixed and loved again, "
                f"so {child.label_word} and {helper.label_word} could enjoy it together."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    item_spec: AntiqueSpec = f["item_spec"]
    tags = set(item_spec.tags)
    tags.add("antique")
    tags.add("sharing")

    knowledge = {
        "antique": [
            (
                "What does antique mean?",
                "Antique means very old, and often special enough that people keep it carefully instead of throwing it away.",
            )
        ],
        "sharing": [
            (
                "What does it mean to share?",
                "To share means to let someone else use something or enjoy it with you.",
            )
        ],
        "quilt": [
            (
                "What is a quilt?",
                "A quilt is a blanket made from many pieces of cloth sewn together, often to keep someone warm.",
            )
        ],
        "music_box": [
            (
                "What is a music box?",
                "A music box is a little box that can play a tune when it is wound up and working properly.",
            )
        ],
        "frame": [
            (
                "What is a picture frame?",
                "A picture frame holds a photo or drawing and helps protect it while it is on display.",
            )
        ],
        "dust": [
            (
                "Why do people dust old things?",
                "People dust old things to keep them clean so they can be seen and used more carefully.",
            )
        ],
        "mend": [
            (
                "What does it mean to mend something?",
                "To mend something means to fix it carefully when it has a tear, crack, or other small problem.",
            )
        ],
        "music": [
            (
                "Why is gentle care important for a music box?",
                "A music box has tiny parts inside, so gentle care helps it keep working and playing its tune.",
            )
        ],
        "picture": [
            (
                "Why do families keep old pictures?",
                "Families keep old pictures because they help remember happy times and people they love.",
            )
        ],
    }

    out: list[QAItem] = []
    for key in ["antique", "sharing", "quilt", "music_box", "frame", "dust", "mend", "music", "picture"]:
        if key in tags and key in knowledge:
            out.extend(QAItem(question=q, answer=a) for q, a in knowledge[key])
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
affords_item(Setting, Item) :- affords(Setting, Item).
has_real_fix(Item) :- needs(Item, Problem), fix(Item, Tool), works(Tool, Problem).
valid(Setting, Item) :- affords_item(Setting, Item), has_real_fix(Item).
valid_story(Setting, Item) :- valid(Setting, Item).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for item_id in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, item_id))
    for item_id, item in ANTIQUE_SPECS.items():
        tool = select_tool(item)
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("needs", item_id, item.problem_noun))
        if tool is not None:
            lines.append(asp.fact("fix", item_id, tool.id))
            lines.append(asp.fact("works", tool.id, item.problem_noun))
            lines.append(asp.fact("tool", tool.id))
    for helper_id in HELPERS:
        lines.append(asp.fact("helper", helper_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if clingo_set != python_set:
        print("MISMATCH between clingo and Python valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        return 1

    print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")

    # Exercise the generator too.
    rng = random.Random(777)
    for setting_id, item_id in sorted(python_set):
        params = StoryParams(
            setting=setting_id,
            item=item_id,
            name=rng.choice(CHILD_NAMES),
            helper=rng.choice(sorted(HELPERS)),
            trait=rng.choice(TRAITS),
            seed=777,
        )
        sample = generate(params)
        if not sample.story.strip():
            print(f"Generator produced an empty story for {setting_id}/{item_id}.")
            return 1
        if "____" in sample.story:
            print(f"Generator leaked a template field for {setting_id}/{item_id}.")
            return 1

    print("OK: generator produced a complete story for every valid setting/item combo.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description=(
            "A heartwarming story world about an antique heirloom, a small problem, "
            "and a shared fix."
        )
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ANTIQUE_SPECS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
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
    if args.setting and args.item:
        setting = SETTINGS[args.setting]
        item = ANTIQUE_SPECS[args.item]
        if not item_in_risk(setting, item):
            raise StoryError(explain_rejection(setting, item))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, item_id = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    name = args.name or rng.choice(CHILD_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        item=item_id,
        name=name,
        helper=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        ANTIQUE_SPECS[params.item],
        params.name,
        params.helper,
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


CURATED = [
    StoryParams(setting="attic", item="quilt", name="Ari", helper="grandma", trait="gentle"),
    StoryParams(setting="parlor", item="music_box", name="Maya", helper="grandpa", trait="curious"),
    StoryParams(setting="sunroom", item="frame", name="Theo", helper="grandma", trait="patient"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, item) combos:\n")
        for setting_id, item_id in combos:
            print(f"  {setting_id:8} {item_id}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.item} in {p.setting} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
