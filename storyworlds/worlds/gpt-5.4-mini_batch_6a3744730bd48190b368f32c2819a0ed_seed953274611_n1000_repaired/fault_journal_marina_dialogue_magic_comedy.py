#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fault_journal_marina_dialogue_magic_comedy.py
=============================================================================

A tiny storyworld set at a marina where a child, a mysterious fault, and a
magic journal create a comic dialogue chain. The world is built to tell one
small complete story: a whimsical setup, a mistaken magical problem, a talky
middle, and a cheerful ending that proves the change.

Seed words: fault, journal
Setting: marina
Features: Dialogue, Magic
Style: Comedy
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)

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
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Marina:
    name: str
    place_line: str
    comic_detail: str
    water_bit: str
    dock_bit: str
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Fault:
    id: str
    label: str
    symptom: str
    comic_sound: str
    makes_magic: bool = True
    dangerous: bool = False
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
class Journal:
    id: str
    label: str
    cover: str
    page_glow: str
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
class MagicResponse:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
    marina: str
    fault: str
    journal: str
    response: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    parent_name: str
    parent_gender: str
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
        self.fired: set[str] = set()
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


MARINAS = {
    "marina": Marina(
        name="marina",
        place_line="The marina was bright with bobbing boats, clinking ropes, and a gull that sounded suspiciously proud of itself.",
        comic_detail="Every rope seemed to creak a joke into the wind.",
        water_bit="The water winked under the docks.",
        dock_bit="The wooden dock was a little wobbly, like it had eaten too much pie.",
    )
}

FAULTS = {
    "snag": Fault(
        id="snag",
        label="snag",
        symptom="a tiny snag in the magic map lines",
        comic_sound="fwip-floop",
        makes_magic=True,
        dangerous=False,
        tags={"fault", "magic"},
    ),
    "wink": Fault(
        id="wink",
        label="wobble fault",
        symptom="a wobble that made every page blink twice",
        comic_sound="boing",
        makes_magic=True,
        dangerous=False,
        tags={"fault", "magic"},
    ),
}

JOURNALS = {
    "spark": Journal(
        id="spark",
        label="journal",
        cover="a blue journal with a brass clasp",
        page_glow="glowed whenever someone told the truth",
        tags={"journal"},
    ),
    "tide": Journal(
        id="tide",
        label="journal",
        cover="a green journal with a shell on the front",
        page_glow="sparkled like a tide pool at noon",
        tags={"journal"},
    ),
}

RESPONSES = {
    "laugh_fix": MagicResponse(
        id="laugh_fix",
        sense=3,
        power=3,
        text="snapped the journal shut, tapped it twice, and told the fault to behave. The pages gave a shy little twinkle, and the snag curled itself into a neat knot",
        fail="snapped the journal shut too hard, and the fault only got fancier",
        qa_text="snapped the journal shut and tapped it twice until the fault curled into a neat knot",
        tags={"magic"},
    ),
    "ink_patch": MagicResponse(
        id="ink_patch",
        sense=2,
        power=2,
        text="drew a silly ink circle around the fault and asked the journal to hold still. The page glow sneezed once, then settled down",
        fail="drew a silly ink circle, but the fault giggled right through it",
        qa_text="drew a silly ink circle around the fault and calmed it with the journal",
        tags={"magic"},
    ),
}

