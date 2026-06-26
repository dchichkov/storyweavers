#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("weight", "noise", "mess", "loss", "help", "risk"):
            self.meters.setdefault(k, 0.0)
        for k in ("gusto", "sorrow", "humor", "relief", "worry", "pride"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    inside: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Act:
    id: str
    verb: str
    gerund: str
    attempt: str
    mishap: str
    fix_word: str
    effect: str
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    plural: bool = False
    owners: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Tool:
    id: str
    label: str
    covers: set[str]
    blocks: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_mishap(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["noise"] < THRESHOLD and actor.meters["weight"] < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.owner != actor.id:
                continue
            if item.meters["loss"] >= THRESHOLD:
                continue
            sig = ("mishap", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["loss"] += 1
            actor.memes["worry"] += 1
            out.append(f"That made trouble for {actor.pronoun('possessive')} {item.label}.")
    return out


def _r_sorrow(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["risk"] < THRESHOLD:
            continue
        sig = ("sorrow", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["sorrow"] += 1
        out.append(f"{actor.pronoun().capitalize()} felt sorrow for a spell.")
    return out


CAUSAL_RULES = [
    Rule("mishap", _r_mishap),
    Rule("sorrow", _r_sorrow),
]


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


def sound_word(act: Act) -> str:
    return act.sound


def introduce(world: World, hero: Entity, elder: Entity) -> None:
    trait = next((t for t in hero.traits if t not in {"little"}), "spirited")
    world.say(
        f"{hero.id} was a little {trait} {hero.type} with more gusto than a marching band on payday."
    )
    world.say(f"{elder.id} had a warm smile and a laugh that could rattle windowpanes.")


def love_of_noise(world: World, hero: Entity, act: Act) -> None:
    hero.memes["gusto"] += 1
    hero.memes["humor"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved {act.gerund}, because every tap and toot sounded like {sound_word(act)}!"
    )


def prize_scene(world: World, hero: Entity, elder: Entity, prize: Prize) -> None:
    prize_ent = world.add(Entity(
        id="prize", label=prize.label, phrase=prize.phrase, owner=hero.id, caretaker=elder.id,
        region=prize.region, plural=prize.plural,
    ))
    prize_ent.worn_by = hero.id
    world.say(
        f"One day, {elder.id} brought home {hero.pronoun('possessive')} {prize.phrase}."
    )
    world.say(f"{hero.id} wore {prize_ent.label} like a treasure fit for a parade.")


def arrive(world: World, hero: Entity, elder: Entity, act: Act) -> None:
    world.say(
        f"One day, {hero.id} and {hero.pronoun('possessive')} {elder.id} went to {world.setting.place}."
    )
    if world.setting.inside:
        world.say(f"The place was cozy, but the floorboards loved to creak back.")
    else:
        world.say(f"The place sat under a sky big enough to hang a whole chorus of clouds.")


def attempt(world: World, hero: Entity, act: Act, prize: Prize) -> None:
    hero.meters["noise"] += 1
    hero.meters["weight"] += 1
    hero.memes["gusto"] += 1
    world.say(
        f"{hero.id} wanted to {act.verb}, so {hero.pronoun()} made a grand attempt: {act.attempt}."
    )
    world.say(f"{sound_word(act)}! went the effort, and {act.sound.lower()}! went the hope.")
    if prize.region in {"head", "torso", "hands"}:
        world.facts["at_risk"] = True
    else:
        world.facts["at_risk"] = False


def warn(world: World, elder: Entity, hero: Entity, act: Act, prize: Prize) -> bool:
    if not world.facts.get("at_risk"):
        return False
    world.facts["predicted_loss"] = act.effect
    world.say(
        f'"Watch out," {elder.id} said. "If you keep at it, that {prize.label} could end up {act.effect}."'
    )
    return True


def clowning(world: World, hero: Entity, act: Act) -> None:
    hero.memes["humor"] += 1
    world.say(
        f"{hero.id} grinned anyway and tried again, with all the gusto a rooster has at sunrise."
    )
    world.say(f"{hero.pronoun().capitalize()} gave one more {act.attempt.lower()}, and the whole place answered with {sound_word(act)}.")


def mishap(world: World, hero: Entity, act: Act, prize: Prize) -> None:
    hero.meters["risk"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then came a foolish little twist: {sound_word(act)}! splat! and the {prize.label} got {act.effect}."
    )
    world.say(f"{hero.id} looked as sorrowful as a violin with one string left.")


def fix(world: World, elder: Entity, hero: Entity, act: Act, prize: Prize) -> Optional[Tool]:
    tool = None
    for t in TOOLS:
        if prize.region in t.covers and act.id in t.blocks:
            tool = t
            break
    if tool is None:
        return None
    ent = world.add(Entity(id=tool.id, label=tool.label, owner=hero.id, caretaker=elder.id, plural=tool.plural))
    ent.worn_by = hero.id
    world.say(
        f"{elder.id} winked and said, \"How about we {tool.prep}?\""
    )
    return tool


def accept(world: World, elder: Entity, hero: Entity, act: Act, prize: Prize, tool: Tool) -> None:
    hero.memes["sorrow"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} laughed through the last of the sorrow and agreed."
    )
    world.say(
        f"With the {tool.label} in place, {hero.id} could {act.verb} without ruining {hero.pronoun('possessive')} {prize.label}."
    )
    world.say(
        f"So they went on together: {tool.tail}. {sound_word(act)}! {sound_word(act)}! and all was right as rain."
    )


def tell(setting: Setting, act: Act, prize_cfg: Prize, hero_name: str, hero_type: str, elder_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait, "stubborn"]))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, label="grandpa"))
    introduce(world, hero, elder)
    love_of_noise(world, hero, act)
    prize_scene(world, hero, elder, prize_cfg)
    world.para()
    arrive(world, hero, elder, act)
    attempt(world, hero, act, prize_cfg)
    warn(world, elder, hero, act, prize_cfg)
    clowning(world, hero, act)
    mishap(world, hero, act, prize_cfg)
    world.para()
    tool = fix(world, elder, hero, act, prize_cfg)
    if tool:
        accept(world, elder, hero, act, prize_cfg, tool)
    world.facts.update(hero=hero, elder=elder, act=act, prize=prize_cfg, tool=tool, resolved=tool is not None)
    return world


