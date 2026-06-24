#!/usr/bin/env python3
"""
A small myth-like story world about an archeologic expedition, a disputed possession,
and a dismal omen that turns into suspense before the final recovery.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "priestess"}
        male = {"boy", "man", "father", "king", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Site:
    place: str = "the buried temple"
    dismal: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    type: str
    powers: set[str] = field(default_factory=set)
    owner_kind: str = "none"


@dataclass
class StoryParams:
    site: str
    relic: str
    seeker: str
    seeker_type: str
    keeper: str
    tone: str
    seed: Optional[int] = None


class World:
    def __init__(self, site: Site) -> None:
        self.site = site
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy as _copy
        w = World(self.site)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _r_foreshadow(world: World) -> list[str]:
    out: list[str] = []
    omen = world.facts.get("omen")
    relic = world.facts.get("relic")
    if omen and relic:
        sig = ("foreshadow", omen.id, relic.id)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append(
                f"The old stones seemed to whisper that {omen.label} would matter before the night was done."
            )
    return out


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    seeker = world.facts.get("seeker")
    relic = world.facts.get("relic")
    if seeker and relic and seeker.memes.get("dread", 0) > 0 and seeker.memes.get("hope", 0) > 0:
        sig = ("suspense", seeker.id, relic.id)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append(
                f"{seeker.id} paused with a held breath, one hand on the door and one thought on {relic.label}."
            )
    return out


def _r_possession(world: World) -> list[str]:
    out: list[str] = []
    relic = world.facts.get("relic")
    seeker = world.facts.get("seeker")
    keeper = world.facts.get("keeper")
    if not relic or not seeker or not keeper:
        return out
    if relic.held_by != seeker.id:
        return out
    sig = ("possession", relic.id, seeker.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    seeker.memes["claim"] = seeker.memes.get("claim", 0) + 1
    keeper.memes["loss"] = keeper.memes.get("loss", 0) + 1
    out.append(
        f"{seeker.id} felt the relic choose a new keeper, though {keeper.id} still called it theirs."
    )
    return out


RULES = [_r_foreshadow, _r_suspense, _r_possession]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(site: Site, relic: Relic, seeker_name: str, seeker_type: str, keeper_type: str, tone: str) -> World:
    world = World(site)
    seeker = world.add(Entity(id=seeker_name, kind="character", type=seeker_type))
    keeper = world.add(Entity(id="Keeper", kind="character", type=keeper_type, label="the keeper"))
    omen = world.add(Entity(id="Omen", kind="thing", type="thing", label="a cracked lantern", phrase="a cracked lantern"))
    relic_ent = world.add(Entity(id=relic.id, kind="thing", type=relic.type, label=relic.label, phrase=relic.phrase, owner=keeper.id))

    world.facts.update(seeker=seeker, keeper=keeper, omen=omen, relic=relic_ent, tone=tone, site=site, relic_cfg=relic)

    seeker.memes["hope"] = 1
    keeper.memes["dread"] = 1
    world.say(
        f"In the {tone} days, {seeker.id} came to {site.place}, a place of buried kings and listening dust."
    )
    world.say(
        f"{seeker.id} sought {relic.phrase}, while {keeper.id} guarded it as an ancient possession."
    )
    world.say(
        f"Near the entrance, {omen.label} leaned against a stone and threw a dismal light over the steps."
    )
    propagate(world, narrate=True)

    world.para()
    seeker.memes["dread"] = seeker.memes.get("dread", 0) + 1
    world.say(
        f"Still, {seeker.id} went deeper, and each fallen pebble made the silence feel heavier."
    )
    world.say(
        f"When the inner chamber opened, {seeker.id} reached for {relic.label}, but {keeper.id} cried out that it was theirs."
    )
    relic_ent.held_by = seeker.id
    propagate(world, narrate=True)

    world.para()
    seeker.memes["hope"] += 1
    keeper.memes["dread"] += 1
    world.say(
        f"Then {seeker.id} saw the mark of the old oath on the wall, and the warning in the stones became clear."
    )
    world.say(
        f"{seeker.id} did not run. Instead, {seeker.id} held the relic high and promised to carry it home without breaking the vow."
    )
    if relic_ent.held_by == seeker.id:
        keeper.memes["loss"] = 0
        keeper.memes["peace"] = 1
        world.say(
            f"{keeper.id} bowed, and the chamber softened from dread to awe as the relic was placed where both could see it."
        )
        world.say(
            f"By dawn, the possession was no longer a quarrel; it had become a shared memory beneath the ancient sky."
        )
    return world


SETTINGS = {
    "temple": Site(place="the buried temple", dismal=True, affords={"excavation", "recovery"}),
    "cave": Site(place="the echoing cave shrine", dismal=True, affords={"excavation", "recovery"}),
    "crypt": Site(place="the royal crypt", dismal=True, affords={"excavation", "recovery"}),
}

RELICS = {
    "idol": Relic(id="idol", label="the sun idol", phrase="a sun idol of polished stone", type="idol", powers={"blessing"}),
    "crown": Relic(id="crown", label="the moon crown", phrase="a moon crown of silver leaves", type="crown", powers={"rightful"}),
    "tablet": Relic(id="tablet", label="the oath tablet", phrase="an oath tablet carved with old signs", type="tablet", powers={"vow"}),
}

SEEKERS = ["Nia", "Ivo", "Mara", "Kian", "Sela", "Taro"]
KEEPERS = ["priest", "priestess", "guard", "queen", "king"]
TONE_WORDS = ["mythic", "ancient", "silent", "gray", "windy"]


def valid_combos() -> list[tuple[str, str]]:
    return [(s, r) for s in SETTINGS for r in RELICS]


@dataclass
class _AspModel:
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Myth-like archeologic story world with possession, foreshadowing, and suspense.")
    ap.add_argument("--site", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--seeker")
    ap.add_argument("--seeker-type", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--keeper", choices=KEEPERS)
    ap.add_argument("--tone", choices=TONE_WORDS)
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
    site = args.site or rng.choice(list(SETTINGS))
    relic = args.relic or rng.choice(list(RELICS))
    seeker_type = args.seeker_type or rng.choice(["girl", "boy", "woman", "man"])
    if args.seeker:
        seeker = args.seeker
    else:
        seeker = rng.choice(SEEKERS)
    keeper = args.keeper or rng.choice(KEEPERS)
    tone = args.tone or rng.choice(TONE_WORDS)
    return StoryParams(site=site, relic=relic, seeker=seeker, seeker_type=seeker_type, keeper=keeper, tone=tone)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.site], RELICS[params.relic], params.seeker, params.seeker_type, params.keeper, params.tone)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth about an archeologic journey in {f["site"].place} that hints at {f["relic"].label}.',
        f"Tell a suspenseful story where {f['seeker'].id} and {f['keeper'].id} argue over an old possession in a dismal place.",
        f'Write a child-friendly myth that uses the words "archeologic", "possession", and "foreshadowing".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    seeker = f["seeker"]
    keeper = f["keeper"]
    relic = f["relic"]
    return [
        QAItem(
            question=f"What did {seeker.id} want to find in {f['site'].place}?",
            answer=f"{seeker.id} wanted to find {relic.phrase} in {f['site'].place}.",
        ),
        QAItem(
            question=f"Why did the story feel dismal at the start?",
            answer=f"It felt dismal because the place was old, quiet, and full of shadow, and even {f['omen'].label} made the path feel lonely.",
        ),
        QAItem(
            question=f"What caused the suspense in the inner chamber?",
            answer=f"The suspense came when {seeker.id} reached for {relic.label} and {keeper.id} said it was theirs, so everyone had to wait and see what would happen next.",
        ),
        QAItem(
            question=f"How did the possession problem end?",
            answer=f"It ended when {seeker.id} promised to carry {relic.label} carefully and let both sides honor the old vow.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does archeologic mean?",
            answer="Archeologic means related to studying old things left by people from long ago, like ruins, bones, pots, or carved stones.",
        ),
        QAItem(
            question="What is possession?",
            answer="Possession means having something as yours or keeping it with you.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue that hints at what may happen later in a story.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the tense feeling you get when you are waiting to learn what will happen next.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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
    out = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        out.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
site(S) :- setting(S).
relic(R) :- relic_cfg(R).
foreshadow(S,R) :- site(S), relic(R).
suspense(X,R) :- seeker(X), relic(R), longing(X), warning(R).
possession(X,R) :- seeker(X), relic(R), held_by(R,X).
#show foreshadow/2.
#show suspense/2.
#show possession/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for r in RELICS:
        lines.append(asp.fact("relic_cfg", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show site/1.\n#show relic/1."))
    return sorted(set(asp.atoms(model, "site"))) + sorted(set(asp.atoms(model, "relic")))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show foreshadow/2.\n#show suspense/2.\n#show possession/2."))
    if model is None:
        print("No ASP model.")
        return 1
    print("OK: ASP program solved.")
    return 0


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
    StoryParams(site="temple", relic="idol", seeker="Nia", seeker_type="girl", keeper="priest", tone="mythic"),
    StoryParams(site="cave", relic="tablet", seeker="Kian", seeker_type="boy", keeper="guard", tone="ancient"),
    StoryParams(site="crypt", relic="crown", seeker="Mara", seeker_type="woman", keeper="queen", tone="gray"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show foreshadow/2.\n#show suspense/2.\n#show possession/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
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
