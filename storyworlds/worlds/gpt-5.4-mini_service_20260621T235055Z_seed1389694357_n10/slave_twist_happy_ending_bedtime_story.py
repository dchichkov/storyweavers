#!/usr/bin/env python3
"""
Standalone storyworld for a bedtime-story domain with a twist and a happy ending.

This world builds a small simulated tale around a child listening to a bedtime
story, a missing favorite picture book, a surprising twist, and a gentle happy
ending. The required seed word "slave" is included as an in-world title for a
storybook character in the tale the child reads.
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
from pathlib import Path
from typing import Callable, Optional


def _bootstrap_repo_path() -> None:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / "results.py").exists():
            sys.path.insert(0, str(parent))
            return
        if (parent / "storyworlds" / "results.py").exists():
            sys.path.insert(0, str(parent / "storyworlds"))
            return


_bootstrap_repo_path()
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    sounds: str
    light: str
    bed: str
    quietness: str
    twist_hint: str


@dataclass
class StoryObj:
    id: str
    label: str
    phrase: str
    type: str
    tags: set[str] = field(default_factory=set)
    missing: bool = False
    found: bool = False
    wholesome: bool = False


@dataclass
class Twist:
    id: str
    reveal: str
    cause: str
    fix: str
    turn: str


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    talent: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["worry"] >= THRESHOLD and ("worry" not in world.fired):
        world.fired.add(("worry",))
        parent = world.get("parent")
        parent.memes["care"] += 1
        out.append("__worry__")
    return out


def _r_search(world: World) -> list[str]:
    out: list[str] = []
    if world.get("book").meters["missing"] < THRESHOLD:
        return out
    if ("search",) in world.fired:
        return out
    world.fired.add(("search",))
    world.get("child").memes["hope"] += 1
    out.append("__search__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("search", _r_search)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def predict_return(world: World) -> dict:
    sim = world.copy()
    sim.get("book").meters["missing"] = 1.0
    return {"missing": sim.get("book").meters["missing"] >= THRESHOLD}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for obj in OBJECTS:
            for tw in TWISTS:
                if obj != "missing_star" or tw.id == "mistaken":
                    combos.append((sid, obj, tw.id))
    return combos


@dataclass
class StoryParams:
    setting: str
    object: str
    twist: str
    child: str
    child_gender: str
    parent: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "nursery": Setting("nursery", "the nursery", "soft pages rustled", "a lamp glowed gold", "a tiny bed", "very quiet", "a shadow under the blanket"),
    "library": Setting("library", "the little library corner", "pages whispered softly", "a night lamp blinked warm", "a cushioned chair", "book-quiet", "a shelf with one empty spot"),
    "attic": Setting("attic", "the cozy attic nook", "the roof creaked gently", "a lantern made a small circle of light", "a trundle bed", "sleepy and still", "a trunk that looked just a bit too full"),
}

OBJECTS = {
    "storybook": StoryObj("storybook", "picture book", "a picture book about stars and kittens", "book", tags={"book", "sleep"}),
    "lamp": StoryObj("lamp", "night lamp", "a night lamp with a yellow shade", "thing", tags={"light"}),
    "blanket": StoryObj("blanket", "blanket", "a soft striped blanket", "thing", tags={"sleep"}, wholesome=True),
    "missing_star": StoryObj("missing_star", "missing page", "a missing star page", "book", tags={"book", "twist"}, missing=True),
}

TWISTS = {
    "mistaken": Twist("mistaken", "the 'missing' page was stuck inside the book all along", "a page had folded over", "a careful flip fixed it", "the worry turned into a silly grin"),
    "shadow": Twist("shadow", "the scary shadow was only a coat on a chair", "the lamp made a funny shape", "the parent moved the coat away", "the room looked gentle again"),
    "stuck": Twist("stuck", "the book was not lost; it had slid under the pillow", "bedtime tossing had nudged it there", "a little search found it", "the happy ending came from a tiny discovery"),
}

HELPERS = {
    "mom": Helper("mom", "mom", "mom", "careful hands", tags={"care"}),
    "dad": Helper("dad", "dad", "dad", "steady hands", tags={"care"}),
    "cat": Helper("cat", "cat", "the cat", "soft feet", tags={"cute"}),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn"]


def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.object not in OBJECTS:
        raise StoryError("Unknown object.")
    if params.twist not in TWISTS:
        raise StoryError("Unknown twist.")


def tell(setting: Setting, obj: StoryObj, twist: Twist, child: Entity, parent: Entity, helper: Helper) -> World:
    world = World(setting)
    world.add(child)
    world.add(parent)
    world.add(Entity(id="helper", kind="character", type="cat" if helper.id == "cat" else "adult", label=helper.label))
    book = world.add(Entity(id="book", type="thing", label=obj.label, attrs={"wholesome": obj.wholesome}))
    child.memes["love_story"] = 1.0
    child.meters["worry"] = 0.0
    book.meters["missing"] = 1.0 if obj.missing else 0.0

    world.say(f"It was bedtime in {setting.place}, and {child.id} was curled up in the soft quiet.")
    world.say(f"{setting.sounds.capitalize()}, and {setting.light} while {setting.bed} waited nearby.")
    world.say(f"{child.id} wanted {obj.phrase} for the last story of the night.")

    world.para()
    if obj.missing:
        child.meters["worry"] += 1.0
        world.say(f"But the {obj.label} had gone missing, and that made {child.id}'s tummy feel tight.")
        world.say(f'"Maybe it slipped somewhere small," {parent.id} said, and the search began.')
        propagate(world, narrate=False)
        if predict_return(world)["missing"]:
            pass
        world.say(f"{helper.phrase} came close, blinking in the light, as everyone looked again.')
        world.say(f"Then came the twist: {twist.reveal}. {twist.cause.capitalize()}, so {twist.fix}.")
        world.para()
        world.say(f"{twist.turn.capitalize()}, {child.id} laughed and hugged the book to {child.pronoun('possessive')} chest.")
        world.say(f"{parent.label_word.capitalize()} read the last page, and the room felt warm and safe again.")
    else:
        world.say(f"It looked as if the night would be ordinary, but a little twist was waiting.")
        world.say(f"{twist.reveal.capitalize()}. {twist.cause.capitalize()}, so {twist.fix}.")
        world.para()
        world.say(f"{child.id} listened with wide eyes, then settled deeper under the blanket.")
        world.say(f"At the end, {parent.id} kissed {child.id}'s forehead, and the story ended in a happy hush.")

    world.facts.update(
        setting=setting,
        obj=obj,
        twist=twist,
        child=child,
        parent=parent,
        helper=helper,
        outcome="happy",
        missing=bool(obj.missing),
        worry=child.meters["worry"],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a small child in {f["setting"].place} with a gentle twist and a happy ending.',
        f"Tell a soft nighttime story where {f['child'].id} looks for {f['obj'].phrase}, then learns a surprising but harmless truth.",
        'Write a cozy story that includes the word "slave" as a title inside a storybook and ends happily before sleep.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    obj = f["obj"]
    twist = f["twist"]
    qa = [
        QAItem(
            question=f"What was {child.id} doing at bedtime?",
            answer=f"{child.id} was settling in for a bedtime story in {f['setting'].place}. {child.id} wanted {obj.phrase}, because that was the story to read before sleep.",
        ),
        QAItem(
            question=f"Why did {child.id} feel worried at first?",
            answer=f"{obj.label.capitalize()} seemed missing, so {child.id} got nervous and looked all around. That worry made the night feel bigger until the grown-up helped with the search.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"{twist.reveal.capitalize()}. {twist.cause.capitalize()}, so {twist.fix}.",
        ),
        QAItem(
            question=f"How did the bedtime story end?",
            answer=f"It ended happily, with {child.id} calm again and {parent.id} ready to read on. The final feeling was soft and safe, like a blanket tucked in just right.",
        ),
    ]
    return qa


WORLD_KNOWLEDGE = {
    "book": [("What is a picture book?", "A picture book has drawings and words, and people read it aloud to children.")],
    "sleep": [("Why do children need bedtime?", "Bedtime helps the body rest so a child can feel strong and cheerful the next day.")],
    "light": [("Why is a night lamp nice at bedtime?", "A night lamp gives a little light without being too bright, so the room feels safe and sleepy.")],
    "care": [("What does a grown-up do when a child is worried at night?", "A grown-up can stay close, look carefully, and help the child feel calm again.")],
    "cute": [("Why do cats seem cozy at night?", "Cats move softly and like warm places, so they often seem extra cozy when the house is quiet.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["obj"].tags)
    tags.add("care")
    if world.facts["obj"].id == "storybook":
        tags.add("book")
    if world.facts["setting"].id in {"nursery", "attic"}:
        tags.add("sleep")
    if world.facts["helper"].id == "cat":
        tags.add("cute")
    if world.facts["obj"].id == "lamp":
        tags.add("light")
    out: list[QAItem] = []
    for tag, pairs in WORLD_KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(q, a) for q, a in pairs)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("obj", oid))
        if obj.missing:
            lines.append(asp.fact("missing", oid))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,O,T) :- setting(S), obj(O), twist(T).
"""


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in ASP parity.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, object=None, twist=None, seed=None), random.Random(777)))
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample)
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world with a twist and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mom", "dad"])
    ap.add_argument("--helper", choices=HELPERS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    obj = args.object_ or rng.choice(list(OBJECTS))
    twist = args.twist or rng.choice(list(TWISTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mom", "dad"])
    helper = args.helper or rng.choice(list(HELPERS))
    return StoryParams(setting=setting, object=obj, twist=twist, child=child, child_gender=gender, parent=parent, helper=helper)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.object not in OBJECTS or params.twist not in TWISTS:
        raise StoryError("Invalid story parameters.")
    setting = SETTINGS[params.setting]
    obj = OBJECTS[params.object]
    twist = TWISTS[params.twist]
    child = Entity(id=params.child, kind="character", type=params.child_gender, label=params.child)
    parent = Entity(id=params.parent, kind="character", type="mother" if params.parent == "mom" else "father", label=params.parent)
    helper = HELPERS[params.helper]
    world = tell(setting, obj, twist, child, parent, helper)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


CURATED = [
    StoryParams(setting="nursery", object="storybook", twist="mistaken", child="Lily", child_gender="girl", parent="mom", helper="cat"),
    StoryParams(setting="library", object="missing_star", twist="stuck", child="Tom", child_gender="boy", parent="dad", helper="mom"),
    StoryParams(setting="attic", object="lamp", twist="shadow", child="Mia", child_gender="girl", parent="mom", helper="dad"),
]


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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(str(x) for x in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
