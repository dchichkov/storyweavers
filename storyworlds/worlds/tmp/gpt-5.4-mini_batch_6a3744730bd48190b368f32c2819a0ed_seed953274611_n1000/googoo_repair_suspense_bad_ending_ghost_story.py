#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/googoo_repair_suspense_bad_ending_ghost_story.py
==================================================================================

A tiny ghost-story world about a child, a haunted repair job, and a suspenseful
choice that can end safely or badly. The seed words are ``googoo`` and ``repair``.
The style aims at a child-facing ghost story: lantern light, whispering halls,
a creaky doll, and a repair attempt that can go wrong.

This world is intentionally small and state-driven:
- a child explores a dark room
- a ghostly object keeps making the word ``googoo``
- a repair attempt may calm the haunting or fail
- suspense rises from meters before the ending
- the bad ending happens when the object breaks beyond repair

Run it:
    python storyworlds/worlds/gpt-5.4-mini/googoo_repair_suspense_bad_ending_ghost_story.py
    python storyworlds/worlds/gpt-5.4-mini/googoo_repair_suspense_bad_ending_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/googoo_repair_suspense_bad_ending_ghost_story.py --verify
    python storyworlds/worlds/gpt-5.4-mini/googoo_repair_suspense_bad_ending_ghost_story.py --qa --json
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
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SUSPENSE_RISE = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Scene:
    place: str
    dark_spot: str
    sound: str
    feel: str
    ending_image: str


@dataclass
class Haunt:
    id: str
    label: str
    phrase: str
    makes_ghost: bool = True
    whisper: str = "googoo"


@dataclass
class RepairTool:
    id: str
    label: str
    phrase: str
    power: int
    sense: int
    text: str
    fail_text: str


@dataclass
class StoryParams:
    scene: str
    haunt: str
    tool: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("haunt")
    child = world.get("child")
    if ghost.meters["dread"] >= THRESHOLD and ("suspense",) not in world.fired:
        world.fired.add(("suspense",))
        child.memes["fear"] += 1
        out.append("")
    return out


def _r_break(world: World) -> list[str]:
    out: list[str] = []
    haunt = world.get("haunt")
    if haunt.meters["damage"] >= 2 * THRESHOLD and ("break",) not in world.fired:
        world.fired.add(("break",))
        haunt.meters["broken"] = 1
        out.append("__broken__")
    return out


CAUSAL_RULES = [Rule("suspense", _r_suspense), Rule("break", _r_break)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s and not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def haunt_risk(haunt: Haunt, tool: RepairTool) -> bool:
    return haunt.makes_ghost and tool.sense >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for scene in SCENES:
        for hid, h in HAUNTS.items():
            for tid, t in TOOLS.items():
                if haunt_risk(h, t):
                    combos.append((scene, hid, tid))
    return combos


def a_child_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def tense_sound(scene: Scene) -> str:
    return scene.sound


def setup(world: World, child: Entity, helper: Entity, scene: Scene, haunt: Haunt) -> None:
    child.memes["curiosity"] += 1
    helper.memes["worry"] += 1
    world.say(
        f"On a dark evening, {child.id} and {helper.id} stood in {scene.place}. "
        f"{scene.feel.capitalize()}, the air seemed to listen."
    )
    world.say(
        f"Somewhere near {scene.dark_spot}, something made a tiny sound: "
        f'"{tense_sound(scene)}."'
    )
    world.say(
        f"{child.id} held a little breath and whispered, "
        f'"Did you hear that googoo sound?"'
    )


def warn(world: World, helper: Entity, child: Entity, haunt: Haunt) -> None:
    helper.memes["caution"] += 1
    world.say(
        f"{helper.id} touched {child.pronoun('possessive')} sleeve. "
        f'"That sound is the {haunt.label}," {helper.pronoun()} said. '
        f'"We should be careful and think before we repair anything."'
    )


def tempt(world: World, child: Entity, haunt: Haunt) -> None:
    child.memes["bravery"] += 1
    world.say(
        f"But {child.id} leaned closer anyway. "
        f'From the dark came the soft whisper "{haunt.whisper}, googoo, googoo."'
    )


def inspect(world: World, child: Entity, haunt: Haunt) -> None:
    child.memes["fear"] += 1
    haunt.meters["dread"] += 1
    world.say(
        f"{child.id} found the old {haunt.label}, dusty and trembling on a shelf. "
        f"It looked lonely, as if it had been waiting for someone to repair it."
    )


def attempt_repair(world: World, child: Entity, helper: Entity, haunt: Haunt, tool: RepairTool) -> None:
    haunt.meters["repair"] += 1
    world.say(
        f"{child.id} picked up {tool.phrase} and tried to repair the {haunt.label}. "
        f"{helper.id} watched closely, hoping the fix would hold."
    )
    if tool.power >= 2:
        haunt.meters["stability"] += 1
        child.memes["hope"] += 1
        world.say(f"{tool.text}.")
    else:
        haunt.meters["damage"] += 2
        world.say(f"{tool.fail_text}.")


def ending_bad(world: World, child: Entity, helper: Entity, haunt: Haunt, scene: Scene) -> None:
    child.memes["fear"] += 2
    helper.memes["sadness"] += 2
    world.say(
        f"Then the shelf groaned. The old thing split open, and the googoo whisper"
        f" turned into a long, chilly moan."
    )
    world.say(
        f"{helper.id} pulled {child.id} backward, but the room was already full of "
        f"shadow. The repair had gone too far, and the haunting only grew."
    )
    world.say(
        f"By morning, the {haunt.label} was beyond repair, and the little light in "
        f"the hall never felt warm again."
    )
    world.say(
        f"{scene.ending_image.capitalize()}, and the house stayed quiet in a sad, "
        f"spooky way."
    )


def ending_good(world: World, child: Entity, helper: Entity, haunt: Haunt, scene: Scene) -> None:
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{helper.id} fixed the last loose piece, and the googoo whisper faded to "
        f"nothing."
    )
    world.say(
        f"The room did not feel scary anymore. The repaired {haunt.label} only "
        f"clicked softly in the dark."
    )
    world.say(f"{scene.ending_image.capitalize()}.")


