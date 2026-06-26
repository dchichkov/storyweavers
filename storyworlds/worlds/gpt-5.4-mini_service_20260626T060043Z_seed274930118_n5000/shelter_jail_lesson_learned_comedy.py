#!/usr/bin/env python3
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

ASP_RULES = r"""
#show valid/4.
#show valid_story/5.

valid(P, A, O, S) :- place(P), activity(A), object(O), shelter_ok(P, A, O), style(S), style_ok(S).
valid_story(P, A, O, S, L) :- valid(P, A, O, S), lesson(L).
"""

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
    location: str = ""
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    is_indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    lesson: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    label: str
    phrase: str
    type: str
    location: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class StoryParams:
    place: str
    activity: str
    object: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


SETTINGS = {
    "shelter": Setting(place="the shelter", is_indoor=True, affords={"tail", "nap", "paint"}),
    "park": Setting(place="the park", is_indoor=False, affords={"tail", "nap"}),
}

ACTIVITIES = {
    "tail": Activity(
        id="tail",
        verb="chase the wagging tail",
        gerund="chasing a wagging tail",
        rush="zoom after the tail",
        mess="tumble",
        lesson="slow down and look where you are going",
        keyword="tail",
        tags={"funny", "pet"},
    ),
    "nap": Activity(
        id="nap",
        verb="take a nap in the blanket pile",
        gerund="napping in the blanket pile",
        rush="plop into the blankets",
        mess="snore",
        lesson="resting is nice, but you should ask first",
        keyword="blanket",
        tags={"pet"},
    ),
    "paint": Activity(
        id="paint",
        verb="paint a sign",
        gerund="painting a sign",
        rush="grab the paint",
        mess="smudge",
        lesson="careful hands make cleaner art",
        keyword="paint",
        tags={"art", "comedy"},
    ),
}

OBJECTS = {
    "clipboard": ObjectCfg(label="clipboard", phrase="a shiny clipboard", type="clipboard", location="desk"),
    "ball": ObjectCfg(label="ball", phrase="a squeaky red ball", type="ball", location="floor"),
    "sign": ObjectCfg(label="sign", phrase="a big paper sign", type="sign", location="wall"),
}

NAMES = ["Mina", "Toby", "Ruby", "Finn", "Nora", "Leo"]
HELPERS = ["volunteer", "caretaker", "helper", "manager"]
TRAITS = ["silly", "bouncy", "curious", "goofy", "cheerful"]