SETTINGS = {
    "barn": Setting(place="the barn", inside=True, affords={"stampede", "juggle", "honk"}),
    "fair": Setting(place="the county fair", inside=False, affords={"juggle", "honk", "tune"}),
    "river": Setting(place="the riverbank", inside=False, affords={"honk", "tune"}),
    "school": Setting(place="the schoolhouse yard", inside=False, affords={"juggle", "tune"}),
}

ACTIVITIES = {
    "juggle": Act(
        id="juggle",
        verb="juggle tin kettles",
        gerund="juggling tin kettles",
        attempt="toss the kettles high",
        mishap="one kettle bonked the rafters",
        fix_word="apron",
        effect="banged up",
        sound="CLANG",
        tags={"sound", "humor"},
    ),
    "honk": Act(
        id="honk",
        verb="honk a goose horn",
        gerund="honking a goose horn",
        attempt="blow a mighty honk",
        mishap="the horn blasted a window clean open",
        fix_word="muzzle",
        effect="scared silly",
        sound="HONK",
        tags={"sound", "humor"},
    ),
    "tune": Act(
        id="tune",
        verb="tune a fiddle",
        gerund="tuning a fiddle",
        attempt="draw the bow with a whoop",
        mishap="the fiddle squealed like a kitten on skates",
        fix_word="chin rest",
        effect="out of tune",
        sound="SQUEEE",
        tags={"sound", "humor"},
    ),
    "stampede": Act(
        id="stampede",
        verb="start a parade of goats",
        gerund="parading goats",
        attempt="wave the feed sack",
        mishap="the goats danced into every bucket in sight",
        fix_word="fence",
        effect="kicked over",
        sound="THUMP-THUMP",
        tags={"humor", "sound"},
    ),
}

PRIZES = {
    "hat": Prize(label="hat", phrase="a tall white hat", region="head"),
    "vest": Prize(label="vest", phrase="a bright red vest", region="torso"),
    "boots": Prize(label="boots", phrase="polished boots", region="feet", plural=True),
}

TOOLS = [
    Tool(id="apron", label="a canvas apron", covers={"torso"}, blocks={"juggle"}),
    Tool(id="muzzle", label="a horn muzzle", covers={"head"}, blocks={"honk"}),
    Tool(id="chinrest", label="a softer chin rest", covers={"head"}, blocks={"tune"}),
    Tool(id="fence", label="a goat fence", covers={"feet", "torso"}, blocks={"stampede"}, plural=False),
]

