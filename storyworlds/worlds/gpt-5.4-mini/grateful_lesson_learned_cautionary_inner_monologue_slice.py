#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/grateful_lesson_learned_cautionary_inner_monologue_slice.py
===========================================================================================

A tiny slice-of-life storyworld about a child carrying something precious, a
quiet cautionary inner monologue, a small mistake, and a grateful lesson learned.

Seed words / instruments:
- grateful
- Lesson Learned
- Cautionary
- Inner Monologue
- Slice of Life

The domain stays small on purpose: one child, one caregiver, one fragile thing,
one safe helper, and one everyday choice that can go well or wobble.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/grateful_lesson_learned_cautionary_inner_monologue_slice.py
    python storyworlds/worlds/gpt-5.4-mini/grateful_lesson_learned_cautionary_inner_monologue_slice.py --all
    python storyworlds/worlds/gpt-5.4-mini/grateful_lesson_learned_cautionary_inner_monologue_slice.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/grateful_lesson_learned_cautionary_inner_monologue_slice.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: str = ""
    caretaker: str = ""
    materials: list[str] = field(default_factory=list)
    fragile: bool = False
    helpful: bool = False
    hot: bool = False
    has_lid: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Scene:
    place: str
    weather: str
    purpose: str
    background: str
    quiet_detail: str
    ending_image: str


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    worry: str
    risk: str
    zone: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    use: str
    cover: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.scene)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def hazard_at_risk(task: Task, fragile: Entity) -> bool:
    return fragile.fragile and task.zone in fragile.materials


def sensible_helpers() -> list[Helper]:
    return [h for h in HELPERS.values() if h.sense >= SENSE_MIN]


def helper_ok(helper: Helper) -> bool:
    return helper.sense >= SENSE_MIN


def severity(task: Task, delay: int) -> int:
    return 1 + delay


def contained(helper: Helper, task: Task, delay: int) -> bool:
    return helper.power >= severity(task, delay)


