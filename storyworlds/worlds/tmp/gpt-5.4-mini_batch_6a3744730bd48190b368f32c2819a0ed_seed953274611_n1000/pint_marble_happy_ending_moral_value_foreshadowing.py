#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pint_marble_happy_ending_moral_value_foreshadowing.py
=====================================================================================

A small standalone storyworld for a tiny adventure tale: a child goes on a
short quest, meets a little problem, notices a foreshadowing clue, chooses a
moral action, and ends with a happy image that proves the change.

Seed words: pint, marble
Features: Happy Ending, Moral Value, Foreshadowing
Style: Adventure
"""

from __future__ import annotations

import argparse
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
MORAL_MIN = 1.0


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
    tags: set[str] = field(default_factory=set)

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
class Place:
    id: str
    scene: str
    dark_spot: str
    promise: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    object: str
    phrase: str
    owner: str
    risky: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class MoralChoice:
    id: str
    action: str
    value: str
    fix: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        import copy as _copy
        return World(place=self.place, entities=_copy.deepcopy(self.entities), fired=set(self.fired),
                     paragraphs=[[]], facts=dict(self.facts))


@dataclass
class StoryParams:
    place: str
    quest: str
    choice: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    seed: Optional[int] = None


PLACES = {
    "harbor": Place(
        id="harbor",
        scene="a bright harbor with old stone steps and a dock that creaked in the breeze",
        dark_spot="the narrow cave under the dock",
        promise="hidden treasure",
        clue="a cool smell of salt and a shiny mark on the boards",
        tags={"harbor", "dock", "cave"},
    ),
    "garden": Place(
        id="garden",
        scene="a winding garden with vines, a fountain, and a small trail of lantern stones",
        dark_spot="the shadowed arch behind the fountain",
        promise="a secret path",
        clue="a trail of tiny wet footprints",
        tags={"garden", "fountain", "trail"},
    ),
    "hill": Place(
        id="hill",
        scene="a windy hill with grass, a stone path, and a lookout tower far above",
        dark_spot="the low tunnel beside the tower",
        promise="the old map",
        clue="a scrap of ribbon caught on a thorn bush",
        tags={"hill", "tower", "tunnel"},
    ),
}

QUESTS = {
    "pint": Quest(
        id="pint",
        object="pint",
        phrase="a little pint cup of juice for the trail",
        owner="hero",
        risky=True,
        tags={"pint", "drink"},
    ),
    "marble": Quest(
        id="marble",
        object="marble",
        phrase="a smooth marble that could roll into tiny cracks",
        owner="hero",
        risky=True,
        tags={"marble", "stone"},
    ),
    "lamp": Quest(
        id="lamp",
        object="lamp",
        phrase="a small lamp for the dark place",
        owner="hero",
        risky=False,
        tags={"lamp", "light"},
    ),
}

CHOICES = {
    "share": MoralChoice(
        id="share",
        action="shared it with the helper",
        value="sharing",
        fix="the problem grew smaller when they worked together",
        lesson="good things are bigger when they are shared",
        tags={"share", "kind"},
    ),
    "return": MoralChoice(
        id="return",
        action="gave it back to its owner",
        value="honesty",
        fix="the right owner smiled, and the path felt lighter",
        lesson="doing the honest thing makes a story end well",
        tags={"return", "honest"},
    ),
    "care": MoralChoice(
        id="care",
        action="carried it carefully and watched the trail",
        value="carefulness",
        fix="nothing broke, because they moved slowly and looked ahead",
        lesson="being careful helps an adventure stay safe",
        tags={"care", "careful"},
    ),
}

HEROES = [("Mina", "girl"), ("Finn", "boy"), ("Lina", "girl"), ("Toby", "boy")]
HELPERS = [("Pip", "boy"), ("Nora", "girl"), ("Jules", "boy"), ("Ada", "girl")]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid in PLACES:
        for qid, q in QUESTS.items():
            for cid in CHOICES:
                if q.risky and qid in {"pint", "marble"}:
                    out.append((pid, qid, cid))
                elif not q.risky and cid in CHOICES:
                    out.append((pid, qid, cid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with pint, marble, moral choice, and foreshadowing.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
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


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        if q.risky:
            lines.append(asp.fact("risky", qid))
    for cid in CHOICES:
        lines.append(asp.fact("choice", cid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,Q,C) :- place(P), quest(Q), choice(C), risky(Q).
valid(P,Q,C) :- place(P), quest(Q), choice(C), not risky(Q).
"""


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def reasonableness_ok(place: Place, quest: Quest, choice: MoralChoice) -> bool:
    return True


def predict(world: World, choice: MoralChoice) -> dict:
    sim = world.copy()
    sim.get("hero").memes["moral"] += 1
    sim.get("helper").memes["trust"] += 1
    return {"resolved": choice.id in CHOICES}


