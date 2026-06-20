#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/antihistamine_cloak_airport_rhyme_reconciliation_suspense_fairy.py
===================================================================================================

A standalone storyworld for a tiny fairy-tale airport tale: a child in a cloak
gets an itchy sneezy problem, a sensible adult reaches for antihistamine, a
stolen cloak creates suspense, and the family reconciles before the flight.

The world is built from state, not frozen prose:
- characters have meters and memes,
- the airport has a small set of locations,
- a suspense turn can delay the rescue,
- rhyme is used in child-facing dialogue,
- reconciliation changes the ending image.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/antihistamine_cloak_airport_rhyme_reconciliation_suspense_fairy.py
    python storyworlds/worlds/gpt-5.4-mini/antihistamine_cloak_airport_rhyme_reconciliation_suspense_fairy.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/antihistamine_cloak_airport_rhyme_reconciliation_suspense_fairy.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2

KID_NAMES = ["Mira", "Luna", "Nina", "Ivy", "Pip", "Theo", "Bram", "Owen", "Milo", "Ada"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    rhyme_seed: str
    suspense_spot: str
    safe_spot: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Remedy:
    id: str
    label: str
    sense: int
    power: int
    phrase: str
    fail_phrase: str
    qa_phrase: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def rhyme_line(a: str, b: str) -> str:
    return f"{a} and {b}, quick and bright, kept their hearts aloft tonight."


SETTINGS = {
    "airport": Setting("airport", "the airport", "silver bell", "the gate desk", "the quiet bench"),
}

ACTIONS = {
    "sneezing": {
        "label": "sneezing spell",
        "trouble": "itchy sneezes and watery eyes",
        "trigger": "a drift of dust from the old cloak",
    }
}

REMEDIES = {
    "antihistamine": Remedy(
        "antihistamine",
        "antihistamine",
        sense=3,
        power=3,
        phrase="gave the child the antihistamine syrup and waited for the sneezy spell to soften",
        fail_phrase="gave the child the antihistamine syrup, but the sneezes still danced on",
        qa_phrase="gave the child the antihistamine syrup",
    ),
    "water": Remedy(
        "water",
        "water",
        sense=1,
        power=1,
        phrase="offered a cup of water and hoped for the best",
        fail_phrase="offered a cup of water, but it could not calm the sneezes",
        qa_phrase="offered a cup of water",
    ),
}

# a cloak can be carried, worn, hidden, or missing
CLOAK_STATES = {"worn", "missing", "found", "safe"}



def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid in SETTINGS:
        for remedy in REMEDIES:
            for cloak_state in ("worn", "missing"):
                out.append((sid, remedy, cloak_state))
    return out


@dataclass
class StoryParams:
    setting: str
    remedy: str
    cloak_state: str
    child: str = "Mira"
    child_gender: str = "girl"
    parent: str = "Mother"
    parent_gender: str = "mother"
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")

CURATED = [
    ("airport", "antihistamine", "worn"),
]



def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale airport storyworld with rhyme, suspense, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--cloak-state", choices=sorted(CLOAK_STATES))
    ap.add_argument("--child", choices=KID_NAMES)
    ap.add_argument("--parent", choices=["Mother", "Father"])
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
    if args.remedy and REMEDIES[args.remedy].sense < SENSE_MIN:
        raise StoryError("Only sensible remedies are allowed in this storyworld.")
    sid = args.setting or rng.choice(list(SETTINGS))
    remedy = args.remedy or "antihistamine"
    cloak_state = args.cloak_state or rng.choice(["worn", "missing"])
    if cloak_state not in CLOAK_STATES:
        raise StoryError("Invalid cloak state.")
    return StoryParams(
        setting=sid,
        remedy=remedy,
        cloak_state=cloak_state,
        child=args.child or rng.choice(KID_NAMES),
        child_gender="girl" if (args.child or "").lower() in {"mira", "luna", "nina", "ivy", "pip", "ada"} else "boy",
        parent=args.parent or rng.choice(["Mother", "Father"]),
        parent_gender="mother" if (args.parent or "Mother") == "Mother" else "father",
    )


def reasonableness_ok(params: StoryParams) -> bool:
    return params.remedy in REMEDIES and REMEDIES[params.remedy].sense >= SENSE_MIN


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(R) :- remedy(R), sense(R,S), sense_min(M), S >= M.
valid(S,R,C) :- setting(S), sensible(R), cloak_state(C).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def _sneeze(world: World, child: Entity) -> None:
    child.meters["sneezing"] += 1
    child.memes["fear"] += 1


def _find_cloak(world: World, child: Entity, parent: Entity) -> None:
    child.memes["hope"] += 1
    world.say(f"At the airport, {child.id} hugged {child.pronoun('possessive')} cloak and whispered, \"Soft cloak, stay close.\"")


def _suspense(world: World, child: Entity, parent: Entity) -> None:
    child.memes["fear"] += 1
    parent.memes["worry"] += 1
    world.say(
        f"But then the cloak went missing near {world.setting.suspense_spot}. "
        f"{parent.id} looked one way, then the other, while the loud airport clock ticked and ticked."
    )
    world.say(rhyme_line(child.id, parent.id))
    world.say(f'"Where is my cloak?" {child.id} asked, small as a sigh.')


def _reconcile(world: World, child: Entity, parent: Entity) -> None:
    child.memes["trust"] += 1
    parent.memes["warmth"] += 1
    world.say(
        f"{parent.id} knelt beside {child.id} and said, \"No blame, no shame. We find things best when we speak the same.\""
    )
    world.say(f"{child.id} took a breath and nodded. The worry in {child.id}'s chest grew lighter.")


def _give_remedy(world: World, child: Entity, parent: Entity, remedy: Remedy) -> None:
    child.meters["sneezing"] = 0.0
    child.memes["calm"] += 1
    parent.memes["calm"] += 1
    world.say(
        f"Then {parent.id} {remedy.phrase}. Soon {child.id}'s nose grew quiet, and the fairy-tale rush became still."
    )


def _ending(world: World, child: Entity, parent: Entity) -> None:
    world.say(
        f"In the end, the cloak was found folded safe on the {world.setting.safe_spot}, and {child.id} wore it again with a smile."
    )
    world.say(
        f"{parent.id} and {child.id} walked on together, no longer cross, with the airport lights shining like tiny stars."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(params.child, kind="character", type=params.child_gender, role="child"))
    parent = world.add(Entity(params.parent, kind="character", type=params.parent_gender, role="parent"))
    cloak = world.add(Entity("cloak", label="cloak", role="cloak"))
    remedy = REMEDIES[params.remedy]

    child.memes["love"] += 1
    child.meters["cloak_on"] += 1 if params.cloak_state == "worn" else 0

    world.say(
        f"Once at {world.setting.place}, {child.id} wore a cloak so fine, a silver thread and a moonlit line."
    )
    world.say(f"{child.id} sniffled at the gate, because {ACTIONS['sneezing']['trigger']} had begun to make trouble.")
    _find_cloak(world, child, parent)
    world.para()
    _sneeze(world, child)
    _suspense(world, child, parent)
    _reconcile(world, child, parent)
    world.para()
    _give_remedy(world, child, parent, remedy)
    _ending(world, child, parent)
    world.facts.update(child=child, parent=parent, cloak=cloak, remedy=remedy, outcome="reconciled")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a fairy-tale airport story with rhyme, suspense, and reconciliation, and include the words antihistamine and cloak.",
        f"Tell a child-facing airport tale where {f['child'].id} loses a cloak, worries at the gate, and is comforted with a calm rhyming line before help arrives.",
        f"Write a suspenseful but gentle story set in an airport where a parent uses antihistamine to help {f['child'].id} feel better and the family makes up.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    remedy = f["remedy"]
    return [
        QAItem(
            question="What made the story feel suspenseful?",
            answer=f"The cloak went missing near the gate desk, so {child.id} and {parent.id} had to search before the flight. That little delay made the airport feel tense for a moment.",
        ),
        QAItem(
            question="How did the family reconcile?",
            answer=f"{parent.id} knelt down, spoke gently, and told {child.id} there would be no blame or shame. {child.id} listened, took a breath, and the two of them became calm again.",
        ),
        QAItem(
            question="What helped the child feel better?",
            answer=f"{parent.id} gave {child.id} the antihistamine syrup, and the sneezing spell softened. That made it easier for {child.id} to smile and keep going.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is antihistamine?",
            answer="Antihistamine is medicine that helps with allergies like sneezing, itchy eyes, or a runny nose. Grown-ups give it when it is needed.",
        ),
        QAItem(
            question="What is a cloak?",
            answer="A cloak is a loose piece of clothing that hangs over your shoulders like a cape. It can help keep a child warm or dress them like a character in a fairy tale.",
        ),
        QAItem(
            question="Why can an airport feel suspenseful?",
            answer="An airport feels suspenseful because people are hurrying, bags can go missing, and everyone is watching the time. That makes even a small problem feel important.",
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
        if e.type:
            bits.append(f"type={e.type}")
        lines.append(f"  {e.id:8} {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "Only sensible fairy-tale remedies are allowed here."


def asp_verify() -> int:
    rc = 0
    cset, pset = set(asp_valid_combos()), set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        print("MISMATCH in valid combos.")
        rc = 1
    csens, psens = set(asp_sensible()), {r for r, rem in REMEDIES.items() if rem.sense >= SENSE_MIN}
    if csens == psens:
        print("OK: sensible remedy set matches.")
    else:
        print("MISMATCH in sensible remedy set.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, remedy=None, cloak_state=None, child=None, parent=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[item for item in story_qa(world)],
        world_qa=[item for item in world_knowledge_qa(world)],
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
        print(asp_program(show="#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible remedies: {', '.join(asp_sensible())}")
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(*combo, child="Mira", parent="Mother")) for combo in CURATED]
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