def _r_soak(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.meters["spilled"] < THRESHOLD:
            continue
        sig = ("soak", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "floor" in world.entities:
            world.get("floor").meters["mess"] += 1
        for e in world.entities.values():
            if e.kind == "character":
                e.memes["concern"] += 1
        out.append("__mess__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in ( _r_soak, ):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_spill(world: World, task: Task, fragile_id: str) -> bool:
    sim = world.copy()
    _do_task(sim, sim.get("hero"), task, narrate=False)
    return sim.get(fragile_id).meters["spilled"] >= THRESHOLD


def _do_task(world: World, hero: Entity, task: Task, narrate: bool = True) -> None:
    hero.meters["careless"] += 1
    world.get("item").meters["spilled"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, hero: Entity, adult: Entity) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"After breakfast, {hero.id} and {adult.id} moved through the quiet house "
        f"where {world.scene.background}."
    )
    world.say(
        f"{hero.id} looked at {world.scene.purpose}. {world.scene.quiet_detail}"
    )


def inner_monologue(world: World, hero: Entity, task: Task, fragile: Entity) -> None:
    hero.memes["worry"] += 1
    world.say(
        f'In {hero.pronoun("possessive")} head, {hero.id} thought, '
        f'"If I rush, I might {task.risk}. I should be careful."'
    )
    world.say(
        f'Another thought followed: "It would be nicer to finish this neatly and '
        f"feel {WORD}.""
    )


def caution(world: World, adult: Entity, hero: Entity, task: Task, fragile: Entity) -> bool:
    if not predict_spill(world, task, fragile.id):
        return False
    adult.memes["care"] += 1
    world.facts["predicted_spill"] = True
    world.say(
        f'"Slow down," {adult.id} said gently. "{hero.id}, if you hurry, '
        f"the {fragile.label} could {task.risk}."
    )
    return True


def choose_slow(world: World, hero: Entity, helper: Helper) -> None:
    hero.memes["resolve"] += 1
    world.say(
        f"{hero.id} took a breath, picked up {helper.phrase}, and decided to move "
        f"carefully instead of rushing."
    )


def mistake(world: World, hero: Entity, task: Task, fragile: Entity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"{hero.id} tried to {task.verb}, but the cup tipped, and a small spill "
        f"spread across the table."
    )
    if fragile.fragile:
        world.say(
            f"The {fragile.label} wobbled near the edge, which made everyone freeze."
        )


def fix(world: World, adult: Entity, helper: Helper, fragile: Entity) -> None:
    fragile.meters["spilled"] = 0.0
    world.get("table").meters["mess"] = 0.0
    adult.memes["relief"] += 1
    world.say(
        f"{adult.label_word.capitalize()} came over right away and used {helper.use}. "
        f"The little mess was cleaned up before it could spread."
    )
    world.say(
        f"Then {adult.id} smiled and said, \"Good job telling me. "
        f"{helper.cover} helps on days like this.\""
    )


def lesson(world: World, hero: Entity, adult: Entity, task: Task, helper: Helper) -> None:
    hero.memes["gratitude"] += 1
    hero.memes["lesson"] += 1
    world.say("For a moment, the room was quiet again.")
    world.say(
        f"Then {hero.id} felt grateful. {hero.id} had learned that careful hands, "
        f"a slow breath, and a helpful tray could keep an ordinary morning calm."
    )
    world.say(
        f"By the end, {hero.id} was walking more slowly, and the cup stayed steady "
        f"in {hero.pronoun('possessive')} hands."
    )


def tell(scene: Scene, task: Task, helper: Helper, name: str = "Maya",
         gender: str = "girl", adult_type: str = "mother", delay: int = 0) -> World:
    world = World(scene)
    hero = world.add(Entity(id=name, kind="character", type=gender))
    adult = world.add(Entity(id="Mom", kind="character", type=adult_type, label="the parent"))
    item = world.add(Entity(id="item", type="thing", label="mug", fragile=True, hot=True))
    table = world.add(Entity(id="table", type="thing", label="table"))
    floor = world.add(Entity(id="floor", type="thing", label="floor"))
    world.facts["delay"] = delay

    setup(world, hero, adult)
    world.para()
    inner_monologue(world, hero, task, item)
    caution(world, adult, hero, task, item)

    world.para()
    if delay == 0:
        choose_slow(world, hero, helper)
        fix(world, adult, helper, item)
        lesson(world, hero, adult, task, helper)
        outcome = "careful"
    else:
        mistake(world, hero, task, item)
        fix(world, adult, helper, item)
        lesson(world, hero, adult, task, helper)
        outcome = "spilled"

    world.facts.update(hero=hero, adult=adult, item=item, table=table, floor=floor,
                       task=task, helper=helper, scene=scene, outcome=outcome)
    return world


SCENES = {
    "kitchen": Scene(
        "the kitchen", "quiet", "bringing warm cocoa to the table",
        "the windows were soft with morning light",
        "A spoon clinked once in a mug, and the whole room felt sleepy and safe.",
        "In the end, the cocoa stayed warm, the table stayed neat, and the child felt proud."),
    "porch": Scene(
        "the porch", "breezy", "carrying lemonade outside",
        "the porch boards were still cool from the morning",
        "A little breeze pushed at the curtains, making everything feel gently alive.",
        "In the end, the drink arrived safely, and the porch stayed tidy and bright."),
    "hallway": Scene(
        "the hallway", "still", "taking soup from the kitchen to the couch",
        "the hallway was narrow and lined with shoes",
        "A tiny lamp glowed near the wall, and the house felt close and warm.",
        "In the end, the soup made it across, and the hallway looked just as calm as before."),
}

TASKS = {
    "cocoa": Task("cocoa", "carry the cocoa", "carrying cocoa", "spill the cocoa", "spill", "table", {"spill"}),
    "lemonade": Task("lemonade", "carry the lemonade", "carrying lemonade", "spill the lemonade", "spill", "floor", {"spill"}),
    "soup": Task("soup", "carry the soup", "carrying soup", "spill the soup", "spill", "floor", {"spill"}),
}

HELPERS = {
    "tray": Helper("tray", "tray", "a little tray", "a paper towel and a cloth", "hold a cup steady", 3, 3, {"tray"}),
    "twohands": Helper("twohands", "two hands", "both hands", "a slow careful walk", "keep things level", 2, 3, {"careful"}),
    "mat": Helper("mat", "mat", "a rubber mat", "a quick wipe", "catch drips", 1, 2, {"mat"}),
}

WORD = "grateful"

GIRL_NAMES = ["Maya", "Nina", "Lila", "Ava", "Ella", "Zoe"]
BOY_NAMES = ["Noah", "Eli", "Finn", "Theo", "Leo", "Sam"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, scene in SCENES.items():
        for tid, task in TASKS.items():
            for helper in HELPERS.values():
                if helper_ok(helper):
                    combos.append((sid, tid, helper.id))
    return combos


@dataclass
class StoryParams:
    scene: str
    task: str
    helper: str
    name: str
    gender: str
    adult: str
    delay: int = 0
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about caution, gratitude, and a small lesson learned.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], default=0)
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


def explain_rejection(task: Task) -> str:
    return f"(No story: the chosen task does not support the slice-of-life lesson.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.task is None or c[1] == args.task)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, task, helper = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult = args.adult or rng.choice(["mother", "father"])
    return StoryParams(scene, task, helper, name, gender, adult, args.delay)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a small child that includes the word "{WORD}".',
        f"Tell a gentle cautionary story where {f['hero'].id} notices a small risk, listens to an inner thought, and learns to slow down.",
        f"Write a story about an ordinary moment at {f['scene'].place} that ends with a grateful lesson learned.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    adult = f["adult"]
    task = f["task"]
    helper = f["helper"]
    outcome = f["outcome"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id} and {adult.label_word}. They are in a quiet everyday moment, not a big adventure."),
        ("What did {hero} think about before acting?".replace("{hero}", hero.id),
         f"{hero.id} thought about whether rushing might cause a spill. That inner monologue helped {hero.pronoun()} choose care."),
    ]
    if outcome == "careful":
        qa.append((
            f"How did {hero.id} keep the drink safe?",
            f"{hero.id} picked up {helper.phrase} and moved slowly instead of rushing. That kept the cup steady and the room calm."
        ))
    else:
        qa.append((
            f"What went wrong when {hero.id} rushed?",
            f"A small spill spread across the table, and the drink wobbled near the edge. Even so, the adult helped clean it up right away."
        ))
    qa.append((
        f"What lesson did {hero.id} learn?",
        f"{hero.id} learned to slow down, listen to the quiet warning in {hero.pronoun('possessive')} head, and use help when carrying something fragile. That made {hero.id} feel grateful."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does grateful mean?",
         "Grateful means feeling glad and thankful because someone helped you or gave you something kind."),
        ("Why can a spill be a problem?",
         "A spill can make a surface wet and messy, and sometimes it can also make something fragile slip or wobble."),
        ("What does a tray help with?",
         "A tray helps carry things together and can keep a cup steadier, so it is easier to move carefully."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.fragile:
            bits.append("fragile")
        if e.helpful:
            bits.append("helpful")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
helper_ok(H) :- helper(H), sense(H,S), sense_min(M), S >= M.
valid(SC, TK, HP) :- scene(SC), task(TK), helper(HP), helper_ok(HP).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("sense", hid, h.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = set(asp_valid_combos()) == set(valid_combos())
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    if not sample.story:
        return 1
    if ok:
        print("OK: ASP parity and normal generation smoke test passed.")
        return 0
    print("MISMATCH: ASP and Python disagree.")
    return 1


def tell_story(params: StoryParams) -> StorySample:
    world = tell(
        SCENES[params.scene],
        TASKS[params.task],
        HELPERS[params.helper],
        params.name,
        params.gender,
        params.adult,
        params.delay,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return tell_story(params)


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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(s, t, h, "Maya", "girl", "mother", 0))
                   for s, t, h in [(p.scene, p.task, p.helper) for p in [resolve_params(argparse.Namespace(scene=None, task=None, helper=None, gender="girl", name="Maya", adult="mother", delay=0), random.Random(i)) for i in range(5)]]]
    else:
        seen = set()
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
