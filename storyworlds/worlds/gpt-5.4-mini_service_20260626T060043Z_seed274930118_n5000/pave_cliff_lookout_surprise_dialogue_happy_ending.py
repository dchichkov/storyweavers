#!/usr/bin/env python3
"""
storyworlds/worlds/pave_cliff_lookout_surprise_dialogue_happy_ending.py
=======================================================================

A small bedtime-story world set at a cliff lookout, built around paving a
little safe path, a gentle surprise, dialogue, and a happy ending.

Premise:
- A child wants to help pave a winding lookout path.
- The lookout is beautiful but a little risky near the cliff edge.
- A parent worries about safety.
- While they work, a surprise is revealed.
- The story ends with a calm, happy image proving the change.

The world is intentionally small and constraint-checked: this is a classical
simulation, not a frozen prose template. The meters and memes below drive the
story beats, the Q&A, and the ASP twin.
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
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the cliff lookout"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Surprise:
    id: str
    label: str
    reveal: str
    gift: str
    tags: set[str] = field(default_factory=set)


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
        self.facts: dict = {}
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
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _r_dust(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters.get("pave", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("dust", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dusty"] = item.meters.get("dusty", 0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got dusty.")
    return out


def _r_fear(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes.get("edge_worry", 0.0) < THRESHOLD:
            continue
        sig = ("fear", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["fear"] = actor.memes.get("fear", 0) + 1
        out.append(f"The edge felt too close for a moment.")
    return out


CAUSAL_RULES = [
    _r_dust,
    _r_fear,
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in {"feet", "legs"} and "cliff_edge" in activity.tags


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = clone_world(world)
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"dusty": prize.meters.get("dusty", 0) >= THRESHOLD}


def clone_world(world: World) -> World:
    import copy
    c = World(world.setting)
    c.entities = copy.deepcopy(world.entities)
    c.paragraphs = [[]]
    c.fired = set(world.fired)
    c.zone = set(world.zone)
    c.facts = dict(world.facts)
    return c


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = {"feet", "legs"}
    actor.meters["pave"] = actor.meters.get("pave", 0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who loved quiet evening walks and smooth stones.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_pave"] = hero.memes.get("love_pave", 0) + 1
    world.say(f"{hero.pronoun().capitalize()} loved to {activity.verb}, because {activity.gerund} made the path feel kind and safe.")


def arrive(world: World, hero: Entity, parent: Entity) -> None:
    world.say(f"One soft evening, {hero.id} and {hero.pronoun('possessive')} {parent.label_word} went to the cliff lookout.")
    world.say("The sea was whispering below, and the sky looked sleepy and gold.")


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    world.say(f"{hero.id} wanted to {activity.verb} right away, but {hero.pronoun('possessive')} {parent.label_word} said, \"Slow feet near the edge, please.\"")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict(world, hero, activity, prize.id)
    if not pred["dusty"]:
        return False
    hero.memes["edge_worry"] = hero.memes.get("edge_worry", 0) + 1
    world.say(f"\"If we hurry, your {prize.label} will get dusty,\" {hero.pronoun('possessive')} {parent.label_word} said.")
    return True


def surprise(world: World, surprise_def: Surprise) -> None:
    world.facts["surprise"] = surprise_def
    world.say(f"Then came a surprise: {surprise_def.reveal}")


def dialogue_and_fix(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, surprise_def: Surprise) -> None:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        raise StoryError("No safe gear matches this story.")
    gear = world.add(Entity(id=gear_def.id, type="thing", label=gear_def.label, protective=True, covers=set(gear_def.covers)))
    gear.worn_by = hero.id
    world.say(f"\"Can we still {activity.verb}?\" {hero.id} asked.")
    world.say(f"\"Yes,\" said {hero.pronoun('possessive')} {parent.label_word}. \"We can {gear_def.prep}, and then take our time.\"")
    world.say(f"They smiled at the little {surprise_def.label.lower()} tucked near the stones.")
    do_activity(world, hero, activity, narrate=True)
    world.say(f"Soon the path was {activity.gerund}, {prize.label} stayed clean, and the surprise was safely brought home.")
    world.say(f"{hero.id} held up {surprise_def.gift} and said, \"I like this ending.\"")
    world.say(f"\"Me too,\" said {parent.label_word}, \"because we made it safe and gentle.\"")
    hero.memes["joy"] = hero.memes.get("joy", 0) + 2
    hero.memes["love"] = hero.memes.get("love", 0) + 1
    hero.memes["fear"] = 0.0
    world.facts["gear"] = gear_def
    world.facts["resolved"] = True


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, surprise_def: Surprise,
         hero_name: str = "Mina", hero_type: str = "girl",
         parent_type: str = "mother", trait: str = "gentle") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mom" if parent_type == "mother" else "dad"))
    prize = world.add(Entity(id="prize", type=prize_cfg.id, label=prize_cfg.label, phrase=prize_cfg.phrase, region=prize_cfg.region, plural=prize_cfg.plural, owner=hero.id, caretaker=parent.id))
    hero.memes["trait_kind"] = 1.0
    introduce(world, hero)
    loves_activity(world, hero, activity)
    world.say(f"{hero.id} carried {hero.pronoun('possessive')} {prize.label} very carefully, like something small and precious.")
    world.para()
    arrive(world, hero, parent)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    surprise(world, surprise_def)
    world.say(f"\"Oh!\" said {hero.id}. \"That is the sweetest surprise.\"")
    world.para()
    dialogue_and_fix(world, parent, hero, activity, prize, surprise_def)
    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting, surprise=surprise_def)
    return world


SETTINGS = {
    "cliff lookout": Setting(place="the cliff lookout", affords={"pave"}),
}

ACTIVITIES = {
    "pave": Activity(
        id="pave",
        verb="pave the lookout path",
        gerund="paving the lookout path",
        rush="carry stones too near the edge",
        mess="dusty",
        soil="dusty",
        keyword="pave",
        tags={"cliff_edge", "stone", "path"},
    ),
}

PRIZES = {
    "shoes": Prize(id="shoes", label="shoes", phrase="little walking shoes", region="feet", plural=True),
    "dress": Prize(id="dress", label="dress", phrase="a soft bedtime dress", region="legs"),
    "jacket": Prize(id="jacket", label="jacket", phrase="a cozy jacket", region="torso"),
}

SURPRISES = {
    "lantern": Surprise(id="lantern", label="lantern", reveal="a tiny blue lantern hidden behind a stone", gift="the tiny blue lantern", tags={"light"}),
    "shell": Surprise(id="shell", label="shell", reveal="a spiral shell shining like a moonbeam", gift="the spiral shell", tags={"sea"}),
    "note": Surprise(id="note", label="note", reveal="a folded note that said, 'For the bravest helper'", gift="the folded note", tags={"kindness"}),
}

GEAR = [
    Gear(id="boots", label="little work boots", covers={"feet"}, guards={"dusty"}, prep="put on little work boots", tail="walked back with careful steps", plural=True),
    Gear(id="smock", label="a smock", covers={"torso"}, guards={"dusty"}, prep="put on a smock", tail="walked back with careful steps"),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if not prize_at_risk(act, prize):
                    continue
                if not select_gear(act, prize):
                    continue
                for sur_id in SURPRISES:
                    out.append((place, act_id, prize_id, sur_id))
    return out


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    surprise: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "pave": [("What does it mean to pave something?", "To pave something means to cover it with stones, bricks, or another hard surface so it becomes smoother to walk on.")],
    "cliff": [("What is a cliff?", "A cliff is a very steep rock wall or high edge of land. People need to stay careful near it.")],
    "lantern": [("What is a lantern for?", "A lantern gives off light, so people can see better when it is getting dark.")],
    "shell": [("What is a shell?", "A shell is a hard outer home made by some sea animals, like snails and clams.")],
    "note": [("What is a note?", "A note is a short written message, often left for someone to find.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    activity = f["activity"]
    return [
        f'Write a bedtime story about a child who wants to {activity.verb} at the cliff lookout and finds a gentle surprise.',
        f"Tell a calm story where {hero.id} and {hero.pronoun('possessive')} parent talk kindly while paving a lookout path.",
        f'Write a child-friendly story that includes the word "{activity.keyword}" and ends happily at the cliff lookout.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, activity, surprise = f["hero"], f["parent"], f["prize"], f["activity"], f["surprise"]
    return [
        QAItem(
            question=f"Where did {hero.id} and {hero.pronoun('possessive')} {parent.label_word} go?",
            answer=f"They went to {world.setting.place}, a quiet place above the sea.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do there?",
            answer=f"{hero.id} wanted to {activity.verb}.",
        ),
        QAItem(
            question=f"Why did {hero.pronoun('possessive')} {parent.label_word} worry about the {prize.label}?",
            answer=f"{parent.label_word.capitalize()} worried that the {prize.label} would get dusty near the lookout path while they worked.",
        ),
        QAItem(
            question=f"What was the surprise?",
            answer=f"The surprise was {surprise.reveal}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, with the path paved, the surprise found, and {hero.id} feeling calm and glad.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in world.facts["activity"].tags | world.facts["surprise"].tags | {"pave"}:
        if tag in KNOWLEDGE:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="cliff lookout", activity="pave", prize="shoes", surprise="lantern", name="Mina", gender="girl", parent="mother", trait="gentle"),
    StoryParams(place="cliff lookout", activity="pave", prize="dress", surprise="shell", name="Noah", gender="boy", parent="father", trait="curious"),
    StoryParams(place="cliff lookout", activity="pave", prize="jacket", surprise="note", name="Ava", gender="girl", parent="mother", trait="brave"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.verb} does not realistically risk a {prize.label} in this small world.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: try --gender {ok} for a {PRIZES[prize_id].label} story.)"


ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), splashes(A,R), worn_on(P,R).
has_fix(A,P) :- prize_at_risk(A,P), gear(G), guards(G,M), mess_of(A,M), covers(G,R), worn_on(P,R).
valid(Place,A,P,S) :- setting(Place), affords(Place,A), prize_at_risk(A,P), has_fix(A,P), surprise(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted({"feet", "legs"}):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    for s in SURPRISES:
        lines.append(asp.fact("surprise", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: a cliff lookout, a paving job, a surprise, and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=["gentle", "curious", "brave", "cheerful"])
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
        if not prize_at_risk(act, pr):
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.surprise is None or c[3] == args.surprise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize, surprise = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    name = args.name or rng.choice(["Mina", "Luna", "Theo", "Finn", "Ava", "Ivy"])
    trait = args.trait or rng.choice(["gentle", "curious", "brave", "cheerful"])
    return StoryParams(place=place, activity=activity, prize=prize, surprise=surprise, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], SURPRISES[params.surprise], params.name, params.gender, params.parent, params.trait)
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, prize, surprise) combos:\n")
        for combo in combos:
            print("  ", combo)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} (surprise: {p.surprise})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
