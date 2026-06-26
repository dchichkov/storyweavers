#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/exclaim_chump_humor_tall_tale.py
===============================================================================================================

A small, self-contained storyworld in a tall-tale style with humor, built
around a child, an overblown boast, and a cheerful safer way to finish the day.

Seed words:
- exclaim
- chump

Style:
- Tall tale
- Humor
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

    def __post_init__(self):
        for k in ["dust", "jostle", "tatter", "shine", "giggle"]:
            self.meters.setdefault(k, 0.0)
        for k in ["boast", "worry", "humor", "pride", "calm", "conflict"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
    indoor: bool = False
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
    joke: str


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["dust"] < THRESHOLD and actor.meters["jostle"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("mess", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["tatter"] += 1
            item.meters["dust"] += 1
            out.append(f"{actor.id}'s {item.label} came out dusty and a mite ragged.")
    return out


def _r_giggle(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes["humor"] >= THRESHOLD and ("giggle", e.id) not in world.fired:
            world.fired.add(("giggle", e.id))
            e.meters["giggle"] += 1
            out.append("A giggle went rolling through the place like a barrel downhill.")
    return out


def _r_conflict(world: World) -> list[str]:
    for e in world.characters():
        if e.memes["worry"] >= THRESHOLD and e.memes["boast"] >= THRESHOLD:
            sig = ("conflict", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["conflict"] += 1
            return ["__conflict__"]
    return []


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["calm"] >= THRESHOLD and e.memes["conflict"] >= THRESHOLD:
            sig = ("calm", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["conflict"] = 0.0
            out.append(f"{e.id} settled down like a lantern after the wind quit.")
    return out


CAUSAL_RULES = [
    _r_mess,
    _r_giggle,
    _r_conflict,
    _r_calm,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = World(world.setting)
    import copy
    sim.entities = copy.deepcopy(world.entities)
    sim.zone = set(activity.zone)
    sim.get(actor.id).meters[activity.mess] += 1
    for rule in CAUSAL_RULES:
        rule(sim)
    prize = sim.entities[prize_id]
    return {"soiled": prize.meters["dust"] >= THRESHOLD, "giggles": sum(e.meters["giggle"] for e in sim.entities.values())}


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", "bright-eyed"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the grown-up"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    hero.memes["humor"] += 1
    hero.memes["boast"] += 1
    world.say(f"{hero.id} was a little {hero_type} with a grin big enough to hang a hat on.")
    world.say(f"{hero.id} loved a good joke, a big laugh, and a tall tale that could outrun a prairie wind.")
    world.say(f"One day {parent.label} bought {hero.pronoun('object')} {prize.phrase}, and {hero.id} wore {prize.it()} like treasure.")

    world.para()
    world.say(f"At {world.setting.place}, {hero.id} wanted to {activity.verb}.")
    world.say(f"{hero.id} said, \"I can {activity.verb} faster than a jackrabbit with a trumpet!\"")
    world.say(f"That was such a chump-sized boast that even the fence posts seemed to smirk.")
    world.say(f"{parent.label.capitalize()} looked at {prize.label} and said, \"Easy there, chump, or you'll get {prize.label} {activity.soil}.\"")

    pred = predict_mess(world, hero, activity, prize.id)
    if pred["soiled"]:
        world.facts["predicted_soil"] = activity.soil
        hero.memes["worry"] += 1

    world.say(f"{hero.id} heard that, but the itch to play was still buzzing in {hero.pronoun('possessive')} boots.")
    hero.meters[activity.mess] += 1
    world.zone = set(activity.zone)
    propagate(world, narrate=True)

    world.para()
    world.say(f"{hero.id} dashed toward the fun and nearly kicked up a cloud the size of a barn roof.")
    world.say(f"{parent.label.capitalize()} held up a hand and shouted, \"Not that way, chump!\"")
    hero.memes["worry"] += 1
    hero.memes["humor"] += 1
    propagate(world, narrate=True)

    gear_def = select_gear(activity, prize)
    if not gear_def:
        raise StoryError("No reasonable gear exists for this tall tale.")
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id

    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        raise StoryError("The gear does not honestly solve the problem.")

    world.say(f"Then {parent.label} smiled a small smile and said, \"How about we {gear_def.prep}?\"")
    hero.memes["calm"] += 1
    hero.memes["pride"] += 1
    world.say(f"{hero.id} blinked, then laughed at {hero.pronoun('possessive')} own hot air and agreed.")
    world.say(f"They {gear_def.tail}, and soon {hero.id} was {activity.gerund}, {prize.label} staying clean, and everybody laughing like kettledrums in church.")

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=gear_def, setting=setting, resolved=True)
    return world


SETTINGS = {
    "barnyard": Setting(place="the barnyard", indoor=False, affords={"rope", "splash"}),
    "fair": Setting(place="the county fair", indoor=False, affords={"rope", "splash"}),
    "riverbank": Setting(place="the riverbank", indoor=False, affords={"splash"}),
}

ACTIVITIES = {
    "rope": Activity(
        id="rope",
        verb="lasso the washer line",
        gerund="lassoing the washer line",
        rush="run at the line",
        mess="dust",
        soil="dusty as a chimney sweep",
        zone={"hands", "torso"},
        keyword="rope",
        joke="a rope so long it could tickle a cloud",
    ),
    "splash": Activity(
        id="splash",
        verb="splash through the creek",
        gerund="splashing through the creek",
        rush="dash into the creek",
        mess="jostle",
        soil="splashed and muddy",
        zone={"feet", "legs"},
        keyword="creek",
        joke="a splash big enough to wet a rooster's opinion",
    ),
}

PRIZES = {
    "hat": Prize(label="hat", phrase="a shiny new hat", type="hat", region="torso"),
    "boots": Prize(label="boots", phrase="a pair of polished boots", type="boots", region="feet", plural=True),
    "overalls": Prize(label="overalls", phrase="a fresh pair of overalls", type="overalls", region="legs", plural=True),
}

GEAR = [
    Gear(id="dustcoat", label="a dustcoat", covers={"torso"}, guards={"dust"}, prep="put on a dustcoat first", tail="went back for the dustcoat"),
    Gear(id="mudboots", label="mud boots", covers={"feet"}, guards={"jostle"}, prep="pull on mud boots first", tail="came back with the mud boots", plural=True),
    Gear(id="overalls-old", label="old overalls", covers={"legs", "torso"}, guards={"dust", "jostle"}, prep="wear the old overalls", tail="headed out in the old overalls", plural=True),
]

GIRL_NAMES = ["Mabel", "Dot", "Nell", "Ruby", "Sadie"]
BOY_NAMES = ["Buster", "Eli", "Hank", "Wes", "Milo"]
TRAITS = ["brave", "cheerful", "mischievous", "sparkly", "lively"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a humorous tall-tale story for a child about "{f["hero"].id}" and a "chump" who boasts too big for the day.',
        f"Tell a playful story where {f['hero'].id} wants to {f['activity'].verb} at {f['setting'].place}, but the grown-up worries about {f['prize'].label}.",
        f'Write a short story that includes the words "exclaim" and "chump" and ends with a safer way to play.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, activity = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Who is the tall-tale story about?",
            answer=f"It is about {hero.id}, a little {hero.type} who loves jokes and big boisterous boasting.",
        ),
        QAItem(
            question=f"Why did {parent.label} warn {hero.id} about {prize.label}?",
            answer=f"{parent.label.capitalize()} warned {hero.id} because {hero.id} wanted to {activity.verb}, and that could leave {prize.label} {activity.soil}.",
        ),
        QAItem(
            question=f"What did {hero.id} call {him := 'him' if hero.type in {'boy', 'father', 'man'} else 'her'}self after the warning?",
            answer=f"{hero.id} was a bit of a chump about the whole thing at first, because {hero.id} kept boasting even though {parent.label} was trying to help.",
        ),
    ] + (
        [
            QAItem(
                question=f"How did the story end?",
                answer=f"It ended with {hero.id} agreeing to use {f['gear'].label} first, so {hero.id} could {activity.verb} without ruining {prize.label}.",
            )
        ] if f.get("resolved") else []
    )


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does exclaim mean?",
            answer="To exclaim means to say something loudly and with feeling, often because you are surprised or excited.",
        ),
        QAItem(
            question="What is a chump?",
            answer="A chump is a silly, gullible, or foolish person; in a funny story, it can mean somebody who boasts too much and gets embarrassed.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
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
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="barnyard", activity="rope", prize="hat", name="Mabel", gender="girl", parent="mother", trait="cheerful"),
    StoryParams(place="fair", activity="splash", prize="boots", name="Buster", gender="boy", parent="father", trait="mischievous"),
    StoryParams(place="riverbank", activity="splash", prize="overalls", name="Ruby", gender="girl", parent="mother", trait="lively"),
]


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protected(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), protected(_,A,P).
valid_story(Place,A,P,Gender) :- valid(Place,A,P), wears(Gender,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world with humor, an exclaim, and a chump.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError("That pair does not make a reasonable tall-tale problem.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize = rng.choice(sorted(combos))
    pr = PRIZES[prize]
    gender = args.gender or rng.choice(sorted(pr.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"{place:10} {act:8} {prize:10} [{', '.join(genders)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.name}: {p.activity} at {p.place} ({p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
