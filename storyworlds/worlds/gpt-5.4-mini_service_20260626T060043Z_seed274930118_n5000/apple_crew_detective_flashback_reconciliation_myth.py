#!/usr/bin/env python3
"""
A myth-styled story world about an apple crew, a detective, a flashback, and a reconciliation.

The premise:
- A small crew tends a sacred orchard.
- A detective arrives after an apple goes missing or is found cracked.
- A flashback reveals an old promise, a forgotten kindness, or a misunderstood action.
- The ending resolves through reconciliation, restoring trust and purpose.

This script is self-contained and follows the Storyweavers world contract.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"detective"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"crew", "crowd"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the orchard"
    detail: str = "an old orchard beneath a watchful hill"


@dataclass
class Crew:
    name: str
    role: str
    vow: str
    task: str


@dataclass
class Case:
    id: str
    label: str
    threat: str
    clue: str
    outcome: str


@dataclass
class Flashback:
    id: str
    title: str
    memory: str
    reason: str


@dataclass
class Reconciliation:
    id: str
    act: str
    gift: str
    bond: str


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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "orchard": Setting(place="the orchard", detail="an old orchard beneath a watchful hill"),
    "grove": Setting(place="the grove", detail="a quiet grove where the wind kept the leaves singing"),
    "courtyard": Setting(place="the courtyard", detail="a moonlit courtyard beside a stone hall"),
}

CREWS = {
    "orchard-keepers": Crew(
        name="orchard-keepers",
        role="apple crew",
        vow="to guard every bright apple",
        task="gathering apples before the dawn birds arrived",
    ),
    "harvest-band": Crew(
        name="harvest-band",
        role="apple crew",
        vow="to share the fruit fairly",
        task="sorting the apples in woven baskets",
    ),
    "watchers": Crew(
        name="watchers",
        role="apple crew",
        vow="to keep the paths clear",
        task="patrolling the branches by lantern light",
    ),
}

CASES = {
    "missing-apple": Case(
        id="missing-apple",
        label="a missing apple",
        threat="one apple had vanished from the basket",
        clue="a red peel-scrape on the old stone",
        outcome="the apple had been carried only a little way, not stolen forever",
    ),
    "split-apple": Case(
        id="split-apple",
        label="a split apple",
        threat="one sacred apple had cracked open",
        clue="a bruise shaped like a dropped star",
        outcome="the crack came from an honest mistake, not from spite",
    ),
    "lost-basket": Case(
        id="lost-basket",
        label="a lost basket",
        threat="the best basket could not be found",
        clue="twine threads caught on a low branch",
        outcome="the basket had been moved to keep it dry",
    ),
}

FLASHBACKS = {
    "old-promise": Flashback(
        id="old-promise",
        title="an old promise",
        memory="Long before, the detective had once been a child in the orchard and had promised to return kindness to the crew.",
        reason="the crew feared the detective had forgotten that promise",
    ),
    "shared-rain": Flashback(
        id="shared-rain",
        title="a rainy memory",
        memory="The crew remembered a stormy night when the detective helped them gather apples by lantern while the rain sang on the leaves.",
        reason="the detective had looked stern, and the crew had mistaken sternness for blame",
    ),
    "broken-lantern": Flashback(
        id="broken-lantern",
        title="a broken lantern",
        memory="The detective remembered tripping over a root and knocking a lantern against a wall, which had frightened the crew.",
        reason="the crew believed the noise had been anger, but it had only been clumsiness",
    ),
}

RECONCILIATIONS = {
    "shared-basket": Reconciliation(
        id="shared-basket",
        act="the detective placed the apples back into the crew's shared basket",
        gift="a polished basket handle wrapped in blue thread",
        bond="the crew and detective could work as one again",
    ),
    "apology-fire": Reconciliation(
        id="apology-fire",
        act="the detective bowed and spoke a true apology beneath the lanterns",
        gift="a little lantern wick trimmed bright and clean",
        bond="the old fear melted from the crew's hearts",
    ),
    "fruit-oath": Reconciliation(
        id="fruit-oath",
        act="the crew offered the detective the first apple of the season",
        gift="a sweet apple cut into equal wedges",
        bond="their trust was renewed like a river after rain",
    ),
}

NAMES = ["Arin", "Mira", "Talen", "Ivo", "Nessa", "Rho", "Elin", "Sera"]
DETECTIVE_NAMES = ["Inspector Ash", "Detective Rowan", "Seer Vale", "Watcher Bram"]
TRAITS = ["patient", "cautious", "bright-eyed", "steadfast", "gentle", "grave"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    crew: str
    case: str
    flashback: str
    reconciliation: str
    detective: str
    crew_member: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
crew(C) :- crew_name(C).
case(CS) :- case_name(CS).
flashback(F) :- flashback_name(F).
reconciliation(R) :- reconciliation_name(R).

valid_story(S, C, CS, F, R) :- setting(S), crew(C), case(CS), flashback(F), reconciliation(R).

compatible(CS, F) :- case_name(CS), flashback_name(F).
compatible(R, F) :- reconciliation_name(R), flashback_name(F).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CREWS:
        lines.append(asp.fact("crew_name", cid))
    for cid in CASES:
        lines.append(asp.fact("case_name", cid))
    for fid in FLASHBACKS:
        lines.append(asp.fact("flashback_name", fid))
    for rid in RECONCILIATIONS:
        lines.append(asp.fact("reconciliation_name", rid))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_story_count() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    return len(asp.atoms(model, "valid_story"))

def asp_verify() -> int:
    py = len(list(valid_combos()))
    cl = asp_valid_story_count()
    if py == cl:
        print(f"OK: ASP and Python agree on {py} valid story combinations.")
        return 0
    print(f"MISMATCH: Python={py}, ASP={cl}")
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos():
    for s in SETTINGS:
        for c in CREWS:
            for cs in CASES:
                for f in FLASHBACKS:
                    for r in RECONCILIATIONS:
                        yield (s, c, cs, f, r)

def validate_choice(setting: str, crew: str, case: str, flashback: str, reconciliation: str) -> None:
    if setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {setting}")
    if crew not in CREWS:
        raise StoryError(f"Unknown crew: {crew}")
    if case not in CASES:
        raise StoryError(f"Unknown case: {case}")
    if flashback not in FLASHBACKS:
        raise StoryError(f"Unknown flashback: {flashback}")
    if reconciliation not in RECONCILIATIONS:
        raise StoryError(f"Unknown reconciliation: {reconciliation}")


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------

def choose_name(rng: random.Random) -> str:
    return rng.choice(NAMES)

def choose_detective(rng: random.Random) -> str:
    return rng.choice(DETECTIVE_NAMES)

def choose_trait(rng: random.Random) -> str:
    return rng.choice(TRAITS)

def setting_line(setting: Setting) -> str:
    return f"{setting.detail} lay quiet under the sky, where the apple trees kept their silver leaves."

def intro_line(crew: Crew, crew_member: str, trait: str, detective: str) -> str:
    return (
        f"{crew_member} was a {trait} member of the {crew.role}, and {detective} came to the orchard "
        f"with a careful eye and a soft cloak."
    )

def case_line(case: Case) -> str:
    return f"That night, the crew found trouble: {case.threat}."

def flashback_line(flash: Flashback, detective: str) -> str:
    return f"In a flashback, everyone remembered that {flash.memory} {detective} had once carried that memory like a hidden stone."

def reconciliation_line(rec: Reconciliation, detective: str) -> str:
    return (
        f"At last, {rec.act}. Then {detective} offered {rec.gift}, and {rec.bond}."
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    crew = CREWS[params.crew]
    case = CASES[params.case]
    flash = FLASHBACKS[params.flashback]
    rec = RECONCILIATIONS[params.reconciliation]

    w = World(setting)
    detective = w.add(Entity(id="detective", kind="character", type="detective", label=params.detective))
    member = w.add(Entity(id="crew_member", kind="character", type="crew", label=params.crew_member))
    apple = w.add(Entity(id="apple", kind="thing", type="apple", label="apple", phrase="a bright orchard apple"))

    apple.meters["value"] = 1.0
    member.memes["worry"] = 1.0
    detective.memes["focus"] = 1.0

    w.facts.update(
        setting=setting,
        crew=crew,
        case=case,
        flashback=flash,
        reconciliation=rec,
        detective=detective,
        member=member,
        apple=apple,
    )

    w.say(f"Long ago, {crew.name} swore {crew.vow}.")
    w.say(setting_line(setting))
    w.say(intro_line(crew, params.crew_member, params.trait, params.detective))
    w.para()
    w.say(case_line(case))
    w.say(f"{params.detective} studied {case.clue}, and {params.crew_member} feared a blame that would split the crew.")
    w.para()
    w.say(flashback_line(flash, params.detective))
    w.say(f"That memory changed the meaning of the clues; the stern face was not anger, only the weight of old duty.")
    w.para()
    w.say(reconciliation_line(rec, params.detective))
    w.say(f"In the end, the apple was safe, the crew's hearts were eased, and the orchard felt whole again.")
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mythic story about an apple crew and a detective in {f["setting"].place}, with a flashback that changes the meaning of the clues.',
        f"Tell a gentle legend where {f['detective'].label} investigates {f['case'].label} and the crew learns the truth through a flashback.",
        f"Write a short myth-like tale about apples, a careful detective, and a reconciliation that repairs trust.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    setting: Setting = f["setting"]
    crew: Crew = f["crew"]
    case: Case = f["case"]
    flash: Flashback = f["flashback"]
    rec: Reconciliation = f["reconciliation"]
    detective: Entity = f["detective"]
    member: Entity = f["member"]

    return [
        QAItem(
            question=f"Where did the story happen?",
            answer=f"It happened in {setting.place}, {setting.detail.lower()}.",
        ),
        QAItem(
            question=f"What trouble did the apple crew find?",
            answer=f"They found {case.threat}, which made the crew worry until the detective studied the clues.",
        ),
        QAItem(
            question=f"What was revealed in the flashback?",
            answer=f"The flashback showed that {flash.memory.lower()} The memory explained why the detective seemed so serious.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended in reconciliation: {rec.act}, and that meant {rec.bond}.",
        ),
        QAItem(
            question=f"Who was the detective helping?",
            answer=f"{detective.label} was helping the {crew.role}, especially {member.label}, who had feared the orchard mystery.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective?",
            answer="A detective is someone who looks for clues and tries to solve a mystery.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a story moment that shows something from before, so the listener understands the present better.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people make peace after a disagreement and trust starts to return.",
        ),
        QAItem(
            question="Why are apples often picked carefully?",
            answer="Apples are often picked carefully so they do not bruise, crack, or fall and spoil.",
        ),
    ]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic apple-crew detective story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--crew", choices=CREWS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--flashback", choices=FLASHBACKS)
    ap.add_argument("--reconciliation", choices=RECONCILIATIONS)
    ap.add_argument("--detective")
    ap.add_argument("--crew-member")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    crew = args.crew or rng.choice(list(CREWS))
    case = args.case or rng.choice(list(CASES))
    flashback = args.flashback or rng.choice(list(FLASHBACKS))
    reconciliation = args.reconciliation or rng.choice(list(RECONCILIATIONS))
    validate_choice(setting, crew, case, flashback, reconciliation)
    return StoryParams(
        setting=setting,
        crew=crew,
        case=case,
        flashback=flashback,
        reconciliation=reconciliation,
        detective=args.detective or choose_detective(rng),
        crew_member=args.crew_member or choose_name(rng),
        trait=args.trait or choose_trait(rng),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/5."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} valid stories")
        for v in vals[:20]:
            print(v)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for s in SETTINGS:
            for c in CREWS:
                for cs in CASES:
                    for f in FLASHBACKS:
                        for r in RECONCILIATIONS:
                            params = StoryParams(
                                setting=s,
                                crew=c,
                                case=cs,
                                flashback=f,
                                reconciliation=r,
                                detective="Detective Rowan",
                                crew_member="Arin",
                                trait="steadfast",
                            )
                            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
