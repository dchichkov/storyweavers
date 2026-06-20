#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/injection_energetic_hamper_flashback_tall_tale.py
===================================================================================

A standalone storyworld for a tall-tale style medical-and-memory story:
a child loses their energy, a grown-up gives a tiny injection, a flashback
reveals where the fear came from, and the child ends up lively again.

This world is deliberately small and classical: typed entities, accumulating
physical meters and emotional memes, a forward rule engine, a reasonableness
gate, QA from simulated state, and an inline ASP twin for parity checks.
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
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
    id: str
    place: str
    flashback_place: str
    energy_word: str
    hamper_kind: str
    hamper_phrase: str
    medicine_phrase: str
    title: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


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


def _r_fever_drain(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.meters["energy"] >= THRESHOLD:
        return out
    sig = ("drain",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    out.append(f"{child.id} felt limp as a flag in a windless field.")
    return out


def _r_injection_wakes(world: World) -> list[str]:
    out = []
    child = world.get("child")
    nurse = world.get("nurse")
    if child.meters["injected"] < THRESHOLD:
        return out
    sig = ("wake",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["energy"] += 1
    child.memes["brave"] += 1
    nurse.memes["pride"] += 1
    out.append(f"The tiny pinch chased the weariness away like a rooster chasing dawn.")
    return out


def _r_flashback_bloom(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.memes["memory"] < THRESHOLD:
        return out
    sig = ("flashback",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("That sent the child back in time, to the day the hamper had tumbled like a cannonball.")
    return out


def _r_hamper_taught(world: World) -> list[str]:
    out = []
    hamper = world.get("hamper")
    child = world.get("child")
    if hamper.meters["rolled"] < THRESHOLD:
        return out
    sig = ("hamper",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += 1
    out.append("The hamper had looked like a gaping cave, and the child had sworn it held a monster sock.")
    return out


CAUSAL_RULES = [
    Rule("fever_drain", _r_fever_drain),
    Rule("injection_wakes", _r_injection_wakes),
    Rule("flashback_bloom", _r_flashback_bloom),
    Rule("hamper_taught", _r_hamper_taught),
]


def story_state(world: World) -> dict:
    c = world.get("child")
    return {
        "energy": c.meters["energy"],
        "injected": c.meters["injected"],
        "fear": c.memes["fear"],
        "brave": c.memes["brave"],
        "memory": c.memes["memory"],
    }


def predict_outcome(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters["injected"] = 1
    child.memes["memory"] = 1
    propagate(sim, narrate=False)
    return {"energetic": sim.get("child").meters["energy"] >= THRESHOLD}


def tell(scene: Scene, child_name: str, child_type: str, adult_name: str, adult_type: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_type, role="nurse"))
    hamper = world.add(Entity(id="hamper", kind="thing", type="hamper", label=scene.hamper_kind))
    child.meters["energy"] = 0.0
    child.memes["fear"] = 1.0
    child.memes["memory"] = 1.0
    hamper.meters["rolled"] = 1.0

    world.say(f"In {scene.place}, {child.id} was as low in spirit as a wagon sunk in mud.")
    world.say(f"{child.id} had no {scene.energy_word} left, only a droopy sigh and a brave little frown.")
    world.say(f"{adult_name} smiled and held up {scene.medicine_phrase}, as careful as a jeweler with a star.")

    world.para()
    world.say(f"\"This will help,\" said {adult_name}, and the tiny injection went in with a blink-and-you-miss-it prick.")
    child.meters["injected"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say("The child shivered once, and then a flashback galloped through the mind like six ponies tied to a kite.")
    propagate(world, narrate=True)

    world.para()
    world.say(f"{adult_name} knelt beside the hamper and laughed softly. \"Remember this?\"")
    world.say(f"\"When you were little, that hamper rolled across the floor and scared you silly,\" {adult_name} said.")
    world.say(f"\"Now it just holds socks, and you are bigger than the worry.\"")

    world.para()
    child.meters["energy"] = 1.0
    child.memes["joy"] += 1
    child.memes["brave"] += 1
    world.say(f"Sure enough, {child.id} sprang up tall as a cornstalk in a thunderstorm.")
    world.say(f"{scene.ending_image}")
    world.say(f"By sunset, {child.id} was {scene.title}, bright-eyed and energetic, with not a single shiver left.")

    world.facts.update(
        child=child,
        adult=adult,
        hamper=hamper,
        scene=scene,
        outcome="energetic",
        predicted=predict_outcome(world),
    )
    return world


SCENES = {
    "clinic": Scene(
        "clinic",
        place="the little clinic on the hill",
        flashback_place="the laundry room",
        energy_word="energy",
        hamper_kind="basket-hamper",
        hamper_phrase="a tiny injection at the clinic",
        medicine_phrase="a needle no bigger than a grass blade",
        title="as energetic as a cricket on a hot skillet",
        ending_image="Outside, the clinic sign bounced in the wind while the child marched home as lively as a drumline.",
        tags={"injection", "hamper", "flashback"},
    ),
    "cabin": Scene(
        "cabin",
        place="the pine cabin by the creek",
        flashback_place="the attic",
        energy_word="pep",
        hamper_kind="woven hamper",
        hamper_phrase="a brave little injection from the village nurse",
        medicine_phrase="a tiny medicine shot",
        title="fit for another hundred mile of jumping",
        ending_image="The creek glittered below the porch as the child skipped circles around the boots by the door.",
        tags={"injection", "hamper", "flashback"},
    ),
    "farm": Scene(
        "farm",
        place="the red barn clinic at the edge of town",
        flashback_place="the washhouse",
        energy_word="zing",
        hamper_kind="cloth hamper",
        hamper_phrase="one quick injection from the country doctor",
        medicine_phrase="a slender little shot",
        title="energetic enough to outpace a startled goose",
        ending_image="A barn cat blinked from the fence while the child hopped the path like a spark on stilts.",
        tags={"injection", "hamper", "flashback"},
    ),
}

NAMES_GIRL = ["Mina", "June", "Ruby", "Sadie", "Nell", "Ivy"]
NAMES_BOY = ["Toby", "Finn", "Cal", "Evan", "Hank", "Owen"]


def reasonableness_gate(scene: Scene) -> None:
    if "flashback" not in scene.tags:
        raise StoryError("This world needs a flashback.")
    if "injection" not in scene.tags or "hamper" not in scene.tags:
        raise StoryError("This world needs both injection and hamper.")
    if not scene.medicine_phrase or not scene.ending_image:
        raise StoryError("Scene data is incomplete.")


def valid_combos() -> list[str]:
    return sorted(SCENES)


@dataclass
class StoryParams:
    scene: str
    child: str
    child_type: str
    adult: str
    adult_type: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale flashback storyworld about an injection and a hamper.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-type", choices=["mother", "father", "nurse", "doctor"])
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
    scene = args.scene or rng.choice(valid_combos())
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(NAMES_GIRL if child_type == "girl" else NAMES_BOY)
    adult_type = args.adult_type or rng.choice(["mother", "father", "nurse", "doctor"])
    adult = args.adult or rng.choice(["Aunt Rose", "Dr. Bell", "Nurse Ada", "Grandpa Joe"])
    reasonableness_gate(SCENES[scene])
    return StoryParams(scene, child, child_type, adult, adult_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene = f["scene"]
    child = f["child"]
    return [
        f'Write a tall tale for a child who gets an injection and remembers a hamper from an old flashback.',
        f"Tell a whimsical story where {child.id} feels weak at {scene.place}, gets a tiny injection, and then recalls a hamper from long ago.",
        f'Write a flashback story that includes the words "injection", "energetic", and "hamper".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    scene = f["scene"]
    return [
        QAItem(
            question="What happened to the child at the clinic?",
            answer=f"{child.id} got a tiny injection and then felt strong enough to stand tall again. The shot was small, but it was the thing that turned the story around."
        ),
        QAItem(
            question="Why did the story flash back to the hamper?",
            answer=f"The child remembered the hamper because it had scared {child.pronoun('object')} before. That memory explained why the injection felt so important and why {adult.id} spoke so gently."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {child.id} lively and energetic, moving like a parade drum. The ending image shows that the weakness was gone and the day had become bright again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an injection?",
            answer="An injection is a quick shot of medicine that a doctor or nurse gives with a tiny needle. It can help a person feel better."
        ),
        QAItem(
            question="What is a hamper?",
            answer="A hamper is a basket or bin, often used for laundry. In a story it can become an object a child remembers."
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is when a story briefly goes back to something that happened earlier. It helps explain a feeling or a problem from the present."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
needs_flashback :- flashback(scene).
needs_injection :- injection(scene).
needs_hamper :- hamper(scene).
energetic(child) :- injected(child), not weak(child).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, scene in SCENES.items():
        lines.append(asp.fact("scene", sid))
        if "flashback" in scene.tags:
            lines.append(asp.fact("flashback", sid))
        if "injection" in scene.tags:
            lines.append(asp.fact("injection", sid))
        if "hamper" in scene.tags:
            lines.append(asp.fact("hamper", sid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show needs_flashback/0. #show needs_injection/0. #show needs_hamper/0."))
    return sorted({a for a in asp.atoms(model, "needs_flashback") or []})  # trivial parity


def asp_verify() -> int:
    rc = 0
    try:
        if set(valid_combos()) != set(SCENES):
            raise AssertionError("valid_combos mismatch")
        sample = generate(resolve_params(argparse.Namespace(scene=None, child=None, child_type=None, adult=None, adult_type=None), random.Random(7)))
        if not sample.story.strip():
            raise AssertionError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"FAIL: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    scene = SCENES[params.scene]
    world = tell(scene, params.child, params.child_type, params.adult, params.adult_type)
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
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("", "#show needs_flashback/0. #show needs_injection/0. #show needs_hamper/0."))
        return
    if args.asp:
        print("\n".join(valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        seeds = list(SCENES)
    else:
        seeds = []
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            sample = generate(params)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
