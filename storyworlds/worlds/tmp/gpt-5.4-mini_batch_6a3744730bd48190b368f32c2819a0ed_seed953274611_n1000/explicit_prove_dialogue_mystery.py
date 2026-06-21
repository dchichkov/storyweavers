#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/explicit_prove_dialogue_mystery.py
===================================================================

A small mystery storyworld with explicit dialogue, built around a child-friendly
"find the hidden thing, prove the answer" premise.

Premise:
- Someone notices a clue is missing or odd.
- Characters talk in short dialogue and make a careful guess.
- The guess is tested by a small physical action.
- The ending proves the mystery and changes the world state.

The generated stories always include the words "explicit" and "prove" in a
natural way, and they keep the mood close to a gentle mystery.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Clue:
    id: str
    noun: str
    place: str
    tells: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MysteryGear:
    id: str
    noun: str
    use: str
    can_show: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MysteryOutcome:
    id: str
    required: str
    text: str
    fail: str
    prove_text: str
    tags: set[str] = field(default_factory=set)


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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes["worry"] >= THRESHOLD and ("worry", e.id) not in world.fired:
            world.fired.add(("worry", e.id))
            out.append(f"{e.id} looked more worried.")
    return out


def _r_notice(world: World) -> list[str]:
    out: list[str] = []
    clue = world.entities.get("clue")
    if clue and clue.meters["found"] >= THRESHOLD and ("notice", clue.id) not in world.fired:
        world.fired.add(("notice", clue.id))
        out.append("__notice__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("notice", "plot", _r_notice)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def clue_taken(world: World, clue_id: str) -> bool:
    return world.get(clue_id).meters["taken"] >= THRESHOLD


def mystery_solved(world: World) -> bool:
    return bool(world.facts.get("proved"))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for scene in SCENES:
        for clue_id, clue in CLUES.items():
            for gear_id, gear in GEARS.items():
                if clue_id in scene.clue_ids and gear.can_show == clue_id:
                    combos.append((scene.id, clue_id, gear_id))
    return combos


@dataclass
class StoryParams:
    scene: str
    clue: str
    gear: str
    detective: str
    detective_gender: str
    helper: str
    helper_gender: str
    witness: str
    witness_gender: str
    seed: Optional[int] = None


@dataclass
class Scene:
    id: str
    place: str
    mood: str
    clue_ids: set[str] = field(default_factory=set)
    opener: str = ""
    closing: str = ""


SCENES = {
    "library": Scene(
        id="library",
        place="the little library",
        mood="quiet",
        clue_ids={"ink", "key"},
        opener="The shelves stood in neat rows, and the room was so quiet that even whispers felt loud.",
        closing="the library went calm again",
    ),
    "garden": Scene(
        id="garden",
        place="the garden path",
        mood="misty",
        clue_ids={"footprint", "glove"},
        opener="The garden was misty, and the stones along the path gleamed with tiny drops of water.",
        closing="the garden looked peaceful again",
    ),
    "attic": Scene(
        id="attic",
        place="the old attic",
        mood="dusty",
        clue_ids={"map", "lantern"},
        opener="The attic smelled dusty, and the beams made long shadows across the floorboards.",
        closing="the attic felt ordinary again",
    ),
}

CLUES = {
    "ink": Clue("ink", "ink mark", "the table", "a note had been written there", {"ink", "mystery"}),
    "key": Clue("key", "small brass key", "the rug fringe", "something had opened a tiny box", {"key", "mystery"}),
    "footprint": Clue("footprint", "muddy footprint", "the step by the gate", "someone had gone outside", {"footprint", "mystery"}),
    "glove": Clue("glove", "blue glove", "the bench", "someone had been reaching carefully", {"glove", "mystery"}),
    "map": Clue("map", "folded map", "the trunk", "a hidden place had been marked", {"map", "mystery"}),
    "lantern": Clue("lantern", "old lantern", "the crate", "there had been light in the dark", {"lantern", "mystery"}),
}

GEARS = {
    "magnifier": MysteryGear("magnifier", "magnifying glass", "look closely", "ink", {"look"}),
    "lamp": MysteryGear("lamp", "desk lamp", "shine on the clue", "key", {"light"}),
    "shovel": MysteryGear("shovel", "small trowel", "lift the soft earth", "footprint", {"dig"}),
    "brush": MysteryGear("brush", "soft brush", "dust the shelf", "glove", {"clean"}),
    "ladder": MysteryGear("ladder", "short ladder", "reach the top beam", "map", {"reach"}),
    "flash": MysteryGear("flash", "tiny flashlight", "show the dark corner", "lantern", {"light"}),
}

OUTCOMES = {
    "solved": MysteryOutcome(
        "solved",
        "prove",
        "the clue fit the answer at once",
        "the guess did not fit",
        "That finally proved the mystery.",
        {"prove"},
    )
}

NAMES_GIRL = ["Mia", "Lena", "Tess", "Nora", "Ivy", "Zoe"]
NAMES_BOY = ["Owen", "Milo", "Finn", "Eli", "Noah", "Leo"]


def scene_has(scene: Scene, clue_id: str) -> bool:
    return clue_id in scene.clue_ids


def tell(scene: Scene, clue: Clue, gear: MysteryGear,
         detective: str, detective_gender: str,
         helper: str, helper_gender: str,
         witness: str, witness_gender: str) -> World:
    world = World()
    d = world.add(Entity(id=detective, kind="character", type=detective_gender, role="detective"))
    h = world.add(Entity(id=helper, kind="character", type=helper_gender, role="helper"))
    w = world.add(Entity(id=witness, kind="character", type=witness_gender, role="witness"))
    clue_ent = world.add(Entity(id="clue", kind="thing", type="clue", label=clue.noun, role="clue"))
    gear_ent = world.add(Entity(id="gear", kind="thing", type="gear", label=gear.noun, role="gear"))

    d.memes["curious"] += 1
    h.memes["alert"] += 1
    w.memes["watching"] += 1

    world.say(f"{scene.opener} {detective} frowned. \"Something is off,\" {d.pronoun()} said.")
    world.say(f"\"Be explicit,\" {helper}, said. \"Tell us what you see.\"")
    world.say(f"{detective} pointed. \"There is {clue.noun} by {clue.place}. That should prove something.\"")

    world.para()
    clue_ent.meters["found"] += 1
    clue_ent.meters["taken"] += 1
    propagate(world, narrate=False)
    world.say(f"{helper} got {gear.noun} and {gear.use}.")
    world.say(f"\"Watch closely,\" {helper} said. \"If the clue matches, it will prove the guess.\"")

    world.para()
    if gear.can_show == clue.id and scene_has(scene, clue.id):
        d.memes["confidence"] += 1
        clue_ent.meters["revealed"] += 1
        world.say(f"{gear.noun.capitalize()} caught the tiny detail at {clue.place}.")
        world.say(f"\"Aha,\" {witness} said. \"That is the clue that proves it!\"")
        world.say(f"{clue.tells.capitalize()}. The mystery turned clear at last.")
        world.say(f"{OUTCOMES['solved'].prove_text} {scene.closing}.")
        proved = True
    else:
        d.memes["doubt"] += 1
        world.say(f"{gear.noun.capitalize()} did not fit the clue. \"That does not prove it,\" {h.pronoun()} said.")
        world.say(f"The room stayed full of questions, and the answer slipped away.")
        proved = False

    world.facts.update(
        detective=d, helper=h, witness=w, clue=clue_ent, clue_cfg=clue,
        gear=gear_ent, gear_cfg=gear, scene=scene, proved=proved
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly mystery story with dialogue that uses the words "explicit" and "prove".',
        f"Tell a gentle mystery where {f['detective'].id} says the answer must be explicit and uses a clue to prove it.",
        f"Write a short mystery with a careful guess, a small test, and a clear ending where someone proves what happened.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d, h, clue, gear, scene = f["detective"], f["helper"], f["clue_cfg"], f["gear_cfg"], f["scene"]
    items = [
        QAItem(
            question="What kind of story is this?",
            answer="It is a gentle mystery story with dialogue, where the characters look for a clue and test their guess.",
        ),
        QAItem(
            question=f"What did {d.id} want to do?",
            answer=f"{d.id} wanted to make the answer explicit and prove what was really happening. {d.id} did that by pointing to a clue and then testing it carefully.",
        ),
        QAItem(
            question=f"How did {h.id} help?",
            answer=f"{h.id} listened, gave the right tool, and told everyone to watch closely. That help mattered because the tool could reveal the clue instead of guessing wildly.",
        ),
    ]
    if f["proved"]:
        items.append(QAItem(
            question="How was the mystery solved?",
            answer=f"The clue matched the tool, so the guess proved true. The scene in {scene.place} changed from puzzling to clear when everyone saw the proof.",
        ))
    else:
        items.append(QAItem(
            question="How did the story end?",
            answer="It ended with uncertainty. The characters tried, but the clue did not prove the guess, so they still had a mystery to solve another day.",
        ))
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    clue = f["clue_cfg"]
    gear = f["gear_cfg"]
    return [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small bit of information that helps a detective figure out what happened. A good clue can point toward the answer and help prove a guess.",
        ),
        QAItem(
            question=f"What does {gear.noun} do in this story world?",
            answer=f"It helps a character look closely or check a hidden detail. That kind of tool is useful when a mystery needs proof instead of a wild guess.",
        ),
        QAItem(
            question=f"Why was {clue.noun} important?",
            answer=f"It was the piece that could show what really happened. When a clue is checked carefully, it can prove the right answer.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid, scene in SCENES.items():
        lines.append(asp.fact("scene", sid))
        for cid in sorted(scene.clue_ids):
            lines.append(asp.fact("scene_clue", sid, cid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
    for gid, gear in GEARS.items():
        lines.append(asp.fact("gear", gid))
        lines.append(asp.fact("shows", gid, gear.can_show))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Scene, Clue, Gear) :- scene(Scene), scene_clue(Scene, Clue), gear(Gear), shows(Gear, Clue).
proved(Scene) :- valid(Scene, _, _).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a != p:
        print("MISMATCH in valid combos")
        if a - p:
            print("only in asp:", sorted(a - p))
        if p - a:
            print("only in python:", sorted(p - a))
        return 1
    print(f"OK: ASP matches Python ({len(a)} combos).")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: normal story generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle mystery storyworld with dialogue.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--gear", choices=GEARS)
    ap.add_argument("--detective")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--witness")
    ap.add_argument("--witness-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.scene and args.clue and args.gear and (args.scene, args.clue, args.gear) not in combos:
        raise StoryError("(No valid combination matches the given scene, clue, and gear.)")
    combos = [c for c in combos if (args.scene is None or c[0] == args.scene)
              and (args.clue is None or c[1] == args.clue)
              and (args.gear is None or c[2] == args.gear)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene_id, clue_id, gear_id = rng.choice(sorted(combos))
    scene = SCENES[scene_id]
    clue = CLUES[clue_id]
    gear = GEARS[gear_id]
    dg = args.detective_gender or rng.choice(["girl", "boy"])
    hg = args.helper_gender or rng.choice(["girl", "boy"])
    wg = args.witness_gender or rng.choice(["girl", "boy"])
    detective = args.detective or rng.choice(NAMES_GIRL if dg == "girl" else NAMES_BOY)
    helper = args.helper or rng.choice([n for n in (NAMES_GIRL if hg == "girl" else NAMES_BOY) if n != detective])
    witness = args.witness or rng.choice([n for n in (NAMES_GIRL if wg == "girl" else NAMES_BOY) if n not in {detective, helper}])
    return StoryParams(scene=scene_id, clue=clue_id, gear=gear_id,
                       detective=detective, detective_gender=dg,
                       helper=helper, helper_gender=hg,
                       witness=witness, witness_gender=wg)


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES or params.clue not in CLUES or params.gear not in GEARS:
        raise StoryError("Invalid params.")
    world = tell(SCENES[params.scene], CLUES[params.clue], GEARS[params.gear],
                 params.detective, params.detective_gender,
                 params.helper, params.helper_gender,
                 params.witness, params.witness_gender)
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
    StoryParams(scene="library", clue="ink", gear="magnifier",
                detective="Mia", detective_gender="girl",
                helper="Noah", helper_gender="boy",
                witness="Lena", witness_gender="girl"),
    StoryParams(scene="garden", clue="footprint", gear="shovel",
                detective="Owen", detective_gender="boy",
                helper="Ivy", helper_gender="girl",
                witness="Eli", witness_gender="boy"),
    StoryParams(scene="attic", clue="lantern", gear="flash",
                detective="Tess", detective_gender="girl",
                helper="Finn", helper_gender="boy",
                witness="Zoe", witness_gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for item in asp_valid_combos():
            print(item)
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


if __name__ == "__main__":
    main()
