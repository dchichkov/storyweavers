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
    carried_by: Optional[str] = None
    location: str = ""
    stuck_in: str = ""
    open: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
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
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    cause: str
    fix: str
    noise: str
    reveals: str
    zone: str


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def maybe(v: str) -> str:
    return v[0].upper() + v[1:]


def _r_whistle(world: World) -> list[str]:
    out: list[str] = []
    vent = world.entities.get("vent")
    bean = world.entities.get("soybean")
    if not vent or not bean:
        return out
    if bean.stuck_in == "vent" and vent.open and bean.meters.get("stuck", 0) >= THRESHOLD:
        sig = ("whistle",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        for e in world.entities.values():
            if e.kind == "character":
                e.memes["unease"] = e.memes.get("unease", 0) + 1
        out.append("A thin whistle sang from the vent like a hidden reed in the wall.")
    return out


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    elder = world.entities.get("elder")
    if not elder:
        return out
    if elder.memes.get("misunderstanding", 0) >= THRESHOLD and ("warned",) not in world.fired:
        world.fired.add(("warned",))
        elder.memes["worry"] = elder.memes.get("worry", 0) + 1
        out.append("The elder crossed her arms and thought the little whistle must be a trick of a sprite.")
    return out


def _r_solve(world: World) -> list[str]:
    out: list[str] = []
    bean = world.entities.get("soybean")
    hero = world.entities.get("hero")
    elder = world.entities.get("elder")
    if not bean or not hero or not elder:
        return out
    if bean.stuck_in == "" and bean.meters.get("freed", 0) >= THRESHOLD and ("solve",) not in world.fired:
        world.fired.add(("solve",))
        hero.memes["joy"] = hero.memes.get("joy", 0) + 1
        elder.memes["worry"] = 0.0
        elder.memes["relief"] = elder.memes.get("relief", 0) + 1
        out.append("When the soybean slipped free, the whistle stopped at once, and the mystery was solved.")
    return out


RULES = [_r_whistle, _r_misunderstanding, _r_solve]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    for s in produced:
        world.say(s)
    return produced


SETTINGS = {
    "inn": Setting(
        place="the old river inn",
        detail="Its rafters were low, and a round vent looked down from the wall.",
        affords={"solve"},
    ),
    "kitchen": Setting(
        place="the hearth kitchen",
        detail="A warm fire glowed there, and a square vent breathed above the stones.",
        affords={"solve"},
    ),
    "harbor": Setting(
        place="the little harbor shed",
        detail="The boards smelled of salt, and a vent near the roof whistled in the wind.",
        affords={"solve"},
    ),
}

MYSTERIES = {
    "vent": Mystery(
        id="vent",
        clue="a whisper in the wall",
        cause="a soybean rolled into the vent",
        fix="draw it out with a bent spoon",
        noise="whistled",
        reveals="the soybean was trapped behind the grate",
        zone="vent",
    ),
    "bell": Mystery(
        id="bell",
        clue="a lonely ring in the rafters",
        cause="a soybean tapped against a hanging bell rope",
        fix="nudge it free with a long stick",
        noise="rang",
        reveals="the soybean had bumped the rope each time the wind rose",
        zone="rafters",
    ),
    "chimney": Mystery(
        id="chimney",
        clue="a soft hum from above the fire",
        cause="a soybean slipped into the chimney ledge",
        fix="reach it with tongs and a careful hand",
        noise="hummed",
        reveals="the soybean was stuck where warm air curled",
        zone="chimney",
    ),
}

GIRL_NAMES = ["Mira", "Nora", "Lina", "Tess", "Ada", "Elsie", "Iris"]
BOY_NAMES = ["Finn", "Evan", "Hugo", "Owen", "Jasper", "Noah", "Theo"]
TRAITS = ["curious", "brave", "patient", "bright", "gentle", "merry"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, mystery) for place in SETTINGS for mystery in MYSTERIES]


@dataclass
class StoryEntityConfig:
    hero_type: str
    elder_type: str


