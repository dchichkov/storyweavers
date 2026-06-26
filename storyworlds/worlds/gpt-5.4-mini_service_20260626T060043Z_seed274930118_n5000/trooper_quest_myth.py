#!/usr/bin/env python3
"""
Standalone storyworld: trooper quest myth.

A small classical simulation in a mythic style:
- A trooper is sent on a Quest.
- The Quest risks a sacred token or banner.
- A wise guide predicts danger, offers a fitting charm, and the trooper completes the Quest.

This file is self-contained apart from the shared ``storyworlds/results.py`` and
optional ``storyworlds/asp.py`` helper.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dust": 0.0, "tired": 0.0, "safe": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "fear": 0.0, "duty": 0.0, "pride": 0.0, "calm": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "priestess"}
        male = {"boy", "father", "man", "king", "trooper"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    mythic: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    name: str
    verb: str
    gerund: str
    rush: str
    danger: str
    risk_kind: str
    zone: set[str]
    blessed_by: str
    keyword: str = "Quest"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Charm:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

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
        return any(e.protective and region in e.covers for e in self.worn_items(actor))

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
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_dust(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("dust", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("dust", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dust"] = item.meters.get("dust", 0.0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} gathered dust.")
    return out


def _r_tired(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("tired", 0.0) < THRESHOLD:
            continue
        sig = ("tired", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["calm"] += 1
        out.append(f"{actor.pronoun('subject').capitalize()} steadied {actor.pronoun('object')}self and breathed slowly.")
    return out


def _r_blessed(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("hope", 0.0) < THRESHOLD or actor.memes.get("duty", 0.0) < THRESHOLD:
            continue
        sig = ("blessed", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["safe"] += 1
        out.append("__blessed__")
    return out


CAUSAL_RULES = [_r_dust, _r_tired, _r_blessed]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__blessed__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def risk_present(quest: Quest, prize: Prize) -> bool:
    return prize.region in quest.zone


def select_charm(quest: Quest, prize: Prize) -> Optional[Charm]:
    for charm in CHARMS:
        if quest.risk_kind in charm.guards and prize.region in charm.covers:
            return charm
    return None


def predict_loss(world: World, hero: Entity, quest: Quest, prize_id: str) -> dict:
    sim = world.copy()
    _do_quest(sim, sim.get(hero.id), quest, narrate=False)
    prize = sim.get(prize_id)
    return {
        "dusty": bool(prize and prize.meters.get("dust", 0.0) >= THRESHOLD),
        "safe": bool(hero.meters.get("safe", 0.0) >= THRESHOLD),
    }


def _do_quest(world: World, hero: Entity, quest: Quest, narrate: bool = True) -> None:
    if quest.id not in world.setting.affords:
        return
    world.zone = set(quest.zone)
    hero.meters["dust"] = hero.meters.get("dust", 0.0) + 1
    hero.meters["tired"] = hero.meters.get("tired", 0.0) + 1
    hero.memes["hope"] += 1
    hero.memes["duty"] += 1
    propagate(world, narrate=narrate)


def announce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "brave")
    world.say(
        f"{hero.id} was a little {trait} trooper who listened for omens at dawn."
    )


def speak_of_quest(world: World, hero: Entity, quest: Quest) -> None:
    world.say(
        f"{hero.pronoun('subject').capitalize()} loved the {quest.name} and longed to {quest.verb}."
    )


def give_prize(world: World, guide: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"Before the road opened, {guide.label} placed {hero.pronoun('object')} {prize.phrase}."
    )
    prize.worn_by = hero.id


def depart(world: World, hero: Entity, guide: Entity, quest: Quest) -> None:
    world.say(
        f"One evening, {hero.id} and {guide.label} went to {world.setting.place}, "
        f"where {world.setting.mythic} waited like a secret song."
    )
    world.say(f"{hero.id} wanted to {quest.verb}, but the path was steep and shadowed.")


def warn(world: World, guide: Entity, hero: Entity, quest: Quest, prize: Entity) -> bool:
    pred = predict_loss(world, hero, quest, prize.id)
    if not pred["dusty"]:
        return False
    world.facts["predicted_risk"] = quest.danger
    world.say(
        f'"If you rush ahead, {hero.id}, your {prize.label} will get {quest.danger}," '
        f"{guide.label} said. \"A Quest should be chosen with care.\""
    )
    return True


def resist(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["fear"] += 1
    world.say(
        f"{hero.id} felt the warning in {hero's if False else ''}"
    )

def stubborn_step(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["fear"] += 1
    world.say(f"{hero.id} frowned, then tried to {quest.rush} anyway.")


def touch_guidance(world: World, guide: Entity, hero: Entity) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"But {guide.label} took {hero.pronoun('possessive')} hand and pointed at the lantern road."
    )


def accept_charm(world: World, guide: Entity, hero: Entity, quest: Quest, prize: Entity) -> Optional[Charm]:
    charm_def = select_charm(quest, prize)
    if charm_def is None:
        return None
    charm = world.add(Entity(
        id=charm_def.id,
        type="charm",
        label=charm_def.label,
        owner=hero.id,
        caretaker=guide.id,
        protective=True,
        covers=set(charm_def.covers),
        plural=charm_def.plural,
    ))
    charm.worn_by = hero.id
    if predict_loss(world, hero, quest, prize.id)["dusty"]:
        charm.worn_by = None
        del world.entities[charm.id]
        return None
    world.say(
        f'"How about we {charm_def.prep}?" {guide.label} asked. '
        f"{hero.id} nodded, and the new charm glimmered."
    )
    return charm_def


def resolve(world: World, guide: Entity, hero: Entity, quest: Quest, prize: Entity, charm_def: Charm) -> None:
    hero.memes["fear"] = 0.0
    hero.memes["calm"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} smiled and accepted the path. They {charm_def.tail}."
    )
    world.say(
        f"At last {hero.id} was {quest.gerund}, {prize.label} stayed clean, "
        f"and the stars looked as if they had opened a doorway."
    )


def tell(setting: Setting, quest: Quest, prize_cfg: Prize, hero_name: str, guide_name: str, hero_trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type="trooper",
        traits=["little", hero_trait, "steadfast"],
    ))
    guide = world.add(Entity(
        id=guide_name,
        kind="character",
        type="sage",
        label="the guide",
    ))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=guide.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    announce(world, hero)
    speak_of_quest(world, hero, quest)
    give_prize(world, guide, hero, prize)
    world.para()
    depart(world, hero, guide, quest)
    warn(world, guide, hero, quest, prize)
    stubborn_step(world, hero, quest)
    touch_guidance(world, guide, hero)
    world.para()
    charm_def = accept_charm(world, guide, hero, quest, prize)
    if charm_def:
        resolve(world, guide, hero, quest, prize, charm_def)
    world.facts.update(
        hero=hero, guide=guide, prize=prize, quest=quest, charm=charm_def,
        resolved=charm_def is not None,
        setting=setting,
    )
    return world


SETTINGS = {
    "ridge": Setting(place="the ridge", mythic="old thunder and silver wind", affords={"quest"}),
    "grove": Setting(place="the grove", mythic="green fire under the roots", affords={"quest"}),
    "gate": Setting(place="the gate of dawn", mythic="a bronze bell that never slept", affords={"quest"}),
}

QUESTS = {
    "quest": Quest(
        id="quest",
        name="Quest",
        verb="take the sacred road",
        gerund="walking the sacred road",
        rush="charge down the sacred road",
        danger="dusty",
        risk_kind="dust",
        zone={"torso", "hands"},
        blessed_by="dawn",
        keyword="Quest",
        tags={"quest", "myth"},
    )
}

PRIZES = {
    "cloak": Prize(label="cloak", phrase="a lantern-blue cloak", type="cloak", region="torso"),
    "banner": Prize(label="banner", phrase="a bright banner", type="banner", region="hands", plural=False),
    "helm": Prize(label="helm", phrase="a bronze helm", type="helm", region="head"),
}

CHARMS = [
    Charm(id="dust_cloak", label="a moon-dust cloak", covers={"torso"}, guards={"dust"}, prep="wrap the cloak around you", tail="wrapped the moon-dust cloak around the trooper"),
    Charm(id="lantern_band", label="a lantern band", covers={"hands"}, guards={"dust"}, prep="tie on a lantern band first", tail="tied on the lantern band first"),
    Charm(id="ash_scarf", label="an ash scarf", covers={"torso", "hands"}, guards={"dust"}, prep="wear an ash scarf and keep the banner tucked close", tail="wore the ash scarf and kept faith with the banner"),
]

HERO_NAMES = ["Ari", "Bren", "Cleo", "Dax", "Eira", "Finn"]
GUIDE_NAMES = ["Mara", "Oren", "Iris", "Talan"]
TRAITS = ["bold", "quiet", "steadfast", "bright", "patient"]


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    hero: str
    guide: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for qid in setting.affords:
            q = QUESTS[qid]
            for pid, prize in PRIZES.items():
                if risk_present(q, prize) and select_charm(q, prize):
                    out.append((place, qid, pid))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, guide, quest, prize = f["hero"], f["guide"], f["quest"], f["prize"]
    return [
        f'Write a mythic story for a child about a trooper named {hero.id} and a {quest.keyword}.',
        f"Tell a gentle quest tale where {hero.id} wants to {quest.verb} but {guide.label} worries about {prize.phrase}.",
        f'Write a short myth with the word "{quest.keyword}" that ends with a safer way to travel.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, guide, quest, prize = f["hero"], f["guide"], f["quest"], f["prize"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little trooper, and {guide.label}, who helps on the Quest.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do on the Quest?",
            answer=f"{hero.id} wanted to {quest.verb} on the Quest.",
        ),
        QAItem(
            question=f"Why did {guide.label} worry about {prize.label}?",
            answer=f"{guide.label} worried because the road would make {prize.label} get {quest.danger}.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did the trooper keep {prize.label} safe?",
                answer=f"They used {f['charm'].label} so {prize.label} stayed clean while {hero.id} followed the Quest.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a Quest?",
            answer="A Quest is a special journey with a goal, usually brave, serious, and full of meaning.",
        ),
        QAItem(
            question="What does a trooper do?",
            answer="A trooper is a soldier or traveler who keeps going even when the road is hard.",
        ),
        QAItem(
            question="What does a charm do in a myth?",
            answer="A charm is a special object or sign that helps protect someone on a dangerous road.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = [f"kind={e.kind}", f"type={e.type}"]
        if e.label:
            bits.append(f"label={e.label}")
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append("  " + e.id + " " + " ".join(bits))
    return "\n".join(lines)


ASP_RULES = r"""
risk(A,P) :- zone(A,R), region(P,R).
fix(A,P) :- risk(A,P), charm(C), guards(C,M), riskkind(A,M), covers(C,R), region(P,R).
valid(Place,A,P) :- affords(Place,A), risk(A,P), fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("riskkind", qid, q.risk_kind))
        for r in sorted(q.zone):
            lines.append(asp.fact("zone", qid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    for c in CHARMS:
        lines.append(asp.fact("charm", c.id))
        for g in sorted(c.guards):
            lines.append(asp.fact("guards", c.id, g))
        for r in sorted(c.covers):
            lines.append(asp.fact("covers", c.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def explain_rejection(quest: Quest, prize: Prize) -> str:
    if not risk_present(quest, prize):
        return f"(No story: the Quest would not reach the {prize.label}, so there is no honest danger.)"
    return f"(No story: no charm in this world can protect a {prize.label} from this Quest.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic trooper on a Quest.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--guide")
    ap.add_argument("--trait")
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
    if args.quest and args.prize:
        q, p = QUESTS[args.quest], PRIZES[args.prize]
        if not (risk_present(q, p) and select_charm(q, p)):
            raise StoryError(explain_rejection(q, p))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, prize = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HERO_NAMES)
    guide = args.guide or rng.choice(GUIDE_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, prize=prize, hero=hero, guide=guide, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], QUESTS[params.quest], PRIZES[params.prize], params.hero, params.guide, params.trait)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        triples = sorted(set(asp.atoms(model, "valid")))
        for t in triples:
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in [
            StoryParams(place="ridge", quest="quest", prize="cloak", hero="Ari", guide="Mara", trait="steadfast"),
            StoryParams(place="grove", quest="quest", prize="banner", hero="Cleo", guide="Iris", trait="bright"),
            StoryParams(place="gate", quest="quest", prize="helm", hero="Bren", guide="Oren", trait="patient"),
        ]:
            samples.append(generate(p))
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
