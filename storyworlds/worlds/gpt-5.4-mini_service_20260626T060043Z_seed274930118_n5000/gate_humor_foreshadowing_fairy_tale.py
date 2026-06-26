#!/usr/bin/env python3
"""
Fairy-tale storyworld: a gate, a little humor, and a foreshadowed fix.

A child in a small kingdom wants to pass through a gate to reach a prize in a
nearby place. The gate is old enough to complain, and its squeak can wake a
sleeping watcher. A gentle helper predicts the trouble, notices a comic clue,
and fetches the right simple remedy so the journey can end happily.

The world tracks:
- physical meters: rust, squeak, grease, sleep, noise, open, closeness
- emotional memes: wonder, worry, patience, delight, mischief, relief

The story logic is intentionally small and state-driven:
- pushing an untended gate raises noise and squeak
- loud noise can wake the sleepy watcher
- foreshadowing appears as a tiny hint before the loud moment
- the compromise uses the one remedy that genuinely suits the gate

The prose aims for a fairy-tale voice with child-friendly humor.
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "witch", "fairy", "mother", "mom", "woman"}
        male = {"boy", "prince", "king", "wizard", "father", "dad", "man"}
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
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    effect: str
    weather: str
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
class Remedy:
    id: str
    label: str
    tool_phrase: str
    use_phrase: str
    tail: str
    helps: set[str]
    quiets: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

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
        other = World(self.setting)
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.facts = copy.deepcopy(self.facts)
        other.paragraphs = [[]]
        return other

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _apply_push(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts["hero"]
    gate = world.get("gate")
    if child.meters.get("force", 0) >= THRESHOLD and gate.meters.get("open", 0) < THRESHOLD:
        sig = ("push",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        gate.meters["squeak"] = gate.meters.get("squeak", 0) + 1
        gate.meters["noise"] = gate.meters.get("noise", 0) + 1
        out.append("The old gate gave a long squeak, like a goose trying to sing with a cold.")
    return out


def _apply_wake(world: World) -> list[str]:
    out: list[str] = []
    watcher = world.get("watcher")
    gate = world.get("gate")
    if gate.meters.get("noise", 0) >= THRESHOLD and watcher.meters.get("sleep", 0) >= THRESHOLD:
        sig = ("wake",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        watcher.meters["sleep"] = 0
        watcher.memes["grump"] = watcher.memes.get("grump", 0) + 1
        out.append("Behind the hedge, the sleepy watcher stirred and opened one eye.")
    return out


CAUSAL_RULES = [_apply_push, _apply_wake]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def gate_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in {"beyond_gate"} and activity.id == "pass_gate"


def select_remedy(activity: Activity, prize: Prize) -> Optional[Remedy]:
    for remedy in REMEDIES:
        if activity.keyword in remedy.helps and "squeak" in remedy.quiets:
            return remedy
    return None


def predict(world: World, hero: Entity, activity: Activity) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters["force"] = 1
    propagate(sim, narrate=False)
    return {
        "noise": sim.get("gate").meters.get("noise", 0),
        "woke": sim.get("watcher").meters.get("sleep", 0) < THRESHOLD,
    }


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "brave")
    world.say(
        f"There once was a little {trait} {hero.type} named {hero.id}, who loved to explore places "
        f"that looked as if they had been dreamt by moonlight."
    )


def foreshadow(world: World, hero: Entity, gate: Entity) -> None:
    world.say(
        f"At the path's end stood a green gate with peeling paint and a brass latch shaped like a fish."
    )
    world.say(
        f"It looked friendly enough, but one hinge held itself crooked, as if it were saving up a joke."
    )
    world.facts["foreshadow"] = "crooked hinge"


def desire(world: World, hero: Entity, prize: Entity, activity: Activity) -> None:
    hero.memes["wonder"] = hero.memes.get("wonder", 0) + 1
    world.say(
        f"{hero.id} wanted to {activity.verb} and reach the {prize.label} beyond the gate."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} eyes shone, because the prize was said to be as shiny as a dropped star."
    )


def warn(world: World, elder: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict(world, hero, activity)
    if pred["noise"] < THRESHOLD:
        return False
    world.facts["predicted_noise"] = pred["noise"]
    world.say(
        f'"Mind the gate," {elder.pronoun("subject")} said. "A loud shove can wake the watcher, and then the whole lane will be grumpy before breakfast."'
    )
    return True


def stubborn_move(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["mischief"] = hero.memes.get("mischief", 0) + 1
    hero.meters["force"] = hero.meters.get("force", 0) + 1
    world.say(
        f"But {hero.id} was curious, and curiosity is a kind of small horse that never likes to wait."
    )
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush}.")
    propagate(world, narrate=True)


def remedy_offer(world: World, elder: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Remedy]:
    remedy = select_remedy(activity, prize)
    if remedy is None:
        return None
    gate = world.get("gate")
    gate.meters["grease"] = gate.meters.get("grease", 0) + 1
    gate.meters["squeak"] = 0
    gate.meters["noise"] = 0
    world.say(
        f"{elder.id} lifted a tiny tin and smiled. " 
        f'"How about we use the {remedy.label} first?"'
    )
    world.say(
        f"{hero.id} sniffed the air and laughed. The tin smelled faintly of oranges and cleverness."
    )
    return remedy


def accept(world: World, hero: Entity, elder: Entity, remedy: Remedy, prize: Prize) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    hero.memes["delight"] = hero.memes.get("delight", 0) + 1
    gate = world.get("gate")
    gate.meters["open"] = 1
    world.say(
        f"They {remedy.tail}. The gate moved with a soft little sigh, like a cat waking from a nap."
    )
    world.say(
        f"{hero.id} slipped through at once, and the {prize.label} beyond the hedge turned out to be exactly as bright as hoped."
    )
    world.say(
        f"Even the watcher smiled, because the day's biggest trouble had been only a squeaky hinge."
    )


SETTINGS = {
    "cottage": Setting(place="the cottage garden", affords={"pass_gate"}),
    "orchard": Setting(place="the orchard path", affords={"pass_gate"}),
    "castle": Setting(place="the castle wall", affords={"pass_gate"}),
}

ACTIVITIES = {
    "pass_gate": Activity(
        id="pass_gate",
        verb="pass through the gate",
        gerund="passing through the gate",
        rush="push hard at the gate",
        effect="noise",
        weather="",
        keyword="gate",
        tags={"gate", "humor", "foreshadowing"},
    )
}

PRIZES = {
    "berries": Prize(
        label="basket of berries",
        phrase="a basket of bright berries",
        type="basket",
        region="beyond_gate",
    ),
    "lantern": Prize(
        label="silver lantern",
        phrase="a silver lantern with a ribbon",
        type="lantern",
        region="beyond_gate",
    ),
}

REMEDIES = [
    Remedy(
        id="oil",
        label="tin of oil",
        tool_phrase="a tin of oil",
        use_phrase="grease the hinge",
        tail="they oiled the hinge and rubbed the squeak away",
        helps={"gate"},
        quiets={"squeak"},
    )
]

GIRL_NAMES = ["Mina", "Lily", "Ava", "Nora", "Elsie", "Pip"]
BOY_NAMES = ["Theo", "Finn", "Jasper", "Owen", "Robin", "Bram"]
TRAITS = ["brave", "curious", "cheerful", "merry", "sly", "gentle"]


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
            for prize_id in PRIZES:
                combos.append((place, act_id, prize_id))
    return combos


def explain_rejection() -> str:
    return "(No story: the requested choices do not describe a gate tale that can be resolved fairly.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale gate storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["mother", "father", "witch", "wizard"])
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
        raise StoryError(explain_rejection())
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["mother", "father", "witch", "wizard"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, elder=elder, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", params.trait]))
    elder = world.add(Entity(id="elder", kind="character", type=params.elder, label=params.elder))
    gate = world.add(Entity(id="gate", type="gate", label="gate"))
    watcher = world.add(Entity(id="watcher", kind="character", type="goose", label="watcher"))
    watcher.meters["sleep"] = 1
    prize = world.add(Entity(id="prize", type="treasure", label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase))

    world.facts.update(hero=hero, elder=elder, gate=gate, watcher=watcher, prize=prize, activity=ACTIVITIES[params.activity])

    introduce(world, hero)
    foreshadow(world, hero, gate)
    world.para()
    desire(world, hero, prize, ACTIVITIES[params.activity])
    warn(world, elder, hero, ACTIVITIES[params.activity], prize)
    stubborn_move(world, hero, ACTIVITIES[params.activity])
    world.para()
    remedy = remedy_offer(world, elder, hero, ACTIVITIES[params.activity], prize)
    if remedy:
        accept(world, hero, elder, remedy, prize)
        world.facts["resolved"] = True
        world.facts["remedy"] = remedy
    else:
        world.say("No one could find a proper remedy, so the gate stayed stubborn and the day ended in a sigh.")
        world.facts["resolved"] = False
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    return [
        f"Write a short fairy tale about {hero.id} and a squeaky gate that hides {prize.label} beyond it.",
        f"Tell a child-friendly story where a crooked gate makes a funny sound, a warning comes true, and a clever remedy helps.",
        f"Write a gentle fairy tale with humor and foreshadowing about a child who wants to pass through a gate.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    prize = f["prize"]
    remedy = f.get("remedy")
    qa = [
        QAItem(
            question=f"Who wanted to go through the gate?",
            answer=f"{hero.id} wanted to go through the gate because {hero.pronoun('subject')} hoped to reach {prize.label}.",
        ),
        QAItem(
            question=f"What warning did the elder give about the gate?",
            answer=f"{elder.label} warned that a loud shove could wake the watcher and make the lane grumpy.",
        ),
        QAItem(
            question=f"What funny clue hinted that the gate might cause trouble?",
            answer="One hinge held itself crooked, as if it were saving up a joke, which hinted that the gate would squeak.",
        ),
    ]
    if f.get("resolved") and remedy:
        qa.append(
            QAItem(
                question="How was the gate fixed so the child could pass quietly?",
                answer=f"They used the {remedy.label} and oiled the hinge until the squeak went away.",
            )
        )
        qa.append(
            QAItem(
                question=f"What changed by the end of the story?",
                answer=f"{hero.id} went through the gate happily, and the watcher stayed calm instead of waking in a grumble.",
            )
        )
    return qa


WORLD_QA = {
    "gate": [
        QAItem(question="What is a gate?", answer="A gate is a door or barrier that opens in a fence or wall so people or animals can pass through."),
        QAItem(question="Why do gates sometimes squeak?", answer="A gate can squeak when its hinges are old, dry, or rusty and need a little oil."),
    ],
    "humor": [
        QAItem(question="What makes a story funny?", answer="A story can be funny when something surprises us in a gentle way, like a silly sound or a proud character acting a little too grand."),
    ],
    "foreshadowing": [
        QAItem(question="What is foreshadowing?", answer="Foreshadowing is a small hint that tells readers something important may happen later."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_QA["gate"] + WORLD_QA["humor"] + WORLD_QA["foreshadowing"]


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(cottage).
place(orchard).
place(castle).

activity(pass_gate).
prize(berries).
prize(lantern).

affords(cottage,pass_gate).
affords(orchard,pass_gate).
affords(castle,pass_gate).

valid(P,A,R) :- affords(P,A), place(P), activity(A), prize(R).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for r in PRIZES:
        lines.append(asp.fact("prize", r))
    for p, setting in SETTINGS.items():
        for a in setting.affords:
            lines.append(asp.fact("affords", p, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: ASP matches Python ({len(python_set)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(python_set - asp_set))
    print("asp-only:", sorted(asp_set - python_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
    StoryParams(place="cottage", activity="pass_gate", prize="berries", name="Mina", gender="girl", elder="mother", trait="curious"),
    StoryParams(place="orchard", activity="pass_gate", prize="lantern", name="Theo", gender="boy", elder="wizard", trait="brave"),
    StoryParams(place="castle", activity="pass_gate", prize="berries", name="Elsie", gender="girl", elder="father", trait="merry"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