def build_story_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"curiosity": 1.0},
        memes={"curiosity": 1.0},
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=params.elder,
        label=f"the {params.elder}",
        meters={"worry": 0.0},
        memes={"worry": 0.0},
    ))
    soybean = world.add(Entity(
        id="soybean",
        kind="thing",
        type="soybean",
        label="soybean",
        phrase="a single dry soybean",
        location=setting.place,
        stuck_in="vent",
        meters={"stuck": 1.0},
        memes={"mystery": 1.0},
    ))
    vent = world.add(Entity(
        id="vent",
        kind="thing",
        type="vent",
        label="vent",
        phrase="a wall vent",
        location=setting.place,
        open=True,
        meters={"echo": 1.0},
    ))
    boat = world.add(Entity(
        id="boat",
        kind="thing",
        type="boat",
        label="little boat",
        phrase="a little river boat",
        location=setting.place,
        meters={"voyage": 1.0},
    ))
    world.facts.update(hero=hero, elder=elder, soybean=soybean, vent=vent, boat=boat, mystery=mystery, setting=setting)

    world.say(
        f"Once, in {setting.place}, there lived a {params.trait} child named {params.name} who loved a good voyage and a good riddle."
    )
    world.say(f"{params.name} had sailed the little boat to the inn with {params.elder} to bring home supper and a sack of soybeans.")
    world.para()
    world.say(setting.detail)
    world.say(f"Then they heard {mystery.clue}, and the sound went {mystery.noise} through the room.")
    elder.memes["misunderstanding"] = 1.0
    world.say(f'"That is a sprite behind the boards," said {elder.label}, and that was a grand misunderstanding.')
    world.para()
    world.say(f"But {params.name} listened close, followed the sound, and guessed that {mystery.reveals}.")
    world.say(f"So {params.name} used {mystery.fix}, and the bent tool reached the dark gap where the soybean hid.")
    soybean.stuck_in = ""
    soybean.meters["stuck"] = 0.0
    soybean.meters["freed"] = 1.0
    propagate(world)
    world.para()
    world.say(
        f"When the soybean came out, the vent grew quiet, the elder laughed at the mistake, and the voyage could go on with a lighter heart."
    )
    world.say(
        f"{params.name} tucked the rescued soybean into the sack, and the old river inn felt peaceful again."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, elder, mystery = f["hero"], f["elder"], f["mystery"]
    return [
        f'Write a folk-tale for a young child about a soybean, a vent, and a voyage that ends with a solved mystery.',
        f"Tell a gentle story in which {hero.label} and {elder.label} hear a strange sound from a vent and discover why it happens.",
        f"Write a rhyme-laced story where a child finds out what made the wall vent sing during a little voyage.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, mystery = f["hero"], f["elder"], f["mystery"]
    return [
        QAItem(
            question=f"Who heard the strange sound in {world.setting.place}?",
            answer=f"{hero.label} and {elder.label} heard it together while they were on a little voyage.",
        ),
        QAItem(
            question="What was making the mystery sound?",
            answer=f"A soybean had rolled into the vent, so the wall made a thin whistle until it was freed.",
        ),
        QAItem(
            question="What did the child use to solve the mystery?",
            answer=f"{hero.label} used {mystery.fix} and a careful hand to reach the soybean.",
        ),
        QAItem(
            question="Why was the elder confused at first?",
            answer="The elder thought the noise was something magical, but it was only the trapped soybean and the wind.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a soybean?",
            answer="A soybean is a small bean that grows on a plant and can be used for food.",
        ),
        QAItem(
            question="What is a vent?",
            answer="A vent is an opening that lets air move in and out of a room or wall.",
        ),
        QAItem(
            question="What is a voyage?",
            answer="A voyage is a trip, often by boat or ship, that takes you from one place to another.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something strange that people do not understand at first.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.stuck_in:
            bits.append(f"stuck_in={e.stuck_in}")
        if e.open:
            bits.append("open=True")
        lines.append(f"{e.id}: {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("causes", mid, m.cause))
        lines.append(asp.fact("fixes", mid, m.fix))
    return "\n".join(lines)


ASP_RULES = r"""
% A mystery is solvable when it has a cause and a fix.
solvable(M) :- mystery(M), causes(M,_), fixes(M,_).

valid_story(Place, Mystery) :- setting(Place), mystery(Mystery), solvable(Mystery), affords(Place,solve).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


def explain_rejection(place: str, mystery: str) -> str:
    return f"(No story: the tale at {place} cannot solve the {mystery} mystery with the current rules.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world about a soybean, a vent, and a voyage.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
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
    combos = valid_combos()
    if args.place and args.mystery and (args.place, args.mystery) not in combos:
        raise StoryError(explain_rejection(args.place, args.mystery))
    choices = [c for c in combos if (not args.place or c[0] == args.place) and (not args.mystery or c[1] == args.mystery)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery = rng.choice(choices)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, elder=elder, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_story_world(params)
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
    StoryParams(place="inn", mystery="vent", name="Mira", gender="girl", elder="grandmother", trait="curious"),
    StoryParams(place="kitchen", mystery="chimney", name="Finn", gender="boy", elder="grandfather", trait="gentle"),
    StoryParams(place="harbor", mystery="bell", name="Tess", gender="girl", elder="grandmother", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:\n")
        for place, mystery in combos:
            print(f"  {place:10} {mystery}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