GIRL_NAMES = ["Mina", "Rosa", "Pia", "Luna", "Nina", "Tia"]
BOY_NAMES = ["Owen", "Finn", "Leo", "Milo", "Theo", "Ben"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for marina in MARINAS:
        for fault in FAULTS:
            for journal in JOURNALS:
                combos.append((marina, fault, journal))
    return combos


def hazard_ok(fault: Fault, journal: Journal) -> bool:
    return fault.makes_magic and "journal" in journal.tags


def sensible_responses() -> list[MagicResponse]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def magic_pressure(response: MagicResponse) -> int:
    return response.power


def can_settle(response: MagicResponse, fault: Fault) -> bool:
    return magic_pressure(response) >= 2 and fault.makes_magic


def would_befuddle(fault: Fault, journal: Journal) -> bool:
    return hazard_ok(fault, journal)


def story_setup(world: World, child: Entity, helper: Entity, marina: Marina) -> None:
    child.memes["curiosity"] = 1
    helper.memes["wit"] = 1
    world.say(
        f"At the marina, {child.id} and {helper.id} wandered past the docks. {marina.place_line} {marina.comic_detail}"
    )


def need_journal(world: World, child: Entity, journal: Journal) -> None:
    world.say(
        f'{child.id} held up {journal.cover}. "{journal.label_word.capitalize() if hasattr(journal, "label_word") else "This journal"} {journal.page_glow}, but one page had a fault," {child.pronoun()} said.'
    )


def tempt_and_warn(world: World, child: Entity, helper: Entity, fault: Fault, journal: Journal) -> None:
    child.memes["mischief"] = 1
    helper.memes["concern"] = 1
    world.say(
        f'"I can fix it with a pirate grin," {child.id} said. "{fault.comic_sound}! The fault is only a {fault.label}."'
    )
    world.say(
        f'"A fault is still a fault," {helper.id} said, peeking at the {journal.label}. "If magic misbehaves, we use gentler magic."'
    )


def resolve_fault(world: World, child: Entity, helper: Entity, fault: Fault, journal: Journal, response: MagicResponse) -> None:
    child.memes["relief"] = 1
    helper.memes["relief"] = 1
    world.say(
        f'{helper.id} reached over, and together they {response.text}.'
    )
    world.say(
        f"The page glow settled into a happy blink, and the fault stopped wobbling."
    )


def celebrate(world: World, child: Entity, helper: Entity, journal: Journal, marina: Marina) -> None:
    child.memes["joy"] = 1
    helper.memes["joy"] = 1
    world.say(
        f'"There," {child.id} said. "{journal.label.capitalize()} saved the day!"'
    )
    world.say(
        f'"And no boats were offended," {helper.id} added. {marina.water_bit} {marina.dock_bit}'
    )
    world.say(
        f"Then they wrote the whole silly episode in the {journal.label}, right under the line that said: next time, check the fault before you puff your cheeks."
    )


def tell(marina: Marina, fault: Fault, journal: Journal, response: MagicResponse,
         child_name: str = "Mina", child_gender: str = "girl",
         helper_name: str = "Owen", helper_gender: str = "boy",
         parent_name: str = "Aunt June", parent_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent"))
    journal_ent = world.add(Entity(id="journal", type="thing", label="journal", tags={"journal"}))
    fault_ent = world.add(Entity(id="fault", type="thing", label=fault.label, tags={"fault", "magic"}))

    story_setup(world, child, helper, marina)
    world.para()
    need_journal(world, child, journal)
    tempt_and_warn(world, child, helper, fault, journal)
    world.para()
    if would_befuddle(fault, journal):
        resolve_fault(world, child, helper, fault, journal, response)
        celebrate(world, child, helper, journal, marina)
    world.facts.update(
        child=child, helper=helper, parent=parent, journal=journal_ent, fault=fault_ent,
        marina=marina, response=response, outcome="fixed" if would_befuddle(fault, journal) else "none",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a comedic magical story set at a marina that includes the words "fault" and "journal".',
        f"Tell a funny dialogue story where {f['child'].id} finds a fault in a magic journal at the marina and fixes it with help.",
        f'Write a small comedy about a journal, a fault, and a magical problem by the docks.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, journal, fault, marina = f["child"], f["helper"], f["journal"], f["fault"], f["marina"]
    return [
        ("Where is the story set?",
         f"It is set at the {marina.name}. The docks, boats, and gulls all help make the scene feel busy and funny."),
        ("What was the problem?",
         f"There was a fault in the journal's magic. It made the page wobble and needed careful, silly fixing."),
        ("How did the children fix it?",
         f"They used kinder magic and a calm plan. The fault curled into a neat knot, so the journal could work again."),
        ("How did the story end?",
         f"It ended with a joke and a note in the journal. The children laughed, and the marina stayed happily ordinary."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a marina?",
         "A marina is a place where boats are kept near the water. People walk on docks there, and ropes and sails are common sights."),
        ("What is a journal?",
         "A journal is a book where someone can write thoughts, notes, or stories. In magic stories, a journal can be special too."),
        ("Why can magic be funny in a story?",
         "Magic can be funny when it does surprising things, like wobbling, glowing, or sneezing. That makes the scene playful instead of serious."),
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
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        marina="marina", fault="snag", journal="spark", response="laugh_fix",
        child_name="Mina", child_gender="girl", helper_name="Owen", helper_gender="boy",
        parent_name="Aunt June", parent_gender="woman",
    ),
    StoryParams(
        marina="marina", fault="wink", journal="tide", response="ink_patch",
        child_name="Leo", child_gender="boy", helper_name="Rosa", helper_gender="girl",
        parent_name="Uncle Ray", parent_gender="man",
    ),
]


def explain_rejection(fault: Fault, journal: Journal) -> str:
    if not hazard_ok(fault, journal):
        return "(No story: this fault and journal combo does not make a lively magic problem.)"
    return "(No story: the combination is too thin for a comic magic scene.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comic marina storyworld with a faulty magic journal.")
    ap.add_argument("--marina", choices=MARINAS)
    ap.add_argument("--fault", choices=FAULTS)
    ap.add_argument("--journal", choices=JOURNALS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    if args.fault and args.journal:
        if not hazard_ok(FAULTS[args.fault], JOURNALS[args.journal]):
            raise StoryError(explain_rejection(FAULTS[args.fault], JOURNALS[args.journal]))
    combos = [c for c in valid_combos()
              if (args.marina is None or c[0] == args.marina)
              and (args.fault is None or c[1] == args.fault)
              and (args.journal is None or c[2] == args.journal)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    marina, fault, journal = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(s.id for s in sensible_responses()))
    child_name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    child_gender = "girl" if child_name in GIRL_NAMES else "boy"
    helper_name = args.helper or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != child_name])
    helper_gender = "girl" if helper_name in GIRL_NAMES else "boy"
    parent_name = "Captain Maris"
    parent_gender = "woman"
    return StoryParams(
        marina=marina, fault=fault, journal=journal, response=response,
        child_name=child_name, child_gender=child_gender,
        helper_name=helper_name, helper_gender=helper_gender,
        parent_name=parent_name, parent_gender=parent_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.marina not in MARINAS or params.fault not in FAULTS or params.journal not in JOURNALS or params.response not in RESPONSES:
        raise StoryError("Invalid story parameters.")
    world = tell(MARINAS[params.marina], FAULTS[params.fault], JOURNALS[params.journal], RESPONSES[params.response],
                 params.child_name, params.child_gender, params.helper_name, params.helper_gender,
                 params.parent_name, params.parent_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


ASP_RULES = r"""
valid(M,F,J) :- marina(M), fault(F), journal(J), makes_magic(F).
outcome(fixed) :- valid(M,F,J), journal(J).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for m in MARINAS:
        lines.append(asp.fact("marina", m))
    for f in FAULTS.values():
        lines.append(asp.fact("fault", f.id))
        if f.makes_magic:
            lines.append(asp.fact("makes_magic", f.id))
    for j in JOURNALS.values():
        lines.append(asp.fact("journal", j.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = set(valid_combos())
    rc = 0
    if clingo_set != python_set:
        rc = 1
        print("MISMATCH in valid combos")
    try:
        _ = generate(CURATED[0])
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print("OK: verify passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        for v in vals:
            print(v)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            samples.append(generate(p))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
