#!/usr/bin/env python3
"""
A standalone storyworld: ultra creek chirp foreshadowing misunderstanding myth.

Premise:
A small village trusts a creek spirit's chirp, but a misunderstanding makes the
children fear the sound. The elder follows foreshadowing signs, learns the chirp
means the creek is warning of a stuck stone bridge, and the village works
together to open the water and save the night garden.

The world is classical and tiny:
- typed entities with meters and memes
- state-driven causal turns
- a Python reasonableness gate plus an inline ASP twin
- child-facing story text with QA and trace support
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# World constants.
THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities and world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"elder", "woman", "girl", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def ref(self) -> str:
        return self.label or self.id

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    place: str
    warning: str
    prize: str
    name: str
    role: str
    seed: Optional[int] = None


@dataclass
class Place:
    label: str
    tags: set[str] = field(default_factory=set)
    affords: set[str] = field(default_factory=set)


@dataclass
class Warning:
    id: str
    sound: str
    omen: str
    tells: str
    foreshadows: str
    target: str  # what it points toward
    place_tag: str


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    risk: str


@dataclass
class Fix:
    id: str
    label: str
    action: str
    solves: str
    covers: set[str]
    kind: str = "thing"


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "creek": Place(label="the creek", tags={"water", "creek"}, affords={"listen", "cross", "repair"}),
    "village": Place(label="the village lane", tags={"village"}, affords={"listen", "repair"}),
    "garden": Place(label="the night garden", tags={"garden", "flowers"}, affords={"listen", "repair"}),
}

WARNINGS = {
    "chirp": Warning(
        id="chirp",
        sound="chirp",
        omen="small bird-chirp",
        tells="a warning from the creek spirit",
        foreshadows="trouble under the bridge stones",
        target="bridge",
        place_tag="creek",
    ),
}

PRIZES = {
    "flowers": Prize(
        id="flowers",
        label="flowers",
        phrase="the night flowers",
        region="garden",
        risk="wilt",
    ),
    "lantern": Prize(
        id="lantern",
        label="lantern",
        phrase="a little lantern with a glass belly",
        region="hand",
        risk="smoke",
    ),
    "bridge": Prize(
        id="bridge",
        label="bridge",
        phrase="the stone bridge",
        region="creek",
        risk="jam",
    ),
}

FIXES = {
    "pry": Fix(
        id="pry",
        label="a long pole",
        action="lift the jammed stone",
        solves="open the creek again",
        covers={"creek"},
    ),
    "light": Fix(
        id="light",
        label="a lantern",
        action="guide the night work",
        solves="help everyone see the stones",
        covers={"garden"},
    ),
    "shout": Fix(
        id="shout",
        label="a loud shout",
        action="scare the water",
        solves="nothing useful",
        covers=set(),
    ),
}

NAMES = ["Nia", "Mara", "Oren", "Tavi", "Lio", "Sera"]
ROLES = ["elder", "girl", "boy", "woman", "man"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def risky_pair(warning: Warning, prize: Prize) -> bool:
    return warning.target == prize.id or warning.place_tag == prize.region or prize.region in {"garden", "hand", "creek"}


def select_fix(warning: Warning, prize: Prize) -> Optional[Fix]:
    if warning.target == "bridge":
        return FIXES["pry"]
    if prize.id == "flowers":
        return FIXES["light"]
    return None


def explain_rejection(warning: Warning, prize: Prize) -> str:
    return (
        f"(No story: the chirp does not honestly point to {prize.label} in this setup. "
        f"Choose a prize that the foreshadowing can warn about.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
warns(chirp, bridge).
prize(bridge).
prize(flowers).
prize(lantern).

risky(W, P) :- warns(W, P).
fix(bridge, pry).
fix(flowers, light).

valid(W, P, F) :- risky(W, P), fix(P, F).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("warn", "chirp"),
        asp.fact("points_to", "chirp", "bridge"),
        asp.fact("creek_place", "creek"),
        asp.fact("creek_place", "village"),
        asp.fact("creek_place", "garden"),
        asp.fact("prize", "bridge"),
        asp.fact("prize", "flowers"),
        asp.fact("prize", "lantern"),
        asp.fact("fix", "pry"),
        asp.fact("fix", "light"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple]:
    out = []
    for warn in WARNINGS.values():
        for prize in PRIZES.values():
            if risky_pair(warn, prize) and select_fix(warn, prize):
                out.append((warn.id, prize.id, select_fix(warn, prize).id))
    return sorted(out)


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def foreshadow(world: World, elder: Entity, warning: Warning) -> None:
    elder.memes["curiosity"] += 1
    world.say(
        f"At the edge of {world.place.label}, {elder.ref()} heard the {warning.omen} of a {warning.sound}."
    )
    world.say(
        f"It was a small sound, yet it carried {warning.tells}; the creek seemed to be pointing toward {warning.foreshadows}."
    )


def misunderstanding(world: World, child: Entity, warning: Warning) -> None:
    child.memes["fear"] += 1
    world.say(
        f"{child.ref()} misunderstood the chirp and thought the creek was angry."
    )
    world.say(
        f"{child.pronoun().capitalize()} backed away from the water, because the little sound felt like a bad omen."
    )


def reveal(world: World, elder: Entity, prize: Prize) -> None:
    elder.memes["wisdom"] += 1
    world.say(
        f"Then the elder looked at the wet stones and understood the truth: the chirp had foreshadowed trouble under the stone bridge."
    )
    world.say(
        f"The creek was not scolding anyone. It was asking for help before {prize.label} could be lost to the jam."
    )


def resolve(world: World, elder: Entity, child: Entity, prize: Prize, fix: Fix) -> None:
    child.memes["fear"] = 0.0
    child.memes["wonder"] += 1
    world.say(
        f"The villagers brought {fix.label}, and together they used it to {fix.action}."
    )
    world.say(
        f"Soon the water could run again, {fix.solves}, and {child.ref()} saw that the chirp had been a kind warning all along."
    )
    world.say(
        f"By the end, the night garden shone, the creek sang softly, and the bridge stood open like a smile."
    )


def tell(place: Place, warning: Warning, prize: Prize, name: str, role: str) -> World:
    world = World(place)
    elder = world.add(Entity(id="elder", kind="character", type="elder", label="the elder"))
    child = world.add(Entity(id=name, kind="character", type=role, label=name))
    target = world.add(Entity(id=prize.id, kind="thing", type=prize.id, label=prize.label, phrase=prize.phrase))
    fix = select_fix(warning, prize)
    if fix is None:
        raise StoryError(explain_rejection(warning, prize))

    world.say(
        f"Long ago, near {place.label}, there lived a small village that listened for signs in the wind and water."
    )
    foreshadow(world, elder, warning)
    world.para()
    misunderstanding(world, child, warning)
    world.say(
        f"That evening, {name} kept away from the creek, even though the moon made the water silver."
    )
    world.para()
    reveal(world, elder, target)
    resolve(world, elder, child, target, fix)

    world.facts.update(
        elder=elder, child=child, prize=target, warning=warning, fix=fix, place=place
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short myth for children about a creek sound that seems frightening at first but turns out to be helpful.",
        f"Tell a gentle myth where a {f['warning'].sound} near {f['place'].label} foreshadows trouble and a village learns the truth.",
        f"Write a story with misunderstanding and foreshadowing where {f['child'].ref()} and the elder respond to a creek warning.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    prize = f["prize"]
    warning = f["warning"]
    fix = f["fix"]
    return [
        QAItem(
            question=f"Who first heard the little {warning.sound} near the creek?",
            answer=f"The elder first heard the {warning.sound} near the creek, and {child.ref()} misunderstood it at first.",
        ),
        QAItem(
            question=f"What did the chirp foreshadow in the story?",
            answer=f"It foreshadowed trouble under the stone bridge, because the creek was warning the village before the stones jammed the water.",
        ),
        QAItem(
            question=f"Why was {child.ref()} scared of the sound at first?",
            answer=f"{child.ref()} thought the chirp meant the creek was angry, so the sound became a misunderstanding instead of a message.",
        ),
        QAItem(
            question=f"What helped the village fix the problem?",
            answer=f"They brought {fix.label} and used it to {fix.action}, which helped the creek open again and kept the night garden safe.",
        ),
        QAItem(
            question=f"What changed by the end of the myth?",
            answer=f"By the end, the creek could run freely, the bridge stood open, and {child.ref()} understood that the chirp had been a kind warning.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a foreshadowing sign in a story?",
            answer="A foreshadowing sign is a clue that hints something important may happen later.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks a message means one thing, but it really means something else.",
        ),
        QAItem(
            question="Why do creeks make soft sounds?",
            answer="Creeks make soft sounds because water moves over stones, logs, and tiny bends in the ground.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        m = {k: v for k, v in e.meters.items() if v}
        n = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={m}")
        if n:
            bits.append(f"memes={n}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mythic storyworld about a creek chirp and a misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--warning", choices=WARNINGS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["elder", "girl", "boy", "woman", "man"])
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
    warning = args.warning or rng.choice(list(WARNINGS))
    prize = args.prize or rng.choice(list(PRIZES))
    if args.warning and args.prize:
        if not (risky_pair(WARNINGS[args.warning], PRIZES[args.prize]) and select_fix(WARNINGS[args.warning], PRIZES[args.prize])):
            raise StoryError(explain_rejection(WARNINGS[args.warning], PRIZES[args.prize]))
    name = args.name or rng.choice(NAMES)
    role = args.role or rng.choice(ROLES)
    place = args.place or rng.choice(list(PLACES))
    return StoryParams(place=place, warning=warning, prize=prize, name=name, role=role)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], WARNINGS[params.warning], PRIZES[params.prize], params.name, params.role)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(place="creek", warning="chirp", prize="bridge", name="Nia", role="girl"),
    StoryParams(place="village", warning="chirp", prize="flowers", name="Oren", role="boy"),
    StoryParams(place="garden", warning="chirp", prize="lantern", name="Sera", role="woman"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    rng0 = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            seed = (args.seed if args.seed is not None else random.randrange(2**31)) + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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
