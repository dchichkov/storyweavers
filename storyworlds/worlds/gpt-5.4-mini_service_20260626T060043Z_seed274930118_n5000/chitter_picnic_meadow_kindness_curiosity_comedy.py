#!/usr/bin/env python3
"""
Standalone storyworld: chittering picnic-meadow comedy with kindness and curiosity.

A small child and a curious meadow creature discover a picnic basket, a little
misunderstanding, and a kind fix that ends with everyone sharing laughs.
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
class Meadow:
    place: str = "the picnic meadow"
    affords: set[str] = field(default_factory=lambda: {"chitter", "snack", "share"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    effect: str
    mess: str = ""
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    appetite: str
    plural: bool = False


@dataclass
class World:
    setting: Meadow
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    companion: str
    prize: str
    seed: Optional[int] = None


SETTINGS = {
    "meadow": Meadow(),
}

ACTIVITIES = {
    "chitter": Activity(
        id="chitter",
        verb="follow the chittering sound",
        gerund="following the chittering",
        rush="dash toward the bush",
        effect="a funny chitter-trail of crumbs and giggles",
        mess="crumbs",
        keyword="chitter",
        tags={"chitter", "curiosity", "comedy"},
    ),
    "snack": Activity(
        id="snack",
        verb="share the snack",
        gerund="sharing snacks",
        rush="snatch the crackers",
        effect="happy chewing and louder laughs",
        mess="crumbs",
        keyword="snack",
        tags={"kindness", "comedy"},
    ),
    "share": Activity(
        id="share",
        verb="pass out treats",
        gerund="passing out treats",
        rush="scatter the napkins",
        effect="everyone getting a little bite and a bigger smile",
        mess="crumbs",
        keyword="share",
        tags={"kindness", "comedy"},
    ),
}

PRIZES = {
    "crackers": Prize(
        label="crackers",
        phrase="a little red tin of crackers",
        type="crackers",
        appetite="crumbly",
        plural=True,
    ),
    "berries": Prize(
        label="berries",
        phrase="a paper bowl of sweet berries",
        type="berries",
        appetite="sweet",
        plural=True,
    ),
    "cookies": Prize(
        label="cookies",
        phrase="a plate of round cookies",
        type="cookies",
        appetite="crumbly",
        plural=True,
    ),
}

GIRL_NAMES = ["Mila", "June", "Lily", "Nina", "Pia", "Rosa"]
BOY_NAMES = ["Eli", "Toby", "Sam", "Noah", "Ben", "Max"]
TRAITS = ["curious", "kind", "cheerful", "gentle", "silly", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for aid in setting.affords:
            for pid in PRIZES:
                combos.append((place, aid, pid))
    return combos


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: the meadow joke only works when {activity.verb} can lead to a kind snack scene.)"


def explain_gender(prize_id: str, gender: str) -> str:
    return f"(No story: try a different name/gender pairing for {PRIZES[prize_id].label}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld set in a picnic meadow.")
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--activity", choices=list(ACTIVITIES))
    ap.add_argument("--prize", choices=list(PRIZES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--companion")
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if args.activity not in SETTINGS["meadow"].affords:
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    companion = args.companion or rng.choice(["chipmunk", "squirrel", "rabbit"])
    return StoryParams(name=name, gender=gender, parent=parent, companion=companion, prize=prize)


def _story_name(hero: Entity) -> str:
    return hero.id


def tell(params: StoryParams) -> World:
    world = World(SETTINGS["meadow"])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label="parent"))
    comp = world.add(Entity(id=params.companion, kind="character", type="thing", label=params.companion))
    prize = world.add(Entity(
        id="prize",
        type=PRIZES[params.prize].type,
        label=PRIZES[params.prize].label,
        phrase=PRIZES[params.prize].phrase,
        owner=hero.id,
        caretaker=parent.id,
        plural=PRIZES[params.prize].plural,
    ))

    activity = ACTIVITIES["chitter"]
    snack = ACTIVITIES["snack"]
    share = ACTIVITIES["share"]

    world.say(f"{hero.id} was a little {params.gender} who loved the picnic meadow.")
    world.say(f"{hero.pronoun().capitalize()} was especially curious about any {activity.keyword} in the grass.")
    world.say(f"One sunny day, {parent.label} brought {hero.pronoun('object')} {prize.phrase}.")
    world.say(f"{hero.id} smiled at the snack and kept it close.")

    world.para()
    world.say(f"Near a clover patch, {hero.id} heard a soft {activity.keyword}-chitter-chitter from a bush.")
    world.say(f"{hero.id} wanted to {activity.verb}, while {parent.label} worried the little snack might get nabbed.")
    world.say(f"Before anyone could blink, {hero.id} tried to {activity.rush}, and {comp.id} popped out with a crumb on its nose.")
    world.say(f"{comp.id} looked at the snack and gave a tiny embarrassed chitter.")

    hero.memes["curiosity"] = 1
    hero.memes["kindness"] = 0
    hero.memes["joy"] = 0
    prize.meters["safe"] = 0

    world.para()
    world.say(f"{hero.id} did not get mad.")
    world.say(f"Instead, {hero.id} broke the snack in half and held out a piece.")
    world.say(f'"Here," {hero.id} said. "You can have some too."')
    world.say(f"{comp.id} was so surprised it chittered like a squeaky toy with manners.")
    world.say(f"{parent.label} laughed, because the bush had started the whole fuss and kindness fixed it.")

    hero.memes["kindness"] = 1
    hero.memes["joy"] = 1
    prize.meters["shared"] = 1
    world.facts = {
        "hero": hero,
        "parent": parent,
        "companion": comp,
        "prize": prize,
        "activity": activity,
        "snack": snack,
        "share": share,
        "setting": world.setting,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    return [
        "Write a short comedy story set in a picnic meadow about curiosity and kindness.",
        f"Tell a gentle story where {hero.id} hears a chittering sound, worries about {prize.label}, and chooses kindness.",
        "Write a child-friendly story with a bush, a snack, and a funny surprise ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    comp = f["companion"]
    prize = f["prize"]
    return [
        QAItem(
            question=f"What did {hero.id} hear in the picnic meadow?",
            answer=f"{hero.id} heard a soft chittering sound from a bush near the picnic meadow.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the snack?",
            answer=f"{parent.label} worried because {hero.id} was about to rush toward the bush, and the snack might get taken or dropped.",
        ),
        QAItem(
            question=f"What did {hero.id} do instead of getting angry at {comp.id}?",
            answer=f"{hero.id} shared the snack and offered a piece, which showed kindness.",
        ),
        QAItem(
            question=f"What happened at the end with the snack?",
            answer=f"The snack was shared, so it became part of a funny picnic instead of a problem.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to know more about something new or surprising.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing to help, share, or be gentle with someone else.",
        ),
        QAItem(
            question="What is a picnic meadow?",
            answer="A picnic meadow is a grassy open place where people can sit on blankets, eat snacks, and play outside.",
        ),
        QAItem(
            question="Why might a chipmunk chitter?",
            answer="A chipmunk might chitter to make a warning sound, to talk to other chipmunks, or because it is excited.",
        ),
    ]


ASP_RULES = r"""
curious(hero) :- hears(hero, chittering), wants_to_know(hero).
kind_story(hero) :- curious(hero), shares(hero, snack).
happy_end(hero) :- kind_story(hero), not angry(hero).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("hears", "hero", "chittering"),
        asp.fact("wants_to_know", "hero"),
        asp.fact("shares", "hero", "snack"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Minimal parity check: rules should derive a happy ending from the facts.
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show happy_end/1.\n#show kind_story/1.\n#show curious/1."))
    atoms = set((sym.name, tuple(getattr(a, "name", getattr(a, "string", getattr(a, "number", None))) for a in sym.arguments)) for sym in model)
    expected = {("curious", ("hero",)), ("kind_story", ("hero",)), ("happy_end", ("hero",))}
    if atoms == expected:
        print("OK: ASP derives the same story shape as Python.")
        return 0
    print("MISMATCH between ASP and Python story shape.")
    print("atoms:", atoms)
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show happy_end/1."))
        return
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show happy_end/1.\n#show curious/1.\n#show kind_story/1."))
        print(model)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, p in enumerate([
            StoryParams(name="Mila", gender="girl", parent="mother", companion="chipmunk", prize="crackers"),
            StoryParams(name="Eli", gender="boy", parent="father", companion="squirrel", prize="berries"),
            StoryParams(name="June", gender="girl", parent="mother", companion="rabbit", prize="cookies"),
        ]):
            p.seed = base_seed + i
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
