#!/usr/bin/env python3
"""
storyworlds/worlds/replicate_quackeroo_twist_heartwarming.py
=============================================================

A small heartwarming story world about a child, a noisy quackeroo toy, and a
gentle Twist that helps everyone feel close again.

Premise:
- A child loves a little toy quackeroo that can repeat words and sounds.
- The toy's repeating is funny at first, then gets in the way.
- A caring grown-up offers a calm, kind Twist: use the toy in a quieter,
  helpful way, so the child keeps the joy without the trouble.

The world is deliberately small and constraint-checked:
- There is one at-risk thing that can be overused or repeated too much.
- There is one reasonable fix that redirects the repetition.
- The ending proves the change in state through action and image.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Twist:
    id: str
    label: str
    offer: str
    tail: str
    helps: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _repeat(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("repeat", 0.0) < THRESHOLD:
            continue
        sig = ("repeat", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["overexcited"] = actor.memes.get("overexcited", 0.0) + 1
        out.append(f"{actor.pronoun().capitalize()} kept repeating the same sound again and again.")
    return out


def _calm(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("calmed", 0.0) < THRESHOLD:
            continue
        sig = ("calm", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["happy"] = actor.memes.get("happy", 0.0) + 1
        out.append(f"{actor.pronoun().capitalize()} took a breath and smiled.")
    return out


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_repeat, _calm):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    for s in produced:
        world.say(s)
    return produced


def predict_repetition(world: World, child: Entity, toy: Entity) -> dict:
    sim = world.copy()
    child2 = sim.get(child.id)
    toy2 = sim.get(toy.id)
    child2.meters["repeat"] += 1
    toy2.meters["heard"] = toy2.meters.get("heard", 0.0) + 1
    propagate(sim)
    return {
        "too_much": child2.meters.get("repeat", 0.0) >= THRESHOLD,
        "noise": child2.memes.get("overexcited", 0.0) >= THRESHOLD,
    }


def introduce(world: World, child: Entity) -> None:
    world.say(f"{child.id} was a little {child.type} who loved making kind little echoes with toys and words.")


def loves_toy(world: World, child: Entity, toy: Entity) -> None:
    child.memes["love"] = child.memes.get("love", 0.0) + 1
    world.say(f"{child.id} loved {toy.phrase}; {toy.pronoun('subject').capitalize()} could copy a word in a silly, squawky voice.")


def receives_toy(world: World, parent: Entity, child: Entity, toy: Entity) -> None:
    world.say(f"One morning, {child.id}'s {parent.label} brought home {child.pronoun('object')} {toy.phrase}.")
    world.say(f"{child.id} hugged {toy.it()} right away and tried out its happy little quackeroo sound.")


def playtime(world: World, child: Entity, parent: Entity, toy: Entity, act: Activity) -> None:
    world.para()
    world.say(f"One afternoon at {world.place.name}, {child.id} wanted to {act.verb}.")
    world.say(f"{child.id} kept saying the same word to the quackeroo, and the quackeroo kept copying it: {act.keyword}, {act.keyword}, {act.keyword}.")
    child.meters["repeat"] = child.meters.get("repeat", 0.0) + 1
    toy.meters["heard"] = toy.meters.get("heard", 0.0) + 1
    propagate(world)
    if predict_repetition(world, child, toy)["too_much"]:
        world.say(f"{parent.id} laughed at first, then gently worried that too much repeating would turn fun into a noisy tangle.")


def twist_offer(world: World, parent: Entity, child: Entity, toy: Entity, twist: Twist, act: Activity, prize: Prize) -> None:
    world.para()
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1
    world.say(f"Then {parent.id} had a Twist.")
    world.say(f'"How about we use the quackeroo to {twist.offer}," {parent.pronoun("possessive")} {parent.type} said.')
    world.say(f'That way, the repeating can help instead of getting in the way, and your {prize.label} stays safe.')
    if act.id in twist.helps:
        child.memes["listening"] = child.memes.get("listening", 0.0) + 1


def accept_twist(world: World, child: Entity, parent: Entity, toy: Entity, twist: Twist, act: Activity) -> None:
    child.memes["calmed"] = 1.0
    child.memes["happy"] = child.memes.get("happy", 0.0) + 1
    world.say(f"{child.id} tried it, and the change felt nice.")
    world.say(f"{child.id} made the quackeroo repeat a helpful message instead of the noisy one, and the room felt warm and sweet again.")
    world.say(f"By the end, {child.id} was {act.gerund}, {twist.tail}, while {parent.id} smiled beside {child.pronoun('object')}.")


def build_story(place: Place, act: Activity, prize: Prize, twist: Twist, child_name: str, child_type: str, parent_type: str) -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mom" if parent_type == "mother" else "dad"))
    toy = world.add(Entity(id="Quackeroo", type="toy", label="quackeroo", phrase="a little quackeroo toy"))
    gift = world.add(Entity(id="Prize", type=prize.type, label=prize.label, phrase=prize.phrase, owner=child.id, caretaker=parent.id))

    introduce(world, child)
    loves_toy(world, child, toy)
    receives_toy(world, parent, child, toy)
    playtime(world, child, parent, toy, act)
    twist_offer(world, parent, child, toy, twist, act, prize)
    accept_twist(world, child, parent, toy, twist, act)

    world.facts.update(child=child, parent=parent, toy=toy, prize=gift, activity=act, twist=twist, place=place)
    return world


SETTINGS = {
    "kitchen": Place(name="the kitchen", indoor=True, affords={"repeat"}),
    "bedroom": Place(name="the bedroom", indoor=True, affords={"repeat"}),
    "porch": Place(name="the porch", indoor=False, affords={"repeat"}),
}

ACTIVITIES = {
    "repeat": Activity(
        id="repeat",
        verb="make the quackeroo repeat words",
        gerund="making the quackeroo repeat gentle words",
        rush="say the same thing once more",
        mess="noise",
        soil="too loud",
        keyword="quackeroo",
        tags={"repeat", "quackeroo"},
    ),
}

PRIZES = {
    "blanket": Prize(label="blanket", phrase="a soft little blanket", type="blanket"),
    "book": Prize(label="book", phrase="a picture book with bright pages", type="book"),
    "teddy": Prize(label="teddy bear", phrase="a fuzzy teddy bear", type="teddy"),
}

TWISTS = {
    "helper_note": Twist(
        id="helper_note",
        label="a helper note",
        offer="help it repeat a kind note for the family",
        tail="the quackeroo repeating a little thank-you note",
        helps={"repeat"},
    ),
    "bedtime_song": Twist(
        id="bedtime_song",
        label="a bedtime song",
        offer="help it repeat part of a bedtime song",
        tail="the quackeroo chirping the song while the lamp glowed softly",
        helps={"repeat"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Pia", "Ivy"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Eli", "Sam"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    twist: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize in PRIZES:
                for tw in TWISTS:
                    out.append((place, act, prize, tw))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming quackeroo story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--twist", choices=TWISTS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.twist is None or c[3] == args.twist)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize, twist = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, activity=activity, prize=prize, twist=twist, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = build_story(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        TWISTS[params.twist],
        params.name,
        params.gender,
        params.parent,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    act = f["activity"]
    return [
        f"Write a heartwarming story about a child and a quackeroo that keeps saying {act.keyword}.",
        f"Tell a gentle story where a grown-up finds a Twist so the quackeroo's repeating becomes helpful.",
        f"Write a short child-friendly story that includes the word quackeroo and ends with a warm family feeling.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, act, prize, twist = f["child"], f["parent"], f["activity"], f["prize"], f["twist"]
    return [
        QAItem(
            question=f"What did {child.id} want to do with the quackeroo at {f['place'].name}?",
            answer=f"{child.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did {parent.id} worry when {child.id} kept saying the same word?",
            answer=f"{parent.id} worried because the quackeroo kept repeating it, and the noise could get too loud and upset the gentle mood.",
        ),
        QAItem(
            question=f"What Twist helped the story end well?",
            answer=f"The story used {twist.label}, which helped turn the quackeroo's repeating into something helpful and kind.",
        ),
        QAItem(
            question=f"What was still safe and cozy by the end?",
            answer=f"{child.id}'s {prize.label} stayed safe, and the family scene felt warm and happy.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a quackeroo?", answer="A quackeroo is a made-up little toy that can copy sounds or words in a silly, cheerful way."),
        QAItem(question="What does a Twist mean in a story?", answer="A Twist is a change that gently redirects what is happening and helps the story end in a new, useful way."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    out = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"{e.id} ({e.type}) " + " ".join(bits))
    return "\n".join(out)


ASP_RULES = r"""
valid_place(P) :- place(P).
valid_story(P,A,R,T) :- place(P), activity(A), prize(R), twist(T).
#show valid_story/4.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for r in PRIZES:
        lines.append(asp.fact("prize", r))
    for t in TWISTS:
        lines.append(asp.fact("twist", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: ASP matches Python ({len(py_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python")
    return 1


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


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
    StoryParams(place="kitchen", activity="repeat", prize="blanket", twist="helper_note", name="Mina", gender="girl", parent="mother"),
    StoryParams(place="bedroom", activity="repeat", prize="book", twist="bedtime_song", name="Theo", gender="boy", parent="father"),
    StoryParams(place="porch", activity="repeat", prize="teddy", twist="helper_note", name="Ivy", gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} compatible stories:")
        for row in vals:
            print("  ", row)
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
