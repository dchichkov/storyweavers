#!/usr/bin/env python3
"""
storyworlds/worlds/exact_medium_cannibal_inner_monologue_whodunit.py
====================================================================

A small whodunit story world with inner monologue.

Seed tale:
---
At the museum, a perfectly exact silver key vanished from a medium-sized display box.
Detective Mina watched the clues, and in her head she kept a careful inner monologue:
"Who had a reason to move it? Who could reach it? Who lied by forgetting a detail?"
The suspects were a baker, a librarian, and a stage actor nicknamed Cannibal for a silly
pirate role. The detective noticed that the baker's flour, the librarian's labels, and the
actor's costume all told a different story. In the end, the key was not stolen at all.
It had been moved to the medium drawer during a tidy-up, and the person who remembered
the exact sequence of events solved the case.

Premise:
- A small cast shares one location.
- One exact object goes missing.
- One medium container, one contradictory clue, and one suspicious nickname create tension.
- The detective's inner monologue tracks uncertainty and deductions.
- Resolution comes from a precise chain of custody, not a dramatic chase.

State model:
- Entities have physical meters and emotional memes.
- The key, box, drawer, and clues can move between hands and places.
- Suspicion rises when a clue contradicts another.
- Relief rises when the exact location is proven.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    type: str = ""
    owner: Optional[str] = None
    location: str = ""
    carries: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ("suspicion", "worry", "relief", "certainty", "order"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self) -> str:
        return "they" if self.kind == "character" else "it"

    def poss(self) -> str:
        return "their" if self.kind == "character" else "its"


@dataclass
class StoryParams:
    setting: str = "museum"
    detective: str = "Mina"
    baker: str = "Pip"
    librarian: str = "June"
    actor: str = "Rory"
    seed: Optional[int] = None


@dataclass
class Scene:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

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

    def copy(self) -> "Scene":
        c = Scene(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        return c


THRESHOLD = 1.0


def whisper(scene: Scene, detective: Entity, text: str) -> None:
    scene.say(f"{detective.id} thought, \"{text}\"")


def clue_count(scene: Scene, name: str) -> int:
    return int(scene.facts.get(name, 0))


def reveal_exact_location(scene: Scene, item: Entity, place: str) -> None:
    item.location = place
    item.memes["certainty"] += 1


def propagate(scene: Scene) -> None:
    changed = True
    while changed:
        changed = False
        if "contradiction" not in scene.fired:
            if scene.facts.get("flour_on_hands") and scene.facts.get("labels_in_order"):
                scene.fired.add("contradiction")
                scene.facts["mystery_deepens"] = True
                changed = True
        if "drawer_hint" not in scene.fired:
            if scene.facts.get("drawer_seen") and scene.facts.get("exact_word"):
                scene.fired.add("drawer_hint")
                scene.facts["drawer_probable"] = True
                changed = True
        if "certainty" not in scene.fired:
            if scene.facts.get("tidy_up") and scene.facts.get("key_in_drawer"):
                scene.fired.add("certainty")
                scene.facts["solution"] = True
                changed = True


def build_world(params: StoryParams) -> Scene:
    scene = Scene(params.setting)
    detective = scene.add(Entity(id=params.detective, kind="character", type="detective"))
    baker = scene.add(Entity(id=params.baker, kind="character", type="baker"))
    librarian = scene.add(Entity(id=params.librarian, kind="character", type="librarian"))
    actor = scene.add(Entity(id=params.actor, kind="character", type="actor"))
    key = scene.add(Entity(id="key", label="exact silver key", phrase="the exact silver key", location="box"))
    box = scene.add(Entity(id="box", label="medium display box", phrase="the medium-sized display box", location="table"))
    drawer = scene.add(Entity(id="drawer", label="medium drawer", phrase="the medium drawer", location="office"))
    scene.add(Entity(id="flour", label="white flour", phrase="a little dust of white flour", location="baker"))
    scene.add(Entity(id="labels", label="tiny labels", phrase="a neat stack of tiny labels", location="librarian"))

    scene.facts.update(
        exact_word=True,
        medium_word=True,
        cannibal_name=True,
        flour_on_hands=True,
        labels_in_order=True,
        drawer_seen=True,
        tidy_up=False,
        key_in_drawer=False,
        solution=False,
    )
    scene.facts["detective"] = detective
    scene.facts["baker"] = baker
    scene.facts["librarian"] = librarian
    scene.facts["actor"] = actor
    scene.facts["key"] = key
    scene.facts["box"] = box
    scene.facts["drawer"] = drawer
    return scene


def tell(scene: Scene) -> None:
    d = scene.facts["detective"]
    b = scene.facts["baker"]
    l = scene.facts["librarian"]
    a = scene.facts["actor"]
    key = scene.facts["key"]
    box = scene.facts["box"]
    drawer = scene.facts["drawer"]

    scene.say(f"At the museum, an exact little mystery waited beside a medium display box.")
    scene.say(f"{d.id} stood very still and listened to the room.")
    whisper(scene, d, "A missing thing is never just missing. Someone moved it, or someone is hiding a tidy mistake.")

    scene.para()
    scene.say(f"The exact silver key had been in {box.label}, but now the box felt empty.")
    scene.say(f"{b.id} had flour on {b.id}'s sleeves, {l.id} kept every label in neat rows, and {a.id} wore a pirate coat with the silly nickname Cannibal.")
    whisper(scene, d, "The flour points one way. The labels point another. And the pirate nickname is trying very hard to look dangerous.")
    propagate(scene)

    scene.para()
    scene.say(f"{d.id} checked the box again and looked at the floor, then at the desk, then at the open drawers nearby.")
    whisper(scene, d, "If the key was not stolen, then it probably traveled during a clean-up. I need the exact path, not a guess.")
    scene.facts["tidy_up"] = True
    scene.facts["key_in_drawer"] = True
    reveal_exact_location(scene, key, drawer.location)
    propagate(scene)

    scene.para()
    scene.say(f"{l.id} finally remembered it: the key had been put in the medium drawer while the room was being tidied.")
    scene.say(f"It had not been taken away at all. It had only been moved to a safer, more exact place.")
    whisper(scene, d, "Of course. The clues were not lying. I was listening to the wrong question.")
    detective.memes["relief"] += 1
    detective.meters["certainty"] += 1
    scene.say(f"{d.id} smiled, and the room felt orderly again.")
    scene.say(f"The exact silver key rested in the medium drawer, and the case ended with a neat little answer instead of a scare.")

    scene.facts["ending"] = "key in medium drawer"
    scene.facts["inner_monologue"] = True


def story_qa(scene: Scene) -> list[QAItem]:
    d = scene.facts["detective"].id
    b = scene.facts["baker"].id
    l = scene.facts["librarian"].id
    a = scene.facts["actor"].id
    return [
        QAItem(
            question="What kind of mystery was it?",
            answer="It was a whodunit about a missing exact silver key and who had moved it."
        ),
        QAItem(
            question="What was the detective thinking about the clues?",
            answer=f"{d} kept a careful inner monologue, comparing the flour, the labels, and the odd pirate nickname instead of guessing too fast."
        ),
        QAItem(
            question="Who looked suspicious at first?",
            answer=f"The baker, the librarian, and {a}, who had the silly nickname Cannibal, all looked suspicious in different ways."
        ),
        QAItem(
            question="What was the real solution?",
            answer="The key had been moved during a tidy-up and was found in the medium drawer."
        ),
        QAItem(
            question="Why did the detective feel better at the end?",
            answer="The detective felt relief because the exact location of the key was discovered and the mystery made sense."
        ),
    ]


def world_qa(scene: Scene) -> list[QAItem]:
    return [
        QAItem(
            question="What does exact mean?",
            answer="Exact means perfectly right, with no mistake or extra guess."
        ),
        QAItem(
            question="What does medium mean?",
            answer="Medium means not too small and not too large."
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a helpful piece of information that can lead to an answer in a mystery."
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is the private thinking voice inside a character's head."
        ),
    ]


def generation_prompts(scene: Scene) -> list[str]:
    return [
        'Write a short whodunit story for children with inner monologue and the words "exact" and "medium".',
        'Tell a mystery where a detective thinks carefully to find a missing exact object in a medium container.',
        'Write a gentle mystery with a suspicious nickname, careful clues, and a neat ending answer.',
    ]


def dump_trace(scene: Scene) -> str:
    lines = ["--- world model state ---"]
    for e in scene.entities.values():
        lines.append(
            f"  {e.id:10} kind={e.kind:9} loc={e.location:8} "
            f"meters={{{', '.join(f'{k}:{v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}:{v}' for k, v in e.memes.items() if v)}}}"
        )
    lines.append(f"  facts={scene.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
exact_word.
medium_word.
cannibal_name.

mystery_deepens :- flour_on_hands, labels_in_order.
drawer_probable :- drawer_seen, exact_word.
solution :- tidy_up, key_in_drawer.

#show mystery_deepens/0.
#show drawer_probable/0.
#show solution/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("flour_on_hands"),
        asp.fact("labels_in_order"),
        asp.fact("drawer_seen"),
        asp.fact("exact_word"),
        asp.fact("medium_word"),
        asp.fact("cannibal_name"),
        asp.fact("tidy_up"),
        asp.fact("key_in_drawer"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world with inner monologue.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    scene = build_world(params)
    tell(scene)
    return StorySample(
        params=params,
        story=scene.render(),
        prompts=generation_prompts(scene),
        story_qa=story_qa(scene),
        world_qa=world_qa(scene),
        world=scene,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print("== (1) Generation prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== (2) Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== (3) World questions ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mystery_deepens/0. #show drawer_probable/0. #show solution/0."))
    atoms = {str(s) for s in model}
    expected = {"mystery_deepens", "drawer_probable", "solution"}
    if atoms == expected:
        print("OK: ASP parity matches Python reasonableness gate.")
        return 0
    print("MISMATCH:", sorted(atoms), sorted(expected))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show mystery_deepens/0. #show drawer_probable/0. #show solution/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show mystery_deepens/0. #show drawer_probable/0. #show solution/0."))
        print("ASP model:", " ".join(str(s) for s in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples.append(generate(StoryParams(seed=base_seed)))
    else:
        for i in range(max(args.n, 1)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
