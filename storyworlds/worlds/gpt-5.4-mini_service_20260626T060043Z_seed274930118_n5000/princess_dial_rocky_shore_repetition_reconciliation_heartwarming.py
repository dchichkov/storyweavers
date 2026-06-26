#!/usr/bin/env python3
"""
A small storyworld about a princess, a stubborn dial, and a rocky shore.

The seed tale that shaped this world:
A princess visits a rocky shore and finds a brass dial mounted on an old
harbor box. She keeps trying to turn it, but the dial is stiff and the sea
spray makes her careful. A worried caretaker warns that the salt could spoil
her fine cloak. The princess tries again and again, gets a little frustrated,
and then they work together with a cloth wrap and a kinder grip. In the end,
the dial turns, the worry softens, and the princess feels happy that she did
not have to choose between the thing she loved and the thing she wore.

This file follows the Storyweavers contract:
- standalone stdlib script
- typed entities with meters and memes
- reasonableness gate + inline ASP twin
- story + prompts + story QA + world QA
- human-readable, child-facing, state-driven prose
"""

from __future__ import annotations

import argparse
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("salt", "dirty", "workload"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "worry", "frustration", "love", "calm", "reconciliation"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "princess":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the rocky shore"
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

    def copy(self) -> "World":
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["salt"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soak", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["salt"] += 1
            item.meters["dirty"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got salty and damp.")
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] += 1
        out.append(f"That would mean more work for {carer.label}.")
    return out


CAUSAL_RULES = [Rule("soak", _r_soak), Rule("workload", _r_workload)]


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


def setting_detail(setting: Setting) -> str:
    return "The rocky shore was bright with gray stones, little tide pools, and white foam."


def turn_stubborn_dial(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.meters["salt"] += 1
    actor.memes["joy"] += 0.5
    propagate(world, narrate=narrate)


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    turn_stubborn_dial(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"soiled": prize.meters["dirty"] >= THRESHOLD, "workload": sum(e.meters["workload"] for e in sim.characters())}


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str = "Iris", gender: str = "girl", parent_type: str = "mother") -> World:
    world = World(setting)
    princess = world.add(Entity(id=name, kind="character", type="princess", traits=["little", "kind", "persistent"]))
    parent = world.add(Entity(id="Caretaker", kind="character", type=parent_type, label="the caretaker"))
    prize = world.add(Entity(id="cloak", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=princess.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural))
    dial = world.add(Entity(id="dial", type="dial", label="brass dial", phrase="a brass dial", owner="shore_box"))

    princess.worn_by = None
    prize.worn_by = princess.id

    world.say(f"{princess.id} was a little princess who loved the sea air and shiny things.")
    world.say(f"On the rocky shore, {princess.id} found {dial.phrase} on an old harbor box.")
    world.say(f"{princess.id} wanted to {activity.verb}, and {activity.gerund} felt exciting to {princess.pronoun('object')}.")

    world.para()
    world.say(setting_detail(setting))
    world.say(f"{princess.id} reached for the dial and tried to turn it once.")
    turn_stubborn_dial(world, princess, activity)

    world.say(f"Then {princess.id} tried again. And again. The dial would only budge a little, with a tiny squeak.")
    princess.memes["frustration"] += 1
    if predict_mess(world, princess, activity, prize.id)["soiled"]:
        world.say(f'"If you keep leaning in that close, your {prize.label} could get {activity.soil}," {parent.label} said gently.')
        princess.memes["worry"] += 1

    world.para()
    world.say(f"{princess.id} frowned, then took a breath. {princess.pronoun().capitalize()} did not want to ruin {princess.pronoun('possessive')} {prize.label}.")
    world.say(f"So {princess.id} tried one more careful time, but the dial still stuck.")
    turn_stubborn_dial(world, princess, activity)

    gear_def = select_gear(activity, prize)
    if gear_def is None:
        raise StoryError("No kind, reasonable gear can protect this prize from the rocky-shore dial.")
    gear = world.add(Entity(id=gear_def.id, type="gear", label=gear_def.label, owner=princess.id, caretaker=parent.id, protective=True, covers=set(gear_def.covers), plural=gear_def.plural))
    gear.worn_by = princess.id

    world.para()
    world.say(f"At last, {princess.id}'s {parent.label} smiled and held up {gear_def.label}.")
    world.say(f'"Let us do it together," said the {parent.type}. "We can keep you dry and still help the dial move."')
    princess.memes["reconciliation"] += 1
    princess.memes["calm"] += 1
    princess.memes["love"] += 1
    princess.memes["frustration"] = 0.0
    world.say(f"{princess.id} nodded, and they wrapped the cloth, held the dial from both sides, and turned it slowly together.")
    world.say(f"This time the dial clicked, then spun smoothly. A soft bell sounded from the shore box, and {princess.id} smiled so hard her cheeks looked warm.")
    world.say(f"{princess.id}'s {prize.label} stayed clean, and the rocky shore felt bright and friendly by the end.")

    world.facts.update(hero=princess, parent=parent, prize=prize, dial=dial, activity=activity, gear=gear, setting=setting)
    return world


SETTINGS = {
    "rocky_shore": Setting(place="the rocky shore", affords={"dial"}),
}

ACTIVITIES = {
    "dial": Activity(
        id="dial",
        verb="turn the dial",
        gerund="turning the dial",
        rush="twist the dial quickly",
        mess="salt",
        soil="sprayed with salt",
        zone={"torso"},
        keyword="dial",
    )
}

PRIZES = {
    "cloak": Prize(
        label="cloak",
        phrase="a soft blue cloak",
        type="cloak",
        region="torso",
    ),
    "dress": Prize(
        label="dress",
        phrase="a pretty dress",
        type="dress",
        region="torso",
        genders={"girl"},
    ),
}

GEAR = [
    Gear(
        id="oilskin_wrap",
        label="an oilskin wrap",
        covers={"torso"},
        guards={"salt"},
        prep="wrap up in an oilskin wrap",
        tail="wrapped up in the oilskin and turned the dial together",
    ),
    Gear(
        id="hooded_cape",
        label="a hooded cape",
        covers={"torso"},
        guards={"salt"},
        prep="put on a hooded cape first",
        tail="put on the hooded cape and tried again",
    ),
]

GIRL_NAMES = ["Iris", "Mina", "Nora", "Luna", "Elin", "Ruby"]
BOY_NAMES = ["Owen", "Jules", "Theo"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a heartwarming story about a princess, a dial, and a gentle compromise on a rocky shore.',
        f"Tell a short story where {f['hero'].id} wants to turn a dial at the rocky shore but worries about {f['prize'].label}.",
        "Write a simple story that repeats a small attempt, then ends with cooperation and relief.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little princess who loved the rocky shore and the brass dial.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about {hero.id}'s {prize.label}?",
            answer=f"{parent.label.capitalize()} worried because the sea spray and the stuck dial could leave {prize.label} salty and damp.",
        ),
        QAItem(
            question=f"How did {hero.id} and {parent.label} solve the problem?",
            answer=f"They used {gear.label} and turned the dial together, so {hero.id} could keep playing without ruining the {prize.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dial?",
            answer="A dial is a round part you can turn to choose, adjust, or start something.",
        ),
        QAItem(
            question="What is the rocky shore like?",
            answer="A rocky shore is a place by the sea with stones, waves, and salty spray.",
        ),
        QAItem(
            question="Why can salt water be messy on clothes?",
            answer="Salt water can make clothes damp and sticky, so they may need washing and drying afterward.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:12} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp

    lines = []
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


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a princess, a dial, and a heartwarming rocky-shore reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def explain_rejection() -> str:
    return "(No story: the rocky-shore dial story needs a prize on the torso that the salt can actually reach.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.gender and args.name is None and args.gender == "boy":
        pass
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError(explain_rejection())
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(PRIZES[prize].genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent)


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
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place=p, activity=a, prize=r, name="Iris", gender="girl", parent="mother")) for p, a, r in valid_combos()]
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
