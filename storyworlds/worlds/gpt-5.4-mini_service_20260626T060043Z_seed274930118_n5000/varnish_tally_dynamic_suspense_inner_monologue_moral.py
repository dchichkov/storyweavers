#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/varnish_tally_dynamic_suspense_inner_monologue_moral.py
=============================================================================================================

A myth-leaning story world about a child of the shrine, a sacred tally, and the
temptation to varnish what should stay true.

The seed words are woven through the domain:
- varnish
- tally
- dynamic

Story shape:
- a young keeper serves at a mountain shrine
- a sudden need creates suspense
- the keeper has an inner monologue about duty and pride
- a moral value is named in the resolution

The generated stories are small, classical, and state-driven: a ritual object can
be protected or ruined, an elder can foresee the risk, and the ending proves
what changed.
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
# World model
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    mood: str
    dangers: set[str] = field(default_factory=set)


@dataclass
class Rite:
    id: str
    verb: str
    gerund: str
    rush: str
    danger: str
    zone: str
    omen: str
    keyword: str


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    sacred: bool = True


@dataclass
class Remedy:
    id: str
    label: str
    method: str
    safe_for: set[str]
    helps: set[str]


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    zone: str = ""

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = self.zone
        return clone


THRESHOLD = 1.0


def meter(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def meme(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def bump_meter(entity: Entity, key: str, amt: float = 1.0) -> None:
    entity.meters[key] = meter(entity, key) + amt


def bump_meme(entity: Entity, key: str, amt: float = 1.0) -> None:
    entity.memes[key] = meme(entity, key) + amt


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "shrine": Setting(place="the high shrine", mood="mythic", dangers={"storm"}),
    "temple": Setting(place="the river temple", mood="solemn", dangers={"flood"}),
    "grove": Setting(place="the moon grove", mood="listening", dangers={"wind"}),
}

RITES = {
    "varnish_tally": Rite(
        id="varnish_tally",
        verb="varnish the tally board",
        gerund="varnishing the tally board",
        rush="hurry to coat the tally board with resin",
        danger="the sacred marks would blur",
        zone="hands",
        omen="The resin glowed like amber under lantern-light.",
        keyword="varnish",
    ),
    "clean_tally": Rite(
        id="clean_tally",
        verb="polish the tally marks",
        gerund="polishing the tally marks",
        rush="rush to wipe the tally marks clean",
        danger="the old soot would hide the count",
        zone="hands",
        omen="The cloth shone bright as a river stone.",
        keyword="tally",
    ),
    "seal_dynamic": Rite(
        id="seal_dynamic",
        verb="seal the dynamic gate",
        gerund="sealing the dynamic gate",
        rush="run to close the shifting gate",
        danger="the gate would swing open to the dark",
        zone="door",
        omen="The hinges sang as if they remembered thunder.",
        keyword="dynamic",
    ),
}

PRIZES = {
    "tally": Prize(
        id="tally",
        label="tally board",
        phrase="the carved tally board of the shrine",
        region="hands",
    ),
    "gate": Prize(
        id="gate",
        label="gate",
        phrase="the shrine gate with bronze hinges",
        region="door",
    ),
}

REMEDIES = {
    "linen_wrap": Remedy(
        id="linen_wrap",
        label="a linen wrap",
        method="wrap the board before any resin touched it",
        safe_for={"tally"},
        helps={"varnish_tally"},
    ),
    "bell_cord": Remedy(
        id="bell_cord",
        label="the bell cord",
        method="tie the gate so it would not swing in the wind",
        safe_for={"gate"},
        helps={"seal_dynamic"},
    ),
}

NAMES = ["Ari", "Mina", "Niko", "Sera", "Tavi", "Lena", "Jori", "Ila"]
GROWNUPS = ["elder", "priest", "priestess", "guardian"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def prize_at_risk(rite: Rite, prize: Prize) -> bool:
    return rite.zone == prize.region or (rite.id == "varnish_tally" and prize.id == "tally")


def select_remedy(rite: Rite, prize: Prize) -> Optional[Remedy]:
    for rem in REMEDIES.values():
        if prize.id in rem.safe_for and rite.id in rem.helps:
            return rem
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for rite in RITES.values():
            for prize in PRIZES.values():
                if prize_at_risk(rite, prize) and select_remedy(rite, prize):
                    out.append((place, rite.id, prize.id))
    return sorted(out)


def explain_rejection(rite: Rite, prize: Prize) -> str:
    return (
        f"(No story: {rite.verb} does not have a believable remedy for {prize.label}. "
        f"The myth needs a real danger and a real way to answer it.)"
    )


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------
def predict_ruin(world: World, hero: Entity, rite: Rite, prize: Prize) -> bool:
    sim = world.copy()
    do_rite(sim, hero, rite, narrate=False)
    target = sim.get(prize.id)
    return meter(target, "ruined") >= THRESHOLD or meter(target, "blurred") >= THRESHOLD


def do_rite(world: World, hero: Entity, rite: Rite, narrate: bool = True) -> None:
    world.zone = rite.zone
    bump_meme(hero, "desire")
    bump_meter(hero, rite.keyword)
    if rite.id == "varnish_tally":
        board = world.get("tally")
        bump_meter(board, "gloss")
        bump_meter(board, "blurred", 1.0)
    elif rite.id == "clean_tally":
        board = world.get("tally")
        bump_meter(board, "clean", 1.0)
    elif rite.id == "seal_dynamic":
        gate = world.get("gate")
        bump_meter(gate, "secure", 1.0)
        bump_meter(gate, "ruined", 0.0)

    if narrate:
        world.say(rite.omen)


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a young keeper at {world.setting.place}, where the lamps "
        f"never quite went out and the old stories still listened."
    )


def longing(world: World, hero: Entity, rite: Rite) -> None:
    bump_meme(hero, "wonder")
    world.say(
        f"{hero.pronoun().capitalize()} loved the rite of {rite.gerund}, because it "
        f"made the shrine feel alive and watched over."
    )


def setup_relic(world: World, hero: Entity, prize: Prize) -> None:
    relic = world.get(prize.id)
    bump_meme(hero, "duty")
    world.say(
        f"Each dawn, {hero.id} counted the carved notches on {relic.label} and "
        f"carried {relic.phrase} as carefully as a prayer."
    )


def suspense_warning(world: World, elder: Entity, hero: Entity, rite: Rite, prize: Prize) -> bool:
    if not predict_ruin(world, hero, rite, prize):
        return False
    bump_meme(elder, "concern")
    world.facts["risk"] = rite.danger
    world.say(
        f'"Wait," {elder.id} said, eyes narrowed at the darkening sky. '
        f'"If you {rite.verb}, then {rite.danger}."'
    )
    return True


def inner_monologue(world: World, hero: Entity, rite: Rite, prize: Prize) -> None:
    bump_meme(hero, "doubt")
    bump_meme(hero, "fear")
    world.say(
        f"{hero.id} stood very still. In {hero.pronoun('possessive')} heart, a small voice said, "
        f"Maybe the elders are too cautious. Maybe the resin will make it beautiful. "
        f"But another voice answered, If the marks blur, the village will lose its count."
    )


def tension(world: World, hero: Entity, rite: Rite) -> None:
    bump_meme(hero, "suspense")
    world.say(
        f"Beyond the shrine wall, thunder rolled once, then paused, as if the world itself "
        f"were holding its breath."
    )
    world.say(
        f"{hero.id} reached toward the workbench anyway, fingers trembling above the bowl of resin."
    )


def offer_remedy(world: World, elder: Entity, hero: Entity, rite: Rite, prize: Prize) -> Optional[Remedy]:
    rem = select_remedy(rite, prize)
    if not rem:
        return None
    world.say(
        f"{elder.id} touched {hero.pronoun('possessive')} shoulder and said, "
        f'"Let us use {rem.label} first; the old way is not always the wisest way."'
    )
    world.say(f"It would {rem.method}.")
    return rem


def accept_remedy(world: World, hero: Entity, elder: Entity, rite: Rite, prize: Prize, rem: Remedy) -> None:
    bump_meme(hero, "resolve")
    bump_meme(hero, "duty")
    hero.memes["doubt"] = 0.0
    world.say(
        f"{hero.id} breathed out and nodded. {hero.pronoun().capitalize()} chose duty over pride, "
        f"and wrapped the board before any resin touched it."
    )
    if rite.id == "seal_dynamic":
        world.say(
            f"Together they tied the bell cord and kept the dynamic gate steady until the storm passed."
        )
    else:
        world.say(
            f"Then {hero.id} varnished only the frame, so the sacred tally stayed clear while the wood was protected."
        )
    world.say(
        f"In the end, the shrine remained faithful, and the work shone with patience instead of haste."
    )


def moral(world: World) -> None:
    world.say(
        f"The moral value was simple: reverence is stronger than vanity, and careful hands "
        f"guard old truths better than hurried hands do."
    )


def tell(setting: Setting, rite: Rite, prize: Prize, hero_name: str, elder_role: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl", label=hero_name))
    elder = world.add(Entity(id=elder_role, kind="character", type=elder_role, label=f"the {elder_role}"))
    world.add(Entity(id=prize.id, kind="thing", type=prize.id, label=prize.label, phrase=prize.phrase, caretaker=elder.id))

    introduce(world, hero)
    longing(world, hero, rite)
    setup_relic(world, hero, prize)
    world.para()

    suspense_warning(world, elder, hero, rite, prize)
    inner_monologue(world, hero, rite, prize)
    tension(world, hero, rite)
    world.para()

    rem = offer_remedy(world, elder, hero, rite, prize)
    if rem:
        accept_remedy(world, hero, elder, rite, prize, rem)
    moral(world)

    world.facts.update(hero=hero, elder=elder, prize=prize, rite=rite, setting=setting, remedy=rem)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    rite = f["rite"]
    prize = f["prize"]
    return [
        f'Write a short myth for children that includes the word "{rite.keyword}" and the idea of a sacred count.',
        f"Tell a suspenseful shrine story where {hero.id} wants to {rite.verb} but fears ruining {prize.phrase}.",
        f"Write a gentle myth with an inner monologue, a warning, and a moral value about patience.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    rite = f["rite"]
    prize = f["prize"]
    rem = f.get("remedy")
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do at the shrine?",
            answer=f"{hero.id} wanted to {rite.verb}.",
        ),
        QAItem(
            question=f"Why did {elder.id} warn {hero.id}?",
            answer=f"{elder.id} warned {hero.id} because {rite.danger} if the work began at once.",
        ),
        QAItem(
            question=f"What inner thought troubled {hero.id} before the storm?",
            answer=(
                f"{hero.id} worried that the beautiful shine might hide the sacred marks, "
                f"and that would ruin {prize.label}."
            ),
        ),
    ]
    if rem:
        qa.append(
            QAItem(
                question=f"How did the keeper avoid harming {prize.label}?",
                answer=(
                    f"They used {rem.label} first, so the shrine work could continue without blurring "
                    f"the sacred count."
                ),
            )
        )
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is varnish?",
            answer="Varnish is a glossy coating that can protect wood, but it can also hide fine marks if it is used carelessly.",
        ),
        QAItem(
            question="What does a tally do?",
            answer="A tally is a way of keeping count with marks or notches, so people can remember how many things there are.",
        ),
        QAItem(
            question="What does dynamic mean?",
            answer="Dynamic means something changes, moves, or shifts instead of staying still.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts ==", *sample.prompts, "", "== Story QA =="]
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"{ent.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# StoryParams and interface
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    rite: str
    prize: str
    name: str
    elder: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="shrine", rite="varnish_tally", prize="tally", name="Ari", elder="elder"),
    StoryParams(place="temple", rite="clean_tally", prize="tally", name="Mina", elder="priestess"),
    StoryParams(place="grove", rite="seal_dynamic", prize="gate", name="Tavi", elder="guardian"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic story world about a sacred tally, varnish, and a dynamic gate.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--rite", choices=RITES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=GROWNUPS)
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
    if args.rite and args.prize:
        rite, prize = RITES[args.rite], PRIZES[args.prize]
        if not (prize_at_risk(rite, prize) and select_remedy(rite, prize)):
            raise StoryError(explain_rejection(rite, prize))
    choices = [c for c in valid_combos()
               if (args.place is None or c[0] == args.place)
               and (args.rite is None or c[1] == args.rite)
               and (args.prize is None or c[2] == args.prize)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    place, rite, prize = rng.choice(choices)
    return StoryParams(
        place=place,
        rite=rite,
        prize=prize,
        name=args.name or rng.choice(NAMES),
        elder=args.elder or rng.choice(GROWNUPS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], RITES[params.rite], PRIZES[params.prize], params.name, params.elder)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(R,P) :- rite(R), prize(P), zone(R,Z), region(P,Z).
has_remedy(R,P) :- remedy(M), helps(M,R), safe_for(M,P).
valid(Place,R,P) :- setting(Place), rite(R), prize(P), prize_at_risk(R,P), has_remedy(R,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for rid, rite in RITES.items():
        lines.append(asp.fact("rite", rid))
        lines.append(asp.fact("zone", rid, rite.zone))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, prize.region))
    for mid, rem in REMEDIES.items():
        lines.append(asp.fact("remedy", mid))
        for r in rem.helps:
            lines.append(asp.fact("helps", mid, r))
        for p in rem.safe_for:
            lines.append(asp.fact("safe_for", mid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.rite} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
