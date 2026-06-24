#!/usr/bin/env python3
"""
storyworlds/worlds/pecan_doughnut_everyday_humor_rhyming_story.py
==================================================================

A tiny standalone storyworld about a child, a pecan doughnut, and an everyday
messy moment that ends in a funny, rhyming compromise.

Seed inspiration:
- pecan
- doughnut
- everyday
- Humor
- Rhyming Story

The world is intentionally small:
- one child wants an everyday treat
- one grown-up worries about crumbs, glaze, and a sticky shirt
- one sensible helper object keeps the story safe and neat
- the ending proves what changed in the world state
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the kitchen"
    affords: set[str] = field(default_factory=set)


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str = "doughnut"
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    prep: str
    tail: str
    covers: set[str]
    guards: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(e.protective and region in e.covers for e in self.worn_items(actor))

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


def _r_risk(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("crumbly", 0.0) < THRESHOLD and actor.meters.get("sticky", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.type != "shirt":
                continue
            if world.covered(actor, "torso"):
                continue
            sig = ("risk", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["crumbly"] = item.meters.get("crumbly", 0.0) + 1
            item.meters["sticky"] = item.meters.get("sticky", 0.0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} shirt got crumbly and sticky.")
    return out


def _r_hassle(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("crumbly", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("hassle", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["cleanup"] = carer.meters.get("cleanup", 0.0) + 1
        out.append(f"That would make more cleanup for {carer.label}.")
    return out


CAUSAL_RULES = [("risk", _r_risk), ("hassle", _r_hassle)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for _, rule in CAUSAL_RULES:
            got = rule(world)
            if got:
                changed = True
                produced.extend(got)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mess(world: World, actor: Entity, snack: Snack, snack_id: str) -> dict:
    sim = world.copy()
    _do_eat(sim, sim.get(actor.id), snack, narrate=False)
    item = sim.get(snack_id)
    return {
        "ruined": bool(item.meters.get("crumbly", 0.0) >= THRESHOLD or item.meters.get("sticky", 0.0) >= THRESHOLD),
        "cleanup": sum(e.meters.get("cleanup", 0.0) for e in sim.characters()),
    }


def _do_eat(world: World, actor: Entity, snack: Snack, narrate: bool = True) -> None:
    if snack.id not in world.setting.affords:
        return
    world.zone = set(snack.zone)
    actor.meters["crumbly"] = actor.meters.get("crumbly", 0.0) + 1
    actor.meters["sticky"] = actor.meters.get("sticky", 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def rhyme(line: str) -> str:
    return line


def intro(world: World, child: Entity) -> None:
    world.say(rhyme(f"{child.id} was a small, bright child with a grin like a kite."))
    world.say(rhyme("Everyday breakfast felt grand when the day felt light."))


def love_snack(world: World, child: Entity, snack: Snack) -> None:
    child.memes["want"] = child.memes.get("want", 0.0) + 1
    world.say(rhyme(f"{child.id} loved {snack.phrase}; it smelled sweet as a song."))
    world.say(rhyme("The pecan on top made the doughnut look jaunty and strong."))


def bring_snack(world: World, parent: Entity, child: Entity, snack: Snack) -> None:
    world.say(rhyme(f"{parent.label_word if hasattr(parent, 'label_word') else parent.label} set {child.id} a plate for the treat."))
    world.say(rhyme(f"The little doughnut waited there, round and neat."))


def arrive(world: World, child: Entity, parent: Entity) -> None:
    world.say(rhyme(f"One everyday morning, {child.id} and {parent.label} stood by the table."))
    world.say(rhyme("The kitchen was warm, and the toast was able."))


def want(world: World, child: Entity, parent: Entity, snack: Snack) -> None:
    child.memes["desire"] = child.memes.get("desire", 0.0) + 1
    world.say(rhyme(f"{child.id} wanted to bite the doughnut right away."))
    world.say(rhyme(f"But {parent.label} lifted a finger and said, “First let’s think, okay?”"))


def warn(world: World, parent: Entity, child: Entity, snack: Snack, shirt: Entity) -> bool:
    pred = predict_mess(world, child, snack, shirt.id)
    if not pred["ruined"]:
        return False
    world.facts["predicted_cleanup"] = pred["cleanup"]
    world.say(rhyme(f"“Your shirt will get {snack.soil},” {parent.label} said with a blink."))
    world.say(rhyme("“Then I’ll clean and scrub, and that is not my favorite sink.”"))
    return True


def defy(world: World, child: Entity, snack: Snack) -> None:
    child.memes["frustration"] = child.memes.get("frustration", 0.0) + 1
    world.say(rhyme(f"{child.id} took one hop and tried to zoom."))
    world.say(rhyme(f"But the doughnut was crumbly, like a joke in a room."))


def offer_helper(world: World, parent: Entity, child: Entity, snack: Snack, shirt: Entity) -> Optional[Helper]:
    if snack.mess not in {"crumbly", "sticky"}:
        return None
    helper = HELPERS["plate"]
    if shirt.type != "shirt":
        return None
    item = world.add(Entity(
        id=helper.id,
        type="plate",
        label=helper.label,
        owner=child.id,
        caretaker=parent.id,
        protective=True,
        covers=set(helper.covers),
        plural=helper.plural,
    ))
    item.worn_by = None
    if predict_mess(world, child, snack, shirt.id)["ruined"]:
        del world.entities[item.id]
        return None
    world.say(rhyme(f"{parent.label} smiled wide and said, “Here is a cleaner way.”"))
    world.say(rhyme(f"“Use the plate and napkin, and you still get your play.”"))
    return helper


def accept(world: World, parent: Entity, child: Entity, snack: Snack, helper: Helper) -> None:
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    child.memes["frustration"] = 0.0
    world.say(rhyme(f"{child.id} laughed, then clapped: “That plan is grand!”"))
    world.say(rhyme(f"They set the doughnut on the plate, so it stayed in hand."))
    world.say(rhyme(f"Then {child.id} ate the pecan doughnut with a napkin near,"))
    world.say(rhyme(f"and {parent.label} smiled at the everyday cheer."))


def tell(setting: Setting, snack: Snack, hero_name: str = "Milo", hero_type: str = "boy",
         parent_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="Mom"))
    shirt = world.add(Entity(id="shirt", type="shirt", label="shirt", phrase="a clean shirt", owner=child.id, caretaker=parent.id))
    world.facts.update(child=child, parent=parent, shirt=shirt, snack=snack)

    intro(world, child)
    love_snack(world, child, snack)
    bring_snack(world, parent, child, snack)
    world.para()
    arrive(world, child, parent)
    want(world, child, parent, snack)
    warn(world, parent, child, snack, shirt)
    defy(world, child, snack)
    world.para()
    helper = offer_helper(world, parent, child, snack, shirt)
    if helper:
        accept(world, parent, child, snack, helper)
    world.facts["helper"] = helper
    world.facts["resolved"] = helper is not None
    return world


@dataclass
class StoryParams:
    place: str
    snack: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"doughnut"}),
    "table": Setting(place="the breakfast table", affords={"doughnut"}),
}

SNACKS = {
    "doughnut": Snack(
        id="doughnut",
        label="pecan doughnut",
        phrase="a pecan doughnut",
        mess="crumbly",
        soil="crumbly and sticky",
        zone={"torso"},
        keyword="pecan",
        tags={"pecan", "doughnut", "everyday"},
    ),
}

HELPERS = {
    "plate": Helper(
        id="plate",
        label="a small plate",
        prep="set it on a plate",
        tail="kept the crumbs off the shirt",
        covers={"torso"},
        guards={"crumbly", "sticky"},
    ),
    "napkin": Helper(
        id="napkin",
        label="a napkin",
        prep="wrap it in a napkin",
        tail="kept the sticky bits in one place",
        covers={"torso"},
        guards={"sticky"},
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Luna", "Ivy"]
BOY_NAMES = ["Milo", "Finn", "Theo", "Ben"]
TRAITS = ["cheery", "brave", "busy", "bouncy"]


def valid_combos() -> list[tuple[str, str]]:
    return [("kitchen", "doughnut"), ("table", "doughnut")]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming story world about a pecan doughnut and an everyday compromise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.snack:
        combos = [c for c in combos if c[1] == args.snack]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, snack = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, snack=snack, name=name, gender=gender, parent=parent, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    snack = f["snack"]
    return [
        'Write a short rhyming story for a small child about a pecan doughnut and an everyday breakfast.',
        f"Tell a humorous story where {f['child'].id} wants to eat {snack.phrase} but {f['parent'].label} worries about a sticky shirt.",
        'Write a gentle, funny story that includes the words "pecan", "doughnut", and "everyday".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, snack = f["child"], f["parent"], f["snack"]
    return [
        QAItem(
            question=f"What did {child.id} want to eat in the story?",
            answer=f"{child.id} wanted to eat {snack.phrase}, a sweet everyday treat with a pecan on top.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the snack?",
            answer=f"{parent.label} worried that the {snack.label} would make {child.pronoun('possessive')} shirt {snack.soil}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The child ate the pecan doughnut neatly with a plate and napkin, so the shirt stayed clean.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pecan?",
            answer="A pecan is a type of nut with a rich, buttery taste. People often put it in pies, cookies, or on top of sweet treats.",
        ),
        QAItem(
            question="What is a doughnut?",
            answer="A doughnut is a sweet round snack, often fried or baked, and sometimes covered with sugar or glaze.",
        ),
        QAItem(
            question="What does everyday mean?",
            answer="Everyday means ordinary or usual, like something that happens on a regular day.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], ""]
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
snack_valid(P) :- place(P), affords(P, doughnut).
risk(S) :- snack(doughnut), worn_on(shirt, torso), splashes(doughnut, torso).
fix(plate) :- helper(plate), covers(plate, torso), guards(plate, crumbly), guards(plate, sticky).
valid_story(P) :- snack_valid(P), fix(plate), risk(doughnut).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for sid, snack in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        lines.append(asp.fact("splashes", sid, "torso"))
        lines.append(asp.fact("worn_on", "shirt", "torso"))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for c in sorted(h.covers):
            lines.append(asp.fact("covers", hid, c))
        for g in sorted(h.guards):
            lines.append(asp.fact("guards", hid, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {("kitchen",), ("table",)}
    if asp_set == py_set:
        print("OK: ASP gate matches Python valid_combos().")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", sorted(asp_set))
    print("PY :", sorted(py_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], SNACKS[params.snack], params.name, params.gender, params.parent)
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
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [
            StoryParams(place="kitchen", snack="doughnut", name="Milo", gender="boy", parent="mother", trait="bouncy"),
            StoryParams(place="table", snack="doughnut", name="Mia", gender="girl", parent="father", trait="cheery"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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
