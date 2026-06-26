#!/usr/bin/env python3
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

    def __post_init__(self):
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "princess", "witch", "woman", "mother"}
        male = {"boy", "king", "prince", "wizard", "man", "father"}
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
    affords: set[str] = field(default_factory=set)


@dataclass
class MagicThing:
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
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for actor in world.characters():
            if actor.meters.get("spark", 0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone or world.covered(actor, item.region):
                    continue
                sig = ("mess", actor.id, item.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[item.label] = item.meters.get(item.label, 0) + 1
                item.meters["dirty"] = item.meters.get("dirty", 0) + 1
                out.append(f"{actor.id}'s {item.label} grew {item.label.lower()}-stained.")
                changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


def prize_at_risk(act: MagicThing, prize: Prize) -> bool:
    return prize.region in act.zone


def select_gear(act: MagicThing, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if act.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def tell(setting: Setting, act: MagicThing, prize_cfg: Prize, name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, meters={}, memes={"curiosity": 1.0}))
    parent = world.add(Entity(id="Guardian", kind="character", type=parent_type, label="the guardian"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural))

    world.say(f"{hero.id} was a little {trait} {hero.type} who loved every bright corner of {setting.place}.")
    world.say(f"{hero.id} watched for turquoise glimmers and listened for magic whispers in the air.")
    world.say(f"One day, {hero.id}'s {parent.label} gave {hero.pronoun('object')} {prize.phrase}, and {hero.id} cherished {prize.it()} dearly.")

    world.para()
    world.say(f"At {setting.place}, a {act.keyword} glow called from the flowers.")
    world.say(f"{hero.id} wanted to {act.verb}, because curiosity tugged harder than caution.")
    world.say(f"Yet {hero.pronoun('possessive')} {parent.label} warned, \"If you rush into the magic, your {prize.label} may come to harm.\"")

    hero.memes["resolve"] = 1.0
    hero.meters["spark"] = 1.0
    world.zone = set(act.zone)
    propagate(world, narrate=False)

    world.para()
    if prize_at_risk(act, prize):
        world.say(f"{hero.id} paused and looked at the {prize.label}.")
        world.say(f"{hero.id} did not want {prize.it()} ruined by glittering trouble.")
        gear_def = select_gear(act, prize)
        if gear_def is not None:
            gear = world.add(Entity(id=gear_def.id, type="gear", label=gear_def.label, protective=True, covers=set(gear_def.covers), plural=gear_def.plural))
            gear.worn_by = hero.id
            world.say(f"Then {hero.pronoun('possessive')} {parent.label} smiled and said, \"Let us {gear_def.prep}.\"")
            world.say(f"{hero.id} agreed at once.")
            world.say(f"Together they {gear_def.tail}, and {hero.id} could {act.gerund} without hurting {hero.pronoun('possessive')} {prize.label}.")
            world.say(f"The little {trait} {hero.type} ended the day with {prize.label} shining clean, and the magic glow twinkling kindly beside {hero.pronoun('object')}.")
        else:
            raise StoryError("No reasonable magical safeguard fits this tale.")
    else:
        world.say(f"{hero.id} reached for the glow and found it gentle, not dangerous.")
        world.say(f"With a happy laugh, {hero.id} did {act.gerund}, and the {prize.label} stayed safe all the same.")
        world.say(f"The turquoise light danced overhead while curiosity turned into delight.")

    world.facts.update(hero=hero, parent=parent, prize=prize, setting=setting, act=act)
    return world


SETTINGS = {
    "garden": Setting(place="the moonlit garden", affords={"glow", "door"}),
    "forest": Setting(place="the whispering forest", affords={"glow", "door"}),
    "tower": Setting(place="the old tower room", affords={"door"}),
    "cottage": Setting(place="the willow cottage", affords={"glow"}),
}

ACTIVITIES = {
    "glow": MagicThing(
        id="glow",
        verb="follow the turquoise glow",
        gerund="following the turquoise glow",
        rush="run after the glow",
        mess="spark",
        soil="dull and dusty",
        zone={"torso"},
        keyword="turquoise",
        tags={"turquoise", "magic", "curiosity"},
    ),
    "door": MagicThing(
        id="door",
        verb="open the magic door",
        gerund="opening the magic door",
        rush="push at the door",
        mess="spark",
        soil="full of soot and sparkles",
        zone={"torso", "hands"},
        keyword="curious",
        tags={"magic", "curiosity"},
    ),
}

PRIZES = {
    "cloak": Prize(label="cloak", phrase="a soft turquoise cloak", type="cloak", region="torso"),
    "ribbon": Prize(label="ribbon", phrase="a turquoise ribbon", type="ribbon", region="hands"),
    "shoes": Prize(label="shoes", phrase="tiny turquoise shoes", type="shoes", region="feet", plural=True),
}

GEAR = [
    Gear(id="gloves", label="silver gloves", covers={"hands"}, guards={"spark"}, prep="put on the silver gloves first", tail="slipped on the silver gloves and tried again"),
    Gear(id="cloakwrap", label="a starry cloak wrap", covers={"torso"}, guards={"spark"}, prep="wrap the cloak in a starry scarf first", tail="wrapped the cloak in a starry scarf and walked on"),
    Gear(id="boots", label="fairy boots", covers={"feet"}, guards={"spark"}, prep="put on fairy boots first", tail="tucked their feet into fairy boots and stepped lightly"),
]

GIRL_NAMES = ["Mira", "Lina", "Nora", "Elsa", "June", "Iris"]
BOY_NAMES = ["Owen", "Finn", "Theo", "Ari", "Jasper", "Eli"]
TRAITS = ["curious", "brave", "gentle", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fairy tale about a curious {f["hero"].type} named {f["hero"].id} and a turquoise magic moment in {f["setting"].place}.',
        f"Tell a gentle story where {f['hero'].id} wants to {f['act'].verb} but the guardian worries about the {f['prize'].label}.",
        f'Write a child-friendly fairy tale that includes the word "turquoise" and ends with a kind magical compromise.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["act"]
    return [
        QAItem(
            question=f"Who was the story about in {f['setting'].place}?",
            answer=f"It was about {hero.id}, a little curious {hero.type}, and {hero.pronoun('possessive')} guardian.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do when the turquoise glow appeared?",
            answer=f"{hero.id} wanted to {act.verb}. Curiosity pulled {hero.pronoun('object')} toward the magic.",
        ),
        QAItem(
            question=f"Why did the guardian worry about the {prize.label}?",
            answer=f"The guardian worried that the {prize.label} could be harmed by the sparkly magic if {hero.id} rushed ahead.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is curiosity?", answer="Curiosity is the feeling that makes someone want to know more, look closer, and ask questions."),
        QAItem(question="What is magic in a fairy tale?", answer="Magic in a fairy tale is special power that can make strange, wonder-filled things happen."),
        QAItem(question="What is turquoise?", answer="Turquoise is a blue-green color, like bright sea water or a pretty stone."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} " + " ".join(bits))
    return "\n".join(lines)


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
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        if p.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), protects(_,A,P).
valid_story(Place,A,P,Gender) :- valid(Place,A,P), wears(Gender,P).
#show valid/3.
#show valid_story/4.
"""


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
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo matches valid_combos() ({len(valid_combos())} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos().")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world with turquoise curiosity and magic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["queen", "king"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid fairy-tale combination matches those choices.")
    place, act, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    if gender not in PRIZES[prize].genders:
        raise StoryError("That prize does not fit the chosen gender in this tale.")
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["queen", "king"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=act, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, params.trait)
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
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible triples ({len(stories)} with gender):")
        for p, a, pr in triples:
            genders = sorted(g for (pp, aa, prr, g) in stories if (pp, aa, prr) == (p, a, pr))
            print(f"  {p:8} {a:8} {pr:8} [{', '.join(genders)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("garden", "glow", "cloak", "Mira", "girl", "queen", "curious"),
            StoryParams("forest", "door", "ribbon", "Owen", "boy", "king", "bright"),
            StoryParams("cottage", "glow", "shoes", "Lina", "girl", "queen", "gentle"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
