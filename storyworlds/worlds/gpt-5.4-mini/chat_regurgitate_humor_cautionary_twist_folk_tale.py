#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/chat_regurgitate_humor_cautionary_twist_folk_tale.py
====================================================================================

A small standalone storyworld for a folk-tale-like cautionary comedy about
children, a gossiping chat, a regurgitated rumor, and a twist ending that turns
the lesson into a bright community fix.

Premise
-------
Two children share a folk-tale-style secret in the village square. A noisy chat
spreads the story too far, and one child "regurgitates" the rumor back in a
mocking way. That causes hurt feelings and a tangle of trouble. A sensible elder
responds with a calm, practical remedy, and the twist is that the rumor was
about a harmless lost pie recipe, not a treasure or curse. The village learns to
listen carefully before passing words along.

Seed words used in the world:
- chat
- regurgitate

Features:
- Humor
- Cautionary
- Twist
- Folk tale style

This script follows the Storyweavers contract:
- typed entities with meters and memes
- state-driven prose
- story-grounded QA from world state
- Python + ASP parity checks
- standard CLI with --verify, --asp, --show-asp, --json, --qa, --trace, --all, -n
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0, "damage": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "fear": 0.0, "embarrassment": 0.0, "wisdom": 0.0}

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
        return {"mother": "mom", "father": "dad", "elder": "elder"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
@dataclass
class StoryParams:
    village: str
    speaker: str
    speaker_gender: str
    listener: str
    listener_gender: str
    elder: str
    elder_gender: str
    rumor: str
    twist: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        return c


VILLAGES = {
    "brook": "the brook-side village",
    "hill": "the hill village",
    "orchard": "the orchard village",
}

RUMORS = {
    "lost_pie": {
        "topic": "a lost berry pie",
        "spread": "the pie was gone from the windowsill",
        "truth": "the pie had been moved to cool on the porch",
        "lesson": "A story should be checked before it is shared again.",
    },
    "magic_bell": {
        "topic": "a magic bell",
        "spread": "the bell was said to summon a storm",
        "truth": "the bell was only a dinner bell with a chipped clapper",
        "lesson": "Not every shiny tale is true just because it sounds grand.",
    },
    "golden_spoon": {
        "topic": "a golden spoon",
        "spread": "the spoon was said to bring luck to anyone who touched it",
        "truth": "the spoon was only the cook's favorite spoon for jam",
        "lesson": "Small things can grow huge when people chat too carelessly.",
    },
}

TWISTS = {
    "pie": "a harmless pie story",
    "bell": "a plain old dinner bell",
    "spoon": "the cook's favorite spoon",
}


def _verbally_wise(world: World) -> None:
    pass


def spread_rumor(world: World, speaker: Entity, listener: Entity, rumor: dict) -> None:
    speaker.memes["joy"] += 1
    listener.memes["curiosity"] += 1
    world.say(
        f"In {world.facts['village_name']}, {speaker.id} and {listener.id} had a chat by the market cart. "
        f'{speaker.id} whispered about {rumor["topic"]}, and the words began to wander.'
    )
    world.say(
        f'Before long, people repeated that {rumor["spread"]}. The little tale grew bigger every time it was told.'
    )


def regurgitate_rumor(world: World, child: Entity, rumor: dict) -> None:
    child.memes["embarrassment"] += 1
    child.meters["mess"] += 1
    world.say(
        f"Then {child.id} tried to regurgitate the rumor in a noisy way, tossing the same words back out again."
    )
    world.say(
        f"That made the folk in the square frown and giggle at once, for the story came out with too much salt and not enough sense."
    )


def elder_warns(world: World, elder: Entity, speaker: Entity, listener: Entity, rumor: dict) -> None:
    elder.memes["wisdom"] += 1
    world.say(
        f"An elder named {elder.id} tapped {speaker.id}'s shoulder and said, "
        f'"Child, words are like seeds. If you throw them without looking, you may grow weeds."'
    )
    world.say(
        f'{elder.id} told {listener.id} to stop and listen carefully, because the tale was not what it first seemed.'
    )


def twist_reveal(world: World, rumor: dict) -> None:
    world.say(
        f"Then came the twist: the great rumor was only {rumor['truth']}."
    )
    world.say(
        f"The whole village laughed, not because anyone was foolish, but because the story had dressed itself in a huge cloak and turned out to be tiny."
    )


def repair(world: World, elder: Entity, speaker: Entity, listener: Entity, rumor: dict) -> None:
    for e in (speaker, listener):
        e.memes["fear"] = max(0.0, e.memes["fear"] - 1.0)
        e.memes["wisdom"] += 1
        e.memes["joy"] += 1
    world.say(
        f"{elder.id} led them to the porch and showed them the truth, then asked them to carry the right message instead: {rumor['lesson']}"
    )
    world.say(
        f"After that, {speaker.id} and {listener.id} promised to chat more slowly and never regurgitate a rumor before checking it."
    )
    world.say(
        f"By sunset, the village was calm again, and the only thing that spread fast was a laugh shared kindly from door to door."
    )


def predict_consequence(world: World, rumor: dict) -> dict:
    sim = world.copy()
    sim.get("speaker").meters["mess"] += 1
    sim.get("listener").memes["embarrassment"] += 1
    return {
        "embarrassment": sim.get("listener").memes["embarrassment"],
        "mess": sim.get("speaker").meters["mess"],
    }


def tell(params: StoryParams) -> World:
    world = World()
    world.facts["village"] = params.village
    world.facts["village_name"] = VILLAGES[params.village]
    rumor = RUMORS[params.rumor]
    world.facts["rumor"] = rumor
    world.facts["twist"] = TWISTS[params.twist]

    speaker = world.add(Entity(id=params.speaker, kind="character", type=params.speaker_gender, role="speaker"))
    listener = world.add(Entity(id=params.listener, kind="character", type=params.listener_gender, role="listener"))
    elder = world.add(Entity(id=params.elder, kind="character", type=params.elder_gender, role="elder", label="the elder"))

    world.say(
        f"Once in {VILLAGES[params.village]}, {speaker.id} and {listener.id} were enjoying a bright chat beneath a signpost."
    )
    world.say(
        f"They were talking about {rumor['topic']}, and the wind kept tugging at the words like a curious puppy."
    )

    world.para()
    spread_rumor(world, speaker, listener, rumor)
    preview = predict_consequence(world, rumor)
    world.facts["preview"] = preview

    world.para()
    elder_warns(world, elder, speaker, listener, rumor)
    regurgitate_rumor(world, listener, rumor)

    world.para()
    twist_reveal(world, rumor)
    repair(world, elder, speaker, listener, rumor)

    world.facts.update(
        speaker=speaker,
        listener=listener,
        elder=elder,
        outcome="repaired",
        lesson=rumor["lesson"],
        rumor_topic=rumor["topic"],
        preview=preview,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale-style story for a young child that includes the words "chat" and "regurgitate" and ends with a twist.',
        f"Tell a cautionary village story where {f['speaker'].id} and {f['listener'].id} chat about {f['rumor_topic']}, then one of them regurgitates the rumor and an elder sets it right.",
        f"Write a humorous but careful story in a folk-tale voice about how a rumor grows when children chat too much and the truth turns out smaller than everyone thought.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    speaker: Entity = f["speaker"]
    listener: Entity = f["listener"]
    elder: Entity = f["elder"]
    rumor = f["rumor"]
    return [
        QAItem(
            question="Who are the story about?",
            answer=f"The story is about {speaker.id}, {listener.id}, and the elder who helped them. They start with a chat and then learn how to handle a rumor kindly."
        ),
        QAItem(
            question=f"Why did the elder warn them?",
            answer=f"The elder warned them because the rumor was being passed around without care, and {listener.id} was about to regurgitate it again. That could hurt feelings and make a small tale grow crooked."
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {rumor['truth']}. The big gossip was only a small plain thing wearing a fancy hat."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to chat?",
            answer="To chat means to talk in a friendly way, often about small everyday things."
        ),
        QAItem(
            question="What does regurgitate mean?",
            answer="Literally, it means to bring food back up. In this story it means repeating words carelessly, as if spitting the rumor back out."
        ),
        QAItem(
            question="Why should people be careful with rumors?",
            answer="Rumors can hurt feelings or become bigger and stranger than the truth. It is wiser to check a story before repeating it."
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        out.append(f"  {e.id}: meters={e.meters} memes={e.memes} role={e.role}")
    out.append(f"  facts={sorted(world.facts.keys())}")
    return "\n".join(out)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale cautionary storyworld about chat, regurgitate, and a twist.")
    ap.add_argument("--village", choices=VILLAGES)
    ap.add_argument("--speaker")
    ap.add_argument("--speaker-gender", choices=["girl", "boy"])
    ap.add_argument("--listener")
    ap.add_argument("--listener-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["woman", "man"])
    ap.add_argument("--rumor", choices=RUMORS)
    ap.add_argument("--twist", choices=TWISTS)
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


NAMES_GIRL = ["Mira", "Tessa", "Lina", "Nora", "Ada", "Wren"]
NAMES_BOY = ["Pip", "Jory", "Milo", "Tobin", "Oren", "Luca"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for v in VILLAGES:
        for r in RUMORS:
            for t in TWISTS:
                combos.append((v, r, t))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combo = rng.choice(valid_combos())
    village, rumor, twist = combo
    if args.village:
        village = args.village
    if args.rumor:
        rumor = args.rumor
    if args.twist:
        twist = args.twist
    if (village, rumor, twist) not in valid_combos():
        raise StoryError("No valid story matches the given options.")
    sg = args.speaker_gender or rng.choice(["girl", "boy"])
    lg = args.listener_gender or rng.choice(["girl", "boy"])
    eg = args.elder_gender or rng.choice(["woman", "man"])
    speaker = args.speaker or rng.choice(NAMES_GIRL if sg == "girl" else NAMES_BOY)
    listener = args.listener or rng.choice([n for n in (NAMES_GIRL if lg == "girl" else NAMES_BOY) if n != speaker])
    elder = args.elder or rng.choice(["Grandma", "Grandpa", "Aunt Nella", "Uncle Bram"])
    return StoryParams(village, speaker, sg, listener, lg, elder, eg, rumor, twist)


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
valid(V, R, T) :- village(V), rumor(R), twist(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for v in VILLAGES:
        lines.append(asp.fact("village", v))
    for r in RUMORS:
        lines.append(asp.fact("rumor", r))
    for t in TWISTS:
        lines.append(asp.fact("twist", t))
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
        print("OK: ASP matches Python valid_combos().")
    else:
        rc = 1
        print("MISMATCH: ASP and Python valid_combos() differ.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as e:
        print(f"FAIL: generate() smoke test crashed: {e}")
        rc = 1
    return rc


CURATED = [
    StoryParams("brook", "Mira", "girl", "Pip", "boy", "Grandma", "woman", "lost_pie", "pie"),
    StoryParams("hill", "Luca", "boy", "Nora", "girl", "Grandpa", "man", "magic_bell", "bell"),
    StoryParams("orchard", "Tessa", "girl", "Oren", "boy", "Aunt Nella", "woman", "golden_spoon", "spoon"),
]


def build_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for v, r, t in asp_valid_combos():
            print(v, r, t)
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = build_story_params(args, random.Random(base + i))
            p.seed = base + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
