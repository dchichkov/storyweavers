#!/usr/bin/env python3
"""
A small whodunit storyworld about providence, an imposter, and a principal.
The mystery is solved through a magic transformation that changes what the
detective can observe, while keeping the prose child-facing and state-driven.

Story premise:
- A careful child or helper notices something odd at school.
- A principal is worried because someone is pretending to be them.
- Magic reveals a hidden clue by transforming an ordinary object.

The simulation tracks:
- Physical meters: clue_hidden, clue_seen, magic_power, suspicion, trust
- Emotional memes: worry, curiosity, relief, pride, surprise, confusion

The narrative is intentionally whodunit-like: a strange sign, suspicion,
investigation, a magical reveal, then a clear ending that proves what changed.
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
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the school"
    indoor: bool = True
    magic_works: bool = True


@dataclass
class ClueItem:
    id: str
    label: str
    phrase: str
    reveals: str
    location: str
    concealed_by: str


@dataclass
class Magic:
    id: str
    label: str
    verb: str
    reveal_text: str
    need: str
    result: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_suspicion(world: World) -> list[str]:
    out: list[str] = []
    principal = world.entities.get("principal")
    imposter = world.entities.get("imposter")
    if not principal or not imposter:
        return out
    if principal.memes.get("worry", 0.0) < THRESHOLD:
        return out
    if imposter.memes.get("confusion", 0.0) < THRESHOLD:
        return out
    sig = ("suspicion",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    principal.meters["suspicion"] = principal.meters.get("suspicion", 0.0) + 1.0
    out.append("The oddness grew into a real mystery.")
    return out


def _r_magic_reveal(world: World) -> list[str]:
    out: list[str] = []
    magic = world.entities.get("magic")
    clue = world.entities.get("clue")
    detective = world.entities.get("detective")
    principal = world.entities.get("principal")
    imposter = world.entities.get("imposter")
    if not all([magic, clue, detective, principal, imposter]):
        return out
    if magic.meters.get("charged", 0.0) < THRESHOLD:
        return out
    if detective.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    sig = ("reveal",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    clue.meters["seen"] = clue.meters.get("seen", 0.0) + 1.0
    detective.meters["solved"] = detective.meters.get("solved", 0.0) + 1.0
    principal.memes["relief"] = principal.memes.get("relief", 0.0) + 1.0
    imposter.memes["confusion"] = max(0.0, imposter.memes.get("confusion", 0.0) - 1.0)
    out.append("A hidden clue finally came into view.")
    return out


def _r_truth(world: World) -> list[str]:
    out: list[str] = []
    detective = world.entities.get("detective")
    principal = world.entities.get("principal")
    imposter = world.entities.get("imposter")
    clue = world.entities.get("clue")
    if not all([detective, principal, imposter, clue]):
        return out
    if clue.meters.get("seen", 0.0) < THRESHOLD:
        return out
    sig = ("truth",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["pride"] = detective.memes.get("pride", 0.0) + 1.0
    principal.memes["trust"] = principal.memes.get("trust", 0.0) + 1.0
    out.append("The mystery had an answer at last.")
    return out


CAUSAL_RULES = [_r_suspicion, _r_magic_reveal, _r_truth]


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


def assert_reasonable(setting: Setting, clue: ClueItem, magic: Magic) -> None:
    if not setting.magic_works:
        raise StoryError("This world needs a place where magic can work.")
    if clue.location not in {"hall", "office", "stage", "desk"}:
        raise StoryError("The clue needs a simple indoor place in this storyworld.")
    if not clue.concealed_by:
        raise StoryError("The mystery needs something to hide the clue.")
    if magic.need != clue.concealed_by:
        raise StoryError("The magic must reveal exactly the thing that hid the clue.")


def copy_name(role: str) -> str:
    return {"principal": "Principal Wren", "imposter": "the imposter", "detective": "Pip", "providence": "Providence"}.get(role, role)


SETTINGS = {
    "school": Setting(place="the school", indoor=True, magic_works=True),
    "library": Setting(place="the library", indoor=True, magic_works=True),
    "museum": Setting(place="the museum", indoor=True, magic_works=True),
}

CLUES = {
    "chalk": ClueItem(
        id="chalk",
        label="chalk mark",
        phrase="a tiny chalk mark",
        reveals="the chalk was left by the imposter",
        location="hall",
        concealed_by="wardrobe",
    ),
    "button": ClueItem(
        id="button",
        label="button",
        phrase="a shiny button",
        reveals="the button matched the imposter's coat",
        location="desk",
        concealed_by="cloak",
    ),
    "mask": ClueItem(
        id="mask",
        label="mask ribbon",
        phrase="a ribbon from a costume mask",
        reveals="the ribbon had been tied by the imposter",
        location="office",
        concealed_by="shadow",
    ),
}

MAGICS = {
    "lantern": Magic(
        id="lantern",
        label="lantern magic",
        verb="shine",
        reveal_text="The lantern glow turned the ordinary air clear enough to notice the clue.",
        need="wardrobe",
        result="seen",
    ),
    "mirror": Magic(
        id="mirror",
        label="mirror magic",
        verb="reflect",
        reveal_text="The mirror flashed, and the hidden thing showed itself at once.",
        need="cloak",
        result="seen",
    ),
    "spark": Magic(
        id="spark",
        label="spark magic",
        verb="sparkle",
        reveal_text="The sparkles drifted over the shadow and made the hidden clue stand out.",
        need="shadow",
        result="seen",
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid, clue in CLUES.items():
            for mid, magic in MAGICS.items():
                if magic.need == clue.concealed_by:
                    combos.append((sid, cid, mid))
    return combos


@dataclass
class StoryParams:
    setting: str
    clue: str
    magic: str
    detective: str
    principal: str
    imposter: str
    seed: Optional[int] = None


NAMES = ["Pip", "Mina", "Toby", "Nora", "Ellis", "June", "Ari"]
TRAITS = ["careful", "curious", "brave", "quiet", "sharp"]


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    clue = CLUES[params.clue]
    magic = MAGICS[params.magic]
    assert_reasonable(setting, clue, magic)

    world = World(setting)
    detective = world.add(Entity(
        id="detective", kind="character", type="child", label=params.detective,
        traits=["little", random.choice(TRAITS)],
    ))
    principal = world.add(Entity(
        id="principal", kind="character", type="adult", label=params.principal,
        meters={"suspicion": 0.0}, memes={"worry": 1.0, "trust": 0.0},
    ))
    imposter = world.add(Entity(
        id="imposter", kind="character", type="adult", label=params.imposter,
        meters={"suspicion": 0.0}, memes={"confusion": 1.0},
    ))
    clue_ent = world.add(Entity(
        id="clue", kind="thing", type="clue", label=clue.label, phrase=clue.phrase,
        location=clue.location, meters={"seen": 0.0, "hidden": 1.0},
    ))
    magic_ent = world.add(Entity(
        id="magic", kind="thing", type="magic", label=magic.label, phrase=magic.reveal_text,
        meters={"charged": 1.0},
    ))
    providence = world.add(Entity(
        id="providence", kind="thing", type="force", label="providence",
        phrase="a lucky nudge at the right moment",
        meters={"hinted": 1.0},
    ))

    world.say(
        f"At {setting.place}, {params.detective} noticed something strange about {params.principal}."
    )
    world.say(
        f"Someone was wearing the right clothes and carrying the right smile, but it felt wrong."
    )
    world.say(
        f"The principal grew worried, because an imposter was hiding near {clue.location}."
    )

    world.para()
    detective.memes["curiosity"] = 1.0
    principal.memes["worry"] = 1.0
    imposter.memes["confusion"] = 1.0
    world.say(
        f"{params.detective} looked closer and found {clue.phrase}, tucked where nobody would think to look."
    )
    world.say(
        f"{copy_name('providence')} seemed to help, as if the right clue had been waiting there all along."
    )
    world.say(
        f"But the clue was hidden by {clue.concealed_by}, so it still needed magic."
    )

    world.para()
    world.say(magic.reveal_text)
    world.say(f"{params.detective} used {magic.label} to {magic.verb} the darkness away.")
    clue_ent.meters["hidden"] = 0.0
    magic_ent.meters["charged"] = 0.0
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"Then the clue made sense: {clue.reveals}."
    )
    world.say(
        f"The imposter could not keep pretending once everyone saw the truth."
    )
    world.say(
        f"The principal smiled again, and {params.detective} stood a little taller, proud to have solved the mystery."
    )

    world.facts.update(
        setting=setting,
        clue=clue,
        magic=magic,
        detective=detective,
        principal=principal,
        imposter=imposter,
        providence=providence,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    clue: ClueItem = f["clue"]
    magic: Magic = f["magic"]
    return [
        f'Write a short whodunit story for a young child that includes "{clue.label}", "{magic.label}", and "principal".',
        f"Tell a mystery where providence helps a child notice an imposter and a magic trick reveals the clue.",
        f"Write a gentle detective story with a surprise, a hidden clue, and a happy answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]
    principal: Entity = f["principal"]
    imposter: Entity = f["imposter"]
    clue: ClueItem = f["clue"]
    magic: Magic = f["magic"]

    return [
        QAItem(
            question=f"Who helped solve the mystery at {world.setting.place}?",
            answer=f"{detective.label} helped solve it by noticing the clue and using {magic.label}.",
        ),
        QAItem(
            question=f"Why was the principal worried?",
            answer=f"The principal was worried because an imposter was pretending to be someone real.",
        ),
        QAItem(
            question=f"What hidden thing showed who the imposter was?",
            answer=f"{clue.phrase} did. When it was revealed, it matched {clue.reveals}.",
        ),
        QAItem(
            question=f"What made the clue visible?",
            answer=f"{magic.label} made it visible. The magic changed the hidden clue into something everyone could see.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The mystery was solved, the imposter was exposed, and the principal felt relieved.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "mystery": [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle about something unknown that people try to figure out.",
        )
    ],
    "imposter": [
        QAItem(
            question="What is an imposter?",
            answer="An imposter is someone who pretends to be another person or tries to fool others.",
        )
    ],
    "principal": [
        QAItem(
            question="What does a principal do at school?",
            answer="A principal helps run the school and makes sure students and teachers are safe.",
        )
    ],
    "magic": [
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something surprising and impossible that can make unusual things happen in the story.",
        )
    ],
    "providence": [
        QAItem(
            question="What does providence mean in a story?",
            answer="Providence means a lucky turn or helpful timing that seems to arrive just when it is needed.",
        )
    ],
    "transformation": [
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form or state into another.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["mystery"])
    out.extend(WORLD_KNOWLEDGE["imposter"])
    out.extend(WORLD_KNOWLEDGE["principal"])
    out.extend(WORLD_KNOWLEDGE["magic"])
    out.extend(WORLD_KNOWLEDGE["providence"])
    out.extend(WORLD_KNOWLEDGE["transformation"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A clue is hidden when it is concealed by something.
hidden(C) :- clue(C), concealed_by(C,_).

% Magic can reveal a clue only if it matches the concealed-by type.
can_reveal(M, C) :- magic(M), clue(C), concealed_by(C, X), reveals(M, X).

% A mystery is solvable when the clue can be revealed and the detective is curious.
solvable(S, C, M) :- setting(S), clue(C), magic(M), can_reveal(M, C), curious_detective.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("concealed_by", cid, clue.concealed_by))
    for mid, magic in MAGICS.items():
        lines.append(asp.fact("magic", mid))
        lines.append(asp.fact("reveals", mid, magic.need))
    lines.append("curious_detective.")
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_asp_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show solvable/3."))
    return sorted(set(asp.atoms(model, "solvable")))


def verify() -> int:
    py = set(valid_combos())
    asp_set = set(valid_asp_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - asp_set))
    print("asp-only:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld with providence, an imposter, and a principal.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--detective")
    ap.add_argument("--principal")
    ap.add_argument("--imposter")
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
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.clue:
        combos = [c for c in combos if c[1] == args.clue]
    if args.magic:
        combos = [c for c in combos if c[2] == args.magic]
    if not combos:
        raise StoryError("No valid mystery matches the given options.")
    setting, clue, magic = rng.choice(sorted(combos))
    detective = args.detective or rng.choice(NAMES)
    principal = args.principal or "Principal Wren"
    imposter = args.imposter or "the imposter"
    return StoryParams(setting=setting, clue=clue, magic=magic, detective=detective, principal=principal, imposter=imposter)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(setting="school", clue="chalk", magic="lantern", detective="Pip", principal="Principal Wren", imposter="the imposter"),
    StoryParams(setting="library", clue="button", magic="mirror", detective="Mina", principal="Principal Vale", imposter="the imposter"),
    StoryParams(setting="museum", clue="mask", magic="spark", detective="Nora", principal="Principal Finch", imposter="the imposter"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solvable/3."))
        return
    if args.verify:
        sys.exit(verify())
    if args.asp:
        combos = valid_asp_combos()
        print(f"{len(combos)} valid mysteries:\n")
        for s, c, m in combos:
            print(f"  {s:8} {c:8} {m:8}")
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
            params = resolve_params(args, random.Random(seed))
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
