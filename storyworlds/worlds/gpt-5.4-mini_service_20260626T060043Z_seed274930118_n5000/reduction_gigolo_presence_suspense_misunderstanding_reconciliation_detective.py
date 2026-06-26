#!/usr/bin/env python3
"""
storyworlds/worlds/reduction_gigolo_presence_suspense_misunderstanding_reconciliation_detective.py
=================================================================================================

A small, self-contained detective-story world with a gentle mystery arc:
an investigator notices a strange presence, follows clues through suspense,
misunderstanding causes a false accusation, and the case ends in reconciliation.

Seed image used to build the model:
---
A child detective walks through a quiet town office at dusk. A famous visitor
called Gigolo is waiting for an interview, but someone says the visitor never
arrived. The detective notices that the visitor's presence is not missing at
all; it has only been reduced to a single set of footprints, a hat on a chair,
and a note that was read too quickly. By tracing the clues, the detective
discovers that the helper was mistaken, the visitor was hiding nearby to avoid
the rain, and everyone can laugh and make up at the end.

World dynamics:
---
- Presence is a physical/social meter: where someone is, whether they are
  noticed, and whether a room feels occupied.
- Reduction is a physical meter: clues can become reduced in size, reduced in
  number, or reduced in certainty when the detective narrows the possibilities.
- Suspense rises when a clue points in two directions.
- Misunderstanding rises when one character interprets the clue too quickly.
- Reconciliation lowers tension when the truth is shown clearly.

The story is kept child-facing and concrete, while still feeling like a small
detective tale with a beginning, middle turn, and ending image.
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
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "detective-girl"}
        male = {"boy", "man", "father", "detective-boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little station office"
    indoors: bool = True
    mood: str = "quiet"


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    kind: str  # footprint, note, hat, scarf, window, umbrella...
    location: str
    hint: str
    reduction: float = 0.0
    suspicious: bool = False


@dataclass
class CharacterPlan:
    id: str
    type: str
    label: str
    trait: str
    role: str  # detective, helper, visitor, clerk
    concern: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.clues: dict[str, Clue] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_clue(self, clue: Clue) -> Clue:
        self.clues[clue.id] = clue
        return clue

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.clues = copy.deepcopy(self.clues)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _bump(world: World, eid: str, key: str, amount: float = 1.0) -> None:
    ent = world.get(eid)
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _bump_mem(world: World, eid: str, key: str, amount: float = 1.0) -> None:
    ent = world.get(eid)
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    for clue in world.clues.values():
        if clue.suspicious and clue.reduction < THRESHOLD:
            sig = ("suspense", clue.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            _bump(world, "case", "suspense", 1.0)
            out.append(f"The clue made the room feel even more suspenseful.")
    return out


def _r_reduction(world: World) -> list[str]:
    out: list[str] = []
    for clue in world.clues.values():
        if clue.reduction >= THRESHOLD:
            sig = ("reduction", clue.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            _bump(world, "case", "reduction", 1.0)
            out.append(f"The detective reduced the mystery to one clear clue.")
    return out


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    helper = world.entities.get("helper")
    visitor = world.entities.get("visitor")
    if not helper or not visitor:
        return out
    if helper.memes.get("jump_to_conclusion", 0.0) < THRESHOLD:
        return out
    if helper.memes.get("misunderstanding", 0.0) >= THRESHOLD:
        return out
    sig = ("misunderstanding",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["misunderstanding"] = 1.0
    _bump(world, "case", "misunderstanding", 1.0)
    out.append("The helper misunderstood the clue and blamed the wrong person.")
    return out


def _r_reconciliation(world: World) -> list[str]:
    out: list[str] = []
    helper = world.entities.get("helper")
    visitor = world.entities.get("visitor")
    detective = world.entities.get("detective")
    if not helper or not visitor or not detective:
        return out
    if world.facts.get("truth_shown") and helper.memes.get("misunderstanding", 0.0) >= THRESHOLD:
        sig = ("reconcile",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        helper.memes["misunderstanding"] = 0.0
        helper.memes["relief"] = helper.memes.get("relief", 0.0) + 1.0
        visitor.memes["relief"] = visitor.memes.get("relief", 0.0) + 1.0
        detective.memes["warmth"] = detective.memes.get("warmth", 0.0) + 1.0
        _bump(world, "case", "reconciliation", 1.0)
        out.append("Once the truth was shown, the helper and the visitor made up.")
    return out


CAUSAL_RULES = [_r_suspense, _r_reduction, _r_misunderstanding, _r_reconciliation]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def validate_reasonable(plan: "StoryParams") -> None:
    if plan.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if plan.detective not in DETECTIVES:
        raise StoryError("Unknown detective.")
    if plan.helper not in HELPERS:
        raise StoryError("Unknown helper.")
    if plan.visitor not in VISITORS:
        raise StoryError("Unknown visitor.")


def clue_is_compatible(clue: Clue, visitor_name: str) -> bool:
    if clue.kind == "umbrella" and visitor_name == "Gigolo":
        return True
    if clue.kind in {"footprint", "hat", "note"}:
        return True
    return False


def needs_reduction(clues: list[Clue]) -> bool:
    return any(c.suspicious for c in clues)


def apply_truth(world: World) -> None:
    world.facts["truth_shown"] = True


def tell(setting: Setting, detective: CharacterPlan, helper: CharacterPlan, visitor: CharacterPlan,
         clue_pack: list[Clue]) -> World:
    world = World(setting)
    world.add(Entity(
        id="case", kind="thing", type="case", label="the case", phrase="the case",
        meters={"suspense": 0.0, "reduction": 0.0}, memes={"misunderstanding": 0.0, "reconciliation": 0.0},
    ))
    det = world.add(Entity(
        id="detective", kind="character", type=detective.type, label=detective.label,
        phrase=detective.label, traits=[detective.trait, "careful"], location=setting.place,
    ))
    h = world.add(Entity(
        id="helper", kind="character", type=helper.type, label=helper.label,
        phrase=helper.label, traits=[helper.trait, "quick"], location=setting.place,
    ))
    v = world.add(Entity(
        id="visitor", kind="character", type=visitor.type, label=visitor.label,
        phrase=visitor.label, traits=[visitor.trait, "quiet"], location=setting.place,
    ))
    for clue in clue_pack:
        world.add_clue(clue)

    world.say(f"{det.label} was a {detective.trait} detective who liked quiet rooms and tiny clues.")
    world.say(f"At {setting.place}, {h.label} waited for {v.label}, a visitor everyone kept talking about.")
    world.say(
        f"The strange thing was the visitor's presence: it seemed to have been reduced to a few clues "
        f"on the floor and a note on the desk."
    )

    world.para()
    world.say(f"Then {det.label} looked closer.")
    for clue in clue_pack[:2]:
        world.say(f"{clue.phrase.capitalize()} gave {det.label} a small, careful hint.")
        clue.reduction += 1.0
    world.say("The more the detective studied the room, the more suspense gathered in the corners.")
    propagate(world, narrate=True)

    world.para()
    world.say(f"{h.label} pointed at the clues too fast and made a bad guess.")
    _bump_mem(world, "helper", "jump_to_conclusion", 1.0)
    propagate(world, narrate=True)
    world.say(f"{h.label} thought {v.label} had left without coming back, and that was not true.")
    _bump_mem(world, "helper", "misunderstanding", 1.0)
    propagate(world, narrate=True)

    world.para()
    world.say(f"{det.label} solved the puzzle by following the smallest clue of all: one wet footprint near the back door.")
    for clue in clue_pack:
        if clue.kind == "footprint":
            clue.reduction += 1.0
    apply_truth(world)
    world.say(f"The footprint showed that {v.label} had only stepped out to avoid the rain.")
    world.say(f"{v.label} was hiding nearby, not gone at all.")
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{det.label} explained everything clearly, and {h.label} felt their face grow warm with embarrassment."
    )
    propagate(world, narrate=True)
    world.say(
        f"Then {h.label} smiled, apologized, and shook hands with {v.label}. The room felt calm again."
    )
    world.say(
        f"By the end, the mystery had been reduced to a simple truth, and everyone stood together in a friendly, "
        f"reconciled presence."
    )

    world.facts.update(
        detective=det,
        helper=h,
        visitor=v,
        clues=clue_pack,
        setting=setting,
        truth_shown=True,
    )
    return world


SETTINGS = {
    "office": Setting(place="the little station office", indoors=True, mood="quiet"),
    "library": Setting(place="the town library", indoors=True, mood="hushed"),
    "hall": Setting(place="the front hall", indoors=True, mood="still"),
}

DETECTIVES = {
    "child": CharacterPlan(
        id="child", type="boy", label="Milo", trait="careful", role="detective",
        concern="likes to notice small things",
    ),
    "girl": CharacterPlan(
        id="girl", type="girl", label="Nina", trait="thoughtful", role="detective",
        concern="likes to ask one more question",
    ),
}

HELPERS = {
    "clerk": CharacterPlan(
        id="clerk", type="woman", label="Mrs. Vale", trait="busy", role="helper",
        concern="wants the room tidy and the schedule correct",
    ),
    "guard": CharacterPlan(
        id="guard", type="man", label="Mr. Reed", trait="stern", role="helper",
        concern="wants the visitor reported quickly",
    ),
}

VISITORS = {
    "gigolo": CharacterPlan(
        id="gigolo", type="man", label="Gigolo", trait="shy", role="visitor",
        concern="does not like the rain on his hat",
    ),
    "singer": CharacterPlan(
        id="singer", type="woman", label="June", trait="soft-spoken", role="visitor",
        concern="does not want a crowd at the door",
    ),
}

CLUE_REGISTRY = {
    "footprint": Clue("footprint", "one wet footprint", "One wet footprint near the back door", "footprint", "back door", "someone stepped out and returned", suspicious=False),
    "hat": Clue("hat", "a tipped hat", "A tipped hat rested on the chair", "hat", "chair", "the visitor had been here recently", suspicious=False),
    "note": Clue("note", "a half-read note", "A half-read note sat under the lamp", "note", "desk", "the words had been read too quickly", suspicious=True),
    "umbrella": Clue("umbrella", "a folded umbrella", "A folded umbrella leaned against the wall", "umbrella", "wall", "the visitor was only waiting for the rain to pass", suspicious=True),
}


@dataclass
class StoryParams:
    setting: str
    detective: str
    helper: str
    visitor: str
    clue_a: str
    clue_b: str
    clue_c: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world about suspense, misunderstanding, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--detective", choices=DETECTIVES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--visitor", choices=VISITORS)
    ap.add_argument("--clue-a", choices=CLUE_REGISTRY)
    ap.add_argument("--clue-b", choices=CLUE_REGISTRY)
    ap.add_argument("--clue-c", choices=CLUE_REGISTRY)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    detective = args.detective or rng.choice(list(DETECTIVES))
    helper = args.helper or rng.choice(list(HELPERS))
    visitor = args.visitor or rng.choice(list(VISITORS))
    clues = list(CLUE_REGISTRY)
    clue_a = args.clue_a or rng.choice(clues)
    clue_b = args.clue_b or rng.choice(clues)
    clue_c = args.clue_c or rng.choice(clues)
    params = StoryParams(setting, detective, helper, visitor, clue_a, clue_b, clue_c)
    validate_reasonable(params)
    return params


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    det = f["detective"].label
    helper = f["helper"].label
    visitor = f["visitor"].label
    place = f["setting"].place
    return [
        f"Write a short detective story about {det} at {place} where a strange presence has to be explained.",
        f"Tell a gentle mystery where {helper} thinks {visitor} is missing, but {det} finds the real clue.",
        f"Write a child-friendly detective tale using the words reduction, gigolo, and presence.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det = f["detective"].label
    helper = f["helper"].label
    visitor = f["visitor"].label
    place = f["setting"].place
    clue_names = ", ".join(c.label for c in f["clues"])
    return [
        QAItem(
            question=f"Who solved the mystery at {place}?",
            answer=f"{det} solved the mystery by carefully looking at the clues and not jumping to conclusions.",
        ),
        QAItem(
            question=f"Why did {helper} make the wrong guess about {visitor}?",
            answer=f"{helper} misunderstood the clues and thought {visitor} had left, even though the visitor was only hiding nearby.",
        ),
        QAItem(
            question=f"What showed that the visitor was really present?",
            answer=f"The wet footprint and the other clues showed that {visitor} was still there, just out of sight for a little while.",
        ),
        QAItem(
            question=f"Which clues mattered in the case?",
            answer=f"The case used {clue_names}, and the clearest clue was the wet footprint near the back door.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks carefully at clues, asks questions, and tries to figure out what really happened.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone gets the wrong idea because they did not understand the clue or the words correctly.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who had a problem talk kindly, forgive each other, and make up.",
        ),
        QAItem(
            question="What is presence?",
            answer="Presence means being there. In a story, it can mean someone is in the room even if they are hard to notice.",
        ),
        QAItem(
            question="What does reduction mean in this story world?",
            answer="Reduction means making the mystery smaller and clearer by following clues until only the most important truth is left.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    for c in world.clues.values():
        lines.append(f"  clue:{c.id:8} reduction={c.reduction} suspicious={c.suspicious}")
    lines.append(f"  fired rules: {sorted({n for (n, *_) in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("office", "child", "clerk", "gigolo", "footprint", "hat", "note"),
    StoryParams("library", "girl", "guard", "gigolo", "note", "footprint", "umbrella"),
    StoryParams("hall", "child", "clerk", "gigolo", "hat", "note", "footprint"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
    for did, d in DETECTIVES.items():
        lines.append(asp.fact("detective", did))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
    for vid, v in VISITORS.items():
        lines.append(asp.fact("visitor", vid))
    for cid, c in CLUE_REGISTRY.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("kind", cid, c.kind))
        lines.append(asp.fact("at", cid, c.location))
        if c.suspicious:
            lines.append(asp.fact("suspicious", cid))
    return "\n".join(lines)


ASP_RULES = r"""
% Suspense when a clue is suspicious and not yet reduced.
suspense(C) :- clue(C), suspicious(C), not reduced(C).