def shelter_ok(place: str, activity: str, obj: str) -> bool:
    return place in SETTINGS and activity in SETTINGS[place].affords and obj in OBJECTS


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p, s in SETTINGS.items():
        for a in s.affords:
            for o in OBJECTS:
                out.append((p, a, o))
    return out


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
        if SETTINGS[p].is_indoor:
            lines.append(asp.fact("indoor", p))
        for a in SETTINGS[p].affords:
            lines.append(asp.fact("affords", p, a))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
        lines.append(asp.fact("lesson", a, ACTIVITIES[a].lesson))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    lines.append(asp.fact("style", "comedy"))
    lines.append(asp.fact("style_ok", "comedy"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    p = set((a, b, c) for a, b, c, _ in asp_valid_combos())
    q = set(valid_combos())
    if p == q:
        print(f"OK: clingo gate matches valid_combos() ({len(q)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(p - q))
    print("  only in python:", sorted(q - p))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld: shelter, jail, and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
              and (args.object_ is None or c[2] == args.object_)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, obj = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    if obj == "clipboard" and activity == "nap":
        raise StoryError("The clipboard story does not fit a nap; try tail or paint.")
    return StoryParams(place=place, activity=activity, object=obj, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    act = ACTIVITIES[params.activity]
    objcfg = OBJECTS[params.object]
    w = World(setting)

    hero = w.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    helper = w.add(Entity(id="helper", kind="character", type="adult", label=f"the {params.helper}"))
    obj = w.add(Entity(id="object", type=objcfg.type, label=objcfg.label, phrase=objcfg.phrase,
                       location=objcfg.location, plural=objcfg.plural, caretaker=helper.id))

    hero.memes["curious"] = 1
    hero.memes["joy"] = 1

    w.say(f"{hero.id} was a {random.choice(TRAITS)} little {params.gender} who loved visiting {setting.place}.")
    w.say(f"At the {params.place}, {hero.pronoun()} spotted {obj.phrase} and got an idea.")
    w.para()
    w.say(f"{hero.id} wanted to {act.verb}, which looked funny enough to make a duck giggle.")
    w.say(f"But in {setting.place}, that plan could turn into a tiny {act.id} disaster.")
    w.say(f"{params.name} rushed to {act.rush}, and a mess of {act.mess} happened.")
    w.para()
    w.say(f"The {params.helper} pointed to a little pretend jail by the door and said, \"Time for the jail lesson: slow bodies, kind hands.\"")
    w.say(f"{hero.id} blinked, then snorted a laugh. \"Oh. Right. My feet are not race cars.\"")
    w.say(f"{hero.id} put the toy away, cleaned up the {act.mess}, and helped tidy the {setting.place}.")
    w.say(f"After that, {hero.id} remembered the lesson learned: {act.lesson}.")
    w.say(f"And the silly little jail stayed empty, except for one very embarrassed cookie the helper had confiscated.")
    w.facts.update(hero=hero, helper=helper, obj=objcfg, activity=act, setting=setting)
    return StorySample(
        params=params,
        story=w.render(),
        prompts=[
            f"Write a short comedy story about a child at {setting.place} with the words shelter and jail.",
            f"Tell a funny lesson learned tale where {params.name} tries to {act.verb}.",
            f"Make a playful story about a helper, a messy mistake, and a child who learns to be careful.",
        ],
        story_qa=story_qa(w),
        world_qa=world_qa(w),
        world=w,
    )


def story_qa(w: World) -> list[QAItem]:
    f = w.facts
    hero = f["hero"]
    act = f["activity"]
    helper = f["helper"]
    obj = f["obj"]
    return [
        QAItem(
            question=f"Why did {hero.id} get into trouble at {w.setting.place}?",
            answer=f"{hero.id} got into trouble because {hero.pronoun()} tried to {act.verb} instead of moving carefully.",
        ),
        QAItem(
            question=f"What lesson learned did {hero.id} remember at the end?",
            answer=f"{hero.id} remembered that {act.lesson}.",
        ),
        QAItem(
            question=f"Who helped turn the problem into a joke?",
            answer=f"The {helper.label} helped, and that made the whole shelter scene feel funny instead of scary.",
        ),
        QAItem(
            question=f"What was the story's silly jail for?",
            answer=f"The little jail was a pretend place to pause, calm down, and stop the mischief before it got bigger.",
        ),
        QAItem(
            question=f"What object made the idea start?",
            answer=f"The story started when {hero.id} noticed {obj.phrase}.",
        ),
    ]


def world_qa(w: World) -> list[QAItem]:
    return [
        QAItem(question="What is a shelter?", answer="A shelter is a safe place where people or animals can stay for a while."),
        QAItem(question="What is jail?", answer="Jail is a place where grown-ups keep someone who broke a serious rule, but a pretend jail can be used in a story as a stern joke."),
        QAItem(question="Why do helpers tell children to slow down?", answer="Helpers tell children to slow down so they can stay safe and avoid making a bigger mess."),
    ]


def dump_trace(w: World) -> str:
    lines = ["--- world model state ---"]
    for e in w.entities.values():
        lines.append(f"  {e.id}: type={e.type} label={e.label} location={e.location}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for i, item in enumerate(sample.story_qa, 1):
            print(f"Q{i}: {item.question}")
            print(f"A{i}: {item.answer}")
        for i, item in enumerate(sample.world_qa, 1):
            print(f"WQ{i}: {item.question}")
            print(f"WA{i}: {item.answer}")


CURATED = [
    StoryParams(place="shelter", activity="tail", object="ball", name="Mina", gender="girl", helper="manager"),
    StoryParams(place="shelter", activity="paint", object="sign", name="Toby", gender="boy", helper="volunteer"),
    StoryParams(place="park", activity="tail", object="clipboard", name="Ruby", gender="girl", helper="caretaker"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, object) combos ({len(stories)} with story form):\n")
        for p, a, o, _ in triples:
            print(f"  {p:8} {a:8} {o:8}")
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
            params.seed = seed
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
