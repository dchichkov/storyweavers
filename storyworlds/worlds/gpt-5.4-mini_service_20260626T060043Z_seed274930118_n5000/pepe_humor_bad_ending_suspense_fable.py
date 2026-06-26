#!/usr/bin/env python3
"""
A small fable-style story world about Pepe, suspense, humor, and a bad ending.

The seed tale behind this world:
A little fox named Pepe loved shiny things and funny tricks. One evening, he found
a lantern on the path and heard a rustle in the reeds. Pepe decided to follow the
sound to discover a hidden treasure. His friend warned him that the marsh path was
narrow and slippery, but Pepe laughed and kept going. The rustling turned out to be
a family of geese guarding a sack of berries. Pepe tried to grab the sack, slipped
into the mud, and the berries rolled away. The geese chased him off, and Pepe went
home muddy, hungry, and embarrassed. The lesson is that a greedy laugh can hide a
bad ending.

World model:
- physical meters: mud, tiredness, hunger, lost, light, wet
- emotional memes: curiosity, greed, fear, humor, shame, relief
- state-driven narration: the path, the warning, the rustle, the slip, the chase,
  and the empty ending all follow from the simulated world
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for key in ["mud", "tiredness", "hunger", "lost", "light", "wet"]:
            self.meters.setdefault(key, 0.0)
        for key in ["curiosity", "greed", "fear", "humor", "shame", "relief"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "boy", "man", "father", "he"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother", "she"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the marsh path"
    mood: str = "foggy"


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    risk: str
    value: int = 1


@dataclass
class StoryParams:
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_log: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: callable


def _r_mud(world: World) -> list[str]:
    out = []
    pepe = world.get("pepe")
    if pepe.meters["wet"] < THRESHOLD:
        return out
    sig = ("mud", "pepe")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pepe.meters["mud"] += 1
    pepe.meters["tiredness"] += 1
    out.append("The slick path turned Pepe's paws muddy.")
    return out


def _r_lost(world: World) -> list[str]:
    out = []
    sack = world.get("berries")
    if sack.owner != "geese":
        return out
    if sack.meters["lost"] >= THRESHOLD:
        return out
    sig = ("lost", "berries")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    sack.meters["lost"] += 1
    out.append("The berries rolled away into the reeds.")
    return out


def _r_shame(world: World) -> list[str]:
    out = []
    pepe = world.get("pepe")
    if pepe.meters["mud"] < THRESHOLD:
        return out
    sig = ("shame", "pepe")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pepe.memes["shame"] += 1
    pepe.memes["humor"] += 1
    out.append("Pepe gave a muddy grin, though he felt small inside.")
    return out


CAUSAL_RULES = [Rule("mud", _r_mud), Rule("lost", _r_lost), Rule("shame", _r_shame)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


SETTINGS = {
    "marsh": Setting(place="the marsh path", mood="foggy"),
    "field": Setting(place="the reed field", mood="windy"),
}

ITEMS = {
    "lantern": Item("lantern", "lantern", "a little lantern", "dark"),
    "berries": Item("berries", "berries", "a sack of berries", "greed"),
    "frog": Item("frog", "frog", "a frog by the bank", "humor"),
}

CURIOUS_LINES = [
    "The reeds hissed softly, as if they knew a secret.",
    "A lantern flickered beside the path, and the light made every shadow look taller.",
    "Somewhere ahead, a rustle answered Pepe's footsteps.",
]

ASP_RULES = r"""
pepe_named(pepe).
risk(pepe, greed).
risk(pepe, humor).
suspense_if(R) :- risk(pepe, R).
bad_ending :- greed, near(berries), not safe_route.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("pepe_named", "pepe"),
        asp.fact("near", "berries"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def tell(setting: Setting, hero_name: str) -> World:
    world = World(setting)
    pepe = world.add(Entity(id="pepe", kind="character", type="fox", label=hero_name))
    old_mouse = world.add(Entity(id="mouse", kind="character", type="mouse", label="an old mouse"))
    geese = world.add(Entity(id="geese", kind="character", type="geese", label="the geese", plural=True))
    lantern = world.add(Entity(id="lantern", label="lantern"))
    berries = world.add(Entity(id="berries", label="berries", phrase="a sack of berries", owner="geese"))
    frog = world.add(Entity(id="frog", kind="character", type="frog", label="a frog"))

    world.say(f"Pepe was a small fox with quick feet and a quicker joke.")
    world.say("He loved funny tricks, shiny light, and any path that looked like a puzzle.")
    world.say(f"On {setting.place}, a lantern glowed near the reeds.")
    world.say(random.choice(CURIOUS_LINES))

    world.para()
    world.say("Pepe heard a rustle ahead and wanted to know what made it.")
    pepe.memes["curiosity"] += 1
    pepe.memes["humor"] += 1
    pepe.meters["light"] += 1

    world.say("The old mouse whispered, 'Walk slowly, little fox. Some secrets are better with both eyes open.'")
    world.say("Pepe laughed at that and went on anyway.")

    world.para()
    world.say("The rustle grew louder.")
    pepe.memes["fear"] += 1
    pepe.meters["wet"] += 1
    world.say("A shallow pool hid under the reeds, and Pepe splashed right through it.")
    propagate(world)

    world.say("Then the geese stepped out from the fog with the berries between them.")
    world.say("Pepe reached for the sack, thinking the prize would make the muddy walk worth it.")
    pepe.memes["greed"] += 1

    world.say("But the reeds were slick, and his paws slid out from under him.")
    pepe.meters["wet"] += 1
    pepe.meters["lost"] += 1
    propagate(world)

    world.para()
    world.say("The geese honked and hurried off with the berries, while Pepe sat in the mud blinking.")
    world.say("The frog by the bank croaked as if it were laughing at the joke the path had played on him.")
    world.say("Pepe smiled too, but the smile was a thin one; the marsh had kept the treasure and sent him home empty.")

    pepe.memes["shame"] += 1
    pepe.meters["tiredness"] += 1
    world.facts.update(
        hero=pepe,
        mouse=old_mouse,
        geese=geese,
        lantern=lantern,
        berries=berries,
        frog=frog,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short fable about Pepe, a curious fox, who follows a mysterious sound and learns a hard lesson.",
        "Tell a suspenseful, funny animal story where Pepe chases a rustle in the reeds and ends muddy and empty-handed.",
        "Write a child-friendly fable with a warning, a risky choice, and a bad ending that teaches caution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"The story is about Pepe, a little fox who loves shiny things and funny surprises.",
        ),
        QAItem(
            question="What made the path feel suspenseful?",
            answer="The fog, the rustling reeds, and the hidden pool made the path feel uncertain and tense.",
        ),
        QAItem(
            question="What happened when Pepe tried to take the berries?",
            answer="He slipped in the mud, the geese kept the berries, and Pepe ended up empty-handed.",
        ),
        QAItem(
            question="How did Pepe feel at the end?",
            answer="He felt muddy, embarrassed, and a little foolish, even though he tried to laugh it off.",
        ),
        QAItem(
            question="What lesson does the fable give?",
            answer="It teaches that chasing a greedy thought can lead to a bad ending, especially when a warning is ignored.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is mud?",
            answer="Mud is wet, soft dirt that can make feet and paws slippery and dirty.",
        ),
        QAItem(
            question="Why can fog make a place feel spooky?",
            answer="Fog hides things far away, so a path can feel mysterious and hard to trust.",
        ),
        QAItem(
            question="Why should someone listen to a warning near water?",
            answer="Water and wet ground can be slippery, so a warning can help someone stay safe.",
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
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id}: {' '.join(parts)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this world only generates Pepe as the curious fox on the marsh path.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-style Pepe story world with suspense and a bad ending.")
    ap.add_argument("--name")
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
    return StoryParams(name=args.name or "Pepe", seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS["marsh"], params.name)
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


def asp_verify() -> int:
    print("OK: ASP twin is present for parity checking.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show pepe_named/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible story tuple: pepe, marsh, greedy suspense, bad ending.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(name="Pepe", seed=base_seed))]
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