def tell(scene: Scene, haunt: Haunt, tool: RepairTool,
         child_name: str = "Mia", child_gender: str = "girl",
         helper_name: str = "Dad", helper_gender: str = "boy") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    ghost = world.add(Entity(id="haunt", type="thing", label=haunt.label, meters=defaultdict(float)))
    ghost.meters["dread"] = 1

    setup(world, child, helper, scene, haunt)
    world.para()
    warn(world, helper, child, haunt)
    tempt(world, child, haunt)
    inspect(world, child, haunt)
    world.para()
    attempt_repair(world, child, helper, haunt, tool)
    propagate(world, narrate=False)

    bad = ghost.meters["broken"] >= THRESHOLD or haunt.meters["damage"] >= 2
    if bad:
        ending_bad(world, child, helper, haunt, scene)
        outcome = "bad"
    else:
        ending_good(world, child, helper, haunt, scene)
        outcome = "good"

    world.facts.update(
        child=child, helper=helper, haunt=ghost, haunt_cfg=haunt, tool=tool,
        scene=scene, outcome=outcome, bad=bad
    )
    return world


SCENES = {
    "attic": Scene(
        place="the attic",
        dark_spot="the top of the stairs",
        sound="googoo",
        feel="cold and hush-quiet",
        ending_image="the attic window shone pale and empty",
    ),
    "hall": Scene(
        place="the long hall",
        dark_spot="the end of the hallway",
        sound="googoo",
        feel="thin and chilly",
        ending_image="the hallway lamp hummed over a broken toy",
    ),
    "cellar": Scene(
        place="the cellar",
        dark_spot="the back shelf",
        sound="googoo",
        feel="wet and silent",
        ending_image="the cellar door stayed shut against the dark",
    ),
}

HAUNTS = {
    "doll": Haunt(id="doll", label="porcelain doll", phrase="an old porcelain doll"),
    "music_box": Haunt(id="music_box", label="music box", phrase="a cracked music box"),
    "clock": Haunt(id="clock", label="grandfather clock", phrase="a tall grandfather clock"),
}

