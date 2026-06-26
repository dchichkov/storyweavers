#!/usr/bin/env python3
"""
storyworlds/worlds/tulip_wipe_dim_bad_ending_cautionary_detective.py
=====================================================================

A small, self-contained story world in a detective-story style.

Premise:
- A careful detective follows a trail in a garden.
- A bright tulip is in danger of being wipe-dimmed: wiped too hard while damp,
  which smudges the color and bends the petals.
- The detective notices clues, but the cautionary turn is that one hasty wipe
  causes a bad ending.

This world is intentionally compact and constraint-checked:
- The only valid story is one where the tulip is at risk from the wipe-dim action.
- The resolution is cautionary rather than triumphant.
- The ending image proves the change in state.
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


THRESHOLD = 1.0


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
    region: str = ""
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "detective"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    outdoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Case:
    id: str
    clue_word: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    warning: str
    keyword: str


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(e.protective and region in e.region for e in self.worn_items(actor))

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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        return clone


def _r_wipe_dim(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("wipe_dim", 0.0) < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.kind != "thing" or item.owner != actor.id:
                continue
            if item.region not in world.zone:
                continue
            if item.protective or world.covered(actor, item.region):
                continue
            sig = ("wipe_dim", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dim"] = item.meters.get("dim", 0.0) + 1
            item.meters["ruined"] = item.meters.get("ruined", 0.0) + 1
            actor.memes["regret"] = actor.memes.get("regret", 0.0) + 1
            out.append(f"The wipe left {item.label} dim and tired.")
    return out


CAUSAL_RULES = [_r_wipe_dim]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting) -> str:
    return f"The {setting.place} was quiet, with damp leaves and a neat path for clues."


def predict_loss(world: World, actor: Entity, case: Case, prize_id: str) -> bool:
    sim = world.copy()
    sim.get(actor.id).meters["wipe_dim"] = 1
    sim.zone = set(case.zone)
    propagate(sim, narrate=False)
    prize = sim.entities[prize_id]
    return prize.meters.get("ruined", 0.0) >= THRESHOLD


def introduce(world: World, detective: Entity) -> None:
    world.say(
        f"{detective.id} was a little detective with a sharp hat, a notebook, and a nose for clues."
    )


def clue_hunt(world: World, detective: Entity, case: Case) -> None:
    detective.memes["curious"] = detective.memes.get("curious", 0.0) + 1
    world.say(
        f"{detective.pronoun().capitalize()} followed the clue word {case.clue_word} through the garden."
    )
    world.say(setting_detail(world.setting))


def show_prize(world: World, detective: Entity, prize: Entity) -> None:
    world.say(
        f"At the edge of the bed stood {prize.phrase}, bright as a tiny lantern."
    )


def warn(world: World, detective: Entity, parent: Entity, case: Case, prize: Entity) -> bool:
    if not predict_loss(world, detective, case, prize.id):
        return False
    world.facts["warning"] = case.warning
    world.say(
        f'"{case.warning}," {parent.pronoun("possessive")} gardener said. '
        f'"A wet wipe can dim the color."'
    )
    return True


def ignore_warning(world: World, detective: Entity, case: Case) -> None:
    detective.memes["stubborn"] = detective.memes.get("stubborn", 0.0) + 1
    world.say(
        f"{detective.pronoun().capitalize()} noticed the warning, but the clue felt urgent."
    )
    world.say(f"{detective.pronoun().capitalize()} tried to {case.rush}.")


def do_wipe(world: World, detective: Entity, case: Case) -> None:
    detective.meters["wipe_dim"] = detective.meters.get("wipe_dim", 0.0) + 1
    world.zone = set(case.zone)
    propagate(world, narrate=True)


def bad_ending(world: World, detective: Entity, prize: Entity, case: Case) -> None:
    if prize.meters.get("ruined", 0.0) < THRESHOLD:
        return
    detective.memes["regret"] = detective.memes.get("regret", 0.0) + 1
    world.say(
        f"When the cloth lifted, {prize.label} had gone dim, and its petals drooped like a sad folded note."
    )
    world.say(
        f"{detective.id} learned the caution the hard way: once a tulip has been wipe-dimmed, the bright shine does not come back."
    )


def tell(setting: Setting, case: Case, prize_cfg: Prize, detective_name: str, helper_name: str) -> World:
    world = World(setting)
    detective = world.add(Entity(id=detective_name, kind="character", type="detective"))
    helper = world.add(Entity(id=helper_name, kind="character", type="gardener", label="the gardener"))
    prize = world.add(Entity(
        id=prize_cfg.id,
        type="flower",
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=helper.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, detective)
    clue_hunt(world, detective, case)
    show_prize(world, detective, prize)

    world.para()
    warn(world, detective, helper, case, prize)
    ignore_warning(world, detective, case)
    do_wipe(world, detective, case)

    world.para()
    bad_ending(world, detective, prize, case)

    world.facts.update(
        detective=detective,
        helper=helper,
        prize=prize,
        case=case,
        setting=setting,
        ruined=prize.meters.get("ruined", 0.0) >= THRESHOLD,
    )
    return world


SETTINGS = {
    "garden": Setting(place="the garden", outdoor=True, affords={"wipe-dim"}),
}

CASES = {
    "wipe-dim": Case(
        id="wipe-dim",
        clue_word="tulip",
        verb="wipe the wet bloom",
        gerund="wiping the wet bloom",
        rush="wipe the bloom clean in a hurry",
        mess="dim",
        soil="dim and dull",
        zone={"flower"},
        warning="Don't wipe a wet tulip too hard",
        keyword="tulip",
    ),
}

PRIZES = {
    "tulip": Prize(
        id="tulip",
        label="tulip",
        phrase="a red tulip with a golden center",
        region="flower",
    ),
}

GEAR = [
    Gear(
        id="soft_cloth",
        label="a soft dry cloth",
        covers={"flower"},
        guards={"dim"},
        prep="use a soft dry cloth instead",
        tail="kept the petals bright",
    ),
]

NAMES = ["Mina", "Jules", "Pip", "Nia", "Toby", "Ben"]
HELPERS = ["the gardener", "the keeper"]
CURIOUS_TRAITS = ["careful", "curious", "patient", "watchful"]


def prize_at_risk(case: Case, prize: Prize) -> bool:
    return prize.region in case.zone


def select_gear(case: Case, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and case.mess in gear.guards:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for case_id in setting.affords:
            case = CASES[case_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(case, prize) and select_gear(case, prize):
                    out.append((place, case_id, prize_id))
    return out


@dataclass
class StoryParams:
    place: str
    case: str
    prize: str
    detective: str
    helper: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective cautionary story world about a wipe-dimmed tulip.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--detective")
    ap.add_argument("--helper")
    ap.add_argument("--trait", choices=CURIOUS_TRAITS)
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
    if args.case and args.prize:
        case = CASES[args.case]
        prize = PRIZES[args.prize]
        if not (prize_at_risk(case, prize) and select_gear(case, prize)):
            raise StoryError("No honest detective story exists for that case and prize.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.case is None or c[1] == args.case)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, case, prize = rng.choice(combos)
    detective = args.detective or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(CURIOUS_TRAITS)
    return StoryParams(place=place, case=case, prize=prize, detective=detective, helper=helper, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for a child featuring a {f["prize"].label} and the clue word "tulip".',
        f'Tell a cautionary story where {f["detective"].id} tries to {f["case"].verb} in the garden, but gets warned not to damage the flower.',
        f'Write a small mystery story that ends with a tulip being wipe-dimmed after a careless mistake.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    prize = f["prize"]
    case = f["case"]
    qa = [
        QAItem(
            question=f"What was {detective.id} trying to do in the garden?",
            answer=f"{detective.id} was trying to {case.verb}.",
        ),
        QAItem(
            question=f"Why did {helper.label} warn {detective.id} about the tulip?",
            answer=f"{helper.label.capitalize()} warned {detective.id} because a wet wipe can dim the tulip's color and bend the petals.",
        ),
        QAItem(
            question=f"What happened to the {prize.label} at the end?",
            answer=f"The {prize.label} was wipe-dimmed, so it ended dim and droopy instead of bright.",
        ),
    ]
    if f.get("ruined"):
        qa.append(
            QAItem(
                question=f"What lesson did {detective.id} learn?",
                answer=f"{detective.id} learned that a child should not hurry to wipe a wet flower, because a quick mistake can make it lose its color.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tulip?",
            answer="A tulip is a flower with petals that can be bright and colorful.",
        ),
        QAItem(
            question="Why should a wet flower be handled gently?",
            answer="A wet flower should be handled gently because rough wiping can bruise petals and make the color look dull.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
        parts = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.region:
            parts.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(C,P) :- case(C), prize(P), zone(C,R), prize_region(P,R).
valid_story(Place,C,P) :- setting(Place), affords(Place,C), at_risk(C,P), has_gear(C,P).
has_gear(C,P) :- gear(G), zone(C,R), prize_region(P,R), covers(G,R), guards(G,M), mess(C,M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for c in sorted(setting.affords):
            lines.append(asp.fact("affords", place, c))
    for cid, case in CASES.items():
        lines.append(asp.fact("case", cid))
        lines.append(asp.fact("mess", cid, case.mess))
        for r in sorted(case.zone):
            lines.append(asp.fact("zone", cid, r))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, prize.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CASES[params.case], PRIZES[params.prize], params.detective, params.helper)
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
    StoryParams(place="garden", case="wipe-dim", prize="tulip", detective="Mina", helper="the gardener", trait="careful")
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combo(s):")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
            header = f"### {p.detective}: {p.case} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
