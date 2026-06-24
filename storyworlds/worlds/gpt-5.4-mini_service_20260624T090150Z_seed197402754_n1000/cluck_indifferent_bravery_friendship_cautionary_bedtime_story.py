#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/cluck_indifferent_bravery_friendship_cautionary_bedtime_story.py
==============================================================================================================

A small bedtime-story world about a sleepy little chick, a cautious night errand,
and a friendship that becomes braver when it is done the safe way.

Seed words:
- cluck
- indifferent

Narrative instruments:
- Bravery
- Friendship
- Cautionary

Style:
- Bedtime Story
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
        for k in ("damp", "muddy", "sleepy"):
            self.meters.setdefault(k, 0.0)
        for k in ("bravery", "friendship", "caution", "indifference", "comfort"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "hen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "rooster"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the moonlit yard"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
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
        return any(item.protective and region in item.covers for item in self.worn_items(actor))

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
        return clone


@dataclass
class Rule:
    name: str
    apply: object


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["damp"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soak", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["damp"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got damp.")
    return out


CAUSAL_RULES = [Rule("soak", _r_soak)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"soiled": prize.meters["damp"] >= THRESHOLD}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError("This setting cannot host that bedtime adventure.")
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["bravery"] += 1
    actor.memes["caution"] += 1
    propagate(world, narrate=narrate)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str,
         hero_type: str, parent_type: str = "hen") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little", "sleepy", "brave"],
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="Mama Hen"))
    friend = world.add(Entity(id="Friend", kind="character", type="mouse", label="Mina"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    hero.memes["friendship"] += 1
    hero.memes["comfort"] += 1

    world.say(f"{hero_name} was a little chick who liked bedtime best, because the night smelled soft and safe.")
    world.say(f"When {hero_name} clucked good-night, the tiny sound made the coop feel cozy.")
    world.say(f"{hero_name} loved {activity.gerund}, and {friend.label} loved telling sleepy tales under the moon.")
    world.say(f"That evening, Mama Hen brought {hero_name} a {prize.phrase}, and {hero_name} wore {prize.it()} every night.")

    world.para()
    world.say(f"One moonlit night, {hero_name} and {friend.label} went to {world.setting.place}.")
    world.say(f"{friend.label} had lost a small bell by the path, and {hero_name} wanted to {activity.verb}.")
    world.say(f"Mama Hen was not indifferent to the problem; she was still and careful, because late-night grass can be tricky.")
    world.say(f"She said, “You may go, but only if you stay on the path and use the lantern.”")

    world.para()
    hero.memes["indifference"] += 0.0
    hero.memes["caution"] += 1
    hero.meters["sleepy"] += 1
    world.say(f"{hero_name} felt a tiny wobble of fear, but {hero_name} remembered {friend.label} and stood a little taller.")
    world.say(f"That was bravery: not roaring, just taking one careful step after another.")
    world.say(f"Together they put on the little boots and lifted the lantern high.")
    _do_activity(world, hero, activity, narrate=True)

    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear = select_gear(activity, prize)
        if gear is None:
            raise StoryError("No safe bedtime gear exists for this story.")
        if gear.id not in world.entities:
            item = world.add(Entity(
                id=gear.id, type="gear", label=gear.label, owner=hero.id,
                caretaker=parent.id, protective=True, covers=set(gear.covers),
                plural=gear.plural,
            ))
            item.worn_by = hero.id
        world.say(f"Still, they had chosen the safe way: {gear.prep}.")
    else:
        world.say("The lantern light kept everything gentle and dry.")

    world.say(f"At last, {friend.label} found the bell, and {hero_name} helped carry it home.")
    world.say(f"Mama Hen smiled, because friendship shines brightest when it is careful.")
    world.say(f"Back in bed, {hero_name}'s {prize.label} stayed clean, the bell jingled softly, and the moon watched over the coop.")

    world.facts.update(
        hero=hero, parent=parent, friend=friend, prize=prize,
        activity=activity, setting=setting, gear=world.entities.get("boots"),
        resolved=True, warning=True,
    )
    return world


SETTINGS = {
    "moonlit_yard": Setting(place="the moonlit yard", affords={"bell_search"}),
    "quiet_garden": Setting(place="the quiet garden", affords={"bell_search"}),
}

ACTIVITIES = {
    "bell_search": Activity(
        id="bell_search",
        verb="look for the lost bell",
        gerund="looking for lost bells",
        rush="dash down the wet path",
        mess="damp",
        soil="damp and sleepy",
        zone={"feet"},
        keyword="cluck",
        tags={"bravery", "friendship", "cautionary", "cluck", "indifferent"},
    )
}

PRIZES = {
    "pajamas": Prize(
        label="pajamas",
        phrase="striped bedtime pajamas",
        type="pajamas",
        region="feet",
        plural=True,
    )
}

GEAR = [
    Gear(
        id="boots",
        label="little boots",
        covers={"feet"},
        guards={"damp"},
        prep="put on little boots and carry the lantern",
        tail="took little boots and the lantern",
        plural=True,
    )
]

HEROES = ["Pip", "Penny", "Wren", "Coco"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str = "hen"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: a brave chick, a careful path, and a friend.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy", "chick"])
    ap.add_argument("--parent", choices=["hen"])
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(SETTINGS))
    activity = args.activity or "bell_search"
    prize = args.prize or "pajamas"
    if not prize_at_risk(ACTIVITIES[activity], PRIZES[prize]) or not select_gear(ACTIVITIES[activity], PRIZES[prize]):
        raise StoryError("No valid bedtime story combination matches those choices.")
    gender = args.gender or "chick"
    name = args.name or rng.choice(HEROES)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent="hen")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a short bedtime story for a small child about {hero.id}, the word "cluck", and a careful night walk.',
        f'Tell a gentle story where a brave chick named {hero.id} helps a friend and stays safe after dark.',
        f'Write a cautionary bedtime story with friendship and bravery in a moonlit yard.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, friend, prize = f["hero"], f["parent"], f["friend"], f["prize"]
    return [
        QAItem(
            question=f"Who was the bedtime story about?",
            answer=f"It was about {hero.id}, a little chick who loved bedtime, and about {friend.label} too.",
        ),
        QAItem(
            question=f"Why did Mama Hen ask them to use the lantern?",
            answer="She wanted them to stay safe on the dark path, because careful choices keep a night walk from turning messy.",
        ),
        QAItem(
            question=f"What did bravery look like in the story?",
            answer=f"Bravery looked like {hero.id} taking a careful step to help a friend even though the moonlit yard felt a little scary.",
        ),
        QAItem(
            question=f"What stayed clean and cozy by the end?",
            answer=f"{hero.id}'s {prize.label} stayed clean, and the bell was carried safely back home.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing the right thing even when you feel a little scared, especially if you do it carefully.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when you care about someone, help them, and want them to feel safe and happy.",
        ),
        QAItem(
            question="Why is caution helpful at night?",
            answer="Caution helps at night because dark paths can hide puddles, bumps, and other little surprises.",
        ),
        QAItem(
            question="What does cluck mean?",
            answer="Cluck is the soft sound a chick or hen makes.",
        ),
        QAItem(
            question="What does indifferent mean?",
            answer="Indifferent means not very interested or not feeling strongly about something.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        if pr.plural:
            lines.append(asp.fact("prize_plural", pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [("moonlit_yard", "bell_search", "pajamas"), ("quiet_garden", "bell_search", "pajamas")]


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only python:", sorted(python_set - clingo_set))
    print("only clingo:", sorted(clingo_set - python_set))
    return 1


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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent)
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

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [
            StoryParams(place="moonlit_yard", activity="bell_search", prize="pajamas", name="Pip", gender="chick"),
            StoryParams(place="quiet_garden", activity="bell_search", prize="pajamas", name="Penny", gender="chick"),
        ]
        samples = [generate(p) for p in params_list]
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