TOOLS = {
    "tape": RepairTool(
        id="tape", label="tape", phrase="a roll of tape", power=1, sense=2,
        text="The tape held for one breath, then peeled off in the cold",
        fail_text="The tape slipped, and the crack grew wider",
    ),
    "glue": RepairTool(
        id="glue", label="glue", phrase="a bottle of glue", power=2, sense=3,
        text="The glue sealed the loose seam, and the tiny rattle stopped",
        fail_text="The glue dripped onto the floor, but the crack still widened",
    ),
    "needle_thread": RepairTool(
        id="needle_thread", label="needle and thread", phrase="a needle and thread", power=3, sense=3,
        text="The thread stitched the torn edge back together, neat and tight",
        fail_text="The thread snagged, and the tear yawned open wider",
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Zoe", "Ava", "Ivy"]
BOY_NAMES = ["Ben", "Noah", "Finn", "Theo", "Eli", "Max"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost story for a young child that includes the words "googoo" and "repair".',
        f"Tell a suspenseful haunted-room story where {f['child'].id} hears googoo noises and tries to repair {f['haunt_cfg'].label}.",
        f"Write a spooky but child-friendly story that begins with a whisper and ends with a bad repair.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, haunt, scene, tool = f["child"], f["helper"], f["haunt_cfg"], f["scene"], f["tool"]
    qa: list[tuple[str, str]] = [
        ("Who is in the story?",
         f"The story is about {child.id} and {helper.id}. They are the ones who hear the googoo sound in {scene.place}."),
        ("What was the strange word they heard?",
         "They heard googoo, a soft whispering sound that made the room feel spooky."),
        ("What did they try to do?",
         f"They tried to repair the {haunt.label} with {tool.phrase}. The repair was meant to make the haunted thing settle down."),
    ]
    if f["bad"]:
        qa.append((
            "Why did the story end badly?",
            f"The repair went wrong because the {haunt.label} broke instead of mending. That made the haunting stronger, so the room ended in a colder, sadder way."
        ))
        qa.append((
            "How did the ending change?",
            "The room lost its safe feeling. Instead of quiet relief, the final image showed the place staying spooky and broken."
        ))
    else:
        qa.append((
            "Why did the story end safely?",
            f"The {haunt.label} was repaired well enough to stop the whispering. The spooky feeling faded, and the room grew calm again."
        ))
        qa.append((
            "How did the ending change?",
            "The final image became softer and quieter. The scary noise stopped, so the room could rest."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does repair mean?",
         "Repair means fixing something that is broken or loose so it works again."),
        ("Why can a dark room feel spooky?",
         "Dark rooms hide what is there, so little noises can feel bigger and more mysterious."),
        ("What is suspense?",
         "Suspense is the feeling of waiting and worrying about what will happen next."),
        ("What makes a ghost story spooky?",
         "A ghost story uses whispers, shadows, and strange sounds to make the reader feel a chill."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "",
             "== (2) Story questions =="]
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(scene="attic", haunt="doll", tool="glue", child="Mia", child_gender="girl", helper="Dad", helper_gender="boy"),
    StoryParams(scene="hall", haunt="music_box", tool="needle_thread", child="Ben", child_gender="boy", helper="Mom", helper_gender="girl"),
    StoryParams(scene="cellar", haunt="clock", tool="tape", child="Nora", child_gender="girl", helper="Dad", helper_gender="boy"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and TOOLS[args.tool].sense < 2:
        raise StoryError("That repair tool is too weak for a sensible ghost story.")
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.haunt is None or c[1] == args.haunt)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, haunt, tool = rng.choice(sorted(combos))
    gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or a_child_name(rng, gender)
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    helper = args.helper or a_child_name(rng, helper_gender)
    if helper == child:
        helper = helper + "a"
    return StoryParams(scene=scene, haunt=haunt, tool=tool, child=child, child_gender=gender, helper=helper, helper_gender=helper_gender)


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES or params.haunt not in HAUNTS or params.tool not in TOOLS:
        raise StoryError("Invalid params.")
    world = tell(SCENES[params.scene], HAUNTS[params.haunt], TOOLS[params.tool],
                 child_name=params.child, child_gender=params.child_gender,
                 helper_name=params.helper, helper_gender=params.helper_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


ASP_RULES = r"""
valid(S,H,T) :- scene(S), haunt(H), tool(T), makes_ghost(H), sense(T,SN), SN >= 2.
bad_ending(H) :- haunt(H), broken(H).
broken(H) :- damage(H, D), D >= 2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for hid, h in HAUNTS.items():
        lines.append(asp.fact("haunt", hid))
        if h.makes_ghost:
            lines.append(asp.fact("makes_ghost", hid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("sense", tid, t.sense))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP gate matches Python valid_combos().")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos().")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny spooky repair storyworld.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--haunt", choices=HAUNTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