% A clue becomes reduced once the detective focuses on it.
reduced(C) :- chosen(C).

% Misunderstanding happens if a suspicious clue is not yet fully reduced and the helper guesses too soon.
misunderstanding :- suspense(C), not reduced(C), helper_guess.

% Reconciliation follows once the truth is shown.
reconciliation :- truth_shown.

#show suspense/1.
#show misunderstanding/0.
#show reconciliation/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    # ASP gate is deliberately small; verify the same idea can be derived by Python facts.
    program = asp_program("#show suspense/1.\n#show misunderstanding/0.\n#show reconciliation/0.")
    model = asp.one_model(program)
    has_suspense = any(sym.name == "suspense" for sym in model)
    has_mis = any(sym.name == "misunderstanding" for sym in model)
    has_rec = any(sym.name == "reconciliation" for sym in model)
    if has_suspense and has_mis and has_rec:
        print("OK: ASP rules are syntactically valid and produce the expected story markers.")
        return 0
    print("ASP verification failed: missing expected markers.")
    return 1


def asp_facts_for_story(sample: StorySample) -> str:
    return asp_facts()


def generate(params: StoryParams) -> StorySample:
    validate_reasonable(params)
    setting = SETTINGS[params.setting]
    detective = DETECTIVES[params.detective]
    helper = HELPERS[params.helper]
    visitor = VISITORS[params.visitor]
    clues = [copy.deepcopy(CLUE_REGISTRY[params.clue_a]),
             copy.deepcopy(CLUE_REGISTRY[params.clue_b]),
             copy.deepcopy(CLUE_REGISTRY[params.clue_c])]
    world = tell(setting, detective, helper, visitor, clues)
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
        print(asp_program("#show suspense/1.\n#show misunderstanding/0.\n#show reconciliation/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show suspense/1.\n#show misunderstanding/0.\n#show reconciliation/0."))
        print("ASP markers:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.detective} / {p.helper} / {p.visitor} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
