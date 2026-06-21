#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sift_confuse_flashback_mystery.py
==================================================================

A small standalone mystery storyworld about a child searching carefully,
sorting clues, and remembering a flashback that turns confusion into a clear
answer.

The world keeps typed entities with physical meters and emotional memes, uses a
small forward-chaining model, and includes a Python reasonableness gate plus an
inline ASP twin for parity checks.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
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
    location: str = ""
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


@dataclass
class Setting:
    id: str
    place: str
    dark_spot: str
    mood: str
    search_surface: str


@dataclass
class MysteryTool:
    id: str
    label: str
    phrase: str
    method: str
    helps_flashback: bool = False


@dataclass
class Clue:
    id: str
    label: str
    place: str
    can_hide: bool = True
    reveals: str = ""


@dataclass
class StoryParams:
    setting: str
    tool: str
    clue: str
    seeker: str
    seeker_gender: str
    helper: str
    helper_gender: str
    parent: str = "mother"
    seed: Optional[int] = None


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
        clone.entities = {k: _deep_entity(v) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _deep_entity(e: Entity) -> Entity:
    return Entity(
        id=e.id,
        kind=e.kind,
        type=e.type,
        label=e.label,
        role=e.role,
        location=e.location,
        traits=list(e.traits),
        attrs=dict(e.attrs),
        meters=defaultdict(float, e.meters),
        memes=defaultdict(float, e.memes),
    )


SETTINGS = {
    "attic": Setting("attic", "the old attic", "a dark corner behind boxes", "dusty", "the floorboards"),
    "library": Setting("library", "the quiet library", "the back shelf", "hushed", "the reading table"),
    "cellar": Setting("cellar", "the cellar", "the shelf under the stairs", "echoey", "the stone floor"),
}

TOOLS = {
    "magnifier": MysteryTool("magnifier", "magnifying glass", "a magnifying glass", "sift tiny details", True),
    "lantern": MysteryTool("lantern", "lantern", "a small lantern", "shine gently", False),
    "notebook": MysteryTool("notebook", "notebook", "a notebook and pencil", "list clues", False),
}

CLUES = {
    "button": Clue("button", "missing button", "under a rug", True, "the coat pocket"),
    "note": Clue("note", "folded note", "inside a book", True, "the old desk"),
    "key": Clue("key", "tiny brass key", "under the bed", True, "the music box"),
    "ticket": Clue("ticket", "old ticket stub", "behind a picture frame", True, "the attic trunk"),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Ivy", "Zoe", "Ella"]
BOY_NAMES = ["Owen", "Eli", "Finn", "Theo", "Ben", "Max"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tool_id in TOOLS:
            for clue_id, clue in CLUES.items():
                if setting.place and clue.can_hide:
                    combos.append((sid, tool_id, clue_id))
    return combos


def is_reasonable(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.tool in TOOLS and params.clue in CLUES


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with sift, confuse, and a flashback.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--seeker", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--seeker-gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.tool is None or c[1] == args.tool)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, tool, clue = rng.choice(sorted(combos))
    seeker_gender = args.seeker_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    seeker = args.seeker or _pick_name(rng, seeker_gender)
    helper = args.helper or _pick_name(rng, helper_gender, avoid=seeker)
    return StoryParams(
        setting=setting,
        tool=tool,
        clue=clue,
        seeker=seeker,
        seeker_gender=seeker_gender,
        helper=helper,
        helper_gender=helper_gender,
        parent=args.parent or rng.choice(["mother", "father"]),
    )


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        if world.get("seeker").meters["confused"] >= THRESHOLD and ("confuse",) not in world.fired:
            world.fired.add(("confuse",))
            world.get("seeker").memes["confusion"] += 1
            changed = True
        if world.get("clue").meters["found"] >= THRESHOLD and ("found",) not in world.fired:
            world.fired.add(("found",))
            world.get("helper").memes["hope"] += 1
            changed = True


def flashback(world: World, seeker: Entity, clue: Clue, setting: Setting) -> None:
    seeker.memes["memory"] += 1
    world.say(
        f"Then came a flashback. {seeker.id} remembered seeing {clue.label} near "
        f"{clue.reveals} in {setting.place}."
    )


def tell(setting: Setting, tool: MysteryTool, clue: Clue, seeker: Entity, helper: Entity, parent: Entity) -> World:
    world = World()
    world.add(seeker)
    world.add(helper)
    world.add(parent)
    world.add(Entity(id="setting", type="room", label=setting.place))
    world.add(Entity(id="tool", type="thing", label=tool.label))
    world.add(Entity(id="clue", type="thing", label=clue.label))

    seeker.meters["searching"] += 1
    helper.meters["sifting"] += 1

    world.say(
        f"On a quiet afternoon, {seeker.id} and {helper.id} were in {setting.place}, "
        f"where the air felt {setting.mood}. {seeker.id} wanted to solve a little mystery."
    )
    world.say(
        f"They found a problem: a {clue.label} was missing, and nobody knew where it had gone. "
        f"{helper.id} raised {helper.pronoun('possessive')} {tool.label} and said they should {tool.method}."
    )

    world.para()
    seeker.meters["confused"] += 1
    seeker.memes["worry"] += 1
    world.say(
        f"At first, the clues seemed to confuse {seeker.id}. The room looked the same "
        f"everywhere, and even the quiet corners gave no answer."
    )
    world.say(
        f"So {helper.id} began to sift through the little things on the floor and the shelf, "
        f"one by one, without rushing."
    )

    clue_entity = world.get("clue")
    clue_entity.meters["found"] += 1
    world.say(
        f"Under the soft dust, they finally spotted the {clue.label}. It was hiding {clue.place}, "
        f"small enough to miss if someone only glanced once."
    )

    world.para()
    flashback(world, seeker, clue, setting)
    world.say(
        f"The memory made everything fit. {seeker.id} remembered that the {clue.label} had "
        f"slipped from an old pocket and landed where it would be easy to overlook."
    )
    world.say(
        f"{helper.id} smiled, and the mystery stopped feeling confusing. Together they picked up "
        f"the {clue.label} and brought it back to {parent.label_word}."
    )
    world.say(
        f"By the end, the room was calm again, the clue was safe in hand, and {seeker.id} knew "
        f"that careful looking could solve even a puzzling day."
    )

    world.facts.update(
        setting=setting,
        tool=tool,
        clue=clue,
        seeker=seeker,
        helper=helper,
        parent=parent,
        outcome="solved",
    )
    propagate(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a young child that includes the words "sift" and "confuse".',
        f"Tell a gentle mystery in {f['setting'].place} where {f['seeker'].id} and {f['helper'].id} search carefully, remember a flashback, and solve a missing {f['clue'].label}.",
        f"Write a story with a flashback that helps explain a clue and turns confusion into a clear answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    seeker = f["seeker"]
    helper = f["helper"]
    clue = f["clue"]
    setting = f["setting"]
    parent = f["parent"]
    return [
        QAItem(
            question="What kind of story is this?",
            answer="It is a small mystery story. The characters are trying to solve a missing clue by looking carefully and remembering an important flashback.",
        ),
        QAItem(
            question=f"Why did {seeker.id} feel confused at first?",
            answer=(
                f"{seeker.id} felt confused because the room gave no clear answer and the missing {clue.label} was hard to spot. "
                f"That confusion made the careful search feel slow until the clue finally appeared."
            ),
        ),
        QAItem(
            question=f"What did the flashback help {seeker.id} remember?",
            answer=(
                f"The flashback helped {seeker.id} remember seeing the {clue.label} near {clue.reveals} in {setting.place}. "
                f"That memory made the hidden clue make sense."
            ),
        ),
        QAItem(
            question=f"How did {helper.id} help solve the mystery?",
            answer=(
                f"{helper.id} helped by using {helper.pronoun('possessive')} {f['tool'].label} to sift through the room one little piece at a time. "
                f"That careful method gave {seeker.id} time to remember the clue."
            ),
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=(
                f"At the end, {seeker.id} and {helper.id} found the missing {clue.label} and brought it back to {parent.label_word}. "
                f"The mystery was solved, and the room felt calm again."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to sift through things?",
            answer="To sift means to look through things carefully, little by little, until you find what you need.",
        ),
        QAItem(
            question="What does confuse mean?",
            answer="To confuse someone means to make them unsure or mixed up so they do not know the answer right away.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a memory scene that shows something from before. It helps explain what is happening now.",
        ),
        QAItem(
            question="Why do mysteries use clues?",
            answer="Mysteries use clues because clues are little pieces of information that help solve the problem.",
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
found(clue) :- clue_entity(clue), clue_known(clue).
confused(seeker) :- seeker_entity(seeker), needs_search(seeker).
solved :- found(clue), flashback_used.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as err:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    return rc


def explain_rejection() -> str:
    return "(No story: that combination doesn't make a sensible mystery.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.tool is None or c[1] == args.tool)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, tool, clue = rng.choice(sorted(combos))
    seeker_gender = args.seeker_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    seeker = args.seeker or _pick_name(rng, seeker_gender)
    helper = args.helper or _pick_name(rng, helper_gender, avoid=seeker)
    return StoryParams(
        setting=setting,
        tool=tool,
        clue=clue,
        seeker=seeker,
        seeker_gender=seeker_gender,
        helper=helper,
        helper_gender=helper_gender,
        parent=args.parent or rng.choice(["mother", "father"]),
    )


def generate(params: StoryParams) -> StorySample:
    if not is_reasonable(params):
        raise StoryError("(Invalid parameters for this mystery world.)")
    seeker = Entity(id=params.seeker, kind="character", type=params.seeker_gender, role="seeker")
    helper = Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper")
    parent = Entity(id="Parent", kind="character", type=params.parent, role="parent", label="the parent")
    world = tell(SETTINGS[params.setting], TOOLS[params.tool], CLUES[params.clue], seeker, helper, parent)
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


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(setting="attic", tool="magnifier", clue="key", seeker="Lina", seeker_gender="girl", helper="Owen", helper_gender="boy", parent="mother"),
        StoryParams(setting="library", tool="notebook", clue="note", seeker="Maya", seeker_gender="girl", helper="Finn", helper_gender="boy", parent="father"),
        StoryParams(setting="cellar", tool="lantern", clue="ticket", seeker="Eli", seeker_gender="boy", helper="Nora", helper_gender="girl", parent="mother"),
    ]


CURATED = build_curated()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible (setting, tool, clue) combos:")
        for c in valid_combos():
            print("  ", c)
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