NAMES = ["Piper", "Nell", "Walt", "June", "Huck", "Maggie", "Bo", "Rosie"]
TRAITS = ["bold", "merry", "spunky", "bright", "reckless", "cheery"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id, prize in PRIZES.items():
                act = ACTIVITIES[act_id]
                if prize.region in {"head", "torso"} or (act.id == "stampede" and prize.region == "feet"):
                    if any(prize.region in t.covers and act.id in t.blocks for t in TOOLS):
                        combos.append((place, act_id, prize_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld with gusto, sorrow, humor, and sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandpa", "grandma"])
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
        raise StoryError("No valid tall-tale combination matches the given options.")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    elder = args.elder or rng.choice(["grandpa", "grandma"])
    name = args.name or rng.choice(NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, elder=elder, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, params.elder, params.trait)
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
    hero = f["hero"]
    act = f["act"]
    prize = f["prize"]
    return [
        f'Write a tall tale for little kids with gusto, sorrow, humor, and sound effects about {hero.id} at {world.setting.place}.',
        f"Tell a funny story where {hero.id} tries to {act.verb} and someone worries about {prize.phrase}.",
        f'Create a child-friendly tall tale that includes the words "gusto" and "sorrow" and ends with a fix.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    act = f["act"]
    prize = f["prize"]
    tool = f["tool"]
    q = [
        QAItem(
            question=f"What did {hero.id} love to do at {world.setting.place}?",
            answer=f"{hero.id} loved {act.gerund}, and every try sounded like {act.sound}!",
        ),
        QAItem(
            question=f"Why did {elder.id} worry about {hero.id}'s {prize.label}?",
            answer=f"{elder.id} worried because all that noise could leave the {prize.label} {act.effect}.",
        ),
        QAItem(
            question=f"How did the grown-up help in the end?",
            answer=f"{elder.id} offered {tool.label if tool else 'a careful fix'}, and that let {hero.id} keep going safely.",
        ),
    ]
    if f.get("resolved"):
        q.append(QAItem(
            question=f"How did {hero.id} feel after the fix?",
            answer=f"{hero.id} felt joy and relief, with the sorrow gone and the gusto still shining.",
        ))
    return q


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is gusto?", answer="Gusto means big, cheerful energy for doing something with all your heart."),
        QAItem(question="What is sorrow?", answer="Sorrow is a sad feeling you get when something goes wrong."),
        QAItem(question="Why do sound effects make a story fun?", answer="Sound effects like CLANG or HONK make a scene feel lively and funny."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"{e.id}: {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
at_risk(A,P) :- act(A), prize(P), prize_region(P,R), act_hits(A,R).
compatible(A,P,T) :- at_risk(A,P), tool(T), tool_blocks(T,A), tool_covers(T,R), prize_region(P,R).
valid(Place,A,P) :- affords(Place,A), compatible(A,P,_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, s in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", place, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("act", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, p.region))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for a in sorted(t.blocks):
            lines.append(asp.fact("tool_blocks", t.id, a))
        for r in sorted(t.covers):
            lines.append(asp.fact("tool_covers", t.id, r))
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
        print(f"OK: clingo matches python ({len(py)} combos).")
        return 0
    print("Mismatch:")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="barn", activity="juggle", prize="vest", name="Piper", gender="girl", elder="grandpa", trait="merry"),
    StoryParams(place="fair", activity="honk", prize="hat", name="Huck", gender="boy", elder="grandma", trait="bold"),
    StoryParams(place="river", activity="tune", prize="hat", name="June", gender="girl", elder="grandpa", trait="cheery"),
]


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
        print(asp_program("#show valid/3."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, a, pr) for (p, a, pr) in valid_combos_impl()]


def valid_combos_impl() -> list[tuple[str, str, str]]:
    combos = []
    for place, s in SETTINGS.items():
        for act_id in s.affords:
            for pr_id, pr in PRIZES.items():
                if pr.region in {"head", "torso"} and any(pr.region in t.covers and act_id in t.blocks for t in TOOLS):
                    combos.append((place, act_id, pr_id))
    return combos


if __name__ == "__main__":
    main()