def tell(place: Place, quest: Quest, choice: MoralChoice, hero_name: str, hero_type: str,
         helper_name: str, helper_type: str) -> World:
    world = World(place=place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    cache = world.add(Entity(id="cache", kind="thing", type="thing", label=quest.object, tags=set(quest.tags)))
    hero.memes["wonder"] += 1
    helper.memes["care"] += 1

    world.say(
        f"{hero.id} and {helper.id} set out through {place.scene}. "
        f"{place.clue} hinted that the day would not stay simple for long."
    )
    world.say(
        f"They wanted to reach {place.promise}, but the path narrowed near {place.dark_spot}."
    )
    world.para()
    world.say(
        f"{hero.id} found {quest.phrase}. {helper.id} noticed the clue first and pointed to it."
    )
    world.say(
        f'"That {place.clue}," {helper.id} said, "means we should slow down and think."'
    )

    if quest.id == "pint":
        hero.meters["carrying"] += 1
        hero.meters["balance"] += 0.5
        helper.memes["concern"] += 1
        world.say(
            f"{hero.id} nearly tipped the pint while hurrying toward the dark opening."
        )
    else:
        hero.meters["carrying"] += 1
        world.say(
            f"{hero.id} kept the marble cupped in both hands so it would not roll away."
        )

    world.say(
        f"{helper.id} warned that small treasures can be lost fast in a place like this."
    )
    world.para()

    hero.memes["curiosity"] += 1
    helper.memes["trust"] += 1
    if choice.id == "share":
        world.say(
            f"{hero.id} smiled and shared it with {helper.id}. Together they used the treasure to mark the path."
        )
    elif choice.id == "return":
        world.say(
            f"{hero.id} did the honest thing and gave it back to its owner at the gate."
        )
    else:
        world.say(
            f"{hero.id} carried it carefully and watched every stone on the trail."
        )

    world.say(
        f"Their careful choice fixed the trouble, and the adventure ended with bright smiles instead of tears."
    )
    world.say(
        f"At the end, {hero.id} and {helper.id} stood safely on the path, "
        f"with {place.promise} ahead and the little treasure no longer in danger."
    )

    world.facts.update(
        place=place,
        quest=quest,
        choice=choice,
        hero=hero,
        helper=helper,
        cache=cache,
        resolved=True,
        foreshadow=place.clue,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a young child that includes the words "pint" and "marble".',
        f"Tell a short adventure where {f['hero'].id} notices a clue, chooses {f['choice'].value}, and the ending is happy.",
        f"Write a moral-value story about a small treasure, a warning clue, and a kind ending in {f['place'].id}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    place = f["place"]
    choice = f["choice"]
    quest = f["quest"]
    return [
        QAItem(
            question="What clue foreshadowed trouble?",
            answer=f"{place.clue} foreshadowed that the path would need extra care. It hinted that the adventure was about to get tricky."
        ),
        QAItem(
            question="What moral choice did the children make?",
            answer=f"They chose {choice.value}. That made the ending good because they solved the problem without acting selfishly."
        ),
        QAItem(
            question=f"Why did {helper.id} help {hero.id}?",
            answer=f"{helper.id} helped because the treasure and the trail both needed care. That teamwork kept the pint or marble safe and let the adventure end happily."
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended happily. The children stayed safe, fixed the trouble, and smiled at the end of the quest."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What is a pint?",
            answer="A pint is a small amount in a cup or container. In a story, it can be a little drink or a small measure."
        ),
        QAItem(
            question="What is a marble?",
            answer="A marble is a small hard ball, often smooth and shiny. It can roll away if you are not careful."
        ),
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives a clue that something important may happen later. It helps the reader feel ready for the turn in the story."
        ),
        QAItem(
            question="What makes an ending a happy ending?",
            answer="A happy ending leaves the characters safe, relieved, or smiling. The problem is solved or made smaller, so the last image feels bright."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(args: argparse.Namespace) -> str:
    return "(No story: the requested combination does not fit this tiny adventure world.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    combos = [c for c in combos
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.choice is None or c[2] == args.choice)]
    if not combos:
        raise StoryError(explain_rejection(args))
    place, quest, choice = rng.choice(sorted(combos))
    hero_name, hero_type = (args.hero, args.hero_type) if args.hero and args.hero_type else rng.choice(HEROES)
    helper_name, helper_type = (args.helper, args.helper_type) if args.helper and args.helper_type else rng.choice(HELPERS)
    if helper_name == hero_name:
        helper_name, helper_type = rng.choice([h for h in HELPERS if h[0] != hero_name])
    return StoryParams(
        place=place,
        quest=quest,
        choice=choice,
        hero=hero_name,
        hero_type=hero_type or "girl",
        helper=helper_name,
        helper_type=helper_type or "boy",
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.quest not in QUESTS:
        raise StoryError("Unknown quest.")
    if params.choice not in CHOICES:
        raise StoryError("Unknown choice.")
    world = tell(
        PLACES[params.place],
        QUESTS[params.quest],
        CHOICES[params.choice],
        params.hero,
        params.hero_type,
        params.helper,
        params.helper_type,
    )
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
    StoryParams(place="harbor", quest="pint", choice="share", hero="Mina", hero_type="girl", helper="Pip", helper_type="boy"),
    StoryParams(place="garden", quest="marble", choice="return", hero="Finn", hero_type="boy", helper="Ada", helper_type="girl"),
    StoryParams(place="hill", quest="pint", choice="care", hero="Lina", hero_type="girl", helper="Jules", helper_type="boy"),
]


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
    else:
        ok = False
        print("MISMATCH in valid combos:")
        print("  only in python:", sorted(py - cl))
        print("  only in asp:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        ok = False
        print(f"SMOKE TEST FAILED: {e}")
    return 0 if ok else 1


def build_default_sample(rng: random.Random) -> StorySample:
    return generate(resolve_params(argparse.Namespace(place=None, quest=None, choice=None, hero=None,
                                                      hero_type=None, helper=None, helper_type=None),
                                   rng))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combinations:")
        for triple in asp_valid_combos():
            print("  ", triple)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} at {p.place} with {p.quest}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
